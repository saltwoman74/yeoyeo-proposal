"""
공공데이터 포털 통합 수집기
==========================
국토부 실거래가 + 한국은행 금리 + KOSIS 인구 + 건축HUB 인허가
4개 공공 API를 통합 관리

사용법:
    python public_data_collector.py                    # 전체 현황
    python public_data_collector.py --setup            # API 키 설정
    python public_data_collector.py --trade            # 실거래가 수집
    python public_data_collector.py --rate             # 기준금리 수집
    python public_data_collector.py --population       # 인구통계 수집
    python public_data_collector.py --all              # 전체 수집
"""
import json
import os
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, '..', 'config.json')
OUTPUT_DIR = os.path.join(BASE_DIR, '..', '수집_결과')


# ============================================================
# 설정 관리
# ============================================================
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def setup_api_keys():
    """대화형 API 키 설정"""
    config = load_config()
    print("=" * 60)
    print("  공공데이터 API 키 설정")
    print("=" * 60)
    
    print("\n[1] 공공데이터포털 (data.go.kr) 서비스키")
    print("    -> 아파트 실거래가 + 건축인허가 API용")
    print("    -> https://data.go.kr 회원가입 -> 활용신청 -> 마이페이지에서 확인")
    key = input("    서비스키 (Encoding): ").strip()
    if key:
        config['data_go_kr_service_key'] = key
    
    print("\n[2] 한국은행 ECOS API 인증키")
    print("    -> 기준금리, GDP, 물가지수 등")
    print("    -> https://ecos.bok.or.kr -> Open API -> 인증키 신청")
    key = input("    인증키: ").strip()
    if key:
        config['ecos_api_key'] = key
    
    print("\n[3] KOSIS 통계 API 인증키 (선택)")
    print("    -> 인구통계, 주택통계 등")
    print("    -> https://kosis.kr -> Open API -> 인증키 신청")
    key = input("    인증키: ").strip()
    if key:
        config['kosis_api_key'] = key
    
    save_config(config)
    print("\n[OK] 설정 저장 완료!")


# ============================================================
# 1. 국토부 아파트 실거래가 API
# ============================================================
# 법정동 코드 (5자리)
AREA_CODES = {
    "의창구_중동": "48123",   # 창원시 의창구 (유니시티)
    "성산구_용호동": "48125",  # 창원시 성산구 (용지아이파크)
    "성산구": "48125",        # 힐스테이트 창원 더 퍼스트
}

# 단지 식별 키워드
COMPLEX_KEYWORDS = {
    "유니시티": ["유니시티", "중동유니시티"],
    "용지아이파크": ["용지아이파크", "아이파크"],
    "힐스테이트창원": ["힐스테이트", "힐스테이트창원"],
    "어반브릭스": ["어반브릭스", "어반브릭스스튜디오"],
}


def fetch_apt_trade(service_key, area_code, deal_ymd):
    """
    국토부 아파트 매매 실거래 상세 자료 API 호출
    
    Args:
        service_key: data.go.kr 서비스키
        area_code: 법정동 코드 5자리
        deal_ymd: 계약년월 6자리 (예: 202603)
    """
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
    params = {
        'serviceKey': service_key,
        'LAWD_CD': area_code,
        'DEAL_YMD': deal_ymd,
        'pageNo': '1',
        'numOfRows': '999'
    }
    
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    full_url = f"{url}?{query}"
    
    try:
        req = urllib.request.Request(full_url)
        response = urllib.request.urlopen(req, timeout=30)
        content = response.read().decode('utf-8')
        
        root = ET.fromstring(content)
        
        # 결과 코드 확인
        result_code = root.find('.//resultCode')
        if result_code is not None and result_code.text != '00':
            result_msg = root.find('.//resultMsg')
            print(f"  [ERROR] {result_code.text}: {result_msg.text if result_msg is not None else 'Unknown'}")
            return []
        
        items = root.findall('.//item')
        trades = []
        for item in items:
            trade = {}
            for child in item:
                trade[child.tag] = child.text.strip() if child.text else ''
            trades.append(trade)
        
        return trades
    except Exception as e:
        print(f"  [ERROR] API 호출 실패: {e}")
        return []

