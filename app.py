import streamlit as st
import subprocess
import sys
import os
from datetime import datetime, timedelta

st.title("부산 AI 뉴스맵")

# 마지막 업데이트 시간 표시
if os.path.exists("busan_news_map.html"):
    modified_time = os.path.getmtime("busan_news_map.html")

    # UTC → 한국시간(KST)
    update_time = datetime.utcfromtimestamp(modified_time) + timedelta(hours=9)

    weekday_map = {
        "Monday": "월요일",
        "Tuesday": "화요일",
        "Wednesday": "수요일",
        "Thursday": "목요일",
        "Friday": "금요일",
        "Saturday": "토요일",
        "Sunday": "일요일"
    }

    weekday = weekday_map[update_time.strftime("%A")]

    st.caption(
        f"마지막 업데이트: {update_time.strftime('%Y-%m-%d %H:%M')}, {weekday}"
    )

# 뉴스 새로고침 버튼
if st.button("뉴스 새로고침"):
    with st.spinner("뉴스 생성 중... 잠시만 기다려주세요"):
        subprocess.run([sys.executable, "BusanAI_News.py"])
    st.success("지도 생성 완료!")
    st.rerun()

# 지도 표시
if os.path.exists("busan_news_map.html"):
    with open("busan_news_map.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=700, scrolling=True)
else:
    st.warning("아직 생성된 지도가 없습니다. '뉴스 새로고침' 버튼을 눌러주세요.")
