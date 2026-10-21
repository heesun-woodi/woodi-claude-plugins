# naver-blog-autopilot 퀵스타트 (모임 참가자용)

이 문서는 AI 커뮤니티 모임에서 `naver-blog-autopilot` 플러그인을 처음 설치하고 첫 글을 네이버 임시저장까지 만들어 보는 참가자를 위한 안내입니다. 이 플러그인은 네이버 블로그의 정보성 글을 **주제 리서치부터 초안·근거 검토·SEO·이미지·임시저장까지 자동으로** 진행하고, **발행은 사람이 네이버에서 직접** 합니다. 글을 대신 올려 주는 도구가 아니라, 손이 많이 가는 준비 과정을 줄이고 마지막 판단은 사람이 하도록 만든 도구입니다.

모임에서는 각자 자기 블로그(업체·전문가·개인·브랜드 어느 쪽이든)에 맞춰 설치와 온보딩을 마치고, 첫 글 한 편을 네이버 임시저장 글로 만들어 보는 것을 목표로 합니다. 설치 단계에서는 「터미널」과 「Claude 입력창」을 구분하는 것이 가장 중요하니, 각 단계의 실행 위치 표시를 꼭 확인해 주세요.

플러그인 전체 설명은 [플러그인 README](../../plugins/naver-blog-autopilot/README.md)에 있습니다.

## 준비물 체크리스트

