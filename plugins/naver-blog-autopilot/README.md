# naver-blog-autopilot

네이버 블로그의 **정보성 글**을 만드는 Claude Code 플러그인입니다. 주제 리서치 → 디자인 시스템 기준 초안 → 법령·공공기관 근거 검토 → 네이버 SEO 다듬기 → 이미지·대표이미지(표지) 합성 → 업로드본 빌드 → 네이버 **임시저장**까지 진행하고, **발행은 사람(담당자)이 네이버에서 직접** 합니다. 이 플러그인은 발행 버튼을 누르지 않습니다.

업종에 묶이지 않습니다. 업체명·연락처·고객 지역·금칙어·업종별 공신 출처 같은 업체 고유 정보는 작업 폴더 `knowledge/`의 템플릿에 채워 씁니다(아래 [처음 채울 것](#처음-채울-것)).

## 설치

Claude Code 입력창에서 차례로 실행합니다.

```
/plugin marketplace add heesun-woodi/woodi-claude-plugins
/plugin install naver-blog-autopilot@woodi-claude-plugins
/naver-blog-autopilot:blog-setup
```

`blog-setup`은 작업 폴더를 준비하고 환경을 진단합니다. 작업 폴더를 어디에 만들지, OS별 준비는 아래 [설치와 첫 사용](#설치와-첫-사용)을 따릅니다. 업데이트는 `/plugin marketplace update woodi-claude-plugins` 뒤 `/plugin` → 설치된 플러그인에서 naver-blog-autopilot를 업데이트합니다.

네이버 임시저장은 외부 도구 **naver-blog-cli**가 맡습니다. 이 플러그인에는 들어 있지 않으니 [사전 요구사항](#사전-요구사항)대로 따로 설치합니다.

- naver-blog-cli: https://github.com/spegas/naver-blog-cli — MIT 라이선스(Copyright (c) jjorae / Johnhyeon / spegas), 원저작 `Johnhyeon/naver-blog-mcp` 계열. 이 플러그인은 그 CLI를 호출만 하고, 에디터 조작 코드는 새로 쓰지 않습니다.

## 왜 이렇게 만들었나

**소스를 먼저 정의합니다.** 글의 품질은 무엇을 보고 따라 쓰느냐에서 갈립니다. 주제는 같은 업종의 참고 블로그(주제 소스)에서 찾고, 글의 모양은 담당자가 "왜 좋은지"를 적어 준 레퍼런스 글에서 가져옵니다(구성·강조·자연스러운 흐름·소제목마다 이미지 한 장·사진과 글의 비율 같은 메모). 이 목록은 작업 폴더 `knowledge/source-blogs.json`에 있고, 바꾸고 싶으면 거기서 고칩니다.

**디자인 시스템 문서 한 장이 정본입니다.** 레퍼런스(자기 글 0번 + 담당자가 고른 글)에서 잰 수치(글자 수 범위·본문 소제목 수·이미지 수·이미지 한 장당 글자 수·굵게 빈도·표·인용 수)와 골격·말투(합니다체)·이미지·마무리 블록·변주 규칙을 `knowledge/design-system.md`에 모아 둡니다. 고정 골격은 도입 2문단 → `## 📑 목차` → `## 1️⃣`… 번호 소제목(표 0~1개·✔️ 이모지 줄·💡 팁 줄) → FAQ → 관련글 2~3개 → `## 📞 문의 안내: <연락처>`입니다. 정본은 **작업 폴더의 `knowledge/` 하나뿐**입니다. 플러그인의 `scaffold/knowledge/`는 설치할 때 한 번 복사되는 초기값(템플릿)이고, 이후에는 담당자가 작업 폴더에서 직접 고칩니다. 스킬과 에이전트는 항상 작업 폴더의 `knowledge/`만 읽습니다.

**쓰는 쪽과 검토하는 쪽을 분리합니다.** 글은 `blog-writer` 에이전트가 쓰고, 사실 검토는 `blog-fact-checker` 에이전트가 따로 합니다. fact-checker는 Edit 도구가 없어 초안을 고치지 못하고 `factcheck.md` 리포트만 씁니다. 쓴 쪽이 자기 글을 승인하지 못하게 하려는 구조입니다. 사용자에게 묻는 일(게이트 3개)은 전부 메인 세션이 하고, 에이전트끼리는 파일 경로로만 넘깁니다. 수치·일정·수수료·법령 조항은 출처 URL이 없으면 초안에 넣지 않습니다. 근거는 `knowledge/official-sources.md`에 등록한 업종별 공신 출처(법령 DB·공공기관·업체 프로필)에서 확인하고, 판정은 PASS / FAIL / 출처필요 / 시점확인 넷 중 하나입니다.

**결정적인 검사는 스크립트가, 판단은 모델이 합니다.** 금칙어, 자리표시(`[[`) 잔존, 빈 이미지 경로, `[출처 필요]` 잔존, 분량, 소제목 수, 이미지 수, 출처 수와 형식(`(출처: URL)` 단독 괄호), 해요체 종결, 제목 지역명, 업로드본의 출처·캡션 제거·표지·마무리 블록·소제목 여백은 `lint_post.py`가 셉니다(`draft`·`final`·`upload` 세 단계). 업로드본 변환은 `build_final.py`가 기계적으로 하고, 업로드 스크립트 `naver_upload.sh`가 같은 핵심 검사를 한 번 더 합니다. 금칙어는 `knowledge/business-profile.md`의 목록(계약·브랜드상 쓰면 안 되는 표현)이고, lint가 공백을 무시하고 비교해 막습니다. 목록 밖이라도 그 뜻을 돌려 말하는 문장은 writer가 쓰지 않고 fact-checker가 FAIL로 잡습니다.

**변주가 요구사항입니다.** 네이버는 복붙·사진 재사용·날짜만 바꾼 반복 글을 낮게 평가합니다. 그래서 글마다 본문 전개 방식(절차형/비교형/체크리스트형/Q&A형), 도입부 유형, 지역 키워드 2개(`business-profile.md`의 `고객 지역`), 제목 지역 1개를 `work/variation-log.md` 최근 5줄과 다르게 고르고(4축 중 2개 이상 다르게), 업로드가 성공할 때마다 로그에 7열 한 줄(`날짜 | 글 | type | structure | intro | region | title_region`)을 더합니다. 제목 지역은 `고객 지역` 순서에서 최근 4편에 안 쓴 첫 지역을 고르는 로테이션입니다. 마무리는 변주하지 않고 고정 블록입니다.

**임시저장까지만 자동입니다.** 네이버 블로그 글쓰기 공식 API는 종료됐습니다. 그래서 오픈소스 `naver-blog-cli`가 Playwright로 스마트에디터ONE을 조작하는 경로를 쓰는데, 이 도구도 "과도하게 쓰면 계정이 제재될 수 있다"고 경고합니다. 업로드 스크립트는 `NAVER_BLOG_READONLY=1`을 켜서 발행·삭제 명령이 CLI에서 아예 빠지게 합니다. 에디터 조작 코드는 새로 쓰지 않고 `naver-blog-cli`에만 맡깁니다.

## 처음 채울 것

`/naver-blog-autopilot:blog-setup`이 복사해 주는 `knowledge/` 파일은 `[…]` 자리가 비어 있는 템플릿입니다. 첫 글 전에 자기 업체 값으로 채웁니다. 스크립트는 업체 값을 기본값으로 지어 넣지 않으므로, 필요한 행이 비어 있으면 오류 메시지를 내고 멈춥니다(exit 2).

- `knowledge/business-profile.md` — 업체 기본정보 표: 필수 행 `업체명`·`연락처`·`상품·서비스`·`고객 지역`·`장소 검색어`·`업체 유형어`(제목에서 지울 업체 유형 표현)·`업종 일반어`(겹침 계산에서 뺄 흔한 단어), 업체 정보 행 `주소`·`제공 방식`·`지원 형태`(스크립트는 확인하지 않지만 글·팩트체크가 업체 정보 근거로 씁니다 — 비우면 그 주장은 출처필요), 선택 행 `배지 문구`·`제목 정규화`·`홍보 표지어`·`공지 표지어`·`브랜드 색`. 그리고 `## 금칙어` 절(필수 — 계약·브랜드상 쓰면 안 되는 표현, 공백 무시 비교. 금칙어가 없으면 `- 없음` 한 줄, 비워 두면 lint가 멈춥니다), 꼭 지켜야 할 점, 홍보/정보 비율. 필수 행과 `## 금칙어`는 `scripts/check_profile.py`가 확인합니다(`blog-setup`과 `blog-run` Step 0이 실행 — 비어 있으면 `profile: MISSING <행>`). `고객 지역`의 순서가 제목 지역 로테이션 순서이고, `장소 검색어`가 글 끝 `:::place` 장소 카드가 됩니다. `배지 문구` 행이 없으면 표지에 배지를 그리지 않습니다.
- 작업 폴더 `.env`의 `NAVER_BLOG_ID=` — 글을 올릴 블로그 ID(`blog.naver.com/<여기>`). lint의 final·upload 단계와 업로드 스크립트가 읽습니다. `/naver-blog-autopilot:blog-setup`이 값을 물어 적어 줍니다.
- `knowledge/source-blogs.json` — `own_blog`(자기 블로그 ID `blogId`(`.env`의 `NAVER_BLOG_ID`와 같은 값)와 카테고리), `topic_sources`(주제 소스 블로그와 카테고리), `design_references`(레퍼런스 글과 "왜 좋은지" 메모 — 자기 글 1편은 `role: "own-style"`로 레퍼런스 0).
- `knowledge/official-sources.md` — 업종별 공신 출처(법령 DB·공공기관·업체 프로필)와 주장 유형별 조회처·접근성 기록. 팩트체크가 이 파일을 조회처의 정본으로 씁니다.
- `knowledge/design-system.md` — 처음에는 템플릿입니다. 레퍼런스와 자기 글을 재서 수치를 정하는 방법은 `blog-design-system` 스킬과 그 템플릿의 「자기 블로그 기준 측정 절차」에 있습니다.
- `photos/business-intro.png` — 업체소개 이미지(업체명·연락처·주소). 모든 글 끝 마무리 블록에 들어가는 고정 자산입니다.

## 사전 요구사항

macOS와 Windows에서 씁니다. Windows는 먼저 [Windows에서 쓰기](#windows에서-쓰기)를 보세요. 아래 명령 중 OS마다 다른 것은 **macOS:**(터미널) / **Windows:**(PowerShell)로 나눠 적었습니다.

**자기 블로그에 발행한 글 2편 이상.** 업로드본 lint의 `related_links`는 자기 블로그 글 링크 2개 이상을 요구하는 하드 게이트이고, 디자인 시스템은 자기 글 1편을 레퍼런스 0(겉모습 기준)으로 잽니다. 새 블로그라면 처음 2편은 네이버에서 직접 써서 발행해 두세요 — 그 전에는 관련글 단계(B'의 관련글 링크 치환·업로드본 lint)에서 멈춥니다.

**naver-blog-cli 설치.** 네이버 임시저장은 외부 도구 [naver-blog-cli](https://github.com/spegas/naver-blog-cli)(MIT)에 맡깁니다. uv와 Python 3.11 이상이 있으면 한 줄입니다.

```bash
uv tool install git+https://github.com/spegas/naver-blog-cli
```

설치되면 `naver-blog-cli`가 `~/.local/bin`(Windows는 `%USERPROFILE%\.local\bin`)에 생깁니다(PATH에 없으면 `uv tool update-shell`). 브라우저 조작용 Playwright Chromium이 없다면 설치합니다.

- macOS: `"$(uv tool dir)/naver-blog-cli/bin/playwright" install chromium`
- Windows: `& "$(uv tool dir)\naver-blog-cli\Scripts\playwright.exe" install chromium`

로그인 스크립트 `login_setup.py`는 이 설치에 들어 있지 않으므로 저장소를 한 번 clone해 둡니다: `git clone https://github.com/spegas/naver-blog-cli ~/naver-blog-cli`(Windows PowerShell: `git clone https://github.com/spegas/naver-blog-cli "$HOME\naver-blog-cli"`).

**로그인은 1회, 사람이 직접.** **터미널**(Windows는 PowerShell, Claude 입력창 아님)에서 작업 폴더로 이동한 뒤 아래 명령을 실행하면 브라우저가 열립니다.

macOS:

```bash
cd ~/naver-blog-work
NAVER_STATE="$PWD/playwright-state/storage_state.json" \
  "$(uv tool dir)/naver-blog-cli/bin/python" ~/naver-blog-cli/login_setup.py
```

Windows (PowerShell):

```powershell
cd ~\naver-blog-work
$env:NAVER_STATE = "$PWD\playwright-state\storage_state.json"; & "$(uv tool dir)\naver-blog-cli\Scripts\python.exe" "$HOME\naver-blog-cli\login_setup.py"
```

직접 로그인하고, **로그인 버튼을 누르기 전에 "로그인 상태 유지"를 체크**하세요(체크하지 않으면 몇 시간 뒤 글쓰기만 로그인 페이지로 바뀝니다). CAPTCHA·2차 인증도 사람이 처리합니다. 비밀번호는 어디에도 저장되지 않고 쿠키 파일(`playwright-state/`)만 남으며, 이 파일은 계정 접근권한 그 자체이니 공유하지 마세요. 세션이 만료되면 같은 명령을 다시 실행합니다.

**블로그 ID와 카테고리.** 글을 올릴 블로그 ID(`blog.naver.com/<여기>`)는 두 곳에 같은 값으로 적습니다 — 작업 폴더 `.env`의 `NAVER_BLOG_ID=`(lint final·upload 단계와 업로드 스크립트가 읽음, `/naver-blog-autopilot:blog-setup`이 물어 적어 줌)와 `knowledge/source-blogs.json`의 `own_blog.blogId`(스킬이 읽음). `/naver-blog-autopilot:blog-run`은 두 값이 없거나 다르면 시작하지 않고, 같으면 그 값을 `naver_upload.sh --blog-id`로 넘깁니다. 스크립트를 직접 돌릴 때 `--blog-id`가 없으면 `.env`의 `NAVER_BLOG_ID`를 씁니다. `lint_post.py`도 `--blog-id`를 받으며, 주면 `.env`보다 우선합니다. 카테고리는 `final.md` frontmatter `category` 또는 `--category` 중 하나가 꼭 있어야 합니다(블로그 ID·카테고리 모두 기본값이 없습니다).

**이미지 AI 키(Gemini 또는 OpenAI 중 하나).** 글에 넣을 AI 이미지는 **Gemini**(Google AI Studio) 또는 **OpenAI**(GPT 이미지) 중 담당자가 가진 키 하나로 만듭니다. `/naver-blog-autopilot:blog-setup`이 키가 없으면 어느 쪽을 쓸지 한 번 묻고, `.env`의 `IMAGE_PROVIDER=` 줄을 적은 뒤 그 제공자의 발급 안내만 보여 줍니다. 키를 넣으면 `scripts/check_image_key.py`가 비용 없이 키와 모델 사용 가능 여부를 확인합니다(이미지를 만들지 않으며 키 값은 출력하지 않음).

- **Gemini**: https://aistudio.google.com/apikey 에서 발급합니다. **결제(Billing)가 설정된 Google Cloud 프로젝트의 키여야 이미지 생성이 됩니다**(무료 키는 429 쿼터 초과로 실패합니다). 기본 모델 `gemini-3-pro-image`, 장당 약 $0.04(추정치, [비용](#비용) 참고).
- **OpenAI(GPT 이미지)**: https://platform.openai.com/api-keys 에서 발급합니다. 결제 수단(Billing)이 등록돼 있어야 하고, GPT 이미지 모델은 **조직 인증(Verify Organization)**이 필요할 수 있습니다(https://platform.openai.com/settings/organization/general) — 키 확인이 통과해도 이미지 생성에서 403이 나면 조직 인증입니다. 기본 모델 `gpt-image-2`, 비용은 OpenAI 요금 페이지에서 확인합니다.

어느 쪽을 쓸지는 `IMAGE_PROVIDER`(gemini|openai, 선택) > `GEMINI_API_KEY`가 있으면 Gemini > `OPENAI_API_KEY`가 있으면 OpenAI 순으로 정합니다. 읽는 곳 — 키: API 키(GEMINI_API_KEY/OPENAI_API_KEY)가 든 첫 .env 파일의 값. 어느 파일에도 없으면 환경변수. IMAGE_PROVIDER·IMAGE_MODEL: 키를 찾은 .env의 값(그 파일에 없으면 미지정). 키를 환경변수에서 읽을 때는 항목마다 cwd .env → 환경변수 중 처음 값이 있는 곳. `IMAGE_PROVIDER`를 적었는데 그 제공자의 키가 비어 있으면 오류로 알려 줍니다. 모델을 바꾸려면 `IMAGE_MODEL=`(선택)을 씁니다. `/naver-blog-autopilot:blog-setup`이 `.env.example`을 복사해 주므로 값만 채우면 됩니다. 키는 **채팅에 붙여넣지 말고** `.env` 파일에 직접 넣고(macOS: `open -e ~/naver-blog-work/.env`, Windows PowerShell: `notepad "$HOME\naver-blog-work\.env"`), `.env`는 커밋하지 마세요.

```
# 선택 — gemini 또는 openai. 비우면 들어 있는 키로 정함
IMAGE_PROVIDER=gemini
# Gemini를 쓸 때
GEMINI_API_KEY=여기에_키
# OpenAI를 쓸 때
OPENAI_API_KEY=여기에_키
```

키가 없어도 `/naver-blog-autopilot:blog-run`은 중단되지 않고 "키 없음 모드"로 진행합니다. 이 경우 AI 이미지 슬롯은 `보류`가 되고 실사진 슬롯만 처리됩니다. 단 `photos/`의 실사진이 디자인 시스템의 이미지 수 하한(`min_images`)보다 적으면 **임시저장까지 가지 못합니다**. 시작할 때 "초안까지만 진행"할지 묻고, 이미지 단계(Step 3) 뒤에서 멈춥니다. 키나 실사진을 준비한 뒤 `/naver-blog-autopilot:blog-run resume <NNN>`으로 이어 갑니다.

**업체 실사진 폴더.** 매장·작업·제품 사진을 작업 폴더의 `photos/`에 넣어 두세요. 홍보성 글의 이미지는 실사진만 쓰고, 정보성 글은 AI 이미지를 쓰되 실사진이 맞는 슬롯에는 이 폴더의 사진이 매칭됩니다. 이전 글에 쓴 사진은 다시 쓰지 않습니다.

**`photos/business-intro.png`(필수).** 모든 글 끝 마무리 블록에 들어가는 업체소개 이미지(업체명·연락처·주소)입니다. 파일명 그대로 `photos/`에 두어야 하며, 이 파일만은 매 글 재사용합니다. 없으면 `/naver-blog-autopilot:blog-run`이 시작하지 않습니다.

**한글 폰트(표지 합성용).** `make_cover.py`는 Pretendard(`Pretendard-ExtraBold.otf`·`Pretendard-SemiBold.otf`, https://github.com/orioncactus/pretendard/releases)를 먼저 쓰고, 없으면 OS 기본 한글 글꼴로 대신합니다. 하나도 없으면 추측 렌더 없이 멈춥니다.

- macOS: Pretendard를 `~/Library/Fonts/`에 넣습니다. 없으면 `/System/Library/Fonts/AppleSDGothicNeo.ttc`.
- Windows: Pretendard 파일을 우클릭 → "설치"(`%LOCALAPPDATA%\Microsoft\Windows\Fonts` 또는 `C:\Windows\Fonts`). 없으면 기본 맑은 고딕 Bold `C:\Windows\Fonts\malgunbd.ttf`.

**uv·Python·Chromium.** `uv`가 있어야 하고, 작업 폴더의 스크립트용으로 `python3` 3.11 이상이 필요합니다(스크립트는 표준 라이브러리만 쓰고, 이미지 생성은 `uv run --with google-genai --with pillow`(OpenAI 경로는 추가 패키지 없음, 명령은 같음), 표지 합성은 `uv run --with pillow`로 패키지를 그때 받습니다 — 시스템 `python3`에 Pillow를 설치할 필요가 없고, 대신 `uv`가 꼭 있어야 합니다). Playwright Chromium은 위 설치 안내를 따릅니다. Windows의 `python3`는 [Windows에서 쓰기](#windows에서-쓰기)를 보세요. `/naver-blog-autopilot:blog-setup`이 이 항목들을 한 번에 진단해 줍니다.

## Windows에서 쓰기

담당자 PC가 Windows여도 그대로 씁니다. Claude Code의 Bash 도구는 Windows에서 **Git Bash**로 돌고, 플러그인의 셸 블록·스크립트가 Git Bash 기준으로 macOS와 같이 동작합니다. 아래 명령은 전부 **PowerShell 창**(시작 → "PowerShell")에서 실행합니다.

1. **Git for Windows (필수, 가장 먼저).** https://git-scm.com/downloads/win 에서 설치합니다. 없으면 Bash 도구가 PowerShell로 돌아 이 플러그인이 동작하지 않습니다(`/naver-blog-autopilot:blog-setup`이 첫 단계에서 멈춥니다).
2. **Claude Code.** `irm https://claude.ai/install.ps1 | iex`
3. **uv.** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
4. **python3.** Windows에 기본으로 보이는 `python3`는 Microsoft Store로 보내는 가짜 별칭이라 실행되지 않습니다. `uv python install 3.12 --default`로 진짜 `python`·`python3`를 만들고, 설정 → 앱 → 고급 앱 설정 → **앱 실행 별칭**에서 `python.exe`·`python3.exe`(앱 설치 관리자)를 끕니다.
5. **PYTHONUTF8.** 한글 Windows 콘솔(cp949)에서 스크립트의 이모지 출력이 오류로 멈추지 않게 `setx PYTHONUTF8 1`을 한 번 실행합니다(새로 여는 창부터 적용 — Claude Code를 다시 엽니다).
6. **한글 글꼴.** Pretendard를 설치하면 가장 좋고, 없어도 Windows 기본 맑은 고딕 Bold(`C:\Windows\Fonts\malgunbd.ttf`)로 표지를 만들 수 있습니다.
7. **naver-blog-cli·Chromium·로그인.** 위 [사전 요구사항](#사전-요구사항)의 **Windows:** 명령(`…\Scripts\playwright.exe`, `…\Scripts\python.exe`)을 씁니다.
8. **이미지 AI 키(Gemini 또는 OpenAI).** `/naver-blog-autopilot:blog-setup`이 어느 쪽을 쓸지 묻고 안내합니다. 키는 PowerShell에서 `notepad "$HOME\naver-blog-work\.env"`(실제 작업 폴더 경로로)로 `.env`를 열어 `GEMINI_API_KEY=…` 또는 `OPENAI_API_KEY=…` 한 줄을 넣고 저장합니다(채팅에 붙여넣지 않기). 메모장이 저장한 Windows 줄바꿈(CRLF)도 그대로 읽힙니다.

그다음은 아래 "설치와 첫 사용"과 같습니다. 셋업 진단표 맨 위에 `OS: Windows(Git Bash)`가 나오면 맞게 돈 것입니다.

## 설치와 첫 사용

아래 `/`로 시작하는 것들은 **터미널이 아니라 Claude Code 입력창**에 그대로 칩니다. `bash` 코드블록은 **터미널**에서, `powershell` 코드블록은 **PowerShell 창**에서 실행합니다.

Claude Code가 없다면 먼저 설치합니다(Windows는 Git for Windows를 먼저 — 위 "Windows에서 쓰기").

- macOS:
  ```bash
  curl -fsSL https://claude.ai/install.sh | bash
  ```
- Windows (PowerShell):
  ```powershell
  irm https://claude.ai/install.ps1 | iex
  ```

1. uv가 없다면 **터미널**(Windows는 PowerShell)에서 먼저 설치합니다.

   macOS:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Windows:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **터미널**(Windows는 PowerShell)에서 작업 폴더를 만들고, 그 폴더에서 Claude Code를 엽니다. 작업 폴더는 **플러그인 저장소 밖**이어야 하고, 글 작업을 할 때는 **매번** 이 폴더에서 Claude Code를 엽니다.

   macOS:

   ```bash
   mkdir -p ~/naver-blog-work && cd ~/naver-blog-work && claude
   ```

   Windows:

   ```powershell
   mkdir -Force ~\naver-blog-work; cd ~\naver-blog-work; claude
   ```

3. Claude Code 입력창에서 마켓플레이스를 추가하고 플러그인을 설치합니다(공개 저장소라 따로 로그인할 필요가 없습니다). 설치 직후 커맨드가 보이지 않으면 `/reload-plugins`를 실행합니다.

   ```
   /plugin marketplace add heesun-woodi/woodi-claude-plugins
   /plugin install naver-blog-autopilot@woodi-claude-plugins
   ```

4. 같은 입력창에서 셋업합니다.

   ```
   /naver-blog-autopilot:blog-setup ~/naver-blog-work
   ```

   환경(uv·Python·Chromium·naver-blog-cli·네이버 세션·이미지 AI 키)을 진단하고 `scaffold/`를 작업 폴더로 복사합니다. `scripts/`는 매번 최신본으로 갱신하고, `knowledge/`는 보존합니다(담당자가 고친 파일은 덮어쓰지 않고, 아직 채워지지 않은 스텁만 교체). 이미지 AI 키가 없으면 **"이미지 AI 고르기"** 질문(Gemini / OpenAI / 아직 없음)이 한 번 나오고, 고른 제공자의 키 발급 안내가 이어집니다. 끝으로 결과를 표로 보여 주고 빠진 항목마다 실행할 명령을 출력합니다.
5. 진단표가 알려 준 설치·로그인 명령은 **터미널(Windows는 PowerShell)에서** 실행합니다(Claude 입력창이 아님). 진단표는 OS에 맞는 갈래만 보여 줍니다. 네이버 로그인은 **1회, 사람이 직접** 하고 "로그인 상태 유지"를 반드시 체크합니다(위 "로그인은 1회" 참고). `.env`에 고른 제공자의 키(`GEMINI_API_KEY=…` 또는 `OPENAI_API_KEY=…`)를 채웁니다(채팅에 키를 붙여넣지 마세요). 셋업 중에 "넣었어요"라고 답하면 바로 `check_image_key.py`로 확인합니다. 블로그 ID를 물으면 `blog.naver.com/<여기>`의 ID를 답합니다(`.env`의 `NAVER_BLOG_ID=`로 저장됨).
6. [처음 채울 것](#처음-채울-것)의 `knowledge/` 파일과 `photos/business-intro.png`를 준비합니다. 레퍼런스를 정했다면 `blog-design-system` 스킬로 `knowledge/design-system.md`를 만듭니다.
7. Claude Code 입력창에서 `/naver-blog-autopilot:blog-setup ~/naver-blog-work`를 다시 실행해 모든 항목이 "확인됨"인지 봅니다.
8. 글을 시작합니다.

   ```
   /naver-blog-autopilot:blog-run
   ```

   주제 번호를 미리 알면 `/naver-blog-autopilot:blog-run 3`, 이미 만든 글의 진행 상황은 `/naver-blog-autopilot:blog-run report 001`, 로그인이 안 돼 업로드를 미룬 글(또는 키·실사진이 없어 이미지 단계에서 멈춘 글)은 준비가 끝난 뒤 `/naver-blog-autopilot:blog-run resume 001`로 이어서 합니다. 한 번 실행에 글은 **한 편**입니다.

## 워크플로우

`/naver-blog-autopilot:blog-run` 한 번이 글 한 편입니다. `●`는 담당자가 답해야 하는 게이트입니다.

| 단계 | 수행 주체 | 산출 파일 | 사용자 게이트 |
|---|---|---|---|
| Step 0 preflight | 메인 | `work/own-posts.json`(기발행 글 목록) | - (키·세션이 없으면 경고 후 단계적으로 저하) |
| Step 1 주제 리서치 | 메인 + `blog-topic-research` 스킬 | `work/topics/<날짜>-topics.md` | ● 게이트 1: 번호·정보/홍보 유형·지역 키워드 2개 선택("이번 제목 지역"을 미리 계산해 보여 줌) |
| B 초안 | `blog-writer` 에이전트 + `blog-draft-writer` 스킬 | `research.md`, `draft.md` | - |
| C 근거 검토 | `blog-fact-checker` 에이전트 + `blog-fact-check` 스킬 | `factcheck.md` (PASS/FAIL/출처필요/시점확인) | - |
| B' 수정 + SEO | `blog-writer` 재개 + `blog-naver-seo` 스킬 | `draft-v2.md`, `seo.md` | - |
| Step 2 lint | 메인 + `lint_post.py --stage draft` | `lint.json` | - |
| 게이트 2 | 메인 | `gates.md` `## 초안피드백`, `work/feedback-log.md` | ● 제목 A/B안(제목 지역 포함 확인)·톤·길이 피드백 + 요청마다 "앞으로 계속/이번 글만" |
| Step 3 이미지·표지 | 메인 + `blog-image-director` 스킬 + `gen_image.py` + `make_cover.py` | `images/image-plan.md`(`00` 표지 행 포함), `images/NN-*.png`, `images/00-bg.png`·`images/00-cover.png` | ● 게이트 3: 표지(승인/줄바꿈·배지 재생성/배경 재생성/실사진 배경) → 슬롯별 승인/재생성/실사진 교체/제거 |
| Step 4 업로드본 빌드 | 메인 + `build_final.py` + `lint_post.py --stage upload` | `final.md`(출처·캡션 제거, 소제목 여백, 마무리 블록), `lint.json` | - |
| Step 5 업로드 | 메인 + `blog-naver-upload` 스킬 + `naver_upload.sh`(`create-draft-from-folder`) | `upload.log`, `gates.md` `## 업로드`(장소·대표이미지 결과), `work/variation-log.md` 한 줄 | - |
| 학습 정리 | 메인 + `blog-learn` 스킬 | `knowledge/learned-preferences.md` | ● 새 규칙·승격 규칙 승인(대기 피드백이 있을 때만) |
| 종료 보고 | 메인 | - | 담당자가 네이버에서 임시저장 → 미리보기 → 발행(직접 고쳤다면 `/naver-blog-autopilot:blog-feedback NNN 주소`) |

- **디스패치 예산**: 글 한 편에 에이전트 호출은 기본 3회(B·C·B'), 재작업을 포함해 최대 7회입니다. 8회째가 필요해지면 멈추고 보고합니다.
- C에서 FAIL과 출처필요가 0건이면 `draft.md`를 `draft-v2.md`로 복사하고, B'는 SEO 다듬기와 관련글 링크 치환만 합니다.
- 게이트 2의 수정은 한 번만 돕니다. 사실 문장이 바뀌었으면 C를 한 번 더(`r2`) 돌립니다.
- 업로드(Step 5)는 로그인·2단계 인증·CAPTCHA가 끼어들 수 있어 서브에이전트에 맡기지 않고 메인이 직접 합니다.
- 대표이미지는 표지(`00-cover`)입니다. 업로드가 본문 맨 앞에 넣고 대표로 지정하므로, 미리보기에서 첫 사진에 '대표' 표시가 있는지만 확인하면 됩니다.
- 끝나면 임시저장 제목·카테고리·태그·이미지 수·장소 카드와 "네이버 앱/웹 → 글쓰기 → 임시저장 글 → 미리보기 → 발행" 안내가 나옵니다.

## 콘텐츠 고치기와 학습

글을 고쳐 달라고 한 내용은 그 글에서 끝나지 않고 **다음 글에도 반영될 수 있습니다.** 요청은 `work/feedback-log.md`에 기록되고, 글이 끝날 때 `blog-learn`이 규칙으로 정리해 `knowledge/learned-preferences.md`에 넣습니다. "앞으로 계속"을 고른 요청은 바로 규칙이 되고, 그 밖의 변경(후보 승격·지운 규칙 재적용·규칙 문장 변경)만 담당자에게 묻습니다.

### 어디서 배우나 — 초안 단계가 주 경로

학습은 주로 **업로드 전, 초안을 보는 동안** 일어납니다. 네 가지 길이 모두 같은 기록(`work/feedback-log.md`)으로 모입니다.

1. **선택지** — 게이트 2의 `더 짧고 간결하게` 같은 옵션, 게이트 3의 재생성·교체·제거.
2. **직접 입력** — 게이트 1·2·3 질문의 `기타`에 쓴 요청(게이트 1에서는 "○○ 주제는 앞으로 빼 주세요" 같은 주제 선호).
3. **파일 직접 수정** — 게이트 2에서 `draft-v2.md`를 메모장(macOS는 텍스트 편집기)으로 직접 고쳐 저장한 뒤 답해도 됩니다(안내에 파일 경로가 나오고, Windows는 `C:\…` 경로도 함께). 메인이 보여 준 판(`draft-v2.shown.md`)과 비교해 바뀐 점을 보여 주고, 다음 글에도 해당할 것을 일반화 문장 1~4개로 제안해 "앞으로도 이렇게 쓸까요?"를 묻습니다 — 고른 것만 "앞으로 계속"으로 기록됩니다. 고친 문단에 숫자·조항·출처가 있으면 근거 검토를 한 번 더 하고, lint에 걸리면 `B'로 고치기` / `내가 다시 고칠게요`를 묻습니다. 수정 요청도 함께 남겼다면 writer는 **담당자가 고친 판을 기준으로** 요청만 반영하고 담당자의 수정은 되돌리지 않습니다. 수정 루프의 재확인과 업로드본 빌드 직전에도 같은 비교를 한 번 더 합니다(게이트 3 동안 고친 것도 잡힙니다).
4. **대화** — 질문 화면 밖에서 "도입이 너무 딱딱해요"처럼 말해도 피드백입니다. 범위를 한 번 묻고 기록하며, 지금 글에 반영할 수 있으면 그 단계에서 고칩니다.

발행 후 비교(아래 "발행 후 알려 주기")는 **보조 경로**입니다 — 업로드본(`final.md`) 기준이라, 초안 단계에서 이미 배운 직접 수정은 두 번 학습되지 않습니다.

### 게이트 2에서 수정 요청 쓰는 법

게이트 2의 "톤·길이·내용" 질문에서 `기타`를 고르고 요청을 직접 씁니다. 잘 반영되게 하려면:

- **구체적으로** — 어디를, 어떻게 바꿀지 씁니다(절 번호·문장·원하는 결과).
- **한 요청에 한 가지** — 여러 가지면 줄을 바꾸거나 번호를 붙여 나눕니다. 나눠 쓴 요청은 따로 기록되고 따로 "앞으로도?"를 묻습니다.
- **이유가 있으면 한마디** — 규칙으로 정리할 때 근거가 됩니다.

| 나쁜 예 | 좋은 예 |
|---|---|
| 좀 더 좋게 써 주세요 | 2️⃣ 절 첫 문단을 고객 상황 예시(퇴근 뒤 주말에 맡기려는 경우)로 시작해 주세요 |
| 너무 딱딱해요 | 문장을 한 문장 40자 안쪽으로 끊고, "~하여야 합니다"는 "~해야 합니다"로 바꿔 주세요 |
| 내용 추가해 주세요, 그리고 FAQ도 이상해요 | 1) 신청부터 완료까지 걸리는 기간을 넣어 주세요(공식 안내 기준) 2) FAQ 마지막 질문을 비용 질문으로 바꿔 주세요 |

말투는 합니다체로 고정이라 해요체로 바꾸는 요청은 받지 않습니다. 사실이 틀렸다는 요청(수치·일정·조항)은 고친 뒤 근거 검토(C r2)를 한 번 더 거칩니다.

### "이번 글만"과 "앞으로 계속"

수정 요청을 남기면 요청마다 "이 요청을 앞으로 쓰는 모든 글에도 적용할까요?"를 묻습니다.

- **이번 글만** — 이 글에만 반영합니다. 바로 규칙이 되지는 않고, 다른 글에도 쓸 수 있는 요청이면 `## 후보`에 쌓이며, 서로 다른 글에서 같은 요청이 2회가 되면 `blog-learn`이 "규칙으로 올릴까요?"를 묻습니다.
- **앞으로 계속** — 이 글에 반영하고, 글이 끝날 때 **다시 묻지 않고 바로** `## 적용 중` 규칙이 됩니다(종료 보고에 새 규칙으로 보입니다). 같은 뜻의 규칙이 이미 있으면 새로 만들지 않고 그 규칙의 근거만 늘어납니다. 예전에 `## 보류·삭제`로 옮긴 규칙과 같은 뜻이면 그때만 "다시 적용할까요?"를 묻습니다.

제목을 A/B안 대신 직접 쓴 경우도 "제목" 요청으로 기록되고 범위를 묻습니다. "그대로 진행"이면 아무것도 기록하지 않습니다.

### 게이트 3 이미지 요청

이미지 재생성·실사진 교체·제거는 묻지 않고 "이번 글만"으로 자동 기록됩니다(재생성 때 쓴 기타 입력이 원문). 게이트 3이 끝날 때 재생성·교체가 하나라도 있었으면 "이미지 요청 중 앞으로도 지킬 것이 있나요?"를 한 번 묻습니다 — 고른 요청은 슬롯 번호·파일명을 뺀 일반화 문장(예: "06 재생성: 스티커 없애기" → "제품·소품에 스티커·로고가 보이지 않게 만들기" — 질문에 그 문장이 보입니다)으로 "앞으로 계속" 기록됩니다. 표지(`00`) 요청은 "표지", 나머지는 "이미지" 범주입니다. 이미지 요청도 구체적으로 쓸수록 좋습니다(예: "사람 얼굴 대신 사물 위주로", "표지 첫 줄에 키워드만").

### 발행 후 알려 주기 (보조 경로)

네이버에서 임시저장 글을 직접 고친 뒤 발행했다면, Claude Code 입력창에서:

```
/naver-blog-autopilot:blog-feedback 003 https://blog.naver.com/<블로그 ID>/<글번호>
```

발행본을 가져와(글 폴더의 `published.json`) **업로드본 `final.md`**와 비교하고(`scripts/diff_published.py`), 다음 글에도 해당할 바뀐 점(제목 형식·말투·분량·소제목 등)을 1~4개 피드백 문장으로 제안합니다. 제안마다 `앞으로 계속` / `이번 글만` / `기록 안 함`을 고르면 고른 것만 "발행후" 피드백으로 기록하고 학습합니다. `final.md`가 없는 예전 글은 비교하지 않고 말로 받습니다.

- 주소 없이 `/naver-blog-autopilot:blog-feedback 003`이면 그 글에 대한 의견을 말로 남깁니다(직접 입력).
- 인자 없이 `/naver-blog-autopilot:blog-feedback`이면 **가장 최근 글 폴더**(번호가 가장 큰 글)를 대상으로 직접 입력을 받습니다.
- 주소만 주면(글 번호 없음) 최근 글 3개 중 어느 글의 발행본인지 먼저 묻습니다.

### 규칙 보기·고치기·지우기

- `/naver-blog-autopilot:blog-feedback rules` — `## 적용 중`·`## 후보` 규칙을 보여 줍니다.
- 직접 고치기 — 작업 폴더의 `knowledge/learned-preferences.md`를 열어 `## 적용 중` 표의 규칙 문장을 고칩니다. 더 쓰지 않을 규칙은 행을 `## 보류·삭제`로 옮기면 됩니다(행을 지워도 되지만, 옮겨 두면 언제·왜 뺐는지 기록이 남아 `blog-learn`이 같은 규칙을 다시 올릴 때 참고합니다). `## 피할 표현`에 표현을 더하면 다음 lint부터 WARN으로 잡힙니다.
- `/naver-blog-autopilot:blog-setup`을 다시 실행해도 이 파일은 덮어쓰지 않습니다.

### 잠긴 규칙

학습 규칙은 아래를 **바꿀 수 없습니다.** 충돌하면 잠긴 규칙대로 쓰고, writer가 반환에 "충돌" 한 줄을 남겨 게이트 2에서 보여 줍니다.

- `knowledge/business-profile.md`의 금칙어와 "꼭 지켜야 할 점"
- 디자인 시스템 ⑤ 반드시 지킬 것 — 이미지 속 글자·얼굴 클로즈업·로고 금지, 홍보글은 실사진만, 사진 재사용 금지(표지의 제목·배지·전화번호 합성은 ⑤가 정한 표지 예외)
- 디자인 시스템 ⑧ — 지어내기 금지(출처 없는 수치·일정·조항), `(출처: URL)` 형식, 금칙

우선순위는 잠긴 규칙 > 학습 규칙(`## 적용 중`) > 디자인 시스템 나머지 > 구조 템플릿 예시입니다. lint 기준(합니다체, 글자수·소제목·이미지 수 범위)도 그대로라, "더 짧게" 같은 규칙은 그 범위 안에서 적용됩니다.

### 규칙이 쌓이면

같은 범주의 규칙이 여러 개 쌓이면 `blog-learn`이 "디자인 시스템에 반영할까요?"를 제안할 수 있습니다. 승인하면 `blog-design-system` 스킬의 갱신 모드(백업 → `work/design-system/proposed.md` → 담당자 승인 → `knowledge/` 교체)로 옮기고, 옮긴 규칙은 `## 보류·삭제`로 정리합니다. 디자인 시스템 한 장이 정본이라는 원칙을 지키기 위해서입니다.

## 작업 폴더 구조

`/naver-blog-autopilot:blog-setup`이 만드는 폴더(예: `~/naver-blog-work/`)입니다. 다시 실행하면 `scripts/`는 플러그인 최신본으로 덮어쓰고, `knowledge/`는 이미 있는 파일을 보존합니다(`Task N에서 채움` 문구가 남은 스텁만 교체). 그 밖의 파일은 없을 때만 복사합니다.

```
.env  .env.example  .gitignore  README.md
knowledge/                      # 정본. 여기서 직접 고친다
  design-system.md              # 글 디자인 시스템(①~⑨, ④에 lint 수치)
  business-profile.md           # 업체 기본정보 + 금칙어
  source-blogs.json             # 주제 소스·레퍼런스·자기 블로그
  official-sources.md           # 업종별 공신 출처(법령·기관), 주장 유형별 매핑
  naver-seo-checklist.md        # 네이버 SEO 필수/권장 항목
  learned-preferences.md        # 학습 규칙(## 적용 중·## 후보·## 보류·삭제·## 피할 표현) — 처음 한 번만 복사
scripts/
  fetch_posts.py  fetch_post.py  dedupe_check.py
  lint_post.py  gen_image.py  make_cover.py  build_final.py  naver_upload.sh  check_blog_account.py  check_image_key.py
  feedback_log.py  diff_published.py
photos/                         # 업체 실사진(커밋 제외). business-intro.png = 마무리 블록 고정 이미지
playwright-state/               # 로그인 세션(로그인 뒤 생성, 커밋 금지)
work/
  own-posts.json                # 기발행 글 목록(중복 검사·관련글 링크)
  variation-log.md              # 업로드 성공마다 한 줄
  feedback-log.md               # 수정 요청 기록(게이트 2·3·발행 후) — feedback_log.py가 만듦
  topics/<날짜>-topics.md       # 주제 후보 표
  posts/NNN-slug/
    topic.md  gates.md          # gates: ## 선택 · ## 초안피드백 · ## 이미지승인 · ## 업로드
    research.md  draft.md  factcheck.md  seo.md
    draft-v2.md                 # 팩트 반영 + SEO + 관련글 실제 URL(출처 괄호 포함 원본)
    draft-v2.shown.md           # 게이트 2에서 마지막으로 보여 준 판(담당자 직접 수정 비교 기준)
    images/image-plan.md  images/NN-*.png  images/00-bg.png  images/00-cover.png(대표이미지)
    final.md                    # build_final.py 결과: 출처·캡션 없음, 이미지 절대경로, 마무리 블록
    lint.json  upload.log
```

게이트 2 이후 사실 문장이 바뀌면 `factcheck-r2.md`가 추가로 생깁니다.

## 계정 안전 수칙

- **하루 1~2편 이내.** 네이버 계정을 자동화된 브라우저로 조작하는 방식이라 과도하게 쓰면 계정이 제재될 수 있습니다. `naver-blog-cli`의 경고 원문은 "과도하게 쓰면 계정이 제재될 수 있습니다. 대량 자동 포스팅 용도로 만들지 않았고, 그런 기능을 넣지 마세요."입니다.
- **임시저장까지만.** 발행은 담당자가 네이버 앱/웹에서 미리보기를 보고 직접 합니다. 업로드 스크립트는 `NAVER_BLOG_READONLY=1`로 발행·삭제 명령을 제거한 상태로만 CLI를 부릅니다.
- **세션 파일은 비밀번호에 준해 다룹니다.** `playwright-state/storage_state.json`은 계정 접근권한 그 자체입니다. 공유·커밋하지 말고(`.gitignore`에 포함돼 있습니다) 다른 사람 컴퓨터로 옮기지 마세요. 비밀번호는 어디에도 저장되지 않습니다.
- **로그인·CAPTCHA·2단계 인증은 사람이.** 에이전트와 스크립트는 로그인을 하지 않습니다.
- **같은 오류로 반복 재시도하지 않습니다.** 업로드 실패는 한 번만 다시 시도하고, 그래도 안 되면 멈추고 보고합니다.

## 비용

- **이미지**: 제공자마다 다릅니다. **Gemini**는 장당 약 $0.04입니다. 이 값은 `gen_image.py`의 `COST_PER_IMAGE_USD`에 적힌 **추정치**이고 검증된 단가가 아닙니다. 실제 요금은 https://ai.google.dev/pricing 에서 확인하세요. 글 한 편에 필요한 이미지 수는 디자인 시스템 ④(글자 수 ÷ 이미지당 글자 수)로 정해지므로, Gemini 이미지 비용은 대략 이미지 수 × $0.04(추정치 기준)로 어림할 수 있습니다. **OpenAI(GPT 이미지)**는 이 문서에 금액을 적지 않습니다 — OpenAI 요금 페이지(https://openai.com/api/pricing/)에서 모델·크기별 단가를 확인하세요. 어느 쪽이든 재생성도 과금되고, 키 확인(`check_image_key.py`)은 비용이 없습니다. 표지는 배경 1장만 생성 비용이 들고(실사진 배경이면 0), 글자 합성(`make_cover.py`)은 로컬이라 비용이 없습니다. `gen_image.py --dry-run`으로 API 호출 없이 예상 비용을 먼저 볼 수 있습니다.
- **모델 사용량**: 글 한 편에 opus 에이전트가 기본 3회(B·C·B'), 재작업까지 최대 7회 돕니다. 메인 세션의 주제 리서치·이미지 검수도 따로 듭니다. 토큰 사용량은 글 길이와 재작업 횟수에 따라 크게 달라지고 요금제마다 과금 방식이 달라, 이 문서에서는 금액을 단정하지 않고 "opus 호출 3~7회" 정도로만 안내합니다.
- 네이버 임시저장과 법령 조회(law.go.kr DRF)는 비용이 없습니다.

## 문제 해결

**`naver_upload.sh` 종료 코드**

`naver-blog-cli`는 성공·실패와 무관하게 종료 코드가 항상 0이라, 스크립트는 종료 코드가 아니라 CLI의 **stdout 문구**로 판정합니다.

| 코드 | 의미 | 할 일 |
|---|---|---|
| 0 | 임시저장 완료 | 네이버에서 미리보기 후 발행 |
| 2 | 사용 오류(경로·frontmatter) | 인자와 `final.md` 머리말 확인 |
| 10 | `lint_post.py --stage upload` 실패 | 출력된 FAIL 항목 수정(본문은 writer 재개, 이미지·표지는 Step 3/4, `closing_block`·`h2_spacing` 같은 빌더 항목은 중단·보고) |
| 11 | 이중 검사 실패(금칙어·`[[`·빈 이미지·`[출처 필요]`·`출처:`/캡션 잔존·`:::place` 없음) | 텍스트는 writer 재개, 출처·캡션·마무리 블록은 `build_final.py` 재실행 |
| 12 | 표지 `images/00-cover.png` 없음, 또는 이미지 경로가 절대경로가 아니거나 파일 없음 | 표지는 `make_cover.py`로 만들고, 경로는 Step 4(`build_final.py`) 재실행 |
| 20 | 세션 없음/만료 또는 `naver-blog-cli` 없음, 계정 확인 실패 | `/naver-blog-autopilot:blog-setup`의 로그인 절차 |
| 21 | 로그인한 계정이 대상 블로그(`--blog-id`)에 글을 쓸 수 없음 — 다른 계정 세션 | 대상 블로그 계정으로 `login_setup.py` 다시 실행(아래 "다른 계정으로 로그인돼 있을 때") |
| 30 | `create-draft-from-folder` 실패 | 출력 문구 확인(`넣기 전에 걸린 것` = 이미지 없음·10MB, 에디터 변경, 세션 만료). 중복 임시저장이 생겼는지 확인 후 재시도는 1회 |
| 31 | 저장은 됐으나 목록에서 제목 확인 불가 | 네이버 → 글쓰기 → 임시저장 글에서 직접 확인 |

`--dry-run`을 붙이면 lint·머리말·이미지 경로·표지 존재만 확인하고 네이버에는 접속하지 않습니다.

**프로필 행·블로그 ID가 비었다는 오류가 날 때.** 스크립트는 업체 값을 기본값으로 지어 넣지 않고 멈춥니다(exit 2). 비어 있는 필수 행은 `blog-run` Step 0의 `profile: MISSING <행>` 줄과 `blog-setup` 진단표에 나옵니다. 오류 메시지에 나온 `knowledge/business-profile.md`의 행(예: `장소 검색어`·`연락처`·`고객 지역`)이나 `## 금칙어` 절(없으면 `- 없음` 한 줄), `.env`의 `NAVER_BLOG_ID`, `knowledge/source-blogs.json`의 `own_blog.blogId`, 또는 `--blog-id`·`--category` 인자를 채운 뒤 같은 단계를 다시 실행합니다. `blog-run`이 `blogId: MISMATCH`로 멈췄다면 `.env`와 `own_blog.blogId`의 값을 같게 맞춥니다.

**"표지 재생성 필요"로 `build_final.py`가 멈출 때.** 게이트 2나 writer 재개에서 제목이 바뀌어, 표지에 박힌 제목(image-plan `00` 행 `제목:`)이 frontmatter `title`과 달라진 것입니다. `00` 행의 `제목:`·`줄바꿈:`을 새 제목에 맞게 고치고 `uv run --with pillow scripts/make_cover.py …`만 다시 돌린 뒤(비용 0, 배경은 그대로) Step 4를 다시 실행합니다. `/naver-blog-autopilot:blog-run`이 이 과정을 자동으로 합니다.

**"경고: 대표이미지 지정 실패"가 나올 때.** 임시저장은 됐지만 CLI가 표지를 대표이미지로 확인하지 못한 경우입니다(노트에 `대표 지정 실패`·`표지 넣기 실패`). 네이버 → 글쓰기 → 임시저장 글을 열어 첫 사진(표지)을 직접 대표로 지정하세요. `gates.md ## 업로드`에 `대표이미지: 실패(직접 지정)`로 남습니다.

**"경고: 장소 카드 확인 필요"가 나올 때.** `:::place` 검색 결과 1번이 우리 업체가 아닐 수 있다는 뜻입니다. 미리보기에서 지도 카드를 확인하고, 다르면 `knowledge/business-profile.md`의 `장소 검색어` 행을 `<업체명> <지역>`처럼 좁혀 다음 글부터 반영합니다.

**이미지 생성이 429(쿼터 초과)로 멈출 때 (Gemini).** `gen_image.py`가 `APIError 429`와 함께 남은 슬롯을 중단했다면, Gemini 이미지 모델을 쓸 수 없는 키입니다. https://aistudio.google.com/apikey 에서 그 키의 Google Cloud 프로젝트에 결제(Billing)가 설정돼 있는지 확인하세요. 무료 키는 기다려도 풀리지 않습니다. 결제를 설정한 뒤 Step 3(이미지)부터 다시 진행합니다.

**OpenAI 키가 401·403으로 거부될 때.** `check_image_key.py`가 종료 3(키 거부)을 내거나 생성이 401/403으로 실패하면: 401은 키 오타·폐기된 키입니다(https://platform.openai.com/api-keys 에서 새로 발급). 403은 대개 GPT 이미지 모델에 필요한 **조직 인증(Verify Organization)**이 안 된 경우입니다 — https://platform.openai.com/settings/organization/general 에서 인증한 뒤 다시 확인하세요. **키 확인이 통과해도 이미지 생성에서 403이 나면 조직 인증이 필요한 것입니다.** 종료 4(모델 없음·권한 없음)면 결제 수단 등록과 `IMAGE_MODEL` 이름을 확인합니다.

**`IMAGE_KEY: CONFLICT`가 나올 때.** `IMAGE_PROVIDER=`(키: API 키(GEMINI_API_KEY/OPENAI_API_KEY)가 든 첫 .env 파일의 값. 어느 파일에도 없으면 환경변수. IMAGE_PROVIDER·IMAGE_MODEL: 키를 찾은 .env의 값(그 파일에 없으면 미지정). 키를 환경변수에서 읽을 때는 항목마다 cwd .env → 환경변수 중 처음 값이 있는 곳.)가 가리키는 제공자의 키가 비어 있거나, 값이 `gemini`/`openai`가 아닙니다(잘못된 값은 화면에 보여 주지 않습니다 — 키를 이 줄에 잘못 넣었는지 확인하세요). 그 제공자의 키를 넣거나, `IMAGE_PROVIDER=`를 가진 키의 제공자로 바꾸거나 줄을 지우세요. `/naver-blog-autopilot:blog-run`은 이 상태에서 시작하지 않습니다.

**세션 만료.** 몇 시간 뒤 글쓰기만 로그인 페이지로 바뀌거나 공인 IP가 바뀌면 세션이 풀립니다. "로그인 상태 유지"를 체크하지 않은 경우가 가장 흔합니다. 터미널(Windows는 PowerShell)에서 작업 폴더로 이동해 위 로그인 명령(`login_setup.py`, OS별 갈래)을 다시 실행하고, 로그인이 끝나면 `/naver-blog-autopilot:blog-run resume <NNN>`으로 업로드만 이어갑니다. 세션이 없을 때 `/naver-blog-autopilot:blog-run`은 Step 4까지 진행하고 업로드만 미룹니다.

**다른 계정으로 로그인돼 있을 때 (exit 21 · `session: WRONG_ACCOUNT`).** 세션 파일(`playwright-state/storage_state.json`)이 테스트 계정 등 다른 계정의 것이면 `naver-blog-cli check-session`은 "글쓰기 가능"으로 통과하지만, 실제 글쓰기 화면은 그 계정의 블로그로 넘어가 임시저장이 `…을 못 찾음`으로 실패합니다. 그래서 업로드 전에 `scripts/check_blog_account.py`가 글쓰기 화면이 대상 블로그로 열리는지 확인합니다(글은 쓰지 않음). 걸리면 터미널(Windows는 PowerShell)에서 작업 폴더로 이동해 위 로그인 명령을 **대상 블로그 계정으로** 다시 실행하세요(세션 파일이 새 계정 것으로 바뀝니다).

**네이버가 에디터를 개편했을 때.** `naver-blog-cli`가 `…을 못 찾음`을 계속 내면 CLI의 셀렉터가 낡은 것입니다. 이 플러그인은 셀렉터·Playwright 코드를 새로 쓰지 않으므로 `naver-blog-cli`의 업데이트를 기다리는 것이 기본입니다. 급할 때는 담당자 승인 아래 aside(AI 브라우저)에 `final.md`와 `images/`를 주고 "임시저장까지만, 발행 금지"로 수동 지시하는 폴백이 있습니다(로그인·2단계 인증은 이 경우에도 담당자가 합니다).

**팩트체크 출처 사이트에 접근할 수 없을 때.** law.go.kr DRF 오픈API는 비교적 안정적이지만, 공공기관 세부 페이지 가운데 JavaScript로 그려지는 곳은 조회가 안 될 수 있습니다(`knowledge/official-sources.md`의 접근성 기록). 그런 주장은 지어내지 않고 `출처필요` 또는 `시점확인`으로 판정되며, **담당자가 직접 확인**한 뒤 답을 주면 그 답이 `gates.md`에 기록되고 다음 수정에 반영됩니다. 네이버 블로그 페이지는 WebFetch가 막히므로 스크립트가 `curl`로 가져옵니다.

## 2차 범위

이 버전(1.0.0)에 없는 것: 스케줄 실행(정해진 시간에 주제 리서치·초안까지 자동으로 돌리기), 이미지 제공자 자동 전환(한쪽이 실패하면 다른 쪽으로 — 지금은 `.env`로 하나를 고름), 글 반응(조회·공감)을 읽어 주제 후보에 가중치를 주는 기능. 글을 발행하는 자동화는 계정 안전상 범위에 넣지 않습니다.
