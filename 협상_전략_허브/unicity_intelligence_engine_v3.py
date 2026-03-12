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

# 전략 문서 (Phase 1-4)
STRATEGY_FILES = {
    "holding_cost": os.path.join(BRAIN_DIR, "holding_cost_analysis.md"),
    "starfield": os.path.join(BRAIN_DIR, "starfield_market_impact_source.md"),
    "school": os.path.join(BRAIN_DIR, "educational_value_source.md"),
    "psychology": os.path.join(BRAIN_DIR, "behavioral_psychology_negotiation.md"),
    "re_psychology": os.path.join(BRAIN_DIR, "real_estate_psychology_strategy.md"),
    "macro": os.path.join(BRAIN_DIR, "regional_development_strategy.md"),
    "transaction": os.path.join(BRAIN_DIR, "transaction_dynamics_analysis.md"),
    "synergy": os.path.join(BRAIN_DIR, "commercial_synergy_map.md"),
    "commute": os.path.join(BRAIN_DIR, "education_commute_analysis.md")
}

def clean_text(text):
    if not text: return ""
    return text.replace("\n", "<br>").replace("'", "\\'").replace('"', '\\"')

def parse_complex_input(user_input):
    # Parsing Unit
    unit_match = re.search(r"(\d)단지\s*(\d+)동\s*(\d+)호", user_input)
    # Parsing Prices (Asking/Offer)
    asking_match = re.search(r"호가는\s*(\d+억\s*\d*천*)", user_input)
    offer_match = re.search(r"매수자는\s*(\d+억\s*\d*천*)", user_input)
    # Parsing Schedule
    schedule_match = re.search(r"중도금으로\s*([\w\s/]+)\s*(\d+억)", user_input)
    
    comp = unit_match.group(1) if unit_match else "1"
    dong = unit_match.group(2) if unit_match else "111"
    ho = unit_match.group(3) if unit_match else "1703"
    
    asking = asking_match.group(1) if asking_match else "미공개"
    offer = offer_match.group(1) if offer_match else "협의필요"
    
    parsed = {
        "comp": comp, "dong": dong, "ho": ho,
        "asking": asking, "offer": offer,
        "raw_input": user_input
    }
    return parsed

def get_unit_intel(comp, dong, ho):
    unit_id = f"U{comp}-{dong}-{ho}"
    intel = {"unit_id": f"{comp}단지 {dong}동 {ho}호", "type": "N/A", "area": "N/A", "cost": "N/A", "grade": "B", "floor": "N/A"}
    
    # 1. 마스터 DB에서 상세 정보 추출
    if os.path.exists(MASTER_DB):
        with open(MASTER_DB, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Unit_ID") == unit_id:
                    intel["type"] = f"{row.get('Pyeong', 'N/A')}평형 / {row.get('Type', 'N/A')}타입"
                    intel["area"] = f"{row.get('Net Area', 'N/A')}㎡"
                    intel["cost"] = f"{row.get('Base Price', 'N/A')}0,000 KRW" # 기초가
                    intel["full_cost"] = f"{row.get('Total Acquisition Cost', 'N/A')}0,000 KRW"
                    intel["floor"] = row.get("Floor", "N/A")
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

def generate_master_dossier(user_narrative):
    # 1. 파싱
    data = parse_complex_input(user_narrative)
    comp, dong, ho = data['comp'], data['dong'], data['ho']
    
    # 2. 데이터 수집
    unit_intel = get_unit_intel(comp, dong, ho)
    
    # 3. 전략 데이터 읽기 (학습 결과 전체 통합)
    strategies = {}
    for key, path in STRATEGY_FILES.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                strategies[key] = f.read()
        else:
            strategies[key] = "Data not found."

    # 4. 템플릿 로드
    if not os.path.exists(REPORT_TEMPLATE):
        print("Error: Template not found.")
        return
        
    with open(REPORT_TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()
    # Part 1: All Unit ID Occurrences
    html = html.replace('U1-111-1904 (1단지 111동 1904호)', f'{unit_intel["unit_id"]}')
    html = re.sub(r'id="unit-id" contenteditable="true">[^<]+', f'id="unit-id" contenteditable="true">{unit_intel["unit_id"]}', html)
    html = re.sub(r'id="unit-type" contenteditable="true">[^<]+', f'id="unit-type" contenteditable="true">{unit_intel["type"]} ({unit_intel["floor"]}층)', html)
    html = re.sub(r'id="unit-area" contenteditable="true">[^<]+', f'id="unit-area" contenteditable="true">{unit_intel["area"]}', html)
    html = re.sub(r'id="unit-grade" contenteditable="true">[^<]+', f'id="unit-grade" contenteditable="true">{unit_intel["grade"]} Grade', html)
    html = re.sub(r'id="unit-cost" contenteditable="true">[^<]+', f'id="unit-cost" contenteditable="true">{unit_intel["full_cost"]}', html)
    
    # User Notes & Specific Context
    negotiation_context = f"<b>사용자 관찰</b>: {user_narrative}<br><br><b>분석 포인트</b>: 도배 및 에어컨 청소비용(약 300-500만원 예상)을 '앵커링' 가격에서 선제적으로 차감 제안 필요."
    html = html.replace('(여기에 사용자가 직접 습득한 현장 내용을 입력하세요. 예: 거실 조망 간섭 없음, 안방 결로 자국 확인 등)', negotiation_context)

    # Proposals Injection (v3 logic)
    html = html.replace('14.2억 ~ 14.5억', data['offer'])
    html = html.replace('14.8억 ~ 15.2억', data['asking'])
    
    # Strategic Appendix (Append at bottom)
    appendix_html = "<div class='report-page'><header><div class='header-title'><h1>STRATEGIC ASSETS APPENDIX</h1><p>COLLECTED KNOWLEDGE BASE</p></div></header>"
    for key, content in strategies.items():
        clean_content = clean_text(content[:2000]) # 2000자 제한
        appendix_html += f"<div class='section'><div class='section-title'>{key.upper()} ANALYSIS</div><div class='content-block'>{clean_content}...</div></div>"
    appendix_html += "</div>"
    
    html = html.replace("</body>", f"{appendix_html}</body>")

    # 6. 파일 저장
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    output_path = os.path.join(OUTPUT_DIR, f"Master_Dossier_{comp}_{dong}_{ho}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Success: Master Dossier generated at -> {output_path}")
    return output_path

if __name__ == "__main__":
    narrative = sys.argv[1] if len(sys.argv) > 1 else "111동 1703호 도배 새로 해야겠고 광고호가 9.8억 매수자 9.6억 하겠다함"
    generate_master_dossier(narrative)
