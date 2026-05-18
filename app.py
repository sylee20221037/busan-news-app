import streamlit as st
import subprocess
import sys
import os

st.title("부산 AI 뉴스맵")

if st.button("뉴스 새로고침"):
    with st.spinner("뉴스 생성 중..."):
        subprocess.run([sys.executable, "BusanAI_News.py"])
    st.success("완료!")

if not os.path.exists("busan_news_map.html"):
    subprocess.run([sys.executable, "BusanAI_News.py"])

if os.path.exists("busan_news_map.html"):
    st.iframe("busan_news_map.html", height=700)
