from pykrx import stock
# import pandas as pd


# 삼성전자 주식 데이터 로드 (2023년 1월 1일부터 2023년 12월 31일까지)
df = stock.get_market_ohlcv_by_date(
    fromdate="20230101", todate="20231231", ticker="005930"
)


# 변동성 돌파 전략 구현
def volatility_breakout_strategy(df, k=0.5):
    df['range'] = df['고가'] - df['저가']  # 전일 변동폭
    df['target'] = df['시가'] + (df['range'].shift(1) * k)  # 매수 목표가
    df['buy_signal'] = df['고가'] > df['target']
    df['sell_price'] = df['종가']
    df['returns'] = 0
    df.loc[df['buy_signal'], 'returns'] = (df['sell_price'] / df['target']) - 1
    df['cumulative_returns'] = (1 + df['returns']).cumprod() - 1
    return df


# 전략 적용 후 result 변수 정의
result = volatility_breakout_strategy(df)
print(result)


# 누적 수익률 출력
print(f"누적 수익률: {result['cumulative_returns'].iloc[-1]}")