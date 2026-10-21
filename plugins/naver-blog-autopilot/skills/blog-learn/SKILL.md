---
name: blog-learn
description: Use when pending content feedback for the Naver blog should be turned into writing rules for the next posts — e.g. "피드백 학습해줘", "피드백 반영해서 규칙 정리", "다음 글부터 이렇게 써줘 기억해", "learned preferences 갱신", "blog-learn", "learn from feedback", and at the end of /naver-blog-autopilot:blog-feedback or /naver-blog-autopilot:blog-run. Reads the 대기 rows of work/feedback-log.md (scripts/feedback_log.py pending) and, for 발행후 rows, the diff_published result, then updates knowledge/learned-preferences.md (적용 중 · 후보 · 보류·삭제 · 피할 표현) with the 담당자 (blog owner)'s approval and marks each log row. Runs in the main session (not a subagent). Do NOT use for recording a new feedback item (use /naver-blog-autopilot:blog-feedback), for editing knowledge/design-system.md (use blog-design-system 갱신 모드 — this skill only suggests it), or for fixing the current draft (blog-writer).
---

# 피드백 학습 (learned preferences 갱신)

## 왜 이 스킬이 있나

담당자가 게이트·발행 뒤에 남긴 피드백을 **다음 글에 반영되는 규칙**으로 바꾼다. 같은 말을 두 번 하지 않게 하는 것이 목적이다.
원칙: 피드백 한 건 = 기록 한 줄(`work/feedback-log.md`), 규칙 = 한 문장 지시형(`knowledge/learned-preferences.md`).
한 번 나온 "이번 글만" 요청은 바로 규칙이 되지 않고 **후보**로 쌓이며, 서로 다른 글에서 2회 이상 나오면 승격을 묻는다.

- 수행 주체: **메인 세션**(서브에이전트 아님). 사용자에게 묻는 일은 4단계 승인 하나뿐이다(최대 4개씩).
- 모든 경로는 **작업 폴더(cwd) 기준**이다. Windows(Git Bash)에서 `PYTHONUTF8`이 영구 설정돼 있지 않으면 python 명령 앞에 `PYTHONUTF8=1 `을 붙인다.
- 우선순위(learned-preferences.md 머리와 같음): **잠긴 규칙** = business-profile.md 금칙어·꼭 지켜야 할 점, design-system.md ⑤ 반드시 지킬 것(이미지 속 글자·얼굴 클로즈업·로고 금지, 홍보글은 실사진만, 사진 재사용 금지), ⑧ 지어내기 금지·출처·금칙 (표지 제목 글자는 ⑤ 표지 예외로 허용) > learned-preferences.md `## 적용 중` > design-system.md 나머지 > structure-templates 예시. 학습 규칙은 잠긴 규칙을 바꿀 수 없다.

## 형식 (계약 — 바꾸지 않는다)

`work/feedback-log.md` (scripts/feedback_log.py가 관리):
`| id | 일시 | 글 | 단계 | 범주 | 적용 범위 | 요청 원문 | 처리 |` — id `F-0001`…, 단계 ∈ 게이트1·게이트2·게이트3·발행후·직접,
범주 ∈ 제목·톤·구조·분량·내용·사실·이미지·표지·주제·SEO·기타, 적용 범위 ∈ 이번 글만·앞으로 계속, 처리 ∈ `대기` · `L-NNN` · `반영 안 함: <사유>`.

`knowledge/learned-preferences.md` (정본, 담당자가 직접 고쳐도 됨):

| 절 | 열 |
|---|---|
| `## 적용 중` | `\| id \| 범주 \| 규칙 \| 근거 \| 생긴 날 \| 마지막 확인 \|` |
| `## 후보` | `\| id \| 범주 \| 규칙 \| 근거 \| 생긴 날 \| 마지막 확인 \| 횟수 \|` |
| `## 보류·삭제` | `\| id \| 규칙 \| 사유 \| 날짜 \|` |
| `## 피할 표현` | `- \`표현\` (L-00x)` 한 줄에 하나 — lint `learned_avoid`가 WARN으로 센다(FAIL 아님) |

