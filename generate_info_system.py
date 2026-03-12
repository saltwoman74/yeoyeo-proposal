"""
창원 유니시티 통합 정보 시스템 생성기 v3
- 단지방: 단지 전체 요약 + 실거래가 시세 요약 + 등급/관리비
- 동방: 동별 상세 + 라인매핑 + 실거래가 시세범위
- 호세대방: 마스터 CSV 기반 전 세대 현황

사용자 확인 Ground Truth 기준 (절대 변경 금지)
"""

import pandas as pd
import os
import re
import sys

sys.path.insert(0, r"c:/Users/sango/Desktop/Anty2/창원유니시티협상전문가")
from ground_truth import GROUND_TRUTH, STRUCTURE, TYPE_MAP

BASE_DIR = r"c:/Users/sango/Desktop/Anty2/창원유니시티협상전문가"
MASTER_CSV = os.path.join(BASE_DIR, "전세대_전수_데이터베이스", "유니시티_6100세대_전수_조사_마스터.csv")
TX_CSV = os.path.join(BASE_DIR, "실거래_이력_데이터베이스", "unicity_transaction_history.csv")
INFO_DIR = os.path.join(BASE_DIR, "단지별_정보")

try:
    df = pd.read_csv(MASTER_CSV, encoding='utf-8-sig')
except:
    df = pd.read_csv(MASTER_CSV, encoding='cp949')

for col in ['Total_Score', 'L_Grade', 'C_Grade', 'S_Grade', 'Base_Price_TenWork', 'Expansion_Fee_TenWork', 'Total_Acquisition_Cost']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

try:
    tx = pd.read_csv(TX_CSV, encoding='utf-8-sig')
    tx['price_만원'] = pd.to_numeric(tx['price_만원'], errors='coerce')
except:
    tx = pd.DataFrame()

# 면적 -> 평형 매핑: area_mapping.py 중앙 모듈에서 import (Single Source of Truth)
from area_mapping import AREA_TO_PYEONG

def get_line(ho):
    m = re.search(r'(\d+)', str(ho))
    return int(m.group(1)) % 100 if m else None

def get_floor(ho):
    m = re.search(r'(\d+)', str(ho))
    return int(m.group(1)) // 100 if m else None

def fmt_price(val):
    try:
        v = float(val)
        if v >= 100000000:
            uk = v / 100000000
            remainder = (v % 100000000) / 10000
            if remainder > 0:
                return f"{int(uk)}억 {int(remainder):,}만"
            return f"{int(uk)}억"
        elif v >= 10000:
            return f"{int(v/10000):,}만"
        return str(int(v))
    except:
        return str(val)

def fmt_manwon(val):
    try:
        v = float(val)
        if v >= 10000:
            uk = int(v / 10000)
            remain = int(v % 10000)
            if remain > 0:
                return f"{uk}억 {remain:,}만"
            return f"{uk}억"
        return f"{int(v):,}만"
    except:
        return str(val)

MGMT_FEE = {
    "1단지": {"25평":"15.2만","30평":"18만","35평":"21.5만","41평":"27만","47평":"34.1만","48평":"34.1만","56평":"34.1만+"},
    "2단지": {"25평":"18.3만","30평":"22만","35평":"25.9만","41평":"33만","47평":"41.2만","48평":"41.2만","56평":"-"},
    "3단지": {"25평":"12.2만","30평":"15만","35평":"17.3만","41평":"22만","47평":"27.5만","48평":"27.5만","56평":"-"},
    "4단지": {"25평":"14.5만","30평":"17만","35평":"20.5만","41평":"26만","47평":"32.6만","48평":"32.6만","56평":"32.6만+"},
}

def get_tx_summary(complex_name, pyeong=None):
    """실거래가 요약 - 단지별 or 단지+평형별"""
    if len(tx) == 0:
        return {}
    t = tx[tx['complex'] == complex_name].copy()
    if pyeong:
        matching_areas = [a for a, p in AREA_TO_PYEONG.items() if p == pyeong]
        t = t[t['area_m2'].astype(str).isin(matching_areas)]
    if len(t) == 0:
        return {}
    recent = t.sort_values('date', ascending=False).head(5)
    return {
        'min': int(t['price_만원'].min()),
        'max': int(t['price_만원'].max()),
        'avg': int(t['price_만원'].mean()),
        'recent_avg': int(recent['price_만원'].mean()),
        'count': len(t),
        'latest_date': str(recent['date'].iloc[0]),
        'latest_price': int(recent['price_만원'].iloc[0]),
    }

