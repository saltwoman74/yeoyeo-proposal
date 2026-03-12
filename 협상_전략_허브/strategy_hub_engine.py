import json
import os
import csv

# 파일 경로 정의
HUB_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\협상_전략_허브\협상_시나리오_허브.json"
MASTER_DB = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\세대_등급_시스템\유니시티_전세대_등급_마스터.csv"

class NegotiationHub:
    def __init__(self):
        self.scenarios = self.load_hub()

    def load_hub(self):
        if os.path.exists(HUB_PATH):
            with open(HUB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "307-4004": {
                "Target_Price": 105000,
                "Seller_Resistance": 106000,
                "Key_Risk": "5월 말 중도금 5억 미확보 시 계약 사고 가능성",
                "Phased_Strategies": [
                    {
                        "Phase": "1단계: 가격 저항 대응 (10억 6천 거절 시)",
                        "Tactics": [
                            "🃏 [Risk Pivot] 1,000만 원 추가 이득보다 5억 원의 중도금 사고 방지가 매도인에게 50배 더 중요한 실리임을 강조.",
                            "🃏 [Market Data] 최근 3단지 유사 평형 실거래 최고가와 현재 매물 적체량을 비교 시연하여 10억 5천이 상위권 가격임을 입증.",
                            "🃏 [Time Decay] 매수인이 다른 동(예: 301동 고층)으로 이동할 가능성을 시사하여 매도인의 조급함 유도."
                        ]
                    },
                    {
                        "Phase": "2단계: 계좌 확보 클로징",
                        "Tactics": [
                            "🃏 [Flash Clause] '오늘 내로 계좌 주시면 중도금 중 1억 원을 3일 내 선지급하겠다'는 파격적 자금 스케줄 제안.",
                            "🃏 [Escrow Logic] 10억 5천 확정 시 매수인의 자금 증빙(잔고증명 등)을 즉시 공유하여 거래의 확실성 담보."
                        ]
                    }
                ],
                "Required_Intelligence": [
                    "307동 최근 1개월 내 이실장 실매물 가격 분포도",
                    "매도인 대출 상환 필요액 (등본상 근저당권 설정액 정밀 확인)",
                    "매수인 가용 현금 비중 및 대출 승인 여부"
                ]
            }
        }

    def save_hub(self):
        os.makedirs(os.path.dirname(HUB_PATH), exist_ok=True)
        with open(HUB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.scenarios, f, ensure_ascii=False, indent=4)

    def get_advice(self, unit_key):
        return self.scenarios.get(unit_key, "해당 세대에 대한 시나리오가 아직 구축되지 않았습니다. 분석을 시작할까요?")

hub = NegotiationHub()
hub.save_hub()
print("창원유니시티 협상 전략 시나리오 허브 가동 시작.")
