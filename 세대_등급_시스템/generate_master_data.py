import csv
import os

def generate_unicity_data():
    # 실제 유니시티 단지 정보
    # 단지ID, 총세대수(근사), 동 리스트, 최고층
    complexes = [
        {"id": 1, "dongs": list(range(101, 114)), "max_floor": 42},
        {"id": 2, "dongs": list(range(201, 208)), "max_floor": 42},
        {"id": 3, "dongs": list(range(301, 311)), "max_floor": 42},
        {"id": 4, "dongs": list(range(401, 413)), "max_floor": 42},
    ]

    output_path = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\세대_등급_시스템\유니시티_전세대_등급_마스터.csv"
    
    with open(output_path, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["Unit_ID", "Complex", "Dong", "Ho", "Floor", "L_Score", "C_Score", "S_Score", "Total_Grade", "Status"])

        total_count = 0
        for comp in complexes:
            comp_id = comp["id"]
            max_floor = comp["max_floor"]
            
            for dong in comp["dongs"]:
                # 층당 1~6호 라인 생성 (최대 42층까지)
                for floor in range(1, max_floor + 1):
                    for ho_idx in range(1, 7): 
                        ho = floor * 100 + ho_idx
                        unit_id = f"U{comp_id}-{dong}-{ho}"
                        
                        # 층수 기반 입지 점수 초기화 (1층 5.0 ~ 42층 9.5)
                        l_score = round(5.0 + (floor / max_floor) * 4.5, 1)
                        c_score = 7.0
                        s_score = 7.0
                        
                        total_score = (l_score * 0.5) + (c_score * 0.3) + (s_score * 0.2)
                        
                        if total_score >= 9.0: grade = "S"
                        elif total_score >= 8.5: grade = "A+"
                        elif total_score >= 8.0: grade = "A"
                        elif total_score >= 7.5: grade = "B+"
                        elif total_score >= 7.0: grade = "B"
                        else: grade = "C"
                        
                        writer.writerow([
                            unit_id, f"{comp_id}단지", f"{dong}동", f"{ho}호", floor, 
                            l_score, c_score, s_score, grade, "공식기초분석완료"
                        ])
                        total_count += 1

    print(f"유니시티 전세대({total_count}개 항목) 데이터베이스 구축 완료.")

if __name__ == "__main__":
    generate_unicity_data()
