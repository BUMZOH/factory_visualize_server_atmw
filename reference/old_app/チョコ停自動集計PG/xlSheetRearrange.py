###########################################################
#     エクセルシート並べ替えプログラム Ver.1.00
###########################################################

import xlwings as xw
import os

def xl_sheet_rearrange(xlbook):
  # 引数xlbool:対象エクセルファイルのパス
  wb = xw.Book(xlbook)

  # シート名をリストで取得(内包表記に注意)
  sheet_names = [sht.name for sht in wb.sheets]
  # 並べ替え
  sheet_names.sort()
  # print(sheet_names) # forDebug

  for sht_name in sheet_names:
    # シートコピー(先頭にNを付ける)
    wb.sheets[sht_name].copy(name='N'+sht_name)
  # コピー元シートの削除
    wb.sheets[sht_name].delete()

  # コピー後シートの先頭'N'除去
  for sht in wb.sheets:
    sht.name = sht.name.replace('N','')


#--- 呼び出しが自分自身の場合 ---------------------------------------------------
if __name__ == '__main__':
  os.chdir(os.path.dirname(__file__))
  xl_sheet_rearrange('xlbook.xlsx')

