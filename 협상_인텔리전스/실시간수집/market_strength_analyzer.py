"""
시장강도 분석기 — KB부동산/한국부동산원 공개 데이터 기반
=======================================================
매물 증감, 매수/매도 우위 지수, 전세가율 추적
협상용 멘트 자동 생성

사용법:
    python market_strength_analyzer.py
    python market_strength_analyzer.py --update
"""
import json
import os
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '수집_결과')
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', '수집_결과', 'market_strength_history.json')


def load_history():
    """시장강도 이력 로드"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"records": []}


def save_history(data):
    """시장강도 이력 저장"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_market_record(record):
    """새로운 시장 데이터 기록 추가"""
    history = load_history()
    record['recorded_at'] = datetime.now().isoformat()
    history['records'].append(record)
    save_history(history)
    return history


def create_manual_input_record():
    """수동 입력 템플릿 — 브라우저에서 확인 후 입력"""
    print("=" * 60)
    print("📊 시장강도 데이터 수동 입력")
    print("   (KB부동산 kbland.kr / 한국부동산원 reb.or.kr 참조)")
    print("=" * 60)
    
    record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "manual_input"
    }
    
    # KB 심리지수
    print("\n[KB부동산 심리지수] (kbland.kr 에서 확인)")
    try:
        record['kb_buyer_superiority'] = float(input("  매수우위지수 (예: 73.4): ") or 0)
        record['kb_seller_pct'] = float(input("  매도자많음 응답% (예: 62.5): ") or 0)
        record['kb_buyer_pct'] = float(input("  매수자많음 응답% (예: 8.2): ") or 0)
        record['kb_sale_outlook'] = float(input("  매매전망지수 (예: 104.0): ") or 0)
        record['kb_rent_outlook'] = float(input("  전세전망지수 (예: 115.5): ") or 0)
    except ValueError:
        print("  [건너뜀]")
    
    # 한국부동산원 주간 동향
    print("\n[한국부동산원 주간 동향] (reb.or.kr 에서 확인)")
    try:
        record['reb_national_sale_change'] = float(input("  전국 매매변동률% (예: 0.04): ") or 0)
        record['reb_gyeongnam_sale_change'] = float(input("  경남 매매변동률% (예: 0.05): ") or 0)
        record['reb_changwon_sale_change'] = float(input("  창원 매매변동률% (예: ): ") or 0)
    except ValueError:
        print("  [건너뜀]")
    
    # 유니시티 매물 현황
    print("\n[유니시티 매물 현황] (네이버부동산/이실장 에서 확인)")
    try:
        record['unicity_listings_count'] = int(input("  현재 등록 매물 수 (예: 150): ") or 0)
        record['unicity_listings_prev'] = int(input("  지난달 매물 수 (예: 115): ") or 0)
        record['unicity_avg_price_35'] = int(input("  35평 평균 호가(만원) (예: 95000): ") or 0)
    except ValueError:
        print("  [건너뜀]")
    
    return record


