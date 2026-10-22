# naver-blog-autopilot 1.1.0 — 온보딩·프로필 v1.1·이미지 소스 계약 (SPEC)

작성 2026-10-21. 이 문서는 1.1.0 작업의 **레인 간 계약**이다. 행 이름·열거값·exit 코드·출력 문구·함수 이름은 여기 적힌 철자 그대로 쓴다. 새 이름을 만들지 않는다. 경로는 플러그인 루트(`plugins/naver-blog-autopilot/`) 기준이다.

용어: 「프로필」 = 작업 폴더 `knowledge/business-profile.md`. 「kdir」 = 그 `knowledge/` 폴더 경로.

---

## 1. 프로필 스키마 v1.1 (`scaffold/knowledge/business-profile.md`)

표 `| 항목 | 내용 |`의 행 이름. ★ = 1.1 신규. 값이 `[치환 변수]` 그대로면 빈 값이다(1.0.0과 같음 — `lint_post.profile_row`).

| 행 | 필수 | 값 | 비고 |
|---|---|---|---|
| ★블로그 유형 | 필수 | `업체` / `전문가` / `개인` / `브랜드` | 온보딩 기본값 선택에만 쓰임. 스크립트는 열거값 검사만 |
| 업체명 | 필수 | 문자열 | 개인이면 블로그 이름·필명 |
| 연락처 | 조건 | 전화 또는 이메일 | `마무리 블록`에 `문의헤딩`이 있으면 필수. 비우면 표지 전화 줄 생략 |
| 주소 | 선택 | | |
| 상품·서비스 | 필수 | 쉼표 목록 | 개인은 주요 주제 영역 |
| 지원 형태 | 선택 | | |
| 제공 방식 | 선택 | | |
| 고객 지역 | 선택 | 쉼표 목록 | **비우면** 지역 키워드 질문·`title_region` 로테이션·lint `title_region` 전부 끔 |
| 강점 | 선택 | | |
| 장소 검색어 | 조건 | | `마무리 블록`에 `장소카드`가 있으면 필수 |
| ★톤 | 필수 | `합니다체` / `해요체` | lint `tone` 동작 결정 |
| ★마무리 블록 | 필수 | `문의헤딩`·`소개이미지`·`장소카드`·`해시태그` 중 쉼표 목록 | 적힌 순서와 무관하게 **이 고정 순서**로 해석한다. `해시태그`는 반드시 포함 |
| ★문의 헤딩 문구 | 선택 | 기본 `문의 안내` | 마지막 헤딩 = `## 📞 <문구>: <연락처>` |
| ★주제 키워드 | 선택 | 쉼표 목록 3~8개 | 연관검색어 확장 씨앗. 확장 결과는 `knowledge/topic-seeds.md` |
| ★이미지 소스 | 필수 | `ai`·`stock`·`photo` 중 쉼표 목록(1개 이상) | `ai` → `.env IMAGE_PROVIDER`+키, `stock` → `.env PEXELS_API_KEY`, `photo` → `photos/` |
| ★이미지 기본 장면 | 선택 | 영문 장면구 | gen_image `PROMPT_PREFIX`의 장면 부분·Pexels 검색어 접두. 기본 `Korean everyday scene` |
| 배지 문구 | 선택 | | 1.0.0과 같음 |
| 브랜드 색 | 선택 | `#RRGGBB` | 1.0.0과 같음 |
| 업체 유형어 | **선택**(1.0.0은 필수) | 쉼표 목록 | 비우면 빈 목록 |
| 업종 일반어 | **선택**(1.0.0은 필수) | 쉼표 목록 | 비우면 빈 목록 |
| 제목 정규화 · 홍보 표지어 · 공지 표지어 | 선택 | | 1.0.0과 같음 |
| `## 금칙어` 절 | 필수 | 백틱 목록 또는 `- 없음` | 1.0.0과 같음(`load_forbidden`) |

### 1-1 유형별 온보딩 기본값 (온보딩 스킬만 사용)

| 유형 | 톤 기본 | 마무리 블록 기본 | 이미지 소스 기본 | 묻지 않는 항목 |
|---|---|---|---|---|
| 업체 | 합니다체 | 문의헤딩, 소개이미지, 장소카드, 해시태그 | ai, photo | — |
| 전문가 | 합니다체 | 문의헤딩, 해시태그 | ai | 장소 검색어 · 소개 이미지 |
| 개인 | 해요체 | 해시태그 | ai, stock | 연락처 · 장소 · 소개 이미지 · 배지 |
| 브랜드 | 합니다체 | 문의헤딩, 소개이미지, 해시태그 | ai | 장소 검색어 |

### 1-2 `check_profile.py` 출력 계약 (한 줄, exit 0 / 2)

