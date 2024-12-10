import os
import mysql.connector
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import plotly.express as px

load_dotenv()

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
    except mysql.connector.Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        raise

def load_trades_data():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM trades ORDER BY timestamp DESC"
    cursor.execute(query)
    trades_data = cursor.fetchall()
    connection.close()
    return trades_data

st.set_page_config(page_title="비트코인 AI 자동매매", layout="wide")
st.title("🤖 비트코인 AI 자동매매 대시보드")
st.write("")
st.write("")

try:
    trades = load_trades_data()
    if not trades:
        st.warning("데이터베이스에 거래 기록이 없습니다.")
    else:
        df = pd.DataFrame(trades)

        column_mapping = {
            "id": "ID",
            "timestamp": "거래 시간",
            "decision": "결정",
            "percentage": "비율 (%)",
            "reason": "결정 이유",
            "btc_balance": "BTC 잔고",
            "krw_balance": "KRW 잔고",
            "btc_avg_buy_price": "BTC 평균 매수가",
            "btc_krw_price": "BTC 현재가",
            "reflection": "반성 내용"
        }
        df.rename(columns=column_mapping, inplace=True)

        st.subheader("📋 전체 거래 데이터")
        st.dataframe(df, use_container_width=True)

        st.write("")

        total_trades = len(df)
        first_trade_date = df["거래 시간"].min().strftime("%Y-%m-%d %H:%M:%S")
        last_trade_date = df["거래 시간"].max().strftime("%Y-%m-%d %H:%M:%S")
        btc_balance_change = df["BTC 잔고"].iloc[0] - df["BTC 잔고"].iloc[-1]
        krw_balance_change = df["KRW 잔고"].iloc[0] - df["KRW 잔고"].iloc[-1]

        initial_total_balance = (
            df.iloc[-1]["KRW 잔고"] + df.iloc[-1]["BTC 잔고"] * df.iloc[-1]["BTC 평균 매수가"]
        )
        current_total_balance = (
            df.iloc[0]["KRW 잔고"] + df.iloc[0]["BTC 잔고"] * df.iloc[0]["BTC 현재가"]
        )

        if initial_total_balance == 1000000:
            profit_rate = 0
        else:
            profit_rate = ((current_total_balance - initial_total_balance) / initial_total_balance) * 100

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 매매 횟수", total_trades)
        col2.metric("첫 거래 일자", first_trade_date)
        col3.metric("마지막 거래 일자", last_trade_date)
        col4.metric("수익률", f"{profit_rate:.2f} %")

        st.divider()

        st.subheader("📊 거래 결정 분포")
        decision_counts = df["결정"].value_counts()
        pie_fig = px.pie(
            names=decision_counts.index,
            values=decision_counts.values,
            title="결정 분포",
            hole=0.4
        )
        st.plotly_chart(pie_fig)

        st.divider()

        st.subheader("📈 BTC 잔액 변화")
        btc_change_fig = px.line(
            df,
            x="거래 시간",
            y="BTC 잔고",
            title="BTC 잔액 변화",
            markers=True
        )
        st.plotly_chart(btc_change_fig)

        st.divider()

        st.subheader("💰 KRW 잔액 변화")
        krw_change_fig = px.line(
            df,
            x="거래 시간",
            y="KRW 잔고",
            title="KRW 잔액 변화",
            markers=True
        )
        st.plotly_chart(krw_change_fig)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
