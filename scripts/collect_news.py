#!/usr/bin/env python3
"""
뉴스 수집 스크립트 v2
- requests + feedparser 사용 (더 안정적인 RSS 처리)
- Google News RSS 경유로 국내외 기사 수집
"""

import json, re, hashlib, sys, os, subprocess
from datetime import datetime, timezone

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

try:
    import requests
except ImportError:
    print("requests 설치 중..."); install("requests"); import requests

try:
    import feedparser
except ImportError:
    print("feedparser 설치 중..."); install("feedparser"); import feedparser

# ── 카테고리 키워드 ──────────────────────────────────────────────────────
CATEGORIES = {
    "국내경제": {
        "label": "🇰🇷 국내경제",
        "keywords": ["경제성장", "GDP", "물가상승", "소비자물가", "내수", "기재부", "국내총생산",
                     "정부예산", "재정", "세수", "한국경제", "무역수지", "경상수지",
                     "산업생산", "소비심리", "수출입"],
        "en_keywords": [],
    },
    "세계경제": {
        "label": "🌐 세계경제",
        "keywords": ["연준", "미국경제", "중국경제", "글로벌 경제", "IMF", "세계은행",
                     "무역전쟁", "관세", "WTO", "OECD", "세계 경기"],
        "en_keywords": ["Federal Reserve", "Fed rate", "US economy", "China economy",
                        "global economy", "IMF", "World Bank", "recession", "tariff",
                        "trade war", "OECD", "global growth", "inflation"],
    },
    "금융": {
        "label": "💹 금융",
        "keywords": ["주식", "코스피", "코스닥", "채권", "금리", "환율", "펀드", "ETF",
                     "증권", "투자", "암호화폐", "비트코인", "기준금리", "배당", "공모주",
                     "상장", "주가", "외환"],
        "en_keywords": ["stock market", "S&P 500", "Nasdaq", "bond yield", "interest rate",
                        "cryptocurrency", "Bitcoin", "hedge fund", "ETF", "earnings",
                        "IPO", "forex", "wall street", "Fed funds"],
    },
    "산업": {
        "label": "🏭 산업",
        "keywords": ["반도체", "삼성전자", "SK하이닉스", "LG전자", "현대차", "기아",
                     "배터리", "전기차", "인공지능", "AI", "스타트업", "바이오",
                     "제약", "조선", "철강", "화학", "통신", "5G", "클라우드", "로봇"],
        "en_keywords": ["semiconductor", "chip", "electric vehicle", "EV", "artificial intelligence",
                        "AI chip", "Apple", "Google", "Microsoft", "Amazon", "Tesla",
                        "startup", "pharma", "biotech", "cloud computing"],
    },
    "엔터": {
        "label": "🎬 엔터",
        "keywords": ["BTS", "블랙핑크", "드라마", "영화", "아이돌", "K-POP", "케이팝",
                     "연예인", "음원", "흥행", "넷플릭스", "콘서트", "시청률", "웹툰", "OTT"],
        "en_keywords": ["K-pop", "BTS", "Korean drama", "Netflix", "Disney+",
                        "box office", "Grammy", "entertainment", "streaming", "celebrity"],
    },
    "스포츠": {
        "label": "⚽ 스포츠",
        "keywords": ["야구", "축구", "농구", "배구", "KBO", "K리그", "올림픽",
                     "월드컵", "손흥민", "류현진", "김민재", "EPL", "NBA", "MLB", "골프", "테니스"],
        "en_keywords": ["soccer", "football", "baseball", "basketball", "NBA", "MLB",
                        "NFL", "Premier League", "Champions League", "Olympics",
                        "golf", "tennis", "UFC", "World Cup"],
    },
}

