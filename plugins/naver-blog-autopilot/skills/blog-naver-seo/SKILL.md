---
name: blog-naver-seo
description: Use when the blog post needs Naver SEO polishing — e.g. "SEO 다듬어줘", "네이버 상위노출", "제목 추천", "제목 2안", "태그 뽑아줘", "키워드 넣어줘", "blog-naver-seo", "blog-run B' 단계". Fixes the one core keyword, writes two title options (both with the gate-1 title_region when the profile has 고객 지역), spreads the keyword into headings and body (3~8 times), keeps image slots caption-free, picks 5~10 tags (the source of the closing hashtag line), runs lint_post.py --stage final on draft-v2.md, and records a self-check table in seo.md. Do NOT use for fact verdicts (blog-fact-check), image generation (blog-image-director), or upload (blog-naver-upload).
---

# 네이버 SEO 검토·다듬기

## 왜 이 스킬이 있나

글이 정확해도 제목·소제목·태그가 검색어와 맞지 않으면 노출되지 않는다. 이 스킬은 **사실은 건드리지 않고** 검색 신호만 맞춘다.
기준은 `knowledge/naver-seo-checklist.md`(필수 전부 PASS)이고, 정량 항목은 `lint_post.py`가 센다. 숫자는 **`knowledge/design-system.md` ④가 정본**이다(글자수·본문 소제목 수·이미지 수는 ④ lint 블록 값, 태그 5~10·본문 키워드 3~8회·제목 20~40자는 lint 기본값 — ④에 그 키가 있으면 그 값).

- 수행 주체: **blog-writer 에이전트의 B' 단계**(팩트체크 반영 직후). 사람이 "SEO 다듬어줘"라고 하면 메인이 수행.
- 전제: cwd = 작업 폴더. 지식 파일은 cwd의 `knowledge/`만 읽는다.
- 입력: 작업 중인 `draft-v2.md`(해당 글 폴더), `knowledge/naver-seo-checklist.md`, `knowledge/design-system.md`, topics 표의 해당 행.
- 출력: 수정된 `draft-v2.md` + 같은 폴더의 `seo.md`.
- **학습 규칙**: `knowledge/learned-preferences.md`(있으면) `## 적용 중`의 `범주=제목`(2단계 제목 2안의 형식·말투·길이 배분)·`범주=SEO`(1·3·4·6단계 키워드 배치·태그) 규칙을 따른다. 잠긴 규칙(잠긴 규칙 = `business-profile.md` 금칙어·꼭 지켜야 할 점, `design-system.md` ⑤ 반드시 지킬 것(이미지 속 글자·얼굴 클로즈업·로고 금지, 홍보글은 실사진만, 사진 재사용 금지), ⑧ 지어내기 금지·출처·금칙)과 아래 정량 범위(lint)가 우선이며, 충돌하면 그 범위대로 쓰고 `seo.md` 끝 "메인에 전달"에 한 줄. 적용한 id는 `seo.md` 머리 줄에 `학습 규칙: L-…`(없으면 "없음")로 적는다.

## 절차

1. **핵심 키워드 1개 확정**. topics 표 행의 키워드를 우선 쓴다. frontmatter `keyword:`에 적는다(없으면 추가). 한 글에 키워드는 하나만.
2. **제목 2안**. 둘 다 20~40자(공백 포함), keyword 포함. `business-profile.md`에 `고객 지역`이 있을 때만 **제목 지역(title_region) 지역명 1개**를 넣는다 — 값은 `research.md ## 변주 선택`(= `gates.md ## 선택`의 `제목 지역:`)의 `title_region`이며 frontmatter `variation.title_region`과 같다(lint `title_region`이 A안 `title`을 본다). 다른 고객 지역명을 함께 넣지 않는다. `고객 지역`이 비어 있으면 제목에 지역이 필요 없다(`variation.title_region` = `-`, lint `title_region`은 `SKIP`).
   - A안 = 키워드 전방배치형(키워드가 제목 앞 1/3 안). frontmatter `title:`에 A를 넣는다.
   - B안 = 호기심/질문형. frontmatter는 첫 줄이어야 하므로, 닫는 `---` 바로 다음 줄에 HTML 주석 `<!-- 제목 B안: … -->`으로 적는다(키워드 횟수 계산에서는 주석이 제외된다). 본문 `# ` 제목은 A와 같게 둔다.
   - 낚시 금지: 본문이 답하지 않는 약속은 쓰지 않는다.
3. **소제목**에 키워드를 1~2개 분산하고, "~방법 / ~순서 / ~비용 / ~기준" 형태로 쓴다. 본문 소제목은 ④ `min_h2`~`max_h2`개(`## 📑 목차`·`## 📞`으로 시작하는 문의 헤딩 제외, FAQ 포함)를 유지하고, 키캡 번호(`## 1️⃣ `)는 그대로 둔다. 소제목을 바꾸면 `## 📑 목차` 항목도 같은 텍스트·순서로 맞춘다.
4. **본문 키워드 3~8회**로 조정한다(목차 절·해시태그 줄은 세지 않는다). 문장이 자연스러워야 하며 억지로 넣지 않는다. 고친 문장의 말투는 `business-profile.md` `톤` 행을 따른다(`design-system.md` ②):
   - `톤` = 합니다체: 평서문은 합니다체로 끝낸다. 의문문은 끝이 `~까요?`·`~나요?`·`~ㅂ니까?/~습니까?`·`~인가요?`·`~세요?`면 된다(`~죠?`·`~해요?` 등은 lint `tone` FAIL).
   - `톤` = 해요체: 해요체 종결로 쓰고 합니다체 종결(`~습니다`·`~입니다`·`~됩니다`)을 섞지 않는다. lint `tone`은 그 문장 수를 `WARN`으로만 알린다(pass 영향 없음) — 0에 가깝게 줄인다. 문장을 고쳐도 `(출처: URL)` 단독 괄호를 유지하고 조항·시행일은 문장 본문에 둔다. `[출처](URL)` 링크형 금지(lint `source_format`). **팩트체크 PASS 문장의 사실 내용(수치·일정·조항·출처)은 바꾸지 않는다** — 조사·어순·소제목 표현만 손댄다. 사실 문장이 바뀌면 fact-checker 재발주가 필요하다고 메인에 알린다.