# ========== 단지방 ==========
def gen_complex_report(cname):
    cdir = os.path.join(INFO_DIR, cname)
    os.makedirs(cdir, exist_ok=True)
    df_c = df[df['Complex'] == cname]
    dongs = GROUND_TRUTH[cname]
    fees = MGMT_FEE.get(cname, {})
    
    L = []
    L.append(f"# 창원중동유니시티 {cname} 종합 정보\n")
    L.append(f"## 기본 정보")
    L.append(f"- **총 동수**: {len(dongs)}개동")
    L.append(f"- **총 세대수**: {len(df_c)}세대")
    L.append(f"- **동 목록**: {', '.join(sorted(dongs.keys()))}\n")
    
    L.append(f"## 평형별 세대 분포 + 실거래 시세")
    L.append(f"| 평형 | 세대수 | 비율 | 월관리비 | 최근실거래(만) | 실거래범위(만) | 건수 |")
    L.append(f"|:---|:---|:---|:---|:---|:---|:---|")
    if len(df_c) > 0:
        for p in sorted(df_c['Pyeong'].unique()):
            cnt = (df_c['Pyeong'] == p).sum()
            pct = f"{cnt/len(df_c)*100:.1f}%"
            fee = fees.get(str(p), '-')
            ts = get_tx_summary(cname, str(p))
            if ts:
                latest = fmt_manwon(ts['latest_price'])
                range_str = f"{fmt_manwon(ts['min'])} ~ {fmt_manwon(ts['max'])}"
                tx_cnt = ts['count']
            else:
                latest = "-"
                range_str = "-"
                tx_cnt = 0
            L.append(f"| {p} | {cnt} | {pct} | {fee} | {latest} | {range_str} | {tx_cnt} |")
    L.append("")
    
    L.append(f"## 등급 분포")
    L.append(f"| 등급 | 세대수 | 비율 |")
    L.append(f"|:---|:---|:---|")
    if 'Total_Grade' in df_c.columns:
        for g, cnt in df_c['Total_Grade'].value_counts().sort_index().items():
            L.append(f"| {g} | {cnt} | {cnt/len(df_c)*100:.1f}% |")
    L.append("")
    
    L.append(f"## 동별 요약")
    L.append(f"| 동 | 라인 | 세대 | 라인별 평형 | 평균점수 |")
    L.append(f"|:---|:---|:---|:---|:---|")
    for dn in sorted(dongs.keys()):
        dd = dongs[dn]
        df_d = df_c[df_c['Dong'] == dn]
        ts = ", ".join([f"{k}호:{v}" for k, v in sorted(dd.items())])
        avg = f"{df_d['Total_Score'].mean():.2f}" if len(df_d) > 0 else "-"
        L.append(f"| {dn} | {len(dd)} | {len(df_d)} | {ts} | {avg} |")
    L.append("")
    
    fp = os.path.join(cdir, f"{cname}_요약.md")
    with open(fp, 'w', encoding='utf-8') as f:
        f.write("\n".join(L))
    print(f"  [OK] {cname}_요약")

