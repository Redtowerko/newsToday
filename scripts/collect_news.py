#!/usr/bin/env python3
"""
뉴스 수집 스크립트 v3
- 카테고리별 최대 50건
- 기자명 파싱
- description 정제 (제목 중복 제거)
- 날짜 ISO8601 정규화
"""

import json, re, hashlib, sys, os, subprocess
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

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

# ── 카테고리 (우선순위 순서 유지) ─────────────────────────────────────────
CATEGORIES = {
    "금융": {
        "label": "💹 금융",
        "ko": ["코스피","코스닥","주가지수","증시","뉴욕증시","나스닥","다우존스","S&P","월가","증권",
               "주가","주가상승","주가하락","주가급등","주가급락","주가반등","주식시장","시가총액",
               "매수","매도","순매수","순매도","공매도","상한가","하한가","급등주","테마주",
               "실적주","배당주","영업이익","순이익","매출","실적","분기실적","어닝","흑자전환","적자전환",
               "국채","회사채","채권시장","금리인상","금리인하","기준금리","장단기금리",
               "환율","원달러","달러환율","달러강세","달러약세","외환시장",
               "ETF","펀드","리츠","공모주","IPO","유상증자","ELS","DLS",
               "선물","옵션","파생상품","레버리지","인버스","헤지",
               "유가","국제유가","WTI","브렌트유","두바이유","원유","금값","금시세","원자재",
               "비트코인","이더리움","암호화폐","가상자산","코인시장","업비트","빗썸",
               "한국은행","기준금리","통화정책","금통위","긴축","양적완화",
               "PER","PBR","ROE","배당수익률","부채비율","현금흐름",
               "대출금리","주담대","전세대출","예금금리","저축은행"],
        "en": ["stock market","S&P 500","Nasdaq","NYSE","Dow Jones","bond yield","interest rate",
               "cryptocurrency","Bitcoin","Ethereum","ETF","IPO","forex","exchange rate",
               "rate cut","rate hike","earnings","EPS","revenue","operating profit","net income",
               "crude oil","WTI","Brent oil","gold price","commodity","futures","options",
               "hedge fund","dividend","bear market","bull market","Fed funds rate"],
    },
    "산업": {
        "label": "🏭 산업",
        "ko": ["반도체","HBM","파운드리","메모리반도체","낸드","D램",
               "삼성전자","SK하이닉스","인텔","TSMC","엔비디아","퀄컴","AMD",
               "인공지능","AI","생성AI","챗GPT","LLM","딥러닝","머신러닝",
               "클라우드","SaaS","데이터센터","디지털전환","핀테크","블록체인",
               "전기차","배터리","이차전지","ESS","수소차","원전","SMR","태양광","풍력",
               "바이오","제약","신약","임상","FDA","항암제","백신","K바이오",
               "자율주행","로봇","드론","UAM","현대차","기아","현대모비스",
               "5G","6G","SKT","KT","LG유플러스","카카오","네이버","쿠팡",
               "조선","철강","포스코","화학","LG화학","한화","두산",
               "우주","방산","한화에어로스페이스","스타트업","유니콘","벤처","M&A"],
        "en": ["semiconductor","chip","TSMC","Nvidia","Samsung Electronics","SK Hynix",
               "electric vehicle","EV","battery","artificial intelligence","AI chip","generative AI",
               "ChatGPT","OpenAI","Anthropic","cloud computing","data center","autonomous driving",
               "Apple","Google","Microsoft","Amazon","Meta","Tesla","SpaceX",
               "pharma","biotech","clinical trial","drug approval","startup","unicorn",
               "5G","robotics","drone","supply chain"],
    },
    "엔터": {
        "label": "🎬 엔터",
        "ko": ["BTS","방탄소년단","블랙핑크","뉴진스","aespa","IVE","르세라핌","세븐틴",
               "K-POP","케이팝","아이돌","가수","배우","연예인","연예계",
               "드라마","영화","예능","OTT","넷플릭스","디즈니플러스","웨이브","왓챠","티빙",
               "시청률","흥행","박스오피스","음원","멜론","빌보드","스트리밍",
               "콘서트","팬미팅","공연","뮤지컬","뮤직비디오",
               "하이브","SM엔터","JYP","YG","카카오엔터","CJ ENM",
               "그래미","아카데미","칸","청룡","백상","웹툰","웹소설","게임","e스포츠"],
        "en": ["K-pop","BTS","Korean drama","Netflix","Disney+","box office","Grammy","Oscar",
               "entertainment","streaming","celebrity","Hollywood","Marvel","anime","gaming","esports"],
    },
    "스포츠": {
        "label": "⚽ 스포츠",
        "ko": ["야구","축구","농구","배구","골프","테니스","수영","육상","격투기","유도","태권도",
               "KBO","K리그","KBL","V리그","한국시리즈","플레이오프",
               "손흥민","류현진","김민재","오타니","황희찬","이강인","양현종","김하성",
               "EPL","프리미어리그","챔피언스리그","라리가","분데스리가",
               "NBA","MLB","NFL","NHL","PGA","ATP","WTA",
               "올림픽","월드컵","아시안게임","아시아컵","전국체전",
               "UFC","복싱","MMA","국가대표","감독","코치","트레이드","FA","드래프트"],
        "en": ["soccer","football","baseball","basketball","NBA","MLB","NFL","NHL",
               "Premier League","Champions League","La Liga","Bundesliga",
               "Olympics","World Cup","Asian Games","Grand Slam","Wimbledon",
               "golf","tennis","PGA Tour","ATP","WTA","UFC","boxing","MMA","Super Bowl"],
    },
    "세계경제": {
        "label": "🌐 세계경제",
        "ko": ["연준","미국경제","중국경제","글로벌경제","IMF","세계은행","OECD","WTO",
               "트럼프 관세","미중무역","무역전쟁","관세폭탄","보복관세",
               "달러패권","달러인덱스","위안절하","엔저","유로화",
               "G7","G20","다보스","APEC",
               "이란전쟁","중동전쟁","호르무즈","우크라이나전쟁","러시아제재",
               "유럽경기","독일경제","일본경제","인도경제","신흥국",
               "글로벌인플레","공급망위기","글로벌공급망"],
        "en": ["Federal Reserve","Fed rate","Fed cut","Fed hike","US economy","China economy",
               "global economy","IMF","World Bank","recession","tariff","trade war","OECD",
               "Trump tariff","US GDP","eurozone","Japan economy","Bank of Japan","ECB","BOJ",
               "Iran war","Middle East conflict","Ukraine war","Russia sanctions",
               "global inflation","supply chain","OPEC","G7","G20","Davos"],
    },
    "국내경제": {
        "label": "🇰🇷 국내경제",
        "ko": ["GDP","성장률","내수","기재부","재정","세수","국세","예산","추경",
               "무역수지","경상수지","수출실적","수입실적","통상","산업부",
               "소비자물가","생산자물가","물가상승","인플레이션","물가안정",
               "소비심리","기업심리","BSI","CSI","경기선행","경기동행",
               "아파트","부동산","전세","월세","분양","청약","공시가","집값","주택시장",
               "재개발","재건축","건설경기","미분양","전세대란","역전세",
               "고용률","취업자","실업률","일자리","최저임금","주52시간","노동시장",
               "임금상승","연봉","퇴직연금","육아휴직","저출생","인구감소",
               "전기요금","가스요금","유류세","기름값","휘발유값",
               "장바구니","식료품가격","외식물가","배달비","통신비",
               "부가세","소득세","법인세","종합부동산세","취득세","양도소득세",
               "국민연금","건강보험료","고용보험","복지예산","기초연금",
               "공정거래위원회","금융감독원","금융위원회","기업결합","독점","담합",
               "중소기업","소상공인","자영업자","골목상권"],
        "en": [],
    },
}

