---
name: blog-onboarding
description: Use when the person who installed naver-blog-autopilot wants the plugin fitted to their own blog through a short conversation — e.g. "온보딩", "온보딩 시작", "내 블로그에 맞춰 설정", "내 블로그에 맞게 세팅해줘", "프로필 채우기", "업체 정보 채워줘", "blog-onboard", "set up my blog profile", "onboard my blog", and when /naver-blog-autopilot:blog-setup or /naver-blog-autopilot:blog-onboard hands over because check_profile.py is not OK. Asks the blog type (업체·전문가·개인·브랜드) and loads type defaults, then fills knowledge/business-profile.md (v1.1 rows such as 블로그 유형·톤·마무리 블록·주제 키워드·이미지 소스), knowledge/source-blogs.json (own_blog·design_references·topic_sources), knowledge/official-sources.md and knowledge/topic-seeds.md with existing values preserved, links image sources (AI key·Pexels·photos/) without ever receiving key values, and finally calls blog-design-system. Runs in the main session. Do NOT use for installing tools or logging in to Naver (use /naver-blog-autopilot:blog-setup), for writing a post (use /naver-blog-autopilot:blog-run), for editing an existing design system only (use blog-design-system 갱신 모드), or for recording feedback (use /naver-blog-autopilot:blog-feedback).
allowed-tools: Read, Write, Edit, Glob, Bash(python3 scripts/check_profile.py:*), Bash(python3 scripts/verify_blogs.py:*), Bash(python3 scripts/keyword_expand.py:*), Bash(python3 scripts/fetch_post.py:*), Bash(python3 scripts/fetch_posts.py:*), Bash(python3 scripts/check_image_key.py:*), Bash(awk:*), Bash(cat:*), Bash(ls:*), Bash(mkdir -p work/design-system), Bash(python3 -m json.tool:*), Bash(rm -f .env.tmp), Bash(tr:*), Bash(echo:*), AskUserQuestion, Skill
---

# 블로그 온보딩 — 설치한 사람의 블로그에 플러그인 맞추기

## 왜 이 스킬이 있나

플러그인은 설치 직후 「빈 프로필」 상태라 글을 쓸 수 없다(`check_profile.py` → `profile: MISSING …`). 이 스킬은 비개발자도 10분 안에 답할 수 있는 질문 몇 개로 **블로그 유형에 맞는 기본값**을 깔고, 프로필·레퍼런스·주제 씨앗·공신 출처·이미지 소스를 채운 뒤 디자인 시스템까지 만든다.

- 수행 주체: **메인 세션**(서브에이전트 아님). 이 스킬 안에서 서브에이전트를 부르지 않는다.
- 진입: `/naver-blog-autopilot:blog-onboard`(작업 폴더 확정 뒤 호출), `/naver-blog-autopilot:blog-setup` 5단계(`시작`을 고른 경우), 또는 트리거 문구.
- 질문·안내 원문: `${CLAUDE_PLUGIN_ROOT}/skills/blog-onboarding/references/question-bank.md`. 이미지 키 안내 정본: `…/references/image-setup.md`. 공신 출처 후보: `…/references/source-candidates.md`. 단계에 들어가기 전에 해당 절을 Read로 읽고 **그 문구를 그대로** 쓴다.
- 사용자에게 보이는 문구는 한국어로, 설명문은 `~합니다`로 쓴다.

## 지키는 것 (모든 단계)

1. **키 값·비밀번호는 어떤 단계에서도 받지 않는다.** 사용자가 채팅에 키를 붙여넣으면 그 값을 어디에도 쓰지 말고 "키는 채팅에 붙여넣지 말고 `.env` 파일에 직접 넣어 주세요. 방금 붙여넣은 키는 발급 페이지에서 폐기하고 새로 만드는 것이 안전합니다."라고 안내한다. `.env`는 값을 출력하지 않는 awk로만 존재를 본다(O0).
2. 설치 명령은 실행하지 않는다(uv·Playwright·폰트 — blog-setup 몫). 네이버 로그인은 안내만 한다.
3. **기존 값 보존 병합**(O11): 이미 채워진 행은 덮지 않고 이번에 묻고 답을 받은 항목만 바꾼다. `source-blogs.json`은 JSON으로 읽어 키만 갱신한다. `official-sources.md`·`topic-seeds.md`는 절 단위로 바꾼다.
4. 행 이름·열거값은 아래 철자 그대로 쓴다 — 행: `블로그 유형` `업체명` `연락처` `주소` `상품·서비스` `고객 지역` `강점` `장소 검색어` `톤` `마무리 블록` `문의 헤딩 문구` `주제 키워드` `이미지 소스` `이미지 기본 장면` `배지 문구` `브랜드 색` · 마무리 블록 항목: `문의헤딩` `소개이미지` `장소카드` `해시태그` · 이미지 소스 항목: `ai` `stock` `photo` · 톤: `합니다체` `해요체` · 유형: `업체` `전문가` `개인` `브랜드`.
5. 질문 수 상한: **AskUserQuestion 14개**(재실행·재확인 제외). 이 스킬의 최대 경로는 10개다(맨 끝 「질문 수」 표). 질문을 새로 만들지 않는다.

## 공통 규칙

**작업 폴더와 cwd.** 모든 경로·명령은 작업 폴더 기준이다(`python3 scripts/<이름>.py …`). 시작할 때 받은 작업 폴더 절대경로(blog-onboard·blog-setup이 넘겨 줌, 없으면 현재 폴더)를 기억한다. Bash 결과가 `No such file or directory: scripts/…`이면 cwd가 돌아간 것이므로 같은 명령 앞에 `cd "<작업 폴더 절대경로>" && `를 붙여 다시 실행한다. Windows(Git Bash)에서 `PYTHONUTF8`이 영구 설정돼 있지 않으면 python 명령 앞에 `PYTHONUTF8=1 `을 붙인다.

**자유 입력.** O2·O7a·O7b·O10은 AskUserQuestion이 아니라 question-bank 3절의 템플릿을 채팅으로 한 번 보여 주고 답을 기다린다. 받은 답은 question-bank 4절 「되돌림 확인 표」로 돌려 보여 주고 `맞아요` / `고칠게요`로 확인한다(재확인 — 질문 수 제외).

