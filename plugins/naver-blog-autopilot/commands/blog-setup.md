---
description: 네이버 블로그 자동화 작업 폴더를 준비하고 환경(uv·Python·Playwright·naver-blog-cli·네이버 로그인 세션·이미지 AI 키(Gemini 또는 OpenAI)·한글 폰트·업체소개 이미지)을 진단합니다.
argument-hint: "[작업 폴더 경로 (선택, 기본 현재 폴더)]"
allowed-tools: Bash, Read, Write, Glob, Skill, AskUserQuestion
---

사용자가 네이버 블로그 자동화의 작업 폴더 셋업을 시작했다. 아래 순서대로 진행하라.
사용자에게 보여주는 모든 안내 문구는 **한국어**로 작성한다.
어떤 단계에서도 비밀번호·API 키 값을 출력하거나 저장하지 않는다. 네이버 로그인은 사람이 직접 한다.

인자: `$ARGUMENTS` (작업 폴더 경로. 비어 있으면 현재 폴더를 쓴다.)

---

## 0. OS 확인 (Windows는 Git for Windows 필수)

아래 모든 블록은 bash 문법이다. macOS 터미널, 또는 Windows의 **Git Bash**(Git for Windows에 포함 — Claude Code의 Bash 도구가 이것으로 돈다)에서만 동작한다. 먼저 한 번 확인한다.

```bash
uname -s
```

- `Darwin` → macOS. 1단계로.
- `MINGW*`·`MSYS*` → **Windows(Git Bash)**. 1단계로. 4단계 설치 안내는 **Windows 갈래**(PowerShell 명령)만 보여 준다.
- 명령이 실패하거나 PowerShell 오류(`uname`을 찾을 수 없음 등)가 나오면 Bash 도구가 Git Bash가 아니다 → "Windows에서는 Git for Windows가 필요합니다(https://git-scm.com/downloads/win). 설치한 뒤 Claude Code를 완전히 닫았다가 다시 열고 `/naver-blog-autopilot:blog-setup`을 다시 실행하세요." 안내 후 **중단**.

## 1. 작업 폴더 확정

`$ARGUMENTS`가 있으면 그 폴더(없으면 만들고)로, 없으면 현재 폴더로 이동한다. `~`·`~/…`는 홈 폴더로 펼친다(따옴표 때문에 셸이 펼치지 않으므로).
**작업 폴더는 플러그인 저장소 밖이어야 한다.** 아래로 확인하고, 걸리면 거부한 뒤 다른 폴더를 요청하고 멈춘다.

```bash
TARGET="$ARGUMENTS"; [ -z "$TARGET" ] && TARGET=.
case "$TARGET" in "~") TARGET="$HOME";; "~/"*) TARGET="$HOME/${TARGET#\~/}";; esac
# 거부 검사를 mkdir보다 먼저 한다 (거부된 경로가 만들어지지 않게). 존재하는 가장 가까운 상위 폴더에서 git 루트를 찾는다.
CHK="$TARGET"; while [ ! -d "$CHK" ] && [ "$CHK" != "/" ] && [ "$CHK" != "." ]; do CHK="$(dirname "$CHK")"; done
ROOT="$(git -C "$CHK" rev-parse --show-toplevel 2>/dev/null)"
if [ -n "$ROOT" ] && { [ -d "$ROOT/.claude-plugin" ] || ls "$ROOT"/plugins/*/.claude-plugin >/dev/null 2>&1; }; then
  echo "REFUSE: 플러그인 저장소 안입니다 ($ROOT)"
else
  mkdir -p "$TARGET" && cd "$TARGET" || { echo "폴더를 만들거나 열 수 없습니다: $TARGET"; exit 1; }
  TARGET="$PWD"   # 절대경로로 고정
  echo "작업 폴더: $TARGET"
  command -v cygpath >/dev/null 2>&1 && echo "작업 폴더(Windows 경로): $(cygpath -w "$TARGET")"
fi
```

출력된 `작업 폴더:` **절대경로**를 기억한다. Windows면 `작업 폴더(Windows 경로):`(`C:\Users\…`)도 기억해 4단계 PowerShell 명령의 `<작업 폴더 Windows 경로>` 자리에 넣는다. Bash 호출마다 cwd가 처음으로 돌아갈 수 있으므로, 2·3·3-1·3-2단계 Bash 블록은 첫 줄 `cd "<그 절대경로>" || exit 1`로 시작한다(아래 블록의 `<작업 폴더 절대경로>` 자리에 그대로 넣는다).

`REFUSE`가 나오면 "작업 폴더는 플러그인 저장소 밖(예: ~/naver-blog-work)이어야 합니다. 다른 폴더를 알려주세요."라고 안내하고 중단한다.

## 2. 환경 진단

한 번의 Bash 호출로 전부 확인하라. 나눠서 여러 번 호출하지 말 것.
`naver-blog-cli`는 **종료 코드가 항상 0**이다. 성공·실패는 종료 코드가 아니라 **stdout 문구**로 판단한다.
키 값은 절대 출력하지 않는다 (존재 여부만).

