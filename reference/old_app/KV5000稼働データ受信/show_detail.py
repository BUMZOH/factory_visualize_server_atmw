#####################################################################
#   稼働データ 機械日付別詳細データ表示Module Ver.1.0
#   Last Update on 2023.5.13
#####################################################################
import os
import xlwings as xw
import datetime

# 定数
DEBUG = False
VIEW_SHEETS = ['Fact1','Fact2_3','Fact4']
if DEBUG:
  DETAIL_FPATH = './TEST/DetailOpeData.xlsx'
else:
  DETAIL_FPATH = '//LS720D6C6/share/P_ProductControl/OperationData/DetailOpeData.xlsx'

# グローバル変数
wb = None

def show_detail()->None:
  global wb
  try:
    wb = xw.books.active  # アクティブブック取得
    print(f'選択ブック={wb.name}')
  except:
    print('エクセルファイルが見つかりません')
    return
  
  sh = xw.sheets.active # アクティブシート取得
  if sh.name not in VIEW_SHEETS:
    print('VIEWシートが選択されていません')
    return

  # アクティブセルの行列取得
  acrow = wb.selection.row
  accol = wb.selection.column
  
  # 機械番号取得
  mcno = sh.range((acrow,1)).value
  if mcno!=None and '号機' in mcno:
    mcno = mcno.replace('号機','')
  else:
    print('不正なセルを選択しています(機番データなし)')
    return
  # 日付取得(シート名)
  date = sh.range((3,accol)).value
  if type(date)==datetime.datetime:
    date = date.strftime('%y%m%d')
  else:
    print('不正なセルを選択しています(日付データなし)')
    return
  print(f'mcno={mcno}/date={date}')

  # 全シート名取得
  sht_names = [x.name for x in wb.sheets]
  if date not in sht_names:
    print('日付に対応するシートが見つかりません')
    return
  
  # 対象データのシート格納
  data_sht = wb.sheets[date]
  # 対象データ列の格納(対象機械のデータ列)
  data_col = serch_data_col(mcno,date)
  print(f'data_col={data_col}')
  if data_col==0:
    print('対象データが見つかりません')
    return
  # 対象データの格納(データは列1529まで)
  ope_data = data_sht.range((1,data_col),(1529,data_col)).value
  # ＜注意＞ データに変換(単なるリストは行データとして扱われるため)
  ope_data = [[x] for x in ope_data]
  d_wb = xw.Book(DETAIL_FPATH)
  d_sh = d_wb.sheets['DATA']
  d_sh.range('B1').value = ope_data

def serch_data_col(mcno,sheet_name)->int:
  sht = wb.sheets[sheet_name]
  for i in range(2,500):
    if sht.range((3,i)).value == 'No.'+str(mcno):
      return i
  return 0  # 見つからなかった場合

#--- モジュール単体テスト用 ------------------------------------------
if __name__=='__main__':
  import tkinter as tk

  #カレントディレクトリ変更
  os.chdir(os.path.dirname(__file__))

  root = tk.Tk()
  root.geometry('200x60+1500+200')
  root.title('ShowDetail')
  root.attributes('-topmost',True)
  root.resizable(0,0) # 最大化の無効
  # root.wm_overrideredirect(True)  #タイトルバー非表示

  btn_excute = tk.Button(text='詳細表示',command=show_detail)
  btn_excute.pack(padx=10,pady=10)

  root.mainloop()






