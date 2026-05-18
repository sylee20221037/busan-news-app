import streamlit as st
import subprocess
import os

st.title("부산 AI 뉴스맵")

# 버튼 누르면 뉴스 새로 생성
if st.button("뉴스 새로고침"):
    subprocess.run(["python", "BusanAI_News.py"])

# 처음 실행 시 html 없으면 자동 생성
if not os.path.exists("busan_news_map.html"):
    subprocess.run(["python", "BusanAI_News.py"])

# 지도 표시
st.iframe("busan_news_map.html", height=700)