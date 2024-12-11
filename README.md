# AutoTrading Bot

## 📌 소개
이 프로젝트는 Python을 사용하여 AI 기반 비트코인 자동매매 시스템을 구현하는 프로젝트입니다. <br/>
MVP 단계로 시작하여 점진적으로 기능을 확장합니다.

## 👥 Team

|김동환|양이준|박찬우|
|:---:|:---:|:---:|
|FE / BE|BE| ??? |

---

## 🗂️ 프로젝트 구조 및 주요 파일
```
src/
├── apis/               
├── libraries/          
├── ui/                 
├── autotrade.py        # 메인 자동매매 코드
└── mvp.py              # 초기 MVP 단계 코드
```
--- 


## 👨‍💻 개발 환경

- **프론트엔드**: <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=Streamlit&logoColor=white">
- **백엔드**: <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=Python&logoColor=white"/> <img src="https://img.shields.io/badge/Selenium-43B02A?style=flat-square&logo=Selenium&logoColor=white"> <img src="https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=NumPy&logoColor=white"> <img src="https://img.shields.io/badge/UpBitAPI-5395FD?style=flat-square&logo=UP&logoColor=white"> <img src="https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=MySQL&logoColor=white"/> <img src="https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=OpenAI&logoColor=white"> <img src="https://img.shields.io/badge/YouTube Transcript API-FF0000?style=flat-square&logo=YouTube&logoColor=white"> <img src="https://img.shields.io/badge/TA lib-000000?style=flat-square&logo=TA&logoColor=white"> <img src="https://img.shields.io/badge/Serp API-000000?style=flat-square&logo=Serp&logoColor=white">
- **협업 도구**: <img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=GitHub&logoColor=white"/>

## 🛠️ 설치 및 실행

### 1. 가상환경 설정
```bash
python -m venv venv
# Mac    : source venv/bin/activate  
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 실행
```bash
python src/autotrade.py
```


## 🧾 프로젝트 개요

- 완전히 자동화된 AI기반의 코인 자동매매 서비스
- 실시간으로 과거의 지표 수집과 더불어 실시간(최근)의 정보 수집 후 학습
- 업비트API를 이용하여 실시간 매수/매도 주문 체결
- 거래 이후 거래 근거 및 결과 기록 후 사용자에게 시각화

## 🌟 주요 기능
- 완전한 자동화
 ```
 -사용자의 자산 상황 및 제공받은 정보를 토대로 매수/매도뿐만 아니라 관망까지도 GPT의 판단하에 자동화
 -이에 더불어 현금자산 대비 매매 비중까지도 AI의 판단하에 능동적으로 조절
 -수익률만 중점적으로 집착하지 않고 시장 상황에 맞게 손절 및 재진입까지 수행
 ```

- Structured Outputs API Docs활용
 ```
 - API에서 구조화된 출력을 제공하는 GPT모델
 - 해당 모델을 사용하여 JSON 형태로 출력을 받음으로써 별도의 데이터 가공 없이 바로 추가 기능에 활용 가능
 - 일반 모델에서 프롬프트로 작업을 하였을때에 비해 60프로 향상된 응답률을 보임
 ```

- 거래기록 회고 및 복기 학습
 ```
 - 거래 기록을 남기는 데에 마치지 않고 해당 거래에서의 판단 근거 및 거래 이후 개선점을 기록 및 재학습
 - 자동적으로 재학습을 함으로써 점진적으로 해당 서비스의 신뢰도 향상 가능
 ```

## 📷 작동 화면

-사진
