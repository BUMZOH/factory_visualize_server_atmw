print("=========================================================")
print("           チョコ停データ集計プログラム Ver.1.01            ")
print("=========================================================")

# import -------------------------------------------------------
import pandas as pd
import xlwings as xw
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import japanize_matplotlib
import glob
from datetime import timedelta
import datetime
import calendar
import sys

# 実行前準備処理 -------------------------------------------------
if True:
  # カレントフォルダ移動(VSCデバッグ時のみ必要な処理)
  os.chdir(os.path.dirname(__file__))
  sys.dont_write_bytecode = True  # __pycache__を作らない設定

# 独自モジュール読み込み ------------------------------------------
# (__pycache__を作らないように上記処理の後に記述すること)
import xlconst  #自作エクセル操作用定数定義
import xlSheetRearrange
import BindAlmData # 独自モジュール(アラーム履歴ファイル結合)

# グローバル変数初期化 -------------------------------------------
if True:
  DebugMode = False    # デバッグ時True
  if DebugMode==True:   
    data_folder_path = './VtAlmData'  # アラーム履歴データ保存場所
    report_folder_path = './AlmReport'  #レポートファイル保存場所
  else:
    # サーバのデータ保存用フォルダ指定のこと
    data_folder_path = r'\\LS720D6C6\share\P_ProductControl\VtAlmData'
    report_folder_path = r'\\LS720D6C6\share\P_ProductControl\AlmReport'
  yearMonthLst = [] #集計対象の年月日([0]=年/[1]=月)
  xl_file = ''
  xl_path = ''

#--- 関数定義 ---------------------------------------------------
#任意の年、月から月初め(1日)を求める関数
def get_first_date(year, month):
    return datetime.date(year, month, 1)

# 任意の年、月から月末を求める関数
# (https://note.nkmk.me/python-datetime-first-last-date-last-week/)
def get_last_date(year, month):
    return datetime.date(year, month, calendar.monthrange(year, month)[1])

# 任意の年、月から翌月1日を求める関数
def get_next_first_date(year,month):
  return get_last_date(year,month) + timedelta(days=1)