- `profile: OK` (0)
- `profile: NOFILE` (2) — kdir 또는 프로필 파일 없음
- `profile: MISSING <행>,<행>,…` (2) — 아래 필수·조건 행 중 빈 것. 순서: 블로그 유형, 업체명, 상품·서비스, 톤, 마무리 블록, 이미지 소스, 연락처(조건), 장소 검색어(조건), 금칙어
- `profile: INVALID <행>=<값>` (2) — MISSING이 없을 때만 검사. 열거값 위반(`블로그 유형`·`톤`·`마무리 블록` 항목·`이미지 소스` 항목), `마무리 블록`에 `해시태그` 없음(`INVALID 마무리 블록=해시태그 없음`). 여러 개면 첫 번째만
- 조건: `연락처`는 `마무리 블록`에 `문의헤딩`이 있을 때 필수, `장소 검색어`는 `장소카드`가 있을 때 필수. 조건 판정은 `마무리 블록` 값이 유효할 때만(아니면 INVALID가 먼저)
- 1.0.0 프로필(새 행 없음)에 대한 기대 출력: `profile: MISSING 블로그 유형,톤,마무리 블록,이미지 소스`

### 1-3 `lint_post.py` 새 헬퍼 (다른 스크립트가 import)

```python
CLOSING_ORDER = ("문의헤딩", "소개이미지", "장소카드", "해시태그")
def load_closing_blocks(kdir) -> list[str]   # 프로필 `마무리 블록` → CLOSING_ORDER 순서로 정렬된 목록. 빈 값이면 ValueError(missing_row). 모르는 항목이나 해시태그 없음이면 ValueError("마무리 블록 값이 올바르지 않습니다: …")
def load_tone(kdir) -> str                   # 'formal'(합니다체) | 'casual'(해요체). 빈 값 ValueError(missing_row), 그 밖 값 ValueError
def load_image_sources(kdir) -> list[str]    # 프로필 `이미지 소스` → ['ai','stock','photo'] 부분집합(순서 유지). 빈 값 ValueError
def own_posts_count(path) -> int | None      # work/own-posts.json의 글 수. 파일 없음·파싱 실패 None
```

### 1-4 `knowledge/topic-seeds.md` (★신규, 온보딩이 생성 · 주제 리서치가 읽음)

```markdown
# 주제 씨앗

## 씨앗 키워드
- 자전거 수리
- 자전거 점검

## 연관 검색어
| 키워드 | 씨앗 | 확인일 |
|---|---|---|
| 자전거 수리점 | 자전거 수리 | 2026-10-21 |

## 공지 소스
| 기관 | URL | 메모 |
|---|---|---|
| [기관명] | [https://…] | [무엇을 보는지] |
```
scaffold 템플릿은 세 절의 머리와 빈 표(자리표시 행 1개)만 둔다. 없어도 주제 리서치는 돈다.

### 1-5 `.env` 추가

`PEXELS_API_KEY=`(선택 — `이미지 소스`에 `stock`이 있을 때 필수). `.env.example` 주석: 발급 https://www.pexels.com/api/ · 무료 · Pexels 라이선스는 출처 표기 의무 없음(표기는 권장) · 채팅에 붙여넣지 않기.

---

## 2. 스크립트 동작 (프로필 구동)

exit 코드·출력 문구 형식은 1.0.0과 호환한다(README 「문제 해결」 표가 그대로 맞아야 한다). 새 스크립트는 표준 라이브러리만 쓴다. 테스트는 HTTP를 mock한다.

### 2-1 기존 스크립트

