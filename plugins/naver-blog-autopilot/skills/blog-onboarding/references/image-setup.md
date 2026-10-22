# 이미지 소스 연동 안내 (정본)

이미지 키·무료 스톡 사진 안내 문구의 **단일 정본**입니다. 온보딩 O9(`skills/blog-onboarding/SKILL.md`)와 `/naver-blog-autopilot:blog-setup`의 3-1·4단계가 이 파일을 인용합니다. 다른 파일에 같은 안내를 다시 적지 않습니다 — 고칠 때는 이 파일만 고칩니다.

메인은 사용자가 고른 이미지 소스의 절만 보여 줍니다. 아래 ``` 블록은 사용자에게 그대로 보여 주는 문구이고, 블록 밖은 메인이 따르는 규칙입니다.

---

## 0. 공통 원칙 (모든 절에 덧붙임)

- 매번 덧붙이는 문장: "**키는 채팅에 붙여넣지 말고 `.env` 파일에 직접** 넣어 주세요."
- 메인은 키 값을 받지도, 읽지도, 출력하지도 않습니다. `.env`에는 메인이 `IMAGE_PROVIDER=` 줄**만** 씁니다(키 줄은 사용자가 직접 씀).
- `.env`를 여는 명령(진단의 OS 갈래만 보여 줌, Claude 입력창이 아니라 **터미널/PowerShell**에서):
  - macOS(터미널): `open -e "<작업 폴더 절대경로>/.env"`
  - Windows(PowerShell): `notepad "<작업 폴더 Windows 경로>\.env"` (예: `notepad "$HOME\naver-blog-work\.env"` — blog-setup 1단계 `작업 폴더(Windows 경로):` 값으로)
- 키를 넣은 뒤 확인은 비용 0 조회입니다(이미지를 만들지 않음). 다시 확인은 **한 번까지** — 그래도 OK가 아니면 결과를 보고 표에 남기고 다음으로 넘어갑니다.

---

## 1. AI 생성 (Gemini 또는 OpenAI)

이미지 생성은 **Gemini**(Google AI Studio) 또는 **OpenAI**(GPT 이미지) 중 가진 키 하나로 합니다. 어느 쪽을 쓸지는 `.env`의 `IMAGE_PROVIDER`(gemini|openai)가 정합니다(없으면 `GEMINI_API_KEY` > `OPENAI_API_KEY` 순). 기본 모델은 gemini=`gemini-3-pro-image`, openai=`gpt-image-2`이고, `.env`의 `IMAGE_MODEL=`로 바꿀 수 있습니다(선택).

### 1-1 Gemini

```
1. https://aistudio.google.com/apikey 에서 API 키를 만듭니다.
2. 결제(Billing)가 설정된 Google Cloud 프로젝트의 키여야 이미지가 만들어집니다.
   무료 키는 이미지 생성에서 429(쿼터 초과)로 실패하고, 기다려도 풀리지 않습니다.
3. 작업 폴더의 .env 에 아래 한 줄을 넣고 저장합니다.

       GEMINI_API_KEY=여기에_키

