import json
import os

class EconomicCalculator:
    def __init__(self):
        # 경상남도 창원시 부동산 취득 관련 법정 요율 (2026 기준 가정)
        self.tax_rates = {
            "acquisition": 0.011, # 1주택 6억 초과 9억 이하 (간이)
            "brokerage": 0.005,   # 9억 이상 협의 요율 상한
            "capital_gains": 0.4, # 일반 세율 가정
            "holding_cost_per_month": 350000, # 유니시티 84㎡ 평균 관리비 + 각종 부대비용
        }

    def calculate_seller_net(self, sale_price, purchase_price, holding_months, renovation_cost=0):
        """매도자 순수익 산출: 양도세, 수수료, 관리비, 인테리어 매몰비용 포함"""
        brokerage_fee = sale_price * self.tax_rates["brokerage"]
        total_holding_cost = self.tax_rates["holding_cost_per_month"] * holding_months
        
        # 양도소득세 (장특공제 미반영 초안)
        gain = sale_price - purchase_price - brokerage_fee - renovation_cost
        tax = max(0, gain * self.tax_rates["capital_gains"])
        
        net_proceeds = sale_price - tax - brokerage_fee - total_holding_cost
        
        return {
            "sale_price": sale_price,
            "brokerage_fee": brokerage_fee,
            "estimated_tax": tax,
            "total_holding_cost": total_holding_cost,
            "renovation_cost": renovation_cost,
            "final_net_proceeds": net_proceeds
        }

    def calculate_buyer_total_cost(self, purchase_price, target_renovation=0):
        """매수자 총 투입비용 산출: 취득세, 인테리어, 수수료 등"""
        acquisition_tax = purchase_price * self.tax_rates["acquisition"]
        brokerage_fee = purchase_price * self.tax_rates["brokerage"]
        
        total_initial_investment = purchase_price + acquisition_tax + brokerage_fee + target_renovation
        
        return {
            "purchase_price": purchase_price,
            "acquisition_tax": acquisition_tax,
            "brokerage_fee": brokerage_fee,
            "target_renovation": target_renovation,
            "total_initial_investment": total_initial_investment
        }

if __name__ == "__main__":
    calc = EconomicCalculator()
    # 예시: 10억 7천 매도 시뮬레이션
    print(json.dumps(calc.calculate_seller_net(1070000000, 800000000, 24, 20000000), indent=4, ensure_ascii=False))
