import json
from pathlib import Path
import gspread
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
    3: "故障中",
    4: "材料待ち",
    13: "自動中",
    14: "停止中",
    15: "異常中"
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


def update_gspread(data:dict):
    spreadsheet = connect_gspread()
    sht = spreadsheet.worksheet("シート1")

    update_list = []

    for mc_no, result in data.items():
        machine = config["machines"][mc_no]

        if not machine["enable"]:
            continue

        start_cell = machine["spreadsheet_position"]

        status_name = STATUS_NAME.get(result["status"], "不明")

        values = [[
            f"MC{mc_no}",
            status_name,
            result["actual_count"],
            result["target_count"],
            result["alarm_count"]
        ]]

        update_list.append({
            "range": start_cell,
            "values": values,
        })

    print(update_list)
    sht.batch_update(update_list)


def read_data_from_plc(config) -> dict:
    plc_ip_add = config["master_plc"]["ip_address"]
    # print(plc_ip_add)

    # 機械ごとの情報をPLCから受信
    machine_results = {}
    for mc_no, machine in config["machines"].items():
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


def main():
    global config
    config = load_config()

    data = read_data_from_plc(config)
    print(data)

    update_gspread(data)
    

if __name__ == "__main__":
    main()