from pykiwoom.kiwoom import Kiwoom

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)  # 로그인 창을 띄워 로그인을 진행합니다.

# 삼성전자("005930")와 현대자동차("005380")의 현재가 정보를 조회하기 위한 코드 리스트
stock_codes = ["005930", "005380"]

# 조회할 항목들: 현재가, 거래량 등을 조회할 수 있습니다. 여기서는 현재가만 조회합니다.
for code in stock_codes:
    # 'opt10001' TR은 주식 기본정보 요청에 사용됩니다.
    # 첫 번째 매개변수는 TR 코드, 두 번째는 종목코드, 세 번째는 출력 타입, 네 번째는 조회 요청 건수입니다.
    data = kiwoom.block_request("opt10001",
                                종목코드=code,
                                output="주식기본정보",
                                next=0)
    
    # 현재가 정보 추출: 반환된 데이터에서 현재가 정보를 가져옵니다.
    name = data['종목명'][0]  # 종목명
    current_price = data['현재가'][0]  # 현재가: 반환값에는 전일대비를 나타내는 +/- 기호가 붙을 수 있습니다.
    print(f"{name}의 현재가: {current_price}원")

# 결과 예시: 삼성전자의 현재가: 80000원