| 스크립트 | 변경 |
|---|---|
| `lint_post.py` | ① `tone`: `load_tone`이 `formal`이면 현행 규칙(FAIL) / `casual`이면 **WARN만** — 항목 `tone`의 상태 `WARN`, 값 = 합니다체 종결(`~습니다`·`~입니다`·`~됩니다`) 문장 수, pass에 영향 없음, 의문문 규칙 미적용. 프로필에 `톤`이 없으면(1.0.0 프로필) 현행 규칙 유지(formal) ② `closing_block`(upload): `load_closing_blocks` 순서대로 **포함된 항목만** 검사. `문의헤딩` 없으면 마지막 h2 제약 없음. 항목 라벨: 문의 헤딩 / 소개 이미지 / 장소 카드 / 해시태그 ③ `title_region`: `profile_list(kdir,'고객 지역')`이 비면 `SKIP`(사유 `고객 지역 없음`) — FAIL 아님 ④ ★`--own-posts PATH`(기본 `<kdir>/../work/own-posts.json`): `related_links`는 `own_posts_count < 2`이면 `WARN`(값 = 링크 수, 기준 `자기 글 2편 미만 — 링크 생략 허용`), pass 영향 없음. 2편 이상이면 현행 FAIL 규칙 ⑤ ★`CONTACT_H`를 `## 📞`로 넓힘(`문의 헤딩 문구`를 바꿔도 h2_count 제외·문의 헤딩 판정이 맞게) · `h2_count`·`EXCLUDED_IMAGES` 불변 |
| `check_profile.py` | §1-2 |
| `dedupe_check.py` | `고객 지역`·`업체 유형어`·`업종 일반어` 빈 값 허용 → 빈 목록(exit 2 아님). `제목 정규화`·표지어 선택은 현행 |
| `build_final.py` | 마무리 블록을 `load_closing_blocks`로 조립: [`문의헤딩` → 마지막 h2가 `## 📞` 접두인지 검사(아니면 현행 오류)] → [`소개이미지` → `![](<photos>/business-intro.png)`, 파일 없으면 현행 오류] → [`장소카드` → `:::place <장소 검색어>:::`, 비면 `missing_row("장소 검색어")`] → 빈 줄 → `**#태그**`(항상). `문의헤딩`이 없으면 마지막 h2 검사를 하지 않는다. `ㅤ` 여백 규칙 불변 |
| `naver_upload.sh` | 이중 검사의 `:::place` 요구와 장소 카드 경고(`장소 카드 확인 필요`)를 `장소카드`가 있을 때만, `business-intro.png` 존재 검사를 `소개이미지`가 있을 때만. 프로필 읽기: `python3 -c 'import sys; sys.path.insert(0,"scripts"); import lint_post; print(",".join(lint_post.load_closing_blocks("knowledge")))'` 한 줄(실패하면 exit 2 + 사유). `**#` 해시태그 줄 요구는 항상 |
| (공통) | 문의 헤딩 판정 접두 = `## 📞`(lint `CONTACT_H`·build_final `CLOSING_H2`·naver_upload.sh 동일). 결정 2026-10-21 |
| `make_cover.py` | `--phone`과 프로필 `연락처`가 둘 다 비면 exit 2 대신 **전화 줄을 그리지 않음**(dry-run 출력에 `전화: 없음`). `--brand`/`업체명`은 여전히 필수(exit 2) |
| `gen_image.py` | ① `PROMPT_PREFIX`의 장면구를 프로필 `이미지 기본 장면`에서 읽음(없으면 `Korean everyday scene`). 금지구(`no text, no letters, no watermark, no close-up faces`)와 `photorealistic`은 고정. 함수 `build_prompt(scene, base_scene=None)` — 테스트·`prompt-patterns.md` 동기 유지 ② `KINDS`에 `stock` 추가: photo처럼 **건너뜀**(경고 없음). `select_ai_rows`는 stock을 ai로 오인하지 않음 ③ `find_env`의 `ENV_NAMES`에 `PEXELS_API_KEY` 추가(제공자 판정에는 영향 없음) |
| `check_image_key.py` | ★`--stock`: `PEXELS_API_KEY`를 `GET https://api.pexels.com/v1/search?query=test&per_page=1`(헤더 `Authorization: <키>`)로 확인. exit 0 `스톡 키 확인: pexels 사용 가능 (<source>)` / 2 키 없음(`스톡 키 없음 — .env에 PEXELS_API_KEY=…`) / 3 거부(401·403) / 5 네트워크. `--stock` 없이 호출하면 1.0.0 동작 그대로 |

### 2-2 새 스크립트

**`verify_blogs.py <blogId 또는 URL …> [--json] [--days 90]`**
- 입력 정규화: `blogId` / `https://blog.naver.com/<id>` / `https://blog.naver.com/<id>/<logNo>` / `https://m.blog.naver.com/<id>/<logNo>` / `https://blog.naver.com/PostView.naver?blogId=<id>&logNo=<n>` → `(id, logNo|None)`. ID 형식 `[A-Za-z0-9_-]+` 아니면 그 항목만 `형식 오류`
- 블로그마다 `fetch_posts.fetch_rss(id)`(현재 `die()`로 종료하는 함수라, verify_blogs는 `fetch_posts.http_get`과 같은 파싱을 **자체 함수** `rss_summary(id)`로 감싸 예외를 행 단위로 받는다 — fetch_posts.py는 수정하지 않음)
- 행: `ID | 응답 | 최근 N일 글 수 | 월 추정 | 카테고리 상위 3 | 최근 제목 3`. 응답 = `OK` / `없음`(채널 없음·404) / `비공개`(RSS 비어 있음) / `네트워크`
- `--json`: `[{"blogId","logNo","status","recent_count","per_month","categories":[…],"recent":[{"title","date","logNo","category"}],"error"}]`
- exit 0(한 개 이상 OK) / 2(인자 없음·전부 형식 오류) / 5(전부 네트워크)
- UA 헤더는 `fetch_posts.UA`, 타임아웃 10초

