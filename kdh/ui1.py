import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QTime
from pykiwoom.kiwoom import Kiwoom

# Kiwoom 로그인
kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

# GUI 로딩
class StockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui.ui", self)  # 여기에서 "gui.ui"는 Qt Designer로 생성된 UI 파일 경로입니다.
        self.button_start.clicked.connect(self.start_retrieval)
        self.button_stop.clicked.connect(self.stop_retrieval)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stock_prices)
        self.running = False

    def start_retrieval(self):
        self.running = True
        self.timer.start(1000)  # 1초마다 update_stock_prices 호출

    def stop_retrieval(self):
        self.running = False
        self.timer.stop()
        # 초기화 코드나 추가적인 정리 작업을 여기에 추가할 수 있습니다.

    def update_stock_prices(self):
        if not self.running:
            return
        
        code_list_text = self.code_list.text()
        codes = code_list_text.split(',')
        
        for code in codes:
            if code:
                data = kiwoom.block_request("opt10001",
                                            종목코드=code.strip(),
                                            output="주식기본정보",
                                            next=0)
                time_str = QTime.currentTime().toString('HH:mm:ss')
                name = data['종목명'][0]
                current_price = data['현재가'][0]
                log_text = f"[{time_str}] [{code}] [{name}] [현재가: {current_price}]"
                self.textboard.append(log_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockApp()
    window.show()
    sys.exit(app.exec_())
