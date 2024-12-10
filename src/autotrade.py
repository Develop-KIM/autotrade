import os
import pyupbit
import pandas as pd
import json
import ta
import time
import requests
import base64
import io
import logging
import mysql.connector

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from PIL import Image
from ta.utils import dropna
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException
from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi
from mysql.connector import Error

class TradingDecision(BaseModel):
    decision: str
    percentage: int
    reason: str

def init_db():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            port=int(os.getenv("MYSQL_PORT")),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE")
        )
        
        cursor = connection.cursor()
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS trades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            decision VARCHAR(10),
            percentage INT,
            reason TEXT,
            btc_balance DECIMAL(20, 8),
            krw_balance INT,
            btc_avg_buy_price INT,
            btc_krw_price INT,
            reflection TEXT)"""
        )
        
        connection.commit()
        return connection
    except Error as e:
        logger.error(f"Error initializing MySQL database: {e}")
        raise

def log_trade(connection, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, reflection):
    try:
        cursor = connection.cursor()
        timestamp = datetime.now()
        query = """INSERT INTO trades 
                   (timestamp, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, reflection) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (timestamp, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, reflection)
        
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        logger.error(f"Error logging trade: {e}")

def get_recent_trades(connection, days=7):
    try:
        cursor = connection.cursor(dictionary=True)
        seven_days_ago = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute("SELECT * FROM trades WHERE timestamp > %s ORDER BY timestamp DESC", (seven_days_ago,))
        return pd.DataFrame(cursor.fetchall())
    except Error as e:
        logger.error(f"Error fetching recent trades: {e}")
        return pd.DataFrame()
    
def calculate_performance(trades_df):
    if trades_df.empty:
        return 0

    initial_balance = trades_df.iloc[-1]['krw_balance'] + trades_df.iloc[-1]['btc_balance'] * trades_df.iloc[-1]['btc_krw_price']
    final_balance = trades_df.iloc[0]['krw_balance'] + trades_df.iloc[0]['btc_balance'] * trades_df.iloc[0]['btc_krw_price']

    return (final_balance - initial_balance) / initial_balance * 100

def generate_reflection(trades_df, current_market_data):
    performance = calculate_performance(trades_df)
    
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an AI trading assistant tasked with analyzing recent trading performance and current market conditions to generate insights and improvements for future trading decisions."
            },
            {
                "role": "user",
                "content": f"""
                Recent trading data:
                {trades_df.to_json(orient='records')}
                
                Current market data:
                {current_market_data}
                
                Overall performance in the last 7 days: {performance:.2f}%
                
                Please analyze this data and provide:
                1. A brief reflection on the recent trading decisions
                2. Insights on what worked well and what didn't
                3. Suggestions for improvement in future trading decisions
                4. Any patterns or trends you notice in the market data
                
                Limit your response to 250 words or less.
                """
            }
        ]
    )
    
    return response.choices[0].message.content

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            port=int(os.getenv("MYSQL_PORT")),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE")
        )
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL database: {e}")
        raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
init_db()

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

def get_fear_and_greed_index():
    url = os.getenv("FNG_API_URL")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['data'][0]
    else:
        logger.error(f"Failed to fetch Fear and Greed Index. Status code: {response.status_code}")
        return None

