
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import requests
import pyupbit
import json

# ====== 전략 자동 불러오기 ======
def load_strategy(filepath="nekito_strategy_87_5_20250411_094606.json"):
    with open(filepath, 'r') as f:
        return json.load(f)

strategy = load_strategy()

rsi_threshold = strategy['rsi_threshold']
volume_multiplier = strategy['volume_multiplier']
hour_start = strategy['hour_start']
hour_end = strategy['hour_end']
use_bb = strategy['use_bb']
use_macd = strategy['use_macd']

# ====== 업비트 키 등록 ======
ACCESS_KEY = "YOUR_ACCESS_KEY"
SECRET_KEY = "YOUR_SECRET_KEY"
upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)

# ====== 텔레그램 정보 ======
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# ====== 데이터 업로드 ======
st.title("💹 넥키토 자동 전략 대시보드")
uploaded_file = st.file_uploader("📁 CSV 파일 업로드", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['time'] = pd.to_datetime(df['snapped_at'])
    df['hour'] = df['time'].dt.hour
    df.rename(columns={'price': 'close', 'total_volume': 'volume'}, inplace=True)

    # 기술지표 계산
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['volume_ma'] = df['volume'].rolling(window=5).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']

    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_cross'] = df['MACD'] > df['MACD_signal']

    df['strategy_match'] = (
        (df['RSI'] < rsi_threshold) &
        (df['volume_ratio'] > volume_multiplier) &
        (df['hour'].between(hour_start, hour_end))
    )
    if use_macd:
        df['strategy_match'] &= df['MACD_cross']

    df['future_close'] = df['close'].shift(-3)
    df['return_%'] = ((df['future_close'] - df['close']) / df['close']) * 100
    df['result'] = np.where(df['return_%'] >= 1, 'SUCCESS', 'FAILURE')

    matched = df[df['strategy_match']]
    st.success(f"✅ 전략 조건에 맞는 시그널 {len(matched)}개 탐지됨")

    st.dataframe(matched[['time', 'close', 'RSI', 'volume_ratio', 'return_%', 'result']])

    # 자동매매 실행
    if st.button("🚀 실전 자동매수 실행"):
        current_price = matched['close'].iloc[-1]
        send_telegram_message(f"🚨 [Nekito] 전략 시그널 발생! RSI<{rsi_threshold}, 거래량 x{volume_multiplier}\n현재가: {current_price}")
        order = upbit.buy_market_order("KRW-SOL", 10000)  # 1만원 매수
        st.success(f"🟢 매수 주문 실행됨: {order}")
