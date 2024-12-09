import os
from dotenv import load_dotenv
import pyupbit
import pandas as pd
import json
from openai import OpenAI
import ta
from ta.utils import dropna
import time

load_dotenv()

def add_indicators(df):
    indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_bbm'] = indicator_bb.bollinger_mavg()
    df['bb_bbh'] = indicator_bb.bollinger_hband()
    df['bb_bbl'] = indicator_bb.bollinger_lband()
    
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
    
    macd = ta.trend.MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()
    
    df['sma_20'] = ta.trend.SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['ema_12'] = ta.trend.EMAIndicator(close=df['close'], window=12).ema_indicator()
    
    return df

def ai_trading():
    access = os.getenv("UPBIT_ACCESS_KEY")
    secret = os.getenv("UPBIT_SECRET_KEY")
    upbit = pyupbit.Upbit(access, secret)

    all_balances = upbit.get_balances()
    filtered_balances = [balance for balance in all_balances if balance['currency'] in ['BTC', 'KRW']]
    
    orderbook = pyupbit.get_orderbook("KRW-BTC")

    df_daily = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=30)
    df_daily = dropna(df_daily)
    df_daily = add_indicators(df_daily)
    
    df_hourly = pyupbit.get_ohlcv("KRW-BTC", interval="minute60", count=24)
    df_hourly = dropna(df_hourly)
    df_hourly = add_indicators(df_hourly)

    client = OpenAI()

    response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
        "role": "system",
        "content": """You are an expert in Bitcoin investing. Analyze the provided data including technical indicators and tell me whether to buy, sell, or hold at the moment. Consider the following indicators in your analysis:
        - Bollinger Bands (bb_bbm, bb_bbh, bb_bbl)
        - RSI (rsi)
        - MACD (macd, macd_signal, macd_diff)
        - Moving Averages (sma_20, ema_12)
        
        Response in json format.

        Response Example:
        {"decision": "buy", "reason": "some technical reason"}
        {"decision": "sell", "reason": "some technical reason"}
        {"decision": "hold", "reason": "some technical reason"}"""
        },
        {
        "role": "user",
        "content": f"Current investment status: {json.dumps(filtered_balances)}\nOrderbook: {json.dumps(orderbook)}\nDaily OHLCV with indicators (30 days): {df_daily.to_json()}\nHourly OHLCV with indicators (24 hours): {df_hourly.to_json()}"
        }
    ],
    response_format={
        "type": "json_object"
    }
    )
    result = response.choices[0].message.content

    result = json.loads(result)

    print("### AI Decision: ", result["decision"].upper(), "###")
    print(f"### Reason: {result['reason']} ###")

    if result["decision"] == "buy":
        my_krw = upbit.get_balance("KRW")
        if my_krw*0.9995 > 5000:
            print("### Buy Order Executed ###")
            print(upbit.buy_market_order("KRW-BTC", my_krw * 0.9995))
        else:
            print("### Buy Order Failed: Insufficient KRW (less than 5000 KRW) ###")
    elif result["decision"] == "sell":
        my_btc = upbit.get_balance("KRW-BTC")
        current_price = pyupbit.get_orderbook(ticker="KRW-BTC")['orderbook_units'][0]["ask_price"]
        if my_btc*current_price > 5000:
            print("### Sell Order Executed ###")
            print(upbit.sell_market_order("KRW-BTC", my_btc))
        else:
            print("### Sell Order Failed: Insufficient BTC (less than 5000 KRW worth) ###")
    elif result["decision"] == "hold":
        print("### Hold Position ###")

# Main loop
while True:
    try:
        ai_trading()
        time.sleep(600)
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(60)