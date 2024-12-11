## 📌 소개
AI 기반 비트코인 자동매매 시스템

## 🌟 주요 기능
**자동화 시스템**
 ```
 - 사용자의 자산 상황 및 제공받은 정보를 토대로 매수/매도뿐만 아니라 관망까지도 GPT의 판단하에 자동화
   이에 더불어 현금자산 대비 매매 비중까지도 AI의 판단하에 능동적으로 조절
 - 수익률만 중점적으로 집착하지 않고 시장 상황에 맞게 손절 및 재진입까지 수행
 ```

**Structured Outputs API 활용**
 ```
 - API에서 구조화된 출력을 제공하는 GPT모델
 - 해당 모델을 사용하여 JSON 형태로 출력을 받음으로써 별도의 데이터 가공 없이 추가 기능에 활용 가능
 - 일반 모델에서 프롬프트로 작업을 하였을때에 비해 정확도 60% 향상 및 응답 속도 10% 향상
 ```

**거래기록 회고 및 복기 학습**
 ```
 - 거래 기록을 남기는 데에 마치지 않고 해당 거래에서의 판단 근거 및 거래 이후 개선점을 기록 및 재학습
 - 자동적으로 재학습함으로써 점진적으로 해당 서비스의 신뢰도 향상 가능
 ```

---

## 👥 Team

|김동환|양이준|박찬우|
|:---:|:---:|:---:|
|FE / BE|BE| ??? |

## 👨‍💻 개발 환경

- **FE**: <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=Streamlit&logoColor=white">
- **BE**: <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=Python&logoColor=white" alt="Python"> <img src="https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=OpenAI&logoColor=white" alt="OpenAI API">
- **Database**: <img src="https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=MySQL&logoColor=white" alt="MySQL">
- **Infrastructure & Deployment**: <img src="https://img.shields.io/badge/AWS EC2-FF9900?style=flat-square&logo=Amazon-AWS&logoColor=white" alt="AWS EC2"> <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=Docker&logoColor=white" alt="Docker">
- **Tools**: <img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=GitHub&logoColor=white"/>

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