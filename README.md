# 📰 나만의 뉴스 대시보드

국내외 주요 언론사 RSS를 자동 수집해서 카테고리별로 보여주는 개인 뉴스 페이지입니다.  
**GitHub 계정만 있으면 완전 무료**로 운영할 수 있습니다.

## ✨ 기능

| 기능 | 설명 |
|------|------|
| 📡 자동 수집 | 매일 오전 6시(KST) GitHub Actions가 자동 실행 |
| 🗂️ 카테고리 분류 | 국내경제 / 세계경제 / 금융 / 산업 / 엔터 / 스포츠 |
| 🌏 국내+해외 | 조선·한경·연합 + AP News·Bloomberg |
| 📱 반응형 | PC·모바일 모두 지원 |
| 💰 비용 | 완전 무료 (GitHub Free 기준) |

---

## 🚀 설치 방법 (5단계)

### 1단계 — 저장소 Fork

1. 이 저장소 우측 상단 **Fork** 클릭
2. 내 계정으로 복사 완료

### 2단계 — GitHub Pages 활성화

1. 내 저장소 **Settings** 탭
2. 왼쪽 메뉴 **Pages**
3. Source: **Deploy from a branch**
4. Branch: **main**, Folder: **/ (root)**
5. **Save** 클릭

> 🔗 주소: `https://[내GitHub아이디].github.io/[저장소이름]/`

### 3단계 — Actions 권한 확인

1. **Settings → Actions → General**
2. **Workflow permissions** → **Read and write permissions** 선택
3. **Save**

### 4단계 — 첫 번째 뉴스 수집 (수동 실행)

1. **Actions** 탭 클릭
2. 왼쪽 **"📰 매일 뉴스 수집"** 선택
3. **Run workflow** → **Run workflow** 클릭
4. 1~2분 후 완료 → `data/news.json` 생성됨

### 5단계 — 확인

브라우저에서 GitHub Pages 주소 접속! 🎉

---

## 🗂️ 파일 구조

```
news-dashboard/
├── index.html                    # 뉴스 대시보드 UI
├── data/
│   └── news.json                 # 수집된 뉴스 (자동 생성)
├── scripts/
│   └── collect_news.py           # RSS 수집·분류 스크립트
└── .github/
    └── workflows/
        └── collect.yml           # GitHub Actions 스케줄
```

---

## ⚙️ 커스터마이징

### 카테고리 키워드 추가/변경

`scripts/collect_news.py` 상단 `CATEGORIES` 딕셔너리 수정:

```python
"금융": {
    "keywords": ["주식", "코스피", "비트코인", ...],  # 추가 가능
}
```

### 피드 추가

`DOMESTIC_FEEDS` 또는 `FOREIGN_FEEDS` 리스트에 추가:

```python
DOMESTIC_FEEDS = [
    ("뉴스위크코리아", "https://www.newsweek.co.kr/rss/allnews.xml"),
    ...
]
```

### 수집 주기 변경

`.github/workflows/collect.yml`의 cron 표현식 수정:

```yaml
- cron: "0 21 * * *"   # UTC 21:00 = KST 06:00 (매일)
- cron: "0 */6 * * *"  # 6시간마다
```

---

## 🛠️ 문제 해결

| 증상 | 해결 |
|------|------|
| 페이지가 빈 화면 | Actions 수동 실행으로 `data/news.json` 생성 |
| 특정 피드 0건 | 해당 매체 RSS 주소 변경됐을 수 있음 → `DOMESTIC_FEEDS` 수정 |
| 카테고리 기사 부족 | `CATEGORIES`에 키워드 추가 |
| Actions 실행 오류 | Settings → Actions → General → Read&write 권한 확인 |

---

## 📄 라이선스

MIT