**수집 메모.** O1~O10에서 받은 값은 대화 안에 「수집 메모」 표(항목 | 값 | 출처 단계)로 들고 있다가 O11에서 한 번에 쓴다. 예외: `.env`의 `NAVER_BLOG_ID`(O3)·`IMAGE_PROVIDER`(O9) 줄과 측정 파일 `work/design-system/*.json`(O4·O7a), `work/own-posts.json`(O4)은 그 단계에서 바로 쓴다(뒤 단계가 쓰기 때문).

**유형별 기본값** (SPEC §1-1 그대로 — 온보딩만 쓴다):

| 유형 | 톤 기본 | 마무리 블록 기본 | 이미지 소스 기본 | 묻지 않는 항목 |
|---|---|---|---|---|
| 업체 | 합니다체 | 문의헤딩, 소개이미지, 장소카드, 해시태그 | ai, photo | — |
| 전문가 | 합니다체 | 문의헤딩, 해시태그 | ai | 장소 검색어 · 소개 이미지 |
| 개인 | 해요체 | 해시태그 | ai, stock | 연락처 · 장소 · 소개 이미지 · 배지 |
| 브랜드 | 합니다체 | 문의헤딩, 소개이미지, 해시태그 | ai | 장소 검색어 |

「묻지 않는 항목」은 템플릿·옵션에서 아예 빼고, 프로필의 그 행은 건드리지 않는다(개인 유형은 연락처·주소·장소 검색어·소개 이미지·배지 문구를 묻지 않는다).

---

## O0 재실행 판정

- **목적**: 작업 폴더가 준비됐는지 보고, 이미 채운 프로필이면 무엇을 다시 할지 정한다.
- **호출 명령**:
  ```bash
  ls -d knowledge scripts && ls scripts/check_profile.py scripts/verify_blogs.py scripts/keyword_expand.py scripts/fetch_post.py scripts/fetch_posts.py scripts/check_image_key.py
  ```
  하나라도 없으면 "작업 폴더가 준비되지 않았거나 스크립트가 옛 버전입니다. 먼저 `/naver-blog-autopilot:blog-setup`을 실행해 주세요."라고 안내하고 **중단**한다.
  ```bash
  python3 scripts/check_profile.py
  ```
  `.env` 상태(키 값은 출력하지 않음 — 블로그 ID·제공자 이름만 보이고 키는 OK/MISSING만):
  ```bash
  awk -v sq="'" 'BEGIN { split("NAVER_BLOG_ID IMAGE_PROVIDER GEMINI_API_KEY OPENAI_API_KEY PEXELS_API_KEY", N, " ") }
  { sub(/\r$/, ""); l = $0; sub(/^[ \t]+/, "", l); sub(/^export[ \t]+/, "", l)
    i = index(l, "="); if (i == 0) next
    k = substr(l, 1, i - 1); sub(/[ \t]+$/, "", k)
    v = substr(l, i + 1); sub(/^[ \t]+/, "", v); q = substr(v, 1, 1)
    if (q == "\"" || q == sq) { v = substr(v, 2); j = index(v, q); if (j) v = substr(v, 1, j - 1); if (v ~ /^[ \t]*$/) v = "" }
    else { if (substr(v, 1, 1) == "#") v = ""; sub(/[ \t]+#.*$/, "", v); sub(/[ \t]+$/, "", v) }
    if (v != "" && !(k in got)) got[k] = v }
  END { for (i = 1; i <= 5; i++) { k = N[i]
    if (!(k in got)) { print k ": MISSING"; continue }
    v = got[k]
    if (k == "NAVER_BLOG_ID") print k ": " (v ~ /^[A-Za-z0-9_-]+$/ ? v : "INVALID")
    else if (k == "IMAGE_PROVIDER") print k ": " (tolower(v) ~ /^(gemini|openai)$/ ? tolower(v) : "INVALID")
    else print k ": OK (.env)" } }' .env
  ```
  (값 읽기 규칙은 blog-setup 2단계 `ENVGET`과 같다. `.env`가 없으면 blog-setup 3단계가 만들므로 blog-setup을 먼저 안내한다.)
  그리고 Read로 `knowledge/business-profile.md`·`knowledge/source-blogs.json`·`knowledge/official-sources.md`·`knowledge/topic-seeds.md`(있으면)를 읽는다.
- **분기**:
  - `profile: NOFILE` → blog-setup 먼저 안내 후 중단.
  - `profile: OK` → 「현재 프로필 요약표」(블로그 유형·업체명·톤·마무리 블록·주제 키워드·이미지 소스·레퍼런스 수·공신 출처 수)를 보여 주고 question-bank O0 질문(재실행 — 질문 수 제외).
    - `그대로` → O13으로(보고만).
    - `항목만 고르기` → question-bank O0 multiSelect로 묶음을 고르고, 고른 묶음의 단계만 돈다(묶음 → 단계: 기본 정보·글 모양 = O1·O2·O5·O6·O10 / 레퍼런스·디자인 시스템 = O3·O4·O7a·O12 / 주제 키워드·공신 출처 = O7b·O8 / 이미지 소스 = O9). O11·O13은 항상 돈다.
    - `전부 다시` → O1부터 전부. 각 질문에 지금 값을 기본값으로 보여 준다.
  - `profile: MISSING …` 또는 `INVALID …`에 `업체명`·`상품·서비스`가 없으면(= 1.0.0 프로필이거나 일부만 채움) 질문 없이 「빈 행만 채우기」로 진행한다 — MISSING/INVALID에 나온 행을 묻는 단계만 돈다(`블로그 유형`→O1, `톤`→O5, `마무리 블록`→O6, `이미지 소스`→O9, `연락처`·`장소 검색어`→O2의 그 줄만, `금칙어`→O10). 레퍼런스·주제 키워드가 비어 있으면(`design_references`·`주제 키워드`에 실제 값 없음) O4·O7a·O7b도 돈다. 무엇을 묻는지 한 줄로 먼저 알린다. 이 경로에서도 O11·O13은 항상 돈다. O7b를 돌면 O8의 Q7도 함께 묻는다. 「레퍼런스·주제 키워드가 비어 있으면」은 OR다 — 둘 중 하나라도 비어 있으면 O4·O7a·O7b를 돈다(1.0.0 프로필은 보통 주제 키워드만 비어 있다). O12는 O4·O7a를 돌았거나 `톤`·`마무리 블록`이 이번에 바뀌었을 때 돈다.
  - 그 밖의 `MISSING`(첫 온보딩) → O1부터 전부.