```bash
cd "<작업 폴더 절대경로>" || exit 1
PYUTF8_BEFORE="${PYTHONUTF8:-}"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export PYTHONUTF8=1   # Windows cp949 콘솔에서 이모지 출력 오류 방지 (macOS 영향 없음)
echo "--- OS ---"
IS_WIN=no
case "$(uname -s)" in MINGW*|MSYS*) IS_WIN=yes; echo "OS: Windows(Git Bash)";; Darwin) echo "OS: macOS";; *) echo "OS: $(uname -s)";; esac
[ "$IS_WIN" = yes ] && { [ "$PYUTF8_BEFORE" = 1 ] && echo "PYTHONUTF8: OK (영구 설정됨)" || echo "PYTHONUTF8: NOT_SET (setx PYTHONUTF8 1 필요)"; }
LAD="${LOCALAPPDATA:-}"; WD="${WINDIR:-${windir:-${SYSTEMROOT:-}}}"
if command -v cygpath >/dev/null 2>&1; then [ -n "$LAD" ] && LAD="$(cygpath -u "$LAD")"; [ -n "$WD" ] && WD="$(cygpath -u "$WD")"; fi
echo "--- uv ---"
if command -v uv >/dev/null 2>&1; then echo "uv: OK ($(uv --version))"; else echo "uv: MISSING"; fi
echo "--- python ---"
PY3="$(command -v python3 2>/dev/null)"
if [ -n "$PY3" ] && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
  echo "python3: OK ($(python3 --version 2>&1))"
elif echo "$PY3" | grep -qi 'WindowsApps'; then echo "python3: MISSING_OR_OLD (Microsoft Store 별칭만 있음: $PY3)"
else echo "python3: MISSING_OR_OLD (3.11 이상 필요: $(python3 --version 2>&1 | head -1))"; fi
echo "--- playwright chromium ---"
PW_DIRS=$(ls ~/Library/Caches/ms-playwright ~/.cache/ms-playwright ${LAD:+"$LAD/ms-playwright"} 2>/dev/null | grep -c chromium)
PW_PY=$(python3 -c "import playwright" 2>/dev/null && echo yes || echo no)
if [ "$PW_DIRS" -gt 0 ]; then echo "chromium: OK (ms-playwright 캐시 ${PW_DIRS}개, python playwright 모듈: $PW_PY)"
else echo "chromium: MISSING (python playwright 모듈: $PW_PY)"; fi
echo "--- naver-blog-cli ---"
if command -v naver-blog-cli >/dev/null 2>&1 && naver-blog-cli --help >/dev/null 2>&1; then echo "naver-blog-cli: OK"
else echo "naver-blog-cli: MISSING"; fi
echo "--- 블로그 ID ---"
# .env 값 읽기(아래 이미지 키 판정도 같은 함수): 따옴표 없는 값은 공백+# 이후가 주석, #로 시작하면 빈 값, 따옴표 안이 공백뿐이면 빈 값. 같은 이름이 여러 줄이면 처음 나온 비어 있지 않은 값. export·따옴표·CRLF 허용.
ENVGET='{ sub(/\r$/, ""); l = $0; sub(/^[ \t]+/, "", l); sub(/^export[ \t]+/, "", l)
  i = index(l, "="); if (i == 0) next
  k = substr(l, 1, i - 1); sub(/[ \t]+$/, "", k); if (k != n) next
  v = substr(l, i + 1); sub(/^[ \t]+/, "", v); q = substr(v, 1, 1)
  if (q == "\"" || q == sq) { v = substr(v, 2); j = index(v, q); if (j) v = substr(v, 1, j - 1); if (v ~ /^[ \t]*$/) v = "" }
  else { if (substr(v, 1, 1) == "#") v = ""; sub(/[ \t]+#.*$/, "", v); sub(/[ \t]+$/, "", v) }
  if (v != "") { if (show) print v; f = 1; exit } }
END { exit(f ? 0 : 1) }'
# NAVER_BLOG_ID(.env — lint final·upload·naver_upload.sh가 읽음)와 own_blog.blogId(knowledge/source-blogs.json — 스킬이 읽음)는 같은 값이어야 한다. 기본값 없음. 블로그 ID 형식([A-Za-z0-9_-])이 아니면(`[…]` 자리표시 포함) 빈 값으로 본다
ENV_ID=""; [ -f .env ] && ENV_ID="$(awk -v n=NAVER_BLOG_ID -v show=1 -v sq="'" "$ENVGET" .env | tr -d '\r')"
printf '%s' "$ENV_ID" | grep -Eq '^[A-Za-z0-9_-]+$' || ENV_ID=""
OWN_ID=""; [ -f knowledge/source-blogs.json ] && command -v python3 >/dev/null 2>&1 && \
  OWN_ID=$( { python3 -c "import json,re;o=json.load(open('knowledge/source-blogs.json',encoding='utf-8')).get('own_blog');b=str((o.get('blogId') if isinstance(o,dict) else o) or '').strip();print(b if re.fullmatch(r'[A-Za-z0-9_-]+',b) else '')" 2>/dev/null || true; } | tr -d '\r')
if [ -z "$ENV_ID" ]; then echo "NAVER_BLOG_ID: MISSING (.env — 3-2단계)"
elif [ -n "$OWN_ID" ] && [ "$OWN_ID" != "$ENV_ID" ]; then echo "NAVER_BLOG_ID: MISMATCH (.env=$ENV_ID ≠ own_blog.blogId=$OWN_ID)"
else echo "NAVER_BLOG_ID: OK ($ENV_ID)"; fi
if [ -n "$OWN_ID" ]; then echo "own_blog.blogId: OK ($OWN_ID)"; else echo "own_blog.blogId: MISSING (knowledge/source-blogs.json — 3단계 복사 뒤 채운다)"; fi
BLOG_ID="${ENV_ID:-$OWN_ID}"   # 세션 확인용: .env 값, 없으면 own_blog.blogId
echo "--- naver 세션 ---"
if [ -z "$BLOG_ID" ]; then echo "session: SKIPPED (blogId 없음 — 3-2단계에서 NAVER_BLOG_ID를 넣은 뒤 다시 실행)"
elif command -v naver-blog-cli >/dev/null 2>&1; then
  SESS=$(NAVER_BLOG_ID="$BLOG_ID" naver-blog-cli check-session 2>&1 | tr -d '\r')
  if echo "$SESS" | grep -q '세션 정상' && echo "$SESS" | grep -q '글쓰기 가능'; then
    # check-session 은 다른 계정 세션도 통과시킨다 → 글쓰기 화면이 $BLOG_ID 블로그로 열리는지 확인 (헤드리스, 글은 안 씀)
    UVT="$(uv tool dir 2>/dev/null)"; command -v cygpath >/dev/null 2>&1 && [ -n "$UVT" ] && UVT="$(cygpath -u "$UVT")"
    CLI_PY=""; for c in "$UVT/naver-blog-cli/bin/python" "$UVT/naver-blog-cli/Scripts/python.exe"; do [ -x "$c" ] && { CLI_PY="$c"; break; }; done
    CHK="${CLAUDE_PLUGIN_ROOT}/scaffold/scripts/check_blog_account.py"
    if [ -n "$CLI_PY" ] && [ -f "$CHK" ]; then
      ACCT=$("$CLI_PY" "$CHK" "$BLOG_ID" 2>&1 | tr -d '\r'; exit "${PIPESTATUS[0]}"); ACCT_RC=$?
      case "$ACCT_RC" in
        0) echo "session: OK (blogId=$BLOG_ID, 계정 확인됨)" ;;
        21) echo "session: WRONG_ACCOUNT (blogId=$BLOG_ID) — $(echo "$ACCT" | tail -1)" ;;
        *) echo "session: LOGIN_NEEDED (blogId=$BLOG_ID) — 계정 확인 실패: $(echo "$ACCT" | tail -1)" ;;
      esac
    else echo "session: LOGIN_NEEDED (blogId=$BLOG_ID) — 계정 확인 불가(naver-blog-cli 의 uv tool python 또는 $CHK 없음 — uv tool install 로 다시 설치)"; fi
  elif echo "$SESS" | grep -q '확인 실패:'; then echo "session: LOGIN_NEEDED (blogId=$BLOG_ID) — $(echo "$SESS" | head -1) (로그인과 무관한 원인일 수 있음 — 예: Chromium 미설치)"
  else echo "session: LOGIN_NEEDED (blogId=$BLOG_ID) — $(echo "$SESS" | head -1)"; fi
else echo "session: SKIPPED (naver-blog-cli 없음)"; fi
echo "--- .env / knowledge ---"
# 이미지 키: IMAGE_PROVIDER > GEMINI_API_KEY > OPENAI_API_KEY. 존재 여부만 본다 — 키 값·IMAGE_MODEL은 출력하지 않고, IMAGE_PROVIDER도 gemini/openai일 때만 출력한다.
# gen_image.py·check_image_key.py와 같은 규칙(여기서 .env는 작업 폴더 .env): 키: API 키(GEMINI_API_KEY/OPENAI_API_KEY)가 든 첫 .env 파일의 값. 어느 파일에도 없으면 환경변수. IMAGE_PROVIDER·IMAGE_MODEL: 키를 찾은 .env의 값(그 파일에 없으면 미지정). 키를 환경변수에서 읽을 때는 항목마다 cwd .env → 환경변수 중 처음 값이 있는 곳.
# .env 값은 위 "블로그 ID" 절에서 정의한 ENVGET으로 읽는다.
G_SRC=""; O_SRC=""
if [ -f .env ]; then
  awk -v n=GEMINI_API_KEY -v show=0 -v sq="'" "$ENVGET" .env && G_SRC=".env"
  awk -v n=OPENAI_API_KEY -v show=0 -v sq="'" "$ENVGET" .env && O_SRC=".env"
fi
if [ -z "$G_SRC$O_SRC" ]; then   # .env에 키가 없을 때만 환경변수의 키
  [ -n "$(printenv GEMINI_API_KEY 2>/dev/null | tr -d '[:space:]')" ] && G_SRC="env"
  [ -n "$(printenv OPENAI_API_KEY 2>/dev/null | tr -d '[:space:]')" ] && O_SRC="env"
fi
IP=""
[ -f .env ] && IP="$(awk -v n=IMAGE_PROVIDER -v show=1 -v sq="'" "$ENVGET" .env | tr -d '\r' | tr '[:upper:]' '[:lower:]')"
[ -z "$IP" ] && [ "$G_SRC" != .env ] && [ "$O_SRC" != .env ] && IP="$(printf '%s' "${IMAGE_PROVIDER:-}" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"   # 키가 .env에 있으면 환경변수 IMAGE_PROVIDER는 보지 않음
case "$IP" in
  gemini) [ -n "$G_SRC" ] && echo "IMAGE_KEY: OK (gemini, $G_SRC)" || echo "IMAGE_KEY: CONFLICT (IMAGE_PROVIDER=gemini인데 GEMINI_API_KEY 없음)" ;;
  openai) [ -n "$O_SRC" ] && echo "IMAGE_KEY: OK (openai, $O_SRC)" || echo "IMAGE_KEY: CONFLICT (IMAGE_PROVIDER=openai인데 OPENAI_API_KEY 없음)" ;;
  "") if [ -n "$G_SRC" ]; then echo "IMAGE_KEY: OK (gemini, $G_SRC)"; elif [ -n "$O_SRC" ]; then echo "IMAGE_KEY: OK (openai, $O_SRC)"; else echo "IMAGE_KEY: MISSING"; fi ;;
  *) echo "IMAGE_KEY: CONFLICT (IMAGE_PROVIDER 값이 gemini/openai가 아님 — 키를 이 줄에 잘못 넣었는지 확인)" ;;
esac
[ -f knowledge/design-system.md ] && echo "design-system.md: OK" || echo "design-system.md: MISSING (경고만, 오류 아님)"
echo "--- 표지·마무리 자산 ---"
# 글꼴: macOS(Pretendard·AppleSDGothicNeo) / Windows(Pretendard 사용자·시스템 설치, 맑은 고딕 Bold) — LAD·WD는 위 OS 절에서 cygpath로 변환됨
if [ -f "$HOME/Library/Fonts/Pretendard-ExtraBold.otf" ] || { [ -n "$LAD" ] && [ -f "$LAD/Microsoft/Windows/Fonts/Pretendard-ExtraBold.otf" ]; } || { [ -n "$WD" ] && [ -f "$WD/Fonts/Pretendard-ExtraBold.otf" ]; }; then echo "font: OK (Pretendard)"
elif [ -f /System/Library/Fonts/AppleSDGothicNeo.ttc ]; then echo "font: OK (AppleSDGothicNeo — Pretendard 권장)"
elif [ -n "$WD" ] && [ -f "$WD/Fonts/malgunbd.ttf" ]; then echo "font: OK (맑은 고딕 — Pretendard 권장)"
else echo "font: MISSING"; fi
[ -f photos/business-intro.png ] && echo "intro-image: OK" || echo "intro-image: MISSING"
```

