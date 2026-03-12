"""
네이버 데이터랩 검색어 트렌드 수집기
==================================
'창원 유니시티 매매' vs '창원 유니시티 전세' 검색량 트렌드 비교 분석

사용법:
    python naver_datalab_collector.py --client-id YOUR_ID --client-secret YOUR_SECRET
    python naver_datalab_collector.py --config config.json

설정:
    네이버 개발자센터 (https://developers.naver.com) 에서
    애플리케이션 등록 → '데이터랩(검색어트렌드)' API 선택 → Client ID/Secret 발급
"""
import json
import urllib.request
import urllib.parse
import os
import sys
from datetime import datetime, timedelta

# ===== 설정 =====
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '수집_결과')

# 검색어 그룹 정의
KEYWORD_GROUPS = [
    {
        "name": "유니시티_매매_vs_전세",
        "keywords": [
            {"groupName": "유니시티 매매", "keywords": ["창원 유니시티 매매", "유니시티 매매", "중동유니시티 매매"]},
            {"groupName": "유니시티 전세", "keywords": ["창원 유니시티 전세", "유니시티 전세", "중동유니시티 전세"]},
        ]
    },
    {
        "name": "창원_아파트_매매_vs_전세",
        "keywords": [
            {"groupName": "창원 아파트 매매", "keywords": ["창원 아파트 매매", "창원시 아파트 매매"]},
            {"groupName": "창원 아파트 전세", "keywords": ["창원 아파트 전세", "창원시 아파트 전세"]},
        ]
    },
    {
        "name": "비교단지_트렌드",
        "keywords": [
            {"groupName": "유니시티", "keywords": ["창원 유니시티", "중동유니시티"]},
            {"groupName": "용지아이파크", "keywords": ["용지 아이파크", "용지아이파크"]},
            {"groupName": "힐스테이트창원", "keywords": ["힐스테이트 창원", "힐스테이트 창원 더퍼스트"]},
        ]
    }
]


