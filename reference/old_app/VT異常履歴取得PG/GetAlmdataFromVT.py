#========================================================================
#  KEYENCE VT-2/3 異常履歴保存プログラム Ver.1.00
#
#  【注意】
#   VTとPCはUSB接続を前提とする(Ethernetは使わない)
#   VT-StudioはVer.8の使用が前提
#   VTの機種はVT-3とVT-5の両方に対応している
#========================================================================
# import処理
import os
import pyautogui as pag
import subprocess
import time
import configparser
import glob
import shutil
import pandas as pd


# カレントディレクトリ変更(VSCodeから実行時のみ必要になる処理)
os.chdir(os.path.dirname(__file__))


# Global変数初期化 ---------------------------------------------------
if True:
  DebugMode = False  #デバッグモードフラグ
  HomeDir = os.environ['USERPROFILE']   # カレントユーザのホームディレクトリ
  VtType = 0  # VT機種(VT3→3 / VT5→5)
  McNo = 0    #機械No(1-999)

# 機械番号/VT機種のユーザ入力処理 -------------------------------------
if True:
  while True:
    # 機械番号McNoはアラームデータのファイル名に使用される
    McNo = pag.prompt(text='機械番号を入力してください。',
                    title='ユーザ入力', default='')
    if McNo != None:
      if not McNo.isdecimal():
        pag.alert(text='整数値を入力してください', title='通知')
        continue
      if len(McNo)>3:
        pag.alert(text='3桁以下の整数を入力して下さい', title='通知')
        continue
      else:
        McNo = str(int(McNo)) # 全角→半角対策
        McNo = McNo.zfill(3)  # 0-padding(3桁数字へ)
        print(f'McNo={McNo}') # forDebug
        break
    else:
      pag.alert(text='処理を中止します', title='通知')
      quit()

  # VT機種情報のユーザ入力(VT3→3 / VT5→5)
  VtType =  0  # VT機種初期化(Global化)
  while True:
    ret = pag.prompt(
      text='VT機種を入力してください\n  VT3 → 3\n  VT5 → 5',
      title='ユーザ入力'
    )
    if ret=='3':
      VtType = 3
      break
    elif ret=='5':
      VtType = 5
      break
    else:
      pag.alert(text='入力値が不正です',title='通知')
      continue  

# VT-Studio(VT2/3用)関連＆出力フォルダPath設定 -----------------
if True:
  # VT-Studioプログラムパス格納(VT3とVT5で分岐)
  # (rはraw文字列という。バックスラッシュを改行とさせないため。)
  if VtType==3:
    VtAppPath = r"C:\Program Files (x86)\KEYENCE\VTS8J\VT3\VTS.EXE"
  elif VtType==5:
    VtAppPath = r"C:\Program Files (x86)\KEYENCE\VTS8J\VT5\VTS.EXE"

  # VT-Studio iniファイルPath設定
  if VtType==3:
    VTTransiniPath = HomeDir + r"\AppData\Local\KEYENCE\VTS4\VTTrans.ini"
    VTSiniPath = HomeDir + r"\AppData\Local\KEYENCE\VTS4\VTS.ini"
  elif VtType==5:
    VTTransiniPath = HomeDir + r"\AppData\Local\KEYENCE\VTS8J\VTTrans.ini"
    VTSiniPath = HomeDir + r"\AppData\Local\KEYENCE\VTS8J\VTS.ini"
  # print('iniファイルPath=',VTSiniPath,VTTransiniPath)  # forDebug

  # データ出力用フォルダ(ローカル)
  datafolder_local = HomeDir + '\\Desktop\VtAlmData'
  # データ出力用フォルダ(サーバ)
  if DebugMode==True:
    # 自宅Server
    datafolder_server = r'\\landisk-0c31f2\disk1\SampleFolder'
  else:
    #会社Server
    datafolder_server = r'\\LS720D6C6\share\P_ProductControl\VtAlmData'

# 必要ファイル/フォルダの有無確認 -------------------------------
if True:
  if not os.path.isfile(VtAppPath):
    pag.alert('VT-Studioプログラムがありません(異常終了)','ERROR')
    quit()
  if not os.path.isfile(VTSiniPath):
    pag.alert('VTS.iniファイルが見つかりません(異常終了)','ERROR')
    quit()
  if not os.path.isfile(VTTransiniPath):
    pag.alert('VTTrans.iniファイルが見つかりません(異常終了','ERROR')
    quit()

  # ローカルのデータ出力用フォルダ存在確認
  # (注意:サーバのデータ出力フォルダの確認は、アラームデータ受信後実施)
  if not os.path.exists(datafolder_local):
    pag.alert(
      text='デスクトップにデータ出力用フォルダ(VtAlmData)を作成します',
      title='通知')
    os.makedirs(datafolder_local)

