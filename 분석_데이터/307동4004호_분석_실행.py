import csv
import json
import os

MASTER_DB_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\세대_등급_시스템\유니시티_전세대_등급_마스터.csv"
VISIT_DATA_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\분석_데이터\세대별_현장_방문_기록.json"

def load_visit_data():
    if os.path.exists(VISIT_DATA_PATH):
        with open(VISIT_DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_visit_data(data):
    os.makedirs(os.path.dirname(VISIT_DATA_PATH), exist_ok=True)
    with open(VISIT_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_unit_report_no_pandas(complex_num, dong, ho, c_score=7.0, s_score=9.5, notes=""):
    search_complex = f"{complex_num}단지"
    search_dong = f"{dong}동"
    search_ho = f"{ho}호"
    
    unit_data = None
    if os.path.exists(MASTER_DB_PATH):
        with open(MASTER_DB_PATH, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Complex'] == search_complex and row['Dong'] == search_dong and row['Ho'] == search_ho:
                    unit_data = row
                    break
    
    if not unit_data:
        return f"❌ {search_complex} {search_dong} {search_ho}를 찾을 수 없습니다."

    # Convert numeric fields
    l_score = float(unit_data['L_Score'])
    c = float(c_score)
    s = float(s_score)
    
    # Calculate Total Grade (L: 50%, C: 30%, S: 20%)
    total_score = (l_score * 0.5) + (c * 0.3) + (s * 0.2)
    
    if total_score >= 9.2: grade = "S+"
    elif total_score >= 8.8: grade = "S"
    elif total_score >= 8.4: grade = "A+"
    elif total_score >= 8.0: grade = "A"
    elif total_score >= 7.5: grade = "B+"
    else: grade = "B"
    
    # Persistent Memory Update
    visits = load_visit_data()
    unit_id = unit_data['Unit_ID']
    visits[unit_id] = {
        "C_Score": c,
        "S_Score": s,
        "Total_Grade": grade,
        "Notes": notes,
        "Update_Date": "2026-03-04"
    }
    save_visit_data(visits)

    # Negotiation Cards (3~5 Cards)
    negotiation_cards = [
        f"🃏 [CARD 1: 자금 압박 활용] 매도인이 5월 말까지 5억 원의 중도금이 필요한 '타임 리스크(Time Risk)'를 안고 있습니다. 10억 5천 계좌 요청 시, '확정적 자금 실행력'을 담보로 강력한 클로징을 시도하십시오.",
        f"🃏 [CARD 2: 입지 가치 증명] 본 307동 {unit_data['Floor']}층은 입지 점수 {l_score}점의 초고층 랜드마크 호실입니다. 매수인에게는 '다시는 안 올 가격 우위'임을, 매도인에게는 '리스크 해지 비용'으로서의 2,000만 원 양보를 설득하십시오.",
        f"🃏 [CARD 3: 심리적 저항선 붕괴] 매수 희망가 10억 5천은 매도인의 심리적 마지노선일 가능성이 높습니다. '계좌 번호 요청'이라는 구체적 행동을 통해 매도인이 '이번 기회를 놓치면 5월 중도금 마련이 불가능하다'는 위기감을 느끼게 유도하십시오.",
        f"🃏 [CARD 4: 계약 조건 유연성] 5월 말 중도금 5억이라는 구체적 니즈가 있으므로, 잔금 일자 조정이나 중도금 선지급 조건을 카드로 제시하여 최종 가격 10억 5천을 확정 지으십시오.",
        f"🃏 [CARD 5: 데이터 기반 확신] 6,100세대 중 본 건의 상황 등급(S)은 9.5점으로 최상위입니다. 즉, '가장 확실한 거래 가능 물건'임을 객관적 데이터로 보여주며 양측의 합의를 이끌어내십시오."
    ]

    report = f"""
================================================================================
🎯 [창원유니시티협상전문가] 정밀 타겟팅 리포트 (3단지 307동 4004호)
================================================================================
[1. 세대 분석 요약]
- Unit ID: {unit_data['Unit_ID']} | 층수: {unit_data['Floor']}층 (초고층 파노라마뷰)
- 분석 일자: 2026-03-04 | 상태: 상황 긴급 분석 완료

[2. 실시간 등급 산정]
- 🔵 입지 등급 (L): {l_score} / 10 (랜드마크 동, 초고층 메리트 반영)
- 🟠 상태 등급 (C): {c} / 10 (현장 실사 전 기본값 반영)
- 🔴 상황 등급 (S): {s} / 10 (중도금 5억 긴급 필요 상황 반영 - 최상위 점수)

>>> 🏆 최종 종합 등급: 【 {grade} 】  <-- 강력 추천 매물

--------------------------------------------------------------------------------
💼 핵심 상황 데이터 (Situation Data)
--------------------------------------------------------------------------------
- 매도 목적: 타 매물 매수로 인한 잔금/중도금 마련 (갈아타기 성공 단계)
- 자금 니즈: 2026년 5월 말까지 '5억 원' 확정 필요 (Critical Condition)
- 가격 전략: 매도 희망가 10억 7천 --> 협상 타겟가 10억 5천 (▲2,000만 원 네고 시도)

--------------------------------------------------------------------------------
🔥 필승 협상 카드 (Negotiation Cards - Strategy 5)
--------------------------------------------------------------------------------
{chr(10).join(negotiation_cards)}
================================================================================
"""
    return report

if __name__ == "__main__":
    # 307동 4004호 분석 실행
    print(get_unit_report_no_pandas(3, 307, 4004, c_score=7.5, s_score=9.8, notes="매도인 5월 말 중도금 5억 급침. 10억 5천 계좌 확보 전략 단계."))
