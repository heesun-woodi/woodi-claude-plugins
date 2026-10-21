---
name: blog-draft-writer
description: Use when a Naver blog post must be written as a draft or revised after fact-check — e.g. "초안 써줘", "블로그 글 작성", "이 주제로 글 써줘", "draft", "blog-run B 단계", "팩트체크 반영해줘", "draft-v2 만들어줘", "blog-run B' 단계". Mode B researches facts with source URLs (research.md) and writes draft.md in the tone set by the profile's 톤 row (합니다체 or 해요체) following knowledge/design-system.md (fixed skeleton — intro, 📑 TOC, keycap headings, FAQ, related-link placeholders only when the blog has 2+ own posts, the 📞 contact heading as last line only when the profile's 마무리 블록 includes 문의헤딩 — section-end image slots, bold/💡 emphasis, `(출처: URL)`-only citations, title with the gate-1 title_region only when the profile has 고객 지역, variation vs work/variation-log.md). Mode B' applies factcheck.md, then the blog-naver-seo procedure, swaps [[관련글]] for real own-blog post URLs (2+ own posts only), adds the final.md frontmatter, and saves draft-v2.md. Do NOT use for fact verdicts (blog-fact-check), topic research (blog-topic-research), image generation (blog-image-director), or upload (blog-naver-upload).
---

# 블로그 초안 작성(B)·수정(B')

## 왜 이 스킬이 있나

담당자가 고른 주제를 **디자인 시스템 한 장(`knowledge/design-system.md`)대로**, 출처 있는 사실만으로 쓰기 위해서다.
쓰는 쪽(이 스킬)과 검토하는 쪽(blog-fact-check)은 분리되어 있다 — 여기서는 사실 판정을 내리지 않고, 결정적 검사는 `lint_post.py`가 센다.

