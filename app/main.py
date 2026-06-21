import json
from pathlib import Path
import gspread
from gspread.utils import a1_to_rowcol, rowcol_to_a1
from datetime import datetime
import time
# original modules
from common_lib_mw import kv_com as kv


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
    13: "自動中",
    14: "停止中",
    15: "異常中"
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

    13: {
        "name": "自動中",
        "bg_color": "green",
    },

    14: {
        "name": "停止中",
        "bg_color": "white",
    },

    15: {
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
    spreadsheet = connect_gspread()
    sht = spreadsheet.worksheet("RealtimeTable")

    update_list = []

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

        values = [[
            f"MC{mc_no}",
            machine["name"],
            status_name,
            result["actual_count"],
            result["target_count"],
            result["alarm_count"]
        ]]

        update_list.append({
            "range": start_cell,
            "values": values,
        })

        # 将来的にはセル色を変更するプログラム追加予定

    # 更新日時
    update_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    update_list.append({
        "range": "P1",
        "values": [[update_time]]
    })

    # debug_dump(update_list)
    sht.batch_update(update_list)


def read_data_from_plc(config) -> dict:
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


def main():
    global config
    config = load_config()

    while True:
        try:
            data = read_data_from_plc(config)
            # debug_dump(data)

            print('--- updating SpreadSheet ---')
            update_gspread(data)

        except Exception as e:
            print(f"ERROR: {e}")
            log(str(e))

        print("--- waiting 5 sec ---")
        time.sleep(5)
    

if __name__ == "__main__":
    main()