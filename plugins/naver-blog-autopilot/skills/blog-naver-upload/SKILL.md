---
name: blog-naver-upload
description: Use when a finished blog post (posts/NNN-slug/final.md, gate 3 passed) must be saved to Naver Blog as a draft — e.g. "네이버에 올려줘", "임시저장", "업로드", "네이버 임시저장해줘", "blog-naver-upload", "blog-run 업로드 단계", "blog-run Step 5". Runs scripts/naver_upload.sh (lint --stage upload → session check → naver-blog-cli create-draft-from-folder with cover as 대표이미지 → list-drafts confirm), then records gates.md and work/variation-log.md. Do NOT use for pressing the publish button (the human publishes), deleting drafts or posts, editing already-uploaded posts, or writing/revising text (blog-draft-writer) or images (blog-image-director).
---

# 네이버 임시저장 업로드

`final.md`를 네이버 블로그 **임시저장**까지만 올린다. 발행은 담당자가 네이버 앱/웹에서 미리보기를 보고 직접 한다.
에디터 조작은 외부 CLI `naver-blog-cli`에만 위임하고(명령·출력 문구: `references/naver-blog-cli.md`), 이 스킬은 Playwright 코드를 쓰지 않는다.

- 수행 주체: **메인 세션이 직접**. 서브에이전트에 맡기지 않는다 — 로그인 만료·2차 인증·CAPTCHA·브라우저 창 개입이 생길 수 있다.
- 전제: cwd = 작업 폴더, 게이트 3(이미지 승인) 통과, `work/posts/NNN-slug/final.md` 존재(frontmatter `title/category/tags/variation`, 이미지 절대경로, 실제 관련글 URL, 출처·캡션 없음, 프로필 `마무리 블록` 행에 든 항목의 마무리 블록 포함)와 같은 폴더의 `images/00-cover.png`(표지).
- 이 스킬은 사용자에게 묻지 않는다. 종료 보고는 `/naver-blog-autopilot:blog-run`이 한다.

## 절차

1. 실행 (작업 폴더에서, `/naver-blog-autopilot:blog-run` Step 5와 같은 형식). `<blogId>`는 blog-run Step 0의 `blogId:` 값(작업 폴더 `.env`의 `NAVER_BLOG_ID` — `knowledge/source-blogs.json`의 `own_blog.blogId`와 같은 값)이다. 스크립트는 `--blog-id`(없으면 `.env`의 `NAVER_BLOG_ID`)로 블로그 ID를 정하고, 둘 다 없으면 멈춘다(기본값 없음). `lint_post.py`도 `--blog-id`를 받으며 그 값을 `.env`보다 우선한다 — 업로드본 lint의 관련글 링크 판정(`related_links`)도 업로드 대상과 같은 블로그 ID 기준이다. 카테고리는 frontmatter `category` 또는 `--category "이름"` 중 하나가 꼭 있어야 한다(기본값 없음).

   먼저 dry-run으로 title/category/tags/이미지 수·이미지 경로를 확인한다(lint·frontmatter·본문·이미지 검사만 하고 세션 확인과 업로드는 생략하므로 로그인 없이 가능):

   ```bash
   bash scripts/naver_upload.sh work/posts/<NNN-slug>/final.md --blog-id <blogId> --dry-run 2>&1; echo "exit=$?"
   ```

   결과를 담당자에게 보여 주고, exit 0일 때만 실제 임시저장을 따로 실행한다:

   ```bash
   bash scripts/naver_upload.sh work/posts/<NNN-slug>/final.md --blog-id <blogId> 2>&1; echo "exit=$?"
   ```

   스크립트가 하는 일, 순서대로: ⓪ 프로필 `마무리 블록` 읽기(`lint_post.load_closing_blocks("knowledge")` 한 줄 — 실패하면 `프로필 마무리 블록을 읽지 못했습니다 — <사유>`, exit 2) → ① 표지 `images/00-cover.png` 확인(없으면 exit 12) → ② `lint_post.py --stage upload`(업로드 대상과 같은 블로그 ID 기준) + 이중 검사(금칙어·`[[`·빈 이미지·`[출처 필요]`·`출처:` 잔존·alt 있는 이미지·`**#` 해시태그 줄 부재(항상), `:::place` 부재(`마무리 블록`에 `장소카드`가 있을 때만 — `:::place 지시문 없음 — scripts/build_final.py 재실행`), `photos/business-intro.png` 존재(`소개이미지`가 있을 때만)) → ③ frontmatter 읽기 → ④ 임시 작업 폴더에 `body.md`(frontmatter·첫 `# ` H1·`<!-- 제목 B안/A안 … -->` 주석 제거; 본문 이미지는 절대경로 그대로)와 `images/00-cover.png` 복사본 생성, 본문 이미지 절대경로 확인(`--dry-run`은 여기서 종료; 표지 경로 출력. `[dry-run] 장소 지시문: …` 줄은 `마무리 블록`에 `장소카드`가 있을 때만 나온다 — 없으면 이 줄이 없는 것이 정상) → ⑤ `naver-blog-cli check-session` + 계정 확인(`check_blog_account.py` — naver-blog-cli의 uv tool python으로 글쓰기 화면을 열어 URL의 블로그 주인이 `--blog-id`인지 본다. 다른 계정 세션이면 `check-session`은 통과해도 여기서 exit 21. 글은 쓰지 않는다) → ⑥ `create-draft-from-folder <임시폴더> --markdown-file body.md --title --category --tags`(표지는 CLI가 본문 맨 앞에 캡션 없이 넣고 대표로 지정) → ⑦ 출력 노트에서 대표 지정 결과·`장소(…)` 값(`장소카드`일 때만)을 확인하고, `list-drafts`에 제목이 보이는지 확인 → `work/posts/NNN-slug/upload.log`에 기록.
   창이 뜨고 글 하나에 수 분 걸린다. CAPTCHA가 뜨면 담당자에게 창을 직접 처리하도록 알린다.

