#!/usr/bin/env python3
"""
뉴스 수집 및 분류 스크립트
- 국내: knews-rss (GitHub)
- 해외: Google News RSS (AP News, Bloomberg)
매일 GitHub Actions에서 자동 실행됨
"""

import json
import re
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

# ── 카테고리별 키워드 정의 ──────────────────────────────────────────────────
CATEGORIES = {
    "국내경제": {
        "keywords": ["GDP", "경제", "성장률", "물가", "소비", "내수", "기재부", "국내총생산",
                     "정부예산", "재정", "세금", "세수", "한국경제", "수출", "수입", "무역수지"],
        "label": "🇰🇷 국내경제",
        "en_keywords": []
    },
    "세계경제": {
        "keywords": ["연준", "Fed", "미국경제", "중국경제", "글로벌", "IMF", "세계은행",
                     "달러", "위안", "엔화", "무역전쟁", "관세", "WTO", "OECD"],
        "label": "🌐 세계경제",
        "en_keywords": ["Fed", "economy", "GDP", "inflation", "recession", "trade", "tariff",
                        "IMF", "World Bank", "global", "dollar", "yuan"]
    },
    "금융": {
        "keywords": ["주식", "코스피", "코스닥", "채권", "금리", "환율", "펀드", "ETF",
                     "증권", "투자", "자산", "암호화폐", "비트코인", "한국은행", "기준금리",
                     "외환", "달러", "배당"],
        "label": "💹 금융",
        "en_keywords": ["stock", "market", "S&P", "Nasdaq", "bond", "interest rate", "crypto",
                        "Bitcoin", "Fed rate", "yield", "hedge fund", "ETF", "finance", "bank"]
    },
    "산업": {
        "keywords": ["반도체", "삼성", "SK하이닉스", "LG", "현대", "기아", "배터리", "전기차",
                     "AI", "인공지능", "IT", "스타트업", "바이오", "제약", "조선", "철강",
                     "화학", "통신", "5G", "클라우드"],
        "label": "🏭 산업",
        "en_keywords": ["semiconductor", "chip", "EV", "electric vehicle", "AI", "artificial intelligence",
                        "tech", "Apple", "Google", "Microsoft", "Amazon", "Tesla", "startup", "pharma"]
    },
    "엔터": {
        "keywords": ["BTS", "블랙핑크", "드라마", "영화", "아이돌", "K-POP", "KPOP", "연예",
                     "음악", "음원", "흥행", "OTT", "넷플릭스", "디즈니", "콘서트", "연기",
                     "시청률", "웹툰", "게임"],
        "label": "🎬 엔터",
        "en_keywords": ["K-pop", "BTS", "drama", "movie", "film", "Netflix", "entertainment",
                        "music", "concert", "celebrity", "streaming", "box office"]
    },
    "스포츠": {
        "keywords": ["야구", "축구", "농구", "배구", "KBO", "K리그", "올림픽", "월드컵",
                     "손흥민", "류현진", "김민재", "UFC", "EPL", "NBA", "MLB", "골프", "테니스",
                     "마라톤", "수영"],
        "label": "⚽ 스포츠",
        "en_keywords": ["soccer", "football", "baseball", "basketball", "NBA", "MLB", "NFL",
                        "Premier League", "Champions League", "Olympics", "golf", "tennis", "UFC"]
    }
}

# ── RSS 피드 목록 ──────────────────────────────────────────────────────────
DOMESTIC_FEEDS = [
    # knews-rss 기반 주요 매체 (README에서 확인된 실제 피드)
    ("조선일보", "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml"),
    ("한국경제", "https://www.hankyung.com/feed/economy"),
    ("매일경제", "https://www.mk.co.kr/rss/30000001/"),
    ("연합뉴스", "https://www.yna.co.kr/RSS/economy.xml"),
    ("머니투데이", "https://api.mt.co.kr/mtview/a_m/economy/1/rss.xml"),
    ("이데일리", "https://rss.edaily.co.kr/edaily/newlist/Economy.xml"),
    ("SBS뉴스", "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"),
    ("KBS", "https://news.kbs.co.kr/rss/rss.do?sourceid=01&amp;isRss=Y&amp;sectionid=02"),
]