def get_bitcoin_news():
    key = os.getenv("SERPAPI_API_KEY")
    url = os.getenv("SERPAPI_URL")
    params = {
        "engine": "google_news",
        "q": "btc",
        "api_key": key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        news_results = data.get("news_results", [])
        headlines = []
        for item in news_results:
            headlines.append({
                "title": item.get("title", ""),
                "date": item.get("date", "")
            })
        
        return headlines[:5]
    except requests.RequestException as e:
        logger.error(f"Error fetching news: {e}")
        return []

def setup_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return chrome_options

def create_driver():
    logger.info("ChromeDriver 설정 중...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=setup_chrome_options())
    return driver

def click_element_by_xpath(driver, xpath, element_name, wait_time=10):
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()
        logger.info(f"{element_name} 클릭 완료")
        time.sleep(2)
    except TimeoutException:
        logger.error(f"{element_name} 요소를 찾는 데 시간이 초과되었습니다.")
    except ElementClickInterceptedException:
        logger.error(f"{element_name} 요소를 클릭할 수 없습니다. 다른 요소에 가려져 있을 수 있습니다.")
    except Exception as e:
        logger.error(f"{element_name} 클릭 중 오류 발생: {e}")

def perform_chart_actions(driver):
    click_element_by_xpath(
        driver,
        "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]",
        "시간 메뉴"
    )
    
    click_element_by_xpath(
        driver,
        "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/cq-menu-dropdown/cq-item[8]",
        "1시간 옵션"
    )
    
    click_element_by_xpath(
        driver,
        "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]",
        "지표 메뉴"
    )
    
    click_element_by_xpath(
        driver,
        "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]/cq-menu-dropdown/cq-scroll/cq-studies/cq-studies-content/cq-item[15]",
        "볼린저 밴드 옵션"
    )

def capture_and_encode_screenshot(driver):
    try:
        png = driver.get_screenshot_as_png()
        
        img = Image.open(io.BytesIO(png))
        
        img.thumbnail((2000, 2000))
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upbit_chart_{current_time}.png"
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        file_path = os.path.join(script_dir, filename)
        
        img.save(file_path)
        logger.info(f"스크린샷이 저장되었습니다: {file_path}")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")

        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return base64_image, file_path
    except Exception as e:
        logger.error(f"스크린샷 캡처 및 인코딩 중 오류 발생: {e}")
        return None, None

def get_combined_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        combined_text = ' '.join(entry['text'] for entry in transcript)
        return combined_text
    except Exception as e:
        logger.error(f"Error fetching YouTube transcript: {e}")
        return ""

def send_slack_notification(decision, coin, quantity, avg_price, krw):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.error("Slack Webhook URL이 설정되지 않았습니다.")
        return
    
    krw_formatted = f"{abs(krw):,} KRW"
    prefix = "수익" if krw >= 0 else "손실"
    
    if decision == "buy":
        message = f"🔔 [매수 알림]\n- 구매 코인: {coin}\n- 구매 수량: {quantity:.8f}\n- 구매 평단가: {avg_price:,} KRW\n- 사용 금액: {krw_formatted}"
    elif decision == "sell":
        message = f"🔔 [매도 알림]\n- 판매 코인: {coin}\n- 판매 수량: {quantity:.8f}\n- 판매 평단가: {avg_price:,} KRW\n- {prefix} 금액: {krw_formatted}"
    else:
        logger.warning("Slack 알림은 매수 또는 매도 결정에만 발송됩니다.")
        return
    
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            logger.info("Slack 알림이 성공적으로 전송되었습니다.")
        else:
            logger.error(f"Slack 알림 전송 실패: {response.status_code}, {response.text}")
    except requests.RequestException as e:
        logger.error(f"Slack 알림 전송 중 오류 발생: {e}")

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

    fear_greed_index = get_fear_and_greed_index()

    news_headlines = get_bitcoin_news()

    youtube_transcript = get_combined_transcript("YOUTUBE_TRANSCRIPT")

    driver = None
    saved_file_path = None
    try:
        driver = create_driver()
        driver.get("https://upbit.com/full_chart?code=CRIX.UPBIT.KRW-BTC")
        logger.info("페이지 로드 완료")
        time.sleep(30)
        logger.info("차트 작업 시작")
        perform_chart_actions(driver)
        logger.info("차트 작업 완료")
        chart_image, saved_file_path = capture_and_encode_screenshot(driver)
        logger.info(f"스크린샷 캡처 완료. 저장된 파일 경로: {saved_file_path}")
    except WebDriverException as e:
        logger.error(f"WebDriver 오류 발생: {e}")
        chart_image, saved_file_path = None, None
    except Exception as e:
        logger.error(f"차트 캡처 중 오류 발생: {e}")
        chart_image, saved_file_path = None, None
    finally:
        if driver:
            driver.quit()

    client = OpenAI()

    connection = get_db_connection()

    recent_trades = get_recent_trades(connection)

    current_market_data = {
        "fear_greed_index": fear_greed_index,
        "news_headlines": news_headlines,
        "orderbook": orderbook,
        "daily_ohlcv": df_daily.to_dict(),
        "hourly_ohlcv": df_hourly.to_dict()
    }
    
    reflection = generate_reflection(recent_trades, current_market_data)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""You are an expert in Bitcoin investing. Analyze the provided data and determine whether to buy, sell, or hold at the current moment. Consider the following in your analysis:

                - Technical indicators and market data
                - Recent news headlines and their potential impact on Bitcoin price
                - The Fear and Greed Index and its implications
                - Overall market sentiment
                - Patterns and trends visible in the chart image
                - Recent trading performance and reflection

                Recent trading reflection:
                {reflection}

                Particularly important is to always refer to the trading method of 'Wonyyotti', a legendary Korean investor, to assess the current situation and make trading decisions. Wonyyotti's trading method is as follows:

                {youtube_transcript}

                Based on this trading method, analyze the current market situation and make a judgment by synthesizing it with the provided data.

                Response format:
                1. Decision (buy, sell, or hold)
                2. If the decision is 'buy', provide a percentage (1-100) of available KRW to use for buying.
                If the decision is 'sell', provide a percentage (1-100) of held BTC to sell.
                If the decision is 'hold', set the percentage to 0.
                3. Reason for your decision

                Ensure that the percentage is an integer between 1 and 100 for buy/sell decisions, and exactly 0 for hold decisions.
                Your percentage should reflect the strength of your conviction in the decision based on the analyzed data."""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Current investment status: {json.dumps(filtered_balances)}
        Orderbook: {json.dumps(orderbook)}
        Daily OHLCV with indicators (30 days): {df_daily.to_json()}
        Hourly OHLCV with indicators (24 hours): {df_hourly.to_json()}
        Recent news headlines: {json.dumps(news_headlines)}
        Fear and Greed Index: {json.dumps(fear_greed_index)}"""   
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{chart_image}"
                        }
                    }
                ]
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "trading_decision",
                "strict": True,
                "schema": {
                "type": "object",
                    "properties": {
                        "decision": {"type": "string", "enum": ["buy", "sell", "hold"]},
                        "percentage": {"type": "integer"},
                        "reason": {"type": "string"}
                    },
                    "required": ["decision", "percentage", "reason"],
                    "additionalProperties": False
                }
            }
        },
        max_tokens=300,
    )
    
    result = TradingDecision.model_validate_json(response.choices[0].message.content)

    print(f"### AI Decision: {result.decision.upper()} ###")

    print(f"### Reason: {result.reason} ###")

    order_executed = False

    if result.decision == "buy":
        my_krw = upbit.get_balance("KRW")
        buy_amount = my_krw * (result.percentage / 100) * 0.9995
        if my_krw * 0.9995 > 5000:
            print(f"### Buy Order Executed: {result.percentage}% of available KRW ###")
            order = upbit.buy_market_order("KRW-BTC", buy_amount)
            if order:
                order_executed = True
            print(order)
        else:
            print("### Buy Order Failed: Insufficient KRW (less than 5000 KRW) ###")
    elif result.decision == "sell":
        my_btc = upbit.get_balance("KRW-BTC")
        sell_amount = my_btc * (result.percentage / 100)
        current_price = pyupbit.get_orderbook(ticker="KRW-BTC")['orderbook_units'][0]["ask_price"]
        if my_btc*current_price > 5000:
            print(f"### Sell Order Executed: {result.percentage}% of held BTC ###")
            order = upbit.sell_market_order("KRW-BTC", sell_amount)
            if order:
                order_executed = True
            print(order)
        else:
            print("### Sell Order Failed: Insufficient BTC (less than 5000 KRW worth) ###")
    elif result.decision == "hold":
        print("### Hold Position ###")

    time.sleep(1)
    balances = upbit.get_balances()
    btc_balance = next((float(balance['balance']) for balance in balances if balance['currency'] == 'BTC'), 0)
    krw_balance = next((float(balance['balance']) for balance in balances if balance['currency'] == 'KRW'), 0)
    btc_avg_buy_price = next((float(balance['avg_buy_price']) for balance in balances if balance['currency'] == 'BTC'), 0)
    current_btc_price = pyupbit.get_current_price("KRW-BTC")

    log_trade(connection, result.decision, result.percentage if order_executed else 0, result.reason, btc_balance, krw_balance, btc_avg_buy_price, current_btc_price, reflection)

    if saved_file_path and os.path.exists(saved_file_path):
        try:
            os.remove(saved_file_path)
            logger.info(f"스냅샷 파일 삭제 완료: {saved_file_path}")
        except Exception as e:
            logger.error(f"스냅샷 파일 삭제 중 오류 발생: {e}")

while True:
    try:
        ai_trading()
        time.sleep(600) 
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        time.sleep(300)