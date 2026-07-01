import json
from pathlib import Path
import gspread
from gspread.utils import a1_to_rowcol, rowcol_to_a1
from datetime import datetime, timedelta
import time
# original modules
from common_lib_mw import kv_com as kv
import db

#--- CONSTANTS --------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "machine_config.json"

SERVICE_ACCOUNT_FILE = BASE_DIR / "secrets" / "mitsuwa-mainfactory.json"
# SPREADSHEET_NAME = "光和工業 本社工場稼動モニタ"
SPREADSHEET_ID = "1lhgBJKB921__GgqreES7som-YchP-MikzS_Gq1ERsUM"

STATUS_NAME = {
    1: "刃具交換",
    2: "段替え",
    3: "故障停止",
    4: "材料切れ",
    15: "自動中",
    16: "停止中",
    20: "異常中"
}

# 色をコードから変更する場合に使用する予定(現在は未使用)
STATUS_INFO = {
    1: {
        "name": "刃具交換",
        "bg_color": "yellow",
    },

    2: {
        "name": "段替え",
        "bg_color": "yellow",
    },

    3: {
        "name": "故障停止",
        "bg_color": "pink",
    },

    4: {
        "name": "材料切れ",
        "bg_color": "light_blue",
    },

    15: {
        "name": "自動中",
        "bg_color": "green",
    },

    16: {
        "name": "停止中",
        "bg_color": "white",
    },

    20: {
        "name": "異常中",
        "bg_color": "pink",
    }
}

#--- GLOBAL VARIABLES -------------------------------------
config = {}


#--- FUNCTIONS --------------------------------------------
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def connect_gspread():
    client = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet


def get_status_cell(start_cell: str) -> str:
    row, col = a1_to_rowcol(start_cell)
    status_col = col + 2    # ステータスのセルは開始位置から+2列目
    return rowcol_to_a1(row, status_col)


def update_gspread(data:dict):
    # debug_dump(data)

    spreadsheet = connect_gspread()
    sht = spreadsheet.worksheet("RealtimeTable")

    update_list = []

    production_date = get_production_date()

    for mc_no, result in data.items():
        machine = config["machines"][mc_no]

        if not machine["enable"]:
            continue

        start_cell = machine["spreadsheet_position"]

        status_info = STATUS_INFO.get(
            result["status"],
            {"name": "不明", "bg_color": "white"}
        )
        status_name = status_info["name"]

        passive_operating_rate = db.get_1day_column_value(
            machine_no=int(mc_no),
            puroduction_date=production_date,
            column_name="passive_operating_rate"
        )

        active_operating_rate = db.get_1day_column_value(
            machine_no=int(mc_no),
            puroduction_date=production_date,
            column_name="active_operating_rate"
        )

        values = [[
            f"MC{mc_no}",
            machine["name"],
            status_name,
            result["actual_count"],
            result["target_count"],
            result["alarm_count"],
            passive_operating_rate,
            active_operating_rate,
        ]]

        update_list.append({
            "range": start_cell,
            "values": values,
        })

        # 将来的にはセル色を変更するプログラム追加予定

    # 更新日時
    update_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    update_list.append({
        "range": "V1",
        "values": [[update_time]]
    })

    # debug_dump(update_list)
    sht.batch_update(update_list)


def get_production_date() -> str:
    """生産日付を取得する

    4:00～翌日3:59までを同じ日付として扱う
    例:
        2026-07-01 03:59 -> 2026-06-30
        2026-07-01 04:00 -> 2026-07-01
    """
    now = datetime.now()

    if now.hour < 4:
        now = now - timedelta(days=1)
    
    return now.strftime("%Y-%m-%d")


def read_realtime_data_from_plc(config) -> dict:
    """ リアルタイムデータをPLCから取得
        (対象データ:現ステータス、生産数、アラーム数)
    """
    plc_ip_add = config["master_plc"]["ip_address"]
    # print(plc_ip_add)

    # 機械ごとの情報をPLCから受信
    machine_results = {}
    for mc_no, machine in config["machines"].items():
        print(f"---MC{mc_no} : Downloading from PLC ---")
        status = int(kv.read_device_u(plc_ip_add, machine["status_device"]))
        actual_count = int(kv.read_device_u(plc_ip_add, machine["actual_count_device"]))
        target_count = int(kv.read_device_u(plc_ip_add, machine["target_count_device"]))
        alarm_count = int(kv.read_device_u(plc_ip_add, machine["alarm_count_device"]))

        machine_results[mc_no] = {
            "status": status,
            "actual_count": actual_count,
            "target_count": target_count,
            "alarm_count": alarm_count
        }

    return machine_results