FOREIGN_FEEDS = [
    ("AP News", "https://news.google.com/rss/search?q=when:24h+allinurl:apnews.com&hl=en-US&gl=US&ceid=US:en"),
    ("Bloomberg", "https://news.google.com/rss/search?q=when:24h+allinurl:bloomberg.com&hl=en-US&gl=US&ceid=US:en"),
]

# ── 유틸리티 함수 ──────────────────────────────────────────────────────────
def fetch_rss(url: str, source: str) -> list[dict]:
    """RSS XML을 가져와 기사 목록으로 파싱"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0; +https://github.com)",
        "Accept": "application/rss+xml, application/xml, text/xml",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"  ⚠️  {source} 수집 실패: {e}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item") or root.findall(".//atom:entry", ns)
    articles = []
    for item in items[:30]:  # 피드당 최대 30건
        title_el = item.find("title")
        link_el  = item.find("link") or item.find("atom:link", ns)
        pub_el   = item.find("pubDate") or item.find("atom:published", ns)
        desc_el  = item.find("description") or item.find("atom:summary", ns)

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        link  = (link_el.text or link_el.get("href", "")).strip() if link_el is not None else ""
        pub   = pub_el.text.strip() if pub_el is not None and pub_el.text else ""
        desc  = re.sub(r"<[^>]+>", "", (desc_el.text or "")).strip() if desc_el is not None else ""

        if title and link:
            articles.append({
                "title": title,
                "link": link,
                "published": pub,
                "description": desc[:200],
                "source": source,
            })
    print(f"  ✅ {source}: {len(articles)}건")
    return articles


def classify(article: dict) -> str | None:
    """기사 제목+설명으로 카테고리 판별 (첫 번째 매치)"""
    text = (article["title"] + " " + article["description"]).lower()
    for cat, conf in CATEGORIES.items():
        kws = conf["keywords"] + conf.get("en_keywords", [])
        if any(k.lower() in text for k in kws):
            return cat
    return None


def dedup(articles: list[dict]) -> list[dict]:
    """URL 중복 + 제목 유사도 기반 중복 제거"""
    seen_urls = set()
    seen_hashes = set()
    result = []
    for a in articles:
        if a["link"] in seen_urls:
            continue
        # 제목 앞 20자 해시로 유사 중복 감지
        title_key = hashlib.md5(re.sub(r"\s+", "", a["title"])[:20].encode()).hexdigest()
        if title_key in seen_hashes:
            continue
        seen_urls.add(a["link"])
        seen_hashes.add(title_key)
        result.append(a)
    return result


# ── 메인 ──────────────────────────────────────────────────────────────────
def main():
    now = datetime.now(timezone.utc).isoformat()
    all_articles = []

    print("\n📡 국내 피드 수집 중...")
    for name, url in DOMESTIC_FEEDS:
        all_articles += fetch_rss(url, name)

    print("\n📡 해외 피드 수집 중...")
    for name, url in FOREIGN_FEEDS:
        all_articles += fetch_rss(url, name)

    print(f"\n총 수집: {len(all_articles)}건 → 중복 제거 중...")
    all_articles = dedup(all_articles)
    print(f"중복 제거 후: {len(all_articles)}건")

    # 카테고리별 분류
    categorized: dict[str, list] = {k: [] for k in CATEGORIES}
    uncategorized = []

    for a in all_articles:
        cat = classify(a)
        if cat:
            categorized[cat].append(a)
        else:
            uncategorized.append(a)

    # 카테고리별 최대 20건
    for cat in categorized:
        categorized[cat] = categorized[cat][:20]

    output = {
        "updated": now,
        "categories": {
            cat: {
                "label": CATEGORIES[cat]["label"],
                "articles": arts
            }
            for cat, arts in categorized.items()
        },
        "stats": {
            "total": len(all_articles),
            "categorized": sum(len(v) for v in categorized.values()),
            "uncategorized": len(uncategorized),
        }
    }

    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ data/news.json 저장 완료")
    for cat, data in output["categories"].items():
        print(f"   {data['label']}: {len(data['articles'])}건")
    print(f"   미분류: {len(uncategorized)}건")


if __name__ == "__main__":
    main()
