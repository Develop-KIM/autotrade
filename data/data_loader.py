from pykrx import stock
import pandas as pd

def load_stock_data(ticker="005930", from_date="20230101", to_date="20231231"):
    """주식 데이터를 불러옵니다."""
    return stock.get_market_ohlcv_by_date(fromdate=from_date, todate=to_date, ticker=ticker)
