import sqlite3
import struct
from datetime import datetime
from pathlib import Path
# original modules
from common_lib_mw import kv_com as kv

# ----- CONSTANTS -----------------------------------------
# 開発時
# DB_PATH = Path(__file__).resolve().parent / "main_factory_production_data.db"
# 運用時
DB_PATH = Path(r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl\operation_data\main_factory_production_data.db")


# DBカラム定義
# key: カラム名
# value: SQLite型
OPERATION_DATA_COLUMNS = {
    "machine_no": "INTEGER",
    "update_at": "TEXT",
    "production_date": "TEXT",
    "actual_production": "INTEGER",
    "target_production": "INTEGER",
    "alarm_number": "INTEGER",
    "all_auto_time": "INTEGER",
    "regular_auto_time": "INTEGER",
    "regular_material_out_time": "INTEGER",
    "passive_operating_rate": "REAL",
    "active_operating_rate": "REAL",
    "all_data": "BLOB",
}

# PLC状態コード
STATUS_CODE = {
    "NO_DATA": 0,       # データなし
    "TOOL_CHANGE": 1,   # 刃具交換
    "CHANGEOVER": 2,    # 段替え
    "BREAKDOWN": 3,     # 故障
    "MATERIAL_OUT": 4,  # 材料切れ
    "AUTO": 15,         # 自動
    "STOP": 16,         # 停止
    "ALARM": 20,        # アラーム
}


# ----- FUNCTIONS -----------------------------------------
def create_table():
    """テーブル作成"""

    columns_sql = ",\n".join(
        f"{column_name} {column_type}"
        for column_name, column_type in OPERATION_DATA_COLUMNS.items()
    )

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS operation_data (
                id INTEGER PRIMARY KEY,
                {columns_sql},
                UNIQUE(machine_no, production_date)
            )
        """)

        conn.commit()

def list_to_blob(data: list[int]) -> bytes:
    """list[int] → BLOB用bytes"""
    if len(data) != 1500:
        raise ValueError("dataは1500個である必要があります")
    
    return struct.pack("<1500H", *data)


def blob_to_list(blob_data: bytes) -> list[int]:
    """BLOB用bytes → list[int]"""
    return list(struct.unpack("<1500H", blob_data))


def insert_1day_data(machine_no: int, data: list[int]):
    """PLC 1日分データを追加・更新"""

    update_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary = calc_operation_summary(data)

    record = {
        "machine_no": machine_no,
        "update_at": update_at,
        **summary,
        "all_data": list_to_blob(data),
    }

    columns = list(OPERATION_DATA_COLUMNS.keys())

    column_sql = ", ".join(columns)

    placeholder_sql = ", ".join(f":{c}" for c in columns)

    update_sql = ", ".join(
        f"{c}=excluded.{c}"
        for c in columns
        if c not in ("machine_no", "production_date")
    )

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute(f"""
            INSERT INTO operation_data (
                {column_sql}
            )
            VALUES (
                {placeholder_sql}
            )
            ON CONFLICT(machine_no, production_date)
            DO UPDATE SET
                {update_sql}
        """, record)

        conn.commit()


def check_data():
    """保存データ確認"""

    columns = list(OPERATION_DATA_COLUMNS.keys())
    column_sql = ", ".join(columns)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(f"""
            SELECT
                id,
                {column_sql}
            FROM operation_data
            ORDER BY update_at DESC
        """)

        rows = cur.fetchall()

    for row in rows:
        data = blob_to_list(row["all_data"])

        print("id:", row["id"])
        print("machine_no:", row["machine_no"])
        print("update_at:", row["update_at"])
        print("production_date:", row["production_date"])
        print("actual_production:", row["actual_production"])
        print("target_production:", row["target_production"])
        print("alarm_number:", row["alarm_number"])
        print("all_auto_time:", row["all_auto_time"])
        print("regular_auto_time:", row["regular_auto_time"])
        print("regular_material_out_time:", row["regular_material_out_time"])
        print("passive_operating_rate:", row["passive_operating_rate"])
        print("active_operating_rate:", row["active_operating_rate"])
        print("data数:", len(data))
        print("先頭20個:", data[:20])
        print("-" * 40)



def calc_operation_summary(data: list[int]) -> dict:
    """1日分の機械状態データ(1500個)から各種稼働データを算出

    Args:
        data (list[int]):
            index=0    : YYMMDD形式日付(下位)
            index=1    : YYMMDD形式日付(上位)
            index=2    : 生産数
            index=3    : アラーム数

            1分ごとの機械状態データ（1440個）
            index=10   : 4:00
            index=250  : 8:00
            index=790  : 17:00
            index=1449 : 翌日3:59

            ※上記以外の要素は未使用(値は0)

    Returns:
        dict:
            {
                "production_date": "YYYY-MM-DD"[str],
                "actual_production": xxx[int],
                "target_production": xxx[int],
                "alarm_number: xxx[int],
                "all_auto_time": xxx[int],
                "regular_auto_time": xxx[int],
                "regular_material_out_time": xxx[int],
                "passive_operating_rate": xxx[float],
                "active_operating_rate": xxx[float]
            }
    """
    if len(data) != 1500:
        raise ValueError("dataが1500個ではありません")

    # 全範囲(24h)
    # index=10   : 4:00
    # index=1449 : 翌日3:59
    STATUS_START = 10
    STATUS_END = 1450

    # 定時範囲 8:00～17:00(9h)
    REGULAR_START = STATUS_START + 4 * 60     # index=250
    REGULAR_END = STATUS_START + 13 * 60      # index=790（17:00含まず）

    # 8:00～17:00の分単位時間
    REGULAR_TIME = 60 * 9

    all_status_data = data[STATUS_START:STATUS_END]
    regular_data = data[REGULAR_START:REGULAR_END]

    result = {}

    plc_date = kv.join_u16_to_u32(data[1], data[0])
    result["production_date"] = kv.decode_plc_date(plc_date)

    result["actual_production"] = data[2]
    result["alarm_number"] = data[3]
    result["target_production"] = data[4]

    result["all_auto_time"] = all_status_data.count(STATUS_CODE["AUTO"])

    result["regular_auto_time"] = regular_data.count(STATUS_CODE["AUTO"])
    result["regular_material_out_time"] = regular_data.count(STATUS_CODE["MATERIAL_OUT"])

    passive_auto_time = (
        result["regular_auto_time"]
        + result["regular_material_out_time"]
    )

    result["passive_operating_rate"] = passive_auto_time / REGULAR_TIME * 100
    result["active_operating_rate"] = result["regular_auto_time"] / REGULAR_TIME * 100

    return result


def get_1day_column_value(
        machine_no: int,
        puroduction_date: str,
        column_name: str
):
    """指定した機械番号・日付・カラム名の値を取得する

    Args:
        machine_no (int): 機械番号
        production_date (str): 生産日付（YYYY-MM-DD）
        column_name (str): 取得したいカラム名

    Returns:
        指定カラムの値
        SQLiteに保存されている型に応じて返る
        INTEGER -> int
        REAL    -> float
        TEXT    -> str
        BLOB    -> bytes

        データが存在しない場合は None
    """

    if column_name not in OPERATION_DATA_COLUMNS:
        raise ValueError(f"存在しないカラム名です: {column_name}")
    
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute(f"""
            SELECT
                {column_name}
            FROM operation_data
            WHERE machine_no = ?
              AND production_date = ?
                 
        """, (machine_no, puroduction_date))

        row = cur.fetchone()

    if row is None:
        return None
    
    return row[0]
    

if __name__ == "__main__":

    create_table()

    # Create Sample Data
    import random
    data = [random.randint(1,20) for i in range(1500)]
    data[0] = 64020
    data[1] = 3

    insert_1day_data(machine_no=1, data=data)

    check_data()