**`keyword_expand.py <씨앗 …> [--depth 1|2] [--json] [--max 60]`**
- 호출: `https://ac.search.naver.com/nx/ac?q=<URL인코딩 씨앗>&con=1&frm=nv&ans=2&r_format=json&r_enc=UTF-8&r_unicode=0&t_koreng=1&run=2&rev=4&q_enc=UTF-8&st=100` · 헤더 `User-Agent: Mozilla/5.0` 필수 · 타임아웃 5초 · 씨앗당 1회
- 결과: `items[0]`의 각 원소 `[키워드, 플래그]` 중 키워드. depth 2면 1차 결과 상위 5개(씨앗 자신 제외)를 다시 조회. 중복 제거(공백 정규화), 씨앗 자체 제외, `--max`에서 자름
- 표: `| 키워드 | 씨앗 |` · `--json`: `[{"keyword","seed","depth"}]`
- exit 0(결과 0개여도 0 + 빈 표 + stderr 안내) / 2(인자 없음) / 5(모든 요청 네트워크 실패). 일부 실패는 stderr 경고 후 계속
- 응답 샘플: 부록 B

**`fetch_stock.py <글 폴더> [--only NN[,NN]] [--dry-run] [--env PATH]`**
- 대상: `<글 폴더>/images/image-plan.md`에서 `유형`이 `stock`인 행. 검색어 = 그 행의 **프롬프트 칸**(영문 2~4단어, 이미지 디렉터가 적음). 비어 있으면 그 행 `검수`에 `검색어 없음`을 적고 건너뜀
- 키: `gen_image.find_env(plan_path, env_override)`와 같은 탐색으로 `PEXELS_API_KEY`. 없으면 exit 2(`스톡 키 없음 — .env에 PEXELS_API_KEY=…`)
- 호출: `GET https://api.pexels.com/v1/search?query=<검색어>&orientation=landscape&per_page=8&locale=ko-KR` · 헤더 `Authorization: <키>`
- 선택: `photos[]` 중 `width >= 1600`인 첫 사진의 `src.large2x`(없으면 `src.large`). 결과 0 → 행 `파일`을 `보류`, `검수`를 `검색 결과 없음`으로 두고 다음 행
- 저장: `images/NN-<slug>.jpg`(slug = `gen_image.slug_for(purpose)`), 행의 `파일` 칸 갱신(`gen_image.rewrite_plan` 사용). 출처 기록: 표에 `출처` 열이 있으면 그 칸에, 없으면 `검수` 칸에 `출처: Pexels/<photographer> <photo.url>`
- `--dry-run`: 네트워크 접속 없이 행별 `슬롯 · 검색어 · 예상 파일명` 출력
- 시작 줄: `스톡: pexels · 키: <source 경로 또는 환경변수>`(키 값 출력 금지, `gen_image.redact` 사용). 끝 줄: `저장 n장 · 보류 n장`
- exit 0(처리 완료, 보류 포함) / 2(키 없음·image-plan 없음·표 파싱 실패) / 3(401·403) / 6(429 — 재시도 없이 중단) / 5(네트워크·5xx)

### 2-3 image-plan `stock` 행 (이미지 디렉터가 쓰는 형식)

표 머리는 1.0.0과 같고 맨 끝에 `출처` 열을 **추가**한다(없어도 스크립트는 돈다 — §2-2 fetch_stock 참고):

```
| 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 검색어(stock) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수 | 출처 |
|---|---|---|---|---|---|---|---|---|
| 03 | ## 3️⃣ 체인 청소 | 현장 | stock | bicycle chain cleaning closeup | 체인을 닦는 장면 | | | |
```
`gen_image.parse_plan`은 열을 **접두 일치**로 찾으므로(`프롬프트`로 시작) 머리글 변경은 호환된다.

### 2-4 검수 뒤 결정 (2026-10-21, L6)

- `related_links`: `own_posts_count`가 None(파일 없음·파싱 실패)이어도 **WARN**(기준 `own-posts.json 없음 — 글 목록 갱신 전`). 파이프라인은 Step 0에서 항상 파일을 만들므로 실제 경로에서는 글 수 기준이 적용된다.
- `마무리 블록` 행이 없거나 빈 값이면 lint(upload 단계)·build_final·naver_upload **모두 멈춘다** — 코드는 각 스크립트의 기존 체계 그대로(lint 2 · build_final 1=변환 불가 · naver_upload 10=lint 실패, 둘째 재검수 2026-10-21 정정). 1.0.0 프로필은 Step 0 `check_profile`에서 먼저 온보딩 안내로 멈춘다. lint draft·final 단계는 이 행을 읽지 않는다.
- `diff_published.py`: `마무리 블록`에 `문의헤딩`이 없는 프로필(개인 등)에서는 `closing_block_kept`를 `해당 없음`으로 둔다(오탐 방지). 요약 라벨은 `마무리 블록(📞→해시태그)`.
- `naver_upload.sh`는 lint를 먼저 돌리므로 `마무리 블록` 값 오류가 exit 10으로 나올 수 있다 — 1.0.0과 같은 동작이라 허용.
- `diff_published.py`의 문의 헤딩 접두도 `📞`로 넓힌다.
- `gen_image.py` 기본 장면구 `Korean everyday scene`은 의도된 변경(1.0.0 `Korean local business scene`).