CAT_ORDER = list(CATEGORIES.keys())

DOMESTIC_SOURCES = {"조선일보","한국경제","매일경제","연합뉴스","머니투데이","이데일리","한겨레","경향신문","프레시안",
                    "구글뉴스(경제)","구글뉴스(산업)","구글뉴스(엔터)","구글뉴스(스포츠)","구글뉴스(한국Top)"}

EXCLUDE_FALLBACK = ["정치","선거","국회","대통령","대선","총선","여당","야당","민주당","국민의힘",
                    "검찰","법원","판결","재판","기소","구속","수사","경찰","범죄","사기","피의자",
                    "사건","사고","화재","붕괴","침수","재난","지진","태풍","폭설","날씨","기상",
                    "전쟁","북한","외교","안보","국방","군사","미사일","핵","통일"]

# ── RSS 피드 목록 ─────────────────────────────────────────────────────────
FEEDS = [
    ("구글뉴스(경제)",   "https://news.google.com/rss/search?q=%EA%B2%BD%EC%A0%9C+%EA%B8%88%EC%9C%B5&hl=ko&gl=KR&ceid=KR:ko"),
    ("구글뉴스(산업)",   "https://news.google.com/rss/search?q=%EB%B0%98%EB%8F%84%EC%B2%B4+%EC%82%B0%EC%97%85&hl=ko&gl=KR&ceid=KR:ko"),
    ("구글뉴스(엔터)",   "https://news.google.com/rss/search?q=%EC%97%B0%EC%98%88+%EB%93%9C%EB%9D%BC%EB%A7%88+%EC%98%81%ED%99%94&hl=ko&gl=KR&ceid=KR:ko"),
    ("구글뉴스(스포츠)", "https://news.google.com/rss/search?q=%EC%95%BC%EA%B5%AC+%EC%B6%95%EA%B5%AC+KBO&hl=ko&gl=KR&ceid=KR:ko"),
    ("구글뉴스(한국Top)","https://news.google.com/rss/headlines/section/geo/KR?hl=ko&gl=KR&ceid=KR:ko"),
    ("조선일보",  "https://news.google.com/rss/search?q=when:6h+site:chosun.com&hl=ko&gl=KR&ceid=KR:ko"),
    ("한국경제",  "https://news.google.com/rss/search?q=when:6h+site:hankyung.com&hl=ko&gl=KR&ceid=KR:ko"),
    ("매일경제",  "https://news.google.com/rss/search?q=when:6h+site:mk.co.kr&hl=ko&gl=KR&ceid=KR:ko"),
    ("연합뉴스",  "https://news.google.com/rss/search?q=when:6h+site:yna.co.kr&hl=ko&gl=KR&ceid=KR:ko"),
    ("머니투데이","https://news.google.com/rss/search?q=when:6h+site:mt.co.kr&hl=ko&gl=KR&ceid=KR:ko"),
    ("이데일리",  "https://news.google.com/rss/search?q=when:6h+site:edaily.co.kr&hl=ko&gl=KR&ceid=KR:ko"),
    ("한겨레",    "https://news.google.com/rss/search?q=when:6h+site:hani.co.kr&hl=ko&gl=KR&ceid=KR:ko"),
    ("경향신문",  "https://news.google.com/rss/search?q=when:6h+site:khan.co.kr&hl=ko&gl=KR&ceid=KR:ko"),
    ("프레시안",  "https://news.google.com/rss/search?q=when:6h+site:pressian.com&hl=ko&gl=KR&ceid=KR:ko"),
    ("Google(Business)",    "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en"),
    ("Google(Tech)",        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en"),
    ("Google(Sports)",      "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-US&gl=US&ceid=US:en"),
    ("Google(Entertainment)","https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en"),
    ("AP News",   "https://news.google.com/rss/search?q=when:6h+allinurl:apnews.com&hl=en-US&gl=US&ceid=US:en"),
    ("Bloomberg", "https://news.google.com/rss/search?q=when:6h+allinurl:bloomberg.com&hl=en-US&gl=US&ceid=US:en"),
    ("Reuters",   "https://news.google.com/rss/search?q=when:6h+allinurl:reuters.com&hl=en-US&gl=US&ceid=US:en"),
    ("CNN",       "https://news.google.com/rss/search?q=when:6h+allinurl:cnn.com&hl=en-US&gl=US&ceid=US:en"),
    ("BBC",       "https://news.google.com/rss/search?q=when:6h+allinurl:bbc.com&hl=en-US&gl=US&ceid=US:en"),
    ("NBC News",  "https://news.google.com/rss/search?q=when:6h+allinurl:nbcnews.com&hl=en-US&gl=US&ceid=US:en"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}

MAX_PER_CAT = 50

# ── 날짜 정규화 ───────────────────────────────────────────────────────────
def parse_pub_date(raw: str) -> str:
    """RFC2822 / ISO8601 등 → ISO8601 UTC 문자열로 통일. 실패 시 원본 반환."""
    if not raw:
        return ""
    try:
        dt = parsedate_to_datetime(raw)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    return raw

# ── description 정제 ─────────────────────────────────────────────────────
def clean_desc(raw_desc: str, title: str) -> str:
    """HTML 제거, 제목 중복 제거, nbsp 정리, 앞 200자만."""
    text = re.sub(r"<[^>]+>", "", raw_desc)
    text = text.replace("&nbsp;", " ").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    # 제목이 그대로 description에 들어있으면 제거
    title_clean = re.sub(r"\s+", " ", title).strip()
    if text.startswith(title_clean):
        text = text[len(title_clean):].strip(" -–—|")
    if len(text) < 20:  # 너무 짧으면 빈 string
        return ""
    return text[:200]

# ── 기자명 파싱 ──────────────────────────────────────────────────────────
def extract_author(entry) -> str:
    """feedparser entry에서 기자명 추출. 없으면 빈 string."""
    # feedparser 표준 author
    author = (entry.get("author") or "").strip()
    if author and len(author) < 40:
        return author

    # author_detail
    ad = entry.get("author_detail", {})
    name = (ad.get("name") or "").strip()
    if name and len(name) < 40:
        return name

    # Dublin Core
    for tag in entry.get("tags", []):
        if "creator" in (tag.get("term") or ""):
            return tag.get("label", "").strip()

    return ""

# ── RSS 수집 ─────────────────────────────────────────────────────────────
def fetch_feed(name: str, url: str) -> list[dict]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"  ⚠️  {name}: {e}")
        return []

    articles = []
    for entry in feed.entries[:40]:
        title = entry.get("title", "").strip()
        link  = entry.get("link", "").strip()
        pub   = parse_pub_date(entry.get("published", entry.get("updated", "")))
        desc  = clean_desc(entry.get("summary", entry.get("description", "")), title)
        author = extract_author(entry)

        if not title or not link:
            continue
        articles.append({
            "title":     title,
            "link":      link,
            "published": pub,
            "description": desc,
            "author":    author,
            "source":    name,
        })

    print(f"  {'✅' if articles else '⚠️ '} {name}: {len(articles)}건")
    return articles

# ── 분류 & 중복 제거 ─────────────────────────────────────────────────────
def classify(article: dict) -> str | None:
    text = (article["title"] + " " + article.get("description", "")).lower()
    for cat in CAT_ORDER:
        conf = CATEGORIES[cat]
        kws = conf.get("ko", []) + conf.get("en", [])
        if any(k.lower() in text for k in kws):
            return cat
    return None

def pub_ts(a: dict) -> float:
    """발행시각 → float (정렬용). 없으면 0."""
    try:
        return datetime.fromisoformat(a["published"]).timestamp()
    except Exception:
        return 0.0

def dedup(articles: list[dict]) -> list[dict]:
    seen, result = set(), []
    for a in articles:
        key = re.sub(r"\s+", "", a["title"])[:28]
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result

# ── 메인 ─────────────────────────────────────────────────────────────────
def main():
    print("\n📡 뉴스 수집 시작...\n")
    all_articles: list[dict] = []
    for name, url in FEEDS:
        all_articles += fetch_feed(name, url)

    print(f"\n총 수집: {len(all_articles)}건 → 중복제거 + 최신순 정렬...")
    all_articles = sorted(dedup(all_articles), key=pub_ts, reverse=True)
    print(f"정제 후: {len(all_articles)}건\n")

    categorized: dict[str, list] = {k: [] for k in CAT_ORDER}
    uncategorized: list[dict] = []

    for a in all_articles:
        cat = classify(a)
        if cat and len(categorized[cat]) < MAX_PER_CAT:
            categorized[cat].append(a)
        elif not cat:
            uncategorized.append(a)

    # fallback: 국내 소스 미분류 → 국내경제
    for a in uncategorized:
        if a["source"] not in DOMESTIC_SOURCES:
            continue
        text = (a["title"] + " " + a.get("description", "")).lower()
        if any(k in text for k in EXCLUDE_FALLBACK):
            continue
        if len(categorized["국내경제"]) < MAX_PER_CAT:
            categorized["국내경제"].append(a)

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "categories": {
            cat: {
                "label": CATEGORIES[cat]["label"],
                "articles": categorized[cat],
            }
            for cat in CAT_ORDER
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

    print("✅ data/news.json 저장 완료")
    for cat in CAT_ORDER:
        cnt = len(categorized[cat])
        print(f"  {'✅' if cnt >= 5 else '⚠️ '} {CATEGORIES[cat]['label']}: {cnt}건")
    print(f"  미분류: {len(uncategorized)}건")

    if output["stats"]["categorized"] == 0:
        print("\n❌ 기사를 하나도 분류하지 못했습니다!")
        sys.exit(1)

if __name__ == "__main__":
    main()
