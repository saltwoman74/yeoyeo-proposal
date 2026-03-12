import streamlit as st
import pandas as pd
import datetime
import urllib.request
import json
import os
import sys

# 추가 폴더 경로 설정 (generate_proposal 등 기존 모듈 불러오기 위해)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from generate_proposal import save_proposal

# 화면 설정 (Wider and Cooler)
st.set_page_config(page_title="VIP 거래 협상 제안서", layout="wide")

# Custom CSS for a premium, wider look
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 95%;
    }
    .st-emotion-cache-1y4p8pa {
        padding-top: 2rem;
    }
    .premium-header {
        background: linear-gradient(135deg, #0f3460, #1a1a2e);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .section-header {
        border-bottom: 2px solid #e94560;
        padding-bottom: 8px;
        margin-bottom: 20px;
        color: #0f3460;
    }
    /* 입력 정보 텍스트 크기 17px, 카테고리 제목 크기 19px, 볼드체 제거 */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
        font-size: 19px !important;
        font-weight: normal !important;
    }
    input, textarea, .stSelectbox div[data-baseweb="select"] {
        font-size: 17px !important;
        font-weight: normal !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-weight: normal !important;
    }
    .stMarkdown h2, .stMarkdown h3 {
        font-size: 19px !important;
        font-weight: normal !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="premium-header"><h1 style="font-weight:normal;">VIP 거래 협상 제안서 자동발행 대시보드</h1><p style="font-size: 17px; color:#ddd;">실시간 데이터 연동 및 맞춤형 인텔리전스 편집 시스템</p></div>', unsafe_allow_html=True)

# 구글 시트 링크
SHEET_ID = "18wOKWY40CbJECrvDuqit5hOKTqVWxyMCVRI1BJuWu2s"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# --- 1단계: 넓은 입력 대시보드 (3단 컬럼) ---
st.markdown('<h2 class="section-header">제안서 기본 및 참고 정보 입력</h2>', unsafe_allow_html=True)

col_input1, col_input2, col_input3 = st.columns([1, 1, 1])

with col_input1:
    st.markdown("<h3>필수 타겟 정보</h3>", unsafe_allow_html=True)
    dong_input = st.text_input("아파트 동 (예: 111)", "111")
    ho_input = st.text_input("아파트 호수 (예: 1904)", "1904")
    asking_price = st.number_input("매도자 현재 호가 (만원)", min_value=10000, value=98500, step=100)
    owner_status = st.selectbox("현재 점유 상태", ["소유자 거주", "세입자 거주 (전월세)", "공실", "상태 미상"])

with col_input2:
    st.markdown("<h3>협상 특이사항 및 요점</h3>", unsafe_allow_html=True)
    special_notes = st.text_area("현장 방문 결과, 매도자/매수자 특이사항", 
                                 "집주인 매도 의지 강함. 8월 말 빠른 잔금 조건 시 추가 가격조정 가능성 매우 높음.", height=130)
    
    st.markdown("<h3>참고 관련 정보 (추가)</h3>", unsafe_allow_html=True)
    ref_info = st.text_area("학군, 인테리어 타공 여부, 뷰 스팟 등", 
                            "거실 뷰 가림 없음. 2년 전 샷시 포함 올수리 완료.", height=100)

with col_input3:
    st.markdown("<h3>수동 오버라이드 (우선 적용)</h3>", unsafe_allow_html=True)
    st.info("비워두면 API 자동 수집값이 들어갑니다. 직접 입력 시 이 값이 최우선으로 보고서에 적용됩니다.")
    manual_bok_rate = st.text_input("수동 기준금리 입력 (%)", placeholder="예: 3.25 (입력시 우선 적용)")
    manual_trade_trend = st.text_input("수동 시장 분위기", placeholder="예: 최근 급매물 소진 중, 상승 전환기")
    
    st.markdown("---")
    bok_api_key = st.text_input("한국은행 API 키", type="password", value="DKL6JFPY68PDAL7P1D2C")


# --- 가운데 생성 버튼 ---
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    generate_btn = st.button("위 정보로 프리미엄 제안서 생성하기", use_container_width=True, type="primary")
st.markdown("<hr>", unsafe_allow_html=True)


# --- 하단: 데이터 연동 및 최종 출력 화면 ---
col_data, col_report = st.columns([1.2, 2.5])

with col_data:
    st.markdown('<h3 class="section-header">실시간 Market Data</h3>', unsafe_allow_html=True)
    
    # 한국은행 API 처리 및 우선순위 로직
    final_bok_rate = "3.50"
    is_manual_rate = False
    
    if manual_bok_rate.strip():
        final_bok_rate = manual_bok_rate.strip()
        is_manual_rate = True
    elif bok_api_key:
        try:
            today = datetime.datetime.now().strftime('%Y%m%d')
            url = f"https://ecos.bok.or.kr/api/StatisticSearch/{bok_api_key}/json/kr/1/1/722Y001/D/{today}/{today}/0101000"
            req = urllib.request.Request(url)
            res = urllib.request.urlopen(req, timeout=5)
            data = json.loads(res.read().decode('utf-8'))
            final_bok_rate = data['StatisticSearch']['row'][0]['DATA_VALUE']
        except Exception:
            pass # Fallback to 3.50
            
    if is_manual_rate:
        st.success(f"적용된 기준금리: **{final_bok_rate}%** (수동 입력 우선 적용됨)")
    else:
        st.info(f"현재 기준금리: **{final_bok_rate}%** (한국은행 ECOS 자동 연동)")

    # 구글 시트 데이터
    st.markdown('<br><h4>경쟁 광고 매물 (구글 시트)</h4>', unsafe_allow_html=True)
    try:
        df = pd.read_csv(SHEET_URL)
        df = df.fillna('')
        st.dataframe(df.head(10), use_container_width=True, height=400)
    except Exception as e:
        st.error(f"구글 시트를 불러오지 못했습니다: {e}")

with col_report:
    st.markdown('<h3 class="section-header">최종 제안서 출력 (수정 가능)</h3>', unsafe_allow_html=True)
    
    if generate_btn:
        with st.spinner("빅데이터 엔진 분석 및 제안서 렌더링 중..."):
            try:
                # 1. 제안서 엔진 호출
                filepath = save_proposal(dong=dong_input, ho=ho_input, trade_type='매매', asking_price=asking_price)
                
                html_filepath = filepath.replace('.md', '.html')
                
                if os.path.exists(html_filepath):
                    with open(html_filepath, 'r', encoding='utf-8') as f:
                        html_code = f.read()

                    # 2. 강제 Inject (수동 정보 등 융합)
                    final_market_trend = manual_trade_trend if manual_trade_trend.strip() else "현재 보합세이므로, 적극적인 협상이 필요한 시점입니다."
                    
                    injection = f"""
                    <div style="background:#f1f8ff; padding:20px; margin:25px 0; border-radius: 8px; border-left:5px solid #0f3460;">
                        <h3 style="color:#0f3460; margin-top:0; border-bottom:1px solid #ddd; padding-bottom:10px;">YEOYEO 현장 인텔리전스 (Special Note)</h3>
                        <p style="font-size: 13pt;"><strong>핵심 특징 및 참고정보:</strong> {ref_info}</p>
                        <p style="font-size: 13pt; color: #cc0000;"><strong>협상 요점:</strong> {special_notes}</p>
                        <hr style="border-top:1px dashed #ccc; margin:15px 0;">
                        <p><strong>점유 상태:</strong> {owner_status}</p>
                        <p><strong>반영된 기준금리:</strong> {final_bok_rate}% / <strong>시장 분위기:</strong> {final_market_trend}</p>
                    </div>
                    """
                    
                    html_code = html_code.replace("<h2>2. 세대 가치 및 입지 분석</h2>", injection + "<h2>2. 세대 가치 및 입지 분석</h2>")

                    # 3. HTML을 편집 가능하게
                    if "<body>" in html_code:
                        html_code = html_code.replace("<body>", '<body contenteditable="true">')

                    st.components.v1.html(html_code, height=900, scrolling=True)
                    st.success("🎉 제안서 생성이 완료되었습니다. 위 화면의 텍스트를 마우스로 직접 클릭하여 워드처럼 편집한 뒤 인쇄(Ctrl+P) 하세요.")

                else:
                    st.error("HTML 제안서가 정상적으로 생성되지 않았습니다.")
            except Exception as e:
                st.error(f"결과 생성 중 에러 발생: {e}")
    else:
        st.write("""
        1. 👈 좌측 대시보드에 필요한 정보를 입력하세요.
        2. 수집된 API 데이터보다 우선하고 싶은 수치가 있다면 **수동 오버라이드** 칸에 입력하세요.
        3. **[제안서 생성하기]** 버튼을 누르면 이 곳에 결과가 출력됩니다.
        """)