# iniファイル前処理(=行の除去) ---------------------------------
if True:
  # VT-5のVTS.iniファイル中には「=」だけの行があり、エラーが
  # 発生するため、「=」文字を削除(一応VT-3の時も実施する)
  with open(VTSiniPath, 'r', encoding='utf-16') as f:
    lines = f.readlines()

  for i,line in enumerate(lines):
    if line == '=\n':
      print(f'i={i}行目が=だけの行です') # forDebug
      lines[i] = '\n'
      
  with open(VTSiniPath,'w',encoding='utf-16') as f:
    f.writelines(lines)

# VT-Studio iniファイルの設定(書き換え) --- ---------------------
if True:
  # VTS.iniの書き換え(通信方式=USBへ) ----------
  #(VT-5は「=」だけの行によりエラーが発生するのでスキップ→今後対応)
  if VtType==3:
    conf = configparser.ConfigParser()
    conf.read(VTSiniPath,encoding='utf-16')
    # print(conf.get('Com','Port')) #forDebug
    conf.set('Com','Port','0')  #USB接続は[Com]/Port=0
    with open(VTSiniPath,'w',encoding='utf-16') as file:
      conf.write(file)

  # VTTrans.iniの書き換え(保存場所等) ----------
  conf = configparser.ConfigParser()  # インスタンス再生成
  conf.read(VTTransiniPath,encoding='utf-16')
  # print(conf.get('RcvAlarm','Path')) #forDebug
  #保存場所(DesktopのVtAlmDataフォルダ)
  conf.set('RcvAlarm','Path', HomeDir + '\\Desktop\\VtAlmData')
  # (最後の文字がバックスラッシュの場合はrow文字列使えない)
  conf.set('RcvAlarm','headstr0','?MC'+McNo+'_ALM?')   #ファイル名先頭文字
  conf.set('RcvAlarm','chkid0','1')   # ID0チェックボックス
  conf.set('RcvAlarm','chkid1','0')   # ID1チェックボックス
  conf.set('RcvAlarm','chkid2','0')   # ID2チェックボックス
  conf.set('RcvAlarm','chkid3','0')   # ID3チェックボックス
  conf.set('RcvAlarm','chkfilename0','1')   #アラームIDﾁｪｯｸﾎﾞｯｸｽ
  conf.set('RcvAlarm','chkfilename1','1')   #日付(年月日)ﾁｪｯｸﾎﾞｯｸｽ
  conf.set('RcvAlarm','chkfilename2','1')   #時刻(時分秒)ﾁｪｯｸﾎﾞｯｸｽ
  conf.set('RcvAlarm','chkfiletype','1')    #ファイル形式=CSV
  with open(VTTransiniPath,'w',encoding='utf-16') as file:
    conf.write(file)

# VT-Studioの起動 ---------------------------------------------
subprocess.Popen(VtAppPath)

# 起動確認(KEYENCEロゴが表示→消滅を確認する)------------
if True:
  # 起動中判別画像の格納
  imgFile = '' #初期化
  if VtType==3:
    imgFile = 'logo_vt3.png'
  elif VtType==5:
    imgFile = 'splash_vt5.png'
  
  # 《注》環境ごとに画像フォルダを切り替えるので注意すること
  imgPath = './img/Res1920x1080Scale100/' + imgFile
  imgFound = False
  loopCounter = 200
  for i in range(loopCounter):
    # confidence使わないと画像サーチ失敗(0.4～正常動作)
    searchRslt = pag.locateOnScreen(
                  imgPath, grayscale=True, confidence=0.6)
    # 初回発見時
    if imgFound==False:
      if searchRslt is not None:
        x,y = pag.center(searchRslt)
        print(f'i={i}:{imgFile}表示確認(検出位置:x={x},y={y})')
        pag.moveTo(x,y) # 検出位置確認のためマウス移動
        imgFound = True
        continue
      else:
        print(f'i={i}:{imgFile}見つかりません')
    
    # SplashWindow消滅待ち(表示中の処理)
    if imgFound==True:
      if searchRslt is None:
        print(f'i={i}:{imgFile}消滅確認(break実行)')
        break
      else:
        x,y = pag.center(searchRslt)
        print(f'i={i}:{imgFile}表示中(検出位置:x={x},y={y})')
    
    # タイムアウト処理
    if imgFound==False and i==loopCounter-1:
      print('VT-Studioの起動を確認できませんでした。終了します。')
      quit()
  time.sleep(1) # DwellTime

# VT-Studioへのキー送信処理  -------------------------------------
if True:
  # 通信(C)メニュー 開く
  pag.hotkey('alt','c');time.sleep(0.3)
  # "VT→PCデータ受信(R)"を実行(キー入力:r)
  pag.hotkey('r');time.sleep(0.3)

  if DebugMode==False:
    # "アラーム履歴受信(L)"を実行(キー入力:l)
    pag.hotkey('l');time.sleep(2)   # sleepタイム要調整★
    
    #--- アラーム履歴受信(USB)ダイアログ表示中 ---
        # 受信(R)ボタンの実行
    pag.hotkey('alt','r')
    # ESP押す(DEBUG時のみ)
    time.sleep(5) # データ転送待ち(画像認識方式へ変更予定)
    # 受信が完了しました(OKボタン付) ウィンドウが表示される
    pag.hotkey('enter')
  else:
    # デバッグ時
    pag.hotkey('esc')   #ダイアログ消去
    time.sleep(1)

  # VT-Studio終了
  pag.hotkey('alt','f4');time.sleep(0.5)

