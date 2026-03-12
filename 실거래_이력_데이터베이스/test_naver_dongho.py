import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://new.land.naver.com/complexes/115528"
}

def fetch_dong_info():
    url = "https://new.land.naver.com/api/complexes/115528/buildings"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=ctx) as res:
            data = json.loads(res.read().decode())
            print("Dong Info:")
            for b in data:
                print(f"  {b['buildingName']}: ID={b['buildingNo']}")
            return data
    except Exception as e:
        print("Dong error:", e)

def fetch_dong_ho_info(building_no):
    # 단지 내 특정 동의 층/호수 배치도(달력형) 또는 리스트 조회
    # (네이버 부동산 공시가격 탭 참조 API)
    url = f"https://new.land.naver.com/api/complexes/115528/buildings/{building_no}/units"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=ctx) as res:
            data = json.loads(res.read().decode())
            # units 배열 내에 각 층별 혹은 호수별 데이터가 있을 것임
            return data
    except Exception as e:
        print("Units error:", e)

if __name__ == "__main__":
    b_data = fetch_dong_info()
    if b_data:
        # 첫 번째 동(S1동 등)의 세대별 정보 호출 테스트
        b_no = b_data[0]['buildingNo']
        units_data = fetch_dong_ho_info(b_no)
        print(f"Units for building {b_no}:")
        if units_data:
            print(json.dumps(units_data[:3], ensure_ascii=False)) # 앞 3개만 출력
        else:
            print("No unit data or blocked.")