- 수행 주체: `blog-writer` 에이전트(`/naver-blog-autopilot:blog-run`의 B·B' 단계). 사람이 직접 요청하면 메인이 같은 절차로 수행한다.
- 전제: cwd = 작업 폴더. 지식 파일은 cwd의 `knowledge/`에서만 읽는다(`${CLAUDE_PLUGIN_ROOT}`의 지식 파일은 읽지 않는다).
- 글 폴더: `work/posts/<NNN-slug>/` (아래에서 `P`로 줄여 쓴다).
- 모드: 발주 프롬프트의 `mode: B` 또는 `mode: B'`. 없으면 `P/draft.md`가 없을 때 B, 있고 factcheck 파일이 있으면 B'.
- 수치(글자수·소제목 수·이미지 수·굵게 빈도 등)는 **`design-system.md` ④가 정본**이다. 아래에는 숫자 대신 ④ lint 블록의 키 이름(`min_chars` 등)과 ③의 범위를 적었다 — 값은 매번 그 문서에서 읽는다.
- 이 스킬이 만드는 `draft.md`·`draft-v2.md`는 **출처 포함본**이다. 업로드본(`final.md`)은 메인이 Step 4에서 `scripts/build_final.py`로 만든다(슬롯 → 이미지 경로·캡션 비움, `(출처: URL)` 제거, 소제목 앞 여백, 프로필 `마무리 블록`대로의 마무리 블록 — 소개이미지·장소카드·해시태그). 그 일들은 여기서 하지 않는다.

| 모드 | 읽기 | 쓰기(이 파일들만) |
|---|---|---|
| B | `P/gates.md`, `P/topic.md`(topics 표의 해당 행), `knowledge/design-system.md`·`business-profile.md`·`official-sources.md`, `work/variation-log.md`(없을 수 있음), `knowledge/learned-preferences.md`(없을 수 있음), 이 스킬의 `references/structure-templates.md` | `P/research.md`, `P/draft.md` |
| B' | 위 전부 + `P/research.md`, `P/draft.md`, `P/factcheck.md`(r2면 `P/factcheck-r2.md`), `knowledge/naver-seo-checklist.md`, `work/own-posts.json`, blog-naver-seo 스킬 `SKILL.md` | `P/draft-v2.md`, `P/seo.md`, `P/research.md`(끝에 `## B' 추가 출처` 절 덧붙이기만) |

**공통 금지**: 위 표의 출력 파일 외에는 어떤 파일도 만들거나 고치지 않는다. `gates.md`는 메인만 쓴다(읽기만). `draft.md`는 B'에서 고치지 않는다(fact-checker가 판정한 원본). `knowledge/`(`learned-preferences.md` 포함)·`work/variation-log.md`·`work/own-posts.json`도 읽기만. 조회 응답 같은 임시 파일은 작업 폴더 밖(`T=$(mktemp -d)`)에 둔다.

---

## 모드 B — 초안

### B-0. 전제 확인

```bash
ls knowledge/design-system.md knowledge/business-profile.md knowledge/official-sources.md scripts/lint_post.py
ls work/posts/<NNN-slug>/
```

`knowledge/`가 없으면 "작업 폴더가 아닙니다. 먼저 `/naver-blog-autopilot:blog-setup`을 실행하세요."로 반환한다. `gates.md`나 `topic.md`가 없으면 추측하지 말고 `## 질문`으로 반환한다.

### B-1. 입력 읽기

- `gates.md`의 `## 선택`: 번호, **유형(정보/홍보)**, **지역 키워드 2개**, **제목 지역**(`- 제목 지역: <지역>` 줄 — 게이트 1 전에 메인이 ⑦ 로테이션으로 정해 기록한다). 이 값들은 담당자의 결정이므로 바꾸지 않는다. **프로필 `고객 지역`이 없으면** 지역 키워드·제목 지역은 `-`이고 지역 변주·제목 지역이 없다(로테이션 계산도 질문도 하지 않는다). 지역이 1개뿐이면 지역 키워드·제목 지역은 그 하나다. 유형이 비어 있으면 `topic.md`의 "추천 유형"을 쓰고 리포트에 적는다. 고객 지역이 있는데 `제목 지역:` 줄이 없으면 ⑦ 로테이션(참고: `business-profile.md` `고객 지역` 행에 적힌 순서에서 `work/variation-log.md` 최근 4편의 `title_region`에 안 쓰인 첫 지역 → 그 지역이 고른 2개 안에 없으면 2개 중 로그상 더 오래전에 쓰인 쪽, 동률이면 안 쓰인 지역 우선, 같으면 고객 지역 순서 앞쪽)으로 직접 정하고 리포트 `## 질문`에 "gates.md에 제목 지역 줄 없음 — <지역>으로 씀" 한 줄을 남긴다.
- `topic.md`(topics 표 한 행): 제목안, **핵심 키워드**(그대로 이 글의 keyword), 검색 의도, 추가 리서치 포인트, 변주 제안.
- `design-system.md` ①~⑨ 전부(특히 ② 톤, ③ 고정 골격·소제목, ④ 수치, ⑤ 이미지, ⑥ 마무리 고정 블록, ⑦ 변주, ⑧ 금칙·출처 형식, ⑨ 홍보글 규칙).
- `business-profile.md`: 업체정보 표·꼭 지켜야 할 점·`## 금칙어` 목록. 글의 모양을 정하는 행: `톤`(`합니다체`/`해요체` — 행이 없으면 합니다체), `마무리 블록`(`문의헤딩`·`소개이미지`·`장소카드`·`해시태그` 중 — 이 글의 마지막 줄이 정해진다), `문의 헤딩 문구`(기본 `문의 안내`), `연락처`, `고객 지역`. `work/own-posts.json`의 글 수(메인이 발주 메시지로 알려 준다)가 2 미만이면 관련글 자리를 쓰지 않는다(B'에서도).
- `learned-preferences.md`(있으면 — 담당자 피드백에서 정리된 학습 규칙): **`## 적용 중`** 표에서 범주가 `제목`·`톤`·`구조`·`분량`·`내용`·`SEO`인 규칙을 읽어 B-3·B-4(그리고 B' 전체)에 적용한다. `## 후보`·`## 보류·삭제`는 따르지 않는다. `## 피할 표현`의 표현은 쓰지 않는다(lint `learned_avoid`가 WARN으로 센다).
  - **우선순위**: 잠긴 규칙(잠긴 규칙 = `business-profile.md` 금칙어·꼭 지켜야 할 점, `design-system.md` ⑤ 반드시 지킬 것(이미지 속 글자·얼굴 클로즈업·로고 금지, 홍보글은 실사진만, 사진 재사용 금지), ⑧ 지어내기 금지·출처·금칙) > `## 적용 중` 학습 규칙 > `design-system.md` 나머지 > `references/structure-templates.md` 예시. 즉 학습 규칙은 디자인 시스템의 기본값(구성·말투 세부·분량 배분)보다 앞서지만, 잠긴 규칙을 바꾸지 못한다.
  - lint 기준(② 톤, ④ 수치 범위)을 벗어나게 만드는 규칙은 그 범위 안에서만 따른다(예: "더 짧게" → ④ 글자수 하한 안에서 줄임).
  - 충돌하면 잠긴 규칙(또는 lint 범위)대로 쓰고, 반환 `## 질문`에 `L-<id>은 <잠긴 규칙·lint 항목>과 충돌 — 잠긴 규칙대로 씀` 한 줄을 남긴다.
  - 실제로 적용한 규칙 id를 기억해 B-6·B'-5 반환의 `학습 규칙 적용:` 줄에 적는다.

### B-2. 추가 리서치 → `research.md`

1. `topic.md`의 "추가 리서치 포인트"와 쓰려는 수치·일정·조항마다 `knowledge/official-sources.md`의 조회처에서 사실을 모은다.
   - 명령: `curl -sL -A "Mozilla/5.0" --max-time 20 "<URL>"`(Bash) 또는 WebFetch. WebFetch가 실패하면 curl로 다시 시도. 요청은 순차, 0.5초 이상 간격.
   - 법령: DRF `lawSearch.do?...&query=<법령명>`로 현행 MST·시행일자 확인 → `lawService.do?...&MST=<MST>&type=XML`에서 조문을 찾는다.
   - 가격·수수료·통계·일정: `official-sources.md`에 등록한 기관 페이지(수수료 안내·통계표·월간 일정·공고). 빈 일정 표로 일정을 단정하지 않는다.
   - 지원 제도(보조금·할인 제도 등): 기관 상세 페이지가 JavaScript로 그려져 curl로 보이지 않을 수 있다(`official-sources.md` 접근성 기록) → 금액·비율은 쓰지 않고, 제도 언급은 "<기관>에서 최신 조건 확인" 문구로 쓴다.
   - `official-sources.md` 접근성 기록에서 "껍데기만"인 URL은 사실 확인 근거로 쓰지 않는다.
2. **이번에 실제로 열어서 문구를 확인한 사실만** 표에 적는다. 열지 못했거나 문구를 못 찾은 사실은 글에 쓰지 않는다. 주제에 꼭 필요해서 남겨야 하면 본문에 `[출처 필요]`를 붙인다(fact-checker가 잡고, lint `placeholder_sources`가 FAIL로 센다).
3. `research.md` 형식:

```markdown
# 리서치 — <NNN-slug>

| 사실 | 출처 URL | 조회 일시 |
|---|---|---|
| <상품·서비스> 이용 수수료 <금액>(<YYYY>년 <M>월 <기관> 기준) | <official-sources.md에 등록한 수수료 안내 URL> | YYYY-MM-DD HH:MM |
| <법령명> 시행규칙 제<n>조 — "<원문 1줄>" (시행 <YYYY-MM-DD>) | https://www.law.go.kr/DRF/lawService.do?OC=test&target=law&MST=<MST>&type=XML | YYYY-MM-DD HH:MM |

## 변주 선택
structure: <…> · intro: <…> · region: [<지역1>, <지역2>] · title_region: <gates.md의 제목 지역 — 고객 지역이 없으면 -> · type: <정보|홍보>
근거: <한 줄 — 최근 5줄과 각각 몇 개 축이 다른지>

## 출처를 못 찾은 것
- <쓰지 않은 사실 또는 [출처 필요]로 남긴 문장> — <어디를 봤는지 URL>
```

   - 사실 칸에는 출처 원문과 같은 값(숫자·조문 번호·시행일자)을 쓴다. 출처 URL은 전체 주소. 열지 않은 URL은 적지 않는다.
   - 시점이 바뀌는 값(가격·수수료·통계·일정)은 "YYYY년 M월 <기관> 기준"을 사실 칸과 본문 양쪽에 붙인다(fact-checker는 기준 시점이 없으면 PASS를 주지 않는다).

### B-3. 구조·변주 선택

1. `references/structure-templates.md`의 본문 전개 방식(구조 템플릿) 4종 중 1개 + 도입부 유형 4종 중 1개를 고른다(`범주=구조` 학습 규칙이 있으면 그 규칙에 맞는 것 중에서). 지역은 `gates.md`의 2개, 제목 지역은 `gates.md`의 `제목 지역:` 값(B-1) — 둘 다 고객 지역이 없으면 `-`. 마무리는 ⑥ 고정 블록이라 고르지 않는다(`cta` 축 없음).
2. `work/variation-log.md`를 읽는다. 형식은 한 줄 7열 `YYYY-MM-DD | posts/NNN-slug | type | structure | intro | region | title_region`. 이 형식의 줄 중 **마지막 5줄 각각**과 비교해 4개 축(structure·intro·region·title_region) 중 **2개 이상**이 달라야 한다(region은 순서 무시, 두 지역 집합으로 비교). 한 줄이라도 1개 축만 다르면 다시 고른다. 지역·제목 지역은 담당자가 정했으므로 structure·intro를 바꿔 맞춘다. 고객 지역이 없으면 region·title_region 축이 없으므로(항상 `-`) structure·intro 2축 중 **1개 이상** 달라야 한다. 파일이 없거나 해당 형식의 줄이 없으면 제약 없음.
3. `topic.md`의 "변주 제안"이 위 규칙을 통과하면 그것을 우선 쓴다.
4. ⑨: 유형이 홍보이고 **이번 글을 포함한 최근 4편**(로그 최근 3줄 + 이번 글) 중 홍보가 2편 이상이 되면(로그가 없으면 각 글 `gates.md ## 선택`의 유형으로 센다) 그대로 쓰되 리포트 `## 질문`에 "⑨ 비율 초과 — 정보로 바꿀지" 한 줄을 남긴다.
5. 고른 값과 근거 한 줄을 `research.md`의 `## 변주 선택`에 적는다(B'가 frontmatter로 옮긴다).

### B-4. `draft.md` 작성

frontmatter 없이 첫 줄이 `# 제목`이다(frontmatter는 B'에서 붙인다). 뼈대는 `design-system.md` ③ **고정 골격** 그대로다. 표지 슬롯은 쓰지 않는다(표지는 이미지 단계가 image-plan `00` 행으로 만들고, 업로드 단계가 본문 맨 앞에 넣는다).

```markdown
# <제목 — keyword를 그대로 포함 + 제목 지역(title_region) 지역명 1개(고객 지역이 있을 때만), ④ title_min~title_max자>
<도입 1문단 — 고른 도입부 유형으로 상황·질문>

<도입 2문단 — **결론 굵게**(검색 의도의 답)>

## 📑 목차
- <소제목 1 텍스트(번호 이모지 없이)>
- <소제목 2 텍스트>
- …
- 자주 묻는 질문 (FAQ)

---
## 1️⃣ <소제목 1 — 검색형 명사구/질문, 끝 이모지 선택>
<본문 — ③ 소제목당 글자수 범위 안, 짧은 문단 · ✔️/📖/🚧 이모지 줄(줄마다 빈 줄로 구분) · 💡 팁 줄 · **핵심 굵게** · (글당 0~1개) 비교표>
![슬롯: <이 절 내용을 요약하는 장면 설명>]()

## 2️⃣ <소제목 2>
<본문>
![슬롯: …]()

…본문 소제목 ④ min_h2~max_h2개(목차·문의 제외, FAQ 포함)…

## n️⃣ 자주 묻는 질문 (FAQ)
**Q. <질문 — 끝이 ~까요?/~나요?/~습니까?/~인가요?/~세요? 중 하나>**

A. <답 문단>

**Q. …**

A. …

[[관련글: <주제 1>]]                ← 자기 글(work/own-posts.json)이 2편 이상일 때만. 2편 미만이면 이 줄들을 쓰지 않는다
[[관련글: <주제 2>]]

## 📞 <문의 헤딩 문구>: <연락처>      ← `마무리 블록`에 `문의헤딩`이 있을 때만(문구 기본 `문의 안내`). 없으면 이 줄 없이 FAQ(또는 관련글)가 마지막
```

`마무리 블록`에 `문의헤딩`이 있으면 `## 📞 <문의 헤딩 문구>: <연락처>`가 **초안의 마지막 줄**이다(문구는 프로필 `문의 헤딩 문구`, 비어 있으면 `문의 안내`). `문의헤딩`이 없으면 이 줄을 쓰지 않고 FAQ(또는 관련글)가 마지막이다. 어느 쪽이든 그 뒤의 소개 이미지(`소개이미지`일 때 `photos/business-intro.png`)·장소 카드(`장소카드`일 때 `:::place`)·`**#태그 …**` 해시태그 줄은 `build_final.py`가 `마무리 블록`대로 붙이므로 쓰지 않는다. 줄글 CTA 단락(업체명·연락처·주소를 늘어놓는 문단)도 쓰지 않는다(⑥). 소제목 앞 여백(`ㅤ` 줄)도 업로드 단계가 넣는다 — 초안에 쓰지 않는다.

규칙(숫자는 `design-system.md` ④가 정본 — 아래 키 이름의 값을 그 lint 블록에서 읽는다):

- **제목**: 첫 줄 `# `. `topic.md`의 핵심 키워드를 공백 무시하고 연속 문자열로 포함, ④ `title_min`~`title_max`자. 프로필 `고객 지역`이 있으면 지역명은 **제목 지역(title_region) 1개만** 넣는다(다른 고객 지역명을 함께 넣지 않는다 — lint `title_region`). 고객 지역이 없으면 지역명을 넣지 않는다(lint `title_region`은 SKIP). 본문이 답하지 않는 약속(낚시) 금지.
- **도입 2문단**: 1문단 = 고른 도입부 유형(질문/상황/통계/오해 바로잡기)으로 독자 처지·질문, 2문단 = 결론 **굵게**("결론부터 말씀드리면, **…**"). "안녕하세요 + 업체 소개"로 시작하지 않는다.
- **목차**: `## 📑 목차` 아래 `- ` 목록, 항목 = 본문 소제목 텍스트(번호 이모지 없이, 같은 순서, FAQ 포함). 목록 뒤 빈 줄, `---` 한 줄. 목차 절은 글자수·키워드 횟수에 들어가지 않는다.
- **소제목**: `## 1️⃣ `처럼 키캡 번호(1️⃣~9️⃣) + 검색형 명사구 또는 질문("~방법 / ~순서 / ~비용 / ~기준 / ~할까요?") + 끝 이모지 선택. 본문 소제목 ④ `min_h2`~`max_h2`개(목차·문의 제외, FAQ 포함). 제목을 소제목으로 반복하지 않는다. 키워드는 소제목 1~2개에 자연스럽게. 고른 전개 방식(절차·비교·체크리스트·Q&A)은 이 번호 절들을 어떻게 펼칠지만 정한다.
- **절 본문 요소**: 짧은 문단(2~4문장), `✔️`/`📖`/`🚧` 이모지 줄(한 줄 = 한 항목, 줄 사이 빈 줄), `💡` 팁 줄, **굵게**. 비교표는 글당 0~1개(표 칸의 수치는 표 바로 아래 문장에 `(출처: URL)`로 근거를 단다). 음영 인용 `> `은 글당 0~1개 — 강조는 굵게 + 💡 줄이 맡는다.
- **FAQ**(권장): 마지막 번호 절 `## n️⃣ 자주 묻는 질문 (FAQ)`, 2~4문답. `**Q. …?**` 줄 → 빈 줄 → `A. …` 문단. Q 줄도 본문으로 센다 — 프로필 `톤`이 합니다체면 의문문은 끝이 `~까요?`·`~나요?`·`~ㅂ니까?/~습니까?`·`~인가요?`·`~세요?`면 된다(`~죠?`·`~해요?` 등은 lint `tone` FAIL), 해요체면 의문문 끝 제한이 없다. 평서문은 프로필 `톤`대로 쓴다.
- **이미지 슬롯**: **절 끝(다음 소제목 직전)에 1~2장**. 문법은 정확히 `![슬롯: <장면 설명>]()`(경로 비움 — 이미지 단계가 채운다).
  - 장면 설명은 이미지 단계 내부용 한 줄로 "무엇이 보이는지"(장소·사물·인물 위치·앵글). 업로드본에는 캡션이 없으므로 캡션·키워드용으로 다듬지 않는다. 글자·간판·숫자·얼굴 클로즈업이 필요한 장면은 쓰지 않는다(⑤). 한 글 안에서 같은 장면을 반복하지 않는다.
  - 총 장수 = ④ `min_images`장 이상, 권장 = 올림(본문 글자수 ÷ ④ 이미지당 글자수 목표). 이미지 사이 본문이 ④ 이미지당 글자수 상한을 넘으면 그 절 끝에 슬롯을 하나 더 넣거나 절을 나눈다. ⑤에 현장 장면 규칙이 있으면 중간 절에 **그 현장·작업 장면 최소 1장**. 목차 절·FAQ 뒤·`## 📞` 뒤에는 슬롯을 두지 않는다.
  - 유형이 홍보면 슬롯은 업체 실사진으로 채울 장면(매장·현장·작업 모습)으로 쓴다(⑤ "홍보성 글 = 실사진만").
- **분량**: 본문 ④ `min_chars`~`max_chars`자(공백 제외, 목차 절·이미지·URL 제외), 소제목당 ③ 범위. 각 `## ` 절 본문은 `design-system.md` ③의 소제목당 글자수 **상한**(숫자는 ③에서 읽는다)을 넘지 않는다. 넘으면 절을 둘로 나누거나(소제목 `max_h2`개 이내) 줄인다.
- **톤(②) — 프로필 `톤` 행이 정한다**(행이 없으면 합니다체). 글 하나에는 한 가지 말투만 쓴다.
  - **`톤` = 합니다체**: 평서 `~입니다/~합니다/~됩니다/~있습니다`, 권유 `~하세요/~해 보세요/~기억해 두세요`, 의문문은 끝이 `~까요?`·`~나요?`·`~ㅂ니까?/~습니까?`·`~인가요?`·`~세요?`면 된다(`~죠?`·`~해요?` 등은 lint `tone` FAIL). **금지 종결**(평서문): `~해요`·`~예요`·`~에요`·`~죠`·`~볼게요`·`~드릴게요`·`~네요`·`~군요` 등 `요`·`죠`로 끝나는 문장(`~세요` 제외 — lint `tone`이 FAIL로 센다).
  - **`톤` = 해요체**(친근): 평서 `~해요/~예요·~이에요/~죠/~네요/~거든요`, 권유 `~해 보세요/~해 봐요`, 의문문은 끝 제한이 없다(`~할까요?`·`~죠?`·`~해요?` 모두 가능). **금지**: 공문체(`~하여야 한다`·`~할 것`·`~바랍니다`)와, 톤이 해요체인 글에 합니다체 종결(`~습니다`·`~입니다`·`~됩니다`)을 섞는 것 — lint `tone`은 합니다체 종결 문장 수를 **WARN**으로만 세지만(통과에 영향 없음) 섞지 않는다. 해요체여도 ⑧(지어내기 금지·출처 단독 괄호·금칙)은 그대로다. 예문은 `references/structure-templates.md` 2-1절.
  - 공통: 짧은 문장, 한 문단 2~4문장, 독자 처지로 말 걸기("~준비하시는 분이라면"), 다음 절 예고 한 문장, 어려운 용어는 첫 등장 때 괄호 풀이. ② 금지 표현("~하여야 한다", "효과 보장", "100%", "무조건" 등) 쓰지 않음.
- **강조**: `**굵게**` 1000자당 ④ 강조 빈도 범위 — 핵심 수치·결론·FAQ 질문 줄에만. `💡` 줄은 절마다 0~1개. 음영 인용 `> ` 0~1개(소제목을 인용으로 만들지 않는다).
- **출처(⑧ 6)**: 숫자·연도·기간·금액·조항 번호가 들어간 **모든** 문장 끝에 `(출처: <URL>)` **단독 괄호**를 붙인다. 조항·시행일은 문장 본문에 쓴다 — (예, 가상 조항) "<법령명> 시행규칙 제12조제1항(시행 2025-01-01)에 따라 …입니다(출처: https://…)." 한 괄호에 조항·시행일·설명과 `출처:`를 섞지 않는다(`(…제12조제1항, 시행 2025-01-01, 출처: URL)` 금지 — lint `source_format` FAIL). `[출처](URL)` 링크형도 쓰지 않는다. 괄호 안은 `출처: ` + URL 하나만, 출처가 둘이면 괄호를 두 개 쓴다. 앞에서 이미 인용한 조항을 다시 언급하는 문장("같은 규칙 제n조" 등), 도입부·FAQ 답의 요약 문장도 예외가 아니다(같은 URL을 반복해도 된다). 예외는 `business-profile.md`의 업체 연락처·주소·상품·서비스명을 그대로 쓴 부분뿐이다. URL은 `research.md`의 그 행과 같은 주소(법령은 독자용 `https://www.law.go.kr/법령/<법령명>`을 써도 되며 이때 조문 번호·시행일자를 문장에 적는다). 출처 각주 2개 이상. 출처가 없으면 그 문장을 쓰지 않거나 `[출처 필요]`. **`(출처: …)`는 초안·draft-v2.md에 반드시 남긴다** — 업로드본(final.md)에서만 `build_final.py`가 이 단독 괄호를 기계 제거한다(근거 기록은 factcheck.md에 남는다).
- **관련글 자리**: **자기 글(`work/own-posts.json`)이 2편 이상일 때만** FAQ 절 끝(`문의헤딩`이 있으면 그 헤딩 바로 앞)에 `[[관련글: <주제>]]` 2~3줄. 2편 미만이면 자리를 두지 않는다(lint `related_links`는 WARN뿐 — 링크 생략 허용). 주제는 ⑥ 기준(같은 상품·서비스 / 다음 단계 / 최근 1년)으로 짐작할 수 있게 쓴다. URL은 B'에서 실제 값으로 바꾼다 — 초안에 URL을 지어 넣지 않는다.
- **마무리(⑥)**: `마무리 블록`에 `문의헤딩`이 있으면 마지막 줄 `## 📞 <문의 헤딩 문구>: <연락처>`(문구는 프로필 `문의 헤딩 문구`, 비면 `문의 안내`. 연락처는 `business-profile.md` `연락처` 행 값 그대로). `문의헤딩`이 없으면 마지막 줄을 따로 두지 않는다. 줄글 CTA 단락·소개 이미지·장소·해시태그는 쓰지 않는다. 본문에서 업체를 말할 때는 `business-profile.md` "강점" 범위와 ⑧ 금칙 안에서만.
- **홍보글(⑨)**: 사실은 `business-profile.md` 범위 안에서만. 가격·할인 등 수치는 쓰지 않는다.
- **금칙(⑧)**: `business-profile.md` `## 금칙어`의 단어(공백 무시) 0건. 목록 밖이라도 **금칙어가 가리키는 사실을 돌려 말하거나 암시하는 문장을 쓰지 않는다**(의미 규칙). 레퍼런스·소스 블로그·자기 기존 글 문장 복붙 금지.

### B-5. 자체 점검 → lint (draft 단계)

lint 전에 아래를 실행해 다음 네 가지를 찾고, 모두 고친 뒤 다시 실행한다. (a)·(c) 0건·(b) 없음, (d)는 프로필 `톤`이 합니다체면 0건이 될 때까지 반복한다(`톤`이 해요체인 프로필의 (d)는 권장 사항이라 건수만 보고한다. B'에서는 파일명을 `draft-v2.md`로).

- (a) 숫자·`제n조`가 들어 있는데 `출처:`가 없는 문장(`business-profile.md`의 연락처·주소·상품·서비스명처럼 숫자가 이름의 일부인 표기가 유일한 숫자인 문장은 제외 — 이 표기의 사실 여부는 fact-checker가 확인)
- (b) ③ 상한을 넘는 절(목차·문의 절 제외)
- (c) 혼합 출처 괄호 — `출처:`가 들어 있는데 `(출처: URL)` 단독형이 아닌 표기(조항·시행일과 섞인 괄호, URL 없는 `출처:` 등)와 `[출처](URL)` 링크형
- (d) 톤 점검 — 프로필 `톤`이 합니다체(또는 행 없음)면 해요체 종결: `요`·`죠`로 끝나는 본문 문장. 평서문은 `세요`(와 필요·중요 같은 명사)만 예외, 의문문(`?`로 끝남)은 끝이 `~까요?`·`~나요?`·`~ㅂ니까?/~습니까?`·`~인가요?`·`~세요?`면 예외(`~죠?`·`~해요?`는 잡힌다)(lint `tone`과 같은 규칙. 소제목·표·인용·이미지·관련글 자리·목차 절 제외, 목록·이모지 줄·FAQ의 `**Q. …**`·`A. …` 줄은 포함). `톤`이 해요체면 반대로 **합니다체 종결 섞임**(평서문 끝이 `니다`, 의문문 제외)만 센다 — 권장 사항이며 lint `tone` WARN과 같은 기준이다

```bash
python3 - work/posts/<NNN-slug>/draft.md <<'PY'
import json, re, sys
t = open(sys.argv[1], encoding="utf-8").read()
t = re.sub(r"\A---\n.*?\n---\n", "", t, flags=re.S)
t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
t = re.sub(r"^## 📑 목차.*?^---[ \t]*$", "", t, flags=re.S | re.M)  # 목차 절(다음 --- 줄까지) 제외
hi = int(re.search(r"소제목당 본문 \d+~(\d+)자", open("knowledge/design-system.md", encoding="utf-8").read()).group(1))
prof = open("knowledge/business-profile.md", encoding="utf-8").read().splitlines()
casual = any(r.startswith("| 톤") and r.split("|")[2].strip() == "해요체" for r in prof)   # 프로필 톤 = 해요체면 (d)는 합니다체 종결 섞임(권장)
try:  # 자기 블로그 ID — FAQ 절 끝 관련글 링크 줄 판별용(없으면 [[관련글·안내 문구로만 판별)
    own = json.load(open("knowledge/source-blogs.json", encoding="utf-8")).get("own_blog") or {}
except (OSError, ValueError):
    own = {}
bid = re.escape(str((own.get("blogId") if isinstance(own, dict) else own) or ""))
ws = lambda s: re.sub(r"\s+", "", s)
keep = [r.split("|")[2] for r in prof if r.startswith(("| 연락처", "| 주소"))]
keep += [c for r in prof if r.startswith("| 상품·서비스") for c in r.split("|")[2].split(",")]
keep = sorted({ws(k) for k in keep if ws(k)}, key=len, reverse=True)  # 공백 무시 비교("예시 상품 2호" = "예시상품2호")
PAREN = re.compile(r"\(출처:\s*https?://\S+?\)")
def haeyo(s, q=False):  # lint tone과 같은 판정: ~죠 / ~요(세요·필요·중요 류 명사 제외), 의문문은 허용 어미 제외
    s = re.sub(r"[\W_]+$", "", s)
    if s.endswith("죠"):
        return True
    if len(s) < 2 or not s.endswith("요") or s[-2] in "세필중주개수소강":
        return False
    return not (q and s.endswith(("까요", "나요", "인가요")))  # ~ㅂ니까?는 요로 끝나지 않아 원래 안 잡힘
def formal(s, q=False):  # 프로필 톤 = 해요체: 합니다체 종결(~니다) 섞임 — 의문문 제외 (lint tone WARN과 같은 기준)
    s = re.sub(r"[\W_]+$", "", s)
    return not q and len(s) >= 2 and s.endswith("니다")
bad, mixed, tone = [], [], []
for ln in t.splitlines():
    # 빈 줄·제목·이미지·관련글 자리·표·인용·::: 줄은 건너뛴다(목록·이모지 줄·FAQ Q/A 줄은 본다)
    if not ln.strip() or re.match(r"\s*(#|!\[|\[\[|\||>|:::)", ln):
        continue
    if len(re.findall(r"출처\s*:", ln)) != len(PAREN.findall(ln)) or re.search(r"\[출처\]\(", ln):
        mixed.append(ln.strip())
    plain = re.sub(r"https?://[^\s)]+", "", PAREN.sub("", ln))  # `…입니다(출처: URL).`의 문장 끝을 살린다
    parts = re.split(r"(?<!\d)([.!?])(?!\d)", plain) + [""]  # [문장, 끝 부호, 문장, 끝 부호, …]
    tone += [parts[k].strip() for k in range(0, len(parts) - 1, 2) if (formal if casual else haeyo)(parts[k], parts[k + 1] == "?")]
    if re.match(r"\s*([-*]\s|\d+\.\s)", ln):  # 목록 줄은 (a)에서 제외
        continue
    for snt in re.split(r"(?<=[.!?])\s+", ln):
        x = ws(snt)
        for k in keep:
            x = x.replace(k, "")
        if re.search(r"(\?|까요[.!]?)\**$", x):  # 앞 문장의 수치를 되묻는 연결 질문·FAQ 질문 줄
            continue
        if re.search(r"\d", x) and "출처:" not in snt and "[출처 필요]" not in snt:
            bad.append(snt.strip())
for name, xs in (("(a) 출처 없는 숫자·조항 문장", bad), ("(c) 혼합 출처 괄호", mixed), ("(d) 톤 점검: 합니다체 종결 섞임(톤=해요체 — 권장)" if casual else "(d) 해요체 종결", tone)):
    print(f"{name}:", len(xs))
    for b in xs:
        print("  -", b)
for sec in re.split(r"\n(?=## )", t)[1:]:
    head, _, body = sec.partition("\n")
    if head.startswith(("## 📑", "## 📞")):
        continue
    # FAQ 절: 관련글 자리(B) 또는 관련글 안내·링크(B')부터 끝은 세지 않는다
    body = re.split(rf"\n(?=\s*(?:\[\[관련글|함께 읽으면|.*blog\.naver\.com/{bid}/))", "\n" + body)[0]
    n = len(ws(re.sub(r"!\[[^\]]*\]\([^)]*\)|https?://\S+", "", body)))
    if n > hi:
        print(f"(b) 절 상한 초과({hi}자): {head} = {n}자")
PY
```

```bash
python3 scripts/lint_post.py work/posts/<NNN-slug>/draft.md --stage draft --json
```

- draft 단계는 `frontmatter`·`title_keyword`·`tags_count`·`related_links`·`image_paths`·`h1_once`·`seo_*` 4종과 upload 전용 5종(`sources_stripped`·`captions_empty`·`cover_file`·`closing_block`·`h2_spacing`)을 SKIP한다. 보는 항목: `forbidden`, `chars`, `h2_count`, `images`, `sources`, `placeholder_sources`, `tone`(`톤`이 해요체면 합니다체 종결 문장 수를 WARN으로만 낸다), `source_format`(`variation`·`title_region`은 frontmatter가 없으니 SKIP. `title_region`은 고객 지역이 없으면 frontmatter가 있어도 SKIP — 사유 `고객 지역 없음`). 세는 법: `chars`는 `## 📑 목차` 절·해시태그 줄·`ㅤ` 제외, `h2_count`는 `## 📑 목차`·`## 📞 문의` 제외, `images`는 표지·업체소개 제외.
- FAIL 항목을 고치고 다시 실행한다(재실행 최대 2회). `placeholder_sources` FAIL은 일부러 남긴 `[출처 필요]` 때문이면 그대로 두고 건수를 보고한다. 그 밖의 FAIL이 2회 뒤에도 남으면 남은 항목과 이유를 보고한다.
- **판정을 선언하지 않는다**: "lint 통과했으니 완성" 같은 말을 쓰지 않는다. 마지막 실행의 `pass` 값과 FAIL id·값을 그대로 옮기고, 위 자체 점검의 (a) 출처 없는 숫자·조항 문장·(c) 혼합 출처 괄호·(d) 톤 점검 건수(합니다체 프로필은 0이어야 함, 해요체 프로필은 건수만 보고)와 (b) 절 상한 초과 건수도 함께 보고한다. 품질 판정은 fact-checker와 담당자의 몫이다.

### B-6. 반환(메인에게, 10줄 이내)

출력 경로(`research.md`·`draft.md`), 제목, keyword, 변주 선택(structure·intro·region·title_region·type — 고객 지역이 없으면 region·title_region은 `-`), lint 마지막 결과(`pass` 값 + FAIL id·값, stats의 chars·h2_count·images·sources·bold_runs·quotes·tone_hits), 자체 점검 (a)·(c)·(d) 건수와 (b) 절 상한 초과 건수, `[출처 필요]` 건수, `학습 규칙 적용: L-001, L-004`(B-1에서 적용한 `## 적용 중` id — 없거나 파일이 없으면 `학습 규칙 적용: 없음`), 그리고 메인/담당자가 답해야 하는 것이 있으면 `## 질문` 절.

---

## 모드 B' — 수정 + SEO

발주(재개) 메시지가 주는 것: `mode: B'`, factcheck 파일 경로(`P/factcheck.md` 또는 r2면 `P/factcheck-r2.md`), blog-naver-seo `SKILL.md` 절대경로, 그리고 경우에 따라 반영할 게이트 2 피드백(`gates.md ## 초안피드백`) 또는 메인 lint 결과(`P/lint.json`).

### B'-0. 시작 파일

- `P/draft-v2.md`가 **이미 있으면**(메인이 FAIL+출처필요 0건이라 `draft.md`를 복사해 둔 경우, 또는 재개) 그 파일에서 시작한다.
- 없으면 `draft.md` 내용을 그대로 `draft-v2.md`로 만든 뒤(Write) 그 파일을 고친다. `draft.md`는 건드리지 않는다.

### B'-1. 팩트체크 반영

factcheck 파일에서 아래만 반영한다(그 밖의 사실 문장은 건드리지 않는다).

- `## B'에서 반영할 것`의 항목 전부:
  - **FAIL** → 표의 "수정 제안" 문장대로 바꾼다. 출처 URL도 판정 근거의 URL로 맞추고, 바뀐 URL은 직접 다시 열어 문구를 확인한 뒤 `research.md` `## B' 추가 출처`에 행을 추가한다.
  - **출처필요** → 출처를 새로 찾아(B-2와 같은 방법, 실제로 열어 확인) 문장을 고치고 본문 각주 `(출처: <URL>)` 단독 괄호를 달거나, 못 찾으면 문장을 삭제하거나, fact-checker가 제안한 "확인 필요" 문구(예: "<기관>에서 최신 내용 확인")로 바꾼다(수치·단정 없이). 새 출처는 `research.md` 끝 `## B' 추가 출처` 절에 B-2와 같은 표 형식으로 덧붙인다(기존 행은 고치지 않는다 — r2 검토 때 fact-checker가 다시 연다). `[출처 필요]` 표시는 B'에서 0건이 되어야 한다.
  - 항목이 `없음`이면 이 단계는 건너뛴다.
- `## 시점 표기 권고`의 항목: 해당 문장 끝에 "(YYYY년 M월 <기관> 기준)"처럼 기준 시점을 붙인다.
- `## 질문`의 항목은 반영하지 않는다(메인이 담당자에게 묻는다). 메인이 답을 발주 메시지로 주면 그 답대로 반영한다.
- **PASS 문장**: 사실 내용(수치·일정·조항·출처)은 그대로 두고 조사·어순·문체만 손댈 수 있다.
- 새로 찾은 출처로 사실 문장을 바꾸거나 더했다면, 그 문장 id·내용을 리포트의 "사실 문장 변경" 줄에 적는다(메인이 C r2 재발주를 판단한다).

### B'-2. SEO — blog-naver-seo 스킬 절차 적용

발주 메시지가 준 blog-naver-seo `SKILL.md`를 읽고 그 **1~8단계를 `draft-v2.md`에 그대로** 수행한다(keyword 확정 → 제목 A/B안(고객 지역이 있으면 둘 다 title_region 포함) → 소제목 키워드 → 본문 키워드 3~8회 → 이미지 슬롯 확인(캡션 없음) → 태그 5~10개 → `--stage final` lint로 SEO 항목만 확인 → `P/seo.md` 셀프 체크표). 이 스킬과 다른 점·보충:

- keyword: `topic.md`의 핵심 키워드. 바꾸지 않는다.
- 제목 B안도 keyword와, 고객 지역이 있으면 제목 지역(`research.md ## 변주 선택`의 `title_region`)을 그대로 포함하게 쓴다(게이트 2에서 담당자가 B안을 고르면 그대로 title이 되므로 lint `title_keyword`·`title_region`을 통과해야 한다 — 고객 지역이 없으면 `title_region`은 SKIP이고 지역명을 넣지 않는다). 지역명은 그 1개만.
- 소제목을 고치면 `## 📑 목차` 항목도 같은 텍스트·순서로 맞춘다. 키캡 번호(`## 1️⃣ `)는 유지한다.
- 이미지 슬롯: `![슬롯: …]()` 문법과 빈 경로는 그대로 둔다. 업로드본에는 캡션이 없으므로(`build_final.py`가 alt를 비운다) 장면 설명을 캡션용으로 다듬거나 keyword를 넣지 않는다 — 설명은 이미지 단계 내부용이다.
- SEO 스킬 7단계의 `--stage final` 실행은 draft-v2.md의 SEO 항목 확인용이다(`final` 단계 이름은 그대로 쓴다 — 업로드본 final.md 검사는 메인이 Step 4에서 `--stage upload`로 한다). `image_paths`·`related_links` FAIL은 정상(슬롯·자리표시 때문)이며 `seo.md`에 "후속 단계 몫"으로 적는다. B'의 최종 lint는 아래 B'-5의 `--stage draft`다.

### B'-3. `[[관련글: …]]` → 실제 링크

**자기 글이 2편 미만이면**(`work/own-posts.json` 길이 기준 — 메인이 발주 메시지에 `관련글: 자기 글 <N>편`을 준다) 이 절은 건너뛴다: 남아 있는 `[[관련글: …]]` 줄과 "함께 읽으면 좋은 글" 안내 줄을 모두 지우고 링크를 걸지 않는다(질문도 하지 않는다 — lint `related_links`는 WARN뿐). 2편 이상이면 아래대로 한다.

`work/own-posts.json`(배열, 항목 `{blogId, title, category, date, logNo, link}`)에서 2~3개를 골라 각 `[[관련글: …]]` 줄을 바꾼다.

- 고르는 기준(⑥ 1): (a) 같은 상품·서비스 주제 (b) 다음 단계 주제(예: 알아보기 → 준비 → 이용) (c) `date`가 최근 1년 이내 우선. 같은 글을 두 번 걸지 않는다.
- **제외**: 제목에 `business-profile.md` `## 금칙어` 단어(공백 무시)가 있는 글 — lint `forbidden`은 링크 텍스트도 검사한다.
- 형식: `- [<그 글의 실제 제목>](https://blog.naver.com/<blogId>/<logNo>)`(`<blogId>`·`<logNo>`는 그 JSON 항목의 값). 제목은 JSON의 `title` 그대로 쓰되 링크 텍스트를 깨는 `[`·`]`는 `(`·`)`로 바꾸고 앞뒤 장식 이모지만 뗄 수 있다. URL은 JSON의 `logNo`로 만든 실제 값만 — 지어낸 URL 금지.
- 관련글 묶음 앞에 한 줄 안내(예: "함께 읽으면 좋은 글")를 둘 수 있다. 위치는 FAQ 절 끝, `마무리 블록`에 `문의헤딩`이 있으면 `## 📞 <문의 헤딩 문구>: <연락처>` 헤딩 바로 앞(그 헤딩이 마지막 줄로 남아야 한다 — 없으면 관련글이 마지막이다).
- 자기 글은 2편 이상인데 맞는 글이 2개 미만이면 찾은 만큼만 걸고 남은 `[[`는 지운 뒤 리포트 `## 질문`에 적는다(`[[`가 남으면 업로드가 막힌다).

### B'-4. frontmatter

B'-2(SEO 1·2·6단계)에서 만든 `title`·`keyword`·`tags`와 B안 주석을 포함해, `draft-v2.md` 맨 위 frontmatter를 아래 형식으로 완성한다(첫 줄 `---`, 키 순서·형식 고정, 닫는 `---` 바로 다음 줄이 B안 주석, 그다음 `# 제목`):

```markdown
---
title: <제목 A안>
keyword: <핵심 키워드>
category: <gates.md ## 선택의 카테고리>
tags: [<키워드>, <지역1 포함 태그>, <지역2 포함 태그>, <상품·서비스명>, <업종 키워드>, …]
variation: {type: <정보|홍보>, structure: <절차형|비교형|체크리스트형|Q&A형>, intro: <질문|상황|통계|오해 바로잡기>, region: [<지역1>, <지역2> | 고객 지역이 없으면 -], title_region: <제목 지역 | 고객 지역이 없으면 ->}
---
<!-- 제목 B안: <제목 B안> -->
# <제목 A안>
```

- `variation.type`은 **`gates.md ## 선택`의 유형** 그대로. 나머지 네 값(structure·intro·region·title_region)은 `research.md`의 `## 변주 선택` 그대로. 고객 지역이 있으면 `title_region`은 `title`(A안)에 들어 있는 지역명과 같아야 한다(lint `title_region`). 고객 지역이 없으면 `region: [-]`, `title_region: -`로 쓴다(lint `title_region`은 SKIP). `cta` 키는 없다.
- `tags`는 업로드본 끝 해시태그 줄(`**#태그 #태그 …**`)의 원천이다(`build_final.py`가 공백을 지워 만든다). 태그는 공백 없는 형태(예: `자전거정기점검`)를 권장한다.
- `category`는 `gates.md ## 선택`의 `카테고리:` 값을 그대로 쓴다(메인이 `own_blog.categories.info` 또는 담당자가 고른 카테고리로 적어 둔다).
- 이미지 슬롯·`(출처: URL)` 괄호·(`문의헤딩`이 있을 때의) `## 📞 <문의 헤딩 문구>: <연락처>` 마지막 줄은 그대로 둔다. 메인이 Step 4에서 `build_final.py`로 `final.md`를 만들며 슬롯을 절대경로(캡션 없음)로 바꾸고, 출처 괄호를 지우고, 소제목 앞 여백과 프로필 `마무리 블록`대로의 마무리 고정 블록(소개 이미지·장소 카드·해시태그)을 붙인다. draft-v2.md는 출처 포함본으로 남는다.

### B'-5. 저장·lint·반환

```bash
python3 scripts/lint_post.py work/posts/<NNN-slug>/draft-v2.md --stage draft --json
```

- lint 전에 B-5의 자체 점검(파일명 `draft-v2.md`)을 먼저 돌려 출처 없는 숫자·조항 문장 0건·절 상한 초과 없음으로 만들고 건수를 보고한다.
- 업로드본 검사(이미지 경로·출처 제거·캡션·마무리 블록·여백 등)는 메인이 `build_final.py` 뒤 `final.md`에 `--stage upload`로 돌린다. 여기서는 draft 단계로 `forbidden`·`chars`·`h2_count`·`images`·`sources`·`placeholder_sources`·`tone`·`source_format`·`title_region`·`variation`(frontmatter가 있으니 `variation`은 PASS여야 하고 `title_region`은 고객 지역이 있으면 PASS, 없으면 SKIP)을 본다. FAIL은 고치고 재실행(최대 2회). `placeholder_sources`는 B'에서 0이어야 한다.
- 판정 선언 금지 — 결과만 옮긴다.
- 반환(메인에게, 10줄 이내): `draft-v2.md`·`seo.md` 경로, 제목 A/B안, 반영한 factcheck 항목 id 목록, **사실 문장 변경**(B'-1에서 factcheck 항목 밖으로 바뀐 사실 문장 — 없으면 "없음"), 관련글 2~3개(제목·logNo), lint 마지막 결과(`pass` + FAIL id·값), `학습 규칙 적용: L-…`(B'-2 SEO 스킬 단계에서 적용한 id(`seo.md` 머리의 `학습 규칙:`) 포함, 없으면 "없음"), `## 질문`(있으면).

### 재개되는 경우 (같은 B' 절차, 범위만 다름)

- **메인 lint FAIL(Step 2)**: 발주 메시지의 `P/lint.json` FAIL 항목만 `draft-v2.md`에서 고치고 B'-5를 다시 한다.
- **담당자 직접 수정 보존**(모든 B' 재개 공통): 재개 메시지에 `직접 수정: 있음`이 있거나 `gates.md` 마지막 `## 초안피드백`의 `- 직접 수정:`이 `있음…`이면, 지금의 `draft-v2.md`는 **담당자가 직접 고친 판**이다. 그 판을 기준으로 이번 범위(피드백 요청·lint FAIL 항목·r2 반영)만 고치고, 담당자가 바꾼 문장·제목·소제목·삭제는 **되돌리지 않는다**(`draft.md`나 이전 판으로 다시 쓰지 않는다). 담당자 수정이 잠긴 규칙이나 lint를 어기면 고치지 말고 그 자리와 이유를 반환 `## 질문`에 적는다 — lint FAIL 재개로 그 항목을 고치라고 받은 경우만 최소한으로 고친다.
- **게이트 2 피드백**: `gates.md ## 초안피드백`대로 고친다. B-1의 학습 규칙 우선순위는 그대로다 — 이번 피드백이 `## 적용 중` 규칙과 어긋나면 이번 글은 피드백대로 고치고(담당자의 최신 지시) `## 질문`에 `L-<id>와 어긋나는 피드백 — 이번 글은 피드백대로` 한 줄, 잠긴 규칙과 어긋나면 잠긴 규칙대로 쓰고 `## 질문`에 적는다. 담당자가 제목 B안을 고르면 frontmatter `title`·`# 제목`을 B로 바꾸고 주석을 `<!-- 제목 A안(미채택): … -->`로 바꾼다. 고객 지역이 있고 담당자가 직접 쓴 제목에 제목 지역이 없으면(메인이 "제목 지역 보완"을 범위로 주면) 그 제목에 `title_region` 지역명 1개를 자연스럽게 넣는다. 사실 문장이 바뀌었으면 "사실 문장 변경"에 적는다(메인이 C r2를 발주한다). 그 뒤 `factcheck-r2.md`가 오면 B'-1부터 그 파일로 다시 한다.

## 하지 말 것

- 출처 없는 수치·일정·조항, 열지 않은 URL, 지어낸 관련글 URL, 조항·시행일과 섞인 출처 괄호, `[출처](URL)` 링크형, 초안·draft-v2.md에서 `(출처: …)` 지우기.
- 프로필 `톤`이 금지한 종결(합니다체 프로필의 해요체 종결 ②, 해요체 프로필의 공문체·합니다체 섞기), 줄글 CTA 단락, 업체소개 이미지·장소 카드·해시태그·`ㅤ` 여백 줄을 초안에 쓰기(`마무리 블록` 항목은 빌더 몫).
- 금칙어·금칙어가 가리키는 사실의 암시(⑧), ② 금지 표현, 복붙.
- 사실 판정·"완성/통과" 선언(자기 승인 금지), 사용자에게 직접 묻기(`## 질문`으로 반환), 서브에이전트 발주.
- 출력 파일 외 파일 수정, `gates.md` 쓰기, B'에서 `draft.md` 수정, 이미지 생성·경로 치환·업로드.