- [ ] **네이버 블로그 계정과 발행한 글 2편 이상(권장).** 없어도 쓸 수 있지만, 자기 글이 2편 미만이면 관련글 링크 검사가 경고만 내고 넘어가고 글 모양 기준도 「측정 전」 기본값으로 시작합니다.
- [ ] **참고할 블로그 글 주소 3~5개.** 네이버에서 "<상품·서비스> <지역>"이나 "<주제> 후기"로 검색해, 구성·말투가 마음에 드는 글의 주소를 미리 모아 오세요. 자기 블로그에서 잘 된 글 1편도 좋습니다. 온보딩에서 한 번에 붙여넣습니다.
- [ ] **Claude Code.** 아래 설치 1단계에서 설치합니다.
- [ ] **uv.** 아래 설치 2단계에서 설치합니다(스크립트용 `python3`은 3.11 이상이 필요합니다).
- [ ] **이미지 키 하나 이상.** Gemini 또는 OpenAI(둘 다 결제 설정 필요) 또는 Pexels(무료) 중 하나 이상을 준비합니다. 발급 방법은 [이미지 소스 연동 안내](../../plugins/naver-blog-autopilot/skills/blog-onboarding/references/image-setup.md)에 있고, 온보딩이 고른 소스의 안내만 보여 줍니다. 키는 채팅에 붙여넣지 말고 `.env` 파일에 직접 넣습니다. 키가 없어도 시작은 할 수 있습니다(아래 자주 묻는 질문).
- [ ] **한글 폰트(표지 합성용).** Pretendard(https://github.com/orioncactus/pretendard/releases)의 `Pretendard-ExtraBold.otf`·`Pretendard-SemiBold.otf`를 설치하면 가장 좋습니다. macOS는 `~/Library/Fonts/`에 넣고, Windows는 파일을 우클릭 → "설치"합니다. 없으면 macOS는 `/System/Library/Fonts/AppleSDGothicNeo.ttc`, Windows는 맑은 고딕 Bold(`C:\Windows\Fonts\malgunbd.ttf`)로 대신합니다.
- [ ] **Windows만: Git for Windows.** https://git-scm.com/downloads/win 에서 **가장 먼저** 설치합니다. 없으면 Claude Code의 Bash 도구가 PowerShell로 돌아 이 플러그인이 동작하지 않습니다.
- [ ] (업체·브랜드에서 글 끝에 소개 이미지를 넣을 때) 업체명·연락처·주소가 담긴 업체소개 이미지. 작업 폴더의 `photos/business-intro.png`로 넣습니다.

## 설치 6단계

**실행 위치 읽는 법.** 각 단계 제목 옆에 실행 위치를 적었습니다.

- 「터미널에서」 — macOS는 **터미널** 앱, Windows는 **PowerShell 창**(시작 → "PowerShell")입니다. macOS는 `bash` 블록을, Windows는 `powershell` 블록을 실행합니다.
- 「Claude 입력창에서」 — 4단계에서 Claude Code를 연 뒤 나오는 입력칸입니다. `/`로 시작하는 줄은 터미널이 아니라 **여기에** 칩니다. 이 줄들은 언어 표기가 없는 회색 블록에 담았습니다.

### 1단계. Claude Code 설치 — 터미널에서

macOS(터미널에서):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Windows(PowerShell에서 — Git for Windows를 먼저 설치한 뒤):

```powershell
irm https://claude.ai/install.ps1 | iex
```

### 2단계. uv와 Python 준비 — 터미널에서

macOS(터미널에서):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows(PowerShell에서):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Windows는 이어서 두 가지를 더 합니다. Windows에 기본으로 보이는 `python3`는 Microsoft Store로 보내는 가짜 별칭이라 실행되지 않으므로, 진짜 `python`·`python3`를 만듭니다(PowerShell에서).

```powershell
uv python install 3.12 --default
```

그다음 설정 → 앱 → 고급 앱 설정 → **앱 실행 별칭**에서 `python.exe`·`python3.exe`(앱 설치 관리자)를 끕니다. 한글 Windows 콘솔(cp949)에서 스크립트의 이모지 출력이 오류로 멈추지 않게 아래도 한 번 실행합니다(PowerShell에서 — 새로 여는 창부터 적용됩니다).

```powershell
setx PYTHONUTF8 1
```

macOS는 셋업 진단표에 `python3 ≥ 3.11`이 MISSING으로 나오면 3.11 이상을 설치합니다.

### 3단계. naver-blog-cli와 Chromium 설치 — 터미널에서

네이버 임시저장은 외부 도구 [naver-blog-cli](https://github.com/spegas/naver-blog-cli)(MIT)가 맡습니다. 이 플러그인에는 들어 있지 않아 따로 설치합니다.

macOS(터미널에서):

```bash
uv tool install git+https://github.com/spegas/naver-blog-cli
"$(uv tool dir)/naver-blog-cli/bin/playwright" install chromium
[ -d ~/naver-blog-cli ] || git clone https://github.com/spegas/naver-blog-cli ~/naver-blog-cli
```

Windows(PowerShell에서):

```powershell
uv tool install git+https://github.com/spegas/naver-blog-cli
& "$(uv tool dir)\naver-blog-cli\Scripts\playwright.exe" install chromium
if (-not (Test-Path "$HOME\naver-blog-cli")) { git clone https://github.com/spegas/naver-blog-cli "$HOME\naver-blog-cli" }
```

`naver-blog-cli`는 `~/.local/bin`(Windows는 `%USERPROFILE%\.local\bin`)에 생깁니다. PATH에 없다는 오류가 나면 아래를 실행합니다(macOS는 터미널, Windows는 PowerShell에서).

```bash
uv tool update-shell
```

```powershell
uv tool update-shell
```

마지막 줄의 `git clone`은 6단계 로그인에 쓰는 `login_setup.py`를 받아 둡니다(설치본에는 들어 있지 않습니다).

### 4단계. 작업 폴더를 만들고 Claude Code 열기 — 터미널에서

작업 폴더는 **플러그인 저장소 밖**이어야 하고, 글 작업을 할 때는 **매번** 이 폴더에서 Claude Code를 엽니다.

macOS(터미널에서):

```bash
mkdir -p ~/naver-blog-work && cd ~/naver-blog-work && claude
```

Windows(PowerShell에서):

```powershell
mkdir -Force ~\naver-blog-work; cd ~\naver-blog-work; claude
```

### 5단계. 플러그인 설치와 셋업 — Claude 입력창에서

마켓플레이스를 추가하고 플러그인을 설치합니다(공개 저장소라 따로 로그인할 필요가 없습니다). macOS·Windows 모두 같습니다.

Claude 입력창에서:

```
/plugin marketplace add heesun-woodi/woodi-claude-plugins
/plugin install naver-blog-autopilot@woodi-claude-plugins
```

설치 직후 커맨드가 보이지 않으면 Claude 입력창에서:

```
/reload-plugins
```

이어서 셋업합니다. Claude 입력창에서:

```
/naver-blog-autopilot:blog-setup ~/naver-blog-work
```

셋업은 환경을 진단하고 작업 폴더에 `knowledge/`·`scripts/` 등을 복사한 뒤 진단표를 보여 줍니다(아래 「blog-setup 진단표 읽는 법」). 블로그 ID를 물으면 `blog.naver.com/<여기>`의 ID를 답합니다. 마지막에 **"지금 온보딩을 시작할까요?"**가 나오면 `시작`을 고릅니다 — 아래 「blog-onboard 질문 미리보기」대로 이어집니다. 온보딩이 끝나면 6단계로 갑니다.

### 6단계. 네이버 로그인(1회, 사람이 직접) — 터미널에서

Claude 입력창이 아니라 **터미널(Windows는 PowerShell)**에서, 작업 폴더로 이동한 뒤 실행합니다. Claude Code가 열려 있는 창과 다른 터미널 창을 하나 더 열어 실행하면 편합니다. 브라우저가 열립니다.

macOS(터미널에서):

```bash
cd ~/naver-blog-work
NAVER_STATE="$PWD/playwright-state/storage_state.json" \
  "$(uv tool dir)/naver-blog-cli/bin/python" ~/naver-blog-cli/login_setup.py
```

Windows(PowerShell에서):

```powershell
cd ~\naver-blog-work
$env:NAVER_STATE = "$PWD\playwright-state\storage_state.json"; & "$(uv tool dir)\naver-blog-cli\Scripts\python.exe" "$HOME\naver-blog-cli\login_setup.py"
```

직접 로그인하고, **로그인 버튼을 누르기 전에 "로그인 상태 유지"를 체크**하세요(체크하지 않으면 몇 시간 뒤 글쓰기만 로그인 페이지로 바뀝니다). CAPTCHA·2차 인증도 사람이 처리합니다. 비밀번호는 어디에도 저장되지 않고 쿠키 파일(`playwright-state/`)만 남으며, 이 파일은 계정 접근권한 그 자체이니 공유하지 마세요.

로그인이 끝나면 셋업을 한 번 더 돌려 모든 항목이 "확인됨"인지 봅니다. Claude 입력창에서:

```
/naver-blog-autopilot:blog-setup ~/naver-blog-work
```

## blog-setup 진단표 읽는 법

진단표는 `항목 | 상태 | 조치` 세 칸입니다. 이미 갖춰진 항목은 "확인됨", 조치 칸은 "-"입니다. 빠진 항목에는 그대로 실행할 수 있는 명령이 **내 OS에 맞는 갈래만** 나옵니다 — macOS 명령은 터미널, Windows 명령은 PowerShell 창에서 실행합니다(Claude 입력창이 아닙니다).

| 항목 | 이렇게 나오면 | 뜻과 할 일 |
|---|---|---|
| OS | `macOS` / `Windows(Git Bash)` | Windows에서 `Windows(Git Bash)`가 나오면 맞게 돈 것입니다 |
| PYTHONUTF8 (Windows만) | NOT_SET | 2단계 `setx PYTHONUTF8 1` 뒤 Claude Code를 닫았다가 다시 엽니다 |
| uv · python3 ≥ 3.11 | MISSING | 2단계. Windows에서 `Microsoft Store 별칭만 있음`이 나오면 `uv python install 3.12 --default`와 앱 실행 별칭 끄기 |
| Playwright Chromium · naver-blog-cli | MISSING | 3단계 |
| 네이버 세션 | blogId 없음 | 첫 셋업에서는 정상입니다. 블로그 ID를 넣은 뒤 셋업을 다시 돌리면 바뀝니다 |
| 네이버 세션 | 로그인 필요 | 6단계 로그인 |
| 네이버 세션 | 다른 계정 로그인 | 글을 올릴 블로그의 계정으로 6단계 로그인을 다시 합니다(세션 파일이 새 계정 것으로 바뀝니다) |
| 블로그 ID | MISSING / MISMATCH | 셋업·온보딩이 물으면 `blog.naver.com/<여기>`의 ID를 답합니다. `.env`의 `NAVER_BLOG_ID`와 `knowledge/source-blogs.json`의 `own_blog.blogId`가 같아야 글을 시작합니다 |
| 이미지 AI 키 · 스톡 사진 키 | 없음(키 없음 모드) / CONFLICT / 거부 / MISSING | 온보딩의 이미지 소스 단계에서 연동합니다. Pexels MISSING은 이미지 소스에 스톡 사진을 고를 때만 조치합니다 |
| business-profile.md 필수 행 | MISSING / INVALID | 첫 셋업에서는 MISSING이 정상입니다. 온보딩이 채웁니다 |
| 한글 폰트 | MISSING | 준비물의 한글 폰트 |
| photos/business-intro.png | MISSING | 글 끝에 소개 이미지를 넣기로 했을 때만 조치합니다. 그 밖에는 "-" |
| knowledge/design-system.md | 없음(경고) | 온보딩 마지막 단계에서 만들어집니다 |
| 학습 규칙 | 첫 사용 — 정상 | 오류가 아닙니다 |

## blog-onboard 질문 미리보기

온보딩은 블로그 유형에 맞춰 프로필·레퍼런스·주제 키워드·공신 출처·이미지 소스·디자인 시스템을 대화로 채웁니다. 셋업 끝에서 `시작`을 고르지 않았거나 나중에 다시 하려면 Claude 입력창에서:

```
/naver-blog-autopilot:blog-onboard
```

- 온보딩은 API 키·비밀번호를 받지 않고, 설치 명령을 실행하지 않으며, 네이버 로그인은 안내만 합니다.
- 자유 입력은 "아래 항목을 한 번에 적어 주세요"로 한 번에 받고, 표로 되돌려 `맞아요` / `고칠게요`를 확인합니다.
- 이미 채워진 값은 덮지 않습니다. 다시 실행하면 `그대로` / `항목만 고르기` / `전부 다시`를 묻고, `항목만 고르기`는 `기본 정보·글 모양` / `레퍼런스·디자인 시스템` / `주제 키워드·공신 출처` / `이미지 소스` 묶음 중에서 고릅니다.

질문 순서(「기타」는 직접 적는 칸으로 자동으로 붙습니다):

| # | 단계 | 질문 원문 | 고르는 것 | 묻는 조건 |
|---|---|---|---|---|
| Q1 | O1 | 이 블로그는 어떤 블로그인가요? 고른 유형에 맞춰 말투·글 끝 구성·이미지의 기본값을 잡아 드립니다. | `업체` / `전문가` / `개인` / `브랜드` | 항상 |
| 자유 | O2 | 아래 항목을 한 번에 적어 주세요. 모르는 칸은 비워 두셔도 됩니다(★는 꼭 필요합니다). — 유형별 템플릿 | — | 항상 |
| Q2 | O3 | 글을 올릴 네이버 블로그 주소의 ID(blog.naver.com/<여기>)를 알려 주세요 | (`own_blog.blogId` 있으면) `<그 값> 쓰기` / `기타에 직접 적기` / `나중에` · MISMATCH면 `.env 값 <값>` / `own_blog.blogId 값 <값>` / `기타에 직접 적기` | NAVER_BLOG_ID 없음·불일치 |
| Q3 | O4 | 정보성 글 카테고리와 기준 글(레퍼런스 0)을 이렇게 잡을까요? 기준 글은 앞으로 쓸 글의 모양·분량의 기준이 됩니다. | `이대로 — <카테고리> · 「<제목>」` / `카테고리 바꾸기` / `기준 글 바꾸기` / `기준 글 없이` | 자기 글 1편 이상 |
| Q4 | O5 | 글 말투를 고르세요. | `합니다체(격식)` / `해요체(친근)` / `내 글 기준: <합니다체\|해요체>`(기준 글 있을 때) | 항상 |
| Q5 | O6 | 글 끝 마무리에 무엇을 넣을까요? 해시태그 줄은 항상 들어갑니다. (여러 개 선택) | 업체 `문의 헤딩 (기본)` / `소개 이미지 (기본)` / `장소 카드 (기본)` · 브랜드 `문의 헤딩 (기본)` / `소개 이미지 (기본)` | 업체·브랜드 |
| Q5′ | O6 | 글 끝에 문의 헤딩(📞 <문의 헤딩 문구>: <연락처>)을 넣을까요? 해시태그 줄은 항상 들어갑니다. | `넣기 (기본)` / `넣지 않기` | 전문가 (Q5 대신) |
| 자유 | O7a | (찾는 법 안내 뒤) 레퍼런스로 쓸 글 주소나 블로그 ID를 한 줄에 하나씩, 한 번에 0~6개 붙여넣어 주세요. … 없으면 「없음」이라고 적어 주세요. | — | 항상 |
| Q6 | O7a | 레퍼런스로 쓸 글을 고르세요(3~5개 권장, 응답 OK만 쓸 수 있습니다). | `OK인 것 전부 쓰기` / `번호로 고르기` / `레퍼런스 없이 진행` | 주소 1개 이상 |
| 자유 | O7b | 주제 키워드(네이버 연관 검색어를 넓혀 볼 씨앗)를 3~8개 정해 주세요. 제안: <…> 그대로 쓰려면 「그대로」, 바꾸려면 쉼표로 다시 적어 주세요. | — | 항상 |
| Q7 | O7b·O8 | 위 세 표(연관 검색어 · 주제 소스 · 공신 출처)를 이대로 저장할까요? | `전부 이대로 저장` / `고칠 것 있음` / `출처 표는 비워 두기`(개인만) | 항상 |
| Q8 | O9 | 글에 넣을 이미지를 어디서 가져올까요? 여러 개 고를 수 있습니다. | `AI 생성(Gemini 또는 OpenAI)` / `무료 스톡 사진(Pexels)` / `내 사진 폴더` | 항상 |
| Q9 | O9 | 글에 넣을 이미지를 만들 AI 키를 고르세요. 이미 쓰고 계신 키가 있으면 그것을 고르세요. | `Gemini(Google AI Studio)` / `OpenAI(GPT 이미지)` / `아직 없음 — 나중에` | AI 생성 선택 + 키 확인이 OK가 아닐 때 |
| Q10 | O9 | 안내대로 .env에 키를 넣으셨나요? 키는 채팅에 붙여넣지 말고 .env 파일에 직접 넣어 주세요. | `넣었어요 — 확인해 주세요` / `나중에 넣을게요` (재확인 1회: `다시 넣었어요 — 한 번 더 확인` / `나중에 넣을게요`) | 키 안내를 보여 준 소스가 있을 때 |
| 자유 | O10 | 마지막입니다. 없으면 「없음」만 적어도 됩니다. 금칙어 / 꼭 지켜야 할 점 / 배지 문구(개인 제외) / 브랜드 색 | — | 항상 |

끝에 "아래 값으로 knowledge/의 파일을 씁니다. 이미 채워진 다른 값은 그대로 둡니다. 이대로 저장할까요?"(`이대로 저장` / `고칠 것 있음`)를 묻고, 디자인 시스템을 만든 뒤 채운 값과 남은 준비물을 보고합니다. 개인 유형은 Q5가 없습니다(글 끝은 해시태그 줄만).

**유형별 기본값** — Q1에서 고른 유형이 아래 기본값을 잡습니다. 질문에서 바꿀 수 있습니다.

| 유형 | 톤 기본 | 마무리 블록 기본 | 이미지 소스 기본 | 묻지 않는 항목 |
|---|---|---|---|---|
| 업체 | 합니다체 | 문의헤딩, 소개이미지, 장소카드, 해시태그 | ai, photo | — |
| 전문가 | 합니다체 | 문의헤딩, 해시태그 | ai | 장소 검색어 · 소개 이미지 |
| 개인 | 해요체 | 해시태그 | ai, stock | 연락처 · 장소 · 소개 이미지 · 배지 |
| 브랜드 | 합니다체 | 문의헤딩, 소개이미지, 해시태그 | ai | 장소 검색어 |

**레퍼런스(O7a).** 준비물에서 모아 온 주소를 붙여넣으면, 블로그마다 응답(`OK` / `없음` / `비공개` / `네트워크`)·최근 글 수·카테고리·최근 제목을 표로 보여 줍니다. 응답이 `OK`인 것만 레퍼런스로 쓸 수 있습니다. 레퍼런스 없이도 진행할 수 있습니다.

**이미지 키(O9).** 고른 소스의 발급 안내만 화면에 나옵니다(정본: [이미지 소스 연동 안내](../../plugins/naver-blog-autopilot/skills/blog-onboarding/references/image-setup.md)). 키는 채팅에 붙여넣지 말고 `.env`를 열어 직접 넣습니다. `.env`는 아래처럼 엽니다.

macOS(터미널에서):

```bash
open -e ~/naver-blog-work/.env
```

Windows(PowerShell에서):

```powershell
notepad "$HOME\naver-blog-work\.env"
```

키를 넣고 저장한 뒤 Claude 입력창의 질문에 `넣었어요 — 확인해 주세요`를 고르면 비용 없는 키 확인을 돌립니다(이미지를 만들지 않습니다).

## 첫 글 blog-run과 3개 게이트

온보딩과 로그인이 끝났으면 글을 시작합니다. 한 번 실행에 글은 **한 편**입니다. Claude 입력창에서:

```
/naver-blog-autopilot:blog-run
```

진행 중에 담당자가 답해야 하는 곳(게이트)은 세 번입니다. 나머지(초안·근거 검토·SEO·업로드본 빌드·임시저장)는 자동으로 진행합니다.

1. **게이트 1 — 주제 고르기.** 주제 후보 표에서 번호·정보/홍보 유형을 고르고, 고객 지역이 있으면 지역 키워드 2개를 고릅니다("이번 제목 지역"을 미리 계산해 보여 줍니다).
2. **게이트 2 — 초안 피드백.** 제목 A/B안(제목 지역 포함 확인)·톤·길이 피드백을 남깁니다. 고칠 점은 `기타`에 직접 쓰고, 요청마다 "앞으로 계속" / "이번 글만"을 고릅니다. 화면에 나온 경로의 `draft-v2.md`를 직접 고쳐 저장한 뒤 답해도 됩니다.
3. **게이트 3 — 표지와 이미지.** 표지(승인 / 줄바꿈·배지 재생성 / 배경 재생성 / 실사진 배경)를 정한 뒤, 슬롯별로 승인 / 재생성 / 실사진 교체 / 제거를 고릅니다.

끝나면 임시저장 제목·카테고리·태그·이미지 수가 나옵니다. 그다음은 사람이 합니다 — 네이버 앱/웹 → 글쓰기 → 임시저장 글 → 미리보기 → 발행. 미리보기에서 첫 사진(표지)에 '대표' 표시가 있는지 확인합니다.

중간에 멈춘 글(로그인이 안 돼 업로드를 미룬 글, 키·사진이 없어 이미지 단계에서 멈춘 글)은 준비가 끝난 뒤 Claude 입력창에서 이어 갑니다(`001` 자리에 글 번호):

```
/naver-blog-autopilot:blog-run resume 001
```

## 비용

- **이미지**: 제공자마다 다릅니다. **Gemini**는 장당 약 $0.04입니다. 이 값은 `gen_image.py`의 `COST_PER_IMAGE_USD`에 적힌 **추정치**이고 검증된 단가가 아닙니다. 실제 요금은 https://ai.google.dev/pricing 에서 확인하세요. 글 한 편에 필요한 이미지 수는 디자인 시스템 ④(글자 수 ÷ 이미지당 글자 수)로 정해지므로, Gemini 이미지 비용은 대략 이미지 수 × $0.04(추정치 기준)로 어림할 수 있습니다. **OpenAI(GPT 이미지)**는 이 문서에 금액을 적지 않습니다 — OpenAI 요금 페이지(https://openai.com/api/pricing/)에서 모델·크기별 단가를 확인하세요. 어느 쪽이든 재생성도 과금되고, 키 확인(`check_image_key.py`)은 비용이 없습니다. 표지는 배경 1장만 생성 비용이 들고(실사진 배경이면 0), 글자 합성(`make_cover.py`)은 로컬이라 비용이 없습니다.
- **스톡 사진(Pexels)**: 무료입니다.
- **모델 사용량**: 글 한 편에 opus 에이전트가 기본 3회(B·C·B'), 재작업까지 최대 7회 돕니다. 메인 세션의 주제 리서치·이미지 검수도 따로 듭니다. 토큰 사용량은 글 길이와 재작업 횟수에 따라 크게 달라지고 요금제마다 과금 방식이 달라, 이 문서에서는 금액을 단정하지 않고 "opus 호출 3~7회" 정도로만 안내합니다.
- 네이버 임시저장과 법령 조회(law.go.kr DRF)는 비용이 없습니다.

## 계정 안전 수칙

- **하루 1~2편 이내.** 네이버 계정을 자동화된 브라우저로 조작하는 방식이라 과도하게 쓰면 계정이 제재될 수 있습니다. `naver-blog-cli`의 경고 원문은 "과도하게 쓰면 계정이 제재될 수 있습니다. 대량 자동 포스팅 용도로 만들지 않았고, 그런 기능을 넣지 마세요."입니다.
- **임시저장까지만.** 발행은 담당자가 네이버 앱/웹에서 미리보기를 보고 직접 합니다. 업로드 스크립트는 `NAVER_BLOG_READONLY=1`로 발행·삭제 명령을 제거한 상태로만 CLI를 부릅니다.
- **세션 파일은 비밀번호에 준해 다룹니다.** `playwright-state/storage_state.json`은 계정 접근권한 그 자체입니다. 공유·커밋하지 말고(`.gitignore`에 포함돼 있습니다) 다른 사람 컴퓨터로 옮기지 마세요. 비밀번호는 어디에도 저장되지 않습니다.
- **로그인·CAPTCHA·2단계 인증은 사람이.** 에이전트와 스크립트는 로그인을 하지 않습니다.
- **같은 오류로 반복 재시도하지 않습니다.** 업로드 실패는 한 번만 다시 시도하고, 그래도 안 되면 멈추고 보고합니다.

## 자주 묻는 질문

### 1. 발행한 글이 없는데 써도 되나요?

됩니다. 자기 글이 2편 미만이면 업로드본 검사의 관련글 링크 항목(`related_links`)은 경고만 내고 넘어갑니다. 디자인 시스템은 자기 글 1편을 기준 글(레퍼런스 0)로 재는데, 글이 없으면 「측정 전」 기본값으로 만듭니다. 그래도 처음 2편을 네이버에서 직접 써서 발행해 두면 관련글 링크와 글 모양 측정이 제대로 돕니다.

### 2. 해요체로 쓸 수 있나요?

있습니다. 온보딩의 「말투」 질문(Q4)에서 `해요체(친근)`를 고르면 됩니다. 개인 유형은 해요체가 기본값입니다. 말투는 글마다 바꾸지 않고 프로필 `톤`으로 고정합니다. 나중에 바꾸려면 온보딩을 다시 실행해 `항목만 고르기` → `기본 정보·글 모양`을 고릅니다. Claude 입력창에서:

```
/naver-blog-autopilot:blog-onboard
```

### 3. 이미지 키가 없으면 못 쓰나요?

쓸 수 있습니다. 온보딩에서 키를 `나중에`로 미뤄도 진행되고, `blog-run`은 "키 없음 모드"로 키가 없는 이미지 소스의 슬롯을 `보류`로 두고 나머지 소스(내 사진 등)로 채웁니다. 다만 사진이 디자인 시스템의 이미지 수 하한(`min_images`)보다 적으면 임시저장까지 가지 못하고 이미지 단계 뒤에서 멈춥니다. 비용 없이 시작하려면 무료인 Pexels 키를 받는 방법이 있습니다. 키를 준비하면 온보딩을 다시 실행해 「이미지 소스」 항목만 고르세요.

### 4. Pexels가 뭔가요?

무료 스톡 사진 서비스입니다. 키 발급도 무료입니다. Pexels 사진은 출처 표기 의무가 없고(표기는 권장), 플러그인이 사진마다 촬영자·사진 주소를 이미지 계획표의 「출처」 칸에 기록해 둡니다. 온보딩 Q8에서 `무료 스톡 사진(Pexels)`을 고르면 발급 안내가 나옵니다(정본: [이미지 소스 연동 안내](../../plugins/naver-blog-autopilot/skills/blog-onboarding/references/image-setup.md) 2절).

### 5. Windows에서도 되나요?

됩니다. Git for Windows를 가장 먼저 설치해야 하고, 이 문서의 `powershell` 블록을 PowerShell 창에서 실행합니다. 2단계의 python3 별칭 끄기와 `PYTHONUTF8` 설정을 빠뜨리지 마세요. 셋업 진단표 맨 위에 `OS: Windows(Git Bash)`가 나오면 맞게 돈 것입니다. `.env`를 메모장으로 저장해도(Windows 줄바꿈) 그대로 읽힙니다.

### 6. 며칠 지나니 업로드가 안 돼요(세션 만료)

몇 시간 뒤 글쓰기만 로그인 페이지로 바뀌거나 공인 IP가 바뀌면 세션이 풀립니다. "로그인 상태 유지"를 체크하지 않은 경우가 가장 흔합니다. 6단계 로그인 명령을 터미널(Windows는 PowerShell)에서 다시 실행한 뒤, Claude 입력창에서 업로드만 이어 갑니다(`001` 자리에 글 번호):

```
/naver-blog-autopilot:blog-run resume 001
```

세션이 없을 때 `blog-run`은 업로드본 빌드(Step 4)까지 진행하고 업로드만 미룹니다.

### 7. 1.0.0을 쓰고 있었어요. 어떻게 올리나요?

Claude 입력창에서 마켓플레이스를 갱신하고, 플러그인 화면(아래 둘째 줄)의 설치된 플러그인에서 naver-blog-autopilot를 업데이트합니다.

```
/plugin marketplace update woodi-claude-plugins
/plugin
```

그다음 작업 폴더에서 셋업을 다시 실행해 `scripts/`를 최신본으로 바꿉니다(`knowledge/`는 보존됩니다). Claude 입력창에서:

```
/naver-blog-autopilot:blog-setup ~/naver-blog-work
```

1.0.0 프로필에는 새 행이 없어 `profile: MISSING 블로그 유형,톤,마무리 블록,이미지 소스`가 나오는 것이 정상입니다. 셋업 끝의 온보딩 질문에서 `시작`을 고르거나, Claude 입력창에서 온보딩을 한 번 실행합니다.

```
/naver-blog-autopilot:blog-onboard
```

온보딩은 이미 채워진 값을 덮지 않습니다. 1.0.0과 같은 글 끝(문의 헤딩·소개 이미지·장소 카드·해시태그)과 합니다체를 유지하려면 유형 `업체`의 기본값을 그대로 고릅니다. 톤·고객 지역·마무리 블록을 1.0.0과 다르게 고르면 작업 폴더의 `knowledge/naver-seo-checklist.md`를 플러그인 최신본으로 교체하고, 디자인 시스템도 `blog-design-system` 갱신 모드로 다시 만들어 달라고 Claude에게 요청하세요(1.0.0 판에는 합니다체·문의 헤딩·지역이 고정값으로 적혀 있습니다).

### 8. 글을 고쳐 달라고 하려면 어떻게 하나요?

게이트 2의 "톤·길이·내용" 질문에서 `기타`를 고르고 요청을 직접 씁니다. **구체적으로**(어디를, 어떻게 바꿀지), **한 요청에 한 가지**, **이유가 있으면 한마디** 쓰면 잘 반영됩니다. 요청마다 "앞으로 계속"(다음 글에도 규칙으로 적용) / "이번 글만"을 고릅니다. 질문 화면 밖에서 "도입이 너무 딱딱해요"처럼 말해도 피드백으로 기록됩니다. 네이버에서 임시저장 글을 직접 고쳐 발행했다면, 발행 글 주소를 주고 Claude 입력창에서 알려 줍니다(`003`은 글 번호):

```
/naver-blog-autopilot:blog-feedback 003 https://blog.naver.com/<블로그 ID>/<글번호>
```

바뀐 점을 비교해 다음 글에도 반영할지 묻습니다.

---

Windows는 아직 실기 검증 전입니다.
