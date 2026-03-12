import urllib.request
import urllib.parse
import json

COMPLEX_NO = "115528"
# 143A-1㎡ 타입의 Pyeong No는 네이버상 2, 3, 4번 등
PTYPE_NO = "2" # 143A-1㎡ 기준

def get_complex_details():
    # 단지 상세 (기본정보, 세대수 등)
    url = f"https://new.land.naver.com/api/complexes/{COMPLEX_NO}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://new.land.naver.com/complexes/{COMPLEX_NO}"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("=== 단지 기본 정보 ===")
            print(f"단지명: {data.get('complexName')}")
            print(f"세대수: {data.get('totalHouseHoldCount')}")
            print(f"주차대수: {data.get('totalParkingCount')} (세대당 {data.get('parkingCountByHousehold')})")
            print(f"건설사: {data.get('batlName')}")
    except Exception as e:
        print("Error fetching details:", e)

    # 평형 상세 (관리비, 재산세, 공시가격 등)
    # 43평형대(25평) 상세 정보 호출
    url_ptype = f"https://new.land.naver.com/api/complexes/{COMPLEX_NO}/pyeongs/{PTYPE_NO}"
    req2 = urllib.request.Request(url_ptype, headers=headers)
    try:
        with urllib.request.urlopen(req2) as response:
            data2 = json.loads(response.read().decode())
            print("\n=== 25평형 (전용59㎡, 광고 43평) 세금/관리비 정보 ===")
            
            # 관리비
            avg_fee_summer = data2.get("averageMaintenanceCost", {}).get("summerPrice", 0)
            avg_fee_winter = data2.get("averageMaintenanceCost", {}).get("winterPrice", 0)
            avg_fee = data2.get("averageMaintenanceCost", {}).get("price", 0)
            print(f"👉 연평균 관리비: {avg_fee:,}원 (여름: {avg_fee_summer:,}원, 겨울: {avg_fee_winter:,}원)")
            
            # 보유세 (재산세)
            tax_info = data2.get("propertyTax", {})
            print(f"👉 재산세(추정): {tax_info.get('taxPrice', 0):,}원")
            
            # 공시가격
            official_price = data2.get("officialPrice", {})
            print(f"👉 최고 공시가격: {official_price.get('price', 0):,}만원 ({official_price.get('baseYearMonth', '기준모름')})")
            
    except Exception as e:
        print("Error fetching pyeong details:", e)

if __name__ == "__main__":
    get_complex_details()