- id `L-001`… 은 세 표·피할 표현 전체에서 하나씩 늘린다(가장 큰 번호 + 1). 후보가 적용 중으로 올라가도, 보류·삭제로 가도 **id를 그대로** 쓴다.
- 근거 칸: `F-0003·F-0007 (002·004, 2회)` — 피드백 id · 글 번호(글 칸의 앞 3자리) · 횟수. design-system과 충돌하면 끝에 `(디자인 시스템 ②와 충돌 — 이 규칙 우선)`.
- 날짜는 `YYYY-MM-DD`. 생긴 날 = 처음 만든 날, 마지막 확인 = 같은 뜻의 피드백이 마지막으로 온 날(또는 승인한 날).
- 칸 안에 `|`를 쓰지 않는다(필요하면 `/`). 행을 지우지 않고 절 사이로 옮긴다.

---

## 0. 전제 확인

```bash
ls -d knowledge scripts work && ls scripts/feedback_log.py scripts/diff_published.py scripts/lint_post.py knowledge/design-system.md knowledge/business-profile.md
[ -f knowledge/learned-preferences.md ] && echo "learned-preferences: OK" || echo "learned-preferences: MISSING"
```

- `knowledge`·`scripts`·`work`가 없으면 "작업 폴더가 아닙니다. 먼저 `/naver-blog-autopilot:blog-setup`을 실행하세요." 안내 후 **중단**.
- `scripts/feedback_log.py`·`diff_published.py`가 없으면 "작업 폴더 scripts가 오래됐습니다 — `/naver-blog-autopilot:blog-setup`을 다시 실행하세요(scripts는 최신본으로 갱신, knowledge는 보존)." 안내 후 **중단**.
- `learned-preferences: MISSING`이면 빈 템플릿을 복사하고 그렇게 했다고 알린 뒤 계속한다(기존 파일은 덮지 않음):
  ```bash
  cp -n "${CLAUDE_PLUGIN_ROOT}/scaffold/knowledge/learned-preferences.md" knowledge/learned-preferences.md
  ```

## 1. 대기 항목 읽기

```bash
python3 scripts/feedback_log.py pending
```

- 출력은 JSON 배열(`[]`이면 대기 없음). 원소 키: `id`·`일시`·`글`·`단계`·`범주`·`적용 범위`·`요청 원문`·`처리`. `요청 원문`은 줄바꿈·`|`가 원문대로 복원돼 있다.
- `[]`이면 "학습할 대기 피드백이 없습니다."라고 알리고 6단계(정리 제안)만 확인한 뒤 끝낸다.
- 함께 읽는다: `knowledge/learned-preferences.md`(4절 전부), `knowledge/design-system.md`(②~⑨ — 충돌 판단용, ⑤ 반드시 지킬 것·⑧은 잠긴 규칙), `knowledge/business-profile.md`(꼭 지켜야 할 점·금칙어 — 잠긴 규칙).
- 단계가 `발행후`인 항목은 같은 글 폴더(`work/posts/<글>/`)에 `final.md`와 `published.json`이 있으면 비교 결과를 근거로 참고한다(쓰기 없음):
  ```bash
  python3 scripts/diff_published.py work/posts/<글>/final.md work/posts/<글>/published.json --json
  ```
  `summary`·`title`·`headings.renamed`·`paragraphs`·`tone`·`length`로 그 피드백이 패턴인지(예: 해요체가 늘었다, 문단을 줄였다) 확인한다. 이 결과만으로 피드백을 새로 만들지 않는다(기록은 `/naver-blog-autopilot:blog-feedback`의 일).

## 2. 항목마다 판정

항목을 id 순으로 하나씩 아래 순서로 판정하고, 판정 표(id · 판정 · 대상 L-id · 규칙 문장)를 작업 메모로 만든다.

