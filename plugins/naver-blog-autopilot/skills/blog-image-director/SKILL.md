---
name: blog-image-director
description: Use when a Naver blog draft needs its image slots planned and filled — e.g. "이미지 뽑아줘", "사진 어디 넣을까", "이미지 생성", "이미지 계획 짜줘", "슬롯에 사진 넣어줘", "blog-image-director", "blog-run 이미지 단계", "blog-run Step 3". Reads the `![슬롯: …]()` slots in posts/NNN-slug/draft-v2.md, decides per slot whether it gets an AI image, a free stock photo (Pexels) or a real business photo — limited to the profile `이미지 소스` row (ai / stock / photo) — writes images/image-plan.md, runs scripts/gen_image.py for the ai slots (image AI = Gemini or OpenAI GPT image, chosen by the work folder .env) and scripts/fetch_stock.py for the stock slots, opens and checks each image, and returns a gate-3 summary. Do NOT use for writing or revising the post text (blog-draft-writer), fact checking (blog-fact-check), SEO scoring (blog-naver-seo), or uploading to Naver (blog-naver-upload).
---

# 블로그 이미지 디렉터

## 왜 이 스킬이 있나

디자인 시스템 레퍼런스 메모가 가리키듯 "소제목마다 요약 이미지 한 장 + 중간 현장 사진"이 글의 읽기 리듬을 만든다(`knowledge/design-system.md` ③·⑤).
이 스킬은 초안의 이미지 슬롯을 하나씩 진단해 **AI 생성(ai)** · **무료 스톡 사진(stock, Pexels)** · **업체 실사진(photo)** 으로 나눈다. 쓸 수 있는 유형은 프로필 `이미지 소스` 행에 든 것뿐이다(§0). ai 슬롯은 이미지 AI로 생성하고(Gemini 또는 OpenAI GPT 이미지 — 작업 폴더 `.env`가 정함, §6), stock 슬롯은 `fetch_stock.py`가 Pexels에서 받는다(§6-2).
홍보성 글에 AI·스톡 이미지를 쓰거나, 글자가 박힌 이미지·얼굴 클로즈업·워터마크·같은 장면 반복이 나가는 것을 여기서 막는다.

- 수행 주체: **메인 세션**(서브에이전트 아님). 전제: cwd = 작업 폴더. 지식 파일은 cwd의 `knowledge/`에서만 읽는다.
- 입력: `work/posts/NNN-slug/draft-v2.md`, `work/posts/NNN-slug/gates.md`(`## 선택`의 유형 = 정보|홍보), `knowledge/business-profile.md`(`이미지 소스`·`이미지 기본 장면`·`마무리 블록`·`연락처` 행), `knowledge/design-system.md` ⑤, `photos/` 목록(+있으면 `photos/README.md`), 이 스킬의 `references/prompt-patterns.md`, `knowledge/learned-preferences.md`(있으면 — `## 적용 중`의 `범주=이미지`·`범주=표지` 학습 규칙. 우선순위는 잠긴 규칙(잠긴 규칙 = `business-profile.md` 금칙어·꼭 지켜야 할 점, `design-system.md` ⑤ 반드시 지킬 것(이미지 속 글자·얼굴 클로즈업·로고 금지, 홍보글은 실사진만, 사진 재사용 금지), ⑧ 지어내기 금지·출처·금칙 — 표지 `00-cover.png`의 제목·배지·전화번호(연락처가 있을 때) 합성은 ⑤의 표지 예외로 허용, 배경(`00-bg.png` 또는 스톡 배경 `00-bg.jpg`)에는 글자 없음) > 학습 규칙 > design-system 나머지 > `prompt-patterns.md` 예시. `## 후보`·`## 보류·삭제`는 따르지 않는다).
- 산출물: `work/posts/NNN-slug/images/image-plan.md`, `images/NN-<slug>.png`(ai 슬롯), `images/NN-<slug>.jpg`(stock 슬롯), 게이트 3용 요약.
- 이 스킬은 **사용자에게 묻지 않는다.** 게이트 3(이미지 승인) 질문과 `gates.md ## 이미지승인` 기록은 `/naver-blog-autopilot:blog-run`이 한다.

## 0. 전제 확인

```bash
P=work/posts/<NNN-slug>
ls $P/draft-v2.md $P/gates.md knowledge/design-system.md scripts/gen_image.py
mkdir -p $P/images
ls photos/ ; cat photos/README.md 2>/dev/null
```

