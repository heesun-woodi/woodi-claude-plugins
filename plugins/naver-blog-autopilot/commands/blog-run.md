---
description: 네이버 블로그 글 한 편을 주제 리서치부터 네이버 임시저장까지 진행합니다(게이트 3개·에이전트 2개·lint·업로드).
argument-hint: "[주제 번호 또는 'report NNN' (선택)]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, Agent, SendMessage, AskUserQuestion
---

사용자(담당자)가 블로그 글 작업을 시작했다. 너(메인 세션)는 **오케스트레이터**다. 아래 순서대로 글 **한 편**을 진행하라.
사용자에게 보여주는 모든 안내 문구는 **한국어**로 쓴다. 비밀번호·API 키 값·세션 파일 내용은 출력하지 않는다.

인자: `$ARGUMENTS`
- 비어 있음 → Step 0부터 전체 진행.
- 숫자(예: `3`) → 주제 번호. 오늘 날짜 topics 파일이 있으면 Step 1 리서치를 건너뛰고 게이트 1에서 이 번호를 기본값으로 쓴다.
- `report NNN` → 맨 아래 "report NNN" 절만 수행하고 끝낸다(preflight·디스패치·파일 쓰기 없음).
- `resume NNN` → 맨 아래 "resume NNN" 절만 수행한다(멈춘 곳부터 이어서 — `final.md`가 있으면 Step 5 업로드만(세션이 없어 업로드를 미뤘을 때), 없고 `draft-v2.md`·`## 초안피드백`이 있으면 Step 3 이미지부터(키·실사진이 없어 멈췄을 때)).

---

## 운영 원칙 (모든 단계에 적용)

- **cwd = 작업 폴더**(`knowledge/`·`scripts/`·`work/`가 있는 폴더). 모든 경로는 작업 폴더 기준. 글 폴더는 `work/posts/<NNN-slug>/`(아래에서 `P`).
- **메인만 하는 일**: 사용자 게이트 3개(AskUserQuestion), `P/gates.md` 기록, 주제 리서치(Step 1)·이미지와 표지 합성(Step 3)·`final.md` 작성 = `scripts/build_final.py` 실행(Step 4)·업로드(Step 5), `work/variation-log.md` 기록, 피드백 기록(`scripts/feedback_log.py add` → `work/feedback-log.md`, 게이트 2·3)과 학습 정리(종료 보고 전 Skill `naver-blog-autopilot:blog-learn` — 디스패치 아님).
- **대화로 준 피드백도 기록**: blog-run 도중 담당자가 질문 화면 밖(일반 입력)으로 콘텐츠 의견을 말하면("도입이 너무 딱딱해요", "사진이 다 비슷해요" 등) 그것도 피드백이다. 단계는 지금 단계(게이트 1 = `게이트1`, 게이트 2·Step 2·수정 루프 = `게이트2`, Step 3·게이트 3 = `게이트3`, 그 밖 = `직접`), 범주는 게이트 2 "피드백 기록" 2번 기준으로 메인이 고르고, 범위를 한 번 물어(AskUserQuestion `앞으로 계속` / `이번 글만`) `feedback_log.py add --text='<원문>'`로 기록한다. 지금 글에 반영할 수 있으면 해당 단계의 흐름으로 처리한다(게이트 2 전후 초안 의견 → 게이트 2 수정 요청·수정 루프, 이미지 의견 → 게이트 3 재생성, 이미 지난 단계면 기록만 하고 종료 보고에 "이번 글에는 반영하지 못함").
- **멈출 때도 학습 정리**: 어떤 이유로 멈추든(게이트 2 `여기서 중단`, 디스패치 예산 초과, 에러 중단·보고, Step 3 뒤 이미지 부족, 세션 없음 모드) 종료 보고 **바로 전에** 아래 "학습 정리"를 한 번 한다 — 그때까지 기록한 피드백이 다음 글에 남게.
- **경로 보여 주기(Windows)**: Step 0의 `os: windows`면 담당자에게 파일 경로(게이트 2의 `draft-v2.md`, 게이트 3의 이미지·표지, 종료 보고의 글 폴더)를 보여 줄 때 Git Bash 경로 옆에 `C:\…` 형식을 함께 적는다(탐색기 주소창·Win+R에 붙여 넣을 수 있게): `for f in <절대경로들>; do printf '%s\n  %s\n' "$f" "$(cygpath -w "$f" | tr -d '\r')"; done`. macOS면 경로 하나만.
- **학습 규칙**(`knowledge/learned-preferences.md`, 없을 수 있음): `## 적용 중` 규칙은 writer·SEO·이미지·주제 리서치가 범주별로 따른다. 우선순위 = 잠긴 규칙(잠긴 규칙 = `business-profile.md` 금칙어·꼭 지켜야 할 점, `design-system.md` ⑤ 반드시 지킬 것(이미지 속 글자·얼굴 클로즈업·로고 금지, 홍보글은 실사진만, 사진 재사용 금지), ⑧ 지어내기 금지·출처·금칙 — 표지 제목·배지·전화번호 합성은 ⑤의 표지 예외로 허용) > `## 적용 중` > design-system 나머지 > structure-templates 예시. 학습 규칙은 잠긴 규칙을 바꾸지 못한다. 이 파일을 고치는 것은 blog-learn 스킬(담당자 승인 뒤)과 담당자뿐이다.
- **Pillow가 필요한 스크립트**(`make_cover.py`·`gen_image.py`)는 항상 `uv run --with pillow …`(gen_image는 `--with google-genai`도 — Gemini 경로용. OpenAI 경로는 표준 라이브러리라 추가 의존성이 없고, 명령은 제공자와 무관하게 같다)로 실행한다. 시스템 `python3`에는 Pillow가 없다. `build_final.py`·`lint_post.py`는 표준 라이브러리만 써서 `python3`로 돌린다.
- **Windows(Git Bash)**: Bash 호출마다 셸이 새로 뜨므로, cp949 콘솔에서 스크립트의 이모지 출력이 `UnicodeEncodeError`로 죽지 않게 `PYTHONUTF8=1`이 영구 설정돼 있어야 한다(`/naver-blog-autopilot:blog-setup`의 `setx PYTHONUTF8 1`). 설정 전이면 python 명령 앞에 `PYTHONUTF8=1 `을 붙인다. Step 0 블록은 스스로 `export PYTHONUTF8=1`을 한다.
- **서브에이전트는 2개뿐**이고 플러그인 네임스페이스로 부른다: `naver-blog-autopilot:blog-writer`(B·B'), `naver-blog-autopilot:blog-fact-checker`(C). model은 넘기지 않는다(에이전트 정의의 `opus`).
  발주 프롬프트에는 **경로만** 넣는다(내용을 붙여넣지 않는다). 절차 스킬은 `${CLAUDE_PLUGIN_ROOT}`가 펼쳐진 **절대경로** 그대로 넣는다.
- **서브에이전트는 사용자에게 묻지 않는다.** 질문은 반환 메시지·`factcheck.md`·`seo.md`의 `## 질문`(또는 "메인에 전달") 절로 돌아온다 → 메인이 AskUserQuestion으로 담당자에게 묻고, 답을 `gates.md`에 기록한 뒤 다음 발주·재개 메시지에 원문으로 넣는다.
- **재개는 `name` + `SendMessage`**: writer는 `blog-writer-<NNN>` 하나를 B부터 끝까지 재개한다(새 Agent로 다시 만들지 않는다). fact-checker는 회차마다 새 Agent `blog-fact-checker-<NNN>-r<k>`(r1, r2).
  `SendMessage`가 실패하면(세션이 바뀌어 에이전트가 없음) 같은 `subagent_type`·같은 `name`으로 새 Agent를 발주하고 B 입력 경로 전부 + B' 메시지를 함께 넣는다(디스패치 1회로 센다).
- **디스패치 예산**: 글 1편당 기본 3회(B·C·B'), 재작업 포함 **최대 7회**(B·C·B'·lint 재개 B'·게이트 2 B'·C r2·r2 반영 B'). Agent 발주와 SendMessage 재개를 모두 1회로 센다. 다음 디스패치가 8회째면 **하지 말고 멈춰서** 담당자에게 보고한다(지금까지 횟수·남은 문제·글 폴더 경로). Step 4의 B' 재개(빌더 텍스트 사유 — 혼합 출처 괄호·📞 헤딩·frontmatter — 또는 upload lint 텍스트 FAIL, 및 Step 5 exit 10·11의 B' 재개)도 1회로 센다 — 최악 경로에서 이것이 8회째면 하지 않고 중단·보고. 매 디스패치 뒤 `디스패치 n/7`을 한 줄로 알린다.
- **완료 확인**: 에이전트가 끝났다고 해도 출력 파일이 실제로 있는지 `ls`로 확인한다. 없으면 같은 에이전트를 1회 재개(예산 포함)하고, 그래도 없으면 멈추고 보고한다.
- **gates.md 절은 4개로 고정**: `## 선택` · `## 초안피드백` · `## 이미지승인` · `## 업로드`. 다른 절을 만들지 않는다. 절 단위로 **append**하고, 같은 절이 둘 이상이면 **마지막 것이 유효**하다. 각 절 첫 줄은 `- 일시: YYYY-MM-DD HH:MM`.
- **에러 시 중단·보고**: 예상 밖 오류(스크립트 exit 2, 파일 없음, 요약 줄 없음 등)는 우회하지 말고 멈춘 뒤 단계·명령·출력 첫 줄·글 폴더를 보고한다. 같은 오류 재시도는 한 번까지.
- 메인은 `draft.md`·`draft-v2.md`·`factcheck*.md`·`research.md`·`seo.md`를 고치지 않는다(예외: B' 생략 규칙의 `cp draft.md draft-v2.md` 한 번).
- **미검증 사실 변경**: writer 반환의 "사실 문장 변경"이 `없음`이 아니면 그 문장은 fact-checker가 보지 않은 것이다. 게이트 2 전에 생긴 것은 게이트 2 수정 루프의 C r2에서 검토한다. C r2 반영 B'가 다시 "사실 문장 변경"을 보고하거나, 게이트 2 이후(Step 4·5의 B' 재개)에 생기면 r3를 발주하지 않고, 바뀐 문장을 담당자에게 보여 주며 AskUserQuestion `이대로 진행` / `여기서 중단`.

---

## Step 0. preflight

한 번의 Bash 호출로 확인한다. 키 값은 출력하지 않는다. `naver-blog-cli`는 종료 코드가 항상 0이므로 **stdout 문구**(`세션 정상` + `글쓰기 가능`)로 판정한다. `check-session`은 **다른 계정으로 로그인된 세션도 통과**시키므로(글쓰기 화면이 그 계정 블로그로 리다이렉트돼도 iframe이 붙음 — 실측), 세션이 정상이면 `scripts/check_blog_account.py`로 글쓰기 화면이 `<blogId>` 블로그로 열리는지 한 번 더 본다(헤드리스, 창 안 뜸, 약 10초, 글은 쓰지 않음).

```bash
PYUTF8_BEFORE="${PYTHONUTF8:-}"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export PYTHONUTF8=1   # Windows cp949 콘솔에서 이모지 출력 오류 방지 (macOS 영향 없음)
case "$(uname -s)" in MINGW*|MSYS*) echo "os: windows"; [ "$PYUTF8_BEFORE" = 1 ] || echo "PYTHONUTF8: NOT_SET (setx PYTHONUTF8 1 후 Claude Code 다시 시작)";; *) echo "os: $(uname -s | tr -d '\r')";; esac
echo "작업 폴더: $PWD"
[ -d knowledge ] && [ -d scripts ] && echo "work-folder: OK" || echo "work-folder: MISSING"
# 이미지 키(blog-setup 2단계와 같은 판정, 네트워크 조회 없음): IMAGE_PROVIDER > GEMINI_API_KEY > OPENAI_API_KEY. 존재 여부만 본다 — 키 값·IMAGE_MODEL은 출력하지 않고, IMAGE_PROVIDER도 gemini/openai일 때만 출력한다.
# gen_image.py·check_image_key.py와 같은 규칙(여기서 .env는 작업 폴더 .env): 키: API 키(GEMINI_API_KEY/OPENAI_API_KEY)가 든 첫 .env 파일의 값. 어느 파일에도 없으면 환경변수. IMAGE_PROVIDER·IMAGE_MODEL: 키를 찾은 .env의 값(그 파일에 없으면 미지정). 키를 환경변수에서 읽을 때는 항목마다 cwd .env → 환경변수 중 처음 값이 있는 곳.
# 따옴표 없는 값은 공백+# 이후가 주석, #로 시작하면 빈 값, 따옴표 안이 공백뿐이면 빈 값. 같은 이름이 여러 줄이면 처음 나온 비어 있지 않은 값. export·따옴표·CRLF 허용.
ENVGET='{ sub(/\r$/, ""); l = $0; sub(/^[ \t]+/, "", l); sub(/^export[ \t]+/, "", l)
  i = index(l, "="); if (i == 0) next
  k = substr(l, 1, i - 1); sub(/[ \t]+$/, "", k); if (k != n) next
  v = substr(l, i + 1); sub(/^[ \t]+/, "", v); q = substr(v, 1, 1)
  if (q == "\"" || q == sq) { v = substr(v, 2); j = index(v, q); if (j) v = substr(v, 1, j - 1); if (v ~ /^[ \t]*$/) v = "" }
  else { if (substr(v, 1, 1) == "#") v = ""; sub(/[ \t]+#.*$/, "", v); sub(/[ \t]+$/, "", v) }
  if (v != "") { if (show) print v; f = 1; exit } }
END { exit(f ? 0 : 1) }'
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
[ -f knowledge/design-system.md ] && echo "design-system.md: OK" || echo "design-system.md: MISSING"
# 필수 profile 행(업체명·연락처·상품·서비스·고객 지역·장소 검색어·업체 유형어·업종 일반어 + ## 금칙어): profile: OK / MISSING <행,…> / NOFILE 한 줄
[ -f scripts/check_profile.py ] && python3 scripts/check_profile.py 2>&1 | tr -d '\r' | head -1
MINIMG=$(grep -o 'min_images=[0-9]*' knowledge/design-system.md 2>/dev/null | head -1 | cut -d= -f2)
echo "min_images: ${MINIMG:-3}"   # lint 블록이 없을 때 = lint 기본값
echo "photos: $(find photos -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \) ! -name 'business-intro.png' 2>/dev/null | wc -l | tr -d ' ')"
[ -f photos/business-intro.png ] && echo "intro-image: OK" || echo "intro-image: MISSING"
# 글꼴: macOS(Pretendard·AppleSDGothicNeo) / Windows(Pretendard 사용자·시스템 설치, 맑은 고딕 Bold)
LAD="${LOCALAPPDATA:-}"; WD="${WINDIR:-${windir:-${SYSTEMROOT:-}}}"
if command -v cygpath >/dev/null 2>&1; then [ -n "$LAD" ] && LAD="$(cygpath -u "$LAD")"; [ -n "$WD" ] && WD="$(cygpath -u "$WD")"; fi
if [ -f "$HOME/Library/Fonts/Pretendard-ExtraBold.otf" ] || { [ -n "$LAD" ] && [ -f "$LAD/Microsoft/Windows/Fonts/Pretendard-ExtraBold.otf" ]; } || { [ -n "$WD" ] && [ -f "$WD/Fonts/Pretendard-ExtraBold.otf" ]; }; then echo "font: OK (Pretendard)"
elif [ -f /System/Library/Fonts/AppleSDGothicNeo.ttc ]; then echo "font: OK (AppleSDGothicNeo — Pretendard 권장)"
elif [ -n "$WD" ] && [ -f "$WD/Fonts/malgunbd.ttf" ]; then echo "font: OK (맑은 고딕 — Pretendard 권장)"
else echo "font: MISSING"; fi
command -v uv >/dev/null 2>&1 && echo "uv: OK" || echo "uv: MISSING"
for s in fetch_posts.py fetch_post.py dedupe_check.py lint_post.py gen_image.py make_cover.py build_final.py naver_upload.sh check_blog_account.py check_image_key.py feedback_log.py diff_published.py check_profile.py; do
  if [ ! -f "scripts/$s" ]; then echo "script: MISSING $s"
  elif ! cmp -s "scripts/$s" "${CLAUDE_PLUGIN_ROOT}/scaffold/scripts/$s"; then echo "script: OUTDATED $s"; fi
done
# 학습 규칙(knowledge/learned-preferences.md): `## 적용 중`·`## 후보` 절의 `| L-001 | …` 행 수. 없으면 첫 사용(경고 아님)
if [ -f knowledge/learned-preferences.md ]; then
  LCNT=$(awk '/^## /{ s = $0; next } /^\|[ \t]*L-[0-9]+/{ if (s ~ /^## 적용 중/) a++; else if (s ~ /^## 후보/) c++ } END { printf "%d %d", a, c }' knowledge/learned-preferences.md | tr -d '\r')
  echo "learned: 적용 중 ${LCNT% *}개 · 후보 ${LCNT#* }개"
else echo "learned: 없음(첫 사용)"; fi
# 블로그 ID(기본값 없음): .env NAVER_BLOG_ID(lint final·upload·naver_upload.sh가 읽음)와 knowledge/source-blogs.json own_blog.blogId(스킬이 읽음)가 둘 다 있고 같아야 한다. 블로그 ID 형식([A-Za-z0-9_-])이 아니면(`[…]` 자리표시 포함) 빈 값으로 본다
ENV_ID=""; [ -f .env ] && ENV_ID="$(awk -v n=NAVER_BLOG_ID -v show=1 -v sq="'" "$ENVGET" .env | tr -d '\r')"
printf '%s' "$ENV_ID" | grep -Eq '^[A-Za-z0-9_-]+$' || ENV_ID=""
OWN_ID=""; [ -f knowledge/source-blogs.json ] && \
  OWN_ID=$( { python3 -c "import json,re;o=json.load(open('knowledge/source-blogs.json',encoding='utf-8')).get('own_blog');b=str((o.get('blogId') if isinstance(o,dict) else o) or '').strip();print(b if re.fullmatch(r'[A-Za-z0-9_-]+',b) else '')" 2>/dev/null || true; } | tr -d '\r')
BLOG_ID=""
if [ -z "$ENV_ID" ]; then echo "blogId: MISSING (.env NAVER_BLOG_ID 없음)"
elif [ -z "$OWN_ID" ]; then echo "blogId: MISSING (knowledge/source-blogs.json own_blog.blogId 없음)"
elif [ "$ENV_ID" != "$OWN_ID" ]; then echo "blogId: MISMATCH (.env NAVER_BLOG_ID=$ENV_ID ≠ own_blog.blogId=$OWN_ID)"
else BLOG_ID="$ENV_ID"; echo "blogId: $BLOG_ID"; fi
if [ -z "$BLOG_ID" ]; then echo "session: SKIPPED (blogId 없음)"
elif command -v naver-blog-cli >/dev/null 2>&1; then
  SESS=$(NAVER_BLOG_ID="$BLOG_ID" naver-blog-cli check-session 2>&1 | tr -d '\r')
  if echo "$SESS" | grep -q '세션 정상' && echo "$SESS" | grep -q '글쓰기 가능'; then
    UVT="$(uv tool dir 2>/dev/null)"; command -v cygpath >/dev/null 2>&1 && [ -n "$UVT" ] && UVT="$(cygpath -u "$UVT")"
    CLI_PY=""; for c in "$UVT/naver-blog-cli/bin/python" "$UVT/naver-blog-cli/Scripts/python.exe"; do [ -x "$c" ] && { CLI_PY="$c"; break; }; done
    if [ -n "$CLI_PY" ] && [ -f scripts/check_blog_account.py ]; then
      ACCT=$("$CLI_PY" scripts/check_blog_account.py "$BLOG_ID" 2>&1 | tr -d '\r'; exit "${PIPESTATUS[0]}"); ACCT_RC=$?
      case "$ACCT_RC" in
        0) echo "session: OK" ;;
        21) echo "session: WRONG_ACCOUNT — $(echo "$ACCT" | tail -1)" ;;
        *) echo "session: LOGIN_NEEDED — $(echo "$ACCT" | tail -1)" ;;
      esac
    else echo "session: LOGIN_NEEDED — 계정 확인 불가(naver-blog-cli 의 uv tool python 또는 scripts/check_blog_account.py 없음 — 업로드도 exit 20)"; fi
  else echo "session: LOGIN_NEEDED — $(echo "$SESS" | head -1)"; fi