| 순서 | 조건 | 처리 |
|---|---|---|
| (c) 잠긴 규칙 | 금칙어를 쓰게 하거나 빼자는 요청, 출처 없이 수치·일정을 쓰자는 요청, 출처 표기를 없애자는 요청, 금칙어가 가리키는 사실의 암시, 이미지에 글자·로고·얼굴을 넣자는 요청, 홍보글에 AI 이미지를 쓰자는 요청, 사진을 재사용하자는 요청 등 — 잠긴 규칙을 바꾸려는 것. 단 **표지(00) 제목 글자**는 ⑤ 표지 예외라 잠긴 규칙이 아니다(표지 글자 크기·줄바꿈·문구 요청은 범주 `표지` 규칙으로 다룬다) | 규칙으로 만들지 않는다. 처리 `반영 안 함: 잠긴 규칙`. 보고에 이유 한 줄(예: "금칙어는 계약·브랜드 규칙이라 학습 규칙으로 바꿀 수 없습니다 — business-profile.md를 담당자가 직접 고쳐야 합니다") |
| (c′) 사실 정정 | 범주 `사실`이거나, 특정 수치·일정·수수료가 틀렸다는 요청 | 규칙이 아니다. 처리 `반영 안 함: 사실 정정(knowledge 확인 필요)`. 보고에 "business-profile.md / official-sources.md에서 출처와 함께 고칠 내용"으로 따로 적는다 |
| (e) lint·프로필과 충돌 | lint가 강제하는 것과 반대인 요청 — lint 블록 범위 밖 분량·소제목·이미지 수, 고정 골격 바꾸기 → 처리 `반영 안 함: 디자인 시스템 갱신 필요`(6단계에서 "blog-design-system 갱신 모드" 제안). 프로필 행이 정하는 것을 바꾸자는 요청 — 프로필 `톤`과 다른 말투(합니다체 프로필에 "해요체로", 해요체 프로필에 "합니다체로"), `고객 지역` 추가·삭제, 마무리 블록(⑥) 구성 변경 → 처리 `반영 안 함: 프로필 변경 필요`(보고에 "`/naver-blog-autopilot:blog-onboard`에서 그 항목을 바꾸세요" 한 줄). 프로필 `톤`과 같은 쪽의 말투 요청(예: 해요체 프로필에서 "더 부드러운 해요체로")은 (a)/(b)로 처리한다 | 위와 같음 |
| (f) 이 글 한정 | 그 글의 주제·특정 수치·날짜·문장 하나에만 해당(예: "3번 문단의 4분을 5분으로") — 범위가 무엇이든. 단 단계 `게이트3`이거나 범위 `앞으로 계속`인 행은 먼저 **슬롯 번호·파일명·이 글의 주제어를 빼고 일반화**해 본다(예: "03번 슬롯 사진이 너무 어둡다" → "실내 장면 이미지는 밝게 만든다"). 담당자가 `앞으로 계속`을 골랐으면 일반화할 수 있는 한 규칙으로 만들고, 일반화한 뒤에도 이 글에만 해당할 때만 이 행을 적용한다 | 처리 `반영 안 함: 이번 글 한정` |
| (g) 범주 `기타` | 로그 범주가 `기타` | 규칙은 10개 범주(제목·톤·구조·분량·내용·사실·이미지·표지·주제·SEO) 중 하나로 **다시 분류**해 만든다(로그 범주 칸은 그대로 둔다 — `기타` 규칙은 읽는 곳이 없다). 다시 분류한 범주로 아래 (d)·(a)·(b)를 판정한다. 어느 범주에도 넣을 수 없으면 처리 `반영 안 함: 범주 불명` |
| (d) 보류·삭제와 같은 뜻 | `## 보류·삭제`에 같은 범주·같은 뜻의 규칙이 있음 | 자동 승격·자동 적용하지 않는다(범위가 "앞으로 계속"이어도). `## 후보`에 그 id 행이 있으면 횟수+1·근거 추가, 없으면 같은 id로 후보 행을 만든다(횟수 1). 처리 = 그 L-id. 범위가 "앞으로 계속"이면 4단계에서 "예전에 삭제한 규칙인데 다시 적용할까요?"로 묻는다 |
| (a) 앞으로 계속 | 범위 `앞으로 계속` | 규칙 문장으로 바꿔 `## 적용 중`에 추가. 같은 범주·같은 뜻의 적용 중 규칙이 있으면 새로 만들지 않고 그 규칙의 근거(F-id·글 번호·횟수)와 마지막 확인만 갱신. 같은 뜻의 후보가 있으면 그 행을 적용 중으로 옮긴다(id 유지, 횟수 열 제거, 근거 합침). 처리 = 그 L-id. **묻지 않고 적용**하되 7단계 보고에 보여 준다 |
| (b) 이번 글만 | 범위 `이번 글만`이고 일반화할 수 있는 요청 | 같은 범주·같은 뜻의 후보가 있으면 횟수+1·근거 추가·마지막 확인 갱신, 없으면 `## 후보`에 새 L-id로 추가(횟수 1). 근거의 **서로 다른 글이 2개 이상**이 되면 **승격 제안** 목록에 넣는다(같은 글에서 두 번은 승격하지 않는다). 처리 = 그 L-id |

