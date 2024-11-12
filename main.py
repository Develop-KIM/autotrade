from data import load_stock_data
from strategy import volatility_breakout_strategy
from visualization import plot_returns

# 주식 데이터 로드
df = load_stock_data()

# 변동성 돌파 전략 적용
result = volatility_breakout_strategy(df)
print(result)

# 누적 수익률 출력
print(f"누적 수익률: {result['cumulative_returns'].iloc[-1]}")

# 수익률 시각화
plot_returns(result)