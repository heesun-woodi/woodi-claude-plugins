---
description: 네이버 블로그 글에 대한 피드백을 언제든 남기고(직접 입력 또는 발행된 글과 업로드본 비교) 다음 글부터 반영되도록 학습시킵니다. 인자 rules면 지금 적용 중인 규칙만 보여 줍니다.
argument-hint: "[NNN] [발행 글 주소 또는 logNo] | rules"
allowed-tools: Bash, Read, Write, Edit, Skill, AskUserQuestion
---

담당자가 블로그 글 피드백을 남기려 한다. 너(메인 세션)는 피드백을 `work/feedback-log.md`에 기록하고, 마지막에 학습 스킬을 실행한다.
사용자에게 보여 주는 모든 문구는 **한국어**로 쓴다. 모든 경로는 작업 폴더(cwd) 기준이다.
Windows(Git Bash)에서 `PYTHONUTF8`이 영구 설정돼 있지 않으면 python 명령 앞에 `PYTHONUTF8=1 `을 붙인다. `$(…)`로 받은 값은 `tr -d '\r'`로 CR을 지운다.

인자: `$ARGUMENTS`
- `rules` → 아래 "rules" 절만 하고 끝낸다(기록·학습 없음).
- 비어 있음 → **직접 입력 모드**, 글 = 가장 최근 글 폴더.
- `NNN`(세 자리 숫자)만 → **직접 입력 모드**, 글 = `work/posts/NNN-*`.
- `NNN <주소 또는 logNo>` → **발행본 비교 모드**.
- 주소·logNo만(NNN 없음) → 최근 글 폴더 3개를 옵션으로 "어느 글의 발행본인가요?"를 AskUserQuestion으로 물은 뒤 발행본 비교 모드.

`report` 같은 다른 하위 명령은 없다.

---

## 0. 전제 확인

```bash
[ -d knowledge ] && [ -d scripts ] && [ -d work ] && echo "work-folder: OK" || echo "work-folder: MISSING"
for s in feedback_log.py diff_published.py fetch_post.py; do [ -f "scripts/$s" ] || echo "script: MISSING $s"; done
[ -f knowledge/learned-preferences.md ] && echo "learned-preferences: OK" || echo "learned-preferences: MISSING"
ls -d work/posts/[0-9][0-9][0-9]-* 2>/dev/null | sort | tail -3 | tr -d '\r'
```

- `work-folder: MISSING` → "작업 폴더가 아닙니다. 먼저 `/naver-blog-autopilot:blog-setup`을 실행하세요." 안내 후 **중단**.
- `script: MISSING` → "작업 폴더 scripts가 오래됐습니다 — `/naver-blog-autopilot:blog-setup`을 다시 실행하세요(scripts는 최신본으로 갱신, knowledge는 보존)." 안내 후 **중단**.
- `learned-preferences: MISSING`은 여기서는 괜찮다(학습 스킬 0단계가 템플릿을 복사한다). rules 절에서만 안내한다.
- 글 폴더(`P`)를 정한다: 인자 `NNN`이면 `ls -d work/posts/NNN-* | head -1`, 없으면 위 목록의 마지막(가장 큰 번호). 글 폴더가 하나도 없거나 `NNN-*`가 없으면 "work/posts에 글이 없습니다(NNN 확인)"라고 알리고 **중단**. `--post` 값은 `P`의 폴더 이름(`NNN-slug`)이다.

## 1-A. 직접 입력 모드 (`--stage 직접`)

담당자에게 글 폴더 이름을 알려 주고 **AskUserQuestion** 한 번(질문 3개)으로 받는다:

1. "어떤 점을 고치고 싶으세요? (아래 '기타'에 원문 그대로 적어 주세요)" — 옵션 `기타에 직접 적기` / `지금은 없음(끝내기)`. 기타 입력 원문이 피드백 원문이다. `지금은 없음`이면 기록 없이 3단계로.
2. "어떤 범주인가요?" — 옵션 `제목` / `톤` / `구조` / `분량`. 질문 문구에 "그 밖: 내용·사실·이미지·표지·주제·SEO·기타는 '기타'에 단어로 적어 주세요"를 넣는다.
3. "이번 글에만 해당하나요, 앞으로 계속 지킬 점인가요?" — 옵션 `이번 글만` / `앞으로 계속`.

