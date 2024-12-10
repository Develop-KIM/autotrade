import os
from dotenv import load_dotenv
load_dotenv()

import pyupbit
import pandas as od
import ta
from ta.utils import dropna

def add_indicators(df):
    # 볼린저 밴드
    indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_bbm' ] = indicator_bb.bollinger_mavg()
    df['bb_bbh' ] = indicator_bb.bollinger_hband()
    df['bb_bbl'] = indicator_bb.bollinger_lband()

    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()

    # MACD
    macd = ta.trend.MACD(close=df['close' ])
    df ['macd' ] = macd.macd()
    df['macd_signal' ] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()

    # 이동평균선
    df['sma_20'] = ta.trend.SMAIndicator(close=df['close' ], window=20).sma_indicator()
    df['ema_12'] = ta.trend.EMAIndicator(close=df['close' ], window=12).ema_indicator()

    return df

# 30일 일봉 데이터 가져오기
df_daily = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=30)
df_daily = dropna(df_daily)
df_daily = add_indicators(df_daily)

# 24시간 시간봉 데이터 가져오기
df_hourly = pyupbit.get_ohlcv("KRW-BTC", interval="minute60", count=24)
df_hourly = dropna(df_hourly)
df_hourly = add_indicators(df_hourly)

print("일봉 데이터 (마지막 5행):")
print(df_daily.tail())

print("\n시간봉 데이터 (마지막 5행):")
print(df_hourly.tail())