# メインプロシージャ(機械ごとの集計・Excel入力処理)
def MainProc(mc_no):
  global xl_file
  global xl_path
  print(f'機械No={mc_no}の処理を開始します。----------')
  # 引数はintのため3桁のstrに変換
  mc_no = str(mc_no).zfill(3)

  # 対象機械(mc_no)のデータファイル検索(csv_pathへの格納) ------------
  if True:
    # チョコ停データファイル名規則 →「MCXXX_ALM0_YYYYMMDDhhmmss.csv」(XXX:機械番号)
    files = glob.glob(data_folder_path + '/*.csv')
    if len(files)==0:
      print('データファイル(csv)が見つかりません。(終了します)')
      return
    # ファイル名に対象機械Noが含まれているものを抽出(pandasのSeries利用)
    sr = pd.Series(files)
    sr = sr[sr.str.contains('MC'+mc_no)]
    if sr.size==0:
      print('対象機械のデータファイルが見つかりません')
      return
    # 最新のファイルのファイル名を取得
    # (将来的には、古いファイルの情報を新しいファイルに統合させる予定★)
    sr = sr.sort_values(ascending=False)
    csv_path = sr.iloc[0]
    print('対象アラーム履歴データ\n'+csv_path) # forDebug

  # CSVファイルからDataFrame(オリジナルデータdf_org)作成 ----------------
  if True:
    # (注意：先頭3行が無効→skiprows設定)
    df_org = pd.read_csv(csv_path,encoding='shift-jis',skiprows=3)
    # DATEとTIMEから日時データ(datetime型)を生成し、カラムに追加
    df_org['DATE_TIME'] = pd.to_datetime(df_org['DATE']+' '+df_org['TIME'])
    # 必要なカラムのみ残す
    df_org = df_org[['DATE_TIME','ALARM No','MESSAGE']]

    # 対象年月(yearMonthLst)による絞り込み -----
    # (単に日付だけの場合は0時0分0秒になる)
    y = int(yearMonthLst[0])
    m = int(yearMonthLst[1])
    dateFrom = str(get_first_date(y, m))    #当月の1日
    dateTo = str(get_next_first_date(y, m)) #翌月の1日
    df_org = df_org[(df_org['DATE_TIME']>=dateFrom) & (df_org['DATE_TIME']<dateTo)]

    # 該当データなしの場合 -----
    if df_org.size==0:
      print('該当データなし(終了)')
      return
    df_org = df_org.sort_values(by='DATE_TIME')  #日付カラムで並び替え

  # アラームごとの集計&グラフ描画 ----------
  if True:
    # groupedはSeriel型
    grouped = df_org.groupby('MESSAGE')['ALARM No'].count()
    grouped = grouped.sort_values(ascending=False)

    # groupedデータのグラフ描画(Excel挿入用) ----------
    fig = plt.figure()
    grouped.plot(kind='bar',color='pink')
    # plt.show()  # ForDebug
    pass

  # 日別アラーム発生回数データ(df_date)の作成と集計(grp_date)-------------
  if True:
    # (日付のみの取り出し→https://smart-hint.com/python/datetime-ymd/)
    # ＜注意＞ 以下の命令「df_date=df」にすると参照が渡された(複製にならなかった)
    df_date = df_org[['DATE_TIME','ALARM No','MESSAGE']]  # DataFrame複製
    df_date['DATE'] = df_date['DATE_TIME'].dt.strftime('%Y-%m-%d')  # 年月日抽出
    df_date = df_date[['DATE','ALARM No','MESSAGE']]  # 必要なカラムのみ残す
    grp_date = df_date.groupby('DATE')['ALARM No'].count()
    grp_date.index = pd.to_datetime(grp_date.index) # IndexをDateTimeIndexへ変換
    # print(grp_date)   # ForDebug

    # 対象月1か月分のSeries(sr_date)を作成(値は0で初期化)
    y = int(yearMonthLst[0])
    m = int(yearMonthLst[1])
    dateFrom = str(get_first_date(y, m))    #当月の1日
    dateTo = str(get_last_date(y,m)) #翌月の末日
    # 対象月の日付からインデックス作成
    date_index = pd.date_range(start=dateFrom,end=dateTo,freq='D')
    lst = [0] * date_index.size # 日数分のリスト作成(値は0)
    sr_date = pd.Series(lst,index=date_index) #Series作成
    # print(sr_date)
    grp_date = (grp_date + sr_date).fillna(0)   # Series連結(fillnaはNaN置換)
    # print(grp_date) # ForDebug

    # グラフ描画 -----------
    # (plotメソッドだけだと、日付の表示が'2022/05/21 00:00:00のように
    #  なるため、以下のようにmatplotlib形式で指定する。)
    # Formatterでx軸の日付ラベルを月・日に設定
    fig2,ax2 = plt.subplots()
    ax2.bar(grp_date.index,grp_date.values,color='pink')
    # Formatterでx軸の日付ラベルを月・日に設定
    xfmt = mdates.DateFormatter("%m/%d")
    # DayLocatorで間隔を日数に
    xloc = mdates.DayLocator()
    ax2.xaxis.set_major_locator(xloc)
    ax2.xaxis.set_major_formatter(xfmt)
    # X軸表示範囲設定(前後1日表示の方がよいため、以下無効化)
    # ax2.set_xlim(grp_date.index[0],grp_date.index[-1])
    # X軸表示文字の回転
    plt.xticks(rotation=90)
    # plt.show()
    pass # dummy

  # エクセルファイルのオープン ------------------------------------------
  if True:
    xl_file = 'AlmReport_' + str(yearMonthLst[0]) + '-' \
                + str(yearMonthLst[1]) + '.xlsx'
    xl_path = report_folder_path + '/' + xl_file
    if not os.path.isfile(xl_path):
      print('データ入力用エクセルファイルありません')
      print('Excelブックを新規作成します')
      # print('(ファイル名:' + xl_file + ')')
      wb = xw.Book()
      wb.save(xl_path)  
    else:
      wb = xw.Book(xl_path)

  # 対象機械(mc_no)用シート準備 ----------------------------------------
  if True:
    # →既にシートが存在する場合は、シートを初期化する目的で一度削除して
    #  再作成する(画像オブジェクトの削除が困難なため)
    for s in wb.sheets:
      # print('sheet name=' + s.name) # ForDebug
      if s.name == mc_no:
        # シートが該当の機械だけ1枚の時エラーがでるので、Sheet1という
        # シートを追加しておく(シートをゼロにはできない)
        # print('len(wb.sheets)=' + str(len(wb.sheets)))
        if len(wb.sheets)==1:
          wb.sheets.add('Sheet1')
        s.delete()
        break
    wb.sheets.add(mc_no)
    # Sheet1という名前のシートがあれば削除しておく
    # (ブック作成時に自動的に作成されるため)
    for s in wb.sheets:
      if s.name == 'Sheet1':
        s.delete()
        break

  # 対象機械用シート(シート名=mc_no)へのデータ記入 -----------------------
  if True:
    sht = wb.sheets[mc_no]
    sht.range(4,1).options(index=False).value = df_org
    sht.range(5,5).options(index=True).value = grp_date #Serisはタイトル行がない
    sht.range(4,8).options(index=True).value = grouped

    # グラフの挿入(H1セルの位置に挿入) ----------
    sht.pictures.add(fig, left=sht.range(4,11).left, top=sht.range(4,11).top)
    sht.pictures.add(fig2, left=sht.range(28,11).left, top=sht.range(28,11).top)

  # 書式設定・表タイトル記入
  if True:
    # 列幅調整
    sht.range(1,1).column_width = 18  # A:DATE_TIME
    sht.range(1,2).column_width = 6   # B:ALARM No
    sht.range(1,3).column_width = 24  # C:MESSAGE
    sht.range(1,4).column_width = 5   # D:(空白列)
    sht.range(1,5).column_width = 11  # E:DATE
    sht.range(1,6).column_width = 6   # F:COUNT
    sht.range(1,7).column_width = 5   # G:(空白列)
    sht.range(1,8).column_width = 24  # H:MESSAGE
    sht.range(1,9).column_width = 6   # I:ALARM No
    sht.range(1,10).column_width = 5  # J:(空白行)
    # カラム名変更
    sht.range(4,1).value = '日付時間'
    sht.range(4,2).value = 'AlmNo'
    sht.range(4,3).value = 'アラーム名称'
    sht.range(4,5).value = '日付'
    sht.range(4,6).value = '回数'
    sht.range(4,8).value = 'アラーム名称'
    sht.range(4,9).value = '合計'
    
    # 表タイトル行への罫線設定(上下中太)&中央揃え
    target_ranges = [sht.range((4,1),(4,3)),
                    sht.range((4,5),(4,6)),
                    sht.range((4,8),(4,9))]
    for rg in target_ranges:
      rg.api.Borders(xlconst.XLEDGETOP).LineStyle = xlconst.XLCONTINUOUS
      rg.api.Borders(xlconst.XLEDGETOP).Weight = xlconst.XLMEDIUM
      rg.api.Borders(xlconst.XLEDGEBOTTOM).LineStyle = xlconst.XLCONTINUOUS
      rg.api.Borders(xlconst.XLEDGEBOTTOM).Weight = xlconst.XLMEDIUM
      rg.api.HorizontalAlignment = xlconst.XLHALIGNCENTER #中央揃え

    # シートタイトル・表タイトル記入
    # (注:str(int(mc_no))でゼロサプレスになる)
    sht.range(1,1).value = \
      f'{str(int(mc_no))}号機 異常発生データ({yearMonthLst[0]}年{yearMonthLst[1]}月)'
    sht.range(1,1).api.Font.Size = 18
    sht.range(1,1).api.Font.Bold = True
    sht.range(3,1).value = '1.全異常データ'
    sht.range(3,1).api.Font.Size = 14
    sht.range(3,5).value = '2.日別発生回数'
    sht.range(3,5).api.Font.Size = 14
    sht.range(3,8).value = '3.異常毎の発生回数'
    sht.range(3,8).api.Font.Size = 14

    # CSVファイル名からデータ取得日記入
    time_stamp = os.path.basename(csv_path)
    tsYear = '20' + time_stamp[11:13]
    tsMonth = time_stamp[13:15]
    tsDay = time_stamp[15:17]
    tsHour = time_stamp[17:19]
    tsMinute = time_stamp[19:21]
    tsSecond = time_stamp[21:23]
    strTimeStamp = f'データ取得日：{tsYear}/{tsMonth}/{tsDay}' +\
                   f' {tsHour}:{tsMinute}:{tsSecond}'
    sht.range(2,1).value = strTimeStamp

    # アラーム別集計表 最終行(合計)の書式設定
    sum_alm = grouped.sum()
    # 最終行取得
    last_row = sht.range('H4').end('down').row
    print(f'last_row={last_row}')
    sht.range(last_row+1,8).value = '合計'
    sht.range(last_row+1,9).value = sum_alm
    ranges = sht.range((last_row+1,8),(last_row+1,9))
    ranges.api.HorizontalAlignment = xlconst.XLHALIGNRIGHT
    ranges.api.Borders(xlconst.XLEDGETOP).LineStyle = xlconst.XLCONTINUOUS
    ranges.api.Borders(xlconst.XLEDGETOP).Weight = xlconst.XLTHIN