- **쓰는 파일·행**: 없음(읽기만).

## O1 블로그 유형 — Q1

- **목적**: 유형을 정하고 위 「유형별 기본값」을 수집 메모에 깐다.
- **질문**: question-bank O1(AUQ, header `블로그 유형`, 옵션 `업체` / `전문가` / `개인` / `브랜드`).
- **분기**: 고른 유형의 기본값(톤·마무리 블록·이미지 소스)을 수집 메모에 넣고, 이후 템플릿·옵션에서 「묻지 않는 항목」을 뺀다. 재실행에서 유형을 바꾸면 "말투·글 끝 구성·이미지 소스 기본값이 바뀝니다 — 이어지는 질문에서 확인합니다." 한 줄을 알린다.
- **호출 명령**: 없음.
- **쓰는 파일·행**: (O11) `business-profile.md` `블로그 유형`.

## O2 기본 정보 — 자유 입력 1회

- **목적**: 업체(블로그) 기본 정보를 한 번에 받는다.
- **질문**: question-bank 3-1의 유형별 템플릿(업체/전문가/개인/브랜드). 받은 뒤 「되돌림 확인 표」 + `맞아요`/`고칠게요`(재확인).
- **분기**:
  - ★ 칸(`업체명`·`상품·서비스`)이 비면 그 줄만 한 번 더 묻는다(재확인).
  - `고객 지역`이 비면 수집 메모에 「비움」으로 둔다 — 지역 키워드 질문·제목 지역 로테이션·lint `title_region`이 꺼진다고 확인 표의 그 줄에 적는다.
  - `연락처`가 비었는데 유형 기본 마무리 블록에 `문의헤딩`이 있으면 확인 표에 "연락처가 없으면 글 끝 📞 문의 헤딩을 넣을 수 없습니다 — O6에서 문의 헤딩을 빼거나 연락처를 적어 주세요" 한 줄을 붙인다(따로 묻지 않음).
  - `문의 헤딩 문구`가 비면 `문의 안내`.
  - 개인 유형 템플릿에는 연락처·주소·장소 검색어 줄이 없다.
- **호출 명령**: 없음.
- **쓰는 파일·행**: (O11) `business-profile.md` `업체명` · `상품·서비스` · `연락처` · `주소` · `고객 지역` · `강점` · `장소 검색어`(업체만) · `문의 헤딩 문구`(개인 제외). 받은 칸만 쓴다.

## O3 블로그 ID — Q2 (없을 때만)

- **목적**: 글을 올릴 자기 블로그 ID를 `.env NAVER_BLOG_ID`와 `own_blog.blogId`에 같은 값으로 둔다.
- **분기**:
  - O0 awk의 `NAVER_BLOG_ID`가 ID 값이고 `own_blog.blogId`가 같거나 자리표시(`[`로 시작)면 **묻지 않는다** — O11에서 `own_blog.blogId`를 그 값으로 맞춘다.
  - `MISSING`·`INVALID`면 question-bank O3 질문(blog-setup 3-2와 같은 질문). 두 값이 모두 ID인데 다르면(MISMATCH) question-bank O3의 MISMATCH 옵션.
  - `나중에` → `.env`를 건드리지 않고 "블로그 ID가 없으면 자기 글을 가져올 수 없어 기준 글 없이(「레퍼런스 0 없음」) 진행합니다. 업로드 전에는 꼭 넣어야 합니다." 안내 후 O4는 0편 경로.
- **호출 명령**(값을 받았을 때 — blog-setup 3-2와 같은 awk 한 줄, `<블로그 ID>` 자리에 받은 값). 실행 전에 메인이 값이 블로그 ID 형식(`^[A-Za-z0-9_-]+$`)인지 확인하고, 아니면 "블로그 ID 형식이 아닙니다(영문·숫자·_·-만)"로 한 번 더 묻는다(재확인). 해당 줄만 교체하고 없으면 끝에 추가하며, `cat >`로 덮어 써 권한·심링크를 보존한다. `.env`가 없으면(awk가 파일 없음 오류) blog-setup 3단계를 먼저 안내한다. 성공(exit 0)이면 "NAVER_BLOG_ID=<값> 저장"이라고 알린다:
  ```bash
  awk -v v="<블로그 ID>" '/^[[:space:]]*(export[[:space:]]+)?NAVER_BLOG_ID[[:space:]]*=/ { if (!d) print "NAVER_BLOG_ID=" v; d = 1; next } { print } END { if (!d) print "NAVER_BLOG_ID=" v }' .env > .env.tmp && cat .env.tmp > .env && rm -f .env.tmp
  ```
- **쓰는 파일·행**: `.env` `NAVER_BLOG_ID=` 줄(즉시) · (O11) `source-blogs.json` `own_blog.blogId`.

## O4 자기 글 가져오기 — Q3

- **목적**: 정보성 카테고리와 기준 글(레퍼런스 0, `role: "own-style"`)을 정하고 측정해 둔다.
- **호출 명령**:
  ```bash
  python3 scripts/fetch_posts.py --rss <blogId> > work/own-posts.json; echo "exit=$?"
  ```
  (`work/own-posts.json`은 lint `related_links`의 `--own-posts` 기본 경로다.) 이어서 Read로 `work/own-posts.json`을 읽어 카테고리별 글 수를 센다(각 글의 `category`·`date`·`logNo`·`title`).