프로필에서 이미지 소스와 마무리 블록을 읽는다(스크립트와 같은 해석):

```bash
python3 -c 'import sys; sys.path.insert(0,"scripts"); import lint_post; print("이미지 소스:", ",".join(lint_post.load_image_sources("knowledge"))); print("마무리 블록:", ",".join(lint_post.load_closing_blocks("knowledge")))'
```

- 이 줄이 오류(`ValueError` — 행이 비었거나 값이 틀림)면 생성하지 말고 요약에 "프로필 `이미지 소스`/`마무리 블록` 확인 필요 — `/naver-blog-autopilot:blog-onboard`"로 적어 메인에 넘긴다.
- `이미지 소스`에 `stock`이 있으면 `ls scripts/fetch_stock.py`도 확인한다. `ai`가 없으면 `gen_image.py`는 돌리지 않는다(§6).
- `이미지 기본 장면` 행(영문 장면구, 비면 `Korean everyday scene`)을 읽어 둔다 — ai 프롬프트 접두(gen_image가 자동)와 stock 검색어의 핵심 명사(§3-2, 이 스킬이 직접 넣음)에 쓰인다.

`draft-v2.md`가 없으면 "B' 단계(draft-v2.md)가 끝나지 않았습니다"라고 보고하고 중단한다. `design-system.md` ⑤를 읽어 둔다(텍스트 렌더링 금지·얼굴 클로즈업 금지·정보성=AI 허용/홍보성=실사진만·재사용 금지·"AI 생성" 표기 규정 유무).

## 1. 슬롯 추출 (등장 순서 = 슬롯 번호)

```bash
grep -n '!\[슬롯:' $P/draft-v2.md
```

위에서부터 `01, 02, …`로 번호를 붙인다. 이 번호가 image-plan.md `슬롯` 열, 파일명 `NN-`, 그리고 Step 4의 치환 순서가 된다.
각 슬롯의 `위치`는 그 슬롯이 속한 절 끝(다음 소제목 직전)의 `## 소제목`으로 적는다.
**`00` 표지는 draft-v2.md 슬롯이 아니다** — 이 스킬이 image-plan.md 맨 윗줄에 직접 추가한다(§5). 슬롯 매칭·확정 이미지 수 계산에서 `00`은 제외된다(메인과 `build_final.py`가 그렇게 처리).
슬롯 수가 본문 슬롯 ≥ min_images(표지 제외), 절 끝 1~2장 기준에 못 미쳐도 **초안을 고치지 않는다** — 요약에 "슬롯 부족 N개"로 적어 메인에 넘긴다.

## 2. 슬롯 진단 — 목적과 유형

슬롯마다 **목적**을 하나 정한다: `표지` / `소제목 요약` / `절차 장면` / `제품·상품` / `현장` / `작업 장면` / `서류·자격` / `안전` / `시험`(해당 업종만) / `업체 소개(실사진)`(프로필 `마무리 블록`에 `소개이미지`가 있을 때만 — 없으면 이 목적을 쓰지 않고, 초안에 업체 소개 성격의 슬롯이 있으면 `현장`으로 진단한다).
(목적 단어가 파일명 slug가 된다(`00` 표지는 고정 `00-cover.png`): 표지→cover, 시험→exam, 절차→steps, 제품·상품→product, 현장→scene, 작업→work, 안전→safety, 서류→documents, 업체 소개→business(`NN-business.png`) …)

