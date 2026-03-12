import json
import os

CALC_ENGINE_PATH = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\정밀_경제_평가_엔진\economic_calc_engine.py"

def calculate_net_proceeds(price, cost_basis, holding_period, is_primary_residence=True):
    # 1. 중개수수료 (경남 조례 기준 근사치: 9억 이상 0.9% 이내 협의, 여기서는 0.5% 가정)
    brokerage_fee = price * 0.005
    
    # 2. 양도소득세 (간이 계산 로직 - 실제는 국세청 홈택스 연동 필요)
    gain = price - cost_basis
    if is_primary_residence and gain <= 120000: # 1주택 비과세 12억 이하 가정
        tax = 0
    else:
        # 비과세 초과분 또는 다주택자 세율 적용 (시나리오별 변동성)
        tax = gain * 0.4 # 임시 세율
        
    return {
        "gross_price": price,
        "brokerage_fee": brokerage_fee,
        "estimated_tax": tax,
        "net_proceeds": price - brokerage_fee - tax
    }

# 이 파일은 향후 세밀한 법적/계산적 로직이 추가될 엔진의 뼈대입니다.
print("정밀 경제 평가 엔진 가동 준비 완료.")
