# ============================================================
# 창원 유니시티 면적-평형 매핑 정의 (Single Source of Truth)
# ============================================================
# 이 파일은 모든 스크립트가 import하는 면적 매핑 중앙 모듈입니다.
# ⚠️ 이 파일을 수정하면 전체 시스템에 영향을 미칩니다.
# 
# 검증 공식: 평형 × 3.3058 ≈ 공급면적 (허용 오차 ±5%)
# 검증일: 2026-03-09 (MOLIT + 네이버 부동산 교차검증 완료)
# ============================================================

# ──────────────────────────────────────────────
# 1. 정규 매핑 테이블 (절대 변경 금지)
# ──────────────────────────────────────────────

AREA_TO_PYEONG = {
    # 25평 (전용 59㎡, 공급 82~85㎡, 검증: 25×3.3=82.6)
    '82': '25평', '83': '25평', '84': '25평', '85': '25평',
    # 30평 (전용 72㎡, 공급 100~102㎡, 검증: 30×3.3=99.2)
    '100': '30평', '102': '30평',
    # 35평 (전용 84㎡, 공급 115~117㎡, 검증: 35×3.3=115.7)
    '115': '35평', '115A': '35평A', '115B': '35평B',
    '116': '35평', '116B': '35평B',
    '117': '35평', '117A': '35평A',
    # 41평 (전용 99㎡, 공급 136~138㎡, 검증: 41×3.3=135.3)
    # ⚠️ 136/138은 41평임! 56평이 아님!
    '136': '41평', '138': '41평',
    # 47평 (전용 115.72㎡, 공급 153~158㎡, 검증: 47×3.3=155.1)
    '153': '47평', '158': '47평',
    # 56평 (전용 135.9㎡, 공급 185A/186B, 검증: 56×3.3=184.9)
    # ⚠️ 185A/186B만 56평! 136/138은 41평!
    '185A': '56평A', '186B': '56평B',
    # 63평 (전용 158㎡, 공급 210~211㎡, 검증: 63×3.3=208.3)
    '210': '63평', '211': '63평',
}

# 평형별 가격 허용 범위 (만원, 2026-03 기준)
PRICE_RANGE = {
    '25평': (50000, 80000),
    '30평': (65000, 95000),
    '35평': (75000, 105000),
    '35평A': (75000, 105000),
    '35평B': (75000, 105000),
    '41평': (95000, 130000),
    '47평': (120000, 160000),
    '56평A': (140000, 190000),
    '56평B': (140000, 190000),
    '63평': (170000, 230000),
}

# 단지별 존재하는 평형 (ground_truth.py 기반)
COMPLEX_TYPES = {
    '1단지': {'25평', '30평', '35평A', '35평B', '41평', '47평', '56평A', '56평B'},
    '2단지': {'25평', '30평', '35평A', '35평B', '41평'},           # ⚠️ 56평 없음!
    '3단지': {'25평', '35평A', '35평B', '41평'},
    '4단지': {'25평', '30평', '35평A', '35평B', '41평', '48평', '56평A', '56평B'},
    '어반브릭스': {'10평', '17평', '25평'},
}

OFFICETEL_MAPPING = {
    '22.64': '10평', '77': '10평', '77.28': '10평',
    '38.56': '17평', '106': '17평', '106.58': '17평',
    '59.5': '25평', '59.50': '25평', '59.6': '25평', '59.60': '25평',
    '143': '25평', '143.34': '25평', '143.53': '25평', '144': '25평', '144.47': '25평'
}


# ──────────────────────────────────────────────
# 2. 검증 함수
# ──────────────────────────────────────────────

def validate_area(area_m2: str, complex_name: str = None) -> str:
    """area_m2 → 평형 변환. 미등록 면적이면 예외 발생."""
    area = str(area_m2).strip()
    
    if complex_name == '어반브릭스':
        pyeong = OFFICETEL_MAPPING.get(area)
        if pyeong:
            return pyeong
            
    pyeong = AREA_TO_PYEONG.get(area)
    if pyeong is None:
        raise ValueError(
            f"[ERROR] 미등록 면적: area_m2='{area}'\n"
            f"   등록된 면적: {sorted(AREA_TO_PYEONG.keys())}\n"
            f"   새 면적 추가 시 area_mapping.py를 먼저 수정하세요."
        )
    return pyeong


