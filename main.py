import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인 (따뜻한 톤)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="centered"
)

# 따뜻한 느낌을 주는 Custom CSS 적용
st.markdown("""
    <style>
    .main {
        background-color: #FFFDF9;
    }
    h1 {
        color: #8B4513;
        font-family: 'Nanum Gothic', sans-serif;
    }
    .stSelectbox label {
        color: #5C4033;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.caption("최신 연도 기준 전국 읍·면·동 성별/연령별 인구 분포를 확인해보세요.")

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 및 전처리 (캐싱 처리로 속도 향상)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # GitHub raw 주소의 zip/csv 파일 읽기 (pandas가 zip 파일 압축을 자동으로 해제합니다)
    url = "https://raw.githubusercontent.com/yunsoyul47/age/main/population_ts_yearly_gender(2).zip"
    df = pd.read_csv(url)
    
    # '연도' 열을 숫자로 변환 후 가장 최신 연도 데이터만 추출
    df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 로딩
try:
    with st.spinner("동네별 인구 데이터를 불러오는 중입니다... ☕"):
        df_data, latest_year = load_data()
    st.success(f"데이터를 성공적으로 불러왔습니다! (기준 연도: {int(latest_year)}년)")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사용자 지역 선택 (시도 -> 시군구 -> 동 3단계 드롭다운)
# -----------------------------------------------------------------------------
st.subheader("📍 지역 선택")
col1, col2, col3 = st.columns(3)

# 1) 시도 선택
sido_list = sorted(df_data['시도'].dropna().unique())
with col1:
    selected_sido = st.selectbox("시·도 선택", sido_list)

# 2) 시군구 선택 (선택된 시도 내 데이터만 필터링)
sigungu_list = sorted(df_data[df_data['시도'] == selected_sido]['시군구'].dropna().unique())
with col2:
    selected_sigungu = st.selectbox("시·군·구 선택", sigungu_list)

# 3) 읍·면·동 선택 (선택된 시도 및 시군구 내 데이터만 필터링)
dong_list = sorted(df_data[(df_data['시도'] == selected_sido) & (df_data['시군구'] == selected_sigungu)]['동'].dropna().unique())
with col3:
    selected_dong = st.selectbox("읍·면·동 선택", dong_list)

# -----------------------------------------------------------------------------
# 4. 선택한 동네의 남/여 연령별 인구 데이터 추출
# -----------------------------------------------------------------------------
# 선택 조건에 맞는 1개 행 추출
target_row = df_data[
    (df_data['시도'] == selected_sido) & 
    (df_data['시군구'] == selected_sigungu) & 
    (df_data['동'] == selected_dong)
]

# 나이 라벨 생성 (0세부터 99세까지는 'N세', 마지막은 '100세 이상')
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

male_pop = []
female_pop = []

if not target_row.empty:
    row = target_row.iloc[0]
    for age in age_labels:
        # 데이터프레임 컬럼명 규칙: '남_0세', '여_0세', ..., '남_100세 이상', '여_100세 이상'
        m_col = f"남_{age}"
        f_col = f"여_{age}"
        
        # 값이 없을 경우 0으로 대체
        m_val = row[m_col] if m_col in row and not pd.isna(row[m_col]) else 0
        f_val = row[f_col] if f_col in row and not pd.isna(row[f_col]) else 0
        
        male_pop.append(m_val)
        female_pop.append(f_val)

# 피라미드 그래프 작성을 위해 남성 인구수는 음수로 전환
male_pop_neg = [-val for val in male_pop]

# -----------------------------------------------------------------------------
# 5. Plotly 인구 피라미드 (가로 막대그래프) 그리기
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"📊 {selected_sido} {selected_sigungu} {selected_dong} 인구 피라미드")

fig = go.Figure()

# 남성 데이터 (왼쪽, 음수 처리) - 따뜻한 네이비/블루 톤 (#4C72B0)
fig.add_trace(go.Bar(
    y=age_labels,
    x=male_pop_neg,
    name='남자',
    orientation='h',
    marker=dict(color='#4C72B0'),
    hoverinfo='text',
    # 마우스 호버 시 음수가 아닌 양수 값으로 표시
    hovertext=[f"남자 {age}: {val:,}명" for age, val in zip(age_labels, male_pop)]
))

# 여성 데이터 (오른쪽, 양수) - 따뜻한 코랄/살구 톤 (#DD8452)
fig.add_trace(go.Bar(
    y=age_labels,
    x=female_pop,
    name='여자',
    orientation='h',
    marker=dict(color='#DD8452'),
    hoverinfo='text',
    hovertext=[f"여자 {age}: {val:,}명" for age, val in zip(age_labels, female_pop)]
))

# -----------------------------------------------------------------------------
# 6. 세로축(나이) 순서 고정 및 레이아웃 설정
# -----------------------------------------------------------------------------
# 축 뒤집기(autorange="reversed")나 값 크기 정렬을 사용하지 않고,
# categoryorder='array'와 categoryarray를 통해 아래(0세)에서 위(100세 이상) 순서로 명시적으로 고정합니다.
fig.update_layout(
    barmode='overlay',
    bargap=0.1,
    title=dict(
        text=f"{selected_dong} 연령별 성별 인구 분포 ({int(latest_year)}년)",
        font=dict(size=16)
    ),
    xaxis=dict(
        title="인구수 (명)",
        tickformat="s",  # K, M 표기 또는 깔끔한 정수 표기
        # x축 눈금에 음수가 보이지 않도록 절대값 사용 호버 설정 처리됨
    ),
    yaxis=dict(
        title="연령",
        type='category',
        categoryorder='array',
        categoryarray=age_labels,  # 0세부터 100세 이상 순서 그대로 세로축에 아래->위로 배치
        tickmode='linear',
        dtick=10  # 눈금이 너무 촘촘하지 않게 10세 단위로 라벨 표시
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    height=750,
    paper_bgcolor='#FFFDF9',
    plot_bgcolor='#FFFFFF'
)

# 스트림릿 화면에 그래프 출력
st.plotly_chart(fig, use_container_width=True)
