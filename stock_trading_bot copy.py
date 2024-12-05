import sys
import os
import requests
import time
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, QTime
from pykiwoom.kiwoom import Kiwoom  # pykiwoom 라이브러리 유지
import datetime
import openai  # ChatGPT API 사용
from pykrx import stock

# OpenAI API 키 설정
openai.api_key = "sk-svcacct-P3fZgZZ_Gr3yfaHKxtxPJerzgJaJyOPfJpdijGXmldPqQxZ5B3RFMJM4jEgfT3BlbkFJjO5-VcfZwl1LcJ1-3HOGt3_FNGK8J6JJMXHqZt6JiiOuFjvx2oPoCU0AsswA"  # OpenAI API 키를 입력하세요.

# GUI 파일 경로 설정
ui_file_path = os.path.join(os.path.dirname(__file__), 'gui.ui')

form_class = uic.loadUiType(ui_file_path)[0]


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)

        # 버튼 클릭 이벤트 연결
        self.button_start.clicked.connect(self.start_trading)
        self.button_stop.clicked.connect(self.stop_trading)
        self.button_recommend.clicked.connect(self.get_recommendations)  # 추천 버튼 연결

        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_market_time)
        self.trade_timer = QTimer(self)
        self.trade_timer.timeout.connect(self.trade_stocks)

        self.bought_list = {}

    def start_trading(self):
        self.timer.start(1000 * 60)  # 1분마다 시장 시간 체크
        self.trade_timer.start(1000 * 17)  # 17초마다 거래 시도
        today = datetime.datetime.now().strftime('%Y%m%d')
        self.bought_list = {code: today for code, buy_date in self.bought_list.items() if buy_date == today}

    def stop_trading(self):
        self.timer.stop()
        self.trade_timer.stop()

    def check_market_time(self):
        """시장 시간을 확인하고 마감 시간이 되면 모든 주식을 매도합니다."""
        now = QTime.currentTime()
        if now.toString("HHmm") >= "1500":
            self.stop_trading()
            self.sell_all_stocks()

    def trade_stocks(self):
        """주식 거래 로직을 실행하는 함수"""
        yesterday = stock.get_nearest_business_day_in_a_week(datetime.datetime.now().strftime('%Y%m%d'))
        today = datetime.datetime.now().strftime('%Y%m%d')
        codes = self.code_list.text().split(',')
        k_value = float(self.k_value.text())

        for code in codes:
            if code.strip() and (code.strip() not in self.bought_list or self.bought_list[code.strip()] != today):
                try:
                    current_price_raw = self.kiwoom.block_request("opt10001",
                                                                  종목코드=code.strip(),
                                                                  output="주식기본정보",
                                                                  next=0)['현재가'][0].replace(",", "")
                    current_price = abs(int(current_price_raw))
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
                except Exception as e:
                    self.textboard.append(f"오류 발생: {str(e)}")
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

                quantity = int(quantity_str) if quantity_str.isdigit() else 0
                if quantity > 0:
                    order_type = 2
                    order_result = self.kiwoom.SendOrder("매도주문", "0101", account_number, order_type, code, quantity, 0, "03", "")
                    if order_result == 0:
                        message = f"매도 주문 성공: [{code}] [수량: {quantity}]"
                    else:
                        message = f"매도 주문 실패: [{code}]"
                    self.send_slack_message(message)
                    self.buysell_log.append(message)
        else:
            message = "매도 주문 실패: 보유 주식 데이터 확인 불가"
            self.send_slack_message(message)
            self.buysell_log.append(message)

    def send_slack_message(self, message):
        webhook_url = "https://hooks.slack.com/services/your-slack-webhook-url"
        headers = {'Content-type': 'application/json'}
        payload = {"text": message}
        try:
            requests.post(webhook_url, json=payload, headers=headers)
        except Exception as e:
            self.textboard.append(f"슬랙 메시지 전송 실패: {str(e)}")
            print(f"슬랙 메시지 전송 실패: {str(e)}")

    def get_recommendations(self):
        """투자자별 순매수 상위종목, 공매도 관련 데이터를 사용하여 ChatGPT로 추천 종목 출력"""
        try:
            today = datetime.datetime.now().strftime('%Y%m%d')

            # 거래량 급증 종목 가져오기
            volume_increase = self.kiwoom.block_request("opt10023",
                                                        일자=today,
                                                        시장구분='000',
                                                        output="거래량급증요청",
                                                        next=0)
            time.sleep(0.5)  # API 호출 간 대기 시간 추가

            # 전일 대비 등락률 상위 종목 가져오기
            top_gainers = self.kiwoom.block_request("opt10027",
                                                    일자=today,
                                                    시장구분='000',
                                                    output="전일대비등락률상위요청",
                                                    next=0)
            time.sleep(0.5)  # API 호출 간 대기 시간 추가

            # 당일 거래량 상위 종목 가져오기
            top_volume_today = self.kiwoom.block_request("opt10030",
                                                        일자=today,
                                                        시장구분='000',
                                                        output="당일거래량상위요청",
                                                        next=0)
            time.sleep(0.5)  # API 호출 간 대기 시간 추가

            # 전일 거래량 상위 종목 가져오기
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y%m%d')
            top_volume_yesterday = self.kiwoom.block_request("opt10031",
                                                             일자=yesterday,
                                                             시장구분='000',
                                                             output="전일거래량상위요청",
                                                             next=0)
            time.sleep(0.5)  # API 호출 간 대기 시간 추가

            # 가격 급등락 종목 가져오기
            price_fluctuations = self.kiwoom.block_request("opt10019",
                                                          일자=today,
                                                          시장구분='000',
                                                          output="가격급등락요청",
                                                          next=0)
            time.sleep(0.5)  # API 호출 간 대기 시간 추가

            # 예상 체결 등락률 상위 종목 가져오기
            expected_price_change = self.kiwoom.block_request("opt10029",
                                                             일자=today,
                                                             시장구분='000',
                                                             output="예상체결등락률상위요청",
                                                             next=0)
            time.sleep(0.5)  # API 호출 간 대기 시간 추가

            # 거래 대금 상위 종목 가져오기
            top_trading_value = self.kiwoom.block_request("opt10032",
                                                        일자=today,
                                                        시장구분='000',
                                                        output="거래대금상위요청",
                                                        next=0)
            time.sleep(0.5)  # API 호출 간 대기 시간 추가

            # 데이터 저장
            data_dict = {
                "거래량 급증 종목": volume_increase,
                "전일 대비 등락률 상위 종목": top_gainers,
                "당일 거래량 상위 종목": top_volume_today,
                "전일 거래량 상위 종목": top_volume_yesterday,
                "가격 급등락 종목": price_fluctuations,
                "예상 체결 등락률 상위 종목": expected_price_change,
                "거래 대금 상위 종목": top_trading_value,
            }

            df = pd.concat({key: pd.DataFrame(value) for key, value in data_dict.items()}, axis=0)
            df.to_csv("kiwoom.csv", encoding="utf-8-sig")

            # 데이터 포맷팅
            volume_increase_data = "\n".join([f"{row['종목코드']}: {row['급증률']}" for _, row in pd.DataFrame(volume_increase).iterrows()])
            top_gainers_data = "\n".join([f"{row['종목코드']}: {row['등락률']}" for _, row in pd.DataFrame(top_gainers).iterrows()])
            top_volume_today_data = "\n".join([f"{row['종목코드']}: {row['거래량']}" for _, row in pd.DataFrame(top_volume_today).iterrows()])
            top_volume_yesterday_data = "\n".join([f"{row['종목코드']}: {row['거래량']}" for _, row in pd.DataFrame(top_volume_yesterday).iterrows()])
            price_fluctuations_data = "\n".join([f"{row['종목코드']}: {row['등락률']}" for _, row in pd.DataFrame(price_fluctuations).iterrows()])
            expected_price_change_data = "\n".join([f"{row['종목코드']}: {row['등락률']}" for _, row in pd.DataFrame(expected_price_change).iterrows()])
            top_trading_value_data = "\n".join([f"{row['종목코드']}: {row['거래대금']}" for _, row in pd.DataFrame(top_trading_value).iterrows()])

            # ChatGPT 요청 생성
            prompt = (
                "다음은 최근 한국 주식시장의 데이터입니다:\n\n"
                "거래량 급증 종목:\n"
                + volume_increase_data + "\n\n"
                "전일 대비 등락률 상위 종목:\n"
                + top_gainers_data + "\n\n"
                "당일 거래량 상위 종목:\n"
                + top_volume_today_data + "\n\n"
                "전일 거래량 상위 종목:\n"
                + top_volume_yesterday_data + "\n\n"
                "가격 급등락 종목:\n"
                + price_fluctuations_data + "\n\n"
                "예상 체결 등락률 상위 종목:\n"
                + expected_price_change_data + "\n\n"
                "거래 대금 상위 종목:\n"
                + top_trading_value_data + "\n\n"
                "이 데이터를 바탕으로 투자하기 좋은 종목 2개의 종목 코드만 알려주세요."
            )

            # ChatGPT API 호출
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 한국 주식시장을 분석하여 투자하기 좋은 종목을 추천하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=1.0
            )
            recommendations = response['choices'][0]['message']['content'].strip()

            if recommendations:
                self.textboard.append("[ChatGPT 종목 코드 추천]\n" + recommendations)
            else:
                self.textboard.append("ChatGPT가 추천 종목을 반환하지 않았습니다.")
        except Exception as e:
            self.textboard.append(f"추천 실패: {str(e)}")
            print(f"추천 실패: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())