def fetch_offi_trade(service_key, area_code, deal_ymd):
    """국토부 오피스텔 매매 실거래 상세 자료 API 호출"""
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade"
    params = {
        'serviceKey': service_key,
        'LAWD_CD': area_code,
        'DEAL_YMD': deal_ymd,
        'pageNo': '1',
        'numOfRows': '999'
    }
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    full_url = f"{url}?{query}"
    
    try:
        req = urllib.request.Request(full_url)
        response = urllib.request.urlopen(req, timeout=30)
        content = response.read().decode('utf-8')
        root = ET.fromstring(content)
        
        result_code = root.find('.//resultCode')
        if result_code is not None and result_code.text != '00':
            return []
            
        items = root.findall('.//item')
        trades = []
        for item in items:
            trade = {}
            for child in item:
                trade[child.tag] = child.text.strip() if child.text else ''
            trade['is_officetel'] = True
            trades.append(trade)
        return trades
    except Exception as e:
        print(f"  [ERROR] 오피스텔 API 호출 실패: {e}")
        return []


def collect_real_trades(service_key, months=6):
    """최근 N개월 실거래 데이터 수집 (3개 단지 비교)"""
    print("\n" + "=" * 60)
    print("  아파트 실거래가 비교 수집")
    print("=" * 60)
    
    all_data = {}
    now = datetime.now()
    
    for area_name, area_code in AREA_CODES.items():
        print(f"\n[{area_name}] (코드: {area_code})")
        area_trades = []
        
        for m in range(months):
            target = now - timedelta(days=30 * m)
            deal_ymd = target.strftime('%Y%m')
            
            print(f"  {deal_ymd}...", end=" ")
            trades = fetch_apt_trade(service_key, area_code, deal_ymd)
            offi_trades = fetch_offi_trade(service_key, area_code, deal_ymd)
            
            total_trades = trades + offi_trades
            print(f"아파트 {len(trades)}건 / 오피스텔 {len(offi_trades)}건")
            area_trades.extend(total_trades)
        
        all_data[area_name] = area_trades
        print(f"  -> 총 {len(area_trades)}건 수집")
    
    # 단지별 분류
    complex_data = {name: [] for name in COMPLEX_KEYWORDS}
    for area_name, trades in all_data.items():
        for trade in trades:
            # 아파트명 또는 단지명(오피스텔)
            apt_name = trade.get('aptNm', '') or trade.get('아파트', '') or trade.get('danji', '') or trade.get('단지', '')
            for complex_name, keywords in COMPLEX_KEYWORDS.items():
                if any(kw in apt_name for kw in keywords):
                    trade['_complex'] = complex_name
                    trade['_area'] = area_name
                    complex_data[complex_name].append(trade)
    
    # 결과 저장
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(OUTPUT_DIR, today)
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, "real_trades_comparison.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(complex_data, f, ensure_ascii=False, indent=2)
    
    # 요약 출력
    print("\n--- 단지별 거래 현황 ---")
    for name, trades in complex_data.items():
        print(f"  {name}: {len(trades)}건")
        if trades:
            prices = []
            for t in trades:
                price_str = t.get('dealAmount', '') or t.get('거래금액', '')
                price_str = price_str.replace(',', '').strip()
                if price_str.isdigit():
                    prices.append(int(price_str))
            if prices:
                print(f"    가격범위: {min(prices):,} ~ {max(prices):,}만원")
                print(f"    평균: {sum(prices)//len(prices):,}만원")
    
    print(f"\n[OK] 저장: {filepath}")
    return complex_data