def load_config():
    """config.json에서 API 키 로드"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(client_id, client_secret):
    """API 키를 config.json에 저장"""
    config = load_config()
    config['naver_client_id'] = client_id
    config['naver_client_secret'] = client_secret
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"[OK] 설정 저장: {CONFIG_PATH}")


def call_datalab_api(client_id, client_secret, keyword_groups, 
                     start_date=None, end_date=None, time_unit="week"):
    """네이버 데이터랩 검색어 트렌드 API 호출"""
    url = "https://openapi.naver.com/v1/datalab/search"
    
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    body = json.dumps({
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": keyword_groups
    }, ensure_ascii=False)
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    request.add_header("Content-Type", "application/json")
    
    try:
        response = urllib.request.urlopen(request, data=body.encode("utf-8"))
        result = json.loads(response.read().decode("utf-8"))
        return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"[ERROR] HTTP {e.code}: {error_body}")
        return None
    except urllib.error.URLError as e:
        print(f"[ERROR] URL Error: {e.reason}")
        return None


def analyze_trend(result, group_name):
    """트렌드 결과 분석 및 인사이트 도출"""
    if not result or 'results' not in result:
        return None
    
    analysis = {
        "group_name": group_name,
        "collected_at": datetime.now().isoformat(),
        "period": f"{result.get('startDate', '')} ~ {result.get('endDate', '')}",
        "trends": [],
        "insights": []
    }
    
    for r in result['results']:
        title = r.get('title', '')
        data = r.get('data', [])
        
        if not data:
            continue
        
        values = [d.get('ratio', 0) for d in data]
        recent_3 = values[-3:] if len(values) >= 3 else values
        prev_3 = values[-6:-3] if len(values) >= 6 else values[:3]
        
        avg_recent = sum(recent_3) / len(recent_3) if recent_3 else 0
        avg_prev = sum(prev_3) / len(prev_3) if prev_3 else 0
        change = ((avg_recent - avg_prev) / avg_prev * 100) if avg_prev > 0 else 0
        
        trend = {
            "keyword": title,
            "latest_value": values[-1] if values else 0,
            "max_value": max(values) if values else 0,
            "avg_recent_3weeks": round(avg_recent, 1),
            "change_vs_prev": round(change, 1),
            "direction": "상승" if change > 5 else ("하락" if change < -5 else "보합"),
            "data_points": len(data)
        }
        analysis['trends'].append(trend)
    
    # 인사이트 생성
    if len(analysis['trends']) >= 2:
        t1, t2 = analysis['trends'][0], analysis['trends'][1]
        ratio = t1['latest_value'] / t2['latest_value'] if t2['latest_value'] > 0 else 0
        
        if ratio > 1.3:
            analysis['insights'].append(
                f"'{t1['keyword']}' 검색량이 '{t2['keyword']}'보다 {ratio:.1f}배 높음 → 매매 수요 우위"
            )
        elif ratio < 0.7:
            analysis['insights'].append(
                f"'{t2['keyword']}' 검색량이 '{t1['keyword']}'보다 {1/ratio:.1f}배 높음 → 전세 수요 우위"
            )
        
        for t in analysis['trends']:
            if t['change_vs_prev'] > 20:
                analysis['insights'].append(
                    f"⚠️ '{t['keyword']}' 최근 검색량 급증 (+{t['change_vs_prev']:.0f}%) → 수요 이동 감지"
                )
    
    return analysis


def collect_all(client_id, client_secret):
    """전체 키워드 그룹 수집"""
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(OUTPUT_DIR, today)
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = {}
    
    for group in KEYWORD_GROUPS:
        print(f"\n[수집] {group['name']}...")
        result = call_datalab_api(
            client_id, client_secret,
            group['keywords'],
            time_unit="week"
        )
        
        if result:
            analysis = analyze_trend(result, group['name'])
            all_results[group['name']] = {
                "raw": result,
                "analysis": analysis
            }
            
            # 개별 저장
            filepath = os.path.join(output_dir, f"trend_{group['name']}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_results[group['name']], f, ensure_ascii=False, indent=2)
            print(f"  [OK] 저장: {filepath}")
            
            # 인사이트 출력
            if analysis and analysis.get('insights'):
                for insight in analysis['insights']:
                    print(f"  💡 {insight}")
        else:
            print(f"  [FAIL] 수집 실패")
    
    # 통합 리포트 저장
    report_path = os.path.join(output_dir, "trend_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n[완료] 통합 리포트: {report_path}")
    
    return all_results


def generate_negotiation_script(analysis):
    """트렌드 분석 결과로 협상용 멘트 자동 생성"""
    scripts = []
    
    if not analysis:
        return scripts
    
    for trend in analysis.get('trends', []):
        if '매매' in trend['keyword'] and trend['direction'] == '상승':
            scripts.append(
                f"📈 \"{trend['keyword']} 검색량이 최근 {trend['change_vs_prev']:.0f}% 증가했습니다. "
                f"매수 대기 수요가 움직이고 있다는 객관적 지표입니다. "
                f"지금이 가격 조율의 마지막 기회일 수 있습니다.\""
            )
        elif '전세' in trend['keyword'] and trend['direction'] == '상승':
            scripts.append(
                f"📈 \"{trend['keyword']} 검색량 {trend['change_vs_prev']:.0f}% 증가 중입니다. "
                f"전세 수요 증가는 실거주 선호 시장을 의미합니다. "
                f"매매 전환 수요도 함께 증가할 가능성이 높습니다.\""
            )
        elif trend['direction'] == '하락':
            scripts.append(
                f"📉 \"{trend['keyword']} 검색량이 {abs(trend['change_vs_prev']):.0f}% 감소했습니다. "
                f"수요가 줄고 있어 매도자 입장에서는 조속한 가격 조정이 유리합니다.\""
            )
    
    return scripts


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='네이버 데이터랩 검색어 트렌드 수집기')
    parser.add_argument('--client-id', help='네이버 Client ID')
    parser.add_argument('--client-secret', help='네이버 Client Secret')
    parser.add_argument('--save-config', action='store_true', help='API 키를 config.json에 저장')
    parser.add_argument('--period', default='1y', choices=['1m', '3m', '6m', '1y', '2y'], help='수집 기간')
    args = parser.parse_args()
    
    # API 키 로드
    config = load_config()
    client_id = args.client_id or config.get('naver_client_id', '')
    client_secret = args.client_secret or config.get('naver_client_secret', '')
    
    if not client_id or not client_secret:
        print("=" * 60)
        print("네이버 데이터랩 API 키가 설정되지 않았습니다.")
        print()
        print("발급 방법:")
        print("  1. https://developers.naver.com 접속")
        print("  2. 로그인 → Application → 애플리케이션 등록")
        print("  3. 애플리케이션 이름 입력 (예: '부동산트렌드수집')")
        print("  4. 사용 API에서 '데이터랩 (검색어트렌드)' 선택")
        print("  5. 등록하기 클릭")
        print("  6. 내 애플리케이션 → Client ID / Client Secret 확인")
        print()
        print("사용법:")
        print("  python naver_datalab_collector.py --client-id YOUR_ID --client-secret YOUR_SECRET --save-config")
        print("=" * 60)
        sys.exit(1)
    
    if args.save_config:
        save_config(client_id, client_secret)
    
    results = collect_all(client_id, client_secret)
    
    # 협상용 멘트 생성
    print("\n" + "=" * 60)
    print("📋 협상용 자동 생성 멘트")
    print("=" * 60)
    for group_name, data in results.items():
        if data.get('analysis'):
            scripts = generate_negotiation_script(data['analysis'])
            for s in scripts:
                print(f"\n{s}")