- **분기**:
  - **글 1편 이상**: question-bank O4의 표 두 개(카테고리별 글 수 / 추천 카테고리의 최근 글 5편 — 추천 카테고리 = 글이 가장 많은 카테고리, 추천 기준 글 = 그 카테고리의 가장 최근 글)를 보여 주고 Q3(AUQ, header `기준 글`). 바꾸기 옵션이면 기타 입력으로 반영한다. 정한 기준 글을 측정한다:
    ```bash
    mkdir -p work/design-system && python3 scripts/fetch_post.py <blogId> <logNo> --json > work/design-system/own-<logNo>.json; echo "exit=$?"
    ```
    exit가 0이 아니면 그 파일은 비어 있거나 깨진 것이므로 측정 실패로 수집 메모에 적고(O12 호출 문맥에 넘김) 기준 글은 유지한다. 측정 요약은 O7a의 awk로 같이 본다.
  - **글 0편**(exit≠0, 빈 목록, O3 `나중에`) 또는 `기준 글 없이` → 질문 없이 「레퍼런스 0 없음」 경로를 안내한다:
    "자기 블로그에 아직 가져올 글이 없어 「레퍼런스 0 없음」 경로로 진행합니다. 디자인 시스템은 템플릿·lint 기본값·외부 레퍼런스로 만들고 「측정 전」으로 표시합니다. 관련글 링크 검사는 자기 글이 2편이 될 때까지 경고(WARN)만 냅니다. 글이 쌓이면 `/naver-blog-autopilot:blog-onboard`를 다시 실행해 「레퍼런스·디자인 시스템」만 고르세요."
    O5의 `내 글 기준` 옵션은 보이지 않는다.
- **쓰는 파일·행**: `work/own-posts.json`·`work/design-system/own-<logNo>.json`(즉시) · (O11) `source-blogs.json` `own_blog.categories.info`, `design_references[0]` = `{"blogId": <blogId>, "logNo": <logNo>, "url": "m.blog.naver.com/<blogId>/<logNo>", "role": "own-style", "why": "구조·모습 전체(기준 글)"}`(레퍼런스 0은 디자인 시스템이 고정 7조각으로 쪼개므로 자동 why 구절을 쓰지 않는다). 0편이면 `own-style` 항목을 만들지 않는다.

## O5 톤 — Q4

- **목적**: 글 말투(`톤`)를 정한다.
- **호출 명령**(기준 글이 있을 때만 — 문장 끝 종결어미 수를 센다, 참고값):
  ```bash
  awk '{ f += gsub(/니다([.!?]|\\n|")/, "&"); c += gsub(/(요|죠)([.!?~]|\\n|")/, "&") } END { printf "합니다체 %d · 해요체 %d\n", f, c }' work/design-system/own-<logNo>.json
  ```
- **질문**: question-bank O5(AUQ, header `말투`). 유형 기본값 옵션에 (기본). 기준 글이 있으면 세 번째 옵션 `내 글 기준: <많은 쪽>`(두 수가 같으면 유형 기본값 쪽)을 보인다.
- **분기**: `내 글 기준`을 고르면 많은 쪽 값으로 둔다.
- **쓰는 파일·행**: (O11) `business-profile.md` `톤` = `합니다체` 또는 `해요체`.

## O6 마무리 블록 — Q5 (개인 유형은 묻지 않음)

- **목적**: 글 끝 구성(`마무리 블록`)을 정한다. `해시태그`는 항상 포함한다.
- **질문**: question-bank O6 — 업체(multiSelect 3옵션)·브랜드(multiSelect 2옵션)·전문가(넣기/넣지 않기). 개인은 묻지 않고 `해시태그`로 둔다("글 끝은 해시태그 줄만 넣습니다. 바꾸려면 나중에 온보딩을 다시 실행해 「기본 정보·글 모양」을 고르세요." 한 줄 안내).
- **분기**:
  - 값은 고른 항목 + `해시태그`를 **고정 순서** `문의헤딩, 소개이미지, 장소카드, 해시태그`로 정렬해 쓴다.
  - `문의헤딩`을 골랐는데 O2의 `연락처`가 비었으면 O11의 `check_profile.py`가 `MISSING 연락처`로 알려 주므로 거기서 그 줄만 묻는다(여기서 따로 묻지 않음).
  - `장소카드`를 골랐는데 `장소 검색어`가 비었으면 같은 방식으로 O11에서 묻는다.
  - `소개이미지`를 골랐으면 안내: "글 끝 소개 이미지는 작업 폴더의 `photos/business-intro.png`(파일명 그대로)입니다. 업체명·연락처·주소가 담긴 소개 이미지를 넣어 두세요 — 없으면 글 작성이 시작되지 않습니다." 현재 상태 확인: `ls photos/business-intro.png`.
- **쓰는 파일·행**: (O11) `business-profile.md` `마무리 블록`(그리고 O2에서 받은 `문의 헤딩 문구`·`장소 검색어`).

## O7a 레퍼런스 확보 — 안내 → 자유 입력 1회 → Q6

- **목적**: 외부(또는 자기) 레퍼런스 글 3~5편을 RSS로 검증하고 측정해 `design_references[1..]`를 만든다.
- **질문**: ① question-bank 2절 「레퍼런스 찾는 법」 안내문을 **먼저** 보여 준다(유형별, `<…>`는 O2 값). ② question-bank 3-2 자유 입력(주소·ID 0~6개). `없음`이면 O7b로. ③ 검증 표 뒤 Q6(AUQ, header `레퍼런스`).
- **호출 명령**:
  - 검증(받은 것을 한 번에):
    ```bash
    python3 scripts/verify_blogs.py <주소 또는 ID 1> <주소 또는 ID 2> … --json
    ```
    exit 0 → JSON의 항목마다 question-bank O7a 표(번호·블로그 ID·응답 `OK`/`없음`/`비공개`/`네트워크`/`형식 오류`·월 발행 `per_month`·카테고리 상위 3·최근 제목 1개). exit 2(전부 형식 오류) → "주소 형식을 알아보지 못했습니다" + 3-2 프롬프트를 한 번 더(재확인). exit 5(전부 네트워크) → "인터넷 연결을 확인해 주세요 — 레퍼런스 없이 진행하고 나중에 다시 실행할 수 있습니다" 안내 후 Q6에서 `레퍼런스 없이 진행`만 권한다.
  - 측정(고른 것마다 — `logNo`가 없던 항목은 JSON `recent[0].logNo`(가장 최근 글)를 쓴다). 번호 `<n>`은 `design_references`에서 `own-style`을 뺀 배열 순서(1부터)다 — `전부 다시`·첫 온보딩이면 1부터, `항목만 고르기`로 추가하면 기존 실제 항목 수 + 1부터:
    ```bash
    mkdir -p work/design-system && python3 scripts/fetch_post.py <blogId> <logNo> --json > work/design-system/ref-<n>-<blogId>.json; echo "exit=$?"
    ```
  - 측정 요약(기준 글 + 레퍼런스 파일을 한 번에):
    ```bash
    awk 'function out() { if (f != "") printf "%s | 글자 %s · 소제목 %s · 굵은 줄 %s · 이미지 %s · FAQ %s\n", f, v["chars"], v["headings"], v["bold_lines"], v["images"], (faq ? "있음" : "없음") }
    FNR == 1 { out(); f = FILENAME; split("", v); faq = 0 }
    { n = split("chars headings bold_lines images", a, " ")
      for (i = 1; i <= n; i++) if (!(a[i] in v) && match($0, "\"" a[i] "\": *[0-9]+")) { s = substr($0, RSTART, RLENGTH); sub(/.*: */, "", s); v[a[i]] = s }
      if ($0 ~ /FAQ|자주 묻는/) faq = 1 }
    END { out() }' work/design-system/own-<logNo>.json work/design-system/ref-<n>-<blogId>.json …
    ```
