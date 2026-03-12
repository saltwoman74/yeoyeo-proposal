import csv
import json
import os

MASTER_DB_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\세대_등급_시스템\유니시티_전세대_등급_마스터.csv"
VISIT_DATA_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\분석_데이터\세대별_현장_방문_기록.json"
STRATEGY_DB_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\협상_전술_엔진\거부_대응_시나리오.json"

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# [협상 전술 엔진 초기화: 계좌 거절 시 대응 시나리오]
INITIAL_STRATEGIES = {
    "PRICE_RESISTANCE": {
        "condition": "매도인이 가격이 너무 낮다고 계좌를 거부할 때",
        "cards": [
            "🃏 [비용 대전환] 매도인의 희망가 10억 7천과 매수 희망가 10억 5천의 차이인 2,000만 원은, 현재 매도인이 처한 '5월 중도금 사고 리스크'에 대한 보험료라고 설득하십시오.",
            "🃏 [기회 비용 강조] 지금 계좌를 주지 않아 10억 5천 매수자를 놓치면, 5월 말까지 새로운 매수자를 찾아 잔금까지 치러야 하는 시간적 압박이 수억 원의 손실로 이어질 수 있음을 경고하십시오."
        ]
    },
    "TIME_PRESSURE": {
        "condition": "매도인이 생각할 시간이 더 필요하다고 할 때",
        "cards": [
            "🃏 [자금 실행력 증명] 매수인이 이미 대출 승인을 마쳤거나 즉시 이체가 가능한 '확정적 자금'임을 강조하여, 불확실한 미래의 매수자보다 지금의 확정적 기회를 잡아야 한다고 압박하십시오.",
            "🃏 [조건부 클로징] '가격은 10억 5천으로 하되, 중도금 지급 기일을 매도인 니즈에 맞춰 4월 초로 당겨주겠다'는 조건부 제안으로 즉시 결정을 유도하십시오."
        ]
    },
    "MARKET_SENTIMENT": {
        "condition": "매도인이 시장이 오를 것 같아 더 받고 싶어할 때",
        "cards": [
            "🃏 [데이터 시연] 최근 유니시티의 실거래가 추이와 매물 적체량을 시각화하여 보여주며, 현재의 10억 5천이 시장 평균 대비 결코 낮은 금액이 아님을 입증하십시오.",
            "🃏 [실리적 접근] '오를지 모를 2천만 원 때문에, 확실히 필요한 5억 원의 자금 흐름에 구멍을 내는 것은 전문가의 판단이 아니다'라고 조언하십시오."
        ]
    }
}

def get_counter_strategy(reason_category):
    strategies = load_json(STRATEGY_DB_PATH)
    if not strategies:
        strategies = INITIAL_STRATEGIES
        save_json(STRATEGY_DB_PATH, strategies)
    
    return strategies.get(reason_category, {"cards": ["해당 상황에 대한 추가 학습이 필요합니다. 현장 데이터를 입력해주세요."]})

def generate_expert_report(complex_num, dong, ho, target_price, current_status=""):
    # (기존 데이터 로딩 및 계산 로직 포함...)
    # [데이터 요구사항 체크리스트]
    missing_data = []
    # 예: 등본상 채권최고액, 임차인 만기일, 전입세대 거주자 성씨 등
    # 이러한 정보가 없으면 시스템이 사용자에게 전술 고도화를 위해 요구함.
    
    report = f"""
# [창원유니시티협상전문가] 계좌 확보 실패 시 '반격 협상 카드'

## 1. 현재 상황 분석 (307동 4004호)
- 타겟 가격: {target_price}
- 매도인 거부 사유: {current_status if current_status else "미입력 (확인 필요)"}

## 2. 거부 사유별 '반격 카드' (Rejection Counter Cards)
"""
    # ... 상황에 따른 전략 추출 ...
    return report

if __name__ == "__main__":
    if not os.path.exists(STRATEGY_DB_PATH):
        save_json(STRATEGY_DB_PATH, INITIAL_STRATEGIES)
    print("협상 전술 엔진 및 거부 대응 시나리오 데이터베이스 구축 완료.")