else echo "session: MISSING (naver-blog-cli 없음)"; fi
for f in "${CLAUDE_PLUGIN_ROOT}/skills/blog-draft-writer/SKILL.md" \
         "${CLAUDE_PLUGIN_ROOT}/skills/blog-draft-writer/references/structure-templates.md" \
         "${CLAUDE_PLUGIN_ROOT}/skills/blog-naver-seo/SKILL.md" \
         "${CLAUDE_PLUGIN_ROOT}/skills/blog-fact-check/SKILL.md" \
         "${CLAUDE_PLUGIN_ROOT}/skills/blog-fact-check/references/claim-types.md"; do
  [ -f "$f" ] && echo "skill: OK $f" || echo "skill: MISSING $f"
done
```

| 결과 | 조치 |
|---|---|
| `work-folder: MISSING` | "작업 폴더가 아닙니다. 먼저 `/naver-blog-autopilot:blog-setup`을 실행하세요." 안내 후 **중단** |
| `IMAGE_KEY: MISSING` | 이미지 키(Gemini/OpenAI)가 없다. `/naver-blog-autopilot:blog-setup` 3-1단계의 두 제공자 안내를 짧게 **경고로 보여 주고 계속**: Gemini — https://aistudio.google.com/apikey, 결제(Billing) 설정된 Google Cloud 프로젝트의 키, `.env`에 `GEMINI_API_KEY=…` / OpenAI — https://platform.openai.com/api-keys, 결제 수단 등록(GPT 이미지는 조직 인증이 필요할 수 있음), `.env`에 `OPENAI_API_KEY=…`. 채팅에 붙여넣지 않기. 이 실행은 "키 없음 모드": Step 3에서 photo 슬롯만 처리하고 ai 슬롯은 `보류`(표지 `00`은 `photos/` 실사진을 배경으로 `make_cover.py`만 돌려 만들 수 있다 — 비용 0). 이때 `photos:` < `min_images:`이면 실사진만으로 이미지 수를 못 채워 업로드까지 갈 수 없다 — B 발주 전에 묻는다(아래 [B] 참고) |
| `IMAGE_KEY: CONFLICT` | `IMAGE_PROVIDER`(키: API 키(GEMINI_API_KEY/OPENAI_API_KEY)가 든 첫 .env 파일의 값. 어느 파일에도 없으면 환경변수. IMAGE_PROVIDER·IMAGE_MODEL: 키를 찾은 .env의 값(그 파일에 없으면 미지정). 키를 환경변수에서 읽을 때는 항목마다 cwd .env → 환경변수 중 처음 값이 있는 곳.)가 가리키는 제공자의 키가 없거나 값이 `gemini`/`openai`가 아니다(출력 괄호 참고 — 잘못된 값은 키가 섞였을 수 있어 출력하지 않는다. 담당자에게도 그 줄 값을 붙여넣게 하지 않는다). 이대로면 `gen_image.py`가 오류로 멈춘다. "`.env`를 고쳐 주세요 — `IMAGE_PROVIDER=`가 가리키는 제공자의 키(`GEMINI_API_KEY=` 또는 `OPENAI_API_KEY=`)를 넣거나, `IMAGE_PROVIDER=`를 가진 키의 제공자로 바꾸거나 줄을 지우세요(키를 채팅에 붙여넣지 않기). 고친 뒤 `/naver-blog-autopilot:blog-setup`으로 확인할 수 있습니다." 안내 후 **중단** |
| `design-system.md: MISSING` | "`blog-design-system` 스킬로 디자인 시스템을 먼저 만들어 주세요." 안내 후 **중단** |
| `blogId: MISSING` / `MISMATCH` | 글을 올릴 블로그 ID가 없거나 두 곳의 값이 다르다. 출력 괄호대로 "작업 폴더 `.env`의 `NAVER_BLOG_ID=`와 `knowledge/source-blogs.json`의 `own_blog.blogId`를 같은 블로그 ID(`blog.naver.com/<여기>`)로 채워 주세요 — `.env` 줄은 `/naver-blog-autopilot:blog-setup`이 받아 적어 줍니다." 안내 후 **중단**(lint는 `--blog-id`가 없으면 `.env` 값을, 업로드 스크립트는 넘겨받은 `--blog-id`를, 스킬은 `own_blog.blogId`를 읽는다. 기본값 없음. 이때 `session: SKIPPED`는 따로 다루지 않는다) |
| `profile: MISSING <행>,…` / `profile: NOFILE` (그 밖에 `profile: OK`가 아닌 출력 포함) | 필수 profile 값이 비었다. MISSING이면 "`knowledge/business-profile.md`의 <행>을 채워 주세요"(출력에 나온 행 이름을 그대로 — `## 금칙어` 절은 금칙어가 없으면 `- 없음` 한 줄), NOFILE이면 "`knowledge/business-profile.md`가 없습니다 — `/naver-blog-autopilot:blog-setup`을 다시 실행하세요" 안내 후 **중단**(필수 = `업체명`·`연락처`·`상품·서비스`·`고객 지역`·`장소 검색어`·`업체 유형어`·`업종 일반어` 행 + `## 금칙어` 절. 비어 있으면 dedupe·lint·표지·빌드가 exit 2로 멈춘다) |
| `session: LOGIN_NEEDED` / `MISSING` | "업로드 전까지 로그인해 두세요"라고 **경고하고 계속**(Step 4까지 진행). 이 실행은 "세션 없음 모드": Step 5는 `--dry-run`만 하고 로그인 안내 후 끝낸다 |
| `session: WRONG_ACCOUNT` | 세션은 살아 있지만 **다른 계정**이라 `<blogId>` 블로그에 글을 쓸 수 없다(출력에 이동한 블로그 주소가 나온다). "업로드 전까지 `<blogId>` 블로그 계정으로 다시 로그인해 두세요 — 지금 세션은 다른 계정입니다"라고 **경고하고 계속**. "세션 없음 모드"와 같이 Step 5는 `--dry-run`만 한다. 로그인 안내는 `/naver-blog-autopilot:blog-setup` 4단계와 같되 **그 블로그 계정으로** 로그인하라고 명시 |
| `intro-image: MISSING` | "마무리 블록을 만들 수 없습니다 — `photos/business-intro.png`를 넣어 주세요." 안내 후 **중단**(`build_final.py`가 모든 글 끝에 붙이는 고정 자산. `photos:` 수에는 세지 않는다) |
| `font: MISSING` | "표지(대표이미지)를 만들 수 없습니다 — Pretendard(ExtraBold·SemiBold)를 설치하세요. macOS: `~/Library/Fonts/`에 넣기(또는 `/System/Library/Fonts/AppleSDGothicNeo.ttc`가 있는 macOS). Windows: 글꼴 파일 우클릭 → 설치(`%LOCALAPPDATA%\Microsoft\Windows\Fonts` 또는 `C:\Windows\Fonts`), 또는 기본 맑은 고딕 Bold `C:\Windows\Fonts\malgunbd.ttf`가 있는지 확인." 안내 후 **중단**(`make_cover.py`는 한글 폰트가 없으면 추측 렌더 없이 exit 2) |
| `PYTHONUTF8: NOT_SET` | (Windows만) "PYTHONUTF8이 영구 설정돼 있지 않아 뒤 단계의 python 명령이 이모지 출력에서 멈출 수 있습니다 — PowerShell에서 `setx PYTHONUTF8 1`을 실행한 뒤 Claude Code를 다시 시작하세요." **경고하고 계속**. 이번 실행에서는 `python3`·`uv run`·`bash scripts/…` 명령 앞에 `PYTHONUTF8=1 `을 붙인다 |
| `uv: MISSING` | "`uv`가 없어 표지 합성·이미지 생성(`uv run --with pillow …`)을 할 수 없습니다." + `/naver-blog-autopilot:blog-setup`의 uv 설치 명령 안내 후 **중단** |
| `skill: MISSING` | 플러그인 설치가 깨짐 — 경로를 보고하고 **중단** |
| `script: MISSING` / `script: OUTDATED` | 작업 폴더 `scripts/`가 없거나 플러그인보다 오래됨 → "`/naver-blog-autopilot:blog-setup <작업 폴더>`를 다시 실행하세요(scripts는 최신본으로 갱신, knowledge는 보존)." 재실행 안내 후 **중단** |
| `os: …` | 정보 줄. `os: windows`면 이번 실행에서 경로를 보여 줄 때 `cygpath -w` 형식을 함께 적는다(운영 원칙 "경로 보여 주기") |
| `learned: …` | 정보 줄(중단·경고 아님). `적용 중 n개 · 후보 n개`를 시작 안내에 한 줄로 보여 준다. `learned: 없음(첫 사용)`이면 학습 규칙 없이 진행한다(아래 발주·재개 메시지의 `knowledge/learned-preferences.md`는 빼고 보낸다) |

