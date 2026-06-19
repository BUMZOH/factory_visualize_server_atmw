#####################################################################
#   稼働データ 月次推移表(ViewTable)コピーModule Ver.1.0
#   Last Update on 2023.5.4
#####################################################################
# インポート処理
import os
import xlwings as xw

# 定数定義
DEBUG = False
if DEBUG:
    TEMPLATE_PATH = './TEST/ViewTemplate.xlsx'
else:
    TEMPLATE_PATH = '//LS720D6C6/share/P_ProductControl/OperationData/ViewTemplate.xlsx'
VIEW_TABLES = ['Fact1','Fact2_3','Fact4']

#----- 関数定義 -----------------------------------------------
def copy_view_table(outf_path:str) -> None:
  #EXCEL起動
  app = xw.App(visible=False, add_book=False)
  
  # コピー元＆コピー先ブックオープン  
  from_wb = app.books.open(TEMPLATE_PATH)
  to_wb = app.books.open(outf_path)

  # シート一覧取得
  sheets = to_wb.sheet_names
  # Viewシートコピー処理
  for vt in VIEW_TABLES:
    if vt not in sheets:
      print(f'---Copying ViewTable<{vt}>')
      from_wb.sheets[vt].copy(before=to_wb.sheets[0])

  # 上書き保存&ブッククローズ
  to_wb.save()
  to_wb.close(); from_wb.close()

  app.kill()  # EXCEL終了(QUITを使うとゾンビ化する)

#----- モジュール単独テスト用  ----------------------------------
if __name__=='__main__':

  # カレントディレクトリ変更(VSCode使用時のみ必要)
  os.chdir(os.path.dirname(__file__))

  outf_path = './TEST/OpeData-2303.xlsx'  # ローカルテスト用
  copy_view_table(outf_path)