5. **이미지 — 캡션 없음.** 업로드본은 캡션을 쓰지 않는다(`build_final.py`가 `![](경로)`로 alt를 비운다 — lint upload `captions_empty`). 슬롯 `![슬롯: 설명]()` 형태는 그대로 두고, 슬롯 설명은 이미지 단계 내부용이므로 **keyword를 넣거나 캡션용으로 다듬지 않는다**.
6. **태그 5~10개**: 키워드, 지역 2개(`고객 지역`이 있을 때), 상품·서비스명, 주제 키워드 등. frontmatter `tags:` 리스트로 쓴다. 키워드는 반드시 들어가고, `고객 지역`이 있으면 지역 키워드도 반드시 들어간다. 태그는 업로드본 끝 해시태그 줄(`**#태그 #태그 …**`)의 원천이므로(빌더가 공백을 지운다) **공백 없는 형태**(예: `자전거정기점검`, `가나동자전거`)를 권장한다.
7. **정량 확인**:
   ```bash
   python3 scripts/lint_post.py work/posts/<NNN-slug>/draft-v2.md --stage final --json
   ```
   `final` 단계는 draft-v2.md(출처·슬롯 포함본)의 SEO 확인용이다 — 업로드본 final.md는 메인이 `build_final.py` 뒤 `--stage upload`로 따로 본다. draft-v2.md에는 슬롯·관련글 자리표시가 남아 있어 `image_paths`·`related_links` 등은 FAIL일 수 있다. **SEO 항목만 본다**: `title_keyword`, `seo_title_length`, `seo_keyword_body`, `seo_keyword_h2`, `tags_count`, `chars`, `h2_count`, `forbidden`, `tone`, `title_region`, `source_format`. 이 중 FAIL을 고치고 재실행한다(최대 3회). `SKIP`(`title_region` — 고객 지역 없음)과 `WARN`(`tone` — 해요체 블로그의 합니다체 문장 수)은 FAIL이 아니다 — WARN은 줄일 수 있으면 줄이고 값을 `seo.md`에 옮긴다. 나머지 FAIL은 후속 단계 몫이라고 `seo.md`에 적는다(`seo_image_captions`는 보지 않는다 — 업로드본은 캡션이 없다).
8. **셀프 체크표**를 `seo.md`에 쓴다. 체크리스트 필수 항목마다 한 행, 열은 `id | 결과(PASS/수정) | 근거`. lint 항목(제목-지역 = lint `title_region`(고객 지역이 없으면 `SKIP` 그대로), 톤 = `tone`, 출처 형식 = `source_format` 포함)은 lint 값을 옮기고, "사람" 항목(제목-위치, 제목-지역의 B안 확인(고객 지역이 있을 때만), 사진 원본성, 태그의 키워드·지역 포함, 원본성-출처의 복붙 여부, 원본성-변주, 주제 일관성)은 직접 판단해 근거를 쓴다. 근거 없이 PASS를 쓰지 않는다.

## seo.md 형식

```markdown
# SEO 채점 — <글 제목 A안>
키워드: <keyword> · 제목 A: … · 제목 B: …
학습 규칙: <적용한 L-… 또는 "없음">

| id | 결과 | 근거 |
|---|---|---|
| 제목-키워드 | PASS | lint title_keyword |
| 제목-위치 | PASS | 키워드가 제목 앞 1/3(…번째 글자)에 있음 |
| 제목-지역 | PASS | lint title_region(A안, '<지역>') + B안에도 '<지역>' 1개 포함 (고객 지역이 없으면: `SKIP` · lint title_region SKIP(고객 지역 없음)) |
| 톤 | PASS | lint tone 0건(톤=합니다체) (톤=해요체면: `PASS` · lint tone WARN <n>건) |
| 출처 형식 | PASS | lint source_format(출처: n건 = 단독 괄호 n건) |
| …필수 항목 전부… | | |

lint(final) 대상 외 FAIL: image_paths, related_links (draft 단계, 후속 단계에서 해결)
```

## 하지 말 것

- 키워드를 3~8회 밖으로 밀어 넣기, 키워드 나열형 문장.
- 팩트체크를 통과한 사실 문장 수정.
- 이미지 생성·경로 치환·업로드 수행(각각 blog-image-director·메인·blog-naver-upload 몫).
- 사용자(담당자)에게 직접 묻기 — 서브에이전트로 돌 때는 판단이 필요한 항목을 `seo.md` 끝 "메인에 전달"에 적는다.
