import urllib.request
import urllib.parse
import json
from datetime import datetime

COMPLEX_NO = "115528"

def get_recent_transactions():
    url = f"https://new.land.naver.com/api/complexes/{COMPLEX_NO}/prices/real"
    params = {
        "complexNo": COMPLEX_NO,
        "tradeType": "A1", # 매매
        "year": datetime.now().year,
        "priceChartChange": "N",
        "areaNo": "", 
        "type": "table"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": f"https://new.land.naver.com/complexes/{COMPLEX_NO}"
    }
    
    all_trades = []
    for year in [2026, 2025]:
        params["year"] = year
        query = urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{url}?{query}", headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if "realPriceList" in data:
                    all_trades.extend(data["realPriceList"])
        except Exception as e:
            print(f"Error fetching {year}: {e}")
            
    print("=== 어반브릭스 매매 최근 실거래가 (43평형대) ===")
    count = 0
    for t in all_trades:
        area = t.get("areaName", "")
        if "143" in str(area) or "144" in str(area):
            date = t.get("tradeDate", "")
            price = t.get("dealPrice", "")
            floor = t.get("floor", "")
            print(f"[{date}] 공급 {area}㎡ | 가격: {price}만 | 층수: {floor}층")
            count += 1
            if count >= 10: break

def get_lowest_listings():
    url = f"https://new.land.naver.com/api/articles/complex/{COMPLEX_NO}"
    params = {
        "realEstateType": "OT",
        "tradeType": "A1",
        "sort": "prc",
        "page": 1
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://new.land.naver.com/complexes/{COMPLEX_NO}"
    }
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}", headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            articles = data.get("articleList", [])
            print("\n=== 어반브릭스 매매 최저가 매물 (43평형대 필터) ===")
            count = 0
            for a in articles:
                area1 = str(a.get("area1", 0))
                if "143" in area1 or "144" in area1:
                    title = a.get("articleName", "")
                    price = a.get("dealOrWarrantPrc", "")
                    floor = a.get("floorInfo", "")
                    desc = a.get("articleFeatureDesc", "")
                    print(f"{title} | 공급 {area1}㎡ | 호가: {price} | 층수: {floor} | 특징: {desc}")
                    count += 1
                    if count >= 10: break
    except Exception as e:
        print("Error fetching listings:", e)

if __name__ == "__main__":
    get_recent_transactions()
    get_lowest_listings()
