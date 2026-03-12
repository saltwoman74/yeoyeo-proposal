import csv
import os

class MarketDataHub:
    def __init__(self):
        self.master_csv = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\세대_등급_시스템\유니시티_전세대_등급_마스터.csv"
        self.market_file = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\시장_데이터_허브\유니시티_실거래_및_광고매물.csv"

        if not os.path.exists(self.market_file):
            self.init_market_file()

    def init_market_file(self):
        os.makedirs(os.path.dirname(self.market_file), exist_ok=True)
        with open(self.market_file, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Complex", "Dong", "Ho", "Floor", "Price", "Type", "Status", "Grade", "Sources"])

    def record_market_event(self, date, complex_id, dong, ho, floor, price, event_type, status, grade, sources=""):
        """실거래가 또는 광고 매물을 기록하여 시장 데이터를 축적함."""
        with open(self.market_file, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([date, complex_id, dong, ho, floor, price, event_type, status, grade, sources])

    def get_comparables(self, grade, complex_id=None):
        """동일 등급 또는 유사 등급의 거래/매물 데이터를 추출하여 비교 분석함."""
        comparables = []
        if os.path.exists(self.market_file):
            with open(self.market_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Grade'] == grade:
                        if complex_id is None or row['Complex'] == complex_id:
                            comparables.append(row)
        return comparables

if __name__ == "__main__":
    hub = MarketDataHub()
    # 3단지 S등급 실거래/매물 예시 데이터 입력
    hub.record_market_event("2026-03-01", "3단지", "304동", "4102호", 41, 1060000000, "실거래", "계약완료", "S", "국토부실거래가")
    hub.record_market_event("2026-02-28", "3단지", "305동", "4203호", 42, 1100000000, "광고매물", "진행중", "S", "네이버부동산")
    print("시장 데이터 기록 및 비교 로직 가동 완료.")
