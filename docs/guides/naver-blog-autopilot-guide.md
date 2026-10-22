# naver-blog-autopilot 설치·사용 가이드

네이버 블로그 정보성 글을 **주제 찾기부터 임시저장까지** 자동으로 만들어 주는 Claude Code 플러그인입니다. 이 가이드는 처음 설치하는 사람이 첫 글을 임시저장하고, 그다음 글부터 혼자 계속 쓸 수 있게 되는 데 필요한 내용을 순서대로 담았습니다.

| 항목 | 내용 |
|---|---|
| 플러그인 | `naver-blog-autopilot` (마켓플레이스 `heesun-woodi/woodi-claude-plugins`, 공개) |
| 이 가이드의 기준 버전 | 1.1.2 |
| 지원 OS | macOS · Windows(Git for Windows 필요 — 실기 검증 전) |
| 라이선스 | CC BY-NC 4.0 — 출처를 표기하면 자유롭게 쓰고 고칠 수 있습니다. 유료 서비스·판매 등 상업적 이용은 허용하지 않습니다 |
| 만든 사람 | heesun-woodi |

---

## 1. 이 플러그인이 하는 일

글 한 편은 아래 순서로 만들어집니다. **●** 표시가 있는 곳만 사람이 답하고, 나머지는 Claude가 진행합니다.

```text
주제 후보 찾기 ─● 주제 고르기
  → 초안 쓰기 → 사실 검토(법령·공공기관 출처) → 고치기 + 네이버 SEO 다듬기
  ─● 초안 확인(제목·톤·길이)
  → 이미지 만들기(AI 생성·무료 스톡 사진·내 사진) + 대표 이미지(표지)
  ─● 이미지 확인
  → 업로드본 만들기 → 네이버 임시저장
  ─● (사람이 네이버에서) 미리보기 → 발행
```

**이 플러그인이 하지 않는 것**

- **발행하지 않습니다.** 임시저장까지만 하고, 발행 버튼은 사람이 네이버 앱이나 웹에서 직접 누릅니다.
- **로그인하지 않습니다.** 네이버 로그인·CAPTCHA·2단계 인증은 사람이 한 번 직접 합니다. 비밀번호는 어디에도 저장되지 않습니다.
- **숫자를 지어내지 않습니다.** 수치·일정·비용·법령 조항은 실제로 열어 본 출처가 있을 때만 씁니다.
- **대량 자동 포스팅용이 아닙니다.** 하루 1~2편 이내로 씁니다(8장 계정 안전).

**설치하면 생기는 명령** (모두 Claude 입력창에 입력합니다)

| 명령 | 하는 일 | 언제 |
|---|---|---|
| `/naver-blog-autopilot:blog-setup` | 환경 진단, 작업 폴더 준비 | 처음 한 번, 그리고 업데이트 뒤 |
| `/naver-blog-autopilot:blog-onboard` | 내 블로그에 맞게 대화로 설정 | 처음 한 번, 설정을 바꿀 때 |
| `/naver-blog-autopilot:blog-run` | 글 한 편 만들기 | 글 쓸 때마다 |
| `/naver-blog-autopilot:blog-feedback` | 의견 남기기·발행본 비교·규칙 보기 | 필요할 때 |

---

## 2. 이 가이드 읽는 법 — 「터미널」과 「Claude 입력창」

명령을 넣는 곳이 두 군데입니다. **이 구분이 설치에서 가장 중요합니다.**

- **「터미널에서」** — macOS는 **터미널** 앱, Windows는 **PowerShell** 창(시작 → "PowerShell")입니다.
- **「Claude 입력창에서」** — 터미널에서 `claude`를 실행하면 나오는 입력칸입니다. `/`로 시작하는 줄은 **여기에** 칩니다.

모든 명령 상자 바로 위에 **macOS(터미널에서)**, **Windows(PowerShell에서)**, **Claude 입력창에서** 중 하나를 적어 두었습니다. 그 표시대로 붙여넣고 Enter를 누릅니다. 내 OS가 아닌 쪽 상자는 건너뜁니다.

> 터미널 명령을 Claude 입력창에 넣거나, `/`로 시작하는 줄을 터미널에 넣으면 동작하지 않습니다.

**권한 확인 창.** Claude Code가 명령을 실행하거나 파일을 쓰기 전에 "허용할까요?"라고 물을 수 있습니다. 이 플러그인의 셋업·온보딩·글쓰기 단계에서 나오는 확인은 작업 폴더 안의 스크립트 실행·파일 쓰기와, 사실 검토용 법령·공공기관 사이트 조회이니, 내용을 읽어 보고 허용합니다. API 키나 비밀번호를 입력하라는 요청은 이 플러그인이 하지 않습니다.

---

## 3. 시작 전 준비물

- [ ] **Claude Code를 쓸 수 있는 계정.** Claude 유료 요금제(Pro·Max 등) 또는 결제가 설정된 Anthropic API(Console) 계정이 필요합니다. 무료 요금제로는 Claude Code를 쓸 수 없습니다. 글 쓰는 에이전트는 opus 모델을 쓰므로, 요금제마다 다른 사용 가능 모델과 사용량 한도를 미리 확인해 두세요.
- [ ] **네이버 블로그와 발행한 글 2편 이상(권장).** 글이 없어도 쓸 수 있지만, 자기 글이 있어야 관련글 링크와 글 모양 측정이 제대로 됩니다(10장 FAQ 1).
- [ ] **참고할 블로그 글 주소 3~5개.** 네이버에서 "<내 주제> 방법"이나 "<상품·서비스> <지역>"으로 검색해, 구성과 말투가 마음에 드는 글의 주소를 모아 둡니다. 온보딩에서 한 번에 붙여넣습니다.
- [ ] **이미지 소스 하나 이상.** 아래 중에서 고릅니다. 키가 없어도 시작은 할 수 있습니다(10장 FAQ 3).

  | 소스 | 비용 | 준비 |
  |---|---|---|
  | AI 생성 — Gemini | 장당 약 $0.04(추정치) | 결제(Billing)가 설정된 Google Cloud 프로젝트의 키 |
  | AI 생성 — OpenAI(GPT 이미지) | OpenAI 요금표 참고 | 결제 수단 등록, 필요하면 조직 인증 |
  | 무료 스톡 사진 — Openverse | 무료 | 키가 필요 없습니다(CC0·퍼블릭 도메인 사진만). Pexels 키가 이미 있는 사람만 Pexels를 골라 쓸 수 있습니다(신규 키 발급 일시 중단) |
  | 내 사진 | 무료 | 작업 폴더의 `photos/`에 넣기 |

