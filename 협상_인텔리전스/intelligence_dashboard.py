"""
통합 인텔리전스 대시보드
========================
모든 수집 스크립트를 통합 실행하고 결과를 관리

사용법:
    python intelligence_dashboard.py                  # 전체 현황
    python intelligence_dashboard.py --collect-all    # 전체 수집
    python intelligence_dashboard.py --trend          # 트렌드만 수집
    python intelligence_dashboard.py --market         # 시장강도만 수집
    python intelligence_dashboard.py --report         # 보고서 생성
"""
import os
import sys
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(BASE_DIR, '수집_결과')

def show_status():
    """현재 수집 상태 개요"""
    print("=" * 70)
    print("   🏢 창원유니시티 협상 인텔리전스 대시보드")
    print(f"   📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    # 학술논문 상태
    papers_dir = os.path.join(BASE_DIR, '학술논문')
    papers_master = os.path.join(papers_dir, '학술논문_수집_마스터.md')
    print(f"\n📚 학술논문: {'✅ 수집 마스터 존재' if os.path.exists(papers_master) else '❌ 미수집'}")
    
    # 거시리포트 상태
    macro_dir = os.path.join(BASE_DIR, '거시리포트')
    macro_master = os.path.join(macro_dir, '거시시장_리포트_수집.md')
    print(f"📊 거시리포트: {'✅ 수집 완료' if os.path.exists(macro_master) else '❌ 미수집'}")
    
    # 트렌드 수집 상태
    config_path = os.path.join(BASE_DIR, 'config.json')
    has_api = False
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        has_api = bool(config.get('naver_client_id'))
    print(f"🔍 네이버 데이터랩: {'✅ API 설정됨' if has_api else '⚠️ API 키 미설정'}")
    
    # 시장강도 상태
    strength_file = os.path.join(RESULT_DIR, 'market_strength_history.json')
    if os.path.exists(strength_file):
        with open(strength_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        count = len(history.get('records', []))
        latest = history['records'][-1] if history.get('records') else None
        date = latest.get('date', '?') if latest else '?'
        print(f"💪 시장강도: ✅ {count}건 기록 (최신: {date})")
    else:
        print("💪 시장강도: ❌ 미수집")
    
    # 수집 결과 폴더
    if os.path.exists(RESULT_DIR):
        dates = sorted([d for d in os.listdir(RESULT_DIR) if os.path.isdir(os.path.join(RESULT_DIR, d))])
        if dates:
            print(f"\n📁 수집 이력: {len(dates)}회")
            for d in dates[-5:]:
                files = os.listdir(os.path.join(RESULT_DIR, d))
                print(f"   {d}: {len(files)}개 파일")
    
    print("\n" + "-" * 70)
    print("🔧 명령어:")
    print("   --collect-all  : 전체 수집 (트렌드 + 시장강도)")
    print("   --trend        : 네이버 데이터랩 트렌드 수집")
    print("   --market       : 시장강도 수동 입력")
    print("   --report       : 협상 브리핑 보고서 생성")
    print("=" * 70)


def collect_trend():
    """네이버 데이터랩 트렌드 수집"""
    sys.path.insert(0, os.path.join(BASE_DIR, '실시간수집'))
    try:
        from naver_datalab_collector import load_config, collect_all
        config = load_config()
        cid = config.get('naver_client_id', '')
        csecret = config.get('naver_client_secret', '')
        if not cid or not csecret:
            print("⚠️ 네이버 API 키가 설정되지 않았습니다.")
            print("   먼저 실행: python 실시간수집/naver_datalab_collector.py --client-id ID --client-secret SECRET --save-config")
            return
        collect_all(cid, csecret)
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")


def collect_market():
    """시장강도 수동 입력"""
    sys.path.insert(0, os.path.join(BASE_DIR, '실시간수집'))
    try:
        from market_strength_analyzer import create_manual_input_record, add_market_record, generate_negotiation_scripts
        record = create_manual_input_record()
        add_market_record(record)
        scripts = generate_negotiation_scripts(record)
        if scripts:
            print("\n📋 자동 생성 협상 멘트:")
            for s in scripts:
                print(f"\n  {s}")
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")


def generate_report():
    """협상 브리핑 보고서 생성"""
    today = datetime.now().strftime("%Y-%m-%d")
    report_dir = os.path.join(RESULT_DIR, today)
    os.makedirs(report_dir, exist_ok=True)
    
    report = f"# 협상 인텔리전스 일일 브리핑\n\n"
    report += f"**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    report += "---\n\n"
    
    # 시장강도 데이터
    strength_file = os.path.join(RESULT_DIR, 'market_strength_history.json')
    if os.path.exists(strength_file):
        with open(strength_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        if history.get('records'):
            latest = history['records'][-1]
            report += "## 📊 시장강도 현황\n\n"
            report += f"| 지표 | 수치 |\n|:---|:---|\n"
            for key, label in [
                ('kb_seller_pct', '매도자많음 %'),
                ('kb_buyer_pct', '매수자많음 %'),
                ('kb_sale_outlook', '매매전망지수'),
                ('reb_gyeongnam_sale_change', '경남 매매변동률%'),
                ('unicity_listings_count', '유니시티 매물수'),
            ]:
                val = latest.get(key)
                if val:
                    report += f"| {label} | {val} |\n"
            report += "\n"
    
    # 트렌드 데이터
    trend_dir = os.path.join(RESULT_DIR, today)
    trend_files = [f for f in os.listdir(trend_dir) if f.startswith('trend_') and f.endswith('.json')] if os.path.exists(trend_dir) else []
    if trend_files:
        report += "## 🔍 검색 트렌드\n\n"
        for tf in trend_files:
            with open(os.path.join(trend_dir, tf), 'r', encoding='utf-8') as f:
                data = json.load(f)
            analysis = data.get('analysis', {})
            if analysis:
                report += f"### {analysis.get('group_name', tf)}\n"
                for trend in analysis.get('trends', []):
                    report += f"- **{trend['keyword']}**: 최근 {trend['latest_value']}, 변동 {trend['change_vs_prev']}% ({trend['direction']})\n"
                for insight in analysis.get('insights', []):
                    report += f"  - 💡 {insight}\n"
                report += "\n"
    
    report += "---\n*자동 생성 보고서 — 협상 인텔리전스 시스템*\n"
    
    report_path = os.path.join(report_dir, "daily_briefing.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[OK] 일일 브리핑 생성: {report_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='협상 인텔리전스 대시보드')
    parser.add_argument('--collect-all', action='store_true', help='전체 수집')
    parser.add_argument('--trend', action='store_true', help='트렌드만 수집')
    parser.add_argument('--market', action='store_true', help='시장강도 입력')
    parser.add_argument('--report', action='store_true', help='보고서 생성')
    args = parser.parse_args()
    
    if args.collect_all:
        collect_trend()
        collect_market()
        generate_report()
    elif args.trend:
        collect_trend()
    elif args.market:
        collect_market()
    elif args.report:
        generate_report()
    else:
        show_status()
