import csv
import os

def create_notebooklm_markdown():
    csv_path = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\전세대_전수_데이터베이스\어반브릭스_462세대_전수_조사_마스터.csv"
    md_output_path = r"c:\Users\sango\Desktop\Anty2\창원유니시티협상전문가\NotebookLM_Sources\11_어반브릭스_462세대_마스터DB.md"
    
    # 헤더 인젝션 (NotebookLM이 컨텍스트를 정확히 이해하도록 강제 명시)
    markdown_content = """# 어반브릭스 오피스텔 462세대 전수조사 마스터 데이터베이스 (인텔리전스)

> **[시스템 필수 프롬프트 제약조건 - AI Agent 필독]**
> * 본 문서는 '어반브릭스 오피스텔'의 전체 462세대 개별 호실(S1동~S3동) 단위의 추정 분양가, 공시가격, 취득세, 예상 등급(Floor Grade), 임차/자가 현황을 담고 있는 단일 소스 오브 트루스(Master DB)입니다.
> * **[핵심]** 사용자가 "어반브릭스 25평", "어반브릭스 59㎡", "어반브릭스 43평"을 언급하면 모두 이 문서에 적힌 **'25평(전용 59㎡)'** 데이터를 참조하여 답변해야 합니다. 절대 아파트 평형과 혼동하지 마십시오.
> * 표에 기재된 금액 컬럼(Base_Price, Official_Price 등)의 단위는 모두 **'단위: 만원'**입니다. (예: 30000 = 3억 원)
> * 취득세는 오피스텔 단일 세율 4.6%가 적용된 계산값입니다.

---

## 🏢 세대별 마스터 데이터 

| 단지 | 동 | 호수 | 층 | 평형(표준화) | 타입 | 전용면적(㎡) | 추정_분양가(만원) | 공시가격(만원) | 취득세_4.6%(만원) | 총취득원가(만원) | L_Grade | Total_Score | Total_Grade | 점유상태 |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
"""
    
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # 불필요한 열은 빼고, 핵심 열만 마크다운 표로 구성 (Token 아끼기 위함)
                # "Unit_ID" "Complex" "Dong" "Ho" "Floor" "Pyeong" "Type" "Net_Area_m2" "Base_Price_TenWork" 
                # "Official_Price_TenWork" "Estimated_Interest_TenWork" "Tax_4_6_Percent" "Total_Acquisition_Cost" 
                # "L_Grade" "C_Grade" "S_Grade" "Total_Score" "Total_Grade" "Naver_Ad_Info" "Owner_Status" "Memo"
                
                md_row = f"| {row['Complex']} | {row['Dong']} | {row['Ho']} | {row['Floor']}층 | {row['Pyeong']} | {row['Type']} | {row['Net_Area_m2']} | {row['Base_Price_TenWork']} | {row['Official_Price_TenWork']} | {row['Tax_4_6_Percent']} | {row['Total_Acquisition_Cost']} | {row['L_Grade']} | {row['Total_Score']} | {row['Total_Grade']} | {row['Owner_Status']} |\n"
                markdown_content += md_row
                
        # 생성된 마크다운을 11번 소스파일로 저장
        os.makedirs(os.path.dirname(md_output_path), exist_ok=True)
        with open(md_output_path, mode='w', encoding='utf-8') as mf:
            mf.write(markdown_content)
            
        print(f"SUCCESS: NotebookLM Source Generated -> {md_output_path}")
        print("462세대의 마크다운 표 변환이 완료되었습니다.")
        
    except Exception as e:
        print(f"ERROR: Failed to generate markdown DB -> {e}")

if __name__ == "__main__":
    create_notebooklm_markdown()