---

### 2-5 1.1.1 패치 (2026-10-22, 리허설 R1-2·디자인 시스템 메모)

- `related_links`: frontmatter `related: none`(선택 키 — 값은 따옴표·대소문자·앞뒤 공백 무시, 그 밖의 값은 없음과 같다)이 있고 `[[` 0건이면 자기 글이 2편 이상이어도 **WARN**(기준 `related: none — 주제에 맞는 자기 글 2편 미만(writer 판단)`, detail `자기 글 N편, 관련글 n개`), pass 영향 없음. 우선순위: 링크 ≥2 → PASS / `[[` 0건이고 (자기 글 2편 미만 · own-posts 없음 · `related: none`) → WARN(기준 문구는 이 순서로 고름) / 그 밖 FAIL. `[[`가 남으면 표시가 있어도 FAIL. 자기 글 2편 이상인데 링크가 모자라고 표시가 없으면 FAIL detail이 `related: none`을 안내한다. 쓰는 쪽: blog-draft-writer B'-3(주제에 맞는 글 2편 미만 → 관련글 전부 삭제, 담당자가 고른 글은 유지 — 관련글이 2개 미만이면 B'-4 frontmatter `variation:` 다음 줄 `related: none`). `build_final.py`는 frontmatter를 그대로 옮기므로 upload 단계에서도 같은 판정이다. exit 코드 변화 없음.
- 디자인 시스템 템플릿: `skills/blog-design-system/references/design-system-template.md` 삭제. 정본 템플릿 = `scaffold/knowledge/design-system.md`(치환 변수 `[…]`), 채우기 안내 = `skills/blog-design-system/references/fill-guide.md`. 계약 테스트 `tests/test_design_system_skill.py`가 치환 변수 ↔ 안내 대응, lint 블록 = `DEFAULTS`, `소제목당 본문 N~M자` 문구(blog-draft-writer 자체 점검이 읽음)를 지킨다.

## 3. 온보딩 플로우 (`skills/blog-onboarding/SKILL.md`)

plan 3-3 표 O0~O13과 같다(여기 재수록하지 않음 — 1.1.0 작업 plan §3-3(비공개 — 온보딩 스킬 본문이 정본)). 보충 규칙:

- 질문은 AskUserQuestion. 자유 입력(O2 기본 정보·O7a URL 묶음·O7b 키워드·O10 금칙어)은 "아래 항목을 한 번에 적어 주세요" 프롬프트 1회 → 표로 되돌려 `맞아요 / 고칠게요` 확인
- 키 값·비밀번호는 어떤 단계에서도 받지 않는다. 설치 명령은 실행하지 않는다. 네이버 로그인은 안내만
- 파일 쓰기는 "기존 값 보존 병합": 이미 채워진 행은 덮지 않고 이번에 바꾼 항목만. `source-blogs.json`은 JSON으로 읽어 키만 갱신
- O3 블로그 ID와 O9 이미지 제공자 `.env` 쓰기는 blog-setup의 awk 한 줄(해당 줄만 교체·없으면 추가)과 같은 방식
- O7a 「찾는 법 안내」 문구는 `references/question-bank.md`에 둔다. URL 묶음은 `verify_blogs.py --json`에 한 번에 넘긴다
- O9 이미지 키 안내 문구의 정본은 `references/image-setup.md` 하나. blog-setup은 이 파일을 인용한다
- 호출 명령은 전부 작업 폴더 기준 `python3 scripts/<이름>.py …`
- O12는 `Skill` 도구로 `blog-design-system`을 부른다. 글 0편이면 스킬의 「레퍼런스 0 없음」 경로

---

## 4. 산문 파일별 변경

plan §3-4 표와 같다(재수록하지 않음). 공통: `## 📞 문의 안내: <연락처>` 고정 표기는 전부 "`마무리 블록`에 `문의헤딩`이 있을 때 `## 📞 <문의 헤딩 문구>: <연락처>`"로. `business-intro.png`·`:::place`·`title_region` 언급마다 조건절을 둔다. "합니다체"는 무조건 규칙이 아니라 `톤` 행 참조로만 쓴다.