```bash
python3 scripts/feedback_log.py add --post <NNN-slug> --stage 직접 --category <범주> --scope "<이번 글만|앞으로 계속>" --text "<원문 그대로>"
```

- 원문은 따옴표 안에 그대로 넣는다(원문의 `"`·`$`·`` ` ``는 `\"`·`\$`·`` \` ``로 이스케이프). 원문이 `-`로 시작하면 `--text=<원문>` 형식으로 넘긴다.
- 출력 한 줄이 새 id(`F-0001` 형식)다. exit 2(범주·범위 값 오류)면 범주를 다시 묻는다(범주가 목록에 없으면 `기타`).
- 기록 뒤 AskUserQuestion `더 남기기` / `끝` — `더 남기기`면 1-A를 한 번 더(최대 5건).

## 1-B. 발행본 비교 모드 (`--stage 발행후`)

1. **주소에서 blogId·logNo 뽑기**(주소 형태: `https://blog.naver.com/<blogId>/<logNo>`, `https://m.blog.naver.com/<blogId>/<logNo>`, `…PostView.naver?blogId=<id>&logNo=<no>`, 숫자만 = logNo):
   ```bash
   python3 - '<주소 또는 logNo>' <<'PY'
   import json, re, sys
   s = sys.argv[1].strip().replace("&amp;", "&")
   m = (re.search(r"blogId=([A-Za-z0-9_-]+).*?logNo=(\d+)", s) or re.search(r"logNo=(\d+).*?blogId=([A-Za-z0-9_-]+)", s)
        or re.search(r"blog\.naver\.com/([A-Za-z0-9_-]+)/(\d+)", s))
   if m and m.re.pattern.startswith("logNo"):
       blog, log = m.group(2), m.group(1)
   elif m:
       blog, log = m.group(1), m.group(2)
   elif re.fullmatch(r"\d{6,}", s):
       try:
           o = json.load(open("knowledge/source-blogs.json", encoding="utf-8")).get("own_blog")
           blog = str((o.get("blogId") if isinstance(o, dict) else o) or "").strip()
       except Exception:
           blog = ""
       if not re.fullmatch(r"[A-Za-z0-9_-]+", blog):   # 기본값 없음 — 빈 값·`[…]` 자리표시면 멈춘다
           sys.exit("블로그 ID가 없습니다 — 주소 전체를 주거나 knowledge/source-blogs.json의 own_blog.blogId를 채우세요")
       log = s
   else:
       sys.exit("주소를 읽지 못했습니다")
   print(blog, log)
   PY
   ```
   실패하면 주소를 다시 받는다(AskUserQuestion, 기타 입력 1회). 그래도 실패하면 직접 입력 모드로.
2. `P/final.md`가 **없으면**(이전 형식 글 — 업로드본이 없어 비교할 수 없음) "이 글은 업로드본(final.md)이 없어 발행본과 비교할 수 없습니다 — 직접 입력으로 받겠습니다."라고 알리고 1-A로 간다.
3. 발행본을 받아 글 폴더에 저장하고 비교한다:
   ```bash
   python3 scripts/fetch_post.py <blogId> <logNo> --json > work/posts/<NNN-slug>/published.json; echo "fetch exit=$?"
   python3 scripts/diff_published.py work/posts/<NNN-slug>/final.md work/posts/<NNN-slug>/published.json --json; echo "diff exit=$?"
   ```
   - `fetch exit`가 0이 아니면(비공개·삭제·주소 오류·네트워크) `published.json`을 지우고(`rm -f`) 출력 첫 줄을 보여 준 뒤 직접 입력 모드로.
   - `diff exit=2`면 멈추고 출력 첫 줄을 보고한다.
4. 담당자에게 보여 준다: `summary` 전체, 제목 전후(`title.changed`면), `headings.renamed`·`added`·`removed`, `paragraphs.changed` 상위 5개(전 → 후), `paragraphs.removed`·`added` 상위 5개, `tone`·`length`·`images`, `closing_block_kept`가 **false일 때만** "마무리 블록(📞→해시태그)이 발행본에서 보이지 않습니다"(null = 해당 없음 — 프로필 `마무리 블록`에 `문의헤딩`이 없는 경우 — 이면 이 문장을 쓰지 않는다).
   제목·소제목·문단 변화가 하나도 없으면 "발행본이 업로드본과 같습니다(정규화 기준)"라고 알리고 1-A(직접 입력)를 제안한다.
5. **패턴 제안**: 바뀐 점 가운데 **다음 글에도 해당할 패턴**으로 보이는 것만 1~4개 피드백 문장으로 만든다. 한 글자 오타·특정 수치 정정처럼 그 글에만 해당하는 수정은 제안하지 않는다.
   | 바뀐 점 | 피드백 문장 예 | 범주 |
   |---|---|---|
   | 제목이 짧아짐·형식 바뀜 | "제목을 'OO 총정리'처럼 짧게(n자 → m자) 바꿨습니다 — 제목은 더 짧게" | 제목 |
   | 해요체 늘어남 | "발행 전에 문장 끝을 해요체로 고쳤습니다(해요체 a → b)" | 톤 |
   | 문단 여러 개 삭제·분량 감소 | "문단 n개를 지우고 분량을 x% 줄였습니다 — 설명을 더 짧게" | 분량 |
   | 소제목 이름 바뀜·삭제·추가 | "소제목을 '…' → '…'로 바꿨습니다 — 소제목은 질문형으로" | 구조 |
   | 같은 표현을 여러 곳에서 지움 | "'…' 표현을 모두 지웠습니다 — 이 표현은 쓰지 않기" | 톤 |
   각 문장 끝에 근거를 괄호로 붙인다(예: `(발행본 비교: 해요체 0 → 3)`).
6. **AskUserQuestion** 한 번 — 제안 하나당 질문 하나(최대 4개). 질문 = `[범주] <피드백 문장>`, 옵션 `앞으로 계속` / `이번 글만` / `기록 안 함`. 기타 입력은 고친 문장으로 받아 `이번 글만`으로 기록하되, "앞으로"가 들어 있으면 `앞으로 계속`.
7. 고른 것만 기록한다:
   ```bash
   python3 scripts/feedback_log.py add --post <NNN-slug> --stage 발행후 --category <범주> --scope "<이번 글만|앞으로 계속>" --text "<피드백 문장>"
   ```
8. 비교로 다 담지 못한 점이 있는지 AskUserQuestion `직접 더 남기기` / `끝` — `직접 더 남기기`면 1-A.

## 2. 학습

기록한 피드백이 1건 이상이면(또는 `python3 scripts/feedback_log.py pending`이 `[]`가 아니면) **Skill 도구로** `naver-blog-autopilot:blog-learn`을 실행해 메인이 직접 수행한다(서브에이전트 아님). 스킬의 승인 질문과 보고까지 마친다.
기록이 없고 대기도 없으면 "남긴 피드백이 없어 학습을 건너뜁니다."라고 알린다.

## 3. 마무리 보고

- 이번에 기록한 id 목록(`F-…: [범주] 원문 앞 40자 — 범위`), blog-learn 보고 요약(새로 적용·승격·후보·반영 안 함 개수).
- 발행본 비교 모드였으면 `work/posts/<NNN-slug>/published.json`에 발행본을 저장했다고 알린다.
- "지금 규칙은 `/naver-blog-autopilot:blog-feedback rules`로 볼 수 있습니다."

---

## rules (지금 적용 중인 규칙 보기)

인자가 `rules`이면 이 절만 수행한다. 파일을 쓰거나 고치지 않는다.

```bash
[ -f knowledge/learned-preferences.md ] || { echo "learned-preferences: MISSING"; exit 0; }
sed -n '/^## 적용 중/,/^## 보류·삭제/p' knowledge/learned-preferences.md | grep '^|'
[ -f scripts/feedback_log.py ] && python3 scripts/feedback_log.py pending | python3 -c "import json,sys;print('대기 피드백:', len(json.load(sys.stdin)), '건')"
```

- `MISSING`이면 "아직 학습된 규칙이 없습니다(`knowledge/learned-preferences.md` 없음). 피드백을 남기면 처음 학습 때 만들어집니다."라고 답하고 끝.
- 있으면 두 표로 보여 준다: **적용 중**(id · 범주 · 규칙 · 근거 · 마지막 확인)과 **후보**(id · 범주 · 규칙 · 횟수 · 근거). 행이 없으면 "없음". 마지막 줄에 대기 피드백 수와 "학습하려면 `/naver-blog-autopilot:blog-feedback`" 한 줄.
