""" KEYENCE KV-5000に対する通信処理
    主に上位リンク通信の処理をラップしたもの。
    FTP通信によるファイルダウンロード処理も含む。
"""

import os
import socket
from ftplib import FTP
from ping3 import ping 
from datetime import datetime

# Definition of Const ------------------------------------------------------
PORT_NO = 8501      # PLCのポート番号(基本固定されている)
TIMEOUT_SEC = 0.5
USER = 'KV'         # FTPログイン用
PASSWORD = ''       # FTPログイン用

# Definition of Function ------------------------------------------------------
def com_with_plc(ip_add: str, cmd: str) -> str:
    """ KEYENCE KV-5000 上位リンク通信 """
    server = (ip_add, PORT_NO)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
        skt.settimeout(TIMEOUT_SEC)
        skt.connect(server)
        skt.sendall(cmd.encode("ascii"))
        
        recv_data = b"" # 空bytes
        while True:
            data = skt.recv(4096)

            # 接続が切断された場合(b""が返ってきた場合)
            if not data:
                raise ConnectionError(
                    "PLCとの接続が切断されました"
                )     

            recv_data += data

            # 終端判定
            if recv_data.endswith(b"\r\n"):
                break

        res = recv_data.decode("shift-jis", errors="replace")

        return res.replace("\r\n", "")
    

def read_device_u(ip_add:str, device:str)->str:
    """ PLCのデバイス1点のデータ読み込み
        (データ形式はU:10進数16ビット符号なし)

    Args:
        ip_add (str): PLCのIPアドレス
        device (str): デバイス名

    Returns:
        str: デバイス値またはエラーコード
    """
    cmd = 'RD ' + device +'.U\r'
    return com_with_plc(ip_add, cmd)


def write_device_u(ip_add:str, device:str, value:int)->str:
    """ PLCのデバイス1点のデータ書き込み
        (データ形式はU:10進数16ビット符号なし)

    Args:
        ip_add (str): PLCのIPアドレス
        device (str): デバイス名
        value (int): 書き込む値

    Returns:
        str: OK(成功時)またはエラーコード
    """
    cmd = 'WR ' + device +'.U ' + str(value) + '\r'
    return com_with_plc(ip_add, cmd)


def connect_check(ip_add:str)->bool:
    """PINGを使用した疎通確認を実施
        PLC以外の機器でも使用可能
        LANで使用するためtimeoutは0.2sec

    Args:
        ip_add (str): 接続先IPアドレス

    Returns:
        bool: 応答ありでTrue
    """
    # <不具合修正 2025/10/06>
    # resが0.0(float)で返ってくることがあり、「res==False」が成立する場合があった
    # (Falseは内部的には0として扱われるため)
    res = ping(ip_add, timeout=0.2)
    if res==False and type(res)==bool:
        print(f'{ip_add} : ping=False(error)')  # ForDebug
        return False    # 応答なし(ping エラー発生時)
    elif res==None:
        print(f'{ip_add} : ping=None(timeout)')  # ForDebug
        return False    # 応答なし(pingタイムアウト)
    else:
        return True     # 応答あり


def get_plc_datetime(ip_add:str)->str:
    """ PLC内部の現在年月日時刻を取得(CM700-CM705取得)
        (フォーマット：YYYY/mm/dd hh:MM:ss)

    Args:
        ip_add (str): PLCのIPアドレス
        port_no (int): PLCポート番号(通常8501)

    Returns:
        str: PLC 年月日 時分秒
    """
    dic = {
        'year': ['CM700.U', 0],
        'month': ['CM701.U', 0],
        'day': ['CM702.U', 0],
        'hour': ['CM703.U', 0],
        'minute': ['CM704.U', 0],
        'second': ['CM705.U', 0]
    }
    
    for value in dic.values():
        cmd = 'RD ' + value[0] + '\r'
        value[1] = com_with_plc(ip_add, cmd)[-2:]   #　最終2文字抽出

    val = f"20{dic['year'][1]}/{dic['month'][1]}/{dic['day'][1]} "
    val = val + f"{dic['hour'][1]}:{dic['minute'][1]}:{dic['second'][1]}"
    return val

def set_plc_datetime(ip_add:str)->str:
    """_summary_

    Args:
        ip_add (str): _description_
        port_no (int): _description_

    Returns:
        str: _description_
    """
    now = datetime.now()
    year = str(now.year - 2000).zfill(2)   # 下2桁
    month = str(now.month).zfill(2)
    day = str(now.day).zfill(2)
    hour = str(now.hour).zfill(2)
    minute = str(now.minute).zfill(2)
    second = str(now.second).zfill(2)
    weekday = str(now.weekday()) # 月曜=0/日曜=6
    
    # weekdayをKEYENCE形式(日曜=0/土曜=6)へ変換
    if weekday=='6':  # 日曜
        weekday = '0'
    else:           # 日曜以外
        weekday = str(int(weekday) + 1) 
    
    cmd = f"WRT {year} {month} {day} {hour} {minute} {second} {weekday}\r"
    return com_with_plc(ip_add, cmd)


