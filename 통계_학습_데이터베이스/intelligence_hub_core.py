import csv
import json
import os
from datetime import datetime

# 데이터 경로 정의
STATS_DB_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\통계_학습_데이터베이스\unicity_cumulative_stats.json"
TEMP_COLLECTION_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\일시적_수집_데이터\temp_market_data.csv"
MASTER_DB_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\세대_등급_시스템\유니시티_전세대_등급_마스터.csv"

class IntelligenceHub:
    def __init__(self):
        self.stats = self.load_stats()
        self.init_temp_collection()

    def load_stats(self):
        if os.path.exists(STATS_DB_PATH):
            with open(STATS_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "last_updated": "",
            "total_records": 0,
            "grade_distribution": {}, # S, A, B 등 등급별 통계
            "price_trends": [],       # 등급별 가격 추이 기록
            "learning_log": []        # 학습된 지식/패턴 목록
        }

    def init_temp_collection(self):
        if not os.path.exists(TEMP_COLLECTION_PATH):
            os.makedirs(os.path.dirname(TEMP_COLLECTION_PATH), exist_ok=True)
            with open(TEMP_COLLECTION_PATH, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Category", "Key", "Value", "Source", "Reliability"])

    def collect_raw_data(self, category, key, value, source, reliability=10):
        """일시적으로 수집 가능한 조각 정보들을 먼저 저장함 (이실장, 광고매물, 구두정보 등)"""
        with open(TEMP_COLLECTION_PATH, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), category, key, value, source, reliability])
        print(f"✅ 일시적 데이터 수집 완료: [{category}] {key} = {value}")

    def update_learning_stats(self):
        """수집된 기초 데이터를 바탕으로 통계치를 학습하고 누적함"""
        # 마스터 DB의 6,100세대 등급 분석 결과를 기반으로 통계 초기화
        if os.path.exists(MASTER_DB_PATH):
            grades = {}
            with open(MASTER_DB_PATH, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    g = row['Total_Grade']
                    grades[g] = grades.get(g, 0) + 1
            self.stats["grade_distribution"] = grades
            self.stats["total_records"] = sum(grades.values())
        
        self.stats["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_stats()

    def save_stats(self):
        with open(STATS_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    hub = IntelligenceHub()
    hub.update_learning_stats()
    # 예시 수집: 이실장 데이터 기반 정보
    hub.collect_raw_data("Market", "3단지 84타입 자가비율", "65%", "이실장_유료분석", 9)
    hub.collect_raw_data("Seller_Context", "307동 4004호 중도금일정", "5월말 5억", "사용자입력", 10)
