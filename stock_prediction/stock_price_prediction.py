import pandas as pd
from pykrx import stock
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt

# 삼성전자 주식 데이터 불러오기
start_date = '2023-01-01'
end_date = '2024-01-31'
stock_code = '005930'  # 삼성전자
df = stock.get_market_ohlcv_by_date(
    fromdate=start_date, todate=end_date, ticker=stock_code
)

# 날짜 인덱스를 설정하여 날짜 기반 슬라이싱을 지원
df.index = pd.to_datetime(df.index)

# 다음날 고가를 예측하기 위해 하루씩 미룬 고가 컬럼을 새로 생성
df['Next_High'] = df['고가'].shift(-1)

# 마지막 행은 다음날 데이터가 없으므로 제거
df = df[:-1]

# 특성과 타깃 분리
X = df.drop('Next_High', axis=1)
y = df['Next_High']

# 훈련 세트와 테스트 세트 분리 (날짜 기반 슬라이싱)
X_train = X[:'2024-01-15']
y_train = y[:'2024-01-15']
X_test = X['2024-01-16':]
y_test = y['2024-01-16':]

# RandomForestRegressor 모델 생성 및 학습
model = RandomForestRegressor(random_state=42)
model.fit(X_train, y_train)

# 예측
y_pred = model.predict(X_test)

# 결과 시각화
plt.figure(figsize=(12, 6))
plt.plot(
    y_test.index, y_test, label='실제 최고가',
    color='blue'
)
plt.plot(
    y_test.index, y_pred, label='예상되는 높은 가격',
    color='red', linestyle='--'
)
plt.xlabel('Date')
plt.ylabel('High Price')
plt.title('삼성전자의 실제 고가 vs 예상 고가')
plt.legend()
plt.show()