- "같은 뜻": 범주가 같고, 규칙 문장으로 바꿨을 때 지시하는 행동이 같으면 같은 뜻이다(표현이 달라도). 애매하면 다른 뜻으로 보고 새 행을 만든다.
- 한 항목에 요청이 여러 개면(예: "제목은 짧게, 도입은 질문으로") 규칙을 나눠 만들고, 로그 처리 칸에는 첫 L-id를 적는다(나머지는 근거 칸에서 같은 F-id로 이어진다).

## 3. 규칙 문장 쓰기

- **한 문장, 지시형, 측정 가능하게.** 예: "도입 첫 문장은 독자 상황을 묻는 질문으로 시작한다." / "제목은 30자 이내로 쓴다." / "한 문단은 3문장을 넘기지 않는다." / "`결론부터 말씀드리면` 표현을 쓰지 않는다."
- 나쁜 예: "글을 더 좋게 쓴다"(측정 불가), "이번 글처럼 쓴다"(대상 불명), "4분을 5분으로 고친다"(이 글 한정 — 규칙 아님).
- 특정 단어·표현을 쓰지 말라는 규칙이면 그 표현을 `## 피할 표현`에도 `- \`표현\` (L-00x)`로 추가한다(lint가 WARN으로 센다). 표현은 본문에 실제로 나오는 글자 그대로(공백은 무시하고 비교됨).
- design-system.md와 충돌하면(예: ②는 "한 문단 2~4문장"인데 규칙은 "3문장 이하") 근거 칸 끝에 `(디자인 시스템 ②와 충돌 — 이 규칙 우선)`을 적고 4단계 질문에도 충돌을 밝힌다. lint가 강제하는 항목과의 충돌은 2단계 (e)로 이미 걸러졌다.

## 4. 승인 (AskUserQuestion)

묻는 대상은 아래 세 가지뿐이다(blog-run의 승인 규칙과 같다):
1. **후보 승격** — (b)에서 근거의 서로 다른 글이 2개 이상이 된 후보.
2. **보류·삭제 재적용** — (d) 중 범위가 "앞으로 계속"이거나, 후보 근거의 서로 다른 글이 2개 이상이 된 것("예전에 보류·삭제한 규칙인데 다시 적용할까요?").
3. **기존 적용 중 규칙의 문장 변경**(근거·마지막 확인만 바뀌는 것은 묻지 않음).

범위 "앞으로 계속"인 (a)의 신규·갱신은 담당자가 이미 골랐으므로 **묻지 않고 적용**하고 7단계 보고에만 보여 준다.

- 질문 하나 = 규칙 하나. 한 번에 최대 4개, 넘으면 나눠서 묻는다.
- 질문 문구: `<L-id> [<범주>] <규칙 문장>` + 근거(`F-…`·글 번호·횟수) + 충돌이 있으면 "(디자인 시스템 ②와 충돌 — 적용하면 이 규칙이 우선)".
- 옵션 3개: `적용` / `이번엔 보류` / `삭제(다시 제안하지 않기)`.

| 답 | 처리 |
|---|---|
| `적용` | `## 적용 중`으로 옮기거나 문장을 바꾼다(id 유지, 마지막 확인 = 오늘). 표현 금지 규칙이면 `## 피할 표현`에도 추가. 2번(보류·삭제 재적용)이면 `## 보류·삭제`의 같은 id 행을 지운다(후보 행도 적용 중으로 옮겼으므로 남지 않는다) |
| `이번엔 보류` | `## 후보`에 그대로 둔다(다음에 같은 뜻이 또 오면 다시 묻는다). 문장 변경이었으면 기존 문장 유지 |
| `삭제(다시 제안하지 않기)` | 후보·적용 중에서 빼서 `## 보류·삭제`에 `\| L-id \| 규칙 \| 담당자 삭제(<F-id>) \| 오늘 \|`로 옮기고, `## 피할 표현`에 그 id 줄이 있으면 지운다 |
| 기타 입력 | 담당자가 문장을 고쳐 준 것이면 그 문장으로 `적용`, 이유를 적은 것이면 `이번엔 보류`로 처리하고 이유를 보고에 옮긴다 |

## 5. 저장과 로그 표시

