---
description: 설치한 사람의 블로그(업체·전문가·개인·브랜드)에 맞춰 프로필·레퍼런스·주제 키워드·공신 출처·이미지 소스를 대화로 채우는 온보딩을 시작합니다. blog-setup으로 작업 폴더를 준비한 뒤 실행합니다.
argument-hint: "[작업 폴더 경로 (선택)]"
allowed-tools: Skill, Bash, Read
---

사용자가 네이버 블로그 자동화의 온보딩을 시작했다. 너(메인 세션)는 작업 폴더를 확정한 뒤 온보딩 스킬을 부른다.
사용자에게 보여 주는 모든 안내 문구는 **한국어**로 쓴다. 어떤 단계에서도 비밀번호·API 키 값을 받거나 출력하지 않는다.

인자: `$ARGUMENTS` (작업 폴더 경로. 비어 있으면 현재 폴더를 쓴다.)

## 1. 작업 폴더 확정

`/naver-blog-autopilot:blog-setup` 1단계와 같은 규칙이다 — `~`·`~/…`는 홈 폴더로 펼치고(따옴표 때문에 셸이 펼치지 않으므로), **플러그인 저장소 안이면 거부**한다. 온보딩은 폴더를 새로 만들지 않는다(셋업이 먼저다).

```bash
TARGET="$ARGUMENTS"; [ -z "$TARGET" ] && TARGET=.
case "$TARGET" in "~") TARGET="$HOME";; "~/"*) TARGET="$HOME/${TARGET#\~/}";; esac
cd "$TARGET" 2>/dev/null || { echo "NOFOLDER: $TARGET"; exit 1; }
TARGET="$PWD"   # 절대경로로 고정
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -n "$ROOT" ] && { [ -d "$ROOT/.claude-plugin" ] || ls "$ROOT"/plugins/*/.claude-plugin >/dev/null 2>&1; }; then
  echo "REFUSE: 플러그인 저장소 안입니다 ($ROOT)"
elif [ -d knowledge ] && [ -d scripts ]; then
  echo "작업 폴더: $TARGET"
else
  echo "NOTSETUP: $TARGET"
fi
```

- `작업 폴더: <절대경로>` → 그 절대경로를 기억하고 2단계로.
- `REFUSE` → "작업 폴더는 플러그인 저장소 밖(예: ~/naver-blog-work)이어야 합니다. 다른 폴더를 알려주세요." 안내 후 **중단**.
- `NOFOLDER`·`NOTSETUP` → "이 폴더는 아직 작업 폴더로 준비되지 않았습니다. 먼저 `/naver-blog-autopilot:blog-setup <작업 폴더 경로>`를 실행해 주세요(셋업이 끝나면 온보딩을 이어서 제안합니다)." 안내 후 **중단**.

## 2. 온보딩 스킬 호출

`Skill` 도구로 `naver-blog-autopilot:blog-onboarding`을 부른다. args에 "작업 폴더: <1단계 절대경로>"를 넣는다. 이후 질문·파일 쓰기·보고는 전부 그 스킬의 절차(O0~O13)를 따른다 — 이 커맨드에서 따로 묻거나 쓰지 않는다.