# サーバへのファイル書き込み処理 -----------------------------------
if True:
  # ユーザ入力(サーバファイル書き込みの判断) ----------
  res = pag.confirm(
    text='サーバへアラームデータを書き込みますか？\n' +
        '(データが正常に受信できなかった場合はNOを選択)',
    title='確認',
    buttons=['YES','NO'])
  if res=='NO':
    pag.alert('プログラム終了します')
    quit()

  # ネットワーク疎通確認(ping使用) ----------
  # (参考:https://shigeblog221.com/python-ping/)
  host = '192.168.1.1'  # ping送信先
  res = subprocess.run(['ping',host,'-n','2','-w','300'],
                       stdout=subprocess.PIPE)
  # print(res.stdout.decode('cp932)')) # forDebug
  if res.returncode==0:
    print('ping success(to 192.168.1.1)')
  else:
    pag.alert('ネットワーク通信確認に失敗しました(終了します)')
    quit()

  # サーバのデータ用フォルダ存在確認(なければ作成) ----------
  if not os.path.exists(datafolder_server):
    pag.alert(
      text='サーバのデータ出力用フォルダが見つかりません(PG終了)',
      title='通知')
    quit()
  else:
    print('The folder is found in server')  # forDebug
  
  # 対象データファイル検索 ----------
  #  ファイル名はVT-Studio側で決められるため、機械番号とファイル名から検索する
  #  データファイル名規則 →「MCXXX_ALM0_YYMMDDhhmmss.csv」(XXX:機械番号)
  files = glob.glob(datafolder_local + '\\*.csv')
  if len(files)==0:
    pag.alert('データファイル(csv)が見つかりません。(終了します)')
    quit()
  # ファイル名に対象機械Noが含まれているものを抽出(pandasのSeries利用)
  sr = pd.Series(files)
  sr = sr[sr.str.contains('MC'+McNo)]
  if sr.size==0:
    pag.alert('対象機械のデータファイルが見つかりません(終了します)')
    quit()
  # 最新のファイルのファイル名を取得
  sr = sr.sort_values(ascending=False)
  csv_path_local = sr.iloc[0]
  print(sr) ; print(csv_path_local) # ForDebug
    
  # ファイル書き込み処理
  csv_filename = os.path.basename(csv_path_local)
  csv_path_server = datafolder_server + '\\' + csv_filename
  print(csv_path_server)
  shutil.copyfile(csv_path_local, csv_path_server)
  pag.alert('サーバにデータファイルを書き込みました。\n'
            + '(File= ' + csv_filename + ')\n\n'
            + 'プログラム終了します')


#--- MEMO -------------------------------------------------------
if True:
# VT-Studio種類
# VTの機種によって使用するVT-Studioが異なる。
# VT-5  →C:\Program Files (x86)\KEYENCE\VTS8J\VT5\VTS.exe
# VT-3→C:\Program Files (x86)\KEYENCE\VTS8J\VT3\VTS.EXE
# VT-3とVT-5ではユーザファイルの拡張子が異なり、自動切換え（たぶん）

# 異常履歴保存ダイアログの設定は以下のiniファイルに保存されている(VT3)
# (チェックボックスの値や保存場所が記録されている)
# (一度ダイアログを開くとVTTrans.iniが生成されるようだ。)
# → C:\Users\fumih\AppData\Local\KEYENCE\VTS4\VTTrans.ini

# 通信設定は以下のiniファイルに保存されている(VT3)
# → C:\Users\fumih\AppData\Local\KEYENCE\VTS4\VTS.ini
# [Com]のportの値
# USB→0 / シリアル→0 / Ehernet→100

# VSCode上で実行している場合は、Pythonプログラムが終了するとVT-Studioが
# 強制終了される。(ダブルクリック時は終了しない)

# VSCodeで折りたためるように各ブロックに"if True:"を記述してある。

# 【今後の機能追加】
#  ・ディスプレイの解像度に合わせて画像認証の画像を切り替える→難しい
#  ・
#
#【課題】
# ・ディスプレイの解像度やスケールが異なると画像認証が失敗する
#  →環境ごとに基準画像を用意する(PG的には楽)
#  →自動で基準画像を拡大縮小させる(たぶん難しい)
#  →メモリ使用量で判断する(案としては良いが、難易度高い)
#  →画面中央の画像を取得し、スプラッシュウィンドウの色分布で
#   判断する→Pillowでできそう◎
# ・VT-5はアラーム履歴受信画面を開く時、直前に通信確認を行う
#  →デバッグ時にエラーが出るので注意
#
#----------------------------------------------------------------
  pass