# streamlit_genetic_evolution.py
# ✅ Colab 자동 실행 지원 포함 + GitHub 연동 자동 분석 로그 생성
# 사용 예시 (Colab):
# !pip install streamlit pyngrok -q
# from pyngrok import ngrok
# !streamlit run streamlit_genetic_evolution.py &>/content/log.txt &
# print("🔄 Streamlit 실행 중...")
# url = ngrok.connect(port=8501)
# print(f"🌐 접속 링크: {url}")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import pyupbit
from datetime import datetime
import time

st.set_page_config(page_title="🧬 유전 알고리즘 진화 과정", layout="wide")
st.title("📈 넥키토 전략 조합 유전 알고리즘 진화 추적")

# Colab 또는 GitHub에서 자동 생성된 로그 경로 확인 함수
def resolve_path():
    possible_paths = [
        "/content/evolution_log.csv",  # Colab
        "./evolution_log.csv",         # 로컬 실행
        "/workspace/evolution_log.csv", # GitHub Codespaces
        os.path.join(os.getcwd(), "evolution_log.csv")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

log_path = resolve_path()

try:
    if log_path:
        # 최고 수익 조합 저장 파일 초기화
        best_output_path = os.path.join(os.path.dirname(log_path), "best_combo_only.csv")
        df = pd.read_csv(log_path)
        df['iteration'] = df['iteration'].astype(int)
        df['avg_profit'] = df['avg_profit'].astype(float)

        st.line_chart(
            df.groupby("iteration")["avg_profit"].mean().rolling(window=100).mean(),
            height=400,
            use_container_width=True
        )

        top_combos = df.groupby("combo_key")["avg_profit"].max().sort_values(ascending=False).head(10)
        st.subheader("🏆 평균 수익률 상위 10개 조합")
        top_df = top_combos.reset_index().rename(columns={"combo_key": "조건 조합", "avg_profit": "최고 평균 수익(₩)"})
        st.table(top_df)
        top_df.to_csv(best_output_path, index=False)

        # ✅ API 키 UI 입력 지원
        with st.expander("🔐 API 키 입력 (보안 환경에서만 사용하세요)"):
            ACCESS_KEY = st.text_input("Upbit ACCESS_KEY", type="password")
            SECRET_KEY = st.text_input("Upbit SECRET_KEY", type="password")
        if ACCESS_KEY and SECRET_KEY:
            upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)
        else:
            upbit = None

        selected_combo = top_df.iloc[0]['조건 조합'].split('_')
        st.success(f"🚀 실전 자동매매 전략으로 반영된 조합: {selected_combo}")

        # ✅ 조건 충족 시 실전 자동 체결 실행
        st.divider()
        st.subheader("🤖 실전 체결 시뮬레이션")
        if upbit:
            try:
                order = upbit.buy_market_order("KRW-BTC", 10000)
                time.sleep(1)
                sell_order = upbit.sell_market_order("KRW-BTC", 10000)
                st.success("💸 실전 매수 체결 완료!")
                st.json(order)
                st.success("💰 실전 매도 체결 완료!")
                st.json(sell_order)
            except Exception as e:
                st.error(f"❌ 실전 체결 실패: {e}")
        else:
            st.warning("🔑 실전 자동매매를 위해 ACCESS_KEY와 SECRET_KEY 환경 변수가 필요합니다.")

        # 📊 오늘 실전매매 시뮬레이션
        st.subheader("📊 오늘 실전매매 시뮬레이션")
        today_df = df[df['combo_key'] == top_df.iloc[0]['조건 조합']]
        if not today_df.empty:
            total_profit = today_df['avg_profit'].sum()
            trade_count = len(today_df)
            st.markdown(f"**총 거래 횟수:** {trade_count} 회")
            st.markdown(f"**총 수익률:** {total_profit:,.2f}₩")
        else:
            st.warning("❗ 선택된 조합으로 오늘 실행된 매매가 없습니다.")
    else:
        st.warning("❗ evolution_log.csv 파일이 없습니다. Colab에 업로드하거나 GitHub에서 자동 생성되도록 설정하세요.")

except Exception as e:
    st.error(f"에러 발생: {e}")