def debug_dump(data):
    print(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )
    )


def log(msg: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_file = BASE_DIR / "log.txt"

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{now} {msg}\n")


def read_1day_data_from_plc(config, mc_no: int) -> list[int]:
    """ 1台1日分の全データ(1500デバイス)を取得 """
    plc_ip_add = config["master_plc"]["ip_address"]

    # 機械ごとの設定情報取得(machine_config.json参照)
    machine = config["machines"][str(mc_no)]

    # ブロックデータ受信(ZF/各設備1500個ずつ)
    block_start_device = machine["block_start_device"]
    block_data = kv.read_devices_u(plc_ip_add, block_start_device, 1500)

    # 一時データ受信(DM20000/各設備60個ずつ)
    temp_start_device = machine["temp_start_device"]
    temp_data = kv.read_devices_u(plc_ip_add, temp_start_device, 60)

    # block_dataとtemp_data結合
    block_data = unite_block_and_temp(block_data, temp_data)

    return block_data


def unite_block_and_temp(block_data: list[int], temp_data: list[int]) -> list[int]:
    """ ブロックデータ(1500個)とテンポラリデータ(60個)の統合処理 """
    # データチェック(個数のみ) 
    if len(block_data)!=1500 or len(temp_data)!=60:
       raise ValueError(f"データサイズが不正です")
    
    # index=10〜1449 が 4:00からの1分ごとの稼働データ 1440個
    invalid_pos = None

    for i in range(10,1450):
        if block_data[i] == 0:
            invalid_pos = i
            print(f"--- (invalid data position = {invalid_pos} / data replaced)")   # ForDebug
            break

    # 無効データ位置からtemp_dataに置き換える
    if invalid_pos is not None:
        replace_end = min(invalid_pos + 60, 1450)
        replace_count = replace_end - invalid_pos

        block_data[invalid_pos:replace_end] = temp_data[:replace_count]

    return block_data


def add_status_data_to_db(config):
    """PLCの1日稼働データ(1500個)を受信し、DBへ登録する
        (machine_config.jsonに記載がある全設備が対象)
    """

    db.create_table()

    for mc_no, machine in config["machines"].items():

        if not machine.get("enable", False):
            print(f"--- MC{mc_no}: skipped(enable=false) ---")
            continue

        if "block_start_device" not in machine:
            print(f"--- MC{mc_no}: block_start_device未設定のためスキップ ---")
            continue

        if "temp_start_device" not in machine:
            print(f"--- MC{mc_no}: temp_start_device未設定のためスキップ ---")
            continue

        try:
            print(f"--- MC{mc_no}: 1日稼働データ取得開始 ---")

            data_1day = read_1day_data_from_plc(config, int(mc_no))

            db.insert_1day_data(
                machine_no=int(mc_no),
                data=data_1day
            )

            print(f"--- MC{mc_no}: DB保存完了")
        
        except Exception as e:
            print(f"ERROR MC{mc_no}: {e}")
            log(f"ERROR MC{mc_no}: {e}")

    # db.check_data()   # ForDebug


def main():
    global config
    config = load_config()

    # addstatus_data_to_db実行タイミング管理用
    DB_PROCESS_INTERVAL = 10
    process_counter = DB_PROCESS_INTERVAL   # 起動時実施


    while True:
        try:
            data = read_realtime_data_from_plc(config)
            # debug_dump(data)

            print('--- updating SpreadSheet ---')
            update_gspread(data)

            if process_counter >= DB_PROCESS_INTERVAL:
                add_status_data_to_db(config)
                process_counter = 0


            process_counter += 1
            print(f"process_counter = {process_counter}")

        except Exception as e:
            print(f"ERROR: {e}")
            log(str(e))

        print("--- waiting 5 sec ---")
        time.sleep(5)
    

if __name__ == "__main__":
    main()