def generate_negotiation_scripts(record):
    """시장강도 데이터 기반 협상 멘트 자동 생성"""
    scripts = []
    
    # 매수우위지수 기반
    buyer_idx = record.get('kb_buyer_superiority', 0)
    if buyer_idx and buyer_idx < 80:
        scripts.append(
            f"📊 \"KB부동산 매수우위지수가 {buyer_idx}입니다. "
            f"100 이하는 매수자가 우위인 시장을 의미합니다. "
            f"현실적인 가격 조정이 빠른 거래 성사로 이어집니다.\""
        )
    
    # 매도자/매수자 비율 기반
    seller_pct = record.get('kb_seller_pct', 0)
    buyer_pct = record.get('kb_buyer_pct', 0)
    if seller_pct > 50 and buyer_pct < 15:
        scripts.append(
            f"📉 \"현재 매도 희망자가 {seller_pct}%, 매수 희망자가 {buyer_pct}%입니다. "
            f"매도 경쟁이 치열한 시장에서 적정가 제시가 최선의 전략입니다.\""
        )
    
    # 매물 증감 기반
    curr = record.get('unicity_listings_count', 0)
    prev = record.get('unicity_listings_prev', 0)
    if curr and prev and curr > prev:
        change_pct = (curr - prev) / prev * 100
        scripts.append(
            f"📈 \"유니시티 매물이 지난달 {prev}건에서 {curr}건으로 "
            f"{change_pct:.0f}% 증가했습니다. 매물 적체가 시작된 구간입니다. "
            f"버티기보다 선제적 가격 조정이 유리합니다.\""
        )
    elif curr and prev and curr < prev:
        change_pct = (prev - curr) / prev * 100
        scripts.append(
            f"📉 \"유니시티 매물이 {prev}건에서 {curr}건으로 "
            f"{change_pct:.0f}% 감소했습니다. 매물 소진 단계로, "
            f"매수 타이밍을 놓치면 선택지가 줄어듭니다.\""
        )
    
    # 매매변동률 기반
    changwon_change = record.get('reb_changwon_sale_change', 0) or record.get('reb_gyeongnam_sale_change', 0)
    if changwon_change:
        if changwon_change > 0:
            scripts.append(
                f"📈 \"한국부동산원 기준 이 지역 매매가가 주간 {changwon_change}% 상승했습니다. "
                f"상승 추세에서의 매수는 시간이 돈입니다.\""
            )
        elif changwon_change < 0:
            scripts.append(
                f"📉 \"이 지역 매매가가 주간 {abs(changwon_change)}% 하락 중입니다. "
                f"추가 하락 전 현실적 가격 조정이 매도자에게 유리합니다.\""
            )
    
    return scripts


def show_summary():
    """최근 시장강도 요약"""
    history = load_history()
    if not history['records']:
        print("아직 수집된 데이터가 없습니다.")
        return
    
    latest = history['records'][-1]
    print("\n" + "=" * 60)
    print(f"📊 최신 시장강도 ({latest.get('date', 'N/A')})")
    print("=" * 60)
    
    for key, label in [
        ('kb_buyer_superiority', 'KB 매수우위지수'),
        ('kb_seller_pct', '매도자많음 %'),
        ('kb_buyer_pct', '매수자많음 %'),
        ('kb_sale_outlook', '매매전망지수'),
        ('reb_gyeongnam_sale_change', '경남 매매변동률%'),
        ('unicity_listings_count', '유니시티 매물수'),
    ]:
        val = latest.get(key)
        if val:
            print(f"  {label}: {val}")
    
    # 멘트 생성
    scripts = generate_negotiation_scripts(latest)
    if scripts:
        print("\n📋 자동 생성 협상 멘트:")
        for s in scripts:
            print(f"\n  {s}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='시장강도 분석기')
    parser.add_argument('--update', action='store_true', help='새 데이터 입력')
    parser.add_argument('--summary', action='store_true', help='최신 요약 확인')
    parser.add_argument('--auto', action='store_true', help='웹에서 자동 데이터 입력 (KB/기준금리 등)')
    args = parser.parse_args()
    
    if args.update:
        record = create_manual_input_record()
        history = add_market_record(record)
        print(f"\n[OK] 기록 추가. 총 {len(history['records'])}건")
        scripts = generate_negotiation_scripts(record)
        if scripts:
            print("\n📋 자동 생성 협상 멘트:")
            for s in scripts:
                print(f"\n  {s}")
    elif args.summary:
        show_summary()
    else:
        # 기본: 이전 데이터 요약 + 최신 KB 데이터로 기본 레코드 생성
        print("시장강도 분석기")
        print("  --update  : 새 데이터 입력")
        print("  --summary : 최신 요약 확인")
        
        # 최신 KB 데이터로 기본 레코드 자동 추가 (2026-03-08 기준)
        if not load_history()['records']:
            initial = {
                "date": "2026-03-08",
                "source": "web_search_initial",
                "kb_seller_pct": 62.5,
                "kb_buyer_pct": 8.2,
                "kb_sale_outlook": 104.0,
                "kb_rent_outlook": 115.5,
                "reb_national_sale_change": 0.04,
                "reb_gyeongnam_sale_change": 0.05,
                "note": "2026년 2월 KB리뷰 + 3월1주 부동산원 데이터"
            }
            add_market_record(initial)
            print("\n[초기화] 2026-03-08 기준 데이터 입력 완료")
            show_summary()
