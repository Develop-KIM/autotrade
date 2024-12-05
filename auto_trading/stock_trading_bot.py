import sys
import requests
import time
import os
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, QTime
from PyQt5.uic import loadUi
from pykiwoom.kiwoom import Kiwoom
from pykrx import stock
import datetime

ui_file_path = os.path.join(os.path.dirname(__file__), 'gui.ui')

class MyWindow(QMainWindow, ui_file_path):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)

        self.button_start.clicked.connect(self.start_trading)
        self.button_stop.clicked.connect(self.stop_trading)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_market_time)
        self.trade_timer = QTimer(self)
        self.trade_timer.timeout.connect(self.trade_stocks)

        self.bought_list = {}

    def start_trading(self):
    # 키움 OpenAPI 연결 상태 확인
        if self.kiwoom.GetConnectState() != 1:
            print("[ERROR] 키움 OpenAPI 연결 실패!")
            self.textboard.append("[ERROR] 키움 OpenAPI 연결 실패!")
            return
        
        # 서버 환경 확인
        server_gubun = self.kiwoom.GetLoginInfo("GetServerGubun")
        if server_gubun == "1":
            print("[INFO] 현재 모의투자 서버에 연결되어 있습니다.")
            self.textboard.append("[INFO] 현재 모의투자 서버에 연결되어 있습니다.")
        elif server_gubun == "0":
            print("[INFO] 현재 실거래 서버에 연결되어 있습니다.")
            self.textboard.append("[INFO] 현재 실거래 서버에 연결되어 있습니다.")
        else:
            print("[ERROR] 서버 정보를 가져올 수 없습니다!")
            self.textboard.append("[ERROR] 서버 정보를 가져올 수 없습니다!")
            return

        # 자동매매 시작
        self.timer.start(1000 * 60)
        self.trade_timer.start(1000 * 20)
        today = datetime.datetime.now().strftime('%Y%m%d')
        self.bought_list = {code: today for code, buy_date in self.bought_list.items() if buy_date == today}

    def stop_trading(self):
        self.timer.stop()
        self.trade_timer.stop()

    def check_market_time(self):
        now = QTime.currentTime()
        if now.toString("HHmm") >= "1500":
            self.stop_trading()
            self.sell_all_stocks()

    def trade_stocks(self):
        yesterday = stock.get_nearest_business_day_in_a_week(datetime.datetime.now().strftime('%Y%m%d'))
        today = datetime.datetime.now().strftime('%Y%m%d')
        codes = self.code_list.text().split(',')
        k_value = float(self.k_value.text())

        for code in codes:
            if code.strip() and (code.strip() not in self.bought_list or self.bought_list[code.strip()] != today):
                current_price_raw = self.kiwoom.block_request("opt10001",
                                                              종목코드=code.strip(),
                                                              output="주식기본정보",
                                                              next=0)['현재가'][0].replace(",", "")
                try:
                    current_price = int(current_price_raw)
                    if current_price < 0:
                        current_price = abs(current_price)
                        
                    name = self.kiwoom.block_request("opt10001",
                                                    종목코드=code.strip(),
                                                    output="주식기본정보",
                                                    next=0)['종목명'][0]
                    self.textboard.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{code}] [{name}] [현재가: {current_price}]")

                    yesterday_data = stock.get_market_ohlcv_by_date(yesterday, yesterday, code.strip())
                    if not yesterday_data.empty:
                        high = yesterday_data['고가'][0]
                        low = yesterday_data['저가'][0]
                        close = yesterday_data['종가'][0]
                        target_price = close + (high - low) * k_value
                        
                        if current_price > target_price:
                            if self.buy_stock(code.strip(), current_price, 1):
                                self.bought_list[code.strip()] = today
                except:
                    continue

    def buy_stock(self, code, price, quantity):
        account_number = self.kiwoom.GetLoginInfo("ACCNO")[0]
        order_type = 1
        order_result = self.kiwoom.SendOrder("매수주문", "0101", account_number, order_type, code, quantity, price, "00", "")
        if order_result == 0:
            message = f"매수 주문 성공: [{code}] [가격: {price}] [수량: {quantity}]"
            self.send_slack_message(message)
            self.buysell_log.append(message)
            return True
        else:
            message = f"매수 주문 실패: [{code}]"
            self.send_slack_message(message)
            self.buysell_log.append(message)
            return False

    def sell_all_stocks(self):
        account_number = self.kiwoom.GetLoginInfo("ACCNO")[0].strip()

        stocks_info = self.kiwoom.block_request("opw00018",
                                                계좌번호=account_number,
                                                비밀번호="",
                                                비밀번호입력매체구분="00",
                                                조회구분=2,
                                                output="계좌평가잔고개별합산",
                                                next=0)

        if '종목번호' in stocks_info:
            for idx, code in enumerate(stocks_info['종목번호']):
                code = code.strip()[1:]
                quantity_str = stocks_info['보유수량'][idx].strip()
                
                if not quantity_str.isdigit():
                    quantity_str = 0
                    
                quantity = int(quantity_str)
                if quantity > 0:
                    order_type = 2
                    order_result = self.kiwoom.SendOrder("매도주문", "0101", account_number, order_type, code, quantity, 0, "03", "")
                    if order_result == 0:
                        message = f"매도 주문 성공: [{code}] [수량: {quantity}]"
                        self.send_slack_message(message)
                        self.buysell_log.append(message)
                    else:
                        message = f"매도 주문 실패: [{code}]"
                        self.send_slack_message(message)
                        self.buysell_log.append(message)
                
                elif quantity == 0:
                    message = "매도 주문 실패: 보유한 주식 없음"
                    self.send_slack_message(message)
                    self.buysell_log.append(message)
        
        else:
            message = "매도 주문 실패: 보유 주식 데이터 확인 불가"
            self.send_slack_message(message)
            self.buysell_log.append(message)

        start_date = pd.Timestamp.today() - pd.Timedelta(days=14)
        dates = pd.date_range(start=start_date, periods=15)
        all_trades = pd.DataFrame()

        for date in dates:
            formatted_date = date.strftime("%Y%m%d")
            data = self.kiwoom.block_request("opt10170",
                                            계좌번호=account_number,
                                            비밀번호="",
                                            기준일자=formatted_date,
                                            단주구분='1',
                                            현금신용구분='0',
                                            output="주식일봉차트조회",
                                            next=0)

            df = pd.DataFrame(data)
            df['기준날짜'] = formatted_date
            all_trades = pd.concat([all_trades, df], ignore_index=True)
            time.sleep(0.5)

        all_trades.to_csv("매매일지.csv", index=False, encoding='utf-8-sig')
        message = "매매일지 csv 파일 저장 완료"
        self.send_slack_message(message)
        self.buysell_log.append(message)

    def send_slack_message(self, message):
        webhook_url = "https://hooks.slack.com/services/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"
        headers = {'Content-type': 'application/json'}
        payload = {"text": message}
        requests.post(webhook_url, json=payload, headers=headers)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())