2. 종료 코드별 대응:

   | 코드 | 의미 | 대응 |
   |---|---|---|
   | 0 | 임시저장 완료 | 아래 3 진행 |
   | 10 | `lint_post.py --stage upload` 실패(실패 항목 출력됨) | 텍스트 id(`tone`·`title_region`·`source_format` 등) → blog-writer를 `SendMessage`로 재개(B', 최대 1회). `image_paths`·`images`·`cover_file` → Step 3/게이트 3(`make_cover.py` 재실행 등 이미지 단계). 빌더 id(`sources_stripped`·`captions_empty`·`closing_block`·`h2_spacing`) → 중단하고 보고(`build_final.py` 버그). `final.md`는 손으로 고치지 않는다 |
   | 11 | 이중 검사 실패(금칙어·`[[`·빈 이미지·`[출처 필요]`·`[출처](` 링크형·`출처:` 잔존·alt 있는 이미지·`**#` 줄 부재·`:::place` 줄 부재(`장소카드`일 때만)) | lint를 통과했는데 걸렸다면 lint 규칙 구멍이다 — 중단하고 담당자에게 한 줄 보고(`final.md`는 손으로 고치지 않고, 원인 단계(B'·`build_final.py`)를 다시 실행) |
   | 12 | 표지 `images/00-cover.png` 없음 / 본문 이미지 경로가 절대경로가 아니거나(URL 포함) 파일이 없음 | 표지 없음: 이미지 단계(`make_cover.py`) 재실행. 경로 문제: `scripts/build_final.py` 재실행 |
   | 20 | 세션 없음/만료 또는 `naver-blog-cli` 없음, 계정 확인 실패 | 담당자에게 로그인 안내: 작업 폴더에서 `NAVER_STATE`를 주고 naver-blog-cli 도구 python으로 `~/naver-blog-cli/login_setup.py` 실행 — macOS 터미널 `"$(uv tool dir)/naver-blog-cli/bin/python"`, Windows PowerShell `& "$(uv tool dir)\naver-blog-cli\Scripts\python.exe" "$HOME\naver-blog-cli\login_setup.py"`(전체 명령은 `/naver-blog-autopilot:blog-setup` 4단계·README), **"로그인 상태 유지" 체크**. 로그인은 사람만 한다. 끝나면 같은 명령 재실행 |
   | 21 | 로그인한 계정이 `--blog-id` 블로그에 글을 쓸 수 없음 — 세션은 살아 있으나 다른 계정(글쓰기 화면이 그 계정 블로그로 리다이렉트). 임시저장은 시도하지 않음 | `확인 결과:` 줄의 이동 주소를 담당자에게 보여 주고 **대상 블로그 계정으로** 다시 로그인하도록 안내(위 20과 같은 `login_setup.py`, 사람이 직접, 기존 세션 파일을 덮어씀). `--blog-id` 값 자체가 틀렸는지도 확인. 끝나면 같은 명령 재실행 |
   | 30 | `create-draft-from-folder` 실패(`넣기 전에 걸린 것`·`작성 실패`·`임시저장이 안 된 것 같습니다`·`…을 못 찾음`·그 외 출력) | 출력 tail의 CLI 문구를 `references/naver-blog-cli.md`의 실패 유형과 대조: `넣기 전에 걸린 것`(이미지 없음·10MB 초과 — 브라우저 열기 전이라 임시저장 안 됨) · 에디터 개편(`…을 못 찾음`) · 세션 만료. 임시저장 수가 늘었을 수 있으니 `list-drafts`/네이버에서 중복 여부를 확인한 뒤 재시도 |
   | 31 | 저장은 끝났으나 목록에서 제목 확인 불가 | 저장됐을 수 있다. 담당자에게 "네이버 → 글쓰기 → 임시저장 글"에서 직접 확인을 요청하고, 있으면 성공으로 처리 |
   | 2 | 사용 오류(경로·frontmatter) · 프로필 `마무리 블록`을 읽지 못함 | 인자와 `final.md` frontmatter 확인. `프로필 마무리 블록을 읽지 못했습니다 — …`면 `python3 scripts/check_profile.py`로 확인하고 `/naver-blog-autopilot:blog-onboard`로 채운다 |

   같은 오류로 재시도는 한 번까지. 반복 실패하면 멈추고 담당자에게 보고한다(계정 안전).

3. 성공 시 기록 (메인이 직접):
   - `work/posts/NNN-slug/gates.md`의 `## 업로드`에 일시·제목·`upload.log` 경로 추가.
   - `work/variation-log.md`에 한 줄 추가. 형식 7열 `YYYY-MM-DD | posts/NNN-slug | type | structure | intro | region | title_region`, 값은 `final.md` frontmatter `variation`에서(`type`은 게이트 1에서 고른 정보/홍보, `region`은 `가나동+다라동`처럼 `+`로 연결, `title_region`은 제목에 넣은 지역 1개 — `고객 지역`이 비어 있는 블로그는 `region`·`title_region` 둘 다 `-`. 아래 줄은 가상 예):

     ```
     2025-03-14 | posts/001-자전거-정기-점검-순서 | 정보 | 절차형 | 상황 | 가나동+다라동 | 가나동
     ```
   - 성공 기록 3에 추가: 대표 지정 결과(`대표 지정` 성공 / 아래 경고)를 `gates.md ## 업로드`에 적는다. 프로필 `마무리 블록`에 `장소카드`가 있을 때만 스크립트 성공 출력의 `장소: …`(노트 `장소(…)` 값)도 적는다 — 이때 CLI가 고른 `장소`에 업체명이 없으면 `경고: 장소 카드 확인 필요 — <값>`이 stderr에 나온다 → 성공 보고에 "미리보기에서 장소 카드가 우리 업체인지 확인" 안내를 넣는다(필요하면 `business-profile.md`의 `장소 검색어`를 `<업체명> <지역>`처럼 좁혀 재업로드).
   - 스크립트 출력에 `경고: 대표이미지 지정 실패` 또는 `경고: 대표이미지 지정 확인 불가`가 있으면(저장은 됐고 exit 0) 성공 보고에 "임시저장 글에서 첫 이미지(표지)를 대표로 직접 지정" 안내를 포함한다.
   - 스크립트 출력에 `경고: 카테고리/태그 설정 실패`가 있으면 성공 보고에 반드시 "카테고리·태그 직접 확인" 안내를 포함한다(임시저장은 됐지만 설정이 빠졌을 수 있다).
   - 담당자에게 안내: "네이버 앱/웹 → 글쓰기 → 임시저장 글 → 미리보기에서 첫 이미지(표지)에 '대표' 표시가 있는지 확인 → 발행". 대표이미지 = 표지(`00-cover`).

## 계정 안전 수칙

- 자동화는 **임시저장만**. `publish-draft`·`delete-draft`·`delete-post`는 호출하지 않는다.
- 하루 1~2편 이내. 같은 날 연속 업로드·재시도를 늘리지 않는다.
- `playwright-state/storage_state.json`은 계정 접근권한이다. 출력·커밋·공유 금지.

## 폴백 (2차)

CLI가 네이버 에디터 개편으로 계속 `…을 못 찾음`을 내면, 담당자 승인 아래 aside(AI 브라우저)에 `final.md`와 `images/`를 주고 **"임시저장까지만, 발행 금지"**로 수동 지시한다. 이 경로에서도 로그인·2FA는 담당자가 한다.