비용: 1장 약 $0.04(추정치, 정확한 단가는 https://ai.google.dev/pricing).
```

### 1-2 OpenAI

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

### 1-3 확인 명령과 결과 안내

```bash
python3 scripts/check_image_key.py 2>&1 | tr -d '\r'; echo "exit=${PIPESTATUS[0]}"
```

(Windows Git Bash에서 `PYTHONUTF8`이 영구 설정돼 있지 않으면 앞에 `PYTHONUTF8=1 `을 붙입니다.)

종료 코드별 안내:
- `0` → 출력 줄(`이미지 키 확인: <provider> · 모델 <model> 사용 가능 (<source>)`)을 그대로 보여 줍니다. Gemini면 "결제가 없는 무료 키는 이 확인은 통과해도 실제 생성에서 429가 날 수 있습니다" 한 줄을 덧붙입니다.
- `2` (키 없음) → `.env`에 저장했는지, 줄 이름(`GEMINI_API_KEY=` / `OPENAI_API_KEY=`)이 맞는지, `IMAGE_PROVIDER`와 넣은 키의 제공자가 같은지 확인해 달라고 안내합니다.
- `3` (키 거부) → Gemini: 키 오타·삭제된 키 — AI Studio에서 키를 다시 복사합니다. OpenAI: 401이면 키 오타·폐기된 키, **403이면 조직 인증(Verify Organization)이 필요**합니다 — 1-2의 조직 설정 주소에서 인증한 뒤 다시 확인합니다.
- `4` (모델 없음·권한 없음) → Gemini: 결제가 설정된 프로젝트의 키인지, `IMAGE_MODEL`을 바꿨다면 이름이 맞는지. OpenAI: 결제 수단 등록·조직 인증 여부, `IMAGE_MODEL` 이름.
- `5` (네트워크·기타) → 인터넷 연결을 확인하고 잠시 뒤 다시 확인합니다. 키 문제로 단정하지 않습니다.
- `127`·`49`·`9009` → 키 문제가 아니라 python3 문제입니다(blog-setup 4단계 python3 항목).

다른 제공자로 바꾸려면: "작업 폴더 `.env`의 `IMAGE_PROVIDER=`를 `gemini` 또는 `openai`로 바꾸세요(그 제공자의 키도 있어야 합니다. 키가 `.env`에 있으면 그 `.env`의 이 줄만 쓰입니다)."

`IMAGE_KEY: CONFLICT`(blog-setup 2단계)가 남아 있으면: "`.env`의 `IMAGE_PROVIDER=`가 가리키는 제공자의 키를 넣거나, `IMAGE_PROVIDER=`를 가진 키의 제공자로 바꾸세요."

---

## 2. 무료 스톡 사진 — Openverse(기본, 키 불필요, CC0·퍼블릭 도메인만, 익명 한도 분당 20회·하루 200회)

무료 스톡 사진의 기본 제공자는 **Openverse**(WordPress 재단, https://api.openverse.org)입니다. 키가 필요 없어 온보딩에서 키 안내를 하지 않습니다. **Pexels**는 이미 키가 있는 사람만 고르는 선택 제공자입니다(Pexels가 신규 API 키 발급을 일시 중단했습니다). 프로필 `이미지 소스`의 `stock` 값과 이미지 계획표의 `유형=stock`은 제공자와 상관없이 같습니다.

**`STOCK_PROVIDER`** (`.env`, 선택 — `openverse` | `pexels`): 어느 제공자를 쓸지 정합니다.
- 결정 순서: `STOCK_PROVIDER`가 있으면 그 값 → 없고 `PEXELS_API_KEY`가 있으면 `pexels` → 둘 다 없으면 `openverse`.
- 값이 `openverse`/`pexels`가 아니면 오류입니다(값은 출력하지 않음 — blog-setup·blog-run 진단 `STOCK: CONFLICT`). `STOCK_PROVIDER=pexels`인데 `PEXELS_API_KEY`가 없어도 오류입니다(`STOCK: MISSING`). 어느 쪽이든 다른 제공자로 넘어가지 않습니다.
- `.env`를 찾는 순서와 읽는 곳은 `PEXELS_API_KEY`와 같습니다. 메인은 이 줄을 쓰지 않습니다 — 사용자가 직접 넣거나 지웁니다.

### 2-1 Openverse (기본 — 키 불필요)

```
무료 스톡 사진은 키 없이 바로 씁니다. 가입하거나 .env 에 넣을 것이 없습니다.
- 사진: Openverse(WordPress 재단이 운영하는 공개 라이선스 이미지 검색)에서
  CC0·퍼블릭 도메인 사진만 받습니다.
- 출처: 사진마다 사이트·작가·라이선스·원본 주소를 이미지 계획표의 「출처」 칸에 자동으로 기록해 둡니다.
- 한도: 키 없이 쓰는 익명 한도가 있습니다(분당 20회·하루 200회).
- 한국 지명·한국어 간판·한국 거리 같은 장면은 거의 없습니다.
  그런 자리는 AI 생성이나 내 사진으로 채웁니다.
```

### 2-2 Pexels (선택 — 이미 키가 있을 때. 신규 키 발급 일시 중단)

Pexels 키가 이미 있는 사람에게만 보여 줍니다(온보딩 O9에서는 한 줄 안내만 — 아래 블록은 사용자가 Pexels를 쓰겠다고 할 때).

```
Pexels는 신규 API 키 발급을 일시 중단했습니다. 이미 Pexels 키가 있는 분만 쓸 수 있습니다.
작업 폴더의 .env 에 아래 한 줄을 넣고 저장하면 자동으로 Pexels를 씁니다.

       PEXELS_API_KEY=여기에_키

키를 넣어 두고도 Openverse를 쓰려면 .env 에 STOCK_PROVIDER=openverse 줄을 함께 넣습니다.
비용: 무료이고 결제 수단이 필요 없습니다. 사용량 한도가 있습니다(Pexels 안내 기준 기본 시간당 200회·월 20,000회).
라이선스: Pexels 사진은 출처 표기 의무가 없습니다(표기는 권장). 촬영자·주소를 「출처」 칸에 자동으로 기록해 둡니다.
```

### 2-3 확인 명령과 결과 안내

확인 명령(비용 0 조회 — openverse는 검색 1회, pexels는 키 확인):

```bash
python3 scripts/check_image_key.py --stock 2>&1 | tr -d '\r'; echo "exit=${PIPESTATUS[0]}"
```

종료 코드별 안내:
- `0` → 출력 줄(`스톡 확인: openverse 사용 가능 (키 불필요)` 또는 `스톡 키 확인: pexels 사용 가능 (<source>)`)을 그대로 보여 줍니다.
- `2` (설정 오류) → 진단의 `STOCK:` 줄과 같은 원인입니다.
  - `STOCK_PROVIDER` 값이 `openverse`/`pexels`가 아님(`스톡 설정 오류: STOCK_PROVIDER 값이 올바르지 않습니다 — …` · 진단 `STOCK: CONFLICT`) → "`.env`의 `STOCK_PROVIDER=` 줄을 `openverse`나 `pexels`로 고치거나 줄을 지워 주세요." 그 줄 값을 채팅에 붙여넣게 하지 않습니다(키가 섞였을 수 있음).
  - `STOCK_PROVIDER=pexels`인데 키 없음(`STOCK: MISSING`) → "Pexels 키가 있으면 `.env`에 `PEXELS_API_KEY=` 한 줄을 넣고(줄 이름·앞뒤 공백·따옴표 확인), 없으면 `STOCK_PROVIDER=openverse`로 고치거나 줄을 지워 주세요 — 키 없이 Openverse를 씁니다."
- `3` (pexels 키 거부 — 401·403) → 키를 끝까지 복사했는지 확인하고 Pexels 계정 화면에서 키를 다시 복사합니다. 키 없이 쓰려면 `STOCK_PROVIDER=openverse`로 바꿉니다.
- `5` (네트워크·5xx — openverse 요청 한도(429)면 `확인 실패: openverse HTTP 429 — 요청 한도 — 잠시 뒤 다시`) → 인터넷 연결을 확인하고 잠시 뒤 다시 확인합니다. 키 문제로 단정하지 않습니다.
- `127`·`49`·`9009` → 키 문제가 아니라 python3 문제입니다(blog-setup 4단계 python3 항목).

---

## 3. 내 사진 폴더 (`photos/`)

```
직접 찍은 사진을 작업 폴더의 photos/ 폴더에 넣어 주세요(jpg·png, 파일명은 자유).
글마다 다른 사진을 씁니다 — 같은 사진을 여러 글에 다시 쓰지 않습니다.
사진 속 글자·로고·사람 얼굴이 크게 나온 사진은 피해 주세요.
photos/business-intro.png 는 마무리 블록에 소개 이미지를 넣을 때만 쓰는 전용 파일입니다.
```

현재 장수 확인(메인이 실행, 소개 이미지 파일은 세지 않음):

```bash
ls photos 2>/dev/null | awk 'tolower($0) ~ /\.(jpe?g|png|webp|heic)$/ && $0 != "business-intro.png" { n++ } END { print "photos: " n + 0 "장" }'
```

---

## 4. 키를 나중에 넣을 때 (키 없음 모드)

`나중에`를 고르면 `.env`의 키 줄을 건드리지 않고 이렇게 안내합니다:

```
키 없이 진행합니다. /naver-blog-autopilot:blog-run 은 키가 없는 이미지 소스의 슬롯을 「보류」로 두고
나머지 소스(내 사진 등)로 채웁니다. 사진이 디자인 시스템 ④의 min_images보다 적으면 임시저장까지 가지 못하니,
키를 준비하면 /naver-blog-autopilot:blog-onboard 를 다시 실행해 「이미지 소스」 항목만 고르세요.
```