---

## 부록 A. 테스트 픽스처

### A-1 `scaffold/scripts/tests/fixtures/profile-business.md`

```markdown
# 업체 기본정보

| 항목 | 내용 |
|---|---|
| 블로그 유형 | 업체 |
| 업체명 | 가나자전거 |
| 연락처 | 02-000-0000 |
| 주소 | 서울시 가나구 다라로 12 |
| 상품·서비스 | 자전거 수리, 자전거 정기 점검, 전기자전거 배터리 교체 |
| 지원 형태 | 카드 결제 |
| 제공 방식 | 매장 방문 |
| 고객 지역 | 가나동, 다라동, 마바동 |
| 강점 | 10년 운영, 당일 수리 |
| 장소 검색어 | 가나자전거 가나동 |
| 톤 | 합니다체 |
| 마무리 블록 | 문의헤딩, 소개이미지, 장소카드, 해시태그 |
| 문의 헤딩 문구 | 문의 안내 |
| 주제 키워드 | 자전거 수리, 자전거 점검, 전기자전거 배터리 |
| 이미지 소스 | ai, photo |
| 이미지 기본 장면 | Korean neighborhood bicycle repair shop |
| 배지 문구 | GANA BIKE |
| 브랜드 색 | #1F5E3A |
| 업체 유형어 | 자전거수리점, 자전거샵 |
| 업종 일반어 | 자전거 |
| 제목 정규화 | 전기 자전거→전기자전거 |
| 홍보 표지어 | |
| 공지 표지어 | |

## 꼭 지켜야 할 점

1. 타 브랜드 비방 금지.
2. 홍보글보다 정보성 글 위주로 쓰고, 홍보는 필요할 때만 합니다.
3. 복붙·사진 재사용·날짜만 바꾼 반복 글은 금지이며, 글마다 변주합니다.

## 금칙어

- `평생 무상 수리` — 변형 `평생무상수리`도 금지

## 홍보/정보 비율

정보성 3 : 홍보 1 이하.
```

### A-2 `scaffold/scripts/tests/fixtures/profile-personal.md`

```markdown
# 업체 기본정보

| 항목 | 내용 |
|---|---|
| 블로그 유형 | 개인 |
| 업체명 | 민수의 AI 노트 |
| 연락처 | |
| 주소 | |
| 상품·서비스 | AI 도구 활용 팁, 업무 자동화 |
| 지원 형태 | |
| 제공 방식 | |
| 고객 지역 | |
| 강점 | 직접 써 본 도구만 소개 |
| 장소 검색어 | |
| 톤 | 해요체 |
| 마무리 블록 | 해시태그 |
| 문의 헤딩 문구 | |
| 주제 키워드 | AI 도구 추천, 챗GPT 활용법, 업무 자동화 |
| 이미지 소스 | ai, stock |
| 이미지 기본 장면 | |
| 배지 문구 | |
| 브랜드 색 | |
| 업체 유형어 | |
| 업종 일반어 | |
| 제목 정규화 | |
| 홍보 표지어 | |
| 공지 표지어 | |

## 꼭 지켜야 할 점

1. 홍보글보다 정보성 글 위주로 쓰고, 홍보는 필요할 때만 합니다.
2. 복붙·사진 재사용·날짜만 바꾼 반복 글은 금지이며, 글마다 변주합니다.

## 금칙어

- 없음

## 홍보/정보 비율

정보성 3 : 홍보 1 이하.
```

기대: 두 픽스처 모두 `check_profile.py` → `profile: OK`. 개인 픽스처로 `build_final.py` → 마무리는 해시태그 줄만. 개인 픽스처로 `lint_post.py --stage upload` → `closing_block`은 해시태그만 검사, `tone` WARN, `title_region` SKIP.

## 부록 B. 네이버 자동완성 응답 샘플 (2026-10-21 실측, `q=자전거 수리`)

```json
{
"query" : ["자전거 수리"],
"answer" : [],
"intend" : [],
"items" : [
[["자전거 수리점", "0"],["근처 자전거 수리점", "0"],["전기자전거 수리", "0"],["전기자전거 수리점", "0"],["자전거 수리", "0"],["자전거 수리키트", "0"],["근처 자전거 수리", "0"],["평택 자전거 수리", "0"],["청주 자전거 수리", "0"],["잠실 자전거 수리", "0"]]
]
}
```
키워드 = `items[0][i][0]`. `items`가 비어 있거나 `items[0]`이 없으면 결과 0개.

## 부록 C. Pexels 검색 응답 필드 (사용하는 것만)