중단할 항목이 없으면(경고 항목은 모드만 기억하고) 기발행 글 목록을 갱신한다(`<blogId>`는 위 출력값):

```bash
python3 scripts/fetch_posts.py --all <blogId> --out work/own-posts.json
```

실패하면 중단·보고. 위 `skill: OK` 줄의 절차 스킬 5개 **절대경로**를 기억해 둔다 — 아래 발주·재개 메시지의 `${CLAUDE_PLUGIN_ROOT}/…` 자리에는 이 절대경로를 넣는다(변수 문자열 그대로 넘기지 않는다).

## Step 1. 주제 리서치 (메인)

- 인자로 번호가 왔고 `work/topics/$(date +%F)-topics.md`가 있으면 → 리서치를 건너뛰고 게이트 1로.
- 그 밖에는 **Skill 도구로** `naver-blog-autopilot:blog-topic-research`를 실행해 메인이 직접 수행한다(서브에이전트 아님). Step 0에서 `work/own-posts.json`을 방금 갱신했으므로 스킬의 1단계(`--all` 갱신)는 건너뛰어도 된다. 스킬의 자체검증이 `ALL OK`여야 끝난다.
- 학습 규칙: 스킬이 `knowledge/learned-preferences.md`(있으면) `## 적용 중`의 `범주=주제` 규칙을 후보 선정·제외에 반영한다(규칙으로 뺀 후보는 "제외한 주제와 이유"에 `학습 규칙 L-…`로 남는다).
- 산출: `work/topics/<YYYY-MM-DD>-topics.md`(열 10개: 번호 | 제목안 | 핵심 키워드 | 검색 의도 | 출처 글(링크) | 출처 글 chars/images | 우리 블로그 중복 | 추천 유형 | 추가 리서치 포인트 | 변주 제안).

## ● 게이트 1 — 주제 선택

**먼저 "이번 제목 지역"을 계산한다**(디자인 시스템 ⑦ `title_region` 로테이션). `work/variation-log.md`(7열, 마지막 열 `title_region`; 없을 수 있음)와 `knowledge/business-profile.md`의 `고객 지역` 행(적힌 순서 그대로)을 읽어, 최근 4편의 `title_region`에 없는 첫 지역을 고른다(로그 없음 → 첫 지역). 인자 없이 실행하면 기본값만, 게이트 1 뒤 담당자가 고른 지역 2개를 인자로 주면 최종 "제목 지역"까지 출력한다:

```bash
python3 - <<'PY'        # 게이트 1 뒤에는 고른 지역 2개를 인자로: python3 - <지역1> <지역2> <<'PY'
import os, sys
sys.path.insert(0, "scripts"); import lint_post
order = lint_post.load_regions("knowledge")                  # business-profile.md `고객 지역` 순서
used = []                                                    # variation-log title_region 열(오래된 → 최근)
if os.path.isfile("work/variation-log.md"):
    for ln in open("work/variation-log.md", encoding="utf-8"):
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) >= 7 and cols[0][:4].isdigit():
            used.append(cols[6])
recent = used[-4:]
base = next((r for r in order if r not in recent), order[0])
print(f"이번 제목 지역: {base} (최근 4편 title_region: {', '.join(recent) or '없음'})")
picked = sys.argv[1:]
if picked:
    last = lambda r: max((i for i, u in enumerate(used) if u == r), default=-1)   # -1 = 안 쓰임
    rank = lambda r: order.index(r) if r in order else len(order)
    tr = base if base in picked else min(picked, key=lambda r: (last(r), rank(r)))  # 더 오래전에 쓰인 쪽, 동률이면 순서 앞쪽
    print(f"제목 지역: {tr}")
PY
```

topics 표와 "이번 제목 지역"을 담당자에게 보여 준 뒤 **AskUserQuestion** 한 번으로 묻는다.

1. 번호 — 옵션은 추천 후보 최대 4개(`<번호>. <제목안>`), 그 밖의 번호는 기타 입력. 인자로 번호가 왔으면 그 번호를 첫 옵션으로. 질문 문구에 "주제에 대한 바람(예: '공지성 주제는 앞으로 빼 주세요', '가격 비교 주제를 더 다뤄 주세요')도 기타에 적을 수 있습니다"를 함께 적는다.
2. 유형 — `정보` / `홍보`(해당 행의 "추천 유형"을 첫 옵션으로).
3. 지역 키워드 2개 — multiSelect: 첫 옵션 = 이번 제목 지역(`… (이번 제목 지역)`), 나머지는 고객 지역 순서대로 3개(빠진 지역은 기타 입력). 정확히 2개가 아니면 이 질문만 다시 묻는다. 질문 문구에 "이번 제목 지역을 넣으면 제목에 그 지역명이 들어갑니다(글마다 번갈아)"라고 함께 적는다.

답을 받으면 위 스니펫을 고른 지역 2개를 인자로 다시 돌려 **제목 지역**을 확정한다(고른 2개에 이번 제목 지역이 있으면 그것, 없으면 2개 중 로그상 더 오래전에 쓰인 쪽 — 안 쓰인 지역 우선, 같으면 고객 지역 순서 앞쪽).

**주제 선호(기타 입력)**: 1번 기타 입력이 번호가 아니라 주제에 대한 바람("○○ 주제는 앞으로 제외/더 다뤄 줘" 등)이면 원문을 그대로 기억하고, 범위를 게이트 2 "피드백 기록" 3번과 같은 방식으로 한 번 묻고(AskUserQuestion — `앞으로 계속` / `이번 글만`), 번호 질문만 다시 묻는다(이번 topics 표는 그대로 — 규칙은 다음 주제 리서치부터 반영). 글 폴더를 만든 직후 기록한다(원문 따옴표 처리는 게이트 2와 같다):

```bash
FID=$(python3 scripts/feedback_log.py add --post <NNN-slug> --stage 게이트1 --category 주제 --scope "<앞으로 계속|이번 글만>" --text='<주제 선호 원문>' | tr -d '\r'); echo "$FID"
```

기록한 id는 `## 선택`의 `- 피드백 기록: F-…(<범위>)` 줄로 남긴다(없으면 줄을 쓰지 않는다).

번호를 여러 개 고르면 이번 실행은 **한 편만** 진행한다 — 어느 번호부터 할지 한 번 더 묻고, 나머지는 종료 보고에 "`/naver-blog-autopilot:blog-run <번호>`로 이어서" 안내한다(하루 1~2편 이내).

선택이 끝나면 글 폴더를 만든다.

```bash
LAST=$(ls -d work/posts/[0-9][0-9][0-9]-* 2>/dev/null | sed -E 's#.*/([0-9]{3})-.*#\1#' | sort -n | tail -1)
NNN=$(printf '%03d' $((10#${LAST:-0} + 1))); echo "NNN=$NNN"
```

- slug = 고른 행의 제목안 핵심어 2~4개를 `-`로 이은 것(한글 그대로, 공백·기호 제거, 40자 이내). 예(가상): `001-자전거-정기-점검-순서`.
- `mkdir -p work/posts/<NNN-slug>/images`
- `P/topic.md` = topics 파일의 표 머리 줄 + 구분선 + 고른 행 **원문 그대로**(3줄).
- `P/gates.md`를 만들고 `## 선택`을 쓴다:

```markdown
# gates — <NNN-slug>

## 선택
- 일시: YYYY-MM-DD HH:MM
- 번호: 3
- 유형: 정보
- 지역 키워드: 가나동, 다라동
- 제목 지역: 가나동
- 카테고리: <own_blog.categories.info 값>
- topics 파일: work/topics/YYYY-MM-DD-topics.md
- topics 행: | 3 | … (고른 행 원문 그대로) … |
```

카테고리는 `knowledge/source-blogs.json`의 `own_blog.categories.info` 값을 쓰고, 담당자가 다른 것을 지정할 때만 바꾼다(`own_blog.categories` 값 중 하나). 위 예의 지역·slug는 가상 값이다.

## [B] 초안 — `naver-blog-autopilot:blog-writer` 발주 (디스패치 1)

**발주 전 확인(키 없음 + 실사진 부족)**: 키 없음 모드이고 Step 0의 `photos:` 값이 `min_images:`보다 작으면, 이 글은 이미지 수 기준을 채우지 못해 임시저장까지 갈 수 없다. 이유를 한 줄로 알리고 **AskUserQuestion** `초안까지만 진행(업로드 불가)` / `중단하고 키·사진 준비`.
- `중단하고 키·사진 준비` → `.env`에 이미지 키(Gemini `GEMINI_API_KEY` — 결제 설정된 Google Cloud 프로젝트의 키 / OpenAI `OPENAI_API_KEY` — 결제 수단 등록·필요 시 조직 인증. blog-setup 3-1단계 안내) 또는 `photos/`에 실사진 `min_images`장 이상을 준비하라고 안내하고 끝낸다(디스패치 0).
- `초안까지만 진행(업로드 불가)` → 그대로 B부터 진행한다. Step 3 끝의 "확정 이미지 수 확인"에서 멈추고 `resume`을 안내하게 된다.

```
Agent 도구
  subagent_type: naver-blog-autopilot:blog-writer
  name: blog-writer-<NNN>
  prompt:
    mode: B
    글 폴더: work/posts/<NNN-slug>/
    입력: work/posts/<NNN-slug>/gates.md (## 선택), work/posts/<NNN-slug>/topic.md,
          knowledge/design-system.md, knowledge/business-profile.md, knowledge/official-sources.md,
          work/variation-log.md (없을 수 있음), work/own-posts.json,
          knowledge/learned-preferences.md (있으면 — 학습 규칙. 잠긴 규칙 다음, 디자인 시스템보다 우선)
    절차 스킬: ${CLAUDE_PLUGIN_ROOT}/skills/blog-draft-writer/SKILL.md
              ${CLAUDE_PLUGIN_ROOT}/skills/blog-draft-writer/references/structure-templates.md
    출력: work/posts/<NNN-slug>/research.md, work/posts/<NNN-slug>/draft.md
    반환에 "학습 규칙 적용: L-…"(없으면 "없음") 한 줄을 넣을 것
```

반환을 받으면 `ls P/research.md P/draft.md`로 확인하고, 반환의 lint 결과·`[출처 필요]` 건수·`학습 규칙 적용:` 줄·`## 질문`을 기록해 둔다(writer 반환마다 `학습 규칙 적용:` 줄을 모아 종료 보고에 쓴다). `## 질문`(예: ⑨ 홍보 비율 초과)은 아래 "질문 처리"대로 담당자에게 묻는다.

## [C] 근거 검토 — `naver-blog-autopilot:blog-fact-checker` 발주 (디스패치 2)

```
Agent 도구
  subagent_type: naver-blog-autopilot:blog-fact-checker
  name: blog-fact-checker-<NNN>-r1
  prompt:
    회차: r1
    초안: work/posts/<NNN-slug>/draft.md
    리서치: work/posts/<NNN-slug>/research.md
    지식: knowledge/official-sources.md, knowledge/business-profile.md
    절차 스킬: ${CLAUDE_PLUGIN_ROOT}/skills/blog-fact-check/SKILL.md
              ${CLAUDE_PLUGIN_ROOT}/skills/blog-fact-check/references/claim-types.md
    출력: work/posts/<NNN-slug>/factcheck.md
```