- [ ] **한글 폰트(대표 이미지 제목용).** Pretendard 글꼴의 `Pretendard-ExtraBold.otf`·`Pretendard-SemiBold.otf` 두 파일을 설치하면 가장 좋습니다. macOS는 `~/Library/Fonts/`에 넣고, Windows는 파일을 우클릭해 "설치"합니다. 파일은 [Pretendard 배포 페이지](https://github.com/orioncactus/pretendard/releases)에서 받습니다. 없으면 macOS 기본 애플SD산돌고딕, Windows 기본 맑은 고딕 Bold로 대신합니다.
- [ ] **macOS만: 명령줄 도구(git 포함).** 새 Mac에는 git이 없어 설치 명령이 멈춥니다. 터미널에서 아래를 한 번 실행하고, 뜨는 창에서 "설치"를 누릅니다. 이미 있으면 "already installed"가 나옵니다.

  macOS(터미널에서):

  ```bash
  xcode-select --install
  ```

- [ ] **Windows만: Git for Windows.** [Git for Windows](https://git-scm.com/downloads/win)를 **가장 먼저** 설치합니다. 없으면 플러그인이 동작하지 않습니다.
- [ ] **업체·브랜드: 소개 이미지 한 장.** 업체·브랜드 유형의 기본값은 글 끝에 소개 이미지를 넣습니다. 업체명·연락처·주소가 담긴 이미지를 준비해 두었다가, 4-5 셋업 뒤 작업 폴더의 `photos/business-intro.png`(파일명 그대로)로 넣습니다. 준비가 안 됐으면 온보딩의 글 끝 구성에서 소개 이미지를 빼면 됩니다. 이 파일 없이 소개 이미지를 켜 두면 글쓰기가 시작되지 않습니다.

---

## 4. 설치 (6단계)

### 4-1. Claude Code 설치 — 터미널에서

macOS(터미널에서):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Windows(PowerShell에서 — Git for Windows를 먼저 설치한 뒤):

```powershell
irm https://claude.ai/install.ps1 | iex
```

설치가 끝나면 **터미널 창을 닫고 새로 엽니다.** 새로 설치한 프로그램은 새 창에서부터 찾을 수 있습니다. 처음 `claude`를 실행하면 Claude 계정 로그인 창이 뜹니다. 화면 안내대로 로그인합니다.

### 4-2. uv와 Python 준비 — 터미널에서

macOS(터미널에서):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows(PowerShell에서):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

uv 설치가 끝나면 **터미널(Windows는 PowerShell) 창을 닫고 새로 엽니다.** 새 창에서 아래 명령으로 Python 3.12를 기본 Python으로 설치합니다. macOS 기본 `python3`는 버전이 낮고, Windows 기본 `python3`는 Microsoft Store로 보내는 가짜 별칭이라 둘 다 쓸 수 없기 때문입니다.

macOS(새 터미널에서):

```bash
uv python install 3.12 --default
```

Windows(새 PowerShell에서):

```powershell
uv python install 3.12 --default
```

Windows는 두 가지를 더 합니다. 설정 → 앱 → 고급 앱 설정 → **앱 실행 별칭**에서 `python.exe`·`python3.exe`(앱 설치 관리자)를 끕니다. 그리고 한글 Windows에서 출력이 깨져 멈추지 않도록 아래를 한 번 실행합니다.

Windows(PowerShell에서):

```powershell
setx PYTHONUTF8 1
```

여기까지 했으면 **터미널(Windows는 PowerShell) 창을 모두 닫고 새로 엽니다.** 새 창에서 아래가 각각 버전 번호를 보여 주면 4-3으로 갑니다(`python3`는 3.11 이상이어야 합니다).

macOS(새 터미널에서):

```bash
claude --version
uv --version
python3 --version
```

Windows(새 PowerShell에서):

```powershell
claude --version
uv --version
python3 --version
```

하나라도 찾을 수 없다고 나오면 4-3 끝의 `uv tool update-shell`을 실행하고 창을 새로 엽니다. 세 프로그램 모두 같은 폴더(`~/.local/bin`)에 설치됩니다.

### 4-3. naver-blog-cli와 Chromium 설치 — 터미널에서

네이버 임시저장은 외부 도구 [naver-blog-cli](https://github.com/spegas/naver-blog-cli)(MIT)가 맡습니다. 플러그인에 들어 있지 않아 따로 설치합니다.

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

마지막 줄의 `git clone`은 4-6단계 로그인에 쓰는 `login_setup.py`를 받아 둡니다.

`naver-blog-cli`를 찾을 수 없다는 오류가 나면 아래를 실행한 뒤 창을 새로 엽니다.

macOS(터미널에서):

```bash
uv tool update-shell
```

Windows(PowerShell에서):

```powershell
uv tool update-shell
```

### 4-4. 작업 폴더를 만들고 Claude Code 열기 — 터미널에서

작업 폴더는 글과 설정이 쌓이는 곳입니다. **글을 쓸 때는 매번 이 폴더에서 Claude Code를 엽니다.**

macOS(터미널에서):

```bash
mkdir -p ~/naver-blog-work && cd ~/naver-blog-work && claude
```

Windows(PowerShell에서):

```powershell
mkdir -Force ~\naver-blog-work; cd ~\naver-blog-work; claude
```

### 4-5. 플러그인 설치와 셋업 — Claude 입력창에서

마켓플레이스를 추가하고 플러그인을 설치합니다. 공개 저장소라 GitHub 로그인이 필요 없습니다.

Claude 입력창에서:

```
/plugin marketplace add heesun-woodi/woodi-claude-plugins
/plugin install naver-blog-autopilot@woodi-claude-plugins
```

설치한 뒤 명령이 보이지 않으면 Claude 입력창에서:

```
/reload-plugins
```

이어서 셋업합니다. Claude 입력창에서:

```
/naver-blog-autopilot:blog-setup ~/naver-blog-work
```

셋업은 환경을 진단하고, 작업 폴더에 설정 파일(`knowledge/`)과 스크립트(`scripts/`)를 복사한 뒤 진단표를 보여 줍니다(5-1). 블로그 ID를 물으면 `blog.naver.com/<여기>`의 ID를 답합니다. 마지막에 **"지금 온보딩을 시작할까요?"** 질문이 나오면 `시작`을 고릅니다(5-2). **온보딩이 끝나면 4-6단계(네이버 로그인)로 돌아옵니다.**

### 4-6. 네이버 로그인(1회, 사람이 직접) — 터미널에서

화면에 `blog-setup`의 「4단계 로그인 절차」라고 나오면 이 단계를 말합니다.

Claude 입력창이 아니라 **터미널**에서 실행합니다. Claude Code가 열린 창과 다른 터미널 창을 하나 더 열면 편합니다. 실행하면 브라우저가 열립니다.

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

브라우저에서 직접 로그인합니다. **로그인 버튼을 누르기 전에 "로그인 상태 유지"를 꼭 체크하세요.** 체크하지 않으면 몇 시간 뒤 업로드가 로그인 화면에서 막힙니다. 로그인이 확인되면 자동으로 저장하고 브라우저를 닫습니다. 5분 안에 로그인하지 않으면 아무것도 저장하지 않고 끝나니, 그때는 같은 명령을 다시 실행합니다.

로그인이 끝나면 작업 폴더에 `playwright-state/` 폴더가 생깁니다. 이 폴더는 계정 열쇠와 같으니 다른 사람에게 주거나 인터넷에 올리지 마세요.

로그인한 뒤 셋업을 한 번 더 실행합니다. Claude 입력창에서:

```
/naver-blog-autopilot:blog-setup ~/naver-blog-work
```

조치 칸이 모두 `-`이면 준비가 끝난 것입니다. 소개 이미지를 쓰지 않기로 했다면 그 줄은 MISSING이어도 됩니다. 무료 스톡 사진은 키가 필요 없어 보통 `STOCK: OK (openverse, 키 불필요)`로 나옵니다.

---

## 5. 내 블로그에 맞추기

### 5-1. 셋업 진단표 읽는 법

진단표는 `항목 | 상태 | 조치` 세 칸입니다. 갖춰진 항목은 "확인됨"으로 나오고, 빠진 항목에는 대부분 내 OS에 맞는 명령이 함께 나옵니다. 그 명령은 **터미널**에서 실행합니다.

| 항목 | 이렇게 나오면 | 할 일 |
|---|---|---|
| uv · python3 ≥ 3.11 | MISSING | 4-2단계(`uv python install 3.12 --default` 뒤 새 창) |
| Chromium · naver-blog-cli | MISSING | 4-3단계 |
| PYTHONUTF8 (Windows만) | NOT_SET | 4-2단계 `setx PYTHONUTF8 1` 뒤 PowerShell 창을 새로 열고 4-4단계 명령으로 Claude Code를 다시 엽니다 |
| 네이버 세션 | blogId 없음 | 첫 셋업에서는 정상입니다. 블로그 ID를 넣은 뒤 셋업을 다시 돌리면 바뀝니다 |
| 네이버 세션 | 로그인 필요 | 4-6단계 로그인 |
| 네이버 세션 | 다른 계정 로그인 | 글을 올릴 블로그의 계정으로 4-6단계를 다시 합니다 |
| 블로그 ID | MISSING · MISMATCH | 셋업·온보딩이 물으면 블로그 ID를 답합니다 |
| 이미지 AI 키 | 없음 · MISSING | 온보딩의 이미지 소스 단계에서 연결합니다. AI 생성을 쓰지 않으면 MISSING이어도 됩니다 |
| 무료 스톡 사진 | OK (openverse, 키 불필요) | 할 일 없음. MISSING·CONFLICT가 나오면 `.env`의 `STOCK_PROVIDER=` 줄을 `openverse`로 고치거나 그 줄을 지웁니다. 스톡 사진을 쓰지 않으면 무시해도 됩니다 |
| business-profile.md 필수 행 | MISSING | 첫 셋업에서는 정상입니다. 온보딩이 채웁니다 |
| 한글 폰트 | MISSING | 3장 준비물의 한글 폰트 |
| photos/business-intro.png | MISSING | 글 끝에 소개 이미지를 넣기로 했을 때만 조치합니다 |
| knowledge/design-system.md | 없음(경고) | 온보딩 마지막 단계에서 만들어집니다 |
| 학습 규칙 | 첫 사용 — 정상 | 오류가 아닙니다 |

### 5-2. 온보딩 — 대화로 설정하기(약 10분)

온보딩은 질문 몇 개로 내 블로그의 기본값을 잡고, 설정 파일을 채우고, 글 모양 기준(디자인 시스템)까지 만듭니다. 셋업 끝에서 `시작`을 고르지 않았거나 나중에 다시 하려면 Claude 입력창에서:

```
/naver-blog-autopilot:blog-onboard
```

**온보딩이 묻는 것**

| 순서 | 묻는 것 | 참고 |
|---|---|---|
| 1 | 블로그 유형 — `업체` / `전문가` / `개인` / `브랜드` | 고른 유형에 맞춰 아래 기본값이 잡힙니다 |
| 2 | 기본 정보(한 번에 적기) — 이름, 다루는 상품·서비스나 주제, 연락처, 주소, 고객 지역, 강점 | 모르는 칸은 비워도 됩니다. 고객 지역을 비우면 제목에 지역을 넣지 않습니다 |
| 3 | 블로그 ID | 셋업에서 이미 넣었으면 묻지 않습니다 |
| 4 | 정보성 글 카테고리와 기준 글 | 자기 블로그 글을 불러와 보여 줍니다. 기준 글은 앞으로 쓸 글의 모양·분량 기준이 됩니다 |
| 5 | 말투 — `합니다체(격식)` / `해요체(친근)` | 기준 글이 있으면 그 글의 말투를 추천합니다 |
| 6 | 글 끝 구성 — 문의 헤딩 · 소개 이미지 · 장소 카드 | 해시태그 줄은 항상 들어갑니다. 개인 유형은 묻지 않습니다 |
| 7 | 레퍼런스 글 주소 붙여넣기(0~6개) | 준비물에서 모은 주소. 실제로 있는 블로그인지 확인하고 글 모양을 측정합니다 |
| 8 | 주제 키워드 3~8개 | 네이버 연관 검색어로 넓혀 주제 후보의 씨앗으로 저장합니다 |
| 9 | 주제 소스·공신 출처 확인 | 사실 검토에 쓸 공공기관·법령 출처 후보를 제안합니다 |
| 10 | 이미지 소스 — AI 생성 / 무료 스톡 사진(키 없이 바로) / 내 사진 | AI 생성을 고르면 키 발급 안내가 나옵니다(5-3). 무료 스톡 사진은 키 없이 바로 씁니다 |
| 11 | 금칙어·꼭 지켜야 할 점 | 없으면 「없음」 |

마지막에 채운 값을 표로 보여 주고 "이대로 저장할까요?"를 묻습니다. 저장한 뒤 디자인 시스템을 만들고, 남은 준비물(로그인·폰트 등)을 알려 줍니다.

**블로그 유형별 기본값** — 질문에서 바꿀 수 있습니다.

| 유형 | 말투 | 글 끝 구성 | 이미지 소스 |
|---|---|---|---|
| 업체 | 합니다체 | 문의 헤딩 · 소개 이미지 · 장소 카드 · 해시태그 | AI 생성 · 내 사진 |
| 전문가 | 합니다체 | 문의 헤딩 · 해시태그 | AI 생성 |
| 개인 | 해요체 | 해시태그 | AI 생성 · 무료 스톡 사진 |
| 브랜드 | 합니다체 | 문의 헤딩 · 소개 이미지 · 해시태그 | AI 생성 |

**온보딩은 이렇게 동작합니다**

- API 키와 비밀번호는 받지 않습니다. 키는 채팅에 붙여넣지 말고 `.env` 파일에 직접 넣습니다(5-3).
- 이미 채운 값은 덮지 않습니다. 다시 실행하면 `그대로` / `항목만 고르기` / `전부 다시` 중에서 고릅니다.

### 5-3. 이미지 키 넣기

무료 스톡 사진은 키가 필요 없습니다. 이 절은 AI 생성 키(그리고 Pexels 키가 이미 있는 경우)에만 해당합니다. 온보딩에서 고른 소스의 발급 안내가 화면에 나옵니다. 발급 절차의 자세한 내용은 [이미지 소스 연동 안내](https://github.com/heesun-woodi/woodi-claude-plugins/blob/main/plugins/naver-blog-autopilot/skills/blog-onboarding/references/image-setup.md)에 있습니다.

발급받은 키는 작업 폴더의 `.env` 파일에 넣습니다. 아래 명령으로 `.env`를 엽니다.

macOS(터미널에서):

```bash
open -e ~/naver-blog-work/.env
```

Windows(PowerShell에서):

```powershell
notepad "$HOME\naver-blog-work\.env"
```

열린 `.env` 파일 안에는 `GEMINI_API_KEY=` 같은 줄이 이미 있습니다. 고른 소스의 줄에서 `=` 바로 뒤에 키만 붙여 넣고 저장합니다. 쓰지 않는 줄은 그대로 비워 둡니다.

`.env` 파일 안에서(Claude 입력창이 아닙니다) — 예:

```text
GEMINI_API_KEY=AIzaSy...
```

키는 괄호·따옴표·공백 없이 키 글자만 넣습니다. Pexels 키가 이미 있는 분만(선택) `PEXELS_API_KEY=` 줄에 넣으면 무료 스톡 사진을 Pexels에서 받습니다. Pexels는 신규 키 발급을 일시 중단했으니, 키가 없으면 그 줄은 비워 둡니다(키 없이 Openverse를 씁니다).

저장한 뒤 온보딩 질문에 `넣었어요 — 확인해 주세요`를 고르면 비용 없이 키를 확인합니다(이미지를 만들지 않습니다).

- **Gemini**: 결제가 설정되지 않은 무료 키는 확인은 통과해도 이미지 생성에서 실패(429)합니다.
- **OpenAI**: 키 확인이 통과해도 이미지 생성에서 403이 나면 조직 인증(Verify Organization)이 필요한 것입니다.
- **무료 스톡 사진**: 키가 필요 없습니다. Openverse의 CC0·퍼블릭 도메인 사진만 받고, 사진 출처는 플러그인이 기록해 둡니다. Pexels 키가 이미 있으면 Pexels를 씁니다(선택).

---

## 6. 글 쓰기

### 6-1. 글 한 편 만들기

작업 폴더에서 Claude Code를 연 뒤(4-4단계 명령), Claude 입력창에서:

```
/naver-blog-autopilot:blog-run
```

한 번 실행에 글은 **한 편**입니다. 진행 중에 사람이 답하는 곳은 주로 아래 세 번입니다. 가끔 사실 확인 질문이나 새 규칙 승인 질문이 더 나옵니다.

**● 게이트 1 — 주제 고르기**

주제 후보 8~10개가 표로 나옵니다. 번호와 유형(정보/홍보)을 고릅니다. 보기에는 추천 후보 4개가 나오고, 다른 번호는 `기타`에 적습니다. 프로필에 고객 지역이 있으면 지역 키워드 2개도 고릅니다. 앞으로 빼거나 더 다룰 주제가 있으면 `기타`에 적습니다(예: "가격 비교 주제를 더 다뤄 주세요").

**● 게이트 2 — 초안 확인**

초안 전문과 제목 A안·B안, 사실 검토 요약이 나옵니다.

- 제목은 `A안` / `B안`을 고르거나 직접 씁니다.
- 내용은 `그대로 진행` / `더 짧고 간결하게` / `문장을 더 짧게` 중에서 고르거나, `기타`에 고칠 점을 직접 씁니다.
- 고칠 점마다 **"앞으로 계속"**(다음 글에도 규칙으로 적용) 또는 **"이번 글만"** 중 하나를 고릅니다.
- 화면에 나온 `draft-v2.md` 파일을 메모장이나 텍스트 편집기로 직접 고쳐 저장한 뒤 답해도 됩니다. 고친 부분은 다음 글에도 반영할지 묻습니다.
- 글 끝의 "함께 읽으면 좋은 글"은 내 블로그 글 중 주제가 맞는 것으로 채웁니다. 맞는 글이 2편 미만이면 생략하고, 생략했다는 한 줄을 보여 줍니다. 꼭 걸고 싶은 글이 있으면 그 글 주소를 `기타`에 적습니다.

**● 게이트 3 — 이미지 확인**

먼저 대표 이미지(표지)를 정합니다(`승인` / `재생성 — 줄바꿈·배지 문구` / `재생성 — 배경` / `실사진 배경으로`). 그다음 본문 이미지마다 고릅니다. AI 이미지는 `승인` / `재생성` / `실사진으로 교체` / `제거`, 스톡 사진은 `승인` / `다른 사진으로(검색어 수정)` / `실사진으로 교체` / `제거`입니다. 내 사진 자리는 후보 파일(최대 3개) 중 하나 또는 `제거`를 고릅니다. 키가 없어 `보류`된 자리는 `보류 유지` / `제거` / `실사진으로 교체` 중에서 고릅니다. 바꿀 점은 `기타`에 적습니다. 다시 만들거나 바꾼 요청이 있으면 끝에 "앞으로도 지킬 것이 있나요?"를 한 번 묻습니다.

### 6-2. 네이버에서 발행하기(사람이 직접)

`blog-run`이 끝나면 임시저장된 글의 제목·카테고리·태그·이미지 수가 나옵니다. 그다음은 네이버에서 직접 합니다.

1. 네이버 블로그 앱이나 웹 → **글쓰기** → **임시저장 글**을 엽니다.
2. **미리보기**로 글을 봅니다. 첫 사진(표지)에 '대표' 표시가 있는지 확인합니다.
3. 고칠 곳이 있으면 고치고 **발행**합니다.

네이버에서 직접 고쳐서 발행했다면 6-4의 "발행 후 알려 주기"로 고친 내용을 플러그인에 알려 주세요. 다음 글부터 반영됩니다.

### 6-3. 이어 하기·다시 보기

| 하고 싶은 것 | Claude 입력창에서 |
|---|---|
| 주제 번호를 미리 정해 시작(오늘 만든 후보 표의 3번) | `/naver-blog-autopilot:blog-run 3` |
| 중간에 멈춘 글 이어 가기(로그인·키·사진 준비 뒤) | `/naver-blog-autopilot:blog-run resume 001` |
| 만든 글의 진행 상황 보기 | `/naver-blog-autopilot:blog-run report 001` |

`001`은 글 번호입니다. 글은 작업 폴더의 `work/posts/001-…` 같은 폴더에 쌓입니다.

**멈추는 경우와 이어 가는 법**

- **네이버 로그인이 안 돼 있을 때**: 업로드본까지 만들고 업로드만 미룹니다. 4-6단계 로그인 뒤 `resume`으로 이어 갑니다.
- **이미지 키·사진이 부족할 때**: 글을 시작할 때 `초안까지만 진행(업로드 불가)` / `중단하고 키·사진 준비`를 묻습니다. 초안까지만 진행하면 이미지 단계 뒤에서 멈추고, 키나 사진을 준비한 뒤 `resume`으로 이어 갑니다.

### 6-4. 글을 고쳐 달라고 하기와 학습

고쳐 달라고 한 내용은 그 글에서 끝나지 않고 **다음 글에도 반영될 수 있습니다.** "앞으로 계속"을 고른 요청은 글이 끝날 때 규칙이 되고, 다음 글부터 자동으로 적용됩니다.

**잘 반영되는 요청 쓰는 법**

- **구체적으로** — 어디를, 어떻게 바꿀지 씁니다.
- **한 요청에 한 가지** — 여러 개면 번호를 붙여 나눕니다.
- **이유가 있으면 한마디** — 규칙으로 정리할 때 근거가 됩니다.

| 이렇게 쓰면 잘 안 됩니다 | 이렇게 쓰면 잘 됩니다 |
|---|---|
| 좀 더 좋게 써 주세요 | 2️⃣ 절 첫 문단을 고객 상황 예시로 시작해 주세요 |
| 너무 딱딱해요 | 한 문장을 40자 안쪽으로 끊어 주세요 |
| 내용 추가해 주세요, FAQ도 이상해요 | 1) 신청부터 완료까지 걸리는 기간을 넣어 주세요 2) FAQ 마지막 질문을 비용 질문으로 바꿔 주세요 |

말투(합니다체·해요체)는 글마다 바꾸지 않고 프로필로 고정합니다. 바꾸려면 온보딩을 다시 실행합니다(6-5).

**발행 후 알려 주기** — 네이버에서 직접 고쳐 발행한 경우, 발행 글 주소를 주면 고친 부분을 비교해 다음 글에 반영할지 묻습니다. Claude 입력창에서(`003`은 글 번호):

```
/naver-blog-autopilot:blog-feedback 003 https://blog.naver.com/<블로그 ID>/<글번호>
```

| 하고 싶은 것 | Claude 입력창에서 |
|---|---|
| 특정 글에 대한 의견 남기기 | `/naver-blog-autopilot:blog-feedback 003` |
| 가장 최근 글에 의견 남기기 | `/naver-blog-autopilot:blog-feedback` |
| 지금 적용 중인 규칙 보기 | `/naver-blog-autopilot:blog-feedback rules` |

규칙을 직접 고치거나 지우려면 작업 폴더의 `knowledge/learned-preferences.md`를 엽니다. 더 쓰지 않을 규칙은 `## 보류·삭제` 표로 옮깁니다.

**학습 규칙이 바꿀 수 없는 것** — 금칙어와 "꼭 지켜야 할 점", 이미지 기본 규칙(이미지 속 글자·얼굴 클로즈업·로고 금지, 사진 재사용 금지), 출처 없는 수치 금지는 항상 지켜집니다.

### 6-5. 설정 바꾸기

말투, 글 끝 구성, 레퍼런스, 주제 키워드, 이미지 소스를 바꾸려면 온보딩을 다시 실행해 `항목만 고르기`를 고릅니다. Claude 입력창에서:

```
/naver-blog-autopilot:blog-onboard
```

| 묶음 | 바뀌는 것 |
|---|---|
| 기본 정보·글 모양 | 블로그 유형, 기본 정보, 말투, 글 끝 구성, 금칙어 |
| 레퍼런스·디자인 시스템 | 기준 글, 레퍼런스, 글 모양 기준 |
| 주제 키워드·공신 출처 | 주제 씨앗, 연관 검색어, 사실 검토 출처 |
| 이미지 소스 | AI 생성·스톡 사진·내 사진, 키 연결 |

설정 파일은 작업 폴더의 `knowledge/`에 있고 직접 고쳐도 됩니다. 가장 자주 보는 파일은 `knowledge/business-profile.md`(프로필·금칙어)입니다.

### 6-6. 플러그인 업데이트

새 버전이 나오면 마켓플레이스를 갱신합니다. 아래 둘째 줄 `/plugin`을 실행하면 나오는 화면의 설치된 플러그인 목록에서 naver-blog-autopilot을 업데이트합니다.

Claude 입력창에서:

```
/plugin marketplace update woodi-claude-plugins
/plugin
```

업데이트한 뒤 Claude 입력창에서 `/reload-plugins`를 실행하거나 Claude Code를 다시 엽니다. 그다음 작업 폴더에서 셋업을 다시 실행해 `scripts/`를 최신본으로 바꿉니다. 내 설정(`knowledge/`)은 그대로 남습니다. Claude 입력창에서:

```
/naver-blog-autopilot:blog-setup ~/naver-blog-work
```

1.1.1에서 올리는 경우, 위처럼 셋업을 다시 실행하면 끝입니다. 무료 스톡 사진은 키 없이 Openverse를 쓰고, Pexels 키가 이미 `.env`에 있으면 자동으로 Pexels를 계속 씁니다. 1.1.0에서 올리는 경우, 이미 채워진 디자인 시스템은 그대로 쓰면 됩니다. 디자인 시스템을 아직 만들지 않았다면 온보딩에서 「레퍼런스·디자인 시스템」을 골라 한 번 만듭니다. 1.0.0에서 올리는 경우는 10장 FAQ 7을 봅니다.

---

## 7. 비용

| 항목 | 비용 |
|---|---|
| AI 이미지 — Gemini | 장당 약 $0.04(추정치 — 정확한 단가는 [Google 요금표](https://ai.google.dev/pricing)). 다시 만들기도 과금됩니다 |
| AI 이미지 — OpenAI | [OpenAI 요금표](https://openai.com/api/pricing/)에서 확인 |
| 대표 이미지 배경 | AI로 만들면 이미지 1장 값, 내 사진이나 스톡 사진 배경이면 무료 |
| 무료 스톡 사진 — Openverse(기본) · Pexels(선택) | 무료(요청 한도만 있음) |
| 대표 이미지 제목 합성 | 무료(내 컴퓨터에서 처리) |
| 키 확인 | 무료(이미지를 만들지 않음) |
| 네이버 임시저장·법령 조회 | 무료 |
| Claude 사용량 | 글 한 편에 Claude 작업자 호출 3~7회와 주제 찾기·이미지 확인이 듭니다. 요금제마다 과금 방식이 달라 금액은 단정하지 않습니다 |

---

## 8. 계정 안전 수칙

- **하루 1~2편 이내로 씁니다.** 자동화된 브라우저로 네이버를 조작하는 방식이라, 과도하게 쓰면 계정이 제재될 수 있습니다.
- **임시저장까지만 합니다.** 발행은 사람이 미리보기를 본 뒤 직접 합니다. 플러그인은 발행·삭제 명령을 쓰지 않습니다.
- **`playwright-state/` 폴더는 비밀번호처럼 다룹니다.** 계정 접근권한 그 자체라서 공유하거나, 커밋하거나, 다른 컴퓨터로 옮기지 않습니다.
- **로그인·CAPTCHA·2단계 인증은 사람이 합니다.** 플러그인은 로그인하지 않습니다.
- **`.env`의 키는 채팅에 붙여넣지 않습니다.** 실수로 붙여넣었다면 발급 페이지에서 그 키를 폐기하고 새로 만듭니다.

---

## 9. 문제 해결

| 증상 | 원인 | 할 일 |
|---|---|---|
| `/naver-blog-autopilot:…` 명령이 안 보임 | 설치 직후 목록이 갱신되지 않음 | Claude 입력창에서 `/reload-plugins` |
| "프로필이 완성되지 않았습니다"로 `blog-run`이 멈춤 | 온보딩을 하지 않았거나 필수 항목이 빔 | `/naver-blog-autopilot:blog-onboard` |
| `blogId: MISMATCH`로 멈춤 | `.env`의 `NAVER_BLOG_ID=`와 `knowledge/source-blogs.json`의 `own_blog.blogId`가 다름 | 온보딩을 다시 실행해 `항목만 고르기` → 「레퍼런스·디자인 시스템」(블로그 ID 질문)을 고르거나, 두 값을 같게 맞춤 |
| `IMAGE_KEY: CONFLICT`로 멈춤 | `.env`의 `IMAGE_PROVIDER=`가 가리키는 제공자의 키가 비어 있음. 또는 그 줄 값이 gemini·openai가 아님(키를 그 줄에 잘못 넣음) | 그 제공자의 키를 넣거나, `IMAGE_PROVIDER=`를 키가 있는 제공자로 바꾸거나 그 줄을 지움 |
| "마무리 블록을 만들 수 없습니다"로 멈춤 | 글 끝 구성에 소개 이미지가 있는데 `photos/business-intro.png`가 없음 | 그 파일을 넣거나, 온보딩에서 글 끝 구성의 소개 이미지를 뺌 |
| "표지(대표이미지)를 만들 수 없습니다"로 멈춤 | 한글 폰트를 찾지 못함 | 3장 준비물의 한글 폰트 설치 |
| 업로드 단계에서 "세션 없음/만료"(exit 20) | 로그인이 풀림. "로그인 상태 유지"를 체크하지 않은 경우가 많음 | 4-6단계 로그인 → `/naver-blog-autopilot:blog-run resume <글 번호>` |
| "다른 계정으로 로그인"(exit 21) | 글을 올릴 블로그가 아닌 계정으로 로그인함 | 그 블로그 계정으로 4-6단계 로그인을 다시 함 |
| 이미지 생성이 429로 멈춤(Gemini) | 결제가 설정되지 않은 무료 키 | Google Cloud 프로젝트에 결제 설정 후 다시 |
| 이미지 생성이 403(OpenAI) | 조직 인증이 안 됨 | OpenAI 조직 설정에서 Verify Organization |
| 스톡 사진 자리가 `보류` | 검색 결과 없음 · 사진 받기 실패 · 요청 한도(한꺼번에 많이 받음) · `STOCK_PROVIDER` 설정(진단 `STOCK: MISSING`·`CONFLICT`) | 게이트 3에서 `다른 사진으로(검색어 수정)` — 영문 일반 사물 2~3단어로. 요청 한도면 잠시 뒤 `/naver-blog-autopilot:blog-run resume <글 번호>`. 설정 문제면 `.env`의 `STOCK_PROVIDER=` 줄을 `openverse`로 고치거나 지움 |
| "표지 재생성 필요"로 멈춤 | 게이트 2에서 제목이 바뀜 | `blog-run`이 표지 제목만 다시 만들고 이어 갑니다(비용 없음) |
| "대표이미지 지정 실패" 경고 | 임시저장은 됐지만 대표 지정 확인 실패 | 네이버 임시저장 글에서 첫 사진을 직접 대표로 지정 |
| "장소 카드 확인 필요" 경고 | 지도 검색 1번 결과가 우리 업체가 아닐 수 있음 | 미리보기에서 지도 확인. 다르면 프로필의 `장소 검색어`를 `<업체명> <지역>`으로 좁힘 |
| 사실 검토에서 `출처필요`가 많음 | 공공기관 페이지가 자동 조회되지 않음 | 게이트 2에서 직접 확인한 내용을 알려 주면 반영됩니다 |
| "카테고리/태그 설정 실패" 경고 | 임시저장은 됐지만 카테고리·태그가 안 들어감 | 네이버 임시저장 글에서 카테고리·태그를 직접 지정 |
| 네이버 에디터에서 계속 "…을 못 찾음" | 네이버가 에디터를 바꿈 | `naver-blog-cli` 업데이트를 기다리거나 플러그인 제작자에게 알림 |

Windows에서 이모지가 깨지거나 멈추면 4-2단계의 `setx PYTHONUTF8 1`을 하고, PowerShell 창을 새로 연 뒤 4-4단계 명령으로 Claude Code를 다시 엽니다.

---

## 10. 자주 묻는 질문

**1. 발행한 글이 없는데 써도 되나요?**
됩니다. 글 모양 기준은 「측정 전」 기본값으로 시작하고, 관련글 링크 검사는 경고만 내고 넘어갑니다. 자기 글이 쌓이면 온보딩을 다시 실행해 「레퍼런스·디자인 시스템」을 고르세요.

자기 글이 있어도 지금 쓰는 글과 주제가 맞는 글이 2편 미만이면 관련글을 억지로 붙이지 않습니다. 이때는 게이트 2와 마지막 보고에 관련글을 생략했다는 한 줄이 나옵니다.

**2. 해요체로 쓸 수 있나요?**
있습니다. 온보딩의 말투 질문에서 `해요체(친근)`를 고르면 됩니다. 개인 유형은 해요체가 기본값입니다.

**3. 이미지 키가 없으면 못 쓰나요?**
시작은 할 수 있습니다. 키가 없는 소스의 이미지 자리는 `보류`로 두고 나머지(내 사진 등)로 채웁니다. 다만 이미지가 정해진 최소 개수보다 적으면 임시저장 전에 멈춥니다. 키 없이 시작하면 대표 이미지 배경에도 `photos/`의 내 사진이 필요합니다. 비용 없이 시작하려면 온보딩을 다시 실행해 「이미지 소스」에서 `무료 스톡 사진(키 없이 바로)`을 고르세요. Pexels 키는 필요 없습니다(개인 유형 말고는 기본값에 스톡 사진이 없습니다). 지명·한국어 간판 같은 한국 장면은 스톡 사진에 거의 없어서, 그런 자리는 AI 생성이나 내 사진으로 채웁니다.

**4. 이미지는 어떤 것이 들어가나요?**
본문 이미지에는 글자·로고·얼굴 클로즈업이 들어가지 않게 만듭니다. 홍보 글에는 내 사진만 씁니다. 대표 이미지(표지)는 배경 위에 글 제목을 얹어 만듭니다.

**5. Windows에서도 되나요?**
되도록 만들었지만 아직 실제 Windows PC에서 끝까지 검증하지는 않았습니다. Git for Windows를 가장 먼저 설치하고, 이 가이드에서 「Windows(PowerShell에서)」 표시가 붙은 명령을 PowerShell에서 실행합니다. 셋업 진단표 맨 위에 `OS: Windows(Git Bash)`가 나오면 맞게 돈 것입니다.

**6. 컴퓨터 두 대에서 쓸 수 있나요?**
각 컴퓨터에 따로 설치하고 로그인합니다. 작업 폴더의 `knowledge/`와 `work/`는 복사해 가도 됩니다(`work/`까지 옮겨야 글 번호와 변주 기록이 이어집니다). `.env`의 키는 새 컴퓨터에서 다시 넣고, `playwright-state/` 폴더는 옮기지 말고 새로 로그인합니다.

**7. 1.0.0을 쓰고 있었어요. 어떻게 올리나요?**
6-6대로 업데이트하고 셋업을 다시 실행한 뒤 온보딩을 한 번 실행합니다. 1.0.0 설정에는 새 항목이 없어, 셋업 진단표에 `MISSING 블로그 유형,톤,마무리 블록,이미지 소스`가 나오는 것이 정상입니다(온보딩 전에 글쓰기를 시작하면 "프로필이 완성되지 않았습니다"로 멈춥니다). 1.0.0과 같은 글 모양(합니다체, 문의 헤딩·소개 이미지·장소 카드)을 유지하려면 유형 `업체`의 기본값을 고릅니다.

톤·고객 지역·글 끝 구성을 1.0.0과 다르게 고르면, 작업 폴더의 `knowledge/naver-seo-checklist.md`를 플러그인 최신본으로 바꾸고 디자인 시스템도 `blog-design-system` 갱신 모드로 다시 만들어 달라고 Claude에게 요청하세요. 1.0.0 판에는 합니다체·문의 헤딩·지역이 고정값으로 적혀 있고, 셋업은 이 파일들을 덮어쓰지 않습니다.

**8. 글이 마음에 안 들면 처음부터 다시 쓸 수 있나요?**
게이트 2에서 고칠 점을 적으면 한 번 고쳐 줍니다. 완전히 다른 글을 원하면 `blog-run`을 다시 실행해 새 주제로 시작합니다.

---

## 부록 A. 명령 한눈에 보기

**Claude 입력창에서**

| 명령 | 하는 일 |
|---|---|
| `/plugin marketplace add heesun-woodi/woodi-claude-plugins` | 마켓플레이스 추가(처음 한 번) |
| `/plugin install naver-blog-autopilot@woodi-claude-plugins` | 플러그인 설치(처음 한 번) |
| `/naver-blog-autopilot:blog-setup ~/naver-blog-work` | 환경 진단, 작업 폴더 준비 |
| `/naver-blog-autopilot:blog-onboard` | 내 블로그에 맞게 설정 |
| `/naver-blog-autopilot:blog-run` | 글 한 편 만들기 |
| `/naver-blog-autopilot:blog-run 3` | 후보 표의 3번 주제로 시작 |
| `/naver-blog-autopilot:blog-run resume 001` | 멈춘 글 이어 가기 |
| `/naver-blog-autopilot:blog-run report 001` | 글 진행 상황 보기 |
| `/naver-blog-autopilot:blog-feedback 003 <발행 글 주소>` | 발행본과 비교해 학습 |
| `/naver-blog-autopilot:blog-feedback rules` | 적용 중인 규칙 보기 |
| `/plugin marketplace update woodi-claude-plugins` | 새 버전 확인 |

**터미널에서**

| 할 일 | 명령 |
|---|---|
| 작업 폴더에서 Claude Code 열기 | macOS `cd ~/naver-blog-work && claude` · Windows `cd ~\naver-blog-work; claude` |
| 네이버 로그인 | 4-6단계 명령 |
| `.env` 열기 | macOS `open -e ~/naver-blog-work/.env` · Windows `notepad "$HOME\naver-blog-work\.env"` |

## 부록 B. 작업 폴더 안에 생기는 것

```text
naver-blog-work/
  .env                   # 블로그 ID와 이미지 키 (공유 금지)
  knowledge/             # 내 설정 — 직접 고쳐도 됨
    business-profile.md  #   프로필(유형·말투·글 끝 구성·이미지 소스)과 금칙어
    design-system.md     #   글 모양 기준
    learned-preferences.md  # 피드백에서 배운 규칙
    source-blogs.json  official-sources.md  topic-seeds.md  naver-seo-checklist.md
  photos/                # 내 사진, 소개 이미지(business-intro.png)
  playwright-state/      # 네이버 로그인 세션 (비밀번호처럼 다루기)
  scripts/               # 플러그인 스크립트 (셋업할 때마다 최신본으로 바뀜)
  work/
    topics/              # 날짜별 주제 후보 표
    posts/001-…/         # 글 한 편의 모든 파일
      draft-v2.md        #   게이트 2에서 보고 고치는 초안
      final.md           #   네이버에 올라간 업로드본
      images/            #   본문 이미지와 대표 이미지(00-cover.png)
```

## 부록 C. 더 읽을거리

- [플러그인 README](https://github.com/heesun-woodi/woodi-claude-plugins/blob/main/plugins/naver-blog-autopilot/README.md) — 전체 동작, 종료 코드, 설계 이유
- [이미지 소스 연동 안내](https://github.com/heesun-woodi/woodi-claude-plugins/blob/main/plugins/naver-blog-autopilot/skills/blog-onboarding/references/image-setup.md) — Gemini·OpenAI 키 발급, 무료 스톡 사진(Openverse 기본·Pexels 선택) 설정
- [naver-blog-cli](https://github.com/spegas/naver-blog-cli) — 네이버 임시저장을 맡는 외부 도구
