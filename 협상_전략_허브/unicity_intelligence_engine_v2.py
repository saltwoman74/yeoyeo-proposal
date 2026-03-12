import csv
import json
import os
import re
import sys

# 정적 경로 정의 (사용자 환경에 맞춤)
BASE_DIR = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가"
BRAIN_DIR = r"C:\Users\sango\.gemini\antigravity\brain\785fe410-8768-4826-a7ba-50d768762474"

# 데이터 소스 파일
MASTER_DB = os.path.join(BASE_DIR, "전세대_전수_데이터베이스", "유니시티_6100세대_전수_조사_마스터.csv")
GRADE_DB = os.path.join(BASE_DIR, "세대_등급_시스템", "유니시티_전세대_등급_마스터.csv")
REPORT_TEMPLATE = os.path.join(BASE_DIR, "협상_전략_허브", "통합_유니시티_지능형_보고서_양식.html")
OUTPUT_DIR = os.path.join(BASE_DIR, "협상_전략_허브", "출력된_통합_보고서")

# 전략 문서 (Phase 1-3)
STRATEGY_FILES = {
    "holding_cost": os.path.join(BRAIN_DIR, "holding_cost_analysis.md"),
    "starfield": os.path.join(BRAIN_DIR, "starfield_market_impact_source.md"),
    "school": os.path.join(BRAIN_DIR, "educational_value_source.md"),
    "psychology": os.path.join(BRAIN_DIR, "behavioral_psychology_negotiation.md"),
    "macro": os.path.join(BRAIN_DIR, "regional_development_strategy.md")
}

def clean_text(text):
    # HTML에 삽입하기 위해 기본적인 클리닝 (Markdown -> HTML 변환은 생략하고 텍스트 위주)
    if not text: return ""
    return text.replace("\n", "<br>").replace("'", "\\'").replace('"', '\\"')

def get_unit_intel(comp, dong, ho):
    unit_id = f"U{comp}-{dong}-{ho}"
    intel = {"unit_id": f"{comp}단지 {dong}동 {ho}호", "type": "N/A", "area": "N/A", "cost": "N/A", "grade": "B"}
    
    # 1. 마스터 DB에서 상세 정보 추출
    if os.path.exists(MASTER_DB):
        with open(MASTER_DB, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Unit_ID") == unit_id:
                    intel["type"] = f"{row.get('Pyeong', 'N/A')}평형 / {row.get('Type', 'N/A')}타입"
                    intel["area"] = f"{row.get('Net Area', 'N/A')}㎡"
                    intel["cost"] = f"{row.get('Total Acquisition Cost', 'N/A')}0,000 KRW" # 단위 보정
                    break
    
    # 2. 등급 DB에서 등급 추출
    if os.path.exists(GRADE_DB):
        with open(GRADE_DB, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Unit_ID") == unit_id:
                    intel["grade"] = row.get("Total_Grade", "B")
                    break
                    
    return intel

def generate_full_report(unit_id_str, user_observations=""):
    # 1. 입력 파싱
    match = re.search(r"(\d)단지\s*(\d+)동\s*(\d+)호", unit_id_str)
    if not match:
        print(f"Error: Invalid Unit Input Format: {unit_id_str}")
        return
    comp, dong, ho = match.groups()
    
    # 2. 데이터 수집
    unit_intel = get_unit_intel(comp, dong, ho)
    
    # 3. 전략 데이터 읽기 (전부 통합하여 학습 결과 반영 느낌)
    strategies = {}
    for key, path in STRATEGY_FILES.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # 간단한 정제를 통해 보고서 하단에 넣을 준비
                # (현 단계에서는 HTML 인젝션용으로만 간단히 처리)
                strategies[key] = clean_text(content[:1000] + "...") # 요약본 느낌
        else:
            strategies[key] = "Data not found."

    # 4. 템플릿 로드 및 인젝션
    if not os.path.exists(REPORT_TEMPLATE):
        print("Error: Template not found.")
        return
        
    with open(REPORT_TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()

    # 데이터 치환 (re.sub 또는 replace 활용)
    # Part 1: Unit Intel - Using regex to find the ID span or replacing the specific default
    html = re.sub(r'id="unit-id" contenteditable="true">[^<]+', f'id="unit-id" contenteditable="true">{unit_intel["unit_id"]}', html)
    html = re.sub(r'id="unit-type" contenteditable="true">[^<]+', f'id="unit-type" contenteditable="true">{unit_intel["type"]}', html)
    html = re.sub(r'id="unit-area" contenteditable="true">[^<]+', f'id="unit-area" contenteditable="true">{unit_intel["area"]}', html)
    html = re.sub(r'id="unit-grade" contenteditable="true">[^<]+', f'id="unit-grade" contenteditable="true">{unit_intel["grade"]} Grade', html)
    html = re.sub(r'id="unit-cost" contenteditable="true">[^<]+', f'id="unit-cost" contenteditable="true">{unit_intel["cost"]}', html)
    
    # Part 3: User Observations
    if user_observations:
        html = html.replace('(여기에 사용자가 직접 습득한 현장 내용을 입력하세요. 예: 거실 조망 간섭 없음, 안방 결로 자국 확인 등)', user_observations)

    # 5. 파일 저장
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    output_path = os.path.join(OUTPUT_DIR, f"Comprehensive_Report_{comp}_{dong}_{ho}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Success: Full Intelligence Report generated at -> {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) > 2:
        target = sys.argv[1]
        obs = " ".join(sys.argv[2:])
        generate_full_report(target, obs)
    elif len(sys.argv) > 1:
        generate_full_report(sys.argv[1])
    else:
        # Default test
        generate_full_report("1단지 111동 1904호", "로열층이며 전면동이라 일조가 매우 풍부함. 거실 인테리어가 매우 고급스럽게 되어 있어 추가 비용 절감이 기대됨.")