1. `knowledge/learned-preferences.md`를 Edit 도구로 고친다 — 표 머리·구분선·절 헤딩·머리 주석·안내 문단은 그대로 두고 행만 더하거나 옮긴다.
2. 판정마다 로그 처리 칸을 표시한다(대기 항목 전부, 하나도 `대기`로 남기지 않는다):
   ```bash
   python3 scripts/feedback_log.py mark F-0003 L-005
   python3 scripts/feedback_log.py mark F-0004 "반영 안 함: 이번 글 한정"
   ```
   exit 1(없는 id)·2(값 오류)면 멈추고 그 명령·출력 첫 줄을 보고한다.
3. 자체 점검 — 하나라도 실패하면 고친 뒤 다시 돌린다:
   ```bash
   python3 - <<'PY'
   import re, sys
   sys.path.insert(0, "scripts"); import feedback_log, lint_post
   want = {"## 적용 중": 6, "## 후보": 7, "## 보류·삭제": 4}
   sec, ids, bad = None, [], []   # ids: (절, id)
   for n, ln in enumerate(open("knowledge/learned-preferences.md", encoding="utf-8").read().split("\n"), 1):
       if ln.startswith("## "):
           sec = ln.strip()
       elif sec in want and ln.lstrip().startswith("| L-"):
           cells = feedback_log.split_row(ln)
           if len(cells) != want[sec]:
               bad.append(f"{n}행 {sec}: 열 {len(cells)}개(필요 {want[sec]})")
           ids.append((sec, cells[0]))
   secs = lambda i: [s for s, x in ids if x == i]
   # 같은 절에 두 번, 또는 적용 중과 다른 절에 함께 있으면 중복(후보+보류·삭제 같은 id는 (d)라 허용)
   dup = sorted({i for _, i in ids if len(secs(i)) != len(set(secs(i))) or ("## 적용 중" in secs(i) and len(secs(i)) > 1)})
   avoid = lint_post.load_learned_avoid("knowledge")
   print("rules:", len(ids), "| dup:", dup or "없음", "| avoid:", len(avoid or []), "|", "; ".join(bad) or "열 OK")
   print("ALL OK" if not bad and not dup else "FIX")
   PY
   python3 scripts/feedback_log.py pending
   ```
   `ALL OK`이고 `pending`이 `[]`여야 끝난다. 같은 id가 두 절에 있어도 되는 경우는 (d)의 `## 후보` + `## 보류·삭제` 한 쌍뿐이다.

## 6. 정리 제안 (제안만 — 자동으로 고치지 않는다)

다음 중 하나라도 맞으면 보고 끝에 "디자인 시스템 정식 반영을 권합니다 — `blog-design-system` 스킬의 **갱신 모드**로 이 규칙들을 design-system.md에 옮기고 learned-preferences.md에서는 보류·삭제(사유: 디자인 시스템 반영)로 옮기세요."를 대상 규칙 id와 함께 적는다:

- `## 적용 중` 규칙이 **12개를 넘는다**.
- 같은 범주 규칙 2개 이상이 디자인 시스템 한 절(예: ② 톤앤매너, ③ 구조, ④ 분량)과 겹친다.
- 2단계 (e) `반영 안 함: 디자인 시스템 갱신 필요`가 이번에 1건 이상 있었다(그 요청 원문을 함께 보여 준다).

`knowledge/design-system.md`는 이 스킬에서 절대 고치지 않는다.

## 7. 결과 보고 (사용자에게, 한국어)

1. 한 줄 요약: `새로 적용 n개 · 승격 n개 · 후보 n개(새 a · 횟수 증가 b) · 반영 안 함 n개`.
2. 바뀐 규칙 목록 — `L-id [범주] 규칙 문장 — 근거` (새로 적용·승격·문장 변경·삭제를 구분). "앞으로 계속"이라 묻지 않고 적용한 것도 여기에 보인다.
3. 반영 안 함 목록 — `F-id: 사유` + 할 일(잠긴 규칙 → business-profile.md 직접 수정, 사실 정정 → knowledge 출처 확인, 디자인 시스템 갱신 필요 → 6단계 제안).
4. 6단계 정리 제안(해당할 때만).
5. "다음 글부터 blog-writer가 `knowledge/learned-preferences.md`의 적용 중 규칙을 따릅니다. 지금 규칙은 `/naver-blog-autopilot:blog-feedback rules`로 볼 수 있습니다."

산출물: `knowledge/learned-preferences.md`(갱신), `work/feedback-log.md`(처리 칸), 보고 메시지.
