import csv
import os
from datetime import datetime

TRANS_DB_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\실거래_이력_데이터베이스\unicity_transaction_history.csv"

def init_trans_db():
    if not os.path.exists(TRANS_DB_PATH):
        os.makedirs(os.path.dirname(TRANS_DB_PATH), exist_ok=True)
        with open(TRANS_DB_PATH, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Trade_Date", "Unit_ID", "Complex", "Dong", "Ho", "Floor", "Price_TenWork", "Trade_Type", "Source"])

def record_trade(date, unit_id, complex_id, dong, ho, floor, price, trade_type="매매", source="국토부"):
    init_trans_db()
    with open(TRANS_DB_PATH, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([date, unit_id, complex_id, dong, ho, floor, price, trade_type, source])
    print(f"✔️ 실거래 기록 완료: {unit_id} ({date} / {price}만)")

if __name__ == "__main__":
    # 샘플 데이터 기록 (검색 결과 반영)
    record_trade("2025-11-08", "U3-30x-2xx", "3단지", "30x동", "2xx호", 2, 63000, "매매", "국토부")
    record_trade("2026-02-15", "U1-105-2501", "1단지", "105동", "2501호", 25, 107000, "매매", "이실장")
