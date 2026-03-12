import pandas as pd
import os
import json

MASTER_DB_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\세대_등급_시스템\유니시티_전세대_등급_마스터.csv"
VISIT_DATA_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\분석_데이터\세대별_현장_방문_기록.json"

def load_visit_data():
    if os.path.exists(VISIT_DATA_PATH):
        with open(VISIT_DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_visit_data(data):
    with open(VISIT_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_unit_data(complex_num, dong, ho, c_score=None, s_score=None, notes=""):
    """상태(C)와 상황(S) 점수를 직접 입력하여 데이터를 업데이트하고 리포트를 생성합니다."""
    
    if not os.path.exists(MASTER_DB_PATH):
        return "오류: 마스터 데이터가 없습니다."

    df = pd.read_csv(MASTER_DB_PATH)
    
    search_complex = f"{complex_num}단지" if "단지" not in str(complex_num) else complex_num
    search_dong = f"{dong}동" if "동" not in str(dong) else dong
    search_ho = f"{ho}호" if "호" not in str(ho) else ho
    
    unit_row = df[(df['Complex'] == search_complex) & (df['Dong'] == search_dong) & (df['Ho'] == search_ho)]
    
    if unit_row.empty:
        return f"❌ {search_complex} {search_dong} {search_ho}를 찾을 수 없습니다."

    unit_idx = unit_row.index[0]
    unit_data = unit_row.iloc[0].to_dict()
    
    # 점수 업데이트 (입력값이 있을 때만)
    if c_score is not None: unit_data['C_Score'] = float(c_score)
    if s_score is not None: unit_data['S_Score'] = float(s_score)
    
    # 종합 등급 재계산 (L: 50%, C: 30%, S: 20%)
    total_score = (unit_data['L_Score'] * 0.5) + (unit_data['C_Score'] * 0.3) + (unit_data['S_Score'] * 0.2)
    
    if total_score >= 9.2: grade = "S+"
    elif total_score >= 8.8: grade = "S"
    elif total_score >= 8.4: grade = "A+"
    elif total_score >= 8.0: grade = "A"
    elif total_score >= 7.5: grade = "B+"
    else: grade = "B"
    
    unit_data['Total_Grade'] = grade
    unit_data['Status'] = "현장분석완료"

    # 영구 저장 (방문 기록 JSON에 저장하여 마스터 데이터와 별개로 '기억' 유지)
    visits = load_visit_data()
    unit_id = unit_data['Unit_ID']
    visits[unit_id] = {
        "C_Score": unit_data['C_Score'],
        "S_Score": unit_data['S_Score'],
        "Total_Grade": grade,
        "Notes": notes,
        "Update_Date": "2026-03-04"
    }
    save_visit_data(visits)

    # 협상 가이드 생성 (3~5개)
    negotiation_guides = []
    
    # 1. 입지 기반 (L)
    if unit_data['L_Score'] >= 8.5:
        negotiation_guides.append("✔️ [희소성 강조] 본 세대는 유니시티 내에서도 상위 10% 이내의 입지 가치를 보유하고 있어, 가격 조정보다는 '물건의 희소성'을 바탕으로 거래를 주도하십시오.")
    else:
        negotiation_guides.append("✔️ [실거주 가치 강조] 입지 평점 대비 합리적인 가격대를 형성하고 있으므로, 실거주 편의성과 가성비를 중점적으로 어필하십시오.")

    # 2. 상태 기반 (C)
    if unit_data['C_Score'] >= 8.5:
        negotiation_guides.append("✔️ [추가 비용 절감] 최고 수준의 내부 관리 상태로 인해 인테리어 비용 약 3~5천만 원의 절감 효과가 있음을 강력히 피력하십시오.")
    elif unit_data['C_Score'] < 6.0:
        negotiation_guides.append("✔️ [Nego 명분 확보] 내부 상태가 다소 미흡하므로, 이를 강력한 가격 네고(Negotiation)의 명분으로 활용하여 매수인의 심리적 저항선을 낮추십시오.")

    # 3. 상황 기반 (S)
    if unit_data['S_Score'] >= 8.5:
        negotiation_guides.append("✔️ [클로징 압박] 매도인의 매매 의지가 매우 강한 '급매' 성격의 물건입니다. 빠른 의사결정이 필요함을 강조하여 즉시 계약(Closing)을 유도하십시오.")
    else:
        negotiation_guides.append("✔️ [장기전략 수립] 매도인의 심리적 저항선이 높으므로, 시간을 두고 상대방의 상황 변화를 주시하며 점진적인 가격 조율을 시도하십시오.")

    # 4. 종합 대응
    negotiation_guides.append(f"✔️ [등급 맞춤 전략] 현재 종합 {grade} 등급 물건입니다. 유사 평형대 평균 등급 대비 우위를 점하고 있음을 데이터로 시연하십시오.")
    
    # 5. 특약 제안
    negotiation_guides.append("✔️ [전문가 특약] 거주 상태와 등급을 고려하여, 잔금 일자 조절이나 옵션 승계 등 매도인/매수인 맞춤형 특약을 제안하여 계약 성사율을 높이십시오.")

    # 리포트 출력
    report = f"""
================================================================================
🏠 [현장 정밀 분석 완료] {search_complex} {search_dong} {search_ho}
================================================================================
[기초 정보]
- Unit ID: {unit_data['Unit_ID']} | 층수: {unit_data['Floor']}층
- 분석 일자: 2026-03-04 | 상태: {unit_data['Status']}

[등급 수치 (현장 방문 반영)]
- 🔵 입지 등급 (Fixed): {unit_data['L_Score']} / 10
- 🟠 상태 등급 (New):   {unit_data['C_Score']} / 10  <-- 수정됨
- 🔴 상황 등급 (New):   {unit_data['S_Score']} / 10  <-- 수정됨

>>> 🏆 최종 종합 등급: 【 {grade} 】

[현장 특이사항]
- {notes if notes else "기록된 특이사항 없음"}

--------------------------------------------------------------------------------
💡 창원유니시티협상전문가 전용 [협상 가이드 (Standard 5)]
--------------------------------------------------------------------------------
{chr(10).join(negotiation_guides)}
================================================================================
"""
    return report

if __name__ == "__main__":
    # 사용 예시 (1단지 105동 2501호 방문 후 상태 9.5, 상황 9.0으로 입력)
    print(update_unit_data(1, 105, 2501, c_score=9.5, s_score=9.0, notes="시스템 에어컨 5대, 나노코팅 완료, 매도인 비과세 기한 임박으로 급매."))
