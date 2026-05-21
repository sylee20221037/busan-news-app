import requests
import folium
from collections import defaultdict
import urllib.parse
import re
from difflib import SequenceMatcher
import os
import webbrowser
from openai import OpenAI
from datetime import datetime
import streamlit as st
import json

# =========================
# 🔑 네이버 API 키
# =========================

CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

# =========================
# 🧠 뉴스 가져오기
# =========================
def get_news():
    query = urllib.parse.quote("부산")
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=50"

    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }

    res = requests.get(url, headers=headers)
    data = res.json()

    if "items" not in data:
        print("❌ API 오류:", data)
        return []

    return data["items"]

# =========================
# 🗺️ 부산 구 좌표
# =========================
districts = {
    "해운대구": [35.1631, 129.1635],
    "수영구": [35.1455, 129.1131],
    "남구": [35.1365, 129.0840],
    "부산진구": [35.1629, 129.0532],
    "동래구": [35.2051, 129.0836],
    "연제구": [35.1762, 129.0798],
    "금정구": [35.2431, 129.0921],
    "사상구": [35.1527, 128.9910],
    "사하구": [35.1045, 128.9748],
    "강서구": [35.2122, 128.9807],
    "중구": [35.1063, 129.0327],
    "동구": [35.1293, 129.0453],
    "서구": [35.0977, 129.0244],
    "영도구": [35.0912, 129.0676],
    "북구": [35.1973, 128.9902],
    "기장군": [35.2446, 129.2223]
}

# =========================
# 📍 구 찾기
# =========================
def find_district(text):
    for d in districts:
        if d in text:
            return d
    return None

# =========================
# 🧹 HTML 태그 제거
# =========================
def clean_text(text):
    return re.sub('<.*?>', '', text)

# =========================c
# =========================
def is_duplicate(title, existing_titles):
    for old_title in existing_titles:
        similarity = SequenceMatcher(None, title, old_title).ratio()
        if similarity > 0.75:   # 75% 이상 비슷하면 중복
            return True
    return False

# =========================
# 🧹 날짜 변환 함
# =========================
def format_pub_date(pub_date):
    dt = datetime.strptime(
        pub_date,
        "%a, %d %b %Y %H:%M:%S %z"
    )

    weekday_map = {
        "Monday": "월요일",
        "Tuesday": "화요일",
        "Wednesday": "수요일",
        "Thursday": "목요일",
        "Friday": "금요일",
        "Saturday": "토요일",
        "Sunday": "일요일"
    }

    weekday_eng = dt.strftime("%A")
    weekday_kor = weekday_map[weekday_eng]

    return f"{dt.year}-{dt.month}-{dt.day} {dt.strftime('%H:%M')}, {weekday_kor}"


# =========================
# 😊 감성 표시 변환
# =========================
def sentiment_badge(sentiment):
    if sentiment == "긍정":
        return '<span style="color:green; font-size:22px; position:relative; top:3px;">●</span> 긍정 논조'
    elif sentiment == "부정":
        return '<span style="color:red; font-size:22px; position:relative; top:3px;">●</span> 부정 논조'
    else:
        return '<span style="color:orange; font-size:22px; position:relative; top:3px;">●</span> 중립 논조'

# =========================
# 🗺️ 지도 생성
# =========================
def create_map(district_news):
    m = folium.Map(location=[35.1796, 129.0756], zoom_start=11)

    for d, articles in district_news.items():
        lat, lon = districts[d]

        news_html = ""
        for a in articles[:5]:
            news_html += f"""
            <a href="{a['link']}" target="_blank">
                <b>{a['title']}</b>
            </a><br>
            <small>{a['pub_date']} · {sentiment_badge(a['sentiment'])}</small><br>
            <small>{a['summary']}</small><br><br>            
            """

        # 나머지 기사 숨김
        if len(articles) > 5:
            news_html += f"<details><summary>... 외 {len(articles)-5}건 더 보기</summary><br>"

            for a in articles[5:]:
                news_html += f"""
                <a href="{a['link']}" target="_blank">
                    <b>{a['title']}</b>
                </a><br>
                <small>{a['pub_date']} · {sentiment_badge(a['sentiment'])}</small><br>
                <small>{a['summary']}</small><br><br>                
                """

            news_html += "</details>"

        popup_text = f"""
        <b>{d} ({len(articles)}건)</b><br><br>
        {news_html}
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=8 + len(articles),
            popup=folium.Popup(popup_text, max_width=300),
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.6
        ).add_to(m)

        folium.map.Marker(
            [lat, lon],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-size: 12px;
                    font-weight: bold;
                    color: black;
                    text-align: center;
                    margin-top: 18px;
                    white-space: nowrap;
                ">
                    {d}
                </div>
                """
                )
            ).add_to(m)

    filename = "busan_news_map.html"
    m.save(filename)

    file_path = os.path.abspath(filename)

    print("✅ 지도 생성 완료!")

# =========================
# 💾 요약 캐시 불러오기
# =========================
def load_summary_cache():
    try:
        with open("summary_cache.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# =========================
# 💾 요약 캐시 저장
# =========================
def save_summary_cache(cache):
    with open("summary_cache.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# =========================
# 🗺️ AI 요약
# =========================
client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

def ai_summarize(title, desc):
    try:
        text = f"제목: {title}\n설명: {desc}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "뉴스를 2문장으로 간단히 요약해줘."},
                {"role": "user", "content": text}
            ],
            max_tokens=100
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
      if "Access blocked" in desc:
        return "요약을 불러올 수 없습니다."
    return desc[:80] + "..."

# =========================
# 🗺️ 기사 감성 분
# =========================
def ai_sentiment(title, desc):
    try:
        text = f"제목: {title}\n설명: {desc}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "뉴스 감성을 한 단어로만 답해줘: 긍정, 부정, 중립"
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=10
        )

        return response.choices[0].message.content.strip()

    except:
        return "중립"

# =========================
# 🚀 실행
# =========================
try:
    news = get_news()
    district_news = defaultdict(list)

    # 캐시 불러오기
    summary_cache = load_summary_cache()

    for article in news:
        title = clean_text(article["title"])
        desc = clean_text(article["description"])
        link = article["link"]
        pub_date = article["pubDate"]

        today = datetime.now().strftime("%d %b %Y")
        if today not in pub_date:
            continue

        pub_date = format_pub_date(pub_date)

        if "Access blocked" in title or "Access blocked" in desc or "Access blocked" in link:
            continue

        text = title + " " + desc
        district = find_district(text)

        if district:
            # 이미 저장된 제목들 가져오기
            existing_titles = [
                a["title"] for a in district_news[district]
            ]

            # 중복 기사면 건너뛰기
            if is_duplicate(title, existing_titles):
                continue

            # 요약 캐시
            if title in summary_cache:
                summary = summary_cache[title]
            else:
                summary = ai_summarize(title, desc)
                summary_cache[title] = summary

            # 감성 분석
            sentiment = ai_sentiment(title, desc)

            # 저장
            district_news[district].append({
                "title": title,
                "desc": desc,
                "summary": summary,
                "link": link,
                "pub_date": pub_date,
                "sentiment": sentiment
            })

    save_summary_cache(summary_cache)
    create_map(district_news)

except Exception as e:
    print("❌ 실행 오류:", e)