- **분기**:
  - Q6 `OK인 것 전부 쓰기` → 응답 OK 항목 전부(5개 초과면 앞 5개). `번호로 고르기` → 기타의 번호(응답 OK인 것만, 6개 이상이면 앞 5개). `레퍼런스 없이 진행` → 측정하지 않는다.
  - 측정 exit가 0이 아닌 항목은 표에서 「측정 실패」로 보이고 레퍼런스에서 뺀다.
  - **why 자동 기입**: 기타에 「번호: 이유」가 있으면 그 문장, 없으면 측정 요약에서 **특징 구절**을 만들어 `(자동) `으로 시작한다(숫자만 적지 않는다 — 레퍼런스는 URL이 아니라 이유이고, 디자인 시스템 4단계가 이 구절을 특징 조각으로 읽는다). 구절은 ` · `로 잇는다: 소제목 수 s(= `headings`, 0이면 `bold_lines`)가 1 이상이면 `소제목으로 나눠 읽기 쉬움(소제목 s개)`, `images`가 1 이상이면 `사진과 글 비율(이미지 <images>장 — 약 <chars÷images를 10단위 반올림>자당 1장)`, FAQ가 있으면 `FAQ로 마무리`. 셋 다 없으면 `(자동) 글 전체 구성`. 예: `(자동) 소제목으로 나눠 읽기 쉬움(소제목 6개) · 사진과 글 비율(이미지 8장 — 약 300자당 1장) · FAQ로 마무리`. 결과를 question-bank O7a 측정 표로 보여 준다(질문 아님 — O11 저장 확인에서 고칠 수 있음).
- **쓰는 파일·행**: `work/design-system/ref-<n>-<blogId>.json`(즉시) · (O11) `source-blogs.json` `design_references[1..]` = `{"blogId", "logNo", "url": "m.blog.naver.com/<blogId>/<logNo>", "why"}`.

## O7b 주제 소스 확보 — 자유 입력 1회 (+ Q7은 O8과 함께)

- **목적**: 주제 리서치가 읽을 소스 세 갈래(주제 소스 블로그·연관 검색어·공지 소스)를 만든다.
- **① 주제 소스 추천**: O7a 검증 결과에서 응답 OK이고 `per_month >= 2`인 블로그를 `topic_sources` 추천 목록으로 만든다(레퍼런스로 고르지 않은 것도 포함). 질문은 O8의 Q7에서 함께 받는다.
- **② 주제 키워드** — question-bank 3-3 자유 입력. **기본 제안 규칙**: `상품·서비스`(개인은 주제)를 쉼표로 나눈 항목(앞 4개, 공백 정리)을 토큰으로 삼아 ⓐ 토큰 그대로를 먼저 놓고 ⓑ 「<토큰> 방법」「<토큰> 비용」「<토큰> 후기」「<토큰> 추천」「<토큰> 비교」를 토큰을 돌아가며(1번 토큰+방법, 2번 토큰+비용, 3번 토큰+후기 …) 붙여 **합계 8개**에서 멈춘다(토큰이 1개면 그 토큰 + 다섯 조합 = 6개). 토큰이 너무 길면(공백 포함 15자 초과) 핵심 명사 2어절로 줄인다. 받은 뒤 되돌림 확인(재확인). 3개 미만이면 "3개 이상 적어 주세요"로 한 번 더(재확인), 8개 초과면 앞 8개.
  ```bash
  python3 scripts/keyword_expand.py "<씨앗 1>" "<씨앗 2>" … --depth 2 --json
  ```
  exit 0 → `[{"keyword","seed","depth"}]`를 번호 붙인 표(번호 | 키워드 | 씨앗)로 만든다(결과 0개면 "연관 검색어를 찾지 못했습니다 — 씨앗만 저장합니다"). exit 5 → "인터넷 연결 문제로 연관 검색어를 가져오지 못했습니다 — 씨앗만 저장하고, 글을 쓸 때 다시 넓힙니다".
- **③ 공지 소스**: O8에서 고른 공신 출처 중 `공지 페이지` 칸이 `—`가 아닌 것을 `## 공지 소스` 행으로 만든다(O8 뒤 O11에서 처리).
- **쓰는 파일·행**: (O11) `business-profile.md` `주제 키워드`(씨앗 쉼표 목록) · `topic-seeds.md` `## 씨앗 키워드`·`## 연관 검색어`(확인일 = 오늘 `YYYY-MM-DD`)·`## 공지 소스` · `source-blogs.json` `topic_sources`.

## O8 공신 출처 — Q7 (O7b ①·②의 정리와 함께 한 질문)