#---<関数定義ここまで>--------------

#=== MainLoop ======================================================


# 集計対象年月の入力(yearMonthLstリストへの格納) ----------------------
while True:
  # アラーム履歴ファイルの統合処理(別モジュール)
  BindAlmData.bind_alm_data()
  
  # (データの絞り込みと記録用エクセルファイルオープン処理に使用する)
  res = input("集計対象年月を「year-month」形式で入力して下さい : ")
  yearMonthLst = res.split("-")
  # print(f"集計年月＝{yearMonthLst[0]}年-{yearMonthLst[1]}月")   # ForDebug
  if yearMonthLst[0].isdecimal() and yearMonthLst[1].isdecimal():
    yearMonthLst[1] = yearMonthLst[1].zfill(2)  #ゼロパディング(2桁)
    break
  else:
    print('入力値が不正です。再入力して下さい')
    continue


# 対象機械番号(mc_no)の入力待ち -----------------------------------
while True:
  mc_no = input('機械番号を入力してください(開始No-終了Noの範囲指定) : ')
  if '-' in mc_no:
    temp_list = mc_no.split('-')
    mc_no_from = temp_list[0]
    mc_no_to = temp_list[1]
  else:
    mc_no_from = mc_no
    mc_no_to = mc_no

  # 入力値チェック(整数のみOK)(isdeximalメソッドはMEMO欄参照)
  if (mc_no_from.isdecimal()) and (mc_no_to.isdecimal()):
    mc_no_from = int(mc_no_from)
    mc_no_to = int(mc_no_to)
    if mc_no_from>mc_no_to:
      print('範囲指定が不正です。')
      continue
  else:
    print('数値データ(整数)を入力してください')
    continue

  print(mc_no_from,mc_no_to,sep='/')
  # メインプロシージャ繰り返し処理
  for s in range(mc_no_from,mc_no_to+1):
    MainProc(s)

  ret = input('処理を継続しますか？(Yes=y)')
  if ret=='y':
    continue
  else:
    break

ret = input('エクセルシートの並べ替えしますか？(Yes=y)')
if ret=='y':
  print('シート並べ替えします')
  xlSheetRearrange.xl_sheet_rearrange(xl_path)

print('プログラム終了')
input()

'''
----- MEMO ----------------------------------------------------------
【isdecimalメソッド解説】
→ https://www.javadrive.jp/python/string/index14.html

【pandasのplotメソッドでグラフを作成しデータを可視化】
→ https://note.nkmk.me/python-pandas-plot/

【XlwingsでMatplotlibのグラフ貼り付け（公式）】
→ https://docs.xlwings.org/ja/latest/matplotlib.html

【xlwing 書式設定＆罫線処理】
→ https://posipochi.com/2021/06/08/python-xlwings-range/#toc6

・編集するエクセルファイルは開いたままでも正常に動作する

・タッチパネルのシステム設定で日時の表現が「年/日/月」の順になる
  可能性があるので注意する(エラーが発生する)

《残作業》

《更新履歴》
 2023/1/9 Ver1.01
 → アラームごとの集計表の最終行に合計の行を追加




'''
