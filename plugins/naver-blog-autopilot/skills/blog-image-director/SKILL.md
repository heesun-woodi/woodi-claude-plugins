---
name: blog-image-director
description: Use when a Naver blog draft needs its image slots planned and filled — e.g. "이미지 뽑아줘", "사진 어디 넣을까", "이미지 생성", "이미지 계획 짜줘", "슬롯에 사진 넣어줘", "blog-image-director", "blog-run 이미지 단계", "blog-run Step 3". Reads the `![슬롯: …]()` slots in posts/NNN-slug/draft-v2.md, decides per slot whether it gets an AI image (informational scenes) or a real business photo (promo/business intro), writes images/image-plan.md, runs scripts/gen_image.py for the ai slots (image AI = Gemini or OpenAI GPT image, chosen by the work folder .env), opens and checks each generated image, and returns a gate-3 summary. Do NOT use for writing or revising the post text (blog-draft-writer), fact checking (blog-fact-check), SEO scoring (blog-naver-seo), or uploading to Naver (blog-naver-upload).
---

# 블로그 이미지 디렉터

## 왜 이 스킬이 있나

디자인 시스템 레퍼런스 메모가 가리키듯 "소제목마다 요약 이미지 한 장 + 중간 현장 사진"이 글의 읽기 리듬을 만든다(`knowledge/design-system.md` ③·⑤).
이 스킬은 초안의 이미지 슬롯을 하나씩 진단해 **AI 생성(ai)** 과 **업체 실사진(photo)** 을 나누고, ai 슬롯만 이미지 AI로 생성한다(Gemini 또는 OpenAI GPT 이미지 — 작업 폴더 `.env`가 정함, §6).
홍보성 글에 AI 이미지를 쓰거나, 글자가 박힌 이미지·얼굴 클로즈업·같은 장면 반복이 나가는 것을 여기서 막는다.

- 수행 주체: **메인 세션**(서브에이전트 아님). 전제: cwd = 작업 폴더. 지식 파일은 cwd의 `knowledge/`에서만 읽는다.
- 입력: `work/posts/NNN-slug/draft-v2.md`, `work/posts/NNN-slug/gates.md`(`## 선택`의 유형 = 정보|홍보), `knowledge/design-system.md` ⑤, `photos/` 목록(+있으면 `photos/README.md`), 이 스킬의 `references/prompt-patterns.md`, `knowledge/learned-preferences.md`(있으면 — `## 적용 중`의 `범주=이미지`·`범주=표지` 학습 규칙. 우선순위는 잠긴 규칙(잠긴 규칙 = `business-profile.md` 금칙어·꼭 지켜야 할 점, `design-system.md` ⑤ 반드시 지킬 것(이미지 속 글자·얼굴 클로즈업·로고 금지, 홍보글은 실사진만, 사진 재사용 금지), ⑧ 지어내기 금지·출처·금칙 — 표지 `00-cover.png`의 제목·배지·전화번호 합성은 ⑤의 표지 예외로 허용, 배경(`00-bg.png`)에는 글자 없음) > 학습 규칙 > design-system 나머지 > `prompt-patterns.md` 예시. `## 후보`·`## 보류·삭제`는 따르지 않는다).
- 산출물: `work/posts/NNN-slug/images/image-plan.md`, `images/NN-<slug>.png`(ai 슬롯), 게이트 3용 요약.
- 이 스킬은 **사용자에게 묻지 않는다.** 게이트 3(이미지 승인) 질문과 `gates.md ## 이미지승인` 기록은 `/naver-blog-autopilot:blog-run`이 한다.

## 0. 전제 확인

```bash
P=work/posts/<NNN-slug>
ls $P/draft-v2.md $P/gates.md knowledge/design-system.md scripts/gen_image.py
mkdir -p $P/images
ls photos/ ; cat photos/README.md 2>/dev/null
```

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

슬롯마다 **목적**을 하나 정한다: `표지` / `소제목 요약` / `절차 장면` / `제품·상품` / `현장` / `작업 장면` / `서류·자격` / `안전` / `시험`(해당 업종만) / `업체 소개(실사진)`.
(목적 단어가 파일명 slug가 된다(`00` 표지는 고정 `00-cover.png`): 표지→cover, 시험→exam, 절차→steps, 제품·상품→product, 현장→scene, 작업→work, 안전→safety, 서류→documents, 업체 소개→business(`NN-business.png`) …)

**유형 판정 규칙(위에서부터 먼저 맞는 것):**
1. 글 유형이 `홍보`(gates.md `## 선택`) → **모든 슬롯 photo**(⑤ "홍보성 글 = 업체 실사진만").
2. 업체 소개(실사진)·이용 안내·매장·현장 실제 모습 슬롯 → **photo**.
3. `photos/`에 그 장면에 맞는 실사진이 있고 **이전 글에서 쓰지 않았다** → 정보성 장면이라도 **photo 우선**.
4. 정보성 장면(작업 과정·제품·도구 사용·절차·서류·안전) → **ai**.