- **목적**: fact-checker가 쓸 공신 출처 3~6개를 정한다.
- **제안 규칙**: Read로 `${CLAUDE_PLUGIN_ROOT}/skills/blog-onboarding/references/source-candidates.md`를 읽고 그 파일 「쓰는 규칙」대로 `상품·서비스` 텍스트에 맞는 후보 3~6개를 고른다(법령 관련이면 law.go.kr 행 유지 → 소관 부처 → 공공 포털 → 협회 → 공통 행). 법령명은 확실한 것만, 주소는 표에 있는 것만 쓴다. 개인 유형은 후보가 0~2개여도 된다.
- **질문**: 표 세 개 — ⓐ O7b 연관 검색어 표 ⓑ 주제 소스 추천 표(블로그 ID·월 발행·카테고리) ⓒ 공신 출처 후보 표(번호 | 기관·페이지 | URL | 어떤 주장에 쓰나) — 를 보여 준 뒤 question-bank Q7(AUQ, header `주제·출처`). `출처 표는 비워 두기` 옵션은 개인 유형에만 보인다.
- **분기**: `고칠 것 있음`이면 기타의 지시(번호 빼기·출처 추가)를 반영하고 세 표를 한 번 더 보여 준다(재확인 — 질문 수 제외). 사용자가 추가한 출처는 받은 이름·주소 그대로 쓴다.
- **쓰는 파일·행**: (O11) `official-sources.md` 첫 표와 「주장 유형 → 확인 출처」 표 · `topic-seeds.md` `## 공지 소스`.

## O9 이미지 소스 연동 — Q8 · Q9 · Q10

- **목적**: `이미지 소스`를 정하고 소스마다 키·폴더를 준비시킨다. 키 값은 받지도 보지도 않는다.
- **먼저 현재 상태 확인**(비용 0 조회, 키 값은 출력되지 않음):
  ```bash
  python3 scripts/check_image_key.py 2>&1 | tr -d '\r'; echo "exit=${PIPESTATUS[0]}"
  python3 scripts/check_image_key.py --stock 2>&1 | tr -d '\r'; echo "exit=${PIPESTATUS[0]}"
  ls photos 2>/dev/null | awk 'tolower($0) ~ /\.(jpe?g|png|webp|heic)$/ && $0 != "business-intro.png" { n++ } END { print "photos: " n + 0 "장" }'
  ```
- **질문 Q8**: question-bank O9 Q8(multiSelect, header `이미지 소스`). 유형 기본값(업체 ai+photo, 개인 ai+stock, 전문가·브랜드 ai)에 (기본), 이미 키 확인이 exit 0인 소스는 라벨 끝에 `— 키 확인됨`.
- **분기 — AI(`ai`)**:
  - `check_image_key.py` exit 0 → 묻지 않고 출력 줄만 보여 준다.
  - 아니면 Q9(header `AI 제공자`). `Gemini`·`OpenAI` → `.env`의 `IMAGE_PROVIDER=` 줄**만** 쓴다(blog-setup 3-1과 같은 awk 한 줄, `<gemini 또는 openai>` 자리에 고른 값 — 해당 줄만 교체·없으면 추가, `cat >`로 권한·심링크 보존, 키 줄은 보지 않음. 성공하면 "IMAGE_PROVIDER=<값> 저장"이라고 알린다):
    ```bash
    awk -v v="<gemini 또는 openai>" '/^[[:space:]]*(export[[:space:]]+)?IMAGE_PROVIDER[[:space:]]*=/ { if (!d) print "IMAGE_PROVIDER=" v; d = 1; next } { print } END { if (!d) print "IMAGE_PROVIDER=" v }' .env > .env.tmp && cat .env.tmp > .env && rm -f .env.tmp
    ```
    이어서 image-setup.md 1-1(Gemini) 또는 1-2(OpenAI)와 0절(.env 여는 명령·"키는 채팅에 붙여넣지 말고 .env에")을 보여 준다.
  - `아직 없음 — 나중에` → `.env`를 건드리지 않고 image-setup.md 4절 문구. `ai`는 `이미지 소스`에 그대로 남긴다(키를 넣으면 바로 쓰임).
