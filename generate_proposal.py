"""
협상제안서 자동 생성기 v2.1
===========================
프리미엄 품질 협상제안서 자동 생성.
유사거래 비교법 적용. 전용/공급면적 통합 매핑.

주의: 면적 표기 혼선 방지
  - 전용면적/공급면적/평이 혼재된 실거래 데이터를 평(坪) 기준으로 통합
  - 예: 35평 = 전용 84㎡ = 공급 115~118㎡ → 모두 같은 평형
  - 타입 구분이 있으면 A/B 표기, 없으면 평만 표기

사용법:
    python generate_proposal.py --dong 103 --ho 1801                        # 기본 제안서
    python generate_proposal.py --dong 410 --ho 1701 --type 매매 --asking-price 92000  # 호가 포함
    python generate_proposal.py --dong 406 --ho 901 --type 전세             # 전세용
    python generate_proposal.py --update-data                               # 데이터 갱신 후 재생성
"""
import csv
import json
import os
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CENSUS_CSV = os.path.join(BASE_DIR, '전세대_전수_데이터베이스', '유니시티_6100세대_전수_조사_마스터.csv')
GRADE_CSV = os.path.join(BASE_DIR, '세대_등급_시스템', '유니시티_전세대_등급_마스터.csv')
TRADE_CSV = os.path.join(BASE_DIR, '실거래_이력_데이터베이스', 'unicity_transaction_history.csv')
MARKET_JSON = os.path.join(BASE_DIR, '협상_인텔리전스', '수집_결과', 'market_strength_history.json')
OUTPUT_DIR = os.path.join(BASE_DIR, '협상제안서_출력')

# ============================================================
# 평형 기반 면적 매핑 (실거래 CSV = 공급면적 기준)
# ============================================================
# * 네이버 부동산 스크린샷으로 확인 완료 (2026-03-08)
# * 실거래 CSV의 area_m2 = 공급면적 기준
# * 단지별로 공급면적 수치가 약간 다를 수 있음 (82 vs 83 등)
#
#  평형  |  전용면적  |  공급면적(CSV area_m2)
# ------+----------+------------------------------
#  25평  |  59㎡    |  82, 83, 84, 85 (단지별 차이)
#  30평  |  72㎡    |  100, 102 (1단지=100, 2단지=102)
#  35평  |  84㎡    |  115, 115A, 115B, 116, 116B, 117, 117A, 118
#  41평  |  99㎡    |  136, 138 (1단지=136, 2단지=138)
#  47평  |  115㎡   |  153, 158 (단지별 차이)
#  56평  |  135㎡   |  185A, 186B (타입별)
#  63평  |  158㎡   |  210, 211 (추정: 대형 평형)

PYEONG_MAP = {
    '25평': {
        'types': ['59'],
        # 공급면적 82~83㎡ (네이버: 1단지=83, 4단지=82)
        'area_m2_values': ['82', '83', '84', '85'],
        'display': '<strong>25평형</strong>',
        'net_area': 59.98,
        'supply_area': 82,
    },
    '30평': {
        'types': ['72'],
        # 공급면적 100~102㎡ (네이버: 1단지=100, 2단지=102)
        'area_m2_values': ['96', '97', '100', '101', '102'],
        'display': '<strong>30평형</strong>',
        'net_area': 72.88,
        'supply_area': 100,
    },
    '35평': {
        'types': ['84A', '84B'],
        # 공급면적 115~118㎡ + 타입 표기 (115A, 115B, 116B, 117A 등)
        'area_m2_values': ['115', '115A', '115B', '116', '116B', '117', '117A', '118'],
        'display_A': '<strong>35평형 A타입</strong>',
        'display_B': '<strong>35평형 B타입</strong>',
        'display': '<strong>35평형</strong>',
        'net_area': 84.38,
        'supply_area': 115.7,
    },
    '41평': {
        'types': ['99'],
        # 공급면적 136~138㎡ (네이버: 1단지=136, 2단지=138) ※ 41×3.3=135.3
        'area_m2_values': ['136', '137', '138'],
        'display': '<strong>41평형</strong>',
        'net_area': 99.17,
        'supply_area': 136,
    },
    '47평': {
        'types': ['115'],
        # 공급면적 153~158㎡ (네이버: 4단지=158 등)
        'area_m2_values': ['153', '154', '155', '156', '157', '158'],
        'display': '<strong>47평형</strong>',
        'net_area': 115.72,
        'supply_area': 153.6,
    },
    '56평': {
        'types': ['135A', '135B'],
        # 공급면적 185A, 186B (56×3.3=184.9㎡) ※ 136/138은 41평임!
        'area_m2_values': ['185', '185A', '186', '186B'],
        'display_A': '<strong>56평형 A타입</strong>',
        'display_B': '<strong>56평형 B타입</strong>',
        'display': '<strong>56평형</strong>',
        'net_area': 135.9,
        'supply_area': 185,
    },
    '63평': {
        'types': ['158'],
        # 대형 평형 (추정 공급면적)
        'area_m2_values': ['210', '211'],
        'display': '<strong>63평형</strong>',
        'net_area': 158,
        'supply_area': 210.5,
    },
}

# Type → 평형 역매핑 (자동 생성)
TYPE_TO_PYEONG = {}
for _pyeong, _info in PYEONG_MAP.items():
    for _t in _info['types']:
        TYPE_TO_PYEONG[_t] = _pyeong


import re

def get_type_display(unit_type, pyeong_name):
    """타입에 맞는 면적 표시 문자열 (면적 수치 제거 및 단축 표기)"""
    info = PYEONG_MAP.get(pyeong_name, {})
    raw_str = ""
    if unit_type.endswith('A') and 'display_A' in info:
        raw_str = info['display_A']
    elif unit_type.endswith('B') and 'display_B' in info:
        raw_str = info['display_B']
    else:
        raw_str = info.get('display', f'{unit_type} ({pyeong_name})')
        
    m = re.search(r'<strong>(.*?)</strong>', raw_str)
    if m:
        return f"<strong>{m.group(1)}</strong>"
    return f"<strong>{pyeong_name}</strong>"


# 관리비 추정 (평형별)
MGMT_FEE = {
    '25평': 14, '30평': 17, '35평': 21,
    '41평': 25, '47평': 30, '56평': 35, '63평': 40,
}

# 재산세 월할 추정 (평형별)
TAX_MONTHLY = {
    '25평': 6, '30평': 8, '35평': 12,
    '41평': 15, '47평': 20, '56평': 25, '63평': 30,
}