## 3. 작업 폴더 준비 (scaffold 복사)

`${CLAUDE_PLUGIN_ROOT}/scaffold/` 를 작업 폴더로 복사한다. 규칙: **scripts는 매번 갱신, knowledge는 보존(스텁만 교체)**.
`scripts/`는 플러그인 코드라 항상 최신본으로 덮어쓴다. `knowledge/`는 담당자가 고친 파일을 보존하고, 아직 `Task N에서 채움` 문구가 남은 스텁만 플러그인 초기값으로 바꾼다. 그 밖의 파일은 없을 때만 복사한다(`cp -n`). 정본은 작업 폴더의 `knowledge/`다.
학습 규칙 파일 `knowledge/learned-preferences.md`(빈 표 템플릿 — `## 적용 중`·`## 후보`·`## 보류·삭제`·`## 피할 표현`)도 이 `cp -n`으로 **처음 한 번만** 들어간다. 템플릿에는 `Task N에서 채움` 문구가 없어 스텁 교체 루프에 걸리지 않으므로, 이후 블로그 작업·`/naver-blog-autopilot:blog-feedback`으로 쌓인 규칙은 다시 실행해도 덮어쓰지 않는다. 피드백 로그 `work/feedback-log.md`는 복사 대상이 아니다 — `scripts/feedback_log.py`가 처음 기록할 때 만든다.