반환 뒤 요약 줄과 질문 여부를 읽는다:

```bash
F=work/posts/<NNN-slug>/factcheck.md
S=$(grep -m1 -E '^요약: PASS [0-9]+ \| FAIL [0-9]+ \| 출처필요 [0-9]+ \| 시점확인 [0-9]+' "$F") || { echo "요약 줄 없음"; exit 1; }
FAIL=$(echo "$S" | sed -E 's/.*FAIL ([0-9]+).*/\1/'); NEED=$(echo "$S" | sed -E 's/.*출처필요 ([0-9]+).*/\1/')
echo "$S"; echo "FAIL+출처필요=$((FAIL + NEED))"
grep -q '^## 질문' "$F" && echo "질문: 있음" || echo "질문: 없음"
```

"요약 줄 없음"이면 중단·보고(완료되지 않은 리포트).

### 질문 처리 (C·B·B' 공통)

`factcheck.md`(또는 `factcheck-r2.md`)에 `## 질문`이 있으면 **FAIL+출처필요 건수와 무관하게** 다음 디스패치 전에 담당자에게 묻는다. writer 반환의 `## 질문`, `seo.md` 끝 "메인에 전달"도 같다.
- AskUserQuestion으로 질문을 원문 그대로(id 포함) 묻는다(한 번에 최대 4개, 넘으면 나눠서).
- 답은 즉시 `P/gates.md`에 `## 초안피드백` 절로 append한다: `- 일시: …` · `- 질문 답: <id> — <담당자 답 원문>`(여러 줄). 이전 `## 초안피드백`이 있으면 그 절의 `제목:`·`톤:`·`길이:`·`수정 요청 원문:`·`피드백 기록:`·기존 `질문 답:` 줄을 새 절에 그대로 옮겨 적는다(마지막 절만 유효하므로 앞 내용이 사라지지 않게). 게이트 2 기록 때 다시 쓰는 `## 초안피드백`에도 `질문 답:` 줄을 그대로 옮겨 적는다.
- 다음 writer 재개 메시지에 `질문 답:` 원문을 넣는다.

## [B'] 수정 + SEO — writer 재개 (디스패치 3)

`SendMessage`로 `blog-writer-<NNN>`을 재개한다. FAIL+출처필요 수에 따라 범위가 다르다.

**(a) FAIL+출처필요 ≥ 1 — 전체 B'**

```
SendMessage → blog-writer-<NNN>
  mode: B'
  범위: 전체(팩트체크 반영 + SEO + 관련글 실제 URL 치환 + frontmatter)
  factcheck: work/posts/<NNN-slug>/factcheck.md
  SEO 스킬: ${CLAUDE_PLUGIN_ROOT}/skills/blog-naver-seo/SKILL.md
  추가 입력: knowledge/naver-seo-checklist.md, work/own-posts.json,
            knowledge/learned-preferences.md (있으면 — 범주 제목·톤·구조·분량·내용·SEO 규칙)
  질문 답: <있으면 담당자 답 원문, 없으면 생략>
  출력: work/posts/<NNN-slug>/draft-v2.md, work/posts/<NNN-slug>/seo.md
  반환에 "학습 규칙 적용: L-…"(없으면 "없음") 한 줄
```

**(b) FAIL+출처필요 = 0 — B' 생략 규칙**: 메인이 먼저 복사한 뒤 범위를 좁혀 재개한다.

```bash
cp work/posts/<NNN-slug>/draft.md work/posts/<NNN-slug>/draft-v2.md
```

```
SendMessage → blog-writer-<NNN>
  mode: B'
  범위: SEO·링크 치환·frontmatter만 (FAIL+출처필요 0건 — draft-v2.md는 메인이 draft.md에서 복사해 둠.
        팩트 반영은 건너뛰고 factcheck.md의 ## 시점 표기 권고만 반영)
  factcheck: work/posts/<NNN-slug>/factcheck.md
  SEO 스킬: ${CLAUDE_PLUGIN_ROOT}/skills/blog-naver-seo/SKILL.md
  추가 입력: knowledge/naver-seo-checklist.md, work/own-posts.json,
            knowledge/learned-preferences.md (있으면)
  질문 답: <있으면>
  출력: work/posts/<NNN-slug>/draft-v2.md, work/posts/<NNN-slug>/seo.md
  반환에 "학습 규칙 적용: L-…"(없으면 "없음") 한 줄
```

반환 뒤 `ls P/draft-v2.md P/seo.md`. 반환의 `학습 규칙 적용:` 줄을 기록해 둔다. 반환의 **"사실 문장 변경"** 줄을 기억한다(`없음`이 아니면 미검증 사실 변경 — 게이트 2에서 보여 주고 수정 루프의 C r2로 검토). `## 질문`·`seo.md` "메인에 전달"은 질문 처리대로.

## Step 2. lint (메인)

```bash
python3 scripts/lint_post.py work/posts/<NNN-slug>/draft-v2.md --stage draft --json > work/posts/<NNN-slug>/lint.json; echo "exit=$?"
```

- exit 0 → 게이트 2로.
- exit 1(FAIL) → B' 재개 **1회**(디스패치 +1):
  ```
  SendMessage → blog-writer-<NNN>
    mode: B'
    범위: lint FAIL 항목만
    lint: work/posts/<NNN-slug>/lint.json
    출력: work/posts/<NNN-slug>/draft-v2.md
  ```
  재개 뒤 같은 lint를 다시 돌려도 FAIL이면 멈추고 FAIL id·값을 보고한다.
- exit 2 → 사용 오류 또는 설정 누락(비어 있는 `business-profile.md` 행·`.env`의 `NAVER_BLOG_ID` — stderr 메시지에 이름이 나온다). 설정 누락이면 그 메시지를 보여 주고 채우라고 안내한 뒤 중단, 그 밖은 중단·보고.

lint.json 형식: `{"stage", "pass", "checks": [{"id","value","rule","result","detail"}], "stats"}`. draft 단계에서 보는 id: `forbidden`·`chars`·`h2_count`·`images`·`sources`·`placeholder_sources`·`tone`(해요체 종결 0건)·`source_format`(`(출처: URL)` 단독 괄호만)·`title_region`(frontmatter `variation.title_region`이 고객 지역이고 title에 포함 — draft-v2.md는 B'에서 frontmatter가 생기므로 여기서 검사됨)·`variation`·`learned_avoid`(`knowledge/learned-preferences.md` `## 피할 표현`에 든 표현 — 결과는 항상 **WARN**이고 `pass`·exit에 영향 없음. B' 재개 사유가 아니며 게이트 2에서 담당자에게 보여 주기만 한다. 파일이 없으면 SKIP).

## ● 게이트 2 — 초안 피드백

보여 주기 직전에 담당자에게 보여 줄 판을 남긴다(아래 "직접 수정 비교"의 기준):

```bash
cp work/posts/<NNN-slug>/draft-v2.md work/posts/<NNN-slug>/draft-v2.shown.md
```

안내 문구에 한 줄을 넣는다: "draft-v2.md를 메모장(macOS는 텍스트 편집기)으로 직접 고쳐 저장한 뒤 답해도 됩니다 — 고친 부분도 다음 글에 반영하도록 배웁니다: <draft-v2.md 절대경로>"(`os: windows`면 `C:\…` 경로도 함께).

담당자에게 보여 준다: `P/draft-v2.md` 절대경로(`os: windows`면 `C:\…` 형식도)와 본문 전체, 제목 A안(frontmatter `title`)·B안(`<!-- 제목 B안: … -->`)과 **제목 지역**(`gates.md ## 선택`의 `제목 지역:` = frontmatter `variation.title_region`), factcheck 요약 줄과 `## 시점 표기 권고`, lint.json의 `pass`·chars·h2_count·images·sources·tone·title_region(`learned_avoid`가 WARN이면 걸린 표현과 detail도 — "앞으로 피하기로 한 표현이 남아 있습니다" 한 줄, 수정 요청 여부는 담당자가 정함), `seo.md`의 표(요약), writer가 보고한 "사실 문장 변경"과 "학습 규칙 적용".

**AskUserQuestion**:
1. 제목 — `A안: <제목>` / `B안: <제목>`(기타 입력으로 직접 쓴 제목도 받는다. 핵심 키워드와 제목 지역 `<지역>`이 그대로 들어 있어야 한다고 함께 안내).
2. 톤·길이·내용 — `그대로 진행` / `더 짧고 간결하게` / `문장을 더 짧게`(말투는 합니다체 고정 — 해요체로 바꾸는 요청은 받지 않는다. 구체적 수정 요청은 기타 입력 원문 그대로 받는다).

**직접 입력 제목에 제목 지역명이 없으면** 1회만 되묻는다(AskUserQuestion): `지역명 넣어 다시 입력`(새 제목을 기타 입력으로 받는다) / `이대로 진행`. `이대로 진행`이면 그 제목 그대로 B' 재개를 보내고, 수정 루프 3의 lint에서 `title_region`이 FAIL하면 B' 재개 범위를 **"제목 지역 보완"**(채택 제목에 제목 지역명만 더함, 디스패치 +1)으로 처리한다. 다시 입력한 제목에도 지역명이 없으면 더 묻지 않고 `이대로 진행`과 같이 처리한다.

**직접 수정 비교** (게이트 2 답 직후 · 수정 루프 4 답 직후 · Step 4 빌드 직전 — 세 곳에서 같은 절차):

```bash
P=work/posts/<NNN-slug>
if [ ! -f "$P/draft-v2.shown.md" ]; then echo "shown: 없음(비교 건너뜀)"
elif cmp -s "$P/draft-v2.shown.md" "$P/draft-v2.md"; then echo "직접 수정: 없음"
else echo "직접 수정: 있음"; python3 scripts/diff_published.py "$P/draft-v2.shown.md" "$P/draft-v2.md" --json; echo "diff exit=$?"; fi
```

