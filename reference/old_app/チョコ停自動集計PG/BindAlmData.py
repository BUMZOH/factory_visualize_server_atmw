################################################################
#   光和工業 VTアラーム履歴ファイル 結合プログラム
#   (AlmAggregation.pyから呼び出されることが前提)
#---------------------------------------------------------------
#   作成:2023.5.6 by Fumihiro Mase
################################################################
# インポート処理 ------------------------------------
import os
import shutil
import glob
import csv
import pprint


# 定数定義 ------------------------------------------
DEBUG = False
if DEBUG:
  TRASH_PATH = './VtAlmData/TrashBox/'
  DATA_PATH = './VtAlmData/'
else:
  TRASH_PATH = '//LS720D6C6/share/P_ProductControl/VtAlmData/TrashBox/'
  DATA_PATH = '//LS720D6C6/share/P_ProductControl/VtAlmData/'


# 関数定義 ------------------------------------------
def bind_alm_data():
  """アラームデータ結合 メイン処理"""
  mc_list = get_mc_info()
  for mcno in mc_list:
    print(f'--- Start binding for {mcno}---') 
    while True:
      mainf,subf = get_latest_2files(mcno)
      if mainf!='':
        print('-----> 2files are bound ')
        bind_2files(mainf,subf)
      else:
        break
  print('--- Binding-process finished ---')

def get_mc_info()->list:
  """データフォルダ内に存在する機械リストを返却"""
  files = glob.glob(DATA_PATH+'MC*.csv')
  if len(files)==0:return []  # 該当ファイルなしの場合(空リスト)
  files = [x.replace('\\','/') for x in files]  # 「//」の置き換え(glob仕様)
  fname = [os.path.basename(x) for x in files]  # ファイル名のみ取得
  mc_list = [x[:5] for x in fname]  # ファイル名先頭5文字抽出(例:MC010)
  mc_list = list(set(mc_list))  # 重複データ除去
  mc_list.sort()  # 並び替え
  return mc_list


def get_latest_2files(mcno:str)->tuple:
  """指定された機械の最新アラームファイル2つ返す"""
  files = glob.glob(DATA_PATH+mcno+'*.csv')
  # ファイルが2個以上ない場合
  if len(files)<=1:
     return ('','') # 空のタプル返却
  
  files = [x.replace('\\','/') for x in files]  # 「//」の置き換え(glob仕様)
  files.sort(reverse=True)  # 降順でソート
  return (files[0],files[1])

def bind_2files(mainf:str, subf:str)->None:
  """2つのファイルを結合させる
     結合後はmainfが残り、subfはTrashBoxへ移動

    引数：
      mainf(str) : メインファイルのパス(結合する側)
      subf(str)  : サブファイルのパス(結合される側)
  """
  # メインファイル データ読み込み
  with open(mainf,'r') as f:
     reader = csv.reader(f)
     m_data = [row for row in reader] # readerには各行がリストで格納
  m_header = m_data[0:4]  # 0-3行目までは非データ部(出力時に使用)
  m_data = m_data[4:]     # 4行目以降(データ部)

  # サブファイル データ読み込み
  with open(subf,'r') as f:
     reader = csv.reader(f)
     s_data = [row for row in reader]
  s_data = s_data[4:] # 先頭4行除去

  # データ結合
  m_data += s_data

  # ID行の追加(ID=DATE+TIME+ALM_No)
  for d in m_data:
     d.insert(0,d[1]+'-'+d[2]+'-'+d[5])

  # IDデータの作成(重複除去→ソート)
  ids = [x[0] for x in m_data]
  ids = list(set(ids))
  ids.sort(reverse=True)

  # IDに基づき重複データの除去
  new_data=[]
  for id in ids:
     for x in m_data:
        if id==x[0]:
           new_data.append(x)
           break  # breakすることにより重複除去となる
  m_data = new_data # 結果の再代入

  # ID列(0列目)の削除
  for d in m_data: d.pop(0)
  
  # No振り直し
  for i,d in enumerate(m_data): d[0] = i

  # ヘッダ部再結合
  m_data = m_header + m_data

  # CSVファイル再出力
  with open(mainf,'w',newline='') as f:
     writer = csv.writer(f)
     writer.writerows(m_data)
  
  # サブファイルのTrashBoxへの移動
  shutil.move(subf,TRASH_PATH)

#--- モジュール単体テスト用 ------------------------------------------
if __name__=='__main__':
  # カレントディレクトリ変更処理(VSCode使用時のみ)
  os.chdir(os.path.dirname(__file__))

  bind_alm_data()


##### MEMO ################################################################
#
# 【データ構造】
#  0:No - 1:DATE - 2:TIME - 3:COUNT - 4:STATUS - 5:ALARM No - 6:MESSAGE
#
#
#
