```json
{"total_results": 123, "page": 1, "per_page": 8,
 "photos": [{"id": 1, "width": 4000, "height": 2667, "url": "https://www.pexels.com/photo/…/",
             "photographer": "Jane Doe", "photographer_url": "https://www.pexels.com/@jane",
             "alt": "…", "src": {"original": "…", "large2x": "…", "large": "…", "medium": "…"}}]}
```
오류: 401/403 `{"error": "…"}` · 429 rate limit. 테스트는 이 형태를 mock한다.

## 부록 D. 메인이 통합 grep에 쓰는 철자 목록

행 이름: `블로그 유형` `톤` `마무리 블록` `문의 헤딩 문구` `주제 키워드` `이미지 소스` `이미지 기본 장면` · 마무리 블록 항목: `문의헤딩` `소개이미지` `장소카드` `해시태그` · 이미지 소스 항목: `ai` `stock` `photo` · env: `PEXELS_API_KEY` · 파일: `topic-seeds.md` · 스크립트: `verify_blogs.py` `keyword_expand.py` `fetch_stock.py` · 헬퍼: `load_closing_blocks` `load_tone` `load_image_sources` `own_posts_count` · 커맨드: `/naver-blog-autopilot:blog-onboard`

---

## 5. 1.1.2 — 무료 스톡 기본 제공자를 Openverse로 (2026-10-22)