- **분기 — 스톡(`stock`)**: `--stock` exit 0 → 출력 줄만. 아니면 image-setup.md 2절(https://www.pexels.com/api/ 발급 → `.env`에 `PEXELS_API_KEY=` 한 줄) + 0절.
- **분기 — 내 사진(`photo`)**: image-setup.md 3절 + 위 `photos: n장`. 0장이면 "사진이 0장입니다 — 글을 쓰기 전에 photos/에 넣어 두세요" 한 줄(질문 아님).
- **질문 Q10**(안내를 보여 준 키가 하나라도 있으면 한 번 — AI·Pexels 함께): question-bank O9 Q10(header `키 확인`). `넣었어요` → 안내한 소스만 다시 확인한다(AI: `python3 scripts/check_image_key.py …`, 스톡: `python3 scripts/check_image_key.py --stock …`) → image-setup.md 1-3·2절의 exit별 안내. OK가 아니면 원인 안내 뒤 **한 번만** 다시 묻는다(재확인). 그래도 OK가 아니거나 `나중에 넣을게요`면 image-setup.md 4절 문구로 넘어간다 — 진행은 막지 않는다.
- **이미지 기본 장면**(질문 없음): 업체·전문가·브랜드는 메인이 `상품·서비스` 첫 항목으로 영문 장면구 2~6단어를 제안한다(예: `Korean neighborhood bicycle repair shop` 꼴 — 글자·로고·얼굴을 부르는 말은 넣지 않음). 개인은 비운다(기본 `Korean everyday scene`). O11 저장 확인 표에 보여 주고 거기서 고칠 수 있다.
- **쓰는 파일·행**: `.env` `IMAGE_PROVIDER=` 줄(즉시, AI 제공자를 고른 경우만) · (O11) `business-profile.md` `이미지 소스`(`ai`, `stock`, `photo` 순서로 고른 것만, 쉼표+공백) · `이미지 기본 장면`.

## O10 금칙어·기타 — 자유 입력 1회

- **목적**: 금칙어와 선택 항목(꼭 지켜야 할 점·배지 문구·브랜드 색)을 받는다.
- **질문**: question-bank 3-4(업체·전문가·브랜드 / 개인 — 개인은 배지 문구 줄 없음). 되돌림 확인(재확인).
- **분기**: 금칙어 `없음`/빈 칸 → `- 없음`. `브랜드 색`이 `#RRGGBB` 형식이 아니면 그 칸만 다시 묻는다(재확인). 꼭 지켜야 할 점이 없으면 프로필의 자리표시 줄(`[`로 시작하는 1번 항목)만 지우고 번호를 다시 매긴다.
- **쓰는 파일·행**: (O11) `business-profile.md` `## 금칙어` 절의 목록 줄 · `## 꼭 지켜야 할 점` 1번 항목 · `배지 문구`(개인 제외) · `브랜드 색`.

## O11 파일 쓰기·검증

- **목적**: 수집 메모를 네 파일에 **기존 값 보존 병합**으로 쓰고 검증한다.
- **저장 전 확인**: 수집 메모 전체를 question-bank 4절 표로 보여 주고 question-bank O11 질문(재확인 — 질문 수 제외). `고칠 것 있음`이면 고친 뒤 표를 한 번 더.
- **쓰기 규칙**(Read로 현재 파일을 읽은 뒤 Edit/Write):
  1. `knowledge/business-profile.md` — **행 단위 교체**. 이번에 답을 받은 행만 `| <행> | <값> |` 한 줄로 바꾼다(Edit, 그 줄만). 행이 표에 없으면 SPEC 행 순서(`블로그 유형` → `업체명` → `연락처` → `주소` → `상품·서비스` → `지원 형태` → `제공 방식` → `고객 지역` → `강점` → `장소 검색어` → `톤` → `마무리 블록` → `문의 헤딩 문구` → `주제 키워드` → `이미지 소스` → `이미지 기본 장면` → `배지 문구` → `브랜드 색` → `업체 유형어` → …)에서 바로 앞 행 다음 줄에 넣는다(`블로그 유형`은 표 머리 `|---|---|` 바로 다음). 사용자가 「비움·없음」이라고 답한 선택 행은 `| <행> | |`로 비운다. 묻지 않은 행·답이 빈 행은 손대지 않는다. `## 금칙어` 절은 설명 문단을 두고 목록 줄(`- `로 시작)만 바꾼다(각 줄 ``- `<금칙어>` ``, 없으면 `- 없음`).
  2. `knowledge/source-blogs.json` — Read로 JSON을 읽고 바꿀 키만 갱신해 Write로 전체를 다시 쓴다(다른 키·값·순서는 그대로, 들여쓰기 2칸). 갱신 키: `own_blog.blogId`(O3), `own_blog.name`(자리표시면 `업체명`), `own_blog.categories.info`(O4), `design_references`(O4·O7a), `topic_sources`(O7b). 배열은 `blogId`가 `[`로 시작하는 자리표시 항목을 지우고, 같은 `blogId`+`logNo` 항목은 새 값으로 바꾸고, 나머지 기존 실제 항목은 남긴다(`전부 다시`로 레퍼런스를 다시 받았으면 `design_references`는 이번 값으로 교체). `topic_sources` 항목 = `{"blogId", "name": <blogId>, "categories": <verify의 categories 상위 3>, "note": "월 <per_month>편 · 온보딩 추천"}`. 고른 것이 없으면 `[]`. 쓴 뒤 확인:
     ```bash
     python3 -m json.tool knowledge/source-blogs.json > /dev/null && echo "source-blogs.json: JSON OK"
     ```
  3. `knowledge/official-sources.md` — **절 단위**. ⓐ 첫 표(`| 번호 | 구분 | 이름 | URL |`)를 다시 만든다: 법령 행(확실한 법령명만, URL 칸은 기존 자리표시 행과 같은 `상세(사람용)`·`API` 형식) → 기관 행(구분 `기관`) → 맨 끝 `업체 | 업체 프로필 | knowledge/business-profile.md …` 행(기존 문구 유지), 번호는 1부터 다시. 자리표시(`[`로 시작) 행은 지우고, 이미 채워진 실제 행은 남긴다. ⓑ 「주장 유형 → 확인 출처」 표의 `[…]` 칸만 고른 출처의 「어떤 주장에 쓰나」에 맞는 이름으로 채우고, 맞는 출처가 없는 칸은 `출처필요 — 글에 수치를 쓰려면 문장마다 출처 URL을 붙입니다`. ⓒ 개인 유형으로 출처를 비웠으면 첫 표 위 설명 문단 끝에 "수치·통계를 쓰면 문장마다 출처 URL을 붙입니다." 한 문장을 더한다. 「접근성 기록」 이하 절은 건드리지 않는다.
  4. `knowledge/topic-seeds.md` — 없으면 SPEC §1-4 형식(`# 주제 씨앗` + `## 씨앗 키워드` + `## 연관 검색어` 표 `| 키워드 | 씨앗 | 확인일 |` + `## 공지 소스` 표 `| 기관 | URL | 메모 |`)으로 만든다. 있으면 이번에 바꾼 절만 통째로 바꾼다(자리표시 행은 지움). `## 공지 소스`의 URL은 공지 페이지 주소가 있으면 그 주소, 경로만 있으면 기관 URL + 메모에 경로(예: `기관 홈 → 알림 → 보도자료`).
- **검증**:
  ```bash
  python3 scripts/check_profile.py
  ```
  `profile: OK`가 아니면 출력의 그 행만 question-bank O11의 재질문(재확인, **1회**)으로 받아 1번 규칙으로 다시 쓰고 한 번 더 확인한다. 그래도 OK가 아니면 그 출력 줄을 O13 보고에 남긴다(O12는 진행).
- **쓰는 파일·행**: 위 네 파일(바꾼 행·키·절만).

## O12 디자인 시스템

- **목적**: 측정해 둔 기준 글·레퍼런스로 `knowledge/design-system.md`를 만든다(중복 fetch 없음).
- **분기**: O0 `그대로`이거나, `항목만 고르기`에서 「레퍼런스·디자인 시스템」을 고르지 않았으면 건너뛴다(O13에 「건너뜀」).
- **호출**: `Skill` 도구로 `naver-blog-autopilot:blog-design-system`을 부른다. args(호출 문맥)에 아래를 그대로 채워 넣는다:
  - 공통: "온보딩(O12)에서 호출합니다. 작업 폴더: <절대경로>. 톤: <합니다체|해요체>. 마무리 블록: <값>. 고객 지역: <있음|비움>. 측정 파일이 이미 있습니다 — `work/design-system/own-<logNo>.json`·`ref-<n>-<blogId>.json`(이번 레퍼런스: <파일 목록>; 목록에 없는 `ref-*` 파일은 지난 측정이라 쓰지 않습니다). 같은 글은 다시 받지 말고, `.md`가 없으면 JSON의 `markdown` 필드로 만드세요. 측정 실패: <목록 또는 없음>."
  - **글 0편이거나 기준 글 없이 진행했으면**(`own-style` 레퍼런스 없음) 문맥에 이 문장을 포함한다: "기준 글이 없습니다(자기 글 <N>편 — `work/own-posts.json` 기준, `own-style` 레퍼런스 없음). 스킬의 「레퍼런스 0 없음」 경로로 만들어 주세요 — 2단계 자기 글 측정 생략, 5단계 lint 키는 기본값, 7단계 조각은 외부 레퍼런스만, 수치는 「측정 전」 표기. ⑥ 관련글 항목은 편수를 적지 않고 그대로 둡니다."
  - `knowledge/design-system.md`의 현재 상태(없음 / 있음 — 자리표시 `[` n개 / 있음 — 채워짐)도 한 줄로 넘긴다. 생성·갱신 모드 판정과 담당자 검토 요청(그 스킬 8단계)은 그 스킬이 한다 — 이 스킬의 질문 수에 넣지 않는다.
- **쓰는 파일·행**: `knowledge/design-system.md`(생성 모드) 또는 `work/design-system/proposed.md`(갱신 모드) — 그 스킬이 쓴다.

## O13 보고

- **목적**: 채운 값과 남은 준비물을 한 화면에 보여 주고 첫 글로 안내한다.
- **호출 명령**(상태만 확인):
  ```bash
  python3 scripts/check_profile.py
  ls playwright-state/storage_state.json photos/business-intro.png knowledge/design-system.md knowledge/topic-seeds.md 2>&1
  ```
- **보고 표**:

  | 항목 | 값 / 상태 |
  |---|---|
  | 블로그 유형 · 업체명 | <유형> · <업체명> |
  | 톤 · 마무리 블록 | <톤> · <마무리 블록> |
  | 고객 지역 | <값 또는 「비움 — 지역 검사 꺼짐」> |
  | 기준 글(레퍼런스 0) · 레퍼런스 | <있음 logNo / 없음 — 레퍼런스 0 없음 경로> · <n>개 |
  | 주제 키워드 · 연관 검색어 · 주제 소스 · 공지 소스 | <n>개 · <n>개 · <n>곳 · <n>곳 |
  | 공신 출처 | <n>개 |
  | 이미지 소스별 키 상태 | ai: <check_image_key 결과 또는 「나중에 — 키 없음 모드」> · stock: <--stock 결과 또는 해당 없음> · photo: <n장 또는 해당 없음> |
  | 디자인 시스템 | 생성 / 갱신 제안(proposed.md 검토 대기) / 건너뜀 |
  | 프로필 검사 | <check_profile 출력 줄> |

- **남은 준비물**(해당하는 줄만):
  - 네이버 세션: `playwright-state/storage_state.json`이 없으면 "네이버 로그인은 직접 한 번 해야 합니다 — `/naver-blog-autopilot:blog-setup`의 4단계 로그인 절차를 따라 주세요."
  - 소개 이미지: `마무리 블록`에 `소개이미지`가 있는데 `photos/business-intro.png`가 없으면 O6의 안내 한 줄.
  - 폰트: "표지 제목용 한글 폰트는 `/naver-blog-autopilot:blog-setup` 진단 표의 「한글 폰트」 줄을 확인해 주세요."
  - 자기 글이 2편 미만이면: "관련글 링크는 자기 글이 2편이 될 때까지 경고만 내고 넘어갑니다."
  - 이미지 키를 미뤘으면 image-setup.md 4절 문구.
- 끝 문장(항상): "준비가 끝났습니다. 첫 글은 `/naver-blog-autopilot:blog-run`으로 시작하세요. 값을 바꾸고 싶으면 언제든 `/naver-blog-autopilot:blog-onboard`를 다시 실행해 「항목만 고르기」를 고르세요." `profile:`이 OK가 아니면 첫 문장 대신 "`knowledge/business-profile.md`의 <행>을 채운 뒤 `/naver-blog-autopilot:blog-onboard`를 다시 실행해 주세요."
- **쓰는 파일·행**: 없음.

---

## 질문 수 (상한 14 — 재실행·재확인 제외)

| # | 단계 | 종류 | 질문 | 묻는 조건 |
|---|---|---|---|---|
| Q1 | O1 | AUQ | 블로그 유형 | 항상 |
| Q2 | O3 | AUQ | 블로그 ID | `.env NAVER_BLOG_ID`가 없거나 두 값이 다를 때 |
| Q3 | O4 | AUQ | 정보성 카테고리·기준 글 | 자기 글 1편 이상 |
| Q4 | O5 | AUQ | 말투 | 항상 |
| Q5 | O6 | AUQ | 글 끝 구성 | 개인 유형 제외 |
| Q6 | O7a | AUQ | 레퍼런스 고르기 | 주소를 1개 이상 받았을 때 |
| Q7 | O7b·O8 | AUQ | 연관 검색어·주제 소스·공신 출처 저장 | 항상 |
| Q8 | O9 | AUQ | 이미지 소스 | 항상 |
| Q9 | O9 | AUQ | AI 제공자 | `ai`를 골랐고 키 확인이 OK가 아닐 때 |
| Q10 | O9 | AUQ | 키 넣었는지 확인 | 키 안내를 보여 준 소스가 있을 때 |
| — | O2 · O7a · O7b · O10 | 자유 입력 | 기본 정보 · 레퍼런스 주소 · 주제 키워드 · 금칙어 | 각 1회 |
| 제외 | O0 | 재실행 | 그대로/항목만 고르기/전부 다시 (+ 묶음 고르기) | 이미 채워진 프로필 |
| 제외 | O2·O7a·O7b·O10·O11·O9 | 재확인 | 맞아요/고칠게요 · 형식 오류 재질문 · 키 재확인 1회 · 저장 확인 · check_profile 재질문 1회 | — |

최대 경로(업체·첫 온보딩·키 없음): AUQ 10개 + 자유 입력 4회. 개인 유형: AUQ 9개(Q5 없음). blog-design-system 스킬 8단계의 담당자 검토 요청은 그 스킬의 질문이라 여기에 세지 않는다.
