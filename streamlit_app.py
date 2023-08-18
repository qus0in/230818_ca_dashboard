import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

@st.cache_resource
def 종목목록가져오기():
    return pd.read_csv('ticker.csv').sort_values('TICKER')

@st.cache_data
def 환율가져오기() -> pd.Series:
    df : pd.DataFrame = yf.download('KRW=X').Close
    df.index = df.index.date
    return df

@st.cache_data
def 종목시세가져오기(종목코드) -> pd.Series:
    시세 : pd.DataFrame = yf.download(종목코드)[['Close']]
    시세.index = 시세.index.date
    환율 = 환율가져오기()
    환율적용시세 = 시세.join(환율, rsuffix='exchange_', how='inner')\
    .product(axis=1).astype(int).rename('가격')
    return 환율적용시세

def 종목분석가져오기(종목코드):
    종목시세 = 종목시세가져오기(종목코드)
    단순이평선200 = 종목시세.rolling(200, min_periods=200)\
        .mean().dropna().astype(int).rename('SMA200')
    지수이평선200 = 종목시세.ewm(200, min_periods=200)\
        .mean().dropna().astype(int).rename('EMA200')
    return pd.concat([종목시세, 단순이평선200, 지수이평선200],\
                      axis=1, join='inner').tail(200)

def 종목필터링(진입=False, 편출=False):
    종목목록 = 종목목록가져오기().TICKER
    종목분석목록 = [(종목코드, 종목분석가져오기(종목코드).iloc[-1]) for 종목코드 in 종목목록.iloc[:]]
    if 진입:
        return [종목코드 for 종목코드, 종목분석 in 종목분석목록
            if (종목분석.가격 > 종목분석.SMA200 and 종목분석.가격 > 종목분석.EMA200)]
    if 편출:
        return [종목코드 for 종목코드, 종목분석 in 종목분석목록
            if (종목분석.가격 < 종목분석.SMA200 and 종목분석.가격 < 종목분석.EMA200)]
    return [종목코드 for 종목코드, 종목분석 in 종목분석목록
            if (종목분석.가격 > 종목분석.SMA200 or 종목분석.가격 > 종목분석.EMA200)]


def 종목차트가져오기(종목코드):
    data = 종목분석가져오기(종목코드)
    fig = px.line(data, height=250)
    fig.update_layout(
        title=종목코드,
        legend=dict(title='데이터'),
        xaxis=dict(title='날짜'),
        yaxis=dict(title='원화가격'))
    return fig

if __name__ == '__main__':
    st.set_page_config(
        page_title='모을까 말까',
        page_icon='🍨'
    )

    st.title('🧀 코스트 애버리징')
    종목목록 = 종목목록가져오기()

    필터링 = st.radio('🫘 종목 필터링', [
        '👀 없음', '😴 유지', '🫠 편출'
    ], index=1, horizontal=True)
    필터링종목목록: list = 종목목록.TICKER.copy()
    if 필터링 == '😴 유지':
        필터링종목목록 = 종목필터링()
    if 필터링 == '🫠 편출':
        필터링종목목록 = 종목필터링(편출=True)
    선택된종목목록 = st.multiselect(
        '☕ 종목 찾기', 종목목록,
        default=필터링종목목록,
        placeholder='체크할 종목 선택')
    st.write(f'💪 종목 수 : {len(필터링종목목록)}개')

    # for 종목코드 in 선택된종목목록:
    for i in range((len(선택된종목목록) + 1) // 2):
        col1, col2 = st.columns(2)
        i1 = i * 2
        i2 = i * 2 + 1
        col1.plotly_chart(
            종목차트가져오기(선택된종목목록[i1]),
            use_container_width=True)
        if len(선택된종목목록) == i2:
            break
        col2.plotly_chart(
            종목차트가져오기(선택된종목목록[i2]),
            use_container_width=True)