이전 글 사용 여부(⑤ 재사용 금지) 확인:

```bash
grep -ho 'photos/[^ ,|)`]*' work/posts/*/images/image-plan.md 2>/dev/null | sort | uniq -c
```

현재 글 폴더의 행은 빼고 본다. 이미 쓴 실사진은 후보에서 제외한다. 단 `photos/business-intro.png`는 고정 자산이라 재사용 검사에서 제외한다.
⑤에 중간 현장 장면 규칙(예: "본문 중간 절에 현장·작업 장면 최소 1장")이 있으면 만족하는지 확인한다(그 장면이 중간 절 슬롯 중 1개 이상).

## 3. ai 슬롯 프롬프트 작성

`references/prompt-patterns.md`의 장면 패턴(1~7)에서 고르고(`00` 표지 배경은 패턴 1·3·4 중, "표지용 배경 패턴" 절 참고) `{time}`·`{angle}`·`{weather}`를 채운다. 원칙:
- 표의 프롬프트 칸에는 **장면 설명만**(영어 1~2문장, `|` 금지). 공통 접두/접미는 `gen_image.py`가 붙인다 — 중복해 쓰지 않는다.
- 같은 글 안에서 패턴·시간대·앵글이 겹치지 않게 변주한다.
- 글자·숫자·로고·번호판·얼굴 정면이 생길 만한 소재(현수막, 게시판, 영수증·결과지, 차량 번호판)를 장면에 넣지 않는다.
- **학습 규칙(`범주=이미지`)**: 장면·앵글·시간대·인물 비중 같은 규칙(예: "인물보다 사물 위주")을 패턴 선택과 프롬프트에 반영한다. 적용한 id를 기억해 8단계 요약에 적는다.

## 4. photo 슬롯 후보

`photos/` 파일명과 `photos/README.md` 설명(있으면)으로 장면에 맞는 후보 **1~3개**를 고른다(작업 폴더 기준 경로 `photos/…`).
맞는 사진이 없으면 후보 칸에 `(실사진 없음 — 담당자 지정 필요)`라고 쓰고, 홍보 글이 아니면 ai로 바꿀지를 게이트 3 질문거리로 남긴다(유형을 임의로 바꾸지 않는다).

## 5. `images/image-plan.md` 저장 (포맷 고정 — Step 4가 소비)

```markdown
# 이미지 계획 — posts/NNN-slug
| 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수 |
|---|---|---|---|---|---|---|---|
| 00 | 표지(대표) | 표지 | cover | a tidy small bicycle shop interior with a workbench, subject centered … (글자 없는 배경 장면, 예) | 제목: <frontmatter title 그대로>; 줄바꿈: 줄1; 줄2[; 줄3] | images/00-cover.png | |
| 01 | ## 소제목1 | 소제목 요약 | ai | hands checking bicycle tire pressure with a floor pump … | 자전거 타이어 공기압을 확인하는 손(예) | | |
| 02 | ## 소제목2 | 업체 소개(실사진) | photo | photos/매장-01.jpg, photos/매장-02.jpg | 정비 공구가 정리된 매장 작업대(예) | (게이트 3에서 확정) | |
```

- **`00` 표지 행(형식 확정, 셀 안 `|` 금지)**: `| 00 | 표지(대표) | 표지 | cover | <글자 없는 배경 장면 프롬프트, 패턴 1·3·4 중> | 제목: <frontmatter title 그대로>; 줄바꿈: 줄1; 줄2[; 줄3] | images/00-cover.png | <검수> |`
  - `제목:`은 게이트 2에서 확정된 draft-v2.md frontmatter `title`과 **글자 그대로** 같아야 한다. `build_final.py`가 대조해 다르면 "표지 재생성 필요"로 멈춘다.
  - `줄바꿈:`은 줄당 12자 이내 2~3줄(`;`로 구분). make_cover.py `--title`에는 `줄1|줄2`로 넘긴다.
  - `파일` 칸은 항상 `images/00-cover.png`(gen_image.py가 바꾸지 않는다). 배경은 `images/00-bg.png`에 따로 저장된다.
  - **학습 규칙(`범주=표지`)**: 줄바꿈 위치(예: "키워드를 첫 줄에")·줄 수·`--sub` 배지 문구·배경 선택(AI 배경 패턴 / 실사진 배경 우선 등) 규칙을 `줄바꿈:`과 배경 프롬프트(또는 실사진 배경)에 반영한다. 줄당 12자·2~3줄과 `제목:` = frontmatter `title` 규칙은 그대로다(빌더 대조).

- `유형` ∈ {ai, photo}. 칸 안에 `|`를 쓰지 않는다.
- `캡션(alt)`: 한 줄, 무엇을 보여주는지. **내부 메모용이며 본문에 노출되지 않는다(업로드본은 캡션 없음).** "AI 생성" 표기는 ⑤에 규정이 있을 때만 따른다. (`00` 행은 예외로 제목·줄바꿈 지정 칸.)
- `파일` 경로 규칙: ai = **글 폴더 기준** `images/NN-<slug>.png`(gen_image.py가 채움), photo = **작업 폴더 기준** `photos/<파일>`(게이트 3에서 확정 후 메인이 채움). Step 4는 `images/…`는 글 폴더, `photos/…`는 작업 폴더를 기준으로 절대경로를 만든다.
- `검수` 열은 7단계에서 채운다(처음엔 비워 둔다). gen_image.py는 열 이름으로 찾으므로 열이 추가돼도 동작한다.

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
- 실패 슬롯은 stderr에 남고 나머지는 계속된다(exit 1). image-plan.md는 슬롯이 성공할 때마다 저장되므로 중간에 끊겨도 완료분은 남는다.
- **재시도·재생성 한도(한 문장 규칙)**: API 실패 슬롯은 `--only`로 1회 재시도(§6), 검수 불합격 슬롯은 프롬프트를 고쳐 슬롯당 최대 2회 재생성(§7), 한 글의 총 생성 호출은 ai 슬롯 수 × 3 이내.

## 7. 생성 이미지 검수 — 반드시 열어서 본다

ai 슬롯 이미지와 `00-bg.png`·`00-cover.png`를 **Read 도구로 한 장씩 열어** 확인한다(파일 존재만으로 통과시키지 않는다):

| 검사 | 불합격 예 |
|---|---|
| 글자 렌더링 없음 | 간판·제품 문구·번호판·서류 글씨·가짜 한글 (OpenAI GPT 이미지는 글자를 또렷하게 잘 그리므로 제품·벽·안내판·옷의 작은 글자까지 더 꼼꼼히 본다) |
| 얼굴 클로즈업 없음 | 정면 얼굴이 식별되는 인물 |
| 같은 글 안 장면 중복 없음 | 두 슬롯이 같은 구도·같은 시간대 |
| 장면이 캡션·소제목과 맞음 | 실내 작업 설명에 야외 장면 |
| 로고·브랜드 없음 | 제조사 로고, 워터마크 |
| (표지 `00`) 제목 글자 잘림·겹침 없음 | 00-cover.png에서 제목이 가장자리에 걸리거나 배지·전화번호와 겹침 |
| (표지 `00`) 오타 없음 | 표지 제목이 frontmatter `title`과 다름 |
| (표지 `00`) 배경(00-bg.png)에 글자·로고 없음 | 배경에 간판·가짜 글씨·로고 |
| (표지 `00`) 중앙 안전 영역 안 | 피사체·제목이 1:1 크롭에서 잘림 |

판정은 `검수` 열에 `PASS` 또는 `FAIL: <사유>`로 적는다. FAIL이면 프롬프트를 고쳐(원인 소재 제거·앵글 변경) `--only <슬롯>`으로 재생성 — **슬롯당 최대 2회**(§6 한도 규칙). 2회 뒤에도 FAIL이면 `FAIL(2회): <사유>`로 남기고 게이트 3에 올린다(photo 전환 후보로 제안).

## 8. 게이트 3용 요약 (메인으로 반환)

```
이미지 계획: work/posts/NNN-slug/images/image-plan.md
| 슬롯 | 위치 | 유형 | 파일 / 후보 | 검수 |
00 표지 cover images/00-cover.png <검수>
01 ## … ai images/01-<slug>.png PASS
02 ## … photo 후보: photos/매장-01.jpg, photos/매장-02.jpg (선택 필요)
…
특이사항: 슬롯 부족 N개 / 실사진 없음 슬롯 / FAIL(2회) 슬롯 / Gate: 이미지 키 대기 / 제공자: <gemini|openai>
적용 규칙: <3·5단계에서 반영한 L-… 또는 "없음">
```

## 9. 게이트 3 이후는 이 스킬 밖

- 게이트 3 질문(교체·재생성·실사진 지정)과 `gates.md ## 이미지승인` 기록은 blog-run(메인)이 한다. 재생성 요청은 `gen_image.py --only NN`(표지는 `--only 00` 뒤 make_cover.py, 줄바꿈·배지만이면 make_cover.py만) 재실행이며 **디스패치가 아니다**.
- 승인 결과 반영(photo 슬롯 `파일` 확정, `scripts/build_final.py`가 final.md를 만든다, `lint_post.py --stage upload`)은 **blog-run Step 4(메인)** 가 image-plan.md를 기준으로 한다.

## 금칙

- 홍보성 글·업체 소개(실사진) 슬롯에 AI 이미지 금지(⑤).
- 이전 글에서 쓴 실사진·AI 이미지 재사용 금지.
- 이미지에 글자·숫자·로고·번호판·얼굴 클로즈업 금지. 금칙어가 가리키는 장소·표지·암시 장면 금지(금칙어 규칙).
- 이 스킬에서 `draft-v2.md`·`final.md`를 고치지 않는다.