# ============================================================
# 2. 한국은행 ECOS API (기준금리)
# ============================================================
def fetch_bok_rate(api_key, stat_code="722Y001", period="M", 
                   start_date=None, end_date=None):
    """
    한국은행 ECOS API 호출
    
    주요 통계코드:
        722Y001: 한국은행 기준금리
        901Y009: 소비자물가지수
        036Y001: 예금은행 가중평균금리 (주택담보대출)
    """
    if not end_date:
        end_date = datetime.now().strftime('%Y%m')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y%m')
    
    # ECOS Open API URL
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/100/{stat_code}/{period}/{start_date}/{end_date}/0101000"
    
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=30)
        content = response.read().decode('utf-8')
        result = json.loads(content)
        
        if 'StatisticSearch' in result:
            rows = result['StatisticSearch'].get('row', [])
            return rows
        else:
            error = result.get('RESULT', {})
            print(f"  [ERROR] {error.get('CODE', '')}: {error.get('MESSAGE', '')}")
            return []
    except Exception as e:
        print(f"  [ERROR] ECOS API 호출 실패: {e}")
        return []


def collect_interest_rates(api_key):
    """기준금리 + 주택담보대출 금리 수집"""
    print("\n" + "=" * 60)
    print("  한국은행 금리 데이터 수집")
    print("=" * 60)
    
    results = {}
    
    # 기준금리
    print("\n[기준금리]")
    rates = fetch_bok_rate(api_key, "722Y001")
    if rates:
        results['base_rate'] = rates
        latest = rates[-1] if rates else {}
        print(f"  최신: {latest.get('TIME', '')} = {latest.get('DATA_VALUE', '')}%")
        print(f"  수집: {len(rates)}건")
    
    # 주택담보대출 금리
    print("\n[주택담보대출 금리]")
    loan_rates = fetch_bok_rate(api_key, "036Y001")
    if loan_rates:
        results['mortgage_rate'] = loan_rates
        latest = loan_rates[-1] if loan_rates else {}
        print(f"  최신: {latest.get('TIME', '')} = {latest.get('DATA_VALUE', '')}%")
    
    # 소비자물가지수
    print("\n[소비자물가지수]")
    cpi = fetch_bok_rate(api_key, "901Y009")
    if cpi:
        results['cpi'] = cpi
        latest = cpi[-1] if cpi else {}
        print(f"  최신: {latest.get('TIME', '')} = {latest.get('DATA_VALUE', '')}")
    
    # 저장
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(OUTPUT_DIR, today)
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, "interest_rates.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 저장: {filepath}")
    
    # 협상 멘트 생성
    if rates:
        latest_rate = float(rates[-1].get('DATA_VALUE', '0'))
        prev_rate = float(rates[-2].get('DATA_VALUE', '0')) if len(rates) >= 2 else latest_rate
        
        if latest_rate < prev_rate:
            print(f"\n[협상 멘트] \"기준금리가 {prev_rate}%에서 {latest_rate}%로 인하되었습니다. "
                  f"대출 부담이 줄어든 지금이 매수 적기입니다.\"")
        elif latest_rate > prev_rate:
            print(f"\n[협상 멘트] \"기준금리가 {latest_rate}%로 인상되었습니다. "
                  f"추가 인상 전 현재 금리에서 대출을 확정하시는 것이 유리합니다.\"")
    
    return results


# ============================================================
# 3. KOSIS 인구통계 API
# ============================================================
def fetch_kosis_population(api_key, org_id="101", tbl_id="DT_1B040A3",
                          start_prd="202401", end_prd=None):
    """
    KOSIS 인구이동 통계 API
    주요 테이블:
        DT_1B040A3: 시군구별 전입/전출
        DT_1IN1502: 시군구별 인구수
    """
    if not end_prd:
        end_prd = datetime.now().strftime('%Y%m')
    
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        'method': 'getList',
        'apiKey': api_key,
        'itmId': 'T1+',
        'objL1': 'ALL',
        'objL2': '',
        'objL3': '',
        'objL4': '',
        'objL5': '',
        'objL6': '',
        'objL7': '',
        'objL8': '',
        'format': 'json',
        'jsonVD': 'Y',
        'prdSe': 'M',
        'startPrdDe': start_prd,
        'endPrdDe': end_prd,
        'orgId': org_id,
        'tblId': tbl_id,
    }
    
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    
    try:
        req = urllib.request.Request(full_url)
        response = urllib.request.urlopen(req, timeout=30)
        content = response.read().decode('utf-8')
        result = json.loads(content)
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"  [ERROR] KOSIS API 호출 실패: {e}")
        return []


# ============================================================
# API 발급 가이드 출력
# ============================================================
def show_api_guide():
    """API 발급 안내"""
    print("=" * 70)
    print("  공공데이터 API 발급 가이드")
    print("=" * 70)
    
    print("""
  [1] 공공데이터포털 (data.go.kr)  -- 실거래가 + 건축인허가
  ---------------------------------------------------------------
  1. https://data.go.kr 접속 -> 회원가입/로그인
  2. 검색: "국토교통부_아파트매매 실거래 상세 자료"
  3. [활용신청] 클릭 -> 목적 입력 -> 신청
  4. 마이페이지 -> Open API -> 활용신청 현황 -> 서비스키 확인
  ** 승인은 보통 즉시 ~ 1시간 소요 **

  [2] 한국은행 ECOS (ecos.bok.or.kr)  -- 기준금리/대출금리/물가
  ---------------------------------------------------------------
  1. https://ecos.bok.or.kr 접속
  2. Open API -> 인증키 신청 (회원가입 필요)
  3. 즉시 발급됨 -> 인증키 복사

  [3] KOSIS 통계포털 (kosis.kr)  -- 인구/주택/경제통계
  ---------------------------------------------------------------
  1. https://kosis.kr 접속 -> 회원가입/로그인
  2. Open API -> 인증키 신청
  3. 발급 후 인증키 복사

  [설정 방법]
  python public_data_collector.py --setup
  -> 대화형으로 3개 API 키를 입력하고 config.json에 저장
""")
    
    config = load_config()
    print("  현재 설정 상태:")
    for key, label in [
        ('data_go_kr_service_key', 'data.go.kr 서비스키'),
        ('ecos_api_key', 'ECOS 인증키'),
        ('kosis_api_key', 'KOSIS 인증키'),
    ]:
        status = "[O] 설정됨" if config.get(key) else "[X] 미설정"
        print(f"    {label}: {status}")
    print()


# ============================================================
# 메인
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='공공데이터 포털 통합 수집기')
    parser.add_argument('--setup', action='store_true', help='API 키 설정')
    parser.add_argument('--trade', action='store_true', help='아파트 실거래가 수집')
    parser.add_argument('--rate', action='store_true', help='한국은행 금리 수집')
    parser.add_argument('--population', action='store_true', help='인구통계 수집')
    parser.add_argument('--all', action='store_true', help='전체 수집')
    parser.add_argument('--months', type=int, default=6, help='실거래 수집 개월수 (기본: 6)')
    parser.add_argument('--guide', action='store_true', help='API 발급 가이드')
    args = parser.parse_args()
    
    if args.guide or (not args.setup and not args.trade and not args.rate 
                       and not args.population and not args.all):
        show_api_guide()
        sys.exit(0)
    
    if args.setup:
        setup_api_keys()
        sys.exit(0)
    
    config = load_config()
    
    if args.trade or args.all:
        data_key = config.get('data_go_kr_service_key', '')
        if data_key:
            collect_real_trades(data_key, months=args.months)
        else:
            print("[SKIP] data.go.kr 서비스키 미설정. --setup 을 먼저 실행하세요.")
    
    if args.rate or args.all:
        ecos_key = config.get('ecos_api_key', '')
        if ecos_key:
            collect_interest_rates(ecos_key)
        else:
            print("[SKIP] ECOS 인증키 미설정. --setup 을 먼저 실행하세요.")
    
    if args.population or args.all:
        kosis_key = config.get('kosis_api_key', '')
        if kosis_key:
            data = fetch_kosis_population(kosis_key)
            if data:
                today = datetime.now().strftime("%Y-%m-%d")
                output_dir = os.path.join(OUTPUT_DIR, today)
                os.makedirs(output_dir, exist_ok=True)
                filepath = os.path.join(output_dir, "population_stats.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"[OK] 인구통계 저장: {filepath}")
        else:
            print("[SKIP] KOSIS 인증키 미설정. --setup 을 먼저 실행하세요.")