```bash
cd "<작업 폴더 절대경로>" || exit 1
cp -rn "${CLAUDE_PLUGIN_ROOT}/scaffold/." . || true   # macOS cp -n은 건너뛴 파일이 있으면 exit 1 — 재실행 시 정상
cp -R "${CLAUDE_PLUGIN_ROOT}/scaffold/scripts/." scripts/   # scripts는 항상 최신본
for f in knowledge/*.md; do grep -q 'Task [0-9]*에서 채움' "$f" && cp "${CLAUDE_PLUGIN_ROOT}/scaffold/knowledge/$(basename "$f")" "$f" && echo "스텁 교체: $f"; done
[ -f .env ] || { cp .env.example .env && echo ".env 새로 생성 (키를 채워야 함)"; }
[ -f .env ] && echo ".env: 있음"
[ -f knowledge/design-system.md ] && echo "design-system.md: OK" || echo "design-system.md: MISSING (경고만)"
# 학습 규칙: `## 적용 중`·`## 후보` 절의 `| L-001 | …` 행 수 (파일 없음·0개는 첫 사용 — 정상)
if [ -f knowledge/learned-preferences.md ]; then
  LCNT=$(awk '/^## /{ s = $0; next } /^\|[ \t]*L-[0-9]+/{ if (s ~ /^## 적용 중/) a++; else if (s ~ /^## 후보/) c++ } END { printf "%d %d", a, c }' knowledge/learned-preferences.md | tr -d '\r')
  echo "learned: 적용 중 ${LCNT% *}개 · 후보 ${LCNT#* }개"
else echo "learned: 없음(첫 사용)"; fi
# 이미지 키 확인(비용 0 조회 — 이미지를 만들지 않음). 스크립트는 방금 복사됐으므로 여기서만 돌릴 수 있다. 키 값은 출력되지 않는다.
export PYTHONUTF8=1
if [ -f scripts/check_image_key.py ]; then IKC=$(python3 scripts/check_image_key.py 2>&1 | tr -d '\r'; exit "${PIPESTATUS[0]}"); IKC_RC=$?
else IKC="scripts/check_image_key.py 없음 — 플러그인을 다시 설치(업데이트)하세요"; IKC_RC=9; fi
case "$IKC_RC" in   # 요약은 첫 줄(사람용 문구)만
  0) echo "IMAGE_KEY_CHECK: OK — $(echo "$IKC" | head -1)" ;;
  2) echo "IMAGE_KEY_CHECK: SKIPPED (키 없음 또는 CONFLICT — 2단계 IMAGE_KEY 참고)" ;;
  3) echo "IMAGE_KEY_CHECK: REJECTED — $(echo "$IKC" | head -1)" ;;
  4) echo "IMAGE_KEY_CHECK: NO_MODEL — $(echo "$IKC" | head -1)" ;;
  5) echo "IMAGE_KEY_CHECK: NETWORK — $(echo "$IKC" | head -1)" ;;
  127) echo "IMAGE_KEY_CHECK: NO_PYTHON (python3 없음 — 4단계 python3 항목)" ;;
  49|9009) echo "IMAGE_KEY_CHECK: PYTHON_STUB (python3가 Microsoft Store 별칭 — 설정 → 앱 → 고급 앱 설정 → 앱 실행 별칭에서 python.exe·python3.exe 끄기)" ;;
  *) echo "IMAGE_KEY_CHECK: ERROR (exit $IKC_RC) — $(echo "$IKC" | head -1)" ;;