**유형 판정 규칙(위에서부터 먼저 맞는 것).** 쓸 수 있는 유형은 프로필 `이미지 소스`에 든 것(`ai`·`stock`·`photo`)뿐이다 — 단 1번(홍보 글 = photo)은 ⑤ 잠긴 규칙이라 예외다.
1. 글 유형이 `홍보`(gates.md `## 선택`) → **모든 슬롯 photo**(⑤ "홍보성 글 = 업체 실사진만" — ai·stock 모두 금지).
2. **업체 고유 장면**(업체 소개(실사진)·간판·매장·직원·이용 안내·현장 실제 모습) → **photo**(`이미지 소스`에 photo가 있을 때). photo가 없으면 **ai**(간판·얼굴 없이 일반 장면으로). 스톡 사진은 남의 매장·사람이라 업체 고유 장면에 쓰지 않는다.
3. `이미지 소스`에 photo가 있고, `photos/`에 그 장면에 맞는 실사진이 있으며 **이전 글에서 쓰지 않았다** → 정보성 장면이라도 **photo 우선**.
4. `이미지 소스`에 **stock**이 있고 슬롯이 **현장·사물·분위기** 일반 장면(목적 `현장`·`제품·상품`·`소제목 요약`·`서류·자격`·`안전`, 또는 2~4단어 검색어로 찾을 수 있는 `절차 장면`·`작업 장면`) → **stock 우선**.
5. 나머지 정보성 장면(특정 동작·도구 사용처럼 검색어로 찾기 어려운 것) → **ai**(`이미지 소스`에 ai가 있을 때). ai가 없으면 stock(검색어를 더 일반적인 장면으로), stock도 없으면 photo 후보(§4).

`이미지 소스`에 `stock`이 없으면 stock 유형은 쓰지 않는다.

이전 글 사용 여부(⑤ 재사용 금지) 확인:

```bash
grep -ho 'photos/[^ ,|)`]*' work/posts/*/images/image-plan.md 2>/dev/null | sort | uniq -c
```

현재 글 폴더의 행은 빼고 본다. 이미 쓴 실사진은 후보에서 제외한다. 단 프로필 `마무리 블록`에 `소개이미지`가 있으면 `photos/business-intro.png`는 마무리 블록의 고정 자산이라 재사용 검사에서 제외한다.
스톡 사진도 재사용 금지다 — 이전 글이 받은 Pexels 사진 주소와 겹치지 않게 본다(같은 검색어는 같은 사진을 돌려주므로 이전 글 검색어와도 겹치지 않게 쓴다):

```bash
grep -ho 'pexels.com/photo/[^ |)]*' work/posts/*/images/image-plan.md 2>/dev/null | sort | uniq -c
```
⑤에 중간 현장 장면 규칙(예: "본문 중간 절에 현장·작업 장면 최소 1장")이 있으면 만족하는지 확인한다(그 장면이 중간 절 슬롯 중 1개 이상).

## 3. ai 슬롯 프롬프트 작성

`references/prompt-patterns.md`의 장면 패턴(1~7)에서 고르고(`00` 표지 배경은 패턴 1·3·4 중, "표지용 배경 패턴" 절 참고) `{time}`·`{angle}`·`{weather}`를 채운다. 원칙:
- 표의 프롬프트 칸에는 **장면 설명만**(영어 1~2문장, `|` 금지). 공통 접두/접미는 `gen_image.py`가 붙인다 — 중복해 쓰지 않는다.
- 같은 글 안에서 패턴·시간대·앵글이 겹치지 않게 변주한다.
- 글자·숫자·로고·번호판·얼굴 정면이 생길 만한 소재(현수막, 게시판, 영수증·결과지, 차량 번호판)를 장면에 넣지 않는다.
- **학습 규칙(`범주=이미지`)**: 장면·앵글·시간대·인물 비중 같은 규칙(예: "인물보다 사물 위주")을 패턴 선택과 프롬프트에 반영한다. 적용한 id를 기억해 8단계 요약에 적는다.

## 3-2. stock 슬롯 검색어 작성

`references/prompt-patterns.md`의 「stock 검색어 패턴」에서 고른다. 표의 프롬프트 칸(머리 `프롬프트(ai) / 검색어(stock) / 후보 파일(photo)`)에 **검색어만** 쓴다.
- **영문 2~4단어 명사구**(예: `bicycle chain cleaning closeup`). 문장·쉼표·`|`·한글을 쓰지 않는다.
- 프로필 `이미지 기본 장면`의 **핵심 명사 1개를 검색어 안에 직접 넣는다**(예: 장면구 `Korean neighborhood bicycle repair shop` → `bicycle` 또는 `repair shop`). **`fetch_stock.py`는 `이미지 기본 장면`을 검색어 앞에 자동으로 붙이지 않는다** — SPEC §1 비고("Pexels 검색어 접두")와 다른 점이다. 스크립트는 칸의 검색어를 그대로 Pexels에 보낸다. `이미지 기본 장면`이 비어 기본값(`Korean everyday scene`)이면 글 주제의 사물 명사 1개를 넣는다.
- 글자·로고·얼굴이 나오기 쉬운 말(`sign`, `logo`, `poster`, `menu`, `portrait`, `face`, `smiling`, `selfie`, `screen`, `brand`)을 넣지 않는다. 사물·손·뒷모습·위에서 본 구도 쪽 말(`hands`, `closeup`, `top view`, `from behind`)을 쓴다.
- 같은 글 안에서, 그리고 이전 글(§2 grep)과 검색어가 겹치지 않게 한다.
- 표지(`00`) 배경도 stock이 될 수 있다(§5) — 이때 검색어는 피사체가 가운데 있는 넓은 장면 쪽으로 고른다.

## 4. photo 슬롯 후보

`photos/` 파일명과 `photos/README.md` 설명(있으면)으로 장면에 맞는 후보 **1~3개**를 고른다(작업 폴더 기준 경로 `photos/…`).
맞는 사진이 없으면 후보 칸에 `(실사진 없음 — 담당자 지정 필요)`라고 쓰고, 홍보 글이 아니면 ai로 바꿀지를 게이트 3 질문거리로 남긴다(유형을 임의로 바꾸지 않는다).

## 5. `images/image-plan.md` 저장 (포맷 고정 — Step 4가 소비)

```markdown
# 이미지 계획 — posts/NNN-slug
| 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 검색어(stock) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수 | 출처 |
|---|---|---|---|---|---|---|---|---|
| 00 | 표지(대표) | 표지 | cover | a tidy small bicycle shop interior with a workbench, subject centered … (글자 없는 배경 장면, 예) | 제목: <frontmatter title 그대로>; 줄바꿈: 줄1; 줄2[; 줄3] | images/00-cover.png | | |
| 01 | ## 소제목1 | 소제목 요약 | ai | hands checking bicycle tire pressure with a floor pump … | 자전거 타이어 공기압을 확인하는 손(예) | | | |
| 02 | ## 소제목2 | 업체 소개(실사진) | photo | photos/매장-01.jpg, photos/매장-02.jpg | 정비 공구가 정리된 매장 작업대(예) | (게이트 3에서 확정) | | |
| 03 | ## 3️⃣ 체인 청소 | 현장 | stock | bicycle chain cleaning closeup | 체인을 닦는 장면(예) | | | |
```

(가상 예. 표 머리는 1.0.0과 같고 맨 끝에 `출처` 열이 추가됐다 — 스크립트는 열을 접두 일치로 찾으므로 `출처` 열이 없는 옛 표도 돈다.)

- **`00` 표지 행(형식 확정, 셀 안 `|` 금지)**: `| 00 | 표지(대표) | 표지 | cover | <글자 없는 배경 장면 프롬프트, 패턴 1·3·4 중> | 제목: <frontmatter title 그대로>; 줄바꿈: 줄1; 줄2[; 줄3] | images/00-cover.png | <검수> |`
  - `제목:`은 게이트 2에서 확정된 draft-v2.md frontmatter `title`과 **글자 그대로** 같아야 한다. `build_final.py`가 대조해 다르면 "표지 재생성 필요"로 멈춘다.
  - `줄바꿈:`은 줄당 12자 이내 2~3줄(`;`로 구분). make_cover.py `--title`에는 `줄1|줄2`로 넘긴다.
  - `파일` 칸은 항상 `images/00-cover.png`(gen_image.py가 바꾸지 않는다). 배경은 `images/00-bg.png`에 따로 저장된다.
  - **학습 규칙(`범주=표지`)**: 줄바꿈 위치(예: "키워드를 첫 줄에")·줄 수·`--sub` 배지 문구·배경 선택(AI 배경 패턴 / 실사진 배경 우선 등) 규칙을 `줄바꿈:`과 배경 프롬프트(또는 실사진 배경)에 반영한다. 줄당 12자·2~3줄과 `제목:` = frontmatter `title` 규칙은 그대로다(빌더 대조).

- **표지 배경을 stock으로**(`이미지 소스`에 stock이 있을 때 — ai가 없으면 표지 배경은 stock 또는 실사진): `00` 행의 `유형`을 `stock`, 프롬프트 칸에 검색어(§3-2), `파일` 칸에 처음에는 `images/00-bg.jpg`를 적는다(fetch_stock은 칸에 `.jpg` 경로가 있으면 그 이름으로 저장한다). 받은 뒤 `make_cover.py --bg $P/images/00-bg.jpg`로 합성하고(§6), `파일` 칸을 `images/00-cover.png`로 바꿔 둔다(뒤 단계는 이 칸을 표지 파일로 읽는다). `제목:`·`줄바꿈:` 규칙은 cover 행과 같다.
- `유형` ∈ {ai, stock, photo}(+ `00` 행의 cover). `이미지 소스`에 없는 유형은 쓰지 않는다(홍보 글의 photo는 예외). 칸 안에 `|`를 쓰지 않는다.
- `캡션(alt)`: 한 줄, 무엇을 보여주는지. **내부 메모용이며 본문에 노출되지 않는다(업로드본은 캡션 없음).** "AI 생성" 표기는 ⑤에 규정이 있을 때만 따른다. (`00` 행은 예외로 제목·줄바꿈 지정 칸.)
- `파일` 경로 규칙: ai = **글 폴더 기준** `images/NN-<slug>.png`(gen_image.py가 채움), stock = **글 폴더 기준** `images/NN-<slug>.jpg`(fetch_stock.py가 채움 — 결과가 없으면 `보류`), photo = **작업 폴더 기준** `photos/<파일>`(게이트 3에서 확정 후 메인이 채움). Step 4는 `images/…`는 글 폴더, `photos/…`는 작업 폴더를 기준으로 절대경로를 만든다.
- `검수` 열은 7단계에서 채운다(처음엔 비워 둔다). fetch_stock.py가 `검색어 없음`·`검색 결과 없음`을 적을 수 있다. gen_image.py·fetch_stock.py는 열 이름으로 찾으므로 열이 추가돼도 동작한다.
- `출처` 열: stock 행만 fetch_stock.py가 `출처: Pexels/<사진가> <사진 주소>`로 채운다(직접 쓰지 않는다). ai·photo 행은 비워 둔다. Pexels 라이선스는 출처 표기 의무가 없다 — 본문 표기는 ⑤에 규정이 있을 때만 따른다.

## 6. 생성

```bash
python3 scripts/gen_image.py $P/images/image-plan.md --dry-run      # 먼저: 대상 슬롯·최종 프롬프트·파일명 확인(키 불필요)
uv run --with google-genai --with pillow scripts/gen_image.py $P/images/image-plan.md   # ai 행 + cover 행. cover는 images/00-bg.png에 배경 저장, `파일` 칸은 그대로 (제공자와 무관하게 같은 명령)
uv run --with pillow scripts/make_cover.py --bg $P/images/00-bg.png --title "줄1|줄2" [--sub "<지역>·<지역> <업체 유형>"] --out $P/images/00-cover.png
```

- **제공자 결정**(gen_image.py가 한다): `--provider gemini|openai`(지정 시) > `.env`의 `IMAGE_PROVIDER` > `GEMINI_API_KEY`가 있으면 gemini > `OPENAI_API_KEY`가 있으면 openai > 없음. `IMAGE_PROVIDER`가 정한 제공자의 키가 비면 오류로 멈춘다. 기본 모델 gemini=`gemini-3-pro-image`, openai=`gpt-image-2`(`.env`의 `IMAGE_MODEL`로 바꿈). 보통은 `--provider`를 넘기지 않는다(`.env`를 따름) — 이 글만 다른 제공자로 돌릴 때만 붙인다.
- **시작 줄 확인**: 실행 직후 `키: … · 제공자: … · 모델: …` 줄을 읽어 의도한 제공자인지 본다(blog-run Step 0의 `IMAGE_KEY: OK (<provider>, …)`와 같은지). 다르면 생성 결과를 쓰지 말고 요약에 적어 메인에 넘긴다. 요약·`gates.md`에는 **`제공자` 값만** 옮긴다 — 시작 줄의 키 파일 경로·모델 값은 옮기지 않는다(잘못 넣은 키가 섞일 수 있음). OpenAI 경로는 표준 라이브러리라 `--with google-genai`가 있어도 무방하다.
- 표지 합성은 로컬 Pillow라 비용 0. 이 머신 python3에는 Pillow가 없으므로 **반드시 `uv run --with pillow`** 로 돌린다.
- 표지 글꼴: Pretendard(ExtraBold·SemiBold)를 먼저 쓰고, 없으면 OS 기본 한글 글꼴(macOS AppleSDGothicNeo, Windows 맑은 고딕 Bold `malgunbd.ttf`)로 대신한다. 하나도 없으면 make_cover.py가 추측 렌더 없이 exit 2 → 생성하지 말고 요약에 글꼴 없음으로 적어 메인에 넘긴다(설치 안내는 `/naver-blog-autopilot:blog-setup`).
- 배경을 실사진으로 쓰려면 `--bg photos/<파일>`(이 경우 gen_image는 `--only <ai 슬롯 번호(쉼표)>`로 ai 행만 생성한다 — 옵션 없이 실행하면 00 행도 생성됨).
- 표지 재생성 요청이 줄바꿈·배지 문구만이면 make_cover.py만 다시(비용 0), 배경이면 `gen_image.py --only 00` 뒤 make_cover.py를 다시 돌린다.

- 키 탐색 순서: `--env` → 작업 폴더(cwd) `.env` → image-plan.md 상위 폴더들의 `.env` → 환경변수. 읽는 곳 — 키: API 키(GEMINI_API_KEY/OPENAI_API_KEY)가 든 첫 .env 파일의 값. 어느 파일에도 없으면 환경변수. IMAGE_PROVIDER·IMAGE_MODEL: 키를 찾은 .env의 값(그 파일에 없으면 미지정). 키를 환경변수에서 읽을 때는 항목마다 cwd .env → 환경변수 중 처음 값이 있는 곳. 같은 이름이 여러 줄이면 처음 나온 비어 있지 않은 값을 쓴다. 키 값은 출력되지 않는다. 키가 없거나 `IMAGE_PROVIDER`와 키가 어긋나면 스크립트가 exit 2 → 생성하지 말고 요약에 **"Gate: 이미지 키 대기"** 로 적어 메인에 넘긴다.
- 결제·권한 실패(제공자별): Gemini `429` = 결제(Billing)가 없는 키(무료 키는 기다려도 안 풀림). OpenAI `401` = 키 오류, `403` = 조직 인증(Verify Organization) 필요 또는 모델 권한 없음, `429`(insufficient_quota·billing) = 결제·한도 문제(남은 슬롯 중단; 그 밖의 429·5xx는 스크립트가 최대 3회 재시도한 뒤 그 슬롯만 실패). 남은 슬롯을 같은 원인으로 반복 호출하지 말고 요약에 원인을 적어 메인에 넘긴다.
- 예상 비용(추정치): Gemini는 장당 약 $0.04(`COST_PER_IMAGE_USD`, 검증된 단가 아님 — gemini-3-pro-image 2K 단가는 https://ai.google.dev/pricing 에서 확인). OpenAI(GPT 이미지)는 금액을 적지 않는다 — OpenAI 요금 페이지(https://openai.com/api/pricing/)에서 확인. 어느 쪽이든 재생성도 과금된다.
- `이미지 소스`에 `ai`가 없으면 `gen_image.py`를 돌리지 않는다(표지 배경은 stock 또는 실사진 `--bg photos/<파일>`). gen_image.py는 stock·photo 행을 건너뛴다(경고 없음 — 시작 줄 `슬롯 N개 (ai a, photo b, stock s) → 이번 대상 ai c개`).
- 표지 전화 줄: `make_cover.py`는 `--phone`을 넘기지 않아도 된다 — 프로필 `연락처`를 쓰고, 둘 다 비면 **전화 줄을 그리지 않는다**(dry-run `전화: 없음`). `업체명`(또는 `--brand`)은 여전히 필수다(없으면 exit 2, `오류: …업체명 행이 비어 있습니다 … (또는 --brand로 지정)`). `--sub`의 지역 부분은 `고객 지역`이 있을 때만 쓴다.
- 실패 슬롯은 stderr에 남고 나머지는 계속된다(exit 1). image-plan.md는 슬롯이 성공할 때마다 저장되므로 중간에 끊겨도 완료분은 남는다.
- **재시도·재생성 한도(한 문장 규칙)**: API 실패 슬롯은 `--only`로 1회 재시도(§6), 검수 불합격 슬롯은 프롬프트를 고쳐 슬롯당 최대 2회 재생성(§7), 한 글의 총 생성 호출은 ai 슬롯 수 × 3 이내.

## 6-2. stock 슬롯 받기 (`이미지 소스`에 stock이 있을 때)

```bash
python3 scripts/fetch_stock.py work/posts/<NNN-slug> --dry-run           # 먼저: 슬롯 · 검색어 · 예상 파일명 (네트워크·키 불필요)
python3 scripts/fetch_stock.py work/posts/<NNN-slug> [--only NN[,NN]]; echo "exit=$?"
```

- 시작 줄 `스톡: pexels · 키: <출처 경로 | 환경변수>`(키 값은 나오지 않는다), 슬롯 줄 `[OK] 03 → images/03-scene.jpg (출처: Pexels/<사진가> <주소>)` / `[보류] 05 검색어 없음` / `[보류] 04 검색 결과 없음 (<검색어>)`, 끝 줄 `저장 n장 · 보류 n장`. dry-run은 `03 · <검색어> · images/03-scene.jpg` 줄과 `(dry-run) 네트워크 접속 없음 · 대상 n장`. stock 행이 없으면 `stock 슬롯이 없습니다.` + `저장 0장 · 보류 0장`(exit 0).
- 키 탐색은 gen_image와 같은 순서(`--env` → cwd `.env` → image-plan.md 상위 폴더들의 `.env` → 환경변수 `PEXELS_API_KEY`). 확인만 하려면 `python3 scripts/check_image_key.py --stock`.
- 슬롯마다 image-plan.md를 바로 저장하므로 중간에 끊겨도 받은 슬롯은 남는다. 사진 선택은 스크립트가 한다(가로 1600px 이상인 첫 사진). Pexels는 무료라 비용은 0이지만 요청 한도가 있다 — 같은 검색어로 반복 호출하지 않는다.

| exit | 조건 | 그때까지 받은 슬롯 | 대응 |
|---|---|---|---|
| 0 | 처리 완료(보류 포함) · `--dry-run` · stock 행 없음 | — | 7단계 검수. `보류` 행은 검색어를 고쳐 `--only NN` 1회, 그래도 보류면 ai 전환 후보로 게이트 3에 |
| 2 | 키 없음(`스톡 키 없음 — .env에 PEXELS_API_KEY=…`) · `--env` 파일 없음 · image-plan.md 없음 · 표 파싱 실패(머리 없음·필수 열 없음·칸 수 초과) · `--only` 오류 · 잘못된 인자 | 요청 없음 | 키 없음이면 요약에 **"Gate: 스톡 키 대기"**. 그 밖은 표·인자를 고쳐 다시 |
| 3 | Pexels 401·403(검색 또는 사진 받기) — 남은 슬롯 중단 | image-plan.md에 저장됨 | 키 거부 — 요약에 원인을 적어 메인에 넘긴다(반복 호출 금지) |
| 5 | 네트워크 오류·타임아웃·5xx·그 밖 HTTP 오류·JSON 아닌 응답 — 남은 슬롯 중단 | 저장됨 | 남은 슬롯만 `--only`로 1회 재시도 |
| 6 | 429(요청 한도) — 재시도 없이 남은 슬롯 중단 | 저장됨 | 재시도하지 말고 요약에 "스톡 요청 한도"로 적어 메인에 넘긴다 |

- 표지 배경이 stock이면(§5) `--only 00`으로 받은 뒤 `uv run --with pillow scripts/make_cover.py --bg $P/images/00-bg.jpg --title "줄1|줄2" [--sub …] --out $P/images/00-cover.png`, 그다음 `00` 행 `파일` 칸을 `images/00-cover.png`로 바꾼다.
- **재시도·재생성 한도**: stock 슬롯은 검색어를 고쳐 슬롯당 최대 2회 다시 받는다(§7). 같은 검색어 재실행은 같은 사진을 돌려주므로 하지 않는다.

## 7. 생성 이미지 검수 — 반드시 열어서 본다

ai 슬롯 이미지, stock 슬롯 사진(`images/NN-<slug>.jpg`)과 `00-bg.png`(또는 `00-bg.jpg`)·`00-cover.png`를 **Read 도구로 한 장씩 열어** 확인한다(파일 존재만으로 통과시키지 않는다):

| 검사 | 불합격 예 |
|---|---|
| 글자 렌더링 없음 | 간판·제품 문구·번호판·서류 글씨·가짜 한글 (OpenAI GPT 이미지는 글자를 또렷하게 잘 그리므로 제품·벽·안내판·옷의 작은 글자까지 더 꼼꼼히 본다) |
| 얼굴 클로즈업 없음 | 정면 얼굴이 식별되는 인물 |
| 같은 글 안 장면 중복 없음 | 두 슬롯이 같은 구도·같은 시간대 |
| 장면이 캡션·소제목과 맞음 | 실내 작업 설명에 야외 장면 |
| 로고·브랜드 없음 | 제조사 로고, 워터마크 |
| (stock) 글자·로고·얼굴 클로즈업·워터마크 없는 사진(⑤와 동일) | 남의 간판·상표, 화면·종이의 읽히는 글자, 정면 얼굴, 사진가 워터마크 |
| (stock) 장면이 글 주제·국내 상황과 어긋나지 않음 | 주제와 무관한 장식 사진, 외국 도로 표지·번호판이 보이는 거리 |
| (표지 `00`) 제목 글자 잘림·겹침 없음 | 00-cover.png에서 제목이 가장자리에 걸리거나 배지·전화번호와 겹침 |
| (표지 `00`) 오타 없음 | 표지 제목이 frontmatter `title`과 다름 |
| (표지 `00`) 배경(00-bg.png)에 글자·로고 없음 | 배경에 간판·가짜 글씨·로고 |
| (표지 `00`) 중앙 안전 영역 안 | 피사체·제목이 1:1 크롭에서 잘림 |

판정은 `검수` 열에 `PASS` 또는 `FAIL: <사유>`로 적는다(stock 행은 fetch_stock이 적은 값이 있으면 그 뒤에 덧붙인다). FAIL이면 프롬프트(stock은 검색어)를 고쳐(원인 소재 제거·앵글 변경) `--only <슬롯>`으로 재생성·재수신 — **슬롯당 최대 2회**(§6·§6-2 한도 규칙). 2회 뒤에도 FAIL이면 `FAIL(2회): <사유>`로 남기고 게이트 3에 올린다(photo 전환 후보로 제안).

## 8. 게이트 3용 요약 (메인으로 반환)

```
이미지 계획: work/posts/NNN-slug/images/image-plan.md
| 슬롯 | 위치 | 유형 | 파일 / 후보 | 검수 |
00 표지 cover images/00-cover.png <검수>
01 ## … ai images/01-<slug>.png PASS
02 ## … photo 후보: photos/매장-01.jpg, photos/매장-02.jpg (선택 필요)
03 ## … stock images/03-scene.jpg PASS (출처: Pexels/<사진가>)
…
특이사항: 슬롯 부족 N개 / 실사진 없음 슬롯 / 보류(stock) 슬롯 / FAIL(2회) 슬롯 / Gate: 이미지 키 대기 / Gate: 스톡 키 대기 / 스톡 요청 한도 / 제공자: <gemini|openai>
적용 규칙: <3·5단계에서 반영한 L-… 또는 "없음">
```

## 9. 게이트 3 이후는 이 스킬 밖

- 게이트 3 질문(교체·재생성·실사진 지정·"다른 사진으로(검색어 수정)")과 `gates.md ## 이미지승인` 기록은 blog-run(메인)이 한다. 재생성 요청은 `gen_image.py --only NN`(표지는 `--only 00` 뒤 make_cover.py, 줄바꿈·배지만이면 make_cover.py만), stock 교체는 검색어를 고친 뒤 `fetch_stock.py work/posts/<NNN-slug> --only NN` 재실행이며 **디스패치가 아니다**.
- 승인 결과 반영(photo 슬롯 `파일` 확정, `scripts/build_final.py`가 final.md를 만든다, `lint_post.py --stage upload`)은 **blog-run Step 4(메인)** 가 image-plan.md를 기준으로 한다.

## 금칙

- 홍보성 글·업체 소개(실사진) 슬롯에 AI 이미지·스톡 사진 금지(⑤).
- 프로필 `이미지 소스`에 없는 유형 사용 금지(홍보 글의 photo는 ⑤ 예외).
- 이전 글에서 쓴 실사진·AI 이미지·스톡 사진 재사용 금지.
- 이미지에 글자·숫자·로고·번호판·얼굴 클로즈업 금지. 금칙어가 가리키는 장소·표지·암시 장면 금지(금칙어 규칙).
- 이 스킬에서 `draft-v2.md`·`final.md`를 고치지 않는다.
