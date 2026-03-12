import csv
import json
import os
import re
import sys

# 파일 경로 정의
BASE_DIR = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가"
MASTER_DB = os.path.join(BASE_DIR, "세대_등급_시스템", "유니시티_전세대_등급_마스터.csv")
VISIT_DATA = os.path.join(BASE_DIR, "분석_데이터", "세대별_현장_방문_기록.json")
TEMPLATE_PATH = os.path.join(BASE_DIR, "협상_전략_허브", "매수_협상제안서_편집용_폼.html")
OUTPUT_DIR = os.path.join(BASE_DIR, "협상_전략_허브", "생성된_제안서")

def parse_unit_input(user_input):
    complex_match = re.search(r"(\d)단지", user_input)
    dong_match = re.search(r"(\d+)동", user_input)
    ho_match = re.search(r"(\d+)호", user_input)
    
    comp = complex_match.group(1) if complex_match else None
    dong = dong_match.group(1) if dong_match else None
    ho = ho_match.group(1) if ho_match else None
    
    return comp, dong, ho

def get_unit_data(comp, dong, ho):
    unit_id = f"U{comp}-{dong}-{ho}"
    if not os.path.exists(MASTER_DB):
        return None
        
    with open(MASTER_DB, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v for k, v in row.items()}
            if row.get('Unit_ID') == unit_id:
                return row
    return None

def get_visit_notes(comp, dong, ho):
    unit_key = f"U{comp}-{dong}-{ho}"
    if os.path.exists(VISIT_DATA):
        with open(VISIT_DATA, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(unit_key, {}).get("Notes", "")
    return ""

def generate_proposal(user_input):
    comp, dong, ho = parse_unit_input(user_input)
    if not all([comp, dong, ho]):
        print(f"Error: Invalid input format. (Input: {user_input})")
        return

    unit_data = get_unit_data(comp, dong, ho)
    visit_notes = get_visit_notes(comp, dong, ho)
    
    if not unit_data:
        print(f"Warning: No master data for {comp} Complex {dong} Dong {ho} Ho. Using defaults.")
        unit_data = {"Complex": f"{comp}단지", "Dong": f"{dong}동", "Ho": f"{ho}호", "Total_Grade": "N/A"}

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Data Injection
    html = re.sub(r'id="unit-info"[^>]*>', f'id="unit-info" value="{comp}단지 {dong}동 {ho}호" style="font-weight:bold;">', html)
    html = re.sub(r'id="unit-grade"[^>]*>', f'id="unit-grade" value="{unit_data.get("Total_Grade", "B")} Grade (Auto-Generated)" >', html)
    
    if visit_notes:
        expert_content = f"- Field Notes: {visit_notes}<br>- Expert briefing: "
        html = re.sub(r'id="expert-insight" contenteditable="true">.*?</div>', 
                      f'id="expert-insight" contenteditable="true" style="min-height: 150px; background-color: #fffde7;">{expert_content}</div>', 
                      html, flags=re.DOTALL)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    output_filename = f"Proposal_{comp}_{dong}_{ho}.html"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Success: Proposal generated at -> {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_arg = " ".join(sys.argv[1:])
        generate_proposal(user_arg)
    else:
        generate_proposal("3단지 307동 4004호")