# ── RSS 피드 ──────────────────────────────────────────────────────────────
FEEDS = [
    # 한국어 검색 기반 (Google News)
    ("구글뉴스-경제",    "https://news.google.com/rss/search?q=%EA%B2%BD%EC%A0%9C+%EA%B8%88%EC%9C%B5+%EC%A3%BC%EC%8B%9D&hl=ko&gl=KR&ceid=KR:ko"),
    ("구글뉴스-산업",    "https://news.google.com/rss/search?q=%EB%B0%98%EB%8F%84%EC%B2%B4+%EC%82%B0%EC%97%85+%EA%B8%B0%EC%97%85&hl=ko&gl=KR&ceid=KR:ko"),
    ("구글뉴스-엔터",    "https://news.google.com/rss/search?q=%EC%97%B0%EC%98%88+%EB%93%9C%EB%9D%BC%EB%A7%88+%EC%98%81%ED%99%94+%EC%95%84%EC%9D%B4%EB%8F%8C&hl=ko&gl=KR&ceid=KR:ko"),
    ("구글뉴스-스포츠",  "https://news.google.com/rss/search?q=%EC%95%BC%EA%B5%AC+%EC%B6%95%EA%B5%AC+%EB%86%8D%EA%B5%AC+%EC%8A%A4%ED%8F%AC%EC%B8%A0&hl=ko&gl=KR&ceid=KR:ko"),
    ("구글뉴스-한국Top", "https://news.google.com/rss/headlines/section/geo/KR?hl=ko&gl=KR&ceid=KR:ko"),
    # 언론사 직접 (Google News 경유)
    ("조선일보",  "https://news.google.com/rss/search?q=when:24h+site:chosun.com&hl=ko&gl=KR&ceid=KR:ko"),
    ("한국경제",  "https://news.google.com/rss/search?q=when:24h+site:hankyung.com&hl=ko&gl=KR&ceid=KR:ko"),
    ("매일경제",  "https://news.google.com/rss/search?q=when:24h+site:mk.co.kr&hl=ko&gl=KR&ceid=KR:ko"),
    ("연합뉴스",  "https://news.google.com/rss/search?q=when:24h+site:yna.co.kr&hl=ko&gl=KR&ceid=KR:ko"),
    ("머니투데이","https://news.google.com/rss/search?q=when:24h+site:mt.co.kr&hl=ko&gl=KR&ceid=KR:ko"),
    # 해외 (Google News 섹션)
    ("Google-Business",     "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en"),
    ("Google-Technology",   "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en"),
    ("Google-Sports",       "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-US&gl=US&ceid=US:en"),
    ("Google-Entertainment","https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en"),
    ("AP News",     "https://news.google.com/rss/search?q=when:24h+allinurl:apnews.com&hl=en-US&gl=US&ceid=US:en"),
    ("Bloomberg",   "https://news.google.com/rss/search?q=when:24h+allinurl:bloomberg.com&hl=en-US&gl=US&ceid=US:en"),
    ("Reuters",     "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com&hl=en-US&gl=US&ceid=US:en"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}

def fetch_feed(name, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"  ⚠️  {name}: {e}")
        return []

    articles = []
    for entry in feed.entries[:30]:
        title = entry.get("title", "").strip()
        link  = entry.get("link", "").strip()
        pub   = entry.get("published", entry.get("updated", ""))
        desc  = re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip()[:250]
        if title and link:
            articles.append({"title": title, "link": link,
                              "published": pub, "description": desc, "source": name})

    print(f"  {'✅' if articles else '⚠️ '} {name}: {len(articles)}건")
    return articles

def classify(article):
    text = (article["title"] + " " + article["description"]).lower()
    for cat, conf in CATEGORIES.items():
        kws = conf["keywords"] + conf.get("en_keywords", [])
        if any(k.lower() in text for k in kws):
            return cat
    return None

def dedup(articles):
    seen_urls, seen_hashes, result = set(), set(), []
    for a in articles:
        if a["link"] in seen_urls:
            continue
        h = hashlib.md5(re.sub(r"\s+", "", a["title"])[:25].encode()).hexdigest()
        if h in seen_hashes:
            continue
        seen_urls.add(a["link"])
        seen_hashes.add(h)
        result.append(a)
    return result

def main():
    print("\n📡 뉴스 수집 시작...\n")
    all_articles = []
    for name, url in FEEDS:
        all_articles += fetch_feed(name, url)

    print(f"\n총 수집: {len(all_articles)}건 → 중복 제거 중...")
    all_articles = dedup(all_articles)
    print(f"중복 제거 후: {len(all_articles)}건\n")

    categorized = {k: [] for k in CATEGORIES}
    uncategorized = []
    for a in all_articles:
        cat = classify(a)
        if cat:
            categorized[cat].append(a)
        else:
            uncategorized.append(a)

    for cat in categorized:
        categorized[cat] = categorized[cat][:20]

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "categories": {
            cat: {"label": CATEGORIES[cat]["label"], "articles": arts}
            for cat, arts in categorized.items()
        },
        "stats": {
            "total": len(all_articles),
            "categorized": sum(len(v) for v in categorized.values()),
            "uncategorized": len(uncategorized),
        },
    }

    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("✅ 저장 완료: data/news.json")
    for cat, data in output["categories"].items():
        cnt = len(data["articles"])
        print(f"  {'✅' if cnt else '⚠️ '} {data['label']}: {cnt}건")
    print(f"  미분류: {len(uncategorized)}건")

    if output["stats"]["categorized"] == 0:
        print("\n❌ 기사를 하나도 가져오지 못했습니다!")
        sys.exit(1)

if __name__ == "__main__":
    main()