# ========== 동방 ==========
def gen_building_report(cname, dong):
    cdir = os.path.join(INFO_DIR, cname)
    os.makedirs(cdir, exist_ok=True)
    dt = GROUND_TRUTH[cname][dong]
    ds = STRUCTURE[cname][dong]
    df_d = df[(df['Complex'] == cname) & (df['Dong'] == dong)]
    fees = MGMT_FEE.get(cname, {})
    
    L = []
    L.append(f"# {cname} {dong} 종합 정보\n")
    L.append(f"## 건물 구조")
    L.append(f"- **라인 수**: {len(dt)}개")
    L.append(f"- **총 세대수**: {len(df_d)}세대")
    piloti = [f"{f}층{l:02d}호" for f, l in ds['piloti']]
    L.append(f"- **필로티**: {', '.join(piloti) if piloti else '없음'}\n")
    
    L.append(f"## 라인별 평형 매핑 (사용자 확인 - 절대 변경 금지)")
    L.append(f"| 라인 | 평형 | 타입 | 최고층 | 세대수 | 분양가(만) | 취득원가 | 관리비 | 최근실거래(만) |")
    L.append(f"|:---|:---|:---|:---|:---|:---|:---|:---|:---|")
    
    for ln in sorted(dt.keys()):
        ut = dt[ln]
        pyeong, tc = TYPE_MAP[ut]
        mf = ds['max'][ln]
        df_l = df_d[df_d['Ho'].apply(get_line) == ln]
        bp = "-"; ac = "-"
        if len(df_l) > 0:
            bpv = df_l['Base_Price_TenWork'].iloc[0]
            bp = f"{int(bpv):,}" if pd.notna(bpv) else "-"
            tcv = df_l['Total_Acquisition_Cost'].iloc[0]
            ac = fmt_price(tcv) if pd.notna(tcv) else "-"
        fee = fees.get(pyeong, '-')
        ts = get_tx_summary(cname, pyeong)
        latest_tx = fmt_manwon(ts['latest_price']) if ts else "-"
        L.append(f"| {ln}호 | {pyeong} | {tc} | {mf}층 | {len(df_l)} | {bp} | {ac} | {fee} | {latest_tx} |")
    L.append("")
    
    # 실거래 시세 요약 (동에 해당하는 평형들)
    pyeongs_in_dong = set(TYPE_MAP[dt[k]][0] for k in dt)
    L.append(f"## 실거래가 시세 요약 (네이버 부동산)")
    L.append(f"| 평형 | 최근거래가(만) | 실거래범위(만) | 건수 | 최근일자 |")
    L.append(f"|:---|:---|:---|:---|:---|")
    for p in sorted(pyeongs_in_dong):
        ts = get_tx_summary(cname, p)
        if ts:
            L.append(f"| {p} | {fmt_manwon(ts['latest_price'])} | {fmt_manwon(ts['min'])} ~ {fmt_manwon(ts['max'])} | {ts['count']}건 | {ts['latest_date']} |")
        else:
            L.append(f"| {p} | - | - | 0건 | - |")
    L.append("")
    
    L.append(f"## 등급 현황")
    if len(df_d) > 0:
        L.append(f"- **평균 점수**: {df_d['Total_Score'].mean():.2f}")
        for g, cnt in df_d['Total_Grade'].value_counts().sort_index().items():
            L.append(f"  - {g}등급: {cnt}세대")
    L.append("")
    
    L.append(f"## 전 세대 상세 현황")
    L.append(f"| 호수 | 층 | 라인 | 평형 | 등기명/점유 | 등급 | 점수 | 분양가(만) | 취득원가 |")
    L.append(f"|:---|:---|:---|:---|:---|:---|:---|:---|:---|")
    
    if len(df_d) > 0:
        dfs = df_d.copy()
        dfs['_f'] = dfs['Ho'].apply(get_floor)
        dfs['_l'] = dfs['Ho'].apply(get_line)
        dfs = dfs.sort_values(['_f', '_l'], ascending=[False, True])
        for _, r in dfs.iterrows():
            ho = r['Ho']
            fl = get_floor(ho) or ''
            ln = get_line(ho) or ''
            py = r.get('Pyeong', '')
            ow = str(r.get('Owner_Status', '')).replace('|', '/')
            gr = r.get('Total_Grade', '')
            sc = f"{r.get('Total_Score', 0):.1f}" if pd.notna(r.get('Total_Score')) else ''
            bpv = f"{int(r['Base_Price_TenWork']):,}" if pd.notna(r.get('Base_Price_TenWork')) else '-'
            tcv = fmt_price(r['Total_Acquisition_Cost']) if pd.notna(r.get('Total_Acquisition_Cost')) else '-'
            L.append(f"| {ho} | {fl} | {ln} | {py} | {ow} | {gr} | {sc} | {bpv} | {tcv} |")
    
    fp = os.path.join(cdir, f"{dong}.md")
    with open(fp, 'w', encoding='utf-8') as f:
        f.write("\n".join(L))
    print(f"  [OK] {dong}")

# ========== 실행 ==========
print("=" * 50)
print("v3 integrated info system (with transactions)")
print("=" * 50)

os.makedirs(INFO_DIR, exist_ok=True)
for cname in sorted(GROUND_TRUTH.keys()):
    print(f"\n[{cname}]")
    gen_complex_report(cname)
    for dong in sorted(GROUND_TRUTH[cname].keys()):
        gen_building_report(cname, dong)

print(f"\n{'=' * 50}")
print(f"[OK] {len(df)} units, {len(tx)} transactions integrated")
print(f"{'=' * 50}")
