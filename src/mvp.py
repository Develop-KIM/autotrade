import os
import pyupbit
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv() 

access = os.getenv("UPBIT_ACCESS_KEY")
secret = os.getenv("UPBIT_SECRET_KEY")
openai = os.getenv("OPENAI_API_KEY")

upbit = pyupbit.Upbit(access, secret)
client = OpenAI()

df = pyupbit.get_ohlcv("KRW-BTC", count=30, interval="day")

response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "You are an expert in Bitcoin investing. Tell me whether to buy, sell, or hold at the moment based on the chart data provided. response in json format.\n\nResponse Example:\n{\"decision\": \"buy\", \"reason\":  \"some technical reason\"}\n{\"decision\": \"sell\", \"reason\":  \"some technical reason\"}\n{\"decision\": \"hold\", \"reason\":  \"some technical reason\"}"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": df.to_json()
        }
      ]
    }
  ],
  response_format={
    "type": "json_object"
  }
)
result = json.loads(response.choices[0].message.content)
decision = result["decision"]   

if decision == "buy":
    my_krw = upbit.get_balance("KRW")
    if my_krw * 0.9995 > 5000:
        print(upbit.buy_market_order("KRW-BTC", my_krw * 0.9995))
        print("buy: ", result["reason"])
    else:
        print("[error]: 5000원 미만 보유")
elif decision == "sell":
    my_btc = upbit.get_balance("KRW-BTC")
    avg_buy_price = upbit.get_avg_buy_price("KRW-BTC") 
    current_price = pyupbit.get_orderbook(ticker="KRW-BTC")['orderbook_units'][0]['ask_price']
    if my_btc * current_price > 5000:
        print(upbit.sell_market_order("KRW-BTC", upbit.get_balance("KRW-BTC")))
        print("sell: ", result["reason"])
    else:
        print("[error]: btc 5000원 미만")
elif decision == "hold":
    print("hold: ", result["reason"])