def dl_alarm_comment(ip_add:str)->list:
    """ PLCのアラーム用デバイスのコメントをダウンロードする
        (対象デバイス=LR10.00-LR29.15の320点)

    Args:
        ip_add (str): PLCのIPアドレス

    Returns:
        list: アラームコメントのリスト
    """
    alarm_info=[]
    for i in range(10,30):
        for j in range(16):
            device = 'LR' + str(i) + str(j).zfill(2)
            cmd = 'RDC '+ device +'\r'
            res = com_with_plc(ip_add, cmd)
            res = res.replace('\r\n','')    # CR&LFの除去
            res = res.replace(' ','')       # スペース除去
            if res=='E6':res='NONE'             # コメントなし(E6)置換
            alarm_info.append([device,res]) # デバイス名-コメント
    
    return alarm_info


def ftp_get_filelist(ip_add:str, folder_name:str)->list:
    """ PLCのSDカード内フォルダのCSVファイル名を取得する
        (フォルダはルートフォルダ内の指定フォルダのみ)
    Args:
        ip_add (str): PLCのIPアドレス
        folder_name (str): SDカードルート上フォルダ名

    Returns:
        list: CSVファイル名のリスト(エラー時は空)
    """
    try:
        # FTPサーバ接続
        ftp = FTP(ip_add)
        ftp.encoding = 'shift-jis'  # KV5000の場合に必須
        ftp.set_pasv('true')
        msg = ftp.login(USER,PASSWORD)
        print(f'   {ip_add}:reply from ftp-server=',msg)

        # ファイル一覧取得(SDカードルート中フォルダのCSVファイルのみ対象)
        folder_path = '/MMC/' + folder_name
        ftp.cwd(folder_path)       # カレントディレクトリ移動
        fpath_list = ftp.nlst('.')   # ファイル一覧取得(フルパス)
        fname_list = [os.path.basename(x) for x in fpath_list]
        fname_list = [n for n in fname_list if n.endswith('.CSV') or n.endswith('.csv')] # CSVファイルのみ
        return fname_list
    except:
        print(f'   {ip_add}:FTP-process failure')
        return []


def ftp_get_file(ip_add:str, folder_name:str, file_name:str, save_folder:str)->bool:
    """ PLCのSDカード内のファイルをダウンロードする

    Args:
        ip_add (str): PLCのIPアドレス
        folder_name (str): SDカードの対象フォルダ名
        file_name (str): DL対象のファイル名
        save_path (str): 保存先フォルダのパス

    Returns:
        bool: 成功時=True / 失敗時=False
    """
    try:
        # FTPサーバ接続
        ftp = FTP(ip_add)
        ftp.encoding = 'shift-jis'  # KV5000の場合に必須
        ftp.set_pasv('true')
        msg = ftp.login(USER,PASSWORD)
        print(f'   {ip_add}:reply from ftp-server=',msg)

        # ファイルダウンロード
        folder_path = '/MMC/' + folder_name
        ftp.cwd(folder_path)       # カレントディレクトリ移動
        f = open(save_folder+'\\'+file_name,'wb')
        ftp.retrbinary('RETR '+file_name, f.write)
        print(f'   {file_name} is downloaded from PLC')
        return True
    except:
        print(f'   {ip_add}:FTP-DL-process failure')
        return False



# テストコード(動作確認用) -----------------------------------------------------------------
if __name__=='__main__':
    # ワーキングディレクトリ変更(VSCode使用時必要)
    # os.chdir(os.path.dirname(__file__))
 
    ip_add = '172.21.0.20'
    # cmd = 'WR DM1990.U 6000\r'
    res = read_device_u(ip_add, 'DM1990')
    print(res)
    exit()

    if connect_check(ip_add):
        res = ''
        # res = com_with_plc(ip_add, cmd)
        # res = read_device_u(ip_add, 'DM1990')
        # res = write_device_u(ip_add, 'DM1990', 6500)
        # res = set_plc_datetime(ip_add)
        # res = get_plc_datetime(ip_add)
        # res = dl_alarm_comment(ip_add)
        print(res)

        if False:
            plc_folder='operation_data'
            save_folder = os.path.expanduser('~/Desktop')   # デスクトップパス
            flist = ftp_get_filelist(ip_add, plc_folder)
            print(flist)
            ftp_get_file(ip_add,plc_folder,flist[1],save_folder)
        
    else:
        print(f'{ip_add}: Connectivity False')




"""
----- 更新履歴 -----

2026.5.10
ChatGPTのアドバイスにより、com_with_plcをリニューアル。
・分割受信(分割判定)
・途中切断による例外発生
に対応した。


"""