배경: Pexels가 신규 API 키 발급을 일시 중단했다(공식 API 페이지 안내). 모임 참가자가 키 없이 스톡 사진을 쓰도록 키가 필요 없는 Openverse(WordPress 재단, https://api.openverse.org)를 기본으로 하고, Pexels는 이미 키가 있는 사람용으로 남긴다. 프로필 `이미지 소스`의 `stock` 값과 image-plan `유형=stock`은 그대로다.

### 5-1 제공자 결정 (`.env`)

- 새 env `STOCK_PROVIDER` = `openverse` | `pexels` (선택).
- 결정 순서: `STOCK_PROVIDER`가 있으면 그 값 → 없고 `PEXELS_API_KEY`가 있으면 `pexels` → 둘 다 없으면 `openverse`.
- `STOCK_PROVIDER` 값이 둘 중 하나가 아니면 오류(값은 출력하지 않음). `STOCK_PROVIDER=pexels`인데 키가 없으면 오류(다른 제공자로 넘어가지 않음).
- `.env` 탐색 순서는 1.1.0과 같다(`--env` → cwd `.env` → image-plan 상위 폴더 `.env` → 환경변수). `STOCK_PROVIDER`도 같은 곳에서 읽는다.

### 5-2 Openverse 호출 규칙 (`fetch_stock.py`)

- 요청: `GET https://api.openverse.org/v1/images/?q=<URL인코딩 검색어>&license=cc0,pdm&aspect_ratio=wide&mature=false&page_size=20`
- 헤더: `User-Agent: naver-blog-autopilot/<plugin version> (+https://github.com/heesun-woodi/woodi-claude-plugins)`. 키 없음(익명 한도: 분당 20회·하루 200회 — 응답 헤더 `x-ratelimit-*`).
- 선택: `results[]`를 순서대로 보며 ① `url`이 비어 있지 않고 ② 원본 `width`가 1200 이상이고 ③ 이미 이 작업 폴더의 다른 글 image-plan에 같은 원본 페이지(`foreign_landing_url`)가 기록돼 있지 않은 첫 결과의 `url`을 받는다. 받은 파일의 실제 가로가 800px 미만이거나 JPEG·PNG가 아니면 버리고 다음 결과(사진 받기는 슬롯당 최대 5번).
- 저장: JPEG면 `images/NN-<slug>.jpg`, PNG면 `images/NN-<slug>.png`. 실제 가로 판정은 표준 라이브러리로 JPEG SOF / PNG IHDR 헤더를 읽는다.
- 출처 기록(`출처` 열, 없으면 `검수` 칸): `출처: Openverse/<source> · <creator 또는 작자 미상> · <license 대문자> <foreign_landing_url>`.
- 결과 0건(또는 조건에 맞는 결과 없음)이고 검색어가 3단어 이상이면 마지막 단어를 뺀 검색어로 1회 재검색한다. 재검색으로 받으면 슬롯 줄 끝에 ` (검색어 줄임: <새 검색어>)`를 붙이고 image-plan 검색어 칸은 그대로 둔다. 그래도 없으면 1.1.0과 같이 `보류`·`검색 결과 없음`.
- 사진 받기(이미지 파일 다운로드) 단계의 403·404·429·5xx·네트워크 오류는 그 후보만 건너뛰고 다음 결과로 간다(슬롯당 받기 최대 5번 유지). 다섯 후보 모두 받기 실패면 그 슬롯은 `보류`·`검수` 칸 `사진 받기 실패`. 검색 API(api.openverse.org) 오류는 아래 exit 규칙대로 중단한다.
- 사진 주소 검사: 결과 `url`은 http·https만 받고, 루프백·사설·링크로컬 IP를 직접 적은 주소는 열지 않고 받기 오류 1번으로 센다.
- 받기 예산·거르기: 슬롯당 받기 최대 5번은 1차 검색과 재검색을 합친 횟수이고 이미 시도한 URL은 다시 받지 않는다(1차에서 5번을 다 썼으면 재검색 없음). 결과의 `filetype`이 있으면 jpg·jpeg·png만 후보, 받을 때 `Content-Length`가 8,000,000바이트 초과(또는 아래 형식 판정에서 걸러지는 `Content-Type`)면 본문을 읽지 않고 건너뛰며(길이 헤더가 없으면 청크로 읽다 8,000,000바이트를 넘는 순간 중단) 받기 1번으로 센다. 보류 사유: 받기를 시도했고 모두 받기 오류면 `사진 받기 실패`, 그 외는 `검색 결과 없음`.
- 형식 판정: 응답 `Content-Type`이 image/jpeg·image/png면 통과, 다른 형식(image/tiff·text/html 등)이면 본문을 읽지 않고 건너뛴다. 헤더가 없거나 application/octet-stream·binary/octet-stream·image/jpg·image/pjpeg이면 본문을 받은 뒤(상한 8,000,000바이트 그대로) 앞부분 매직 바이트(JPEG FFD8FF, PNG 89504E47)로 판정한다. `Content-Length`가 숫자인데 받은 합계와 다르면(잘린 본문) 받기 오류로 세고 파일을 쓰지 않는다. 읽기 중 예외(IncompleteRead 등)도 그 후보만 받기 오류.
- 시작 줄: `스톡: openverse · 키: 필요 없음` / `스톡: pexels · 키: <source>`. 끝 줄 `저장 n장 · 보류 n장`(1.1.0과 같음).
- exit: 0 완료(보류 포함) · 2 설정 오류(`STOCK_PROVIDER` 값 오류 · pexels인데 키 없음 · image-plan 없음/파싱 실패) · 3 거부(401·403) · 5 네트워크·5xx·JSON 아님 · 6 요청 한도(429, 재시도 없음). Pexels 경로의 동작·문구는 1.1.0과 같다.
- `--dry-run`: 네트워크 0, 시작 줄에 결정된 제공자를 보인다.

### 5-3 키·제공자 확인 (`check_image_key.py --stock`)

- openverse: 검색 1회(`q=desk`, `page_size=1`, 위 헤더)로 확인. 출력 `스톡 확인: openverse 사용 가능 (키 불필요)` exit 0 / 네트워크·5xx exit 5 / 429 exit 5(`요청 한도 — 잠시 뒤 다시`).
- pexels: 1.1.0과 같다(`스톡 키 확인: pexels 사용 가능 (<source>)`, exit 0/2/3/5).
- `STOCK_PROVIDER` 값 오류 · pexels인데 키 없음 → exit 2.

### 5-4 진단 줄 (blog-setup 2단계 · blog-run Step 0 — `PEXELS_KEY:` 줄을 대체)

`이미지 소스`에 `stock`이 있을 때만(blog-setup은 항상) 한 줄: `STOCK: OK (openverse, 키 불필요)` · `STOCK: OK (pexels, .env|env)` · `STOCK: MISSING (STOCK_PROVIDER=pexels인데 PEXELS_API_KEY 없음)` · `STOCK: CONFLICT (STOCK_PROVIDER 값이 openverse/pexels가 아님)`. 값은 출력하지 않는다. blog-run에서 MISSING·CONFLICT는 경고 후 「스톡 슬롯 보류」 모드(1.1.0의 `PEXELS_KEY: MISSING`과 같은 처리), OK는 조치 없음.

### 5-5 사용자에게 보이는 이름

- 온보딩 이미지 소스 보기: `무료 스톡 사진(키 없이 바로)`(기존 `무료 스톡 사진(Pexels)` 대체). 고르면 키 안내 없이 진행하고, Pexels 키가 이미 있는 사람만 `.env`에 `PEXELS_API_KEY=`(선택)를 넣는다고 한 줄 안내.
- 문서 표기: 「무료 스톡 사진(Openverse — 키 불필요, CC0·퍼블릭 도메인만)」. Pexels는 「이미 키가 있으면 선택 사용(신규 키 발급 일시 중단)」.
- 한국 특정 장면(지명·한국어 간판·한국 거리)은 Openverse에 거의 없다 → 이미지 디렉터는 그런 슬롯을 stock으로 잡지 않고 ai·photo로.