esac
# 필수 profile 행 확인(비용 0 — 스크립트는 방금 복사됐다): profile: OK / MISSING <행,…> / NOFILE 한 줄
if [ -f scripts/check_profile.py ]; then python3 scripts/check_profile.py 2>&1 | tr -d '\r' | head -1
else echo "profile: SKIPPED (scripts/check_profile.py 없음 — 플러그인을 다시 설치(업데이트)하세요)"; fi
```

복사 후 새로 생긴 파일, 이미 있어서 건너뛴 파일, 갱신한 `scripts/`·교체한 스텁을 구분해 한 줄로 보고한다.
`.env`는 이미 `.gitignore`에 포함되어 있어야 하며 채팅에 키를 붙여넣지 않게 한다. 키를 고르고 넣는 안내는 다음 3-1단계에서 한다.
`IMAGE_KEY_CHECK`가 `NO_PYTHON`(exit 127)·`PYTHON_STUB`(Windows Store 별칭, exit 9009 — bash에서는 49)이면 python3 문제다(4단계 python3 항목) — 키 문제로 안내하지 않는다. `ERROR`(스크립트 없음 등)도 키 문제가 아니다.
`profile:` 줄은 4단계 표의 「business-profile.md 필수 행」에 넣는다. 첫 셋업에서는 템플릿 그대로라 `MISSING`이 정상이다.

## 3-1. 이미지 AI 고르기 (글에 넣을 AI 이미지를 만들 키)

이미지 생성은 **Gemini**(Google AI Studio) 또는 **OpenAI**(GPT 이미지) 중 담당자가 가진 키 하나로 한다. 어느 쪽을 쓸지는 `IMAGE_PROVIDER`(gemini|openai, 선택) > `GEMINI_API_KEY` > `OPENAI_API_KEY` 순으로 정한다. 읽는 곳 — 키: API 키(GEMINI_API_KEY/OPENAI_API_KEY)가 든 첫 .env 파일의 값. 어느 파일에도 없으면 환경변수. IMAGE_PROVIDER·IMAGE_MODEL: 키를 찾은 .env의 값(그 파일에 없으면 미지정). 키를 환경변수에서 읽을 때는 항목마다 cwd .env → 환경변수 중 처음 값이 있는 곳. `IMAGE_PROVIDER`가 정한 제공자의 키가 비어 있거나 값이 gemini/openai가 아니면 오류(`CONFLICT`)다. 기본 모델은 gemini=`gemini-3-pro-image`, openai=`gpt-image-2`이고, `.env`의 `IMAGE_MODEL=`로 바꿀 수 있다(선택).

**2단계 `IMAGE_KEY`가 `OK`면** 질문하지 않는다. 3단계의 `IMAGE_KEY_CHECK` 결과만 4단계 표에 넣고, "다른 키로 바꾸려면 작업 폴더 `.env`의 `IMAGE_PROVIDER=`를 `gemini` 또는 `openai`로 바꾸세요(그 제공자의 키도 있어야 합니다. 키가 `.env`에 있으면 그 `.env`의 이 줄만 쓰입니다)." 한 줄만 안내한다(`IMAGE_KEY_CHECK`가 `REJECTED`·`NO_MODEL`이면 아래 "확인 결과 안내"의 그 제공자 원인도 함께).

**`MISSING`이거나 `CONFLICT`면** AskUserQuestion 한 번:
- 질문: "글에 넣을 이미지를 만들 AI 키를 고르세요. 이미 쓰고 계신 키가 있으면 그것을 고르세요."
- 옵션: `Gemini(Google AI Studio)` / `OpenAI(GPT 이미지)` / `아직 없음 — 나중에`(실사진만으로 쓰거나, 키를 준비한 뒤 `/naver-blog-autopilot:blog-run resume <NNN>`)

`Gemini`·`OpenAI`를 고르면 메인이 `.env`의 `IMAGE_PROVIDER=` 줄**만** 쓴다(있으면 그 줄을 교체, 없으면 끝에 추가, 다른 줄은 그대로). 키 줄은 들여다보거나 출력하지 않는다. `<gemini 또는 openai>` 자리에 고른 값을 넣는다:

```bash
cd "<작업 폴더 절대경로>" || exit 1
PROV=<gemini 또는 openai>
[ -f .env ] || : > .env
awk -v v="$PROV" '/^[[:space:]]*(export[[:space:]]+)?IMAGE_PROVIDER[[:space:]]*=/ { if (!d) print "IMAGE_PROVIDER=" v; d = 1; next } { print } END { if (!d) print "IMAGE_PROVIDER=" v }' .env > .env.tmp && cat .env.tmp > .env && echo "IMAGE_PROVIDER=$PROV 저장"   # cat >로 덮어 써 권한·심링크 보존
rm -f .env.tmp   # 성공·실패와 무관하게 임시 파일 정리
```

`아직 없음 — 나중에`면 `.env`를 건드리지 않고 "키 없음 모드로 진행합니다 — `/naver-blog-autopilot:blog-run`은 AI 이미지 슬롯을 `보류`로 두고 실사진만 씁니다. `photos/` 실사진이 디자인 시스템 ④의 `min_images`보다 적으면 임시저장까지 가지 못하니, 키를 준비하면 이 커맨드를 다시 실행하세요." 안내 후 4단계로.

그다음 **고른 제공자의 안내만** 보여 준다.

- **Gemini**
  ```
  1. https://aistudio.google.com/apikey 에서 API 키를 만듭니다.
  2. 결제(Billing)가 설정된 Google Cloud 프로젝트의 키여야 이미지가 만들어집니다.
     무료 키는 이미지 생성에서 429(쿼터 초과)로 실패하고, 기다려도 풀리지 않습니다.
  3. 작업 폴더의 .env 에 아래 한 줄을 넣고 저장합니다.

         GEMINI_API_KEY=여기에_키

  비용: 1장 약 $0.04(추정치, 정확한 단가는 https://ai.google.dev/pricing).
  ```
- **OpenAI**
  ```
  1. https://platform.openai.com/api-keys 에서 API 키를 만듭니다.
  2. 결제 수단(Billing)이 등록돼 있어야 합니다.
  3. GPT 이미지 모델은 조직 인증(Verify Organization)이 필요할 수 있습니다:
     https://platform.openai.com/settings/organization/general → Verify Organization
  4. 작업 폴더의 .env 에 아래 한 줄을 넣고 저장합니다.

         OPENAI_API_KEY=여기에_키

  키 확인(check_image_key.py)이 통과해도 이미지 생성에서 403이 나면 조직 인증(Verify Organization)이 필요한 것입니다.
  비용: OpenAI 요금 페이지에서 확인하세요(https://openai.com/api/pricing/).
  ```

두 경우 모두 덧붙인다: "**키는 채팅에 붙여넣지 말고 `.env` 파일에 직접** 넣어 주세요." 그리고 `.env`를 여는 명령(진단의 `OS:` 갈래만, Claude 입력창이 아니라 터미널/PowerShell에서):
- macOS(터미널): `open -e "<작업 폴더 절대경로>/.env"`
- Windows(PowerShell): `notepad "<작업 폴더 Windows 경로>\.env"` (예: `notepad "$HOME\naver-blog-work\.env"` — 1단계 `작업 폴더(Windows 경로):` 값으로)

이어서 AskUserQuestion `넣었어요 — 확인해 주세요` / `나중에 넣을게요`. `넣었어요`면 확인한다(비용 0, 키 값은 출력되지 않음):

```bash
cd "<작업 폴더 절대경로>" || exit 1
export PYTHONUTF8=1
python3 scripts/check_image_key.py 2>&1 | tr -d '\r'; echo "exit=${PIPESTATUS[0]}"
```

**확인 결과 안내**(종료 코드별, 결과는 4단계 표의 이미지 AI 키 행에 반영):
- `0` → 출력 줄(`이미지 키 확인: <provider> · 모델 <model> 사용 가능 (<source>)`)을 그대로 보여 준다. Gemini면 "결제가 없는 무료 키는 이 확인은 통과해도 실제 생성에서 429가 날 수 있습니다" 한 줄을 덧붙인다.
- `2` (키 없음) → `.env`에 저장했는지, 줄 이름(`GEMINI_API_KEY=` / `OPENAI_API_KEY=`)이 맞는지, `IMAGE_PROVIDER`와 넣은 키의 제공자가 같은지 확인하라고 안내.
- `3` (키 거부) → Gemini: 키 오타·삭제된 키 — AI Studio에서 키를 다시 복사. OpenAI: 401이면 키 오타·폐기된 키, **403이면 조직 인증(Verify Organization)이 필요** — 위 조직 설정 주소에서 인증 후 다시 확인.
- `4` (모델 없음·권한 없음) → Gemini: 결제 설정된 프로젝트의 키인지, `IMAGE_MODEL`을 바꿨다면 이름이 맞는지. OpenAI: 결제 수단 등록·조직 인증 여부, `IMAGE_MODEL` 이름.
- `5` (네트워크·기타) → 인터넷 연결을 확인하고 잠시 뒤 다시 확인. 키 문제로 단정하지 않는다.

다시 확인은 한 번까지. 그래도 OK가 아니면 결과를 표에 남기고 4단계로 간다(키 없음 모드로도 `/naver-blog-autopilot:blog-run`은 돈다). `나중에 넣을게요`면 그대로 4단계로.

## 3-2. 블로그 ID (`.env`의 `NAVER_BLOG_ID`)

lint의 final·upload 단계와 `naver_upload.sh`는 `--blog-id`를 받지 않으면 작업 폴더 `.env`의 `NAVER_BLOG_ID`(블로그 주소 `blog.naver.com/<여기>`의 ID)를 읽는다. 기본값은 없다(`--blog-id`를 주면 그 값이 `.env`보다 우선한다). 스킬은 같은 값을 `knowledge/source-blogs.json`의 `own_blog.blogId`에서 읽으므로 두 값은 같아야 한다.

**2단계 `NAVER_BLOG_ID`가 `OK`면** 묻지 않는다(`own_blog.blogId: MISSING`이면 4단계 표에서 그 값을 `own_blog.blogId`에도 넣으라고 안내한다).

**`MISSING`이면** AskUserQuestion 한 번 — 질문 "글을 올릴 네이버 블로그 주소의 ID(blog.naver.com/<여기>)를 알려 주세요" — 옵션: (`own_blog.blogId: OK`면 첫 옵션으로) `<그 값> 쓰기` / `기타에 직접 적기` / `나중에`. **`MISMATCH`면** 두 값을 보여 주고 같은 질문으로 어느 값을 쓸지 묻는다(옵션 `.env 값 <값>` / `own_blog.blogId 값 <값>` / `기타에 직접 적기`). 받은 값이 블로그 ID 형식(영문·숫자·`_`·`-`)이 아니면 한 번 더 묻는다.

값을 받으면 메인이 `.env`의 `NAVER_BLOG_ID=` 줄**만** 쓴다(있으면 그 줄을 교체, 없으면 끝에 추가, 다른 줄은 그대로 — 3-1의 `IMAGE_PROVIDER`와 같은 방식). `<블로그 ID>` 자리에 받은 값을 넣는다:

```bash
cd "<작업 폴더 절대경로>" || exit 1
BID=<블로그 ID>
printf '%s' "$BID" | grep -Eq '^[A-Za-z0-9_-]+$' || { echo "블로그 ID 형식이 아닙니다(영문·숫자·_·-만)"; exit 1; }
[ -f .env ] || : > .env
awk -v v="$BID" '/^[[:space:]]*(export[[:space:]]+)?NAVER_BLOG_ID[[:space:]]*=/ { if (!d) print "NAVER_BLOG_ID=" v; d = 1; next } { print } END { if (!d) print "NAVER_BLOG_ID=" v }' .env > .env.tmp && cat .env.tmp > .env && echo "NAVER_BLOG_ID=$BID 저장"   # cat >로 덮어 써 권한·심링크 보존
rm -f .env.tmp   # 성공·실패와 무관하게 임시 파일 정리
```

이어서 "`knowledge/source-blogs.json`의 `own_blog.blogId`도 같은 값으로 맞춰 주세요 — `/naver-blog-autopilot:blog-run`은 두 값이 다르면 시작하지 않습니다." 한 줄을 안내한다(knowledge 파일은 담당자가 고친다). `나중에`면 `.env`를 건드리지 않고 "이 값이 없으면 lint final·upload 단계와 업로드가 멈춥니다"라고 알린 뒤 4단계로. 값을 저장했으면 2단계 Bash 블록을 한 번 더 실행해(진단만, 비용 0) 블로그 ID·네이버 세션 결과를 4단계 표에 반영한다 — 첫 셋업에서도 이 실행에서 로그인 안내까지 나온다.

## 4. 진단 결과 표와 조치

2단계(복사 후 상태는 3단계 출력, 이미지 AI 키는 3-1단계, 블로그 ID는 3-2단계 결과 반영) 결과를 **표**로 보여준다. 항목 | 상태 | 조치. 이미 갖춰진 항목은 "확인됨", 조치 칸은 "-".
세션 `LOGIN_NEEDED`는 오류가 아니라 "로그인 필요"로, `WRONG_ACCOUNT`는 "다른 계정 로그인"으로 표시한다.

| 항목 | 상태 | 조치 |
|---|---|---|
| OS | macOS / Windows(Git Bash) | - (Windows면 아래 설치 명령은 Windows 갈래 — PowerShell 창에서 실행) |
| PYTHONUTF8 (Windows만) | OK / NOT_SET | 아래 Windows 명령 `setx PYTHONUTF8 1` (새 창부터 적용 — Claude Code를 다시 열기) |
| uv | OK / MISSING | 아래 명령(표지 합성·이미지 생성이 `uv run --with pillow …`로 돈다 — 시스템 python3에는 Pillow가 없음) |
| python3 ≥ 3.11 | OK / MISSING | 3.11 이상 설치 (scaffold 스크립트용. naver-blog-cli는 uv가 자체 Python을 씀). **Windows**: `uv python install 3.12 --default`(`python`·`python3` 실행 파일을 `~\.local\bin`에 만듦) + 설정 → 앱 → 고급 앱 설정 → **앱 실행 별칭**에서 `python.exe`·`python3.exe`(앱 설치 관리자) 끄기 — `Microsoft Store 별칭만 있음`이 나오면 이 경우 |
| Playwright Chromium | OK / MISSING | 아래 명령 |
| naver-blog-cli | OK / MISSING | 아래 명령 |
| 네이버 세션 | 정상 / 로그인 필요 / 다른 계정 로그인 / blogId 없음 | 아래 로그인 절차. **blogId 없음**(`SKIPPED (blogId 없음 …)`)이면 3-2단계에서 `NAVER_BLOG_ID`를 넣은 뒤 이 커맨드를 다시 실행하라고 안내(첫 셋업에서는 `.env`·`knowledge/`가 아직 없어 이렇게 나오는 것이 정상). **다른 계정 로그인**(`WRONG_ACCOUNT` — 세션은 살아 있지만 글쓰기 화면이 다른 블로그로 이동)이면 출력의 이동 주소를 보여 주고 `<blogId>` 블로그 계정으로 로그인 절차를 다시 하라고 안내(기존 세션 파일을 덮어씀). 블로그 주소가 틀렸다면 `knowledge/source-blogs.json`의 `own_blog`를 고친다 |
| 블로그 ID (`.env` `NAVER_BLOG_ID` = `own_blog.blogId`) | OK / MISSING / MISMATCH | 3-2단계. `own_blog.blogId: MISSING`이면 `knowledge/source-blogs.json`의 `own_blog.blogId`를 `.env`와 같은 값으로 채우라고 안내(`/naver-blog-autopilot:blog-run`은 둘 중 하나가 없거나 다르면 시작하지 않는다) |
| 이미지 AI 키 (Gemini 또는 OpenAI) | OK (<provider>, 확인됨) / 없음(나중에 — 키 없음 모드) / CONFLICT / 거부 / 모델 없음 / 네트워크 | 3-1단계의 확인 결과 안내(제공자별). 없음이면 "키 없음 모드 — AI 이미지 슬롯 보류" |
| business-profile.md 필수 행 | OK / MISSING <행> / NOFILE | 3단계 `profile:` 줄. MISSING이면 "`knowledge/business-profile.md`의 <행>을 채워 주세요"(필수 = `업체명`·`연락처`·`상품·서비스`·`고객 지역`·`장소 검색어`·`업체 유형어`·`업종 일반어` 행 + `## 금칙어` 절 — 금칙어가 없으면 `- 없음` 한 줄). NOFILE이면 이 커맨드를 다시 실행(3단계 복사). 첫 셋업에서는 MISSING이 정상 |
| 한글 폰트(표지 합성) | OK / MISSING | 아래 안내 |
| photos/business-intro.png | OK / MISSING | 아래 안내 |
| knowledge/design-system.md | OK / 없음(경고) | 5단계 안내 |
| 학습 규칙 (knowledge/learned-preferences.md) | 적용 중 n개 · 후보 n개 / 첫 사용 — 정상 | - (3단계 `learned:` 줄. 파일이 없거나 적용 중 0개면 "첫 사용 — 정상"으로 표시하고 오류로 다루지 않는다) |

**누락된 항목에 대해서만** 그대로 실행할 수 있는 명령을 코드블록으로 출력한다. 진단의 `OS:` 값에 맞는 갈래만 보여 준다. macOS 명령은 **터미널**에서, Windows 명령은 **PowerShell 창**(시작 → "PowerShell")에서 실행한다 — 둘 다 Claude 입력창이 아니다.

- uv
  - macOS:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
  - Windows:
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
- python3 (Windows — Microsoft Store 별칭은 실제로 실행되지 않는다)
  ```powershell
  uv python install 3.12 --default
  ```
  그다음 설정 → 앱 → 고급 앱 설정 → **앱 실행 별칭**에서 `python.exe`·`python3.exe`(앱 설치 관리자)를 끄고 Claude Code를 다시 연다.
- PYTHONUTF8 (Windows만, 1회 — 한글 Windows 콘솔(cp949)에서 스크립트의 이모지 출력이 죽지 않게)
  ```powershell
  setx PYTHONUTF8 1
  ```
  새로 여는 창부터 적용된다. Claude Code를 닫았다가 다시 연다.
- Playwright Chromium
  - macOS:
    ```bash
    uv run --with playwright playwright install chromium
    # naver-blog-cli 설치 후에는: "$(uv tool dir)/naver-blog-cli/bin/playwright" install chromium
    ```
  - Windows (naver-blog-cli 설치 후):
    ```powershell
    & "$(uv tool dir)\naver-blog-cli\Scripts\playwright.exe" install chromium
    ```
- naver-blog-cli (PATH에 `~/.local/bin` 필요 — Windows는 `%USERPROFILE%\.local\bin`. macOS 터미널·PowerShell 모두 같은 명령)
  ```bash
  uv tool install git+https://github.com/spegas/naver-blog-cli
  ```
- 네이버 로그인 (**사람이 직접, 1회**). 로그인 스크립트는 설치본에 없으므로 저장소를 clone해서 쓴다. Claude 입력창이 아니라 **터미널(Windows는 PowerShell)에서**, 반드시 **작업 폴더에서** 실행한다. 세션 파일이 `<작업 폴더>/playwright-state/storage_state.json`에 저장된다.
  - macOS:
    ```bash
    [ -d ~/naver-blog-cli ] || git clone https://github.com/spegas/naver-blog-cli ~/naver-blog-cli
    cd "<작업 폴더 절대경로>"
    NAVER_STATE="$PWD/playwright-state/storage_state.json" \
      "$(uv tool dir)/naver-blog-cli/bin/python" ~/naver-blog-cli/login_setup.py
    ```
  - Windows (PowerShell, `<작업 폴더 Windows 경로>`는 1단계의 `작업 폴더(Windows 경로):` 값):
    ```powershell
    if (-not (Test-Path "$HOME\naver-blog-cli")) { git clone https://github.com/spegas/naver-blog-cli "$HOME\naver-blog-cli" }
    cd "<작업 폴더 Windows 경로>"
    $env:NAVER_STATE = "$PWD\playwright-state\storage_state.json"; & "$(uv tool dir)\naver-blog-cli\Scripts\python.exe" "$HOME\naver-blog-cli\login_setup.py"
    ```
  안내 문구: "브라우저 창이 열리면 직접 로그인하세요. **'로그인 상태 유지'를 반드시 체크**하고, 캡차·2단계 인증·기기 등록도 직접 처리해 주세요. 비밀번호는 저장되지 않고 쿠키 파일만 만들어집니다. 쿠키 파일(`playwright-state/`)은 계정 접근권한 그 자체라 공유·커밋하면 안 됩니다. 로그인 뒤 `/naver-blog-autopilot:blog-setup`을 다시 실행하면 세션이 '정상'으로 바뀝니다."
- 이미지 AI 키 — 3-1단계에서 고른 제공자의 안내(Gemini: `GEMINI_API_KEY=`, 결제 설정된 프로젝트의 키 / OpenAI: `OPENAI_API_KEY=`, 결제 수단·조직 인증)를 다시 보여 준다. `CONFLICT`가 남아 있으면 "`.env`의 `IMAGE_PROVIDER=`가 가리키는 제공자의 키를 넣거나, `IMAGE_PROVIDER=`를 가진 키의 제공자로 바꾸세요". 키 값은 채팅에 붙여넣지 않는다.
- 한글 폰트(표지 합성용, `scripts/make_cover.py`)
  ```
  대표이미지(표지)에 제목을 얹으려면 한글 폰트가 필요합니다. Pretendard를 받아(https://github.com/orioncactus/pretendard/releases)
  Pretendard-ExtraBold.otf·Pretendard-SemiBold.otf를 설치해 주세요.
  - macOS: 두 파일을 ~/Library/Fonts/ 에 넣습니다.
    (macOS 기본 /System/Library/Fonts/AppleSDGothicNeo.ttc가 있으면 그것으로도 만들 수 있습니다.)
  - Windows: 두 파일을 각각 우클릭 → "설치"(또는 "모든 사용자용으로 설치")합니다.
    (Windows 기본 맑은 고딕 Bold C:\Windows\Fonts\malgunbd.ttf가 있으면 그것으로도 만들 수 있습니다.)
  글꼴이 하나도 없으면 /naver-blog-autopilot:blog-run이 멈춥니다.
  ```
- photos/business-intro.png
  ```
  모든 글 끝 마무리 블록(📞 문의 헤딩 → 업체소개 이미지 → 장소 카드 → 해시태그)에 들어가는 고정 이미지입니다.
  업체명·연락처·주소가 담긴 업체소개 이미지를 작업 폴더의 photos/business-intro.png 로 넣어 주세요(파일명 그대로).
  이 파일이 없으면 /naver-blog-autopilot:blog-run이 시작하지 않습니다.
  ```

## 5. 다음 단계 안내

- `knowledge/design-system.md`가 없으면: "design-system.md가 없습니다. `blog-design-system` 스킬로 생성을 요청하세요. (글 검사 `lint_post.py`는 이 파일이 없어도 경고만 냅니다.)"
- `knowledge/design-system.md`가 이미 있으면(예: 레퍼런스 0 자기 글 기준 고정 골격·합니다체·title_region을 담은 판): "디자인 시스템을 고치려면 `blog-design-system` 스킬의 **갱신 모드**를 쓰세요(백업 → `work/design-system/proposed.md` → 담당자 승인 → `knowledge/` 교체). 3단계 복사는 이 파일을 덮어쓰지 않습니다."
- 처음 셋업이면 `knowledge/business-profile.md`·`knowledge/source-blogs.json`·`knowledge/official-sources.md`의 `[…]` 자리를 자기 업체 값으로 채우라고 안내한다(플러그인 README "처음 채울 것"). `business-profile.md`의 필수는 `업체명`·`연락처`·`상품·서비스`·`고객 지역`·`장소 검색어`·`업체 유형어`(제목에서 지울 업체 유형 표현)·`업종 일반어`(겹침 계산에서 뺄 흔한 단어) 행과 `## 금칙어` 절(금칙어가 없으면 `- 없음` 한 줄 — 비워 두면 lint가 멈춘다)이다. 선택 행은 `배지 문구`·`제목 정규화`·`홍보 표지어`·`공지 표지어`·`브랜드 색`, 업체 정보 행 `주소`·`제공 방식`·`지원 형태`는 스크립트가 확인하지 않지만 글·팩트체크가 업체 정보 근거로 쓴다(비어 있으면 그 주장은 출처필요). 비어 있는 필수 행이 있으면 스크립트가 기본값 없이 exit 2로 멈춘다 — 3단계 `profile:` 줄이 그 행을 알려 준다.
- 전제 안내(한 줄, 항상): "관련글 링크 게이트(업로드본 lint `related_links`)는 자기 블로그에 발행한 글이 2편 이상 있어야 통과합니다. 새 블로그라면 처음 2편은 네이버에서 직접 발행해 두세요 — 그 전에는 관련글 단계에서 멈춥니다. 디자인 시스템도 자기 글 1편을 레퍼런스 0으로 잽니다."
- 누락·로그인 필요 항목이 남아 있으면 해결 후 이 커맨드를 다시 실행하라고 안내한다.
- 이미지 AI 키만 없음(나중에)이면 오류가 아니다: "이미지 키 없이도 시작할 수 있습니다(키 없음 모드 — AI 이미지 슬롯 보류, 실사진만). 키를 넣으면 이 커맨드를 다시 실행해 확인하세요."
- 모두 갖춰졌고 3단계 `profile: OK`이면: "준비가 끝났습니다. `/naver-blog-autopilot:blog-run`으로 글 작성을 시작하세요." `profile:`이 OK가 아니면 이 문구를 쓰지 않고 "`knowledge/business-profile.md`의 <행>을 채운 뒤 이 커맨드를 다시 실행하세요"로 끝낸다(`/naver-blog-autopilot:blog-run`도 Step 0에서 같은 검사로 멈춘다).
- 항상 한 줄 덧붙인다: "글 내용·제목·이미지에 대한 의견은 언제든 `/naver-blog-autopilot:blog-feedback [글 번호] [발행 글 주소]`로 남기면 다음 글부터 반영됩니다(네이버에서 직접 고쳐 발행했다면 주소를 주세요 — 고친 부분을 비교합니다). 지금 쓰이는 규칙은 `/naver-blog-autopilot:blog-feedback rules`로 봅니다."