- `직접 수정: 없음`·`shown: 없음` → 아무것도 하지 않는다(`- 직접 수정: 없음`).
- `diff exit=2` → 비교만 건너뛰고(글 작업은 계속) 종료 보고에 "직접 수정 비교 실패: <출력 첫 줄>".
- `직접 수정: 있음` →
  1. `summary`(마무리 블록 줄은 초안에 원래 없으므로 빼고)와 주요 변경(`title`·`headings.renamed/added/removed`·`paragraphs.changed` 상위 5개 전 → 후, `removed`·`added` 상위 5개)을 보여 준다.
  2. **패턴 제안**: 바뀐 점 가운데 다음 글에도 해당할 것만 메인이 **일반화 문장** 1~4개로 만든다(오타 한 글자·특정 수치 정정처럼 이 글에만 해당하는 것은 빼고, 슬롯 번호·이 글의 주제어도 뺀다 — 예: 도입 둘째 문장을 지움 → "도입은 2문장 안쪽으로 짧게"). 범주는 게이트 2 "피드백 기록" 2번 기준.
  3. AskUserQuestion multiSelect "직접 고치신 부분 중 앞으로도 이렇게 쓸까요?" — 옵션 = 그 문장들 + `없음`. **게이트 2(또는 수정 루프 4)의 범위 질문과 같은 호출에 합친다**(한 호출에 질문 최대 4개, 넘으면 나눠서). 제안이 0개면 묻지 않는다.
  4. 고른 것만 기록한다(안 고른 변경은 기록하지 않는다 — 이번 글에는 이미 들어 있다). 단계는 세 곳 모두 `게이트2`:
     ```bash
     FID=$(python3 scripts/feedback_log.py add --post <NNN-slug> --stage 게이트2 --category <범주> --scope "앞으로 계속" --text='초안 직접 수정: <일반화 문장>' | tr -d '\r'); echo "$FID"
     ```
  5. **사실 확인**: `paragraphs.changed`의 after·`paragraphs.added`·`title.after`에 숫자·`제n조`·`(출처:`가 있으면 그 문장을 **미검증 사실 변경**으로 본다 — 게이트 2·수정 루프 단계면 수정 루프 2의 C r2(예산 안에서) 대상에 넣고, Step 4 직전이면 운영 원칙 "미검증 사실 변경"대로(r3 없이 바뀐 문장을 보여 주고 `이대로 진행` / `여기서 중단`).
  6. **lint 다시**: Step 2 lint 명령(`--stage draft`, `lint.json` 갱신)을 draft-v2.md에 다시 돌린다. FAIL(`tone`·`source_format`·`title_region`·`forbidden`·`chars` 등)이면 FAIL id·detail을 보여 주고 AskUserQuestion `B'로 고치기` / `내가 다시 고칠게요`(게이트 2에서 수정 요청도 있어 수정 루프 1의 B' 재개가 어차피 나가면 묻지 않고 그 재개 메시지에 `lint: work/posts/<NNN-slug>/lint.json`의 FAIL 항목을 함께 넣는다 — 디스패치 추가 없음). `B'로 고치기` → Step 2의 lint FAIL 재개(디스패치 +1 — Step 4 직전이면 Step 4의 B' 1회에 포함)에 `직접 수정: 있음 — draft-v2.md는 담당자가 고친 판. 담당자 수정은 되돌리지 말고 FAIL 항목만` 줄을 넣는다. `내가 다시 고칠게요` → 멈추고 보고한다(학습 정리 → 종료 보고, "고친 뒤 `/naver-blog-autopilot:blog-run resume <NNN>`" — Step 4 직전이면 이어서 같은 resume로 다시 빌드).
  7. 끝나면 `cp "$P/draft-v2.md" "$P/draft-v2.shown.md"`로 기준을 갱신한다(다음 비교가 같은 수정을 다시 세지 않게). 기록한 id는 `## 초안피드백`의 `- 직접 수정: 있음(F-…)` 줄에 적는다 — Step 4 직전에 생기면 `## 초안피드백`을 이전 줄을 모두 옮겨 적은 새 절로 한 번 더 append한다(마지막 절이 유효).
- 업로드 뒤 `/naver-blog-autopilot:blog-feedback`의 발행본 비교는 `final.md`(업로드본) 기준이라, 여기서 배운 초안 직접 수정은 final.md에 이미 들어 있어 **두 번 학습되지 않는다**.

**피드백 기록(학습용)** — 2번 답이 `그대로 진행`이고 제목이 A안·B안이면 이 단계는 건너뛴다(기록하지 않는다 — 위 직접 수정 비교는 따로 한다). 그 밖에는:
1. **요청 목록**을 만든다. 2번 답의 옵션(`더 짧고 간결하게`·`문장을 더 짧게`)은 그 문구가 요청 1개, 기타 입력 원문은 1개(원문이 줄·번호·"그리고"로 서로 다른 요청을 나열했으면 나눠서 각각 — 문장은 원문 그대로 자른다). 제목을 A/B 대신 직접 썼으면(다시 입력했으면 마지막 것) `제목 직접 입력 — A안 "<A안>" 대신 "<채택 제목>"`도 1개.
2. **범주**는 메인이 요청 문장으로 하나 고른다(묻지 않는다): 제목 직접 입력 = `제목` · 말투·문장 길이·어미 = `톤` · 글 전체·절 길이 = `분량` · 절 순서·소제목·목차·FAQ 구성 = `구조` · 넣을/뺄 내용·예시 = `내용` · 수치·일정·조항이 틀림 = `사실` · 키워드·태그 = `SEO` · 그 밖 = `기타`. 예: `더 짧고 간결하게` → 분량, `문장을 더 짧게` → 톤.
3. **범위를 묻는다** — AskUserQuestion 한 번, 요청마다 질문 1개(한 호출에 최대 4개, 넘으면 나눠서): 질문 "이 요청을 앞으로 쓰는 모든 글에도 적용할까요? — "<요청 원문>"", 옵션 `앞으로 계속`(글이 끝날 때 바로 규칙이 됩니다 — 다시 묻지 않습니다) / `이번 글만`.
4. 요청마다 기록하고 출력된 id(`F-0003` 형식)를 모은다. 원문은 `--text='<원문>'`처럼 `=`로 붙이고 작은따옴표로 감싼다 — 원문 안의 `'`는 `'\''`로 바꿔 넣는다(셸이 `$`·`"`·`` ` ``를 해석하지 않고, 원문이 `-`로 시작해도 옵션으로 읽히지 않게(exit 2 방지)):
   ```bash
   FID=$(python3 scripts/feedback_log.py add --post <NNN-slug> --stage 게이트2 --category <범주> --scope "<앞으로 계속|이번 글만>" --text='<요청 원문>' | tr -d '\r'); echo "$FID"
   ```
   exit가 0이 아니거나 id가 안 나오면 기록만 건너뛰고(글 작업은 계속) 종료 보고에 "피드백 기록 실패: <출력 첫 줄>"을 남긴다.

`P/gates.md`에 append:

```markdown
## 초안피드백
- 일시: …
- 제목: A안 | B안 | 직접 — <채택 제목 원문>
- 제목 지역: <지역> — 포함 | 미포함(이대로 진행)
- 톤: <답 원문 또는 "그대로">
- 길이: <답 원문 또는 "그대로">
- 수정 요청 원문: <기타 입력 원문, 없으면 "없음">
- 피드백 기록: <F-0003(앞으로 계속), F-0004(이번 글만) — 기록하지 않았으면 "없음">
- 직접 수정: <있음(F-0005, F-0006) | 있음(기록 없음) | 없음>
- 질문 답: <앞서 받은 답이 있으면 그대로 옮김>
```

- **A안 + 그대로 진행**이고 미검증 사실 변경(직접 수정 비교 5 포함)이 없으면 → 디스패치 없이 Step 3(직접 수정만 있었으면 그 판 그대로 — lint는 비교 6에서 이미 봤다).
- 그 밖(B안·직접 제목·수정 요청, 또는 앞선 B'의 사실 문장 변경이나 직접 수정의 사실 변경이 있음) → **수정 루프 1회**:
  1. 제목·톤·길이·수정 요청 중 바꿀 것이 있을 때만 B' 재개(디스패치 +1):
     ```
     SendMessage → blog-writer-<NNN>
       mode: B'
       범위: 게이트 2 피드백 — work/posts/<NNN-slug>/gates.md 의 마지막 ## 초안피드백
       학습 규칙: knowledge/learned-preferences.md (있으면 — 피드백을 반영해도 적용 중 규칙은 유지, 잠긴 규칙 우선)
       직접 수정: <있음 — draft-v2.md는 담당자가 고친 판. 그 판을 기준으로 요청만 반영하고 담당자 수정은 되돌리지 말 것 | 없음>
       출력: work/posts/<NNN-slug>/draft-v2.md, work/posts/<NNN-slug>/seo.md
       반환에 "학습 규칙 적용: L-…"(없으면 "없음") 한 줄
     ```
  2. 이번 글의 B' 반환(앞선 B'·lint 재개·1의 재개) 중 하나라도 "사실 문장 변경"이 `없음`이 아니거나, 직접 수정 비교 5에서 사실 변경이 나왔으면 C r2 발주(디스패치 +1, 새 Agent):
     ```
     Agent 도구
       subagent_type: naver-blog-autopilot:blog-fact-checker
       name: blog-fact-checker-<NNN>-r2
       prompt:
         회차: r2
         초안: work/posts/<NNN-slug>/draft-v2.md
         리서치: work/posts/<NNN-slug>/research.md
         지식: knowledge/official-sources.md, knowledge/business-profile.md
         절차 스킬: ${CLAUDE_PLUGIN_ROOT}/skills/blog-fact-check/SKILL.md
                   ${CLAUDE_PLUGIN_ROOT}/skills/blog-fact-check/references/claim-types.md
         출력: work/posts/<NNN-slug>/factcheck-r2.md
     ```
     C와 같은 명령으로 `factcheck-r2.md` 요약 줄을 읽는다. 질문이 있으면 질문 처리. FAIL+출처필요 ≥ 1 또는 `## 시점 표기 권고`가 `없음`이 아니면 B' 재개(디스패치 +1): `mode: B'` · `범위: 팩트체크 r2 반영` · `factcheck: work/posts/<NNN-slug>/factcheck-r2.md` · `질문 답:`(있으면). 0건·권고 없음이면 재개하지 않는다.
  3. Step 2 lint를 다시 돌린다(FAIL이면 Step 2 규칙대로 B' 재개 1회. 직접 제목 `이대로 진행`으로 `title_region`이 FAIL했으면 그 재개의 범위는 `제목 지역 보완 — 채택 제목에 <제목 지역>만 넣을 것` + 다른 FAIL id).
  4. 보여 주기 직전 `cp P/draft-v2.md P/draft-v2.shown.md`로 기준을 갱신하고(이 판에도 직접 고쳐도 된다는 안내 한 줄), 바뀐 부분(제목·수정 요청 반영 결과·r2 요약)을 보여 주고 AskUserQuestion `이미지 단계로 진행` / `여기서 중단`. 답 직후 위 **직접 수정 비교**를 한 번 더 한다(사실 변경이 나오면 r2를 이미 썼으면 운영 원칙 "미검증 사실 변경"대로). 이 루프는 **한 번만** 돈다 — 추가 수정 요청이면(기타 입력) 그 요청도 위 "피드백 기록"대로 범위를 묻고 `--stage 게이트2`로 기록한 뒤 멈추고 보고한다(담당자가 직접 고치거나 다음 실행에서 이어 감 — 발행 후 고쳤다면 `/naver-blog-autopilot:blog-feedback`).
- 위 어느 디스패치든 8회째가 되면 하지 않고 멈춘다(예산, 최대 7회).

## Step 3. 이미지 (메인)

**Skill 도구로** `naver-blog-autopilot:blog-image-director`를 실행해 메인이 직접 수행한다(입력 `work/posts/<NNN-slug>/draft-v2.md`·`gates.md`, 있으면 `knowledge/learned-preferences.md` — 스킬이 `범주=이미지·표지` 규칙을 프롬프트·표지 줄바꿈·배경 선택에 반영하고 요약에 `적용 규칙: L-…`을 적는다. 이 줄을 종료 보고용으로 기록해 둔다). 산출: `P/images/image-plan.md`(열: 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수), `P/images/NN-<slug>.png`(ai 슬롯), 표지 `P/images/00-bg.png`(배경)·`P/images/00-cover.png`(합성), 게이트 3용 요약.

- **표지 `00` 행**: 스킬이 image-plan.md 맨 윗줄에 `| 00 | 표지(대표) | 표지 | cover | <글자 없는 배경 프롬프트> | 제목: <frontmatter title 그대로>; 줄바꿈: 줄1; 줄2 | images/00-cover.png | <검수> |`를 넣고, 배경 `uv run --with google-genai --with pillow scripts/gen_image.py …`(cover 행 → `images/00-bg.png`) → 합성 `uv run --with pillow scripts/make_cover.py --bg <P>/images/00-bg.png --title "줄1|줄2" [--sub …] --out <P>/images/00-cover.png`까지 만든다. `00`은 draft-v2.md 슬롯이 아니다 — 슬롯 수 대조·확정 이미지 수에서 빠진다. `00` 행 `파일` 칸은 항상 `images/00-cover.png`이고, 표지가 만들어졌는지는 그 파일이 있는지로 본다.
- **키 없음 모드**(Step 0 `IMAGE_KEY: MISSING`) 또는 요약에 **"Gate: 이미지 키 대기"**가 있으면: 생성은 하지 않는다(스킬 1~5단계로 image-plan.md를 쓰고 photo 후보만 고른다). image-plan.md에서 `유형`이 `ai`인 행의 `파일`을 `보류`, `검수`를 `키 없음`으로 적는다. **표지**는 `photos/`의 실사진 1장을 배경으로 `make_cover.py`만 돌려 만들 수 있다(비용 0): `uv run --with pillow scripts/make_cover.py --bg photos/<파일> --title "줄1|줄2" [--sub …] --out <P>/images/00-cover.png` → `00` 행 `검수`를 `실사진 배경 photos/<파일>`로. 맞는 실사진이 없으면 `00` 행 `검수`를 `키 없음(표지 보류)`로 두고 `00-cover.png`는 만들지 않는다(아래 확정 확인에서 멈춘다). 담당자가 그 자리에서 키를 채웠다고 하면 `uv run --with google-genai --with pillow scripts/gen_image.py work/posts/<NNN-slug>/images/image-plan.md`를 실행해 보류를 풀어도 된다(cover 행 배경 `00-bg.png`도 함께 생성되므로 이어서 `make_cover.py`로 표지를 합성). 그 뒤 생성된 각 이미지를 Read로 열어 blog-image-director 스킬 7단계 기준(글자·얼굴·중복·캡션·로고)으로 검수하고 image-plan.md `검수` 열을 갱신한 다음 게이트 3으로 간다. 이 생성도 스킬의 한도(ai 슬롯 수 × 3)에 포함한다.
- **제공자 확인**: `gen_image.py` 시작 줄 `키: … · 제공자: … · 모델: …`이 Step 0의 `IMAGE_KEY: OK (<provider>, …)`와 같은 제공자인지 본다(다르면 생성을 멈추고 `.env`의 `IMAGE_PROVIDER`를 확인하라고 보고). 시작 줄은 그대로 옮기지 않는다 — 보고·`gates.md`에는 `제공자` 값만 쓰고 키 파일 경로·모델은 쓰지 않는다. 생성이 결제·권한 문제로 실패하면 제공자별로 안내한다 — Gemini `429`: 결제(Billing)가 없는 키(무료 키는 기다려도 안 풀림), OpenAI `401`/`403`: 키 오류 또는 조직 인증(Verify Organization) 필요, 결제 수단 미등록, `429`가 insufficient_quota·billing이면 결제·한도 문제(남은 슬롯 중단 — 다른 429·5xx는 스크립트가 최대 3회 재시도 후 그 슬롯만 실패) — 키 확인(`check_image_key.py`)이 통과해도 생성에서 403이 나면 조직 인증이 필요한 것이다. 비용은 Gemini 1장 약 $0.04(추정치) / OpenAI는 요금 페이지 확인.
- `파일` 경로 규칙: ai = **글 폴더 기준** `images/NN-<slug>.png`, photo = **작업 폴더 기준** `photos/<파일>`.

## ● 게이트 3 — 이미지 승인 (슬롯별)

슬롯마다 위치·유형·캡션·파일(ai는 절대경로를 보여 줘 담당자가 열어 볼 수 있게 — `os: windows`면 `cygpath -w`로 바꾼 `C:\…` 경로도 함께, photo는 후보 목록)·검수 결과를 보여 준다. **첫 슬롯은 항상 `00 표지`**(`00-cover.png` 절대경로·표지 제목·줄바꿈·배경 출처).
**AskUserQuestion**으로 슬롯별로 묻는다(한 호출에 최대 4슬롯, 넘으면 나눠서):
- `00 표지`: `승인` / `재생성 — 줄바꿈·배지 문구`(바꿀 줄바꿈·`--sub` 문구는 기타 입력, `make_cover.py`만 다시 — 비용 0) / `재생성 — 배경`(바꿀 장면은 기타 입력, `gen_image.py --only 00` → `make_cover.py`; 키 없음 모드에서는 빼고 묻는다) / `실사진 배경으로`(파일명은 기타 입력, `make_cover.py --bg photos/<파일>`만)
- ai 슬롯: `승인` / `재생성`(바꿀 점은 기타 입력) / `실사진으로 교체`(파일명은 기타 입력) / `제거`
- photo 슬롯: 후보 파일 최대 3개(`photos/…`) / `제거`(다른 파일·AI 전환은 기타 입력)
- `보류` 슬롯(키 없음): `보류 유지`(final.md에서 빠지고 나중에 Step 3 재실행) / `제거` / `실사진으로 교체`(파일명은 기타 입력)

`P/gates.md`에 append:

```markdown
## 이미지승인
- 일시: …
- 00: 승인 — images/00-cover.png (배경 images/00-bg.png)
- 01: 승인 — images/01-summary.png
- 02: 후보 선택 — photos/매장-01.jpg
- 03: 재생성 — 요청: <원문>
- 04: 제거
- 피드백 기록: F-0005(이번 글만), F-0006(이번 글만)
```

**피드백 자동 기록(묻지 않음)** — 답을 받을 때마다, 아래 반영 전에 요청 하나당 한 행을 `--stage 게이트3 --scope "이번 글만"`으로 기록하고 id를 `## 이미지승인`의 `- 피드백 기록:` 줄에 모은다(없으면 `없음`). 범주는 `00` 표지 슬롯이면 `표지`, 그 밖은 `이미지`. 원문 따옴표 처리는 게이트 2와 같다:

| 답 | `--text`(원문) |
|---|---|
| `재생성`(ai)·`재생성 — 배경`·`재생성 — 줄바꿈·배지 문구` | `<NN> 재생성: <기타 입력 원문>` (원문이 없으면 `<NN> 재생성(사유 없음)`) |
| `실사진으로 교체`·`실사진 배경으로` | `<NN> 실사진으로 교체: photos/<파일>` + 기타 입력에 이유가 있으면 ` — <원문>` |
| `제거` | `<NN> 제거(<그 행 캡션(alt)>)` |

`승인`·후보 선택·`보류 유지`는 기록하지 않는다.

```bash
FID=$(python3 scripts/feedback_log.py add --post <NNN-slug> --stage 게이트3 --category <이미지|표지> --scope "이번 글만" --text='<위 표의 원문>' | tr -d '\r'); echo "$FID"
```

반영(메인이 직접, **디스패치 아님**):
- 후보 선택·실사진 교체 → `image-plan.md` 그 행의 `유형`을 `photo`, `파일`을 `photos/<파일>`, `검수`를 `담당자 지정`으로 고친다(파일이 실제로 있는지 `ls`).
- 재생성 → 요청대로 그 행의 프롬프트를 고친 뒤
  ```bash
  uv run --with google-genai --with pillow scripts/gen_image.py work/posts/<NNN-slug>/images/image-plan.md --only NN
  ```
  재생성도 과금된다(Gemini 1장 약 $0.04 추정 / OpenAI는 요금 페이지 확인). 새 이미지를 Read로 열어 검수하고(스킬 7단계 기준) `검수` 열을 갱신한 뒤 그 슬롯만 다시 묻는다. 슬롯당 재생성 최대 2회, 글 전체 생성 호출 ai 슬롯 수 × 3 이내(스킬 규칙). 넘으면 `제거`·실사진 중에서 고르게 한다.
- 표지(`00`) 재생성·실사진 배경 → `00` 행 `캡션(alt)`의 `줄바꿈:`(또는 프롬프트)을 요청대로 고친 뒤
  ```bash
  # 배경을 바꿀 때만(키 있음): 배경 재생성 — 생성 한도에 포함, 과금(Gemini 1장 약 $0.04 추정 / OpenAI는 요금 페이지)
  uv run --with google-genai --with pillow scripts/gen_image.py work/posts/<NNN-slug>/images/image-plan.md --only 00
  # 합성(항상): --bg 는 images/00-bg.png 또는 photos/<파일>, --title 은 줄바꿈: 값을 | 로 이은 것
  uv run --with pillow scripts/make_cover.py --bg <배경> --title "줄1|줄2" [--sub …] --out work/posts/<NNN-slug>/images/00-cover.png
  ```
  `00-cover.png`를 Read로 열어 검수(제목 잘림·오타·배경 글자 없음·안전 영역)하고 `검수` 열을 갱신한 뒤 표지만 다시 묻는다. 표지 재생성은 줄바꿈·배경 합쳐 최대 2회. `00` 행에는 `제거`가 없다(대표이미지는 필수).
- 제거 → 그 행의 `파일`을 `제거`, `검수`를 `제거(담당자)`로 고친다. 보류 유지 → 그대로 둔다(`파일` = `보류`).

**게이트 3 끝 — 앞으로도 지킬 이미지 요청** (모든 슬롯이 끝난 뒤 한 번만): 이번 게이트 3에서 기록한 행 중 재생성·교체 요청(`제거` 제외)이 1개 이상이면 AskUserQuestion 한 번 — 질문 "이미지 요청 중 앞으로도 지킬 것이 있나요?", multiSelect, 옵션 = 그 요청들을 **메인이 일반화한 문장**(슬롯 번호·파일명·이 글에만 있는 장면을 뺀, 다음 글에도 쓸 수 있는 규칙 문장 — 예: `06 재생성: 스티커 없애기` → `제품·소품에 스티커·로고가 보이지 않게 만들기`, `00 실사진으로 교체: photos/매장-03.jpg` → `표지 배경은 AI보다 업체 실사진 우선`. 옵션 설명에 원래 id·원문을 붙인다, 최대 4개 — 넘으면 최근 4개를 보여 주고 나머지는 기타 입력으로 id를 받는다) + `없음`. 기타 입력으로 문장을 고쳐 주면 그 문장을 쓴다. 고른 요청마다, 담당자에게 보여 준 그 일반화 문장으로 기록한다:

```bash
NEW=$(python3 scripts/feedback_log.py add --post <NNN-slug> --stage 게이트3 --category <원래 행의 범주> --scope "앞으로 계속" --text='<담당자에게 보여 준 일반화 문장>' | tr -d '\r'); echo "$NEW"
python3 scripts/feedback_log.py mark <원래 id> "반영 안 함: 앞으로 계속으로 다시 기록" | tr -d '\r'
```

`없음`이면 아무것도 하지 않는다. 재생성·교체가 0개면 묻지 않는다.

모든 슬롯이 승인·확정·제거·보류 유지로 끝나면 마지막 결과로 `## 이미지승인`을 한 번 더 append한다(재질문이 있었거나 위에서 `앞으로 계속` 행이 생긴 경우 — `- 피드백 기록:` 줄에 새 id를 `F-0007(앞으로 계속)`처럼 더해 적는다).

**확정 이미지 수 확인**(Step 4로 가기 전, 매번):

```bash
python3 - work/posts/<NNN-slug> <<'PY'
import os, re, sys
sys.path.insert(0, "scripts"); from gen_image import parse_plan
P = sys.argv[1].rstrip("/")
_, rows = parse_plan(open(f"{P}/images/image-plan.md", encoding="utf-8").read())
m = re.search(r"min_images=(\d+)", open("knowledge/design-system.md", encoding="utf-8").read())
need = int(m.group(1)) if m else 3                                            # lint 블록이 없을 때 = lint 기본값
body = [r for r in rows if r["slot"] != "00"]                                            # 00 표지는 본문 이미지 수에서 제외
ok = sum(1 for r in body if r["file"].strip("` ").startswith(("images/", "photos/")))   # 보류·제거 제외
cover = os.path.isfile(f"{P}/images/00-cover.png")
print(f"확정 이미지: {ok} / 필요 {need} · 표지 00 행: {'있음' if any(r['slot'] == '00' for r in rows) else '없음'} · 00-cover.png: {'있음' if cover else '없음'}")
PY
```

- 확정 이미지 ≥ 필요 **그리고** `00-cover.png: 있음` → Step 4.
- 표지 `00` 행이 없으면 → 스킬 5단계대로 `00` 행을 추가하고 표지를 만든 뒤 게이트 3에서 표지만 묻는다.
- 확정 이미지 < 필요, 또는 `00-cover.png: 없음`(키 없음 + 맞는 실사진 없음) → **Step 4로 가지 않고 멈춘다**(final.md를 만들지 않음). 담당자에게 "확정 이미지 n장 / 필요 m장 · 표지 있음|없음 — 키 또는 실사진 준비 후 `/naver-blog-autopilot:blog-run resume <NNN>`"이라고 알리고 종료 보고로 간다(키는 `.env`에 Gemini `GEMINI_API_KEY` — 결제 설정된 프로젝트의 키 — 또는 OpenAI `OPENAI_API_KEY` — 결제 수단·조직 인증, 실사진은 `photos/`에). image-plan.md·gates.md는 그대로 두어 `resume`이 이어받게 한다.

## Step 4. `final.md` 생성 (메인)

`scripts/build_final.py`가 `draft-v2.md` + `images/image-plan.md`로 업로드본 `final.md`를 만든다(draft-v2.md는 건드리지 않는다 — 출처·슬롯 설명이 남은 원본으로 보존). 하는 일: `![슬롯: …]()`을 등장 순서대로 image-plan `01…` 행(`00` 제외)과 맞춰 캡션 없는 `![](<절대경로>)`로(`제거`·`보류`는 줄째 삭제) · `(출처: URL)` 단독 괄호 제거 · 모든 `## ` 앞 여백(`ㅤ` 줄) · 표지 제목(`00` 행 `제목:`)과 frontmatter `title` 대조 · 마지막 `## 📞 문의 안내: <연락처>` 뒤에 업체소개 이미지 → `:::place <장소 검색어>:::` → 빈 줄 → `**#태그 …**` 마무리 블록. 변환에 실패(exit 1)하면 이전 `final.md`가 있어도 지운다(오래된 본이 업로드 단계로 넘어가지 않게). 메인은 final.md를 손으로 고치지 않는다.

**빌드 직전**: 게이트 2의 **직접 수정 비교**를 한 번 더 한다(기준 = 마지막으로 보여 준 `draft-v2.shown.md` — 게이트 3 동안 담당자가 draft-v2.md를 고쳤을 수 있다). 제목이 바뀌었으면 아래 빌더가 "표지 재생성 필요"를 낸다 → 표대로 make_cover만.

```bash
python3 scripts/build_final.py work/posts/<NNN-slug> 2>&1; echo "exit=$?"
```

- exit 0 → 출력 `final.md 작성 — 슬롯 n개(제거 a개, 보류 b개) · 출처 제거 c개 · 필러 삽입 d줄`을 기록하고 아래 lint로.
- exit 2 → 사용 오류(글 폴더·draft-v2.md 없음). 중단·보고.
- exit 1 → `final.md를 만들지 않았습니다:` 아래 사유 줄마다 처리한다(final.md는 쓰이지 않았다):

| 사유(출력 문구) | 처리 |
|---|---|
| `NN: image-plan.md에 행 없음` · `NN: 파일 칸 미확정(…)` · `NN: 파일 없음 …` · `슬롯 수 불일치: …(00 제외)` · `image-plan.md 없음`/`파싱 실패` | Step 3(게이트 3)으로 돌아가 그 슬롯을 확정한 뒤 Step 4 재실행 — 아래 "Step 4 → Step 3 1회"에 포함 |
| `표지 재생성 필요 — 표지 제목 '…' ≠ title '…'` · `표지(00) 행 캡션에 '제목:' 없음` (게이트 2·B'에서 제목이 바뀜) | `00` 행 `캡션(alt)`을 `제목: <지금 frontmatter title 그대로>; 줄바꿈: …`으로 고치고 줄바꿈을 새 제목에 맞게 다시 정한 뒤 `make_cover.py`만 재실행(Step 3 표지 명령, 비용 0) → `00-cover.png`를 Read로 검수 → Step 4 재실행. 게이트 3을 다시 열지 않으며 Step 3 되돌아가기 횟수에도 넣지 않는다(종료 보고에 "제목 변경으로 표지를 다시 만들었습니다" 한 줄) |
| `표지(00) 행 없음 — …` | Step 3에서 `00` 행 추가·표지 생성 → 게이트 3에서 표지만 묻기 → Step 4 재실행(Step 3 되돌아가기 1회에 포함) |
| `혼합 출처 괄호 — lint source_format 참고: draft-v2.md N행…` | B' 재개 1회(디스패치 +1, `범위: 출처 괄호 단독형으로 — (출처: URL)만 남기고 조항·시행일은 문장 본문으로` · 해당 행 번호) → Step 4 재실행 |
| `마지막 소제목이 '## 📞 문의…'로 시작하지 않음 …`(빌더는 `## 📞 문의` 접두로 판정) | B' 재개 1회(디스패치 +1, `범위: 📞 문의 헤딩 — '## 📞 문의 안내: <연락처>'를 초안 마지막 줄로`(연락처 = `business-profile.md` `연락처` 행)) → Step 4 재실행 |
| `frontmatter title 없음` · `frontmatter tags 없음 — …` · `draft-v2.md frontmatter 오류: …` | B' 재개 1회(디스패치 +1, `범위: frontmatter`) → Step 4 재실행 |
| `업체소개 이미지 없음: …` | **중단** — "마무리 블록을 만들 수 없습니다 — photos/business-intro.png를 넣어 주세요" 안내 후 종료 보고 |

  사유가 여러 줄이면 한 번에 모아 처리한다. 텍스트 사유(B' 재개)가 있으면 재개 전에 `python3 scripts/lint_post.py work/posts/<NNN-slug>/draft-v2.md --stage draft --json > work/posts/<NNN-slug>/lint.json`을 돌려 다른 텍스트 FAIL도 같은 재개 메시지(`lint: …/lint.json`)에 함께 넘긴다 — Step 4의 B' 재개는 빌더 사유·아래 lint FAIL을 합쳐 **글 1편당 1회**다. 재실행해도 같은 사유면 멈추고 보고한다.

final.md가 만들어지면 업로드본 lint를 돌린다:

```bash
python3 scripts/lint_post.py work/posts/<NNN-slug>/final.md --stage upload --json > work/posts/<NNN-slug>/lint.json; echo "exit=$?"
```

- **Step 4 → Step 3 되돌아가기는 글 1편당 1회**(위 빌더 사유의 슬롯 쪽과 아래 lint FAIL의 이미지 쪽 합산). 두 번째로 필요해지면 멈추고 보고한다.
- lint exit 0 → Step 5. exit 2 → 사용 오류 또는 설정 누락 — Step 2와 같이(설정 누락은 안내 후 중단, 그 밖은 중단·보고).
- lint exit 1 → FAIL id별로 처리한다(lint.json의 `checks[].result == "FAIL"`). upload 단계에서 `sources`·`seo_image_captions`는 **SKIP**이다(업로드본은 출처·캡션을 지우므로 — 대신 `sources_stripped`·`captions_empty`가 본다). `learned_avoid`는 WARN뿐이라 처리하지 않는다(게이트 2에서 이미 보여 줌).

| 갈래 | FAIL id | 처리 |
|---|---|---|
| 텍스트 | `forbidden` `chars` `h2_count` `sources` `placeholder_sources` `related_links` `title_keyword` `tags_count` `frontmatter` `variation` `h1_once` `seo_title_length` `seo_keyword_body` `seo_keyword_h2` `tone` `title_region` `source_format` | B' 재개 1회(디스패치 +1, `범위: lint FAIL 항목만` · `lint: work/posts/<NNN-slug>/lint.json` · "final.md가 아니라 draft-v2.md를 고칠 것") → Step 4 재실행(build_final.py부터). 재개로 title이 바뀌면 빌더가 "표지 재생성 필요"를 낸다 → 위 표대로 make_cover만. 그래도 FAIL이면 멈추고 보고 |
| 이미지 | `image_paths` `images` `cover_file` | Step 3/게이트 3에서 해당 슬롯(장수 부족·경로)이나 표지(`00-cover.png` 없음 → make_cover 실행)를 다시 정한 뒤 Step 4 재실행 |
| 빌더 | `sources_stripped` `captions_empty` `closing_block` `h2_spacing` | `build_final.py`가 만들어야 하는 형식이 깨진 것 = 빌더 버그. 고치거나 우회하지 말고 **중단·보고**(FAIL id·detail·글 폴더) |

## Step 5. 업로드 (메인 — 서브에이전트 금지: 로그인·2단계 인증·CAPTCHA 개입 가능)

**Skill 도구로** `naver-blog-autopilot:blog-naver-upload`를 실행해 그 절차대로 메인이 직접 수행한다. 출력은 stdout·stderr를 함께 받는다(경고 줄이 stderr에도 나온다).

`<blogId>`는 Step 0 출력의 `blogId:` 값(`.env`의 `NAVER_BLOG_ID` = `own_blog.blogId`) — 세션 확인과 업로드가 같은 블로그를 쓰게 항상 넘긴다. 실제 임시저장 전에 스크립트가 `check-session`과 `check_blog_account.py`(글쓰기 화면이 그 블로그로 열리는지)를 차례로 확인한다.

스크립트는 `lint --stage upload`(넘겨받은 `--blog-id` 기준 — lint도 이 값을 `.env`보다 우선한다) → 이중 검사(금칙어·`[[`·빈 이미지·`[출처 필요]`·`출처:`/캡션 잔존·`:::place`·`**#` 해시태그 줄) → 본문을 임시 폴더의 `body.md`로, 표지 `P/images/00-cover.png`를 그 폴더의 `images/00-cover.png`로 복사 → `naver-blog-cli create-draft-from-folder <임시 폴더> --markdown-file body.md --title --category --tags` 순으로 돈다. **from-folder는 본문이 참조하지 않는 `images/00-cover.*`를 본문 맨 앞에 캡션 없이 넣고 대표이미지로 지정한다**(노트 `0:표지`·`대표 지정`). 그래서 final.md 본문에는 표지가 없다(lint `cover_file`). 본문의 `:::place …:::`는 네이버 장소 카드가 되고, CLI가 고른 장소는 노트 `장소(…)`로 돌아온다.

1. dry-run — lint·이중 검사·frontmatter·이미지 경로·표지 존재만 확인(세션 확인·업로드 생략). title·category·tags·이미지 수·표지 경로·장소 지시문을 담당자에게 보여 준다.
   ```bash
   bash scripts/naver_upload.sh work/posts/<NNN-slug>/final.md --blog-id <blogId> --dry-run 2>&1; echo "exit=$?"
   ```
   **세션 없음 모드**(Step 0 `session: LOGIN_NEEDED`/`MISSING`/`WRONG_ACCOUNT`)면 여기서 멈춘다: dry-run 결과를 보여 주고 `/naver-blog-autopilot:blog-setup` 4단계 로그인 절차(작업 폴더에서 `login_setup.py`, "로그인 상태 유지" 체크, 사람이 직접. Windows는 PowerShell 갈래 명령 — `Scripts\python.exe`)를 안내한 뒤 "로그인 후 `/naver-blog-autopilot:blog-run resume <NNN>`으로 업로드만 이어서"라고 알리고 종료 보고로 간다. `## 업로드`와 variation-log 줄은 **쓰지 않는다**.
2. dry-run이 exit 0일 때만 실제 임시저장(따로 호출). 창이 뜨고 수 분 걸릴 수 있다고 미리 알린다.
   ```bash
   bash scripts/naver_upload.sh work/posts/<NNN-slug>/final.md --blog-id <blogId> 2>&1; echo "exit=$?"
   ```

종료 코드별 대응(dry-run도 같은 코드를 쓴다):

| exit | 의미 | 대응 |
|---|---|---|
| 0 | 임시저장 완료 | 아래 "성공 기록". 출력의 경고 줄(아래)을 함께 처리 |
| 2 | 사용 오류(경로·frontmatter) | 인자와 `final.md` frontmatter 확인 후 중단·보고 |
| 10 | `lint_post.py --stage upload` 실패 | Step 4의 lint FAIL id별 처리와 같음(텍스트 → B' 재개, 이미지 → Step 3/4, 빌더 → 중단·보고) |
| 11 | 이중 검사 실패 | lint 규칙 구멍이다. 금칙어·`[[`·`[출처 필요]` 같은 텍스트 줄 → B' 재개(draft-v2.md) 후 Step 4 재실행. `출처:` 잔존·캡션 잔존·`:::place` 없음·`**#` 없음·빈 이미지 → `build_final.py` 재실행(Step 4), 그래도 같으면 빌더 버그 — 중단·보고. 어느 쪽이든 담당자에게 한 줄 보고 |
| 12 | 이미지 문제 — 표지 `images/00-cover.png` 없음, 또는 이미지 경로가 절대경로가 아니거나 파일 없음 | 표지 없음 → Step 3의 표지 명령(`make_cover.py`, 배경이 없으면 gen_image `--only 00` 또는 실사진 배경)으로 만든 뒤 업로드 재실행. 경로 문제 → Step 4 재실행(`build_final.py`가 image-plan.md 기준 절대경로로 다시 씀) |
| 20 | 세션 없음/만료 또는 `naver-blog-cli` 없음, 계정 확인 실패 | `/naver-blog-autopilot:blog-setup` 4단계 로그인 절차 안내("로그인 상태 유지" 체크, 사람이 직접. macOS는 터미널 `…/naver-blog-cli/bin/python`, Windows는 PowerShell `& "$(uv tool dir)\naver-blog-cli\Scripts\python.exe" "$HOME\naver-blog-cli\login_setup.py"` — 둘 다 작업 폴더에서 `NAVER_STATE`를 준 뒤) → 끝났다고 하면 같은 명령 1회 재실행 |
| 21 | 로그인한 계정이 `<blogId>` 블로그에 글을 쓸 수 없음(세션은 살아 있으나 다른 계정 — 글쓰기 화면이 그 계정 블로그로 이동). 임시저장은 시도하지 않았다 | 출력의 `확인 결과:` 줄(이동한 블로그 주소)을 담당자에게 보여 주고, **`<blogId>` 블로그 계정으로** `/naver-blog-autopilot:blog-setup` 4단계 로그인을 다시 하도록 안내(사람이 직접, "로그인 상태 유지" 체크, Windows는 PowerShell 갈래 명령. 기존 `playwright-state/storage_state.json`을 그 계정 세션으로 덮어쓴다) → 끝났다고 하면 같은 명령 1회 재실행. `--blog-id`가 잘못된 경우(`.env`의 `NAVER_BLOG_ID`·`knowledge/source-blogs.json`의 `own_blog.blogId`)도 함께 확인 |
| 30 | `create-draft-from-folder` 실패 | 출력된 CLI 문구를 담당자에게 보여 준다. `넣기 전에 걸린 것`(브라우저를 열기 전 이미지 존재·10MB 검사 실패)이면 그 파일을 고친 뒤 재시도. 그 밖(에디터 변경·세션 만료)은 네이버 임시저장 글에 중복이 생겼는지 확인을 요청한 뒤 재시도는 1회까지 |
| 31 | 저장됐으나 목록에서 제목 확인 불가 | 담당자에게 "네이버 → 글쓰기 → 임시저장 글"에서 직접 확인 요청. 있으면 성공으로 기록 |

같은 오류로 재시도는 한 번까지. 반복 실패하면 멈추고 보고한다(계정 안전). `publish-draft`·`delete-draft`는 호출하지 않는다.

**성공 출력 읽기**(exit 0): `임시저장 완료 — …` 다음 줄에 `제목:`·`카테고리: … / 태그: … / 이미지: n장`, 장소 카드가 들어갔으면 `장소: <CLI가 고른 장소>`가 나온다. 경고 줄(저장은 됐으므로 exit 0):
- `경고: 카테고리/태그 설정 실패 — …` → 종료 보고에서 직접 확인 요청.
- `경고: 대표이미지 지정 실패 — 임시저장 글에서 첫 이미지를 대표로 직접 지정` → `## 업로드`에 `대표이미지: 실패(직접 지정)`, 종료 보고에서 직접 지정 요청.
- `경고: 장소 카드 확인 필요 — <값>`(CLI가 고른 장소에 업체명이 없음) → 종료 보고에 그 값과 "미리보기에서 지도 카드가 우리 업체인지 확인 — 아니면 `knowledge/business-profile.md`의 `장소 검색어`를 `<업체명> <지역>`처럼 좁히고 다음 글부터 반영"을 알린다.

**성공 기록**(메인):

1. `P/gates.md`에 append:
   ```markdown
   ## 업로드
   - 일시: …
   - 제목: <임시저장 제목>
   - 카테고리·태그: <스크립트 출력 그대로>
   - 장소: <출력의 "장소:" 값, 없으면 "없음">
   - 대표이미지: 지정됨 | 실패(직접 지정)
   - list-drafts 확인: <upload.log의 "성공 | … | list-drafts: …" 줄의 list-drafts 값, exit 31이면 "담당자 직접 확인">
   - 경고: <출력의 "경고:" 줄 전부(카테고리/태그·대표이미지·장소 카드), 없으면 "없음">
   - 로그: work/posts/<NNN-slug>/upload.log
   ```
2. `work/variation-log.md`에 한 줄 추가(`final.md` frontmatter `variation`에서 읽음, region은 `+`로 연결):
   ```bash
   python3 - work/posts/<NNN-slug> <<'PY'
   import os, re, sys, datetime
   sys.path.insert(0, "scripts"); import lint_post
   P = sys.argv[1].rstrip("/")
   fm, _, err = lint_post.parse_frontmatter(open(f"{P}/final.md", encoding="utf-8").read().splitlines())
   v = str((fm or {}).get("variation", ""))
   one = lambda k: (re.search(rf"\b{k}\s*:\s*([^,}}\[]+)", v) or [None, ""])[1].strip().strip("'\"")
   reg = re.search(r"\bregion\s*:\s*\[([^\]]*)\]", v)
   region = "+".join(x.strip().strip("'\"") for x in reg.group(1).split(",") if x.strip()) if reg else ""
   vals = [one("type"), one("structure"), one("intro"), region, one("title_region")]
   if err or not all(vals):
       sys.exit(f"variation 읽기 실패: {v!r}")
   line = " | ".join([datetime.date.today().isoformat(), "posts/" + os.path.basename(P)] + vals)
   with open("work/variation-log.md", "a", encoding="utf-8") as f:
       f.write(line + "\n")
   print(line)
   PY
   ```
   형식(7열): `YYYY-MM-DD | posts/NNN-slug | type | structure | intro | region | title_region` (예, 가상: `2025-03-14 | posts/002-자전거-정기-점검-순서 | 정보 | 절차형 | 상황 | 가나동+다라동 | 가나동`). 마지막 열은 다음 글 게이트 1의 "이번 제목 지역" 계산에 쓰인다.

## 학습 정리 (메인 — 종료 보고 직전, 매번)

업로드 성공 기록 뒤, 그리고 **멈추는 모든 종료 보고 전**(업로드를 미룬 세션 없음 모드, Step 3 뒤 이미지 부족, 게이트 2 `여기서 중단`, 디스패치 예산 초과 중단, 에러 중단·보고 포함) 종료 보고 **바로 전에** 한 번 한다. 대기 중인 피드백 수를 센다:

```bash
PEND=$(python3 scripts/feedback_log.py pending | python3 -c "import json,sys;print(len(json.load(sys.stdin)))" | tr -d '\r'); echo "pending=$PEND"
```

- `pending=0` → 건너뛴다(종료 보고의 학습 줄은 "새 규칙 0개 · 후보 0개").
- `pending` ≥ 1 → **Skill 도구로** `naver-blog-autopilot:blog-learn`을 실행해 그 절차대로 메인이 직접 수행한다(**디스패치 아님** — 예산에 넣지 않는다). 스킬이 대기 로그를 규칙으로 정리해 `knowledge/learned-preferences.md`를 갱신하고 로그를 `mark`한다. `앞으로 계속` 행은 묻지 않고 적용하고, 서로 다른 글에서 2회가 된 후보 승격·보류/삭제였던 것 재적용·기존 규칙 문장 변경만 AskUserQuestion으로 묻는다(한 번에 최대 4개). 스킬 결과의 새 규칙·후보 수를 종료 보고에 옮긴다.
- 명령이 실패하면(exit ≠ 0, 숫자가 아님) 학습 정리만 건너뛰고 종료 보고에 "학습 정리 실패: <출력 첫 줄>"을 넣는다 — 글 작업 결과에는 영향이 없다.

## ● 종료 보고

담당자에게 보고한다:
- 임시저장 제목 · 카테고리 · 태그 · 이미지 수(스크립트 출력값) · 장소(출력의 `장소:` 값)
- "대표이미지는 표지(00-cover) — 미리보기에서 첫 사진에 '대표' 표시가 있는지 확인해 주세요." (`경고: 대표이미지 지정 실패`가 있었으면 대신: "대표이미지 지정에 실패했습니다. 임시저장 글에서 첫 사진(표지)을 대표로 직접 지정해 주세요.")
- 스크립트 출력에 `경고: 카테고리/태그 설정 실패`가 있었으면 반드시: "임시저장은 됐지만 카테고리·태그가 빠졌을 수 있습니다. 임시저장 글에서 직접 확인해 주세요."
- `경고: 장소 카드 확인 필요`가 있었으면 위 "성공 출력 읽기"의 안내.
- Step 4에서 제목 변경으로 표지를 다시 만들었으면 그 한 줄.
- 안내 문구: **"네이버 앱/웹 → 글쓰기 → 임시저장 글 → 미리보기 → 발행"** (발행은 담당자가 직접)
- 보류 슬롯이 있으면(키 없음 모드): "AI 이미지 보류 n개 — 키 설정 후 `/naver-blog-autopilot:blog-run resume <NNN>`". 그리고 **이번 final.md(임시저장본)는 계획보다 이미지가 n장 적다**는 것, `.env`에 키를 넣은 뒤 `resume <NNN>`을 실행하면 Step 3(이미지)부터 보류 슬롯을 채운 final.md를 새로 만들 수 있다는 것을 함께 알린다.
- 확정 이미지 부족·표지 없음으로 Step 3 뒤에서 멈췄으면: "final.md·임시저장은 아직 없습니다. 확정 이미지 n장 / 필요 m장 · 표지 있음|없음 — 키 또는 실사진 준비 후 `/naver-blog-autopilot:blog-run resume <NNN>`" (위 임시저장 항목·발행 안내 대신)
- 세션 없음 모드로 업로드를 미뤘으면: "임시저장은 아직 안 됐습니다. 로그인 후 `/naver-blog-autopilot:blog-run resume <NNN>`" (위 임시저장 항목·발행 안내 대신)
- 학습 한 줄: "학습: 새 규칙 n개 · 후보 n개 · 이번 글에 적용된 규칙 L-…"(적용된 규칙 = writer 반환들의 `학습 규칙 적용:`, `P/seo.md` 머리의 `학습 규칙:` 줄, 이미지 요약의 `적용 규칙:`, 이번 topics 파일 머리의 `학습 규칙:` 줄 id를 합쳐 중복을 뺀 것, 없으면 "없음").
- 안내 문구(업로드까지 갔을 때): "네이버에서 직접 고친 뒤 발행했다면 `/naver-blog-autopilot:blog-feedback <NNN> <발행 글 주소>`로 알려 주세요 — 고친 부분을 다음 글부터 반영합니다". 지금 쓰이는 규칙은 `/naver-blog-autopilot:blog-feedback rules`로 볼 수 있다는 것도 함께.
- 글 폴더 경로(`os: windows`면 `C:\…` 형식도), 디스패치 `n/7`, 게이트 1에서 남긴 번호가 있으면 "`/naver-blog-autopilot:blog-run <번호>`로 이어서"

---

## resume NNN (멈춘 곳부터 이어서)

인자가 `resume NNN`이면 이 절만 수행한다. **디스패치는 하지 않는다.** 글 폴더 `P=$(ls -d work/posts/NNN-* | head -1)`에서 이어 갈 지점을 정한다.

- `P/final.md`가 있으면 → **업로드 재개**. 단 `P/images/image-plan.md`에 `파일`이 `보류`인 행이 있고 이번 preflight에서 `IMAGE_KEY: OK`이면, AskUserQuestion `보류 이미지 채우고 final.md 다시 만들기` / `지금 final.md로 업로드만` — 앞의 것이면 **이미지 재개**로 간다.
- `final.md`가 없고 `P/draft-v2.md`와 `P/gates.md`의 `## 초안피드백`이 있으면 → **이미지 재개**(Step 3부터).
- 둘 다 아니면 "이어서 할 단계가 없습니다 — `/naver-blog-autopilot:blog-run`으로 게이트 2까지 먼저 진행하세요"라고 답하고 끝.

### 이미지 재개 (Step 3 → 게이트 3 → Step 4 → Step 5)

1. Step 0의 preflight Bash를 그대로 실행하고 Step 0 표대로 판정한다: `work-folder`·`script`·`skill`·`design-system.md`·`blogId`·`profile`·`intro-image`·`font`·`uv`가 MISSING/OUTDATED(`blogId`는 MISMATCH, `profile`은 NOFILE 포함)이면 그 표의 안내 후 끝낸다. `IMAGE_KEY: CONFLICT`면 Step 0 표대로 `.env` 수정 안내 후 끝낸다. `IMAGE_KEY: MISSING`이면 키 없음 모드, `session`이 OK가 아니면 세션 없음 모드로 계속한다. `blogId`·`photos:`·`min_images:`를 기억한다.
2. Step 3을 수행한다. `P/images/image-plan.md`가 이미 있으면 새로 쓰지 않고 그 계획을 이어 쓴다: 키가 있으면 `파일`이 `보류`인 ai 슬롯만 `uv run --with google-genai --with pillow scripts/gen_image.py work/posts/<NNN-slug>/images/image-plan.md --only <보류 슬롯 번호(쉼표)>`로 생성하고(과금 — Gemini 1장 약 $0.04 추정 / OpenAI는 요금 페이지 확인) Step 3의 검수(스킬 7단계 기준·한도)·제공자 확인을 따른다. 실사진을 준비했으면 게이트 3에서 그 슬롯을 `실사진으로 교체`로 고르게 한다.
   **표지(00) 보류 처리**: `00` 행이 없으면(이전 버전 계획) 스킬 5단계대로 맨 윗줄에 추가한다. `P/images/00-cover.png`가 없으면(키 없음 `표지 보류`) — 키가 있으면 `--only` 목록에 `00`을 넣어 배경 `00-bg.png`를 만든 뒤 `make_cover.py`로 합성하고, 키가 없으면 `photos/` 실사진 배경으로 `make_cover.py`만 돌린다(Step 3 표지 명령). 이미 있더라도 `00` 행 `제목:`이 지금 frontmatter `title`과 다르면 `make_cover.py`만 다시 돌린다. 게이트 3의 첫 슬롯은 표지다.
3. 게이트 3 → 확정 이미지 수 확인(여전히 부족하거나 표지가 없으면 다시 멈추고 같은 `resume` 안내) → Step 4(`build_final.py` → `lint --stage upload`) → Step 5 → 종료 보고. Step 4·5에서 B' 재개가 필요해지면(빌더 텍스트 사유, upload lint 텍스트 FAIL, exit 10·11) 디스패치하지 않고 실패 항목을 보고한 뒤 "`/naver-blog-autopilot:blog-run`(전체 워크플로우)으로 고친 뒤 다시 `resume`"이라고 안내하고 끝낸다.

### 업로드 재개 (Step 5만 — 세션이 없어 업로드를 미뤘을 때)

1. Step 0의 preflight Bash를 그대로 실행하고 Step 0 표대로 판정한다: `work-folder: MISSING`·`script: MISSING`/`OUTDATED`·`skill: MISSING`·`blogId: MISSING`/`MISMATCH`·`profile: MISSING`/`NOFILE`이면 그 표의 안내 후 끝낸다. `blogId`를 기억한다. `session: OK`가 아니면(`WRONG_ACCOUNT` 포함) 로그인 안내 후 끝낸다(`IMAGE_KEY`·`design-system.md`·`intro-image`·`font`·`uv`는 업로드만 할 때는 무관 — 무시. final.md는 이미 만들어져 있다. 단 위의 보류 이미지 질문에는 `IMAGE_KEY` 결과를 쓴다).
2. `gates.md`에 `## 업로드`가 이미 있으면 "이미 임시저장했습니다(<일시>)"라고 알리고, 다시 올릴지 AskUserQuestion `다시 올리기` / `그만두기`(중복 임시저장 주의).
3. `python3 scripts/lint_post.py <P>/final.md --stage upload --json > <P>/lint.json` — exit 2(설정 누락 — 비어 있는 `business-profile.md` 행·`.env`의 `NAVER_BLOG_ID`)면 stderr 메시지를 그대로 보여 주고 채우라고 안내한 뒤 끝낸다. exit 1이면 FAIL id를 보고하고 끝낸다(텍스트 수정이 필요하면 이 명령이 아니라 전체 워크플로우로. 출처·캡션이 남아 있고 마무리 블록·소제목 여백·표지가 없는 이전 형식 final.md는 `sources_stripped`·`captions_empty`·`closing_block`·`h2_spacing`·`cover_file`에서 FAIL한다 — 이때는 "이전 형식 final.md입니다 — `resume`으로는 올릴 수 없습니다"라고 알린다).
4. Step 5의 dry-run → 실제 임시저장(`--blog-id <blogId>`) → exit code 표대로 대응 → 성공 기록(`## 업로드` + variation-log 1줄) → 종료 보고.
   단 `resume`에서는 **디스패치하지 않는다**: exit 10(lint 실패)·11(이중 검사 실패)이 나오면 B' 재개(디스패치)가 필요하므로 출력된 실패 항목을 보고하고 "`/naver-blog-autopilot:blog-run`(전체 워크플로우)으로 고친 뒤 다시 `resume`"이라고 안내하고 끝낸다. exit 12(표지 없음·이미지 경로)도 Step 3/4가 필요하므로 같은 방식으로 안내하고 끝낸다.

---

## report NNN (상태 요약만)

인자가 `report NNN`이면 이 절만 수행한다. 파일을 쓰거나 고치지 않고, 디스패치·업로드·preflight를 하지 않는다.

```bash
P=$(ls -d work/posts/NNN-* 2>/dev/null | head -1); echo "P=${P:-없음}"
[ -n "$P" ] && ls -la "$P" "$P/images" 2>/dev/null
[ -n "$P" ] && grep -n '^## \|^- ' "$P/gates.md" 2>/dev/null
[ -n "$P" ] && [ -f "$P/lint.json" ] && python3 -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));print('lint', d['stage'], 'pass=', d['pass']);[print(' FAIL', c['id'], c['value'], c['detail']) for c in d['checks'] if c['result']=='FAIL']" "$P/lint.json"
[ -n "$P" ] && grep -m1 '^요약:' "$P"/factcheck*.md 2>/dev/null
[ -n "$P" ] && tail -n 5 "$P/upload.log" 2>/dev/null
```

글 폴더가 없으면 "work/posts/NNN-* 글이 없습니다"라고만 답한다. 있으면 표로 요약한다: 단계(선택 · 초안(draft.md) · 팩트체크(요약 줄) · draft-v2 · 게이트 2 · 이미지(image-plan.md·표지 `00-cover.png`·승인) · final.md · lint(stage·pass·FAIL id — final.md 검사는 `upload` 단계여야 한다) · 업로드(upload.log 마지막 결과 — `장소=` 값 포함)) | 상태 | 근거 파일. 마지막에 "다음 할 일" 한 줄.
