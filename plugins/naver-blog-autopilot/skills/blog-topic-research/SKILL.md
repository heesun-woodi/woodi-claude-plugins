---
name: blog-topic-research
description: Use when the user wants fresh topic candidates for the blog — e.g. "주제 찾아줘", "이번 주 블로그 주제", "주제 리서치", "오늘 뭐 쓰지", "주제 후보 표 만들어줘", "blog-topic-research", "topic research", "blog-run 1단계". Collects titles from the topic-source blogs (RSS) and our own full post list, filters by category, drops topics we already published, groups them by search intent, measures a few source posts, and writes work/topics/<date>-topics.md. Do NOT use for writing a post (blog-draft-writer), SEO scoring (blog-naver-seo), or image work (blog-image-director).
---

# 블로그 주제 리서치

## 왜 이 스킬이 있나

업체 블로그는 "무엇을 쓸까"에서 막힌다. 이 스킬은 같은 업종의 경쟁·참고 블로그의 **제목·카테고리·통계만** 읽어 후보 8~10개를 표로 만들고,
담당자가 번호만 고르면 되게 한다. 출처 글 본문은 베끼지 않는다(제목·통계만 사용). 정보성 글이 기본이고, 업체 홍보 주제는 전체의 1/4 이하.

- 수행 주체: 메인 세션(서브에이전트 아님). 전제: cwd = 작업 폴더. 지식 파일은 cwd의 `knowledge/`에서만 읽는다.
- 산출물: `work/topics/<YYYY-MM-DD>-topics.md`. 이 스킬은 **표까지만** 만든다. 번호 선택 게이트(게이트 1)는 `/naver-blog-autopilot:blog-run`이 잡는다.
- 요청 간 0.5초 간격, 순차 실행. `fetch_post.py` 호출은 최대 10회.

## 0. 전제 확인

```bash
ls scripts/fetch_posts.py scripts/fetch_post.py knowledge/source-blogs.json knowledge/business-profile.md
mkdir -p work/topics
```

없으면 "작업 폴더가 아닙니다. 먼저 `/naver-blog-autopilot:blog-setup`을 실행하세요."라고 안내하고 중단한다.
`knowledge/source-blogs.json`에서 `topic_sources[]`(`blogId`, `categories`)와 `own_blog`를 읽고, `knowledge/business-profile.md`의 금칙어를 확인해 둔다. `knowledge/learned-preferences.md`가 있으면 `## 적용 중`에서 `범주=주제` 규칙(예: "공지성 주제는 빼기", "활용·사례 주제를 더")을 읽어 둔다(`## 후보`·`## 보류·삭제`는 따르지 않는다).

## 1. 기발행 글 전체 목록 갱신 (중복 검사용)

```bash
python3 scripts/fetch_posts.py --all <own_blog.blogId> --out work/own-posts.json
```

`--all`은 `category`가 비어 있다 — 중복 검사에만 쓰고 카테고리 필터에는 쓰지 않는다. (`<own_blog.blogId>`는 `knowledge/source-blogs.json`의 값 — 작업 폴더 `.env`의 `NAVER_BLOG_ID`와 같다.)

## 2. 소스 블로그 RSS 수집

```bash
D=$(date +%F)
python3 scripts/fetch_posts.py --rss <topic_sources의 blogId 전부> --out work/topics/raw-$D.json
```

스키마는 `{blogId,title,category,date,logNo,link}` 배열. 최근 50개씩이라 블로그마다 분량이 다르다.

## 3. 카테고리 필터

각 글을 **자기 블로그의** `categories`에 든 것만 남긴다(예: 소스 블로그마다 `categories`에 적어 둔 "자전거 정비"·"자전거 정보" 같은 카테고리 — 가상).
최근 90일 글을 우선하고, 후보가 8개 미만이면 90일 밖 글까지 넓힌다. 수집 건수 → 필터 후 건수를 표 머리에 적는다.

## 4. 중복 판정 (우리 블로그 기준, 재현 가능)

판정은 `scripts/dedupe_check.py`(표준 라이브러리만, 플러그인 scaffold에 동봉)로 계산한다. 출처 글 하나당
`python3 scripts/dedupe_check.py "<출처 제목>" "<핵심 키워드>"` — `work/own-posts.json`의 **전체 행**과 비교해 가장 가까운 우리 글 1건을 출력한다.