def validate_price(area_m2: str, price: int, complex_name: str = None) -> list:
    """가격 상식 검증. 경고 목록 반환 (빈 리스트 = 정상)."""
    warnings = []
    pyeong = validate_area(area_m2, complex_name)

    # 가격 범위 검증
    lo, hi = PRICE_RANGE.get(pyeong, (0, 999999))
    if complex_name == '어반브릭스':
        if pyeong == '25평': lo, hi = 25000, 40000
        elif pyeong == '17평': lo, hi = 15000, 25000
        elif pyeong == '10평': lo, hi = 8000, 15000
        
    if price < lo or price > hi:
        warnings.append(
            f"[WARN] 가격 범위 벗어남: {pyeong} {price/10000:.1f}억 "
            f"(허용: {lo/10000:.0f}~{hi/10000:.0f}억)"
        )

    # 단지-평형 교차검증
    if complex_name:
        allowed = COMPLEX_TYPES.get(complex_name, set())
        # 평형 기본명 추출 (35평A → 35평A, 41평 → 41평)
        if allowed and pyeong not in allowed:
            # 기본 평형명으로도 확인 (35평A → 35평 체크)
            base_pyeong = pyeong.rstrip('AB')
            if base_pyeong not in allowed and pyeong not in allowed:
                warnings.append(
                    f"[ERROR] {complex_name}에 {pyeong} 세대 없음! "
                    f"({complex_name} 보유 평형: {sorted(allowed)})"
                )

    return warnings


def validate_trade_record(date: str, complex_name: str, floor: int,
                          area_m2: str, price: int) -> list:
    """실거래 기록 전체 검증. 경고 목록 반환."""
    warnings = []

    # 1. 면적 검증
    try:
        pyeong = validate_area(area_m2, complex_name)
    except ValueError as e:
        return [str(e)]

    # 2. 가격 검증
    warnings.extend(validate_price(area_m2, price, complex_name))

    # 3. 층수 검증
    if floor <= 0 or floor > 50:
        warnings.append(f"[WARN] 비정상 층수: {floor}층")

    return warnings


# ──────────────────────────────────────────────
# 3. 셀프 테스트 (실행 시 자동 검증)
# ──────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("면적-평형 매핑 셀프 검증")
    print("=" * 60)

    # 공식 검증: 평형 × 3.3058 ≈ 공급면적
    formula_checks = [
        ('25평', 25, [82, 83, 84, 85]),
        ('30평', 30, [100, 102]),
        ('35평', 35, [115, 116, 117]),
        ('41평', 41, [136, 138]),
        ('47평', 47, [153, 158]),
        ('56평', 56, [185, 186]),
        ('63평', 63, [210, 211]),
    ]
    all_ok = True
    for name, pyeong_num, areas in formula_checks:
        expected = pyeong_num * 3.3058
        for a in areas:
            diff_pct = abs(a - expected) / expected * 100
            status = "OK" if diff_pct < 8 else "FAIL"
            if status == "FAIL":
                all_ok = False
            print(f"  {status} {name}: {pyeong_num}x3.3={expected:.0f} vs 실제 {a} ({diff_pct:.1f}%)")

    # 금지 매핑 검증 (과거 오류가 재발하지 않는지 확인)
    print("\n금지 매핑 검증 (과거 오류 재발 방지):")
    forbidden = [
        ('100', '41평', '100은 30평이어야 함'),
        ('102', '41평', '102는 30평이어야 함'),
        ('136', '56평', '136은 41평이어야 함'),
        ('136', '56평A', '136은 41평이어야 함'),
        ('138', '56평B', '138은 41평이어야 함'),
        ('158', '63평', '158은 47평이어야 함'),
    ]
    for area, wrong_pyeong, reason in forbidden:
        actual = AREA_TO_PYEONG.get(area, '?')
        if actual == wrong_pyeong:
            print(f"  FAIL {area} → {actual} ({reason})")
            all_ok = False
        else:
            print(f"  OK   {area} → {actual} (≠ {wrong_pyeong})")

    # 2단지 56평 없음 검증
    print("\n단지-평형 교차검증:")
    warnings = validate_price('185A', 170000, '2단지')
    if warnings:
        print(f"  OK   2단지+185A → 경고 발생: {warnings[0]}")
    else:
        print(f"  FAIL 2단지+185A → 경고 미발생 (2단지에 56평 없어야 함)")
        all_ok = False

    print(f"\n{'='*60}")
    print(f"결과: {'[PASS] 전체 PASS' if all_ok else '[FAIL] 오류 있음'}")
    print(f"{'='*60}")
