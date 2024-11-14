from pykiwoom.kiwoom import Kiwoom

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)  # 로그인 창을 띄워 로그인을 진행합니다. block=True는 로그인 완료까지 코드 실행을 대기시킵니다.

accounts = kiwoom.GetLoginInfo("ACCNO")  # 로그인한 계좌 목록을 가져옵니다. 문자열 형태로 계좌번호가 반환됩니다.
first_account = accounts[0]  # 첫 번째 계좌를 선택합니다.

# 예수금 상세 정보 요청
# '예수금'은 "opw00001" TR을 사용하여 조회할 수 있습니다.
# 첫 번째 매개변수는 TR 코드, 두 번째는 계좌번호 10자리, 세 번째는 비밀번호(미사용 시 ""), 
# 네 번째는 조회구분(2: 일반조회, 3: 추정조회), 마지막은 요청구분(0: 조회, 1: 파일로 저장)입니다.
data = kiwoom.block_request("opw00001",
                            계좌번호=first_account,
                            비밀번호="",
                            비밀번호입력매체구분="00",
                            조회구분=2,
                            output="예수금상세현황",
                            next=0)

# 예수금 정보 출력
deposit = data['예수금']
print(f"계좌 예수금: {deposit}원")