1. **토큰화**: 날짜(`YYYY년`·`N월`·`N일`·`(요일)`)를 지우고, 한글·영숫자 외 기호(이모지와 `｜ | [] () ★ ▶ ! ? , ·` 포함 전부)를 공백으로 바꾼 뒤 어절 단위로 자른다. `business-profile.md`의 `제목 정규화` 행(선택)이 있으면 그 규칙대로 띄어쓰기를 통일한다(예: 두 어절로도 쓰는 상품명을 한 어절로 붙이기). 어절이 3글자 이상이면 끝의 조사 1글자(`은 는 이 가 을 를 의 에 도 로 과 와`)를 뗀다.
2. **제거 목록**(`business-profile.md`의 행에서 읽는다):
   - 지역: `고객 지역` 행
   - 홍보 꼬리말(모집·마감·안내처럼 공지에 붙는 말): `홍보 표지어` 행(선택 — 비우면 `dedupe_check.py`의 기본 목록)
   - 업체 유형명(제목에서 지울 업체 유형 표현): `업체 유형어` 행
   - 한글이 2글자 미만인 어절은 버린다.
3. **핵심 토큰**: 후보의 `핵심 키워드`를 같은 방식으로 토큰화한 집합에서 `업종 일반어` 행의 단어(너무 흔해서 겹침 계산에서 빼는 단어)를 뺀 것.
4. **판정**(우리 글 전체 중 ○ → △ → × 순으로 가장 센 것):
   - **○ 중복(제외)**: 자카드(두 토큰 집합) >= 0.5, **또는** 핵심 토큰 2개 이상이 우리 글 토큰에 그대로 있음. 핵심 토큰이 1개뿐인 키워드는 자카드로만 ○가 된다.
   - **△ 부분 중복(남기되 각도 변경 명시)**: 자카드 0.25 이상 0.5 미만.
   - **× 없음**: 자카드 0.25 미만.
   - **공지 유형 규칙**(`--notice`, 대량 제외용): 출처 제목에 공지 표지어(`business-profile.md`의 `공지 표지어` 행(선택 — 비우면 `dedupe_check.py`의 기본 목록), 예: 모집·일정 안내·접수 일정 같은 말)가 있고 우리 글 제목에 **같은 표지어**가 있으면 ○. 날짜·회차만 다른 공지 반복이기 때문이다. 정보 질문으로 다시 짠 후보에는 쓰지 않는다.
   - 우리 글 목록(`work/own-posts.json`)이 비어 있으면(새 블로그) 스크립트는 모든 후보에 `×`(우리 글 없음)를 낸다.
5. **스크립트 판정이 정본**이다. 사람이 바꿀 때는 표 비고에 사유를 적는다. 표에는 `○/△/× J=<자카드> core=<일치 수>`와 매칭된 우리 글 제목·날짜를 그대로 옮긴다.
6. ○는 후보 표가 아니라 "제외한 주제와 이유"로 보낸다. **글마다 행 하나**(blogId·logNo·원제·매칭된 우리 글·사유)를 쓰고 "N여 건" 같은 뭉뚱그림을 쓰지 않는다. 제외 건수 합계는 표 행 수와 일치해야 한다.
7. 출처 제목이 `business-profile.md` 금칙어와 겹치면 그대로 쓰지 않고 금칙어를 뺀 각도(절차·준비물 등)로 재구성한 제목안을 쓴다(제외 표에 "금칙어"로 기록).

(규칙의 정본은 `scripts/dedupe_check.py`다. 위 목록·임계값은 읽는 사람을 위한 사본이며, 어긋나면 스크립트가 맞다. `--help`는 한국어로 나온다.)

## 5. 검색 의도 6종으로 묶고 리서치 포인트 달기

각 후보를 다음 중 하나로 분류한다: **방법·절차 / 일정·신청 / 비용·지원 / 종류·비교 / 활용·사례 / 안전·관리**.
후보 8~10개가 최소 4종 이상에 걸치게 고른다. **학습 규칙(`범주=주제`)**을 후보 선정·제외에 반영한다 — 빼라는 주제는 "제외한 주제와 이유" 표에 사유 `학습 규칙 L-<id>`로 보내고, 더 다루라는 주제는 같은 조건이면 먼저 고른다. 금칙어·중복(○) 판정·홍보 1/4 이하 규칙이 학습 규칙보다 우선이다. 반영한 id는 표 머리에 `학습 규칙: L-…`(없으면 "없음")로 적는다. 후보마다 "풍성하게 만들 추가 리서치 포인트" 1~2개를 쓴다 —
어디서 무엇을 확인할지 구체적으로(법령 → law.go.kr `<법령명>`·시행규칙 조항, 그 밖 → `official-sources.md`에 등록한 기관 페이지).
수치·일정·조항은 이 단계에서 지어 쓰지 않는다. 조회할 곳만 적는다.

## 6. 출처 글 통계 측정 (≤ 10회)

후보 한 건당 1회, 총 10회 이하:

