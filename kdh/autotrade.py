import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, QTime
from pykiwoom.kiwoom import Kiwoom
from pykrx import stock
import datetime

# Qt Designer로 생성한 gui 파일 로드
form_class = uic.loadUiType(r'gui.ui')[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Kiwoom 로그인
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)

        # 버튼 연결
        self.button_start.clicked.connect(self.start_trading)
        self.button_stop.clicked.connect(self.stop_trading)

        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_market_time)
        self.trade_timer = QTimer(self)
        self.trade_timer.timeout.connect(self.trade_stocks)

    def start_trading(self):
        self.timer.start(1000 * 60)  # 1분마다 check_market_time 호출
        self.trade_timer.start(1000 * 17)  # 1초마다 trade_stocks 호출

    def stop_trading(self):
        self.timer.stop()
        self.trade_timer.stop()

    def check_market_time(self):
        now = QTime.currentTime()
        if now.toString("HHmm") >= "1500":  # 15시가 되면 매도
            self.timer.stop()
            self.sell_all_stocks()

    def trade_stocks(self):
        # 직전 거래일 조회
        yesterday = stock.get_nearest_business_day_in_a_week(datetime.datetime.now().strftime('%Y%m%d'))
        codes = self.code_list.text().split(',')  # 종목 코드 분리
        k_value = float(self.k_value.text())  # K 값 입력 받기

        for code in codes:
            if code.strip():
                current_price_raw = self.kiwoom.block_request("opt10001",
                                                            종목코드=code.strip(),
                                                            output="주식기본정보",
                                                            next=0)['현재가'][0].replace(",", "")
                current_price = int(current_price_raw)
                
                # 현재가가 음수인 경우 양수로 변환
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
                    
                    if current_price > target_price:  # 변동성 돌파 전략에 따라 매수
                        self.buy_stock(code.strip(), current_price, 1)

    def buy_stock(self, code, price, quantity):
        account_number = self.kiwoom.GetLoginInfo("ACCNO")[0]  # 계좌번호 조회
        
        order_type = 1  # 매수 주문
        order_result = self.kiwoom.SendOrder("매수주문", "0101", account_number, order_type, code, quantity, price, "00", "")
        if order_result == 0:
            self.buysell_log.append(f"매수 주문 성공: [{code}] [가격: {price}] [수량: {quantity}]")
        else:
            self.buysell_log.append(f"매수 주문 실패: [{code}]")

    def sell_all_stocks(self):
        account_number = self.kiwoom.GetLoginInfo("ACCNO")[0].strip()  # 계좌번호 조회

        # 보유 주식 목록 조회를 위한 TR 요청
        stocks_info = self.kiwoom.block_request("opw00018",
                                                계좌번호=account_number,
                                                비밀번호="",
                                                비밀번호입력매체구분="00",
                                                조회구분=2,
                                                output="계좌평가잔고개별합산",
                                                next=0)

        if '종목번호' in stocks_info:  # 보유 주식 목록이 있는 경우
            for idx, code in enumerate(stocks_info['종목번호']):
                # 종목번호 앞에 붙는 'A' 제거
                code = code.strip()[1:]
                quantity_str = stocks_info['보유수량'][idx].strip()
                
                if not quantity_str.isdigit():
                    continue
                    
                quantity = int(quantity_str)
                if quantity > 0:
                    order_type = 2  # 매도 주문
                    order_result = self.kiwoom.SendOrder("매도주문", "0101", account_number, order_type, code, quantity, 0, "03", "")
                    if order_result == 0:
                        self.buysell_log.append(f"매도 주문 성공: [{code}] [수량: {quantity}]")
                    else:
                        self.buysell_log.append(f"매도 주문 실패: [{code}]")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())