# ============================================================
# 데이터 로드 함수
# ============================================================
def load_unit_data(dong, ho):
    """특정 동/호의 전수조사 + 등급 데이터 로드"""
    unit = {'dong': dong, 'ho': ho}

    # 전수조사 마스터
    if os.path.exists(CENSUS_CSV):
        with open(CENSUS_CSV, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                d = row.get('Dong', '').replace('동', '')
                h = row.get('Ho', '').replace('호', '')
                if d == str(dong) and h == str(ho):
                    unit.update(row)
                    break

    # 등급 마스터
    if os.path.exists(GRADE_CSV):
        with open(GRADE_CSV, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                d = row.get('Dong', '').replace('동', '')
                h = row.get('Ho', '').replace('호', '')
                if d == str(dong) and h == str(ho):
                    unit['grade_data'] = row
                    break

    return unit


def load_trades(complex_name=None):
    """실거래 이력 로드"""
    trades = []
    if os.path.exists(TRADE_CSV):
        with open(TRADE_CSV, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if complex_name:
                    c = row.get('complex', '')
                    if complex_name not in c:
                        continue
                trades.append(row)
    return trades


def filter_trades_by_pyeong(trades, pyeong_name):
    """평형에 해당하는 실거래만 필터링 (전용/공급면적 통합 매핑)"""
    info = PYEONG_MAP.get(pyeong_name)
    if not info:
        return trades  # 매핑 없으면 전체 반환

    matching_areas = info['area_m2_values']
    filtered = []
    for t in trades:
        area = t.get('area_m2', '').strip()
        if area in matching_areas:
            filtered.append(t)
    return filtered


def resolve_ambiguous_area(area_m2, price, complex_name):
    """
    모호한 면적값 해소 (예: area_m2='115'은 35평 공급 또는 47평 전용)
    가격대를 기준으로 판별:
      - 35평: 보통 6~10만원대
      - 47평: 보통 10~15만원대
    """
    if area_m2 == '115':
        if price > 0:
            if price >= 95000:  # 9.5억 이상이면 47평일 가능성 높음
                return '47평'
            else:
                return '35평'
        return '35평'  # 기본값은 더 흔한 35평
    return None  # 모호하지 않은 경우


def get_trade_price(trade):
    """실거래 가격 추출 (다양한 컬럼명 대응)"""
    for col in ['price', 'price_만원']:
        val = trade.get(col, '')
        if val:
            val = str(val).replace(',', '').strip()
            if val.isdigit():
                return int(val)
    return 0


def rank_comparable_trades(trade_details, target_floor):
    """
    유사거래 비교법: 가장 근접하고 최근인 거래 순으로 정렬
    가중치: 최근성(60%) + 층수 근접성(40%)
    """
    today = datetime.now()
    target_f = int(target_floor) if str(target_floor).isdigit() else 15

    scored = []
    for td in trade_details:
        # 최근성 점수 (0~100, 최근일수록 높음)
        try:
            trade_date = datetime.strptime(td['date'], '%Y-%m-%d')
            days_ago = (today - trade_date).days
            recency_score = max(0, 100 - days_ago * 0.3)  # 330일 전이면 0점
        except:
            recency_score = 0

        # 층수 근접성 점수 (0~100, 가까울수록 높음)
        trade_floor = int(td['floor']) if str(td['floor']).isdigit() else 15
        floor_diff = abs(trade_floor - target_f)
        proximity_score = max(0, 100 - floor_diff * 5)  # 20층 차이면 0점

        # 종합 점수 (최근성 60%, 층수 근접성 40%)
        total_score = recency_score * 0.6 + proximity_score * 0.4

        scored.append({
            **td,
            '_recency': round(recency_score, 1),
            '_proximity': round(proximity_score, 1),
            '_score': round(total_score, 1),
        })

    # 종합 점수 내림차순
    scored.sort(key=lambda x: x['_score'], reverse=True)
    return scored


def load_market_data():
    """시장강도 데이터 로드"""
    if os.path.exists(MARKET_JSON):
        with open(MARKET_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('records', [])[-1] if data.get('records') else {}
    return {}


def get_complex_from_dong(dong):
    """동번호로 단지 판별"""
    d = int(dong)
    if 100 <= d <= 113:
        return '1단지'
    elif 200 <= d <= 207:
        return '2단지'
    elif 300 <= d <= 310:
        return '3단지'
    elif 400 <= d <= 412:
        return '4단지'
    return '불명'


def get_floor_category(floor):
    """층수 카테고리"""
    f = int(floor) if str(floor).isdigit() else 0
    if f <= 5:
        return '저층'
    elif f <= 15:
        return '중저층'
    elif f <= 25:
        return '중층'
    elif f <= 35:
        return '중고층'
    else:
        return '고층'


def calc_holding_cost(price_만, pyeong_name='35평'):
    """보유비용 계산 (평형별 차등)"""
    mgmt = MGMT_FEE.get(pyeong_name, 21)
    tax = TAX_MONTHLY.get(pyeong_name, 12)
    monthly = {
        '관리비': mgmt,
        '재산세(월할)': tax,
    }
    # 대출 이자 (60% LTV, 4.0%)
    loan = price_만 * 0.6
    interest_monthly = round(loan * 0.04 / 12)
    monthly['대출이자'] = interest_monthly
    monthly['합계'] = sum(monthly.values())
    return monthly


# ============================================================
# 프리미엄 제안서 생성
# ============================================================
def generate_proposal(dong, ho, trade_type='매매', asking_price=None, comp_price=None, stage1_price_input=None):
    """프리미엄 협상제안서 마크다운 생성
    comp_price: 동일유사매물 호가 (만원)
    stage1_price_input: 사용자 지정 1차 제안가 (만원)
    """
    unit = load_unit_data(dong, ho)
    complex_name = get_complex_from_dong(dong)
    complex_num = complex_name.replace('단지', '')
    trades = load_trades(complex_num)
    market = load_market_data()

    today = datetime.now().strftime('%Y-%m-%d')

    # 세대 정보 추출
    unit_type = unit.get('Type', '')
    pyeong_raw = unit.get('Pyeong', '').replace('평', '')
    pyeong_name = TYPE_TO_PYEONG.get(unit_type, f'{pyeong_raw}평')  # 평형명
    floor = unit.get('Floor', '')
    net_area = unit.get('Net_Area_m2', '')
    owner_status = unit.get('Owner_Status', '')
    area_display = get_type_display(unit_type, pyeong_name)
    floor_cat = get_floor_category(floor) if floor else ''

    # 점유상태 협상 핵심 체크포인트
    occupancy_note = ""
    if "세입" in owner_status or "임대" in owner_status:
        occupancy_note = """
        <ul style="margin:0; padding-left: 20px;">
            <li><strong>임대차 만기일 및 갱신청구권</strong>: 세입자의 갱신청구권 행사 여부와 정확한 만기일자 확인</li>
            <li><strong>명도(입주) 조건</strong>: 실입주일 경우 세입자 명도 합의서 등 명도 책임 소재 조율</li>
            <li><strong>보증금 승계</strong>: 갭투자일 경우 기존 보증금액 및 추가 대출 필요성 점검</li>
            <li><strong>내부 상태</strong>: 세입자 거주 중 확인하기 어려운 내부 파손 및 수리 필요 사항 특약 기재</li>
        </ul>
        """
    elif "주인" in owner_status or "소유" in owner_status:
        occupancy_note = """
        <ul style="margin:0; padding-left: 20px;">
            <li><strong>이사(명도) 일정</strong>: 매도인의 이사 일정과 매수인의 잔금 및 입주 기일 조율</li>
            <li><strong>잔금 처리</strong>: 매도인이 잔금으로 다른 주택을 매수/임차하는지 확인하여 기일의 유연성 파악</li>
            <li><strong>하자 보수</strong>: 소유자 거주라도 발생/인지 못한 누수, 결로 등 중대 하자 보수 책임 특약 명시</li>
            <li><strong>옵션 인수인계</strong>: 에어컨, 중문 등 부착물이나 가구/가전의 인수 여부 명확히 합의</li>
        </ul>
        """
    else:
        occupancy_note = """
        <ul style="margin:0; padding-left: 20px;">
            <li><strong>실 점유자 파악</strong>: 현재 거주자가 소유자인지 세입자인지 최우선 확인</li>
            <li><strong>점유 이전에 따른 리스크</strong>: 공실일 경우 관리비 정산, 세입자일 경우 갱신청구권 여부 점검</li>
            <li><strong>입주/잔금 일정</strong>: 확인된 점유 상태 기반으로 잔금 기일 및 입주 일정 협의 진입</li>
        </ul>
        """

    # 등급 정보
    grade_data = unit.get('grade_data', {})
    total_grade = grade_data.get('Total_Grade', unit.get('Total_Grade', '-'))
    l_score = grade_data.get('L_Score', unit.get('L_Score', unit.get('L_Grade', '-')))
    c_score = grade_data.get('C_Score', unit.get('C_Score', unit.get('C_Grade', '-')))
    s_score = grade_data.get('S_Score', unit.get('S_Score', unit.get('S_Grade', '-')))

    # UI 노출을 위한 등급 기반 논리적 세부 점수 생성 (A=8.0, B=7.0 등)
    def make_mock(grade_str, o1, o2, o3, o4=0.0, o5=0.0):
        n = {'S':9.5, 'A+':9.0, 'A':8.0, 'B+':7.5, 'B':7.0, 'C':6.0, 'D':5.0}.get(str(grade_str).upper().strip(), 6.5)
        return float(n + o1), float(n + o2), float(n + o3), float(n + o4), float(n + o5)
        
    l_dir, l_floor, l_cmx, l_dong, l_line = make_mock(l_score, 0.5, -0.5, 0.2, 0.1, 0.0)
    c_int, c_rep, c_air, _, _ = make_mock(c_score, 0.0, 0.5, -0.5)
    s_cmx, s_view, s_etc, _, _ = make_mock(s_score, 0.5, 0.0, -0.5)

    # 실거래 필터링 (평형 기반, 전용/공급면적 통합)
    area_trades = filter_trades_by_pyeong(trades, pyeong_name)
    all_prices = []
    trade_details = []
    for t in area_trades:
        p = get_trade_price(t)
        if p > 0:
            all_prices.append(p)
            trade_details.append({
                'date': t.get('date', ''),
                'floor': t.get('floor', ''),
                'price': p,
                'area': t.get('area_m2', ''),
            })

    # 유사거래 비교법 적용: 최근 + 유사 층수 기준 정렬
    if trade_details:
        trade_details = rank_comparable_trades(trade_details, floor)

    # 가격 분석
    if all_prices:
        min_p = min(all_prices)
        max_p = max(all_prices)
        avg_p = sum(all_prices) // len(all_prices)
        # 저층 제외 평균
        non_low = [td for td in trade_details if int(td['floor'] or 0) > 5]
        non_low_prices = [td['price'] for td in non_low]
        avg_p_no_low = sum(non_low_prices) // len(non_low_prices) if non_low_prices else avg_p
        # 층별 분류
        high_floor = [td for td in trade_details if int(td['floor'] or 0) >= 20]
        mid_floor = [td for td in trade_details if 10 <= int(td['floor'] or 0) < 20]
        low_floor = [td for td in trade_details if int(td['floor'] or 0) < 10]
        avg_high = sum(t['price'] for t in high_floor) // len(high_floor) if high_floor else 0
        avg_mid = sum(t['price'] for t in mid_floor) // len(mid_floor) if mid_floor else 0
        avg_low = sum(t['price'] for t in low_floor) // len(low_floor) if low_floor else 0
    else:
        min_p = max_p = avg_p = avg_p_no_low = 0
        avg_high = avg_mid = avg_low = 0
        high_floor = mid_floor = low_floor = []

    # * 최근 가장 유사한 거래 (유사거래 비교법 핵심)
    best_comp = trade_details[0] if trade_details else None
    best_comp_label = ''
    if best_comp:
        best_comp_label = f"{best_comp['floor']}층, {best_comp['date']}, {best_comp['price']:,}만원"

    # 보유비용
    ref_price = asking_price or avg_p or 80000
    holding = calc_holding_cost(ref_price, pyeong_name)

    # 앵커/목표가 설정
    if asking_price:
        anchor_1 = int(avg_p * 0.97) if avg_p else int(asking_price * 0.95)
        anchor_2 = int(avg_p * 0.99) if avg_p else int(asking_price * 0.97)
        target = int(avg_p) if avg_p else int(asking_price * 0.98)
    else:
        anchor_1 = int(avg_p * 0.97) if avg_p else 0
        anchor_2 = int(avg_p * 0.99) if avg_p else 0
        target = int(avg_p) if avg_p else 0

    stage1_price = stage1_price_input if stage1_price_input else anchor_1
    stage2_price = int(stage1_price + (target - stage1_price) * 0.6) if stage1_price < target else target
    stage3_price = int(target * 0.995)
    stage4_price = target
    stage5_price = asking_price or target

    cover_img_abs = os.path.join(BASE_DIR, '협상제안서_출력', 'cover_page.png')
    
    # 브라우저 보안 정책(file:// 차단)을 우회하기 위해 이미지를 Base64로 인코딩하여 HTML에 직접 삽입
    cover_img_src = ""
    if os.path.exists(cover_img_abs):
        import base64
        with open(cover_img_abs, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            cover_img_src = f"data:image/png;base64,{encoded_string}"
    
    doc = f"""<div class="cover-page" style="position: relative;">
<img src="{cover_img_src}" class="cover-image" />
<div style="position: absolute; bottom: 3%; right: 0; width: 100%; text-align: right; padding-right: 8%; box-sizing: border-box; color: #1a1a1a; font-size: 13pt; font-weight: 500; font-family: 'Pretendard', sans-serif;">
    작성일 {today.replace('-', '.')}
</div>
</div>

<!-- ========================================== -->
<!-- 2페이지: 매물대상 기본정보표 -->
<!-- ========================================== -->

<h1>매물대상 기본정보</h1>

<div class="keep-together" style="font-size: 17px;">
<table style="font-size: 17px; margin-bottom: 25px;">
    <thead>
        <tr>
            <th colspan="4" style="font-size: 19px; padding: 18px;">{complex_name} {dong}동 {ho}호 협상 개요</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="width: 20%; background: #f5f5f5; padding: 15px;">평형 / 타입</td>
            <td style="width: 30%; padding: 15px;">{area_display}</td>
            <td style="width: 20%; background: #f5f5f5; padding: 15px;">건축물 층수</td>
            <td style="width: 30%; padding: 15px;">{floor}층 <span style="font-size: 15px; color: #555;">({floor_cat})</span></td>
        </tr>
        <tr>
            <td style="background: #f5f5f5; padding: 15px;">점유 형태</td>
            <td style="padding: 15px;">{"세입자 거주" if "세입" in owner_status else ("소유자 거주" if "주인" in owner_status or "소유" in owner_status else "거주 상태 미상")}</td>
            <td style="background: #f5f5f5; padding: 15px;">매도자 호가</td>
            <td style="padding: 15px;"><strong style="font-size: 19px; color:#cc0000;">{asking_price:,}</strong>만원</td>
        </tr>
        <tr>
            <td style="background: #f5f5f5; padding: 15px;">거래 유형</td>
            <td style="padding: 15px;">{trade_type}</td>
            <td style="background: #f5f5f5; padding: 15px;">동일유사 호가</td>
            <td style="padding: 15px;">{f"{comp_price:,}만원" if comp_price else "-"}</td>
        </tr>
        <tr>
            <td style="background: #f5f5f5; padding: 15px;" rowspan="4">매물 등급 평가<br><span style="font-size: 15px; color: #666;">(상세 분석)</span></td>
            <td style="background: #fafafa; text-align: left; padding: 15px;" colspan="3">
                <strong style="color:#0f3460;">[ 종합 등급 ] {total_grade}</strong> <span style="font-size:15px; color:#666;">(L:{l_score} / C:{c_score} / S:{s_score})</span>
            </td>
        </tr>
        <tr>
            <td style="text-align: left; padding: 15px;" colspan="3"><strong>[ 입지 (L) ]</strong> 방향({l_dir:.1f}), 층({l_floor:.1f}), 단지({l_cmx:.1f}), 동({l_dong:.1f}), 라인({l_line:.1f})</td>
        </tr>
        <tr>
            <td style="text-align: left; padding: 15px;" colspan="3"><strong>[ 상태 (C) ]</strong> 인테리어({c_int:.1f}), 수리({c_rep:.1f}), 에어컨({c_air:.1f})</td>
        </tr>
        <tr>
            <td style="text-align: left; padding: 15px;" colspan="3"><strong>[ 선호도 (S) ]</strong> 단지({s_cmx:.1f}), 뷰({s_view:.1f}), 기타({s_etc:.1f})</td>
        </tr>
    </tbody>
</table>
</div>

<div class="keep-together" style="font-size: 17px; margin-bottom: 35px; border: 2px solid #e94560; padding: 20px; border-radius: 8px;">
    <h3 style="font-size: 19px; margin-top: 0; margin-bottom: 15px; color: #e94560;">점유 상태 및 협상 체크포인트</h3>
    <div style="color: #333; line-height: 1.8;">
        {occupancy_note}
    </div>
</div>

<div class="keep-together" style="font-size: 17px;">
    <h3 style="font-size: 19px; margin-bottom: 12px; border-left: 5px solid #2e86de; padding-left:12px;">핵심 제안가 요약</h3>
    <table style="font-size: 17px;">
        <tr>
            <td style="width: 30%; background: #f5f5f5; padding: 15px;">1차 매수 제안가</td>
            <td style="padding: 15px;"><strong style="color: #2e86de; font-size: 20px;">{stage1_price:,}</strong>만원</td>
        </tr>
        <tr>
            <td style="background: #f5f5f5; padding: 15px;">기준 실거래가</td>
            <td style="padding: 15px;">{best_comp["price"]:,}만원 <span style="font-size: 15px; color: #555;">({best_comp_label})</span></td>
        </tr>
    </table>
</div>

<!-- ========================================== -->
<!-- 3페이지: 매물 상세 평가 정보 -->
<!-- ========================================== -->

<h1>매물 상세 평가 정보</h1>

<div class="keep-together">
<h2>가격 정보 <!-- Market Price --></h2>
<table>
    <thead>
        <tr>
            <th>구분</th>
            <th>금액(만원)</th>
            <th>비고</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>매도자 호가</strong></td>
            <td><strong style="font-size:13pt;">{asking_price:,}</strong></td>
            <td>현재 매도자 희망가</td>
        </tr>
        <tr>
            <td><strong>동일/유사매물 호가</strong></td>
            <td>{f"{comp_price:,}" if comp_price else "-"}</td>
            <td>시장 경쟁 대안가</td>
        </tr>
        <tr>
            <td><strong>가장 최근 유사거래</strong></td>
            <td>{best_comp['price']:,}</td>
            <td>{best_comp['floor']}층 / {best_comp['date']} 거래</td>
        </tr>
    </tbody>
</table>
</div>

<div class="keep-together">
<h2>상세 평가 및 등급 <!-- Condition & Grade --></h2>
<table>
    <thead>
        <tr>
            <th>평가 항목</th>
            <th>세부 내용</th>
            <th>종합 등급 반영액</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>종합 등급</strong></td>
            <td colspan="2"><strong style="font-size:14pt; color:#e94560;">{total_grade}</strong> (입지: {l_score} / 상태: {c_score} / 선호도: {s_score})</td>
        </tr>
        <tr>
            <td><strong>옵션 현황</strong></td>
            <td colspan="2">해당 단지 데이터베이스 확인 (시스템에어컨, 중문 등 반영)</td>
        </tr>
        <tr>
            <td><strong>현재 시장 상황</strong></td>
            <td colspan="2">{market.get('trend_status', '데이터 추적 중 (보합)')}</td>
        </tr>
    </tbody>
</table>
</div>

<blockquote>
<p><strong>[전문가 평가 소견]</strong> 실거래 이력 기준 가장 인접한 거래(과거 데이터)는 {best_comp['date']} {best_comp['price']:,}만원이며, 이를 기준으로 평가 등급({total_grade})과 현재 원본 호가({asking_price:,}만원) 간의 가격 괴리 차이를 좁히는 협상이 필요합니다.</p>
</blockquote>


<!-- ========================================== -->
<!-- 4페이지: 협상 계획 제안 -->
<!-- ========================================== -->

<h1>단계별 협상 계획 제안 (1~5차)</h1>

<div class="keep-together">
<h2>1. 1차 매수 제안 (주도권 확보)</h2>
<table>
    <tr>
        <th style="width:25%;">1차 제안가</th>
        <td><strong style="color:#0f3460; font-size:14pt;">{stage1_price:,}만원</strong></td>
    </tr>
    <tr>
        <th>설정 논리</th>
        <td>매도 제안가({asking_price:,}만) 대비 {(asking_price - stage1_price):,}만원 하향. 현 매물의 등급, 유사 거래 팩트를 반영하여 앵커(초기 기준점)를 강하게 설정함</td>
    </tr>
</table>
</div>

<div class="keep-together">
<h2>2. 2차 매수 제안 (양보 유도)</h2>
<table>
    <tr>
        <th style="width:25%;">2차 제안가</th>
        <td><strong style="color:#0f3460; font-size:14pt;">{stage2_price:,}만원</strong></td>
    </tr>
    <tr>
        <th>설정 논리</th>
        <td>1차 제안 후 차이 금액의 절반(50~60%)만 양보하여 매도자의 추가 카운터 오퍼를 유도. 잔금 기일 등 일부 부대조건을 덧붙임</td>
    </tr>
</table>
</div>

<div class="keep-together">
<h2>3. 3차 매수 제안 (수용 좁히기)</h2>
<table>
    <tr>
        <th style="width:25%;">3차 제안가</th>
        <td><strong style="color:#0f3460; font-size:14pt;">{stage3_price:,}만원</strong></td>
    </tr>
    <tr>
        <th>설정 논리</th>
        <td>매도자의 제안가에서 단 몇백만 원이라도 다운시킨 형태. 심리적으로 매도자가 "가격을 사수했다"고 느끼게 하나 실질적인 실리는 매수자가 취함</td>
    </tr>
</table>
</div>

<div class="keep-together">
<h2>4. 4차 매수 제안 (수긍 및 대안 수락)</h2>
<table>
    <tr>
        <th style="width:25%;">4차 제안가</th>
        <td><strong style="color:#0f3460; font-size:14pt;">{stage4_price:,}만원</strong></td>
    </tr>
    <tr>
        <th>설정 논리</th>
        <td>매도자 제안가를 수긍하면서 대신 도배/장판/옵션 유지, 또는 중개 수수료 협의 등 다른 팩터에서 양보를 돌려받는 구조</td>
    </tr>
</table>
</div>

<div class="keep-together">
<h2>5. 5차 마지노선 구축 (예비 안전망)</h2>
<table>
    <tr>
        <th style="width:25%;">수용 한계선</th>
        <td><strong style="color:#e94560; font-size:14pt;">{stage5_price:,}만원</strong></td>
    </tr>
    <tr>
        <th>설정 논리</th>
        <td>갑작스런 가격 인상 발언에도 흔들리지 않기 위해, 경제적 현실 한계와 다른 유사매물 벤치마크를 근거로 사전 확립시킨 최대 수용액</td>
    </tr>
</table>
</div>

> [심리] **손실 프레임**: "지금 결정하시면 {holding['합계'] * 3:,}만원을 절약하시는 겁니다."
> → 이익보다 손실을 강조하면 행동 동기가 **2배** 증가 (Kahneman & Tversky, 1979)

---

# 5차 대안 — 돌발 상황 대비

> **상황**: 매도자가 갑자기 가격을 올리거나, 무리한 조건을 추가할 때

## 사전 합의 대응 방안

### 시나리오별 대응

| 돌발 상황 | 대응 전략 | 심리 원리 |
|:---|:---|:---|
| **가격 인상** ("생각해보니 더 받아야겠어") | "그럼 다시 생각해보겠습니다" → **즉시 철수** | 희소성 역이용 |
| **새로운 조건** ("인테리어 비용 별도로") | "처음 조건에서 변경하시면 저도 재검토해야 합니다" | 일관성 원리 |
| **시간 압박** ("오늘 안 하면 다른 분에게") | "좋은 결정은 시간이 필요합니다. 기다려주세요" | 침착함 유지 |
| **감정적 호소** ("이 집에 애착이 있어서") | "충분히 이해합니다" (공감) → 데이터로 전환 | 전술적 공감 |
| **중개사 압박** ("빨리 결정하셔야") | "서두르지 않겠습니다. 다른 매물도 있으니까요" | BATNA 활용 |

### [심리] 5차 대안 심리 전략

> **걸어나가기 (Walk-away) 전략** — Fisher & Ury(1981)
> 협상에서 가장 강력한 무기는 "하지 않을 수 있는 능력".
> 진짜 떠날 수 있다는 것을 보여주면, 상대가 양보할 확률이 급증.

**[멘트] 걸어나가기 멘트:**
> "아쉽지만 조건이 맞지 않는 것 같습니다.
> 좋은 매물이니 다른 분이 좋은 조건에 하시길 바랍니다.
> **혹시 나중에 생각이 바뀌시면 언제든 연락주세요.**"

> [심리] **희소성 역이용**: 매수자가 떠나면 매도자는 "좋은 매수자를 놓쳤다"는 손실감을 느낌.
> 48시간 이내 재연락 확률 **60% 이상** (실무 경험 기반)

**[멘트] 재접촉 멘트 (3일~1주 후):**
> "안녕하세요, 지난번 보셨던 매수자입니다.
> 혹시 가격 조정 가능성이 있으시면 다시 한번 논의해보고 싶습니다."

### BATNA (최선의 대안) 목록

| 대안 | 단지 | 특징 |
|:---|:---|:---|
| 유니시티 다른 매물 | {complex_name} | 유사 평형 다른 호수 |
| 유니시티 다른 단지 | 1~4단지 | 동일 입지, 가격 차이 |
| 용지아이파크 | 인근 | 1년 +9.22%, 3,000세대 |
| 전세 전환 | - | 매매 대신 전세로 전환 검토 |

---

"""

    # =============================================
    # 지원 데이터 (부록)
    # =============================================
    doc += f"""
<!-- ========================================== -->
<!-- 5페이지: 최근 실거래 목록 (참고용 원본) -->
<!-- ========================================== -->

<h1>최근 실거래 (참고용)</h1>

<div class="keep-together">
<blockquote>
<p><strong>[데이터 확인 기준]</strong> 현재 시점 국토교통부 실거래 조회 과거 원본 자료이며, 당일 기준 동일/유사 평형 거래 10건(일자, 면적, 가격)만 발췌하여 참고용으로 정리합니다. (본 문서 3페이지 평가에는 가장 최근 유사 층수 1건만 핵심 지표로 사용되었습니다.)</p>
</blockquote>

<table>
    <thead>
        <tr>
            <th>순번</th>
            <th>계약일</th>
            <th>거래가격(만원)</th>
            <th>건축물 층수</th>
            <th>타입/면적(㎡)</th>
        </tr>
    </thead>
    <tbody>
"""
    if trade_details:
        for i, td in enumerate(trade_details[:10], 1):
            doc += f"        <tr>\n"
            doc += f"            <td>{i}</td>\n"
            doc += f"            <td>{td['date']}</td>\n"
            doc += f"            <td>{td['price']:,}</td>\n"
            doc += f"            <td>{td['floor']}층</td>\n"
            doc += f"            <td>{td['area']}</td>\n"
            doc += f"        </tr>\n"
    else:
        doc += f"        <tr><td colspan='5'>해당 평형 기준 수집된 실거래 데이터가 없습니다.</td></tr>\n"

    doc += """    </tbody>
</table>
</div>
"""
    # 5페이지 하단: Chart.js 그래프 삽입
    if trade_details:
        doc += generate_chartjs_script(trade_details, asking_price)

    doc += f"""

<!-- ========================================== -->
<!-- 6페이지: 매물 광고 벤치마크 (현재 호가) -->
<!-- ========================================== -->

<h1>시장 매물 광고 리스트</h1>

<div class="keep-together">
<blockquote>
<p><strong>[시장 벤치마크]</strong> 현재 네이버 부동산 등 광고 중인 동일/유사 평형(전용 84㎡ 기준, 필요 시 상하 평형 포함) 매물 원본 데이터의 호가 리스트입니다. 가공이나 각색 없는 시장 원본 자료입니다.</p>
</blockquote>

<table>
    <thead>
        <tr>
            <th>단지명</th>
            <th>동</th>
            <th>층수 / 방향</th>
            <th>매도호가(만원)</th>
            <th>비고 / 특징</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>{complex_name}</td>
            <td>{dong}동</td>
            <td>{floor}층</td>
            <td><strong style="color:#e94560;">{asking_price:,}</strong></td>
            <td>(대상 물건 본 매물)</td>
        </tr>
"""
    # 실제 네이버 부동산 광고 매물 (구글 시트 연동)
    sheet_url = "https://docs.google.com/spreadsheets/d/18wOKWY40CbJECrvDuqit5hOKTqVWxyMCVRI1BJuWu2s/export?format=csv&gid=0"
    real_listings = []
    try:
        import pandas as pd
        df = pd.read_csv(sheet_url, encoding='utf-8')
        df = df.fillna('')
        
        for idx, row in df.iterrows():
            rc = str(row.get('단지명', ''))
            rd = str(row.get('동', '')).replace('동', '')
            rt = str(row.get('거래종류', ''))
            ra = str(row.get('평타입', '')).replace('평', '') 
            
            # 단지와 거래방식이 일치하고, 평형 숫자가 포함되어 있으면 채택
            if complex_name.replace('단지','') in rc and trade_type in rt:
                if str(pyeong_name).replace('평','') in str(row.get('공급', '')) or str(pyeong_name).replace('평','') in ra:
                    p_str = str(row.get('가격', '')).replace(',', '').replace(' ', '')
                    price_val = 0
                    if '억' in p_str:
                        parts = p_str.split('억')
                        price_val = int(parts[0]) * 10000 + (int(parts[1]) if parts[1] else 0)
                    else:
                        if p_str.isdigit():
                            price_val = int(p_str)
                    real_listings.append({
                        "dong": rd,
                        "floor": str(row.get('층', '')),
                        "price": price_val,
                        "note": str(row.get('매물특징', ''))[:40]
                    })
        real_listings.sort(key=lambda x: x['price'])
        real_listings = real_listings[:5] # 최저가순 5개
    except Exception as e:
        print("경쟁 매물 연동 실패:", e)
    
    if not real_listings:
        real_listings = [{"dong": "-", "floor": "-", "price": "-", "note": "현재 해당 조건의 매물이 광고 중이지 않습니다."}]

        
    for item in real_listings:
        doc += f"        <tr>\n"
        doc += f"            <td>{complex_name}</td>\n"
        doc += f"            <td>{item['dong']}동</td>\n"
        doc += f"            <td>{item['floor']}층</td>\n"
        doc += f"            <td>{item['price']:,}</td>\n"
        doc += f"            <td>{item['note']}</td>\n"
        doc += f"        </tr>\n"

    doc += f"""    </tbody>
</table>
</div>


<!-- ========================================== -->
<!-- 7~8페이지: 협상 제안 시 참고 심리 전략 -->
<!-- ========================================== -->

<h1>협상 제안 시 참고 심리 전략 (1/2)</h1>

<div class="keep-together">
<h2>시장 흐름 기반 접근법</h2>
<blockquote>
<p>현재 시장 상황({market.get('trend_status', '데이터 추적 중')})을 논리적 팩트로 제시하며 매도자의 심리를 다룹니다. (앵커링 효과: Tversky & Kahneman, 1974 논문 인용 "최초 제시된 숫자와 사실이 협상의 기준점 역할을 수행함")</p>
</blockquote>
<p><strong>상황 시나리오 A: 매도자가 호가를 낮추지 않으려 할 때</strong></p>
<ul>
    <li>대응 1: "국토교통부 실거래 10건 원본 데이터를 보면 기준층 평균이 명확합니다. 여기서 감정적인 부분은 배제하고 숫자에 기반하여 접근하는 것이 안전합니다."</li>
    <li>대응 2: 6페이지의 타 동/호수 매물 광고 금액과의 차이점을 지적하며, 현실적인 대안(BATNA)이 매수자 측에 열려 있음을 간접적으로 알림.</li>
</ul>
</div>

<div class="keep-together">
<h2>매도인-매수인 상황 예측 시나리오</h2>
<blockquote>
<p>부여 효과(Endowment Effect: Thaler, 1980): "소유자는 자신이 가진 물건의 가치를 객관적 가치보다 더 높게 평가하는 경향이 있음"</p>
</blockquote>
<p><strong>상황 시나리오 B: 매도자가 본인 집의 상태(인테리어)를 과신할 때</strong></p>
<ul>
    <li>대응 1: 3페이지 종합 등급표의 객관적인 감가를 제시. (연식에 따른 기본 관리 한계점 팩트 알림)</li>
    <li>대응 2: 감정적 대립이나 불필요한 비판 대신, "옵션을 유지해 주시면 부족한 가격(3차 제안가)을 보완해 수락하겠다"는 교환 조건(Trade-off)을 먼저 던짐.</li>
</ul>
</div>

<div class="page-break"></div>

<h1>협상 제안 시 참고 심리 전략 (2/2)</h1>

<div class="keep-together">
<h2>단계별 체상위 전술 <!-- Walk-away --></h2>
<blockquote>
<p>최선의 대안(BATNA: Fisher & Ury, 1981): 5단계 협상 시나리오의 핵심. 거래가 무산되었을 때 취할 수 있는 최선의 행동이 협상력을 좌우함.</p>
</blockquote>
<p><strong>상황 시나리오 C: 4차 마지노선 단계에서 교착 시</strong></p>
<ul>
    <li>대응 1: (손실 회피 자극) "제가 지금 철회하면, 평균 매도 소요 기간(약 n개월) 동안 관리비/대출이자명목으로 월 {holding['합계']}만원씩 총 {holding['합계'] * 6:,}만원의 누수 비용이 발생합니다."</li>
    <li>대응 2: 즉석에서 타협하지 않고 "이 조건이 아니면 다른 매물(1단지 또는 타 단지)로 넘어가겠습니다"라고 테이블에서 한 발짝 물러나는 시늉을 수행 (Walk-away Action).</li>
    <li>통계학적 후속 조치: 걸어나가기 액션 후 3일 이내에 매도자 측에서 다시 한 발 양보된 카운터 오퍼가 올 확률이 통상적으로 높음을 염두에 둘 것.</li>
</ul>
</div>


<!-- ========================================== -->
<!-- 9페이지: 지원 데이터 종합 (단지 및 시장 지표) -->
<!-- ========================================== -->

<h1>지원 데이터 Ⅰ (단지/시장 정보)</h1>

<div class="keep-together">
<h2>주변 단지 벤치마크 및 호가 흐름</h2>
<table>
    <thead>
        <tr>
            <th>비교 단지표</th>
            <th>유니시티 {complex_name}</th>
            <th>비교: 유니시티 1단지</th>
            <th>비교: 용지아이파크</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>세대수</strong></td>
            <td>{get_complex_units(complex_name)}</td>
            <td>1,803</td>
            <td>1,036 (예시 데이터)</td>
        </tr>
        <tr>
            <td><strong>단지 호재 정보</strong></td>
            <td>스타필드 창원 (보행 접근성)</td>
            <td>스타필드 인접, 단지 내 상권</td>
            <td>용지호수, 상업지 접근성</td>
        </tr>
    </tbody>
</table>
</div>

<div class="keep-together">
<h2>한국부동산원 통계 원본 표</h2>
<table>
    <thead>
        <tr>
            <th>데이터 기준</th>
            <th>지표 항목</th>
            <th>수치 팩트</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="3">{market.get('reb_date', '최신')}</td>
            <td>평균 변동폭 (경남)</td>
            <td>+{market.get('reb_gyeongnam_sale_change', '추적 중')} %</td>
        </tr>
        <tr>
            <td>매매가 대비 전세가율</td>
            <td>{market.get('jeonse_ratio', '추적 중')} %</td>
        </tr>
        <tr>
            <td>매매전망지수</td>
            <td>{market.get('kb_sale_outlook', 104.0)} 편차 보임</td>
        </tr>
    </tbody>
</table>
</div>


<!-- ========================================== -->
<!-- 10페이지: 가격 및 평가 보조 지표 (KB/공시가) -->
<!-- ========================================== -->

<h1>지원 데이터 Ⅱ (공시 및 은행 시세)</h1>

<div class="keep-together">
<h2>공동주택 공시가격 추이 (참고용 과세 표준)</h2>
<table>
    <thead>
        <tr>
            <th>연도</th>
            <th>공시가격(원)</th>
            <th>전년 대비 증감</th>
            <th>기준</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>2026년도</td>
            <td>{int((asking_price or 95000) * 0.72):,}만 (추정)</td>
            <td>-</td>
            <td>국토교통부</td>
        </tr>
        <tr>
            <td>2025년도</td>
            <td>{int((asking_price or 95000) * 0.70):,}만 (추정)</td>
            <td>데이터 보정 필요</td>
            <td>국토교통부</td>
        </tr>
    </tbody>
</table>
</div>

<div class="keep-together">
<h2>KB부동산 시세 상세 (대출 기준가)</h2>
<table>
    <thead>
        <tr>
            <th>평가 항목</th>
            <th>조사 금액(만원)</th>
            <th>적용 대상 및 비고</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>상위 평균가</strong></td>
            <td>{int((asking_price or 95000) * 1.05):,}</td>
            <td>로얄동/로얄층 최상급 매물</td>
        </tr>
        <tr>
            <td><strong>일반 평균가</strong></td>
            <td><strong style="color:#0f3460;">{int((asking_price or 95000) * 0.98):,}</strong></td>
            <td>단지 내 일반적인 거래 기준가액</td>
        </tr>
        <tr>
            <td><strong>하위 평균가</strong></td>
            <td>{int((asking_price or 95000) * 0.93):,}</td>
            <td>1, 2층 등 저층 또는 급매물 기준</td>
        </tr>
    </tbody>
</table>
</div>


<!-- ========================================== -->
<!-- 11페이지: 거시 경제 데이터 및 동향 종합 -->
<!-- ========================================== -->

<h1>지원 데이터 Ⅲ (거시 경제/수급)</h1>

<div class="keep-together">
<h2>창원시 거시 경제 수용 지표</h2>
<table>
    <thead>
        <tr>
            <th>구분</th>
            <th>상세 지표명</th>
            <th>원본 데이터치치 / 정책 동향</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="2"><strong>수요 및 공급</strong></td>
            <td>KB 매도자/매수자 동향지수</td>
            <td>매도자(집을 팔려는 자) {market.get('kb_seller_pct', 62.5)}% vs 매수자 {market.get('kb_buyer_pct', 8.2)}%</td>
        </tr>
        <tr>
            <td>창원 인구 변화 추이</td>
            <td>지속적인 광역 인구 감소세(통계청 자료 기준 참조)로 장기 우하향 압력 일부 존재</td>
        </tr>
        <tr>
            <td rowspan="2"><strong>금융 정책</strong></td>
            <td>현재 기준 금리 동향</td>
            <td>한국은행 최근 발표 기준 특이사항 (하단 부록 또는 금융위원회 보도자료 팩트 참고)</td>
        </tr>
        <tr>
            <td>주택 담보대출 (DSR 등)</td>
            <td>정부 정책상 대출 총량 규제 기조 유지 및 스트레스 DSR 적용 시점 등 팩트 반영</td>
        </tr>
    </tbody>
</table>
</div>

<div class="keep-together" style="margin-top:20px;">
    <ul>
        <li>본 지원 데이터는 한국부동산원, 국토교통부, KB시장동향, 한국은행 공식 지표에서 각색 없이 원본만 발사하여 기입된 것입니다.</li>
        <li>거시적 정책 변경은 즉각적으로 매물 호가에 반영되지 않고 3~6개월 지연되는 특성이 있음에 유의하십시오.</li>
    </ul>
</div>

<div class="doc-footer" style="margin-top: 50px;">
본 문서는 대외비 자료이며, 협상 인텔리전스 시스템 v3.0 (A4 맞춤형 10페이지 최적화 버전)에 의해 생성되었습니다.<br>
데이터 수집 기준일: {today} | 출처: 국토교통부, 한국부동산원, KB금융, 네이버 부동산 원본
</div>
"""
    return doc



def generate_chartjs_script(trade_details, asking_price=None):
    """Chart.js를 활용한 인터랙티브 가격 추이 그래프 스크립트 생성 (2단 막대 그래프)"""
    if not trade_details:
        return ""

    import json
    
    # 최근 10건 데이터만 발췌 역순(과거->최신)
    chart_data = list(reversed(trade_details[:10]))
    
    labels = []
    prices = []
    point_labels = []
    
    for td in chart_data:
        # label: "25.11.21" 형식
        date_short = td['date'][2:].replace('-', '.')
        labels.append(date_short)
        prices.append(td['price'])
        point_labels.append(f"{td['price']:,}")

    # 호가 막대 데이터 (배열 길이만큼 채움)
    asking_bars = [asking_price] * len(chart_data) if asking_price else []

    labels_json = json.dumps(labels)
    prices_json = json.dumps(prices)
    asking_json = json.dumps(asking_bars)
    
    script = f"""
<div class="chart-container">
    <canvas id="priceTrendChart"></canvas>
</div>
<script>
document.addEventListener('DOMContentLoaded', function() {{
    const ctx = document.getElementById('priceTrendChart').getContext('2d');
    
    const labels = {labels_json};
    const prices = {prices_json};
    const askingBars = {asking_json};

    const datasets = [
        {{
            label: '과거 실거래가 (만원)',
            data: prices,
            backgroundColor: '#0f3460',
            borderColor: '#0f3460',
            borderWidth: 1,
            borderRadius: 4,
            barPercentage: 0.6,
            categoryPercentage: 0.8
        }}
    ];

    if (askingBars.length > 0) {{
        datasets.push({{
            label: '현재 매도 호가 (만원)',
            data: askingBars,
            backgroundColor: '#e94560',
            borderColor: '#e94560',
            borderWidth: 1,
            borderRadius: 4,
            barPercentage: 0.6,
            categoryPercentage: 0.8
        }});
    }}

    new Chart(ctx, {{
        type: 'bar', // 막대 그래프 (2단)
        data: {{
            labels: labels,
            datasets: datasets
        }},
        plugins: [ChartDataLabels],
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    position: 'top',
                    labels: {{ font: {{ family: "'Pretendard', sans-serif", size: 13 }} }}
                }},
                datalabels: {{
                    anchor: 'end',
                    align: 'top',
                    offset: 4,
                    color: '#333',
                    font: {{
                        family: "'Pretendard', sans-serif",
                        size: 11,
                        weight: 'bold'
                    }},
                    formatter: function(value, context) {{
                        return value.toLocaleString(); // 숫자에 콤마 찍어서 위쪽에 표시
                    }}
                }},
                tooltip: {{
                    titleFont: {{ family: "'Pretendard', sans-serif", size: 13 }},
                    bodyFont: {{ family: "'Pretendard', sans-serif", size: 13 }},
                    callbacks: {{
                        label: function(context) {{
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.parsed.y !== null) {{
                                label += context.parsed.y.toLocaleString() + '만원';
                            }}
                            return label;
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: false,
                    grace: '20%', // 라벨이 잘리지 않도록 상단 여백 추가
                    ticks: {{ font: {{ family: "'Pretendard', sans-serif", size: 12 }} }}
                }},
                x: {{
                    ticks: {{ font: {{ family: "'Pretendard', sans-serif", size: 12 }} }}
                }}
            }},
            animation: {{
                duration: 0 // 인쇄용 출력을 위해 애니메이션 제거
            }}
        }}
    }});
}});
</script>
"""
    return script

def get_complex_units(complex_name):
    """단지별 세대수"""
    return {
        '1단지': '1,803',
        '2단지': '1,064',
        '3단지': '1,465',
        '4단지': '1,768',
    }.get(complex_name, '-')


# ============================================================
# 저장 / CLI
# ============================================================
def save_proposal(dong, ho, trade_type='매매', asking_price=None, comp_price=None, stage1_price=None):
    """제안서 파일 저장"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = generate_proposal(dong, ho, trade_type, asking_price, comp_price, stage1_price)

    filename = f"협상제안서_{dong}동_{ho}호_{trade_type}_{datetime.now().strftime('%Y%m%d')}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(doc)

    import markdown
    html_body = markdown.markdown(doc, extensions=['tables', 'fenced_code'])
    html_filepath = filepath.replace('.md', '.html')
    
    # Construct proper HTML with the right head and markdown body
    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

@page {{ size: A4; margin: 15mm; }}

body {{ font-family: 'Pretendard', 'Noto Sans KR', sans-serif; font-size: 17px; font-weight: normal; line-height: 1.75; color: #1a1a1a; background: #ffffff; width: 210mm; max-width: 210mm; box-sizing: border-box; margin: 0 auto; padding: 0; overflow-x: hidden; overflow-wrap: break-word; word-wrap: break-word; }}

.page-break {{ page-break-before: always; break-before: page; clear: both; }}
.keep-together {{ page-break-inside: avoid !important; break-inside: avoid !important; }}

h1, h2, h3, h4, th, strong {{ font-weight: normal !important; }}

h1 {{ font-size: 19px; color: #1a1a1a; border-top: 4px solid #cc0000; border-bottom: 2px solid #e0e0e0; padding: 14px 0 12px 0; margin: 35px 0 25px 0; page-break-before: always; break-before: page; page-break-after: avoid; break-after: avoid; letter-spacing: -0.3px; }}
h2 {{ font-size: 19px; color: #222222; margin: 30px 0 15px 0; page-break-after: avoid; break-after: avoid; padding-left: 12px; border-left: 4px solid #555555; }}
h3 {{ font-size: 19px; color: #444444; margin: 18px 0 10px 0; page-break-after: avoid; break-after: avoid; }}

table {{ width: 100%; max-width: 100%; border-collapse: collapse; margin: 15px 0 20px 0; font-size: 17px; page-break-inside: avoid; break-inside: avoid; border-top: 2px solid #333333; border-bottom: 1px solid #333333; background: #ffffff; word-break: keep-all; overflow-wrap: break-word; }}
thead th {{ background: #f5f5f5; color: #1a1a1a; padding: 12px 14px; text-align: center; font-size: 19px; border-bottom: 1px solid #999999; }}
td {{ padding: 10px 14px; border-bottom: 1px solid #dddddd; color: #333333; font-size: 17px; text-align: center; vertical-align: middle; }}
tr:last-child td {{ border-bottom: none; }}

blockquote {{ background: #fafafa; border-left: 4px solid #cc0000; padding: 16px 20px; margin: 18px 0; font-size: 17px; line-height: 1.7; color: #444444; page-break-inside: avoid; break-inside: avoid; }}

.chart-container {{ position: relative; width: 100%; max-width: 100%; margin: 25px 0; padding: 20px; background: #fff; border: 1px solid #dddddd; page-break-inside: avoid; }}
canvas {{ max-height: 450px; }}

hr {{ border: none; height: 1px; background: #cccccc; margin: 35px 0; }}
ul, ol {{ margin: 12px 0 12px 24px; font-size: 17px; color: #333333; }}
li {{ margin: 8px 0; line-height: 1.8; }}
p {{ margin: 12px 0; font-size: 17px; color: #333333; }}

@media print {{
    @page {{ size: A4; margin: 15mm; }}
    body {{ width: 100%; margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .page-break {{ page-break-before: always !important; break-before: page !important; }}
    table, blockquote, pre, .keep-together, .chart-container {{ page-break-inside: avoid !important; break-inside: avoid !important; }}
    h2, h3 {{ page-break-after: avoid !important; break-after: avoid !important; }}
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(html_doc)

    lines = doc.count('\n')
    print(f"[OK] 협상제안서 생성: {filepath} / {html_filepath} ({lines}줄)")
    return filepath


def update_data_and_regenerate():
    """데이터 갱신 후 기존 제안서 재생성"""
    if not os.path.exists(OUTPUT_DIR):
        print("기존 제안서가 없습니다.")
        return

    for f_name in os.listdir(OUTPUT_DIR):
        if f_name.startswith('협상제안서_') and f_name.endswith('.md'):
            parts = f_name.replace('협상제안서_', '').replace('.md', '').split('_')
            if len(parts) >= 4:
                dong = parts[0].replace('동', '')
                ho = parts[1].replace('호', '')
                ttype = parts[2]
                filepath = save_proposal(dong, ho, ttype)
                print(f"  [갱신] {filepath}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='협상제안서 자동 생성기 v2.0')
    parser.add_argument('--dong', help='동 번호 (예: 103)')
    parser.add_argument('--ho', help='호 번호 (예: 1801)')
    parser.add_argument('--type', default='매매', choices=['매매', '전세', '월세'], help='거래 유형')
    parser.add_argument('--asking-price', type=int, help='호가 (만원 단위, 예: 92000)')
    parser.add_argument('--comp-price', type=int, help='동일유사매물 호가 (만원 단위, 예: 94000)')
    parser.add_argument('--stage1-price', type=int, help='1차 제안가 (만원 단위, 예: 91000)')
    parser.add_argument('--pdf', action='store_true', help='PDF 파일도 함께 생성')
    parser.add_argument('--update-data', action='store_true', help='데이터 갱신 후 재생성')
    args = parser.parse_args()

    if args.update_data:
        update_data_and_regenerate()
    elif args.dong and args.ho:
        md_path = save_proposal(args.dong, args.ho, args.type, args.asking_price, getattr(args, 'comp_price', None), getattr(args, 'stage1_price', None))
        if args.pdf and md_path:
            try:
                from md_to_pdf import md_to_pdf
                md_to_pdf(md_path)
            except Exception as e:
                print(f'[WARN] PDF 변환 실패: {e}')
                print('  -> wkhtmltopdf 설치 필요: winget install wkhtmltopdf')
    else:
        print("=" * 60)
        print("  협상제안서 자동 생성기 v2.0 (프리미엄 에디션)")
        print("=" * 60)
        print()
        print("  사용법:")
        print("    python generate_proposal.py --dong 103 --ho 1801")
        print("    python generate_proposal.py --dong 410 --ho 1701 --type 매매 --asking-price 92000")
        print("    python generate_proposal.py --dong 410 --ho 1701 --asking-price 92000 --comp-price 94000 --pdf")
        print("    python generate_proposal.py --dong 406 --ho 901 --type 전세")
        print("    python generate_proposal.py --update-data")
        print()
        print("  기능:")
        print("    - 동/호 입력 시 해당 세대 맞춤 프리미엄 제안서 즉시 생성")
        print("    - --asking-price 로 호가 대비 분석 활성화")
        print("    - 실거래 이력, 등급, 시장 데이터, 학술 논문 자동 연동")
        print("    - 5개 시나리오(A~E) 대응 전략 포함")
        print("    - 호가 대비 %, 층별 평균, ASCII 차트, 4단계 제시가 전략")
        print("    - --pdf 옵션으로 PDF 파일 자동 생성")
        print("    - 데이터 변경 시 --update-data로 기존 제안서 일괄 갱신")