```bash
python3 scripts/fetch_post.py <blogId> <logNo> --json    # stats.chars, stats.images 사용
```

`sleep 0.5`로 간격을 둔다. 표에는 `chars / images`를 그대로 적고, **chars < 1500이면 ★**(우리가 더 풍성하게 쓸 여지). 측정하지 않은 후보는 "-"로 둔다(추정 금지).
원값 목록은 `work/topics/stats-<날짜>.txt`에 남겨 근거로 쓴다.

## 7. 후보 표 작성

`work/topics/<YYYY-MM-DD>-topics.md` — 후보 8~10개. **열 10개, 이 순서**:

| 번호 | 제목안 | 핵심 키워드 | 검색 의도 | 출처 글(링크) | 출처 글 chars/images | 우리 블로그 중복 | 추천 유형 | 추가 리서치 포인트 | 변주 제안 |
|---|---|---|---|---|---|---|---|---|---|

- **제목안**: 지역 키워드 1~2개(`business-profile.md`의 `고객 지역`) 포함. 이 지역 조합이 `final.md`의 `variation.region`이 된다.
- **핵심 키워드**: **단일 키워드 1개, 4어절 이하**. 그대로 `final.md` frontmatter `keyword:`에 들어가며 린트가 제목에 이 키워드가 포함되는지 검사한다 → 제목안에 그 문자열이 **연속해서 그대로**(공백 무시) 들어 있어야 한다. 아래 자체검증이 이를 강제한다.
- **출처 글**: `https://blog.naver.com/<blogId>/<logNo>` 링크와 원제.
- **우리 블로그 중복**: ○/△/× + 근거 제목(△는 어떤 각도로 다르게 갈지).
- **추천 유형**: `정보` 또는 `홍보` — `final.md`의 `variation.type`이 된다. 홍보는 후보 전체의 1/4 이하.
- **변주 제안**: 구조 템플릿(절차형/비교형/체크리스트형/Q&A형) · 도입부 유형(질문/상황/통계/오해 바로잡기). `work/variation-log.md` 최근 5줄이 있으면 겹치지 않게 제안한다(파일이 없는 첫 실행은 제약 없음).

표 아래에 **"제외한 주제와 이유"** 표를 둔다 — §4 6번 형식(글마다 1행).

**필수 자체검증(표를 닫기 전에 실행, 실패한 행은 고치고 다시 실행)** — 규칙: 공백을 모두 제거한 뒤 `키워드 in 제목안`이어야 하고(공백 무시 부분 문자열), 키워드는 4어절 이하, 어떤 제목안·키워드에도 `knowledge/business-profile.md` `## 금칙어`의 백틱 단어가 없어야 한다(금칙어도 공백 무시 비교).

```bash
python3 - <<'PY'
import re, glob
f = sorted(glob.glob("work/topics/*-topics.md"))[-1]
t = open(f, encoding="utf-8").read().split("## 제외")[0]
bad = re.findall(r"`([^`]+)`", re.search(r"## 금칙어(.*?)(?:\n## |\Z)", open("knowledge/business-profile.md", encoding="utf-8").read(), re.S).group(1))
ok = True
for l in t.splitlines():
    c = [x.strip() for x in l.strip().strip("|").split("|")]
    if len(c) == 10 and c[0].isdigit():
        k = c[2].replace(" ", "") in c[1].replace(" ", "")
        b = [w for w in bad if w.replace(" ", "") in (c[1] + c[2]).replace(" ", "")]
        n = len(c[2].split()) <= 4
        print(c[0], "kw-in-title", k, "forbidden", b, "어절<=4", n); ok &= k and n and not b
print("ALL OK" if ok else "FAIL")
PY
```

`FAIL`이면 해당 행의 키워드를 제목안에 **실제로 있는 연속 문자열**로 줄이거나 제목안을 고친다. `ALL OK`가 나오기 전에는 §8로 넘어가지 않는다.

## 8. 담당자에게 선택 요청

표 맨 끝에 한 줄을 붙이고 이 스킬은 끝낸다:

> 번호와 유형(정보/홍보), 지역 키워드 2개를 골라 주세요. 여러 개 선택해도 됩니다.

선택 이후(`gates.md` 기록, 글 폴더 생성)는 blog-run이 처리한다. 이 스킬 단독 실행 시에는 표 경로와 후보 수·의도 분포만 보고한다.

## 금칙

- 출처 글 **본문을 옮기지 않는다**(제목·통계만).
- 수치·일정·법령 조항을 근거 없이 표에 적지 않는다.
- 업체 홍보 후보는 1/4 이하. 같은 주제의 날짜만 바꾼 후보 금지.
- `business-profile.md` 금칙어를 제목안·키워드에 쓰지 않는다.
