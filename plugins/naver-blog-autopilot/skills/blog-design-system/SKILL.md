---
name: blog-design-system
description: Use when the user wants to create or update the blog's content design system document (knowledge/design-system.md) from its design references — e.g. "디자인 시스템 만들어줘", "디자인 시스템 갱신해줘", "레퍼런스 추가했어", "글 스타일 가이드 만들어줘", "블로그 디자인 가이드", "레퍼런스 블로그 분석해서 규칙 만들어줘", "blog-design-system", "build the blog design system", "update the style guide from references". Measures each reference post with scripts/fetch_post.py, turns the "why" note written for each reference into numeric rules, and writes knowledge/design-system.md (sections ①~⑨ + 부록 A/B, with the lint block in ④). Fills ② from the profile's 톤 row (합니다체 or 해요체) and ③·⑥·⑦ from the 마무리 블록 and 고객 지역 rows. A new blog with no posts of its own (no 'own-style' reference) takes the ★ 레퍼런스 0 없음 path (external references only, lint defaults marked as initial values). Do NOT use for writing a post draft (use blog-draft-writer), for topic research (use blog-topic-research), or for SEO scoring of a draft (use blog-naver-seo).
---

# 블로그 디자인 시스템 만들기·갱신하기

## 왜 이 스킬이 있나

이 플러그인에서 **디자인 가이드가 가장 중요한 문서**다. 원칙은 **"레퍼런스는 URL이 아니라 이유"** —
담당자가 레퍼런스마다 적은 메모(why)를 **측정값**으로 바꾸고, 그 측정값에서 **규칙**을 만든다. 규칙마다 어느 메모·어느 수치에서
왔는지 추적할 수 있어야 하며, 그 추적표가 결과 문서의 "부록 A"다. 인상("보기 좋다")만으로 규칙을 만들지 않는다.

- 산출물: 작업 폴더 `knowledge/design-system.md` (이 파일이 **유일한 정본**. 플러그인 scaffold의 것은 설치 시 복사되는 초기값일 뿐).
- 이 문서를 읽는 쪽: blog-writer 에이전트(초안), blog-fact-checker, `scripts/lint_post.py`(④의 lint 블록만 기계적으로 읽음).
- 수행 주체: 메인 세션. 사용자에게 묻는 일은 마지막 8단계 "담당자 검토 요청" 하나뿐이다.
- 템플릿 = **그 문서 자체**다. 설치 때 복사된 `knowledge/design-system.md`(플러그인 `scaffold/knowledge/design-system.md`)가 `[치환 변수]`와 lint 기본값을 가진 정본 템플릿이고, 생성 모드는 그 파일의 `[치환 변수]`만 채운다(헤딩 ①~⑨·부록 A·B·측정 기록과 표지 1000×1000·`H2_FILLER_LINES`·마무리 순서 같은 상세 규칙은 그대로 남는다). 무엇을 어디에 채우는지는 이 스킬 폴더의 `references/fill-guide.md` 하나에만 있다.

모든 경로는 **작업 폴더(cwd) 기준**이다. 지식 파일을 `${CLAUDE_PLUGIN_ROOT}`에서 읽지 않는다(예외: 작업 폴더에 `knowledge/design-system.md`가 없을 때의 원본 복사, 이 스킬 폴더의 `references/fill-guide.md`).

---

## 0. 전제 확인

```bash
ls -d knowledge scripts && ls knowledge/business-profile.md knowledge/source-blogs.json scripts/fetch_post.py scripts/fetch_posts.py scripts/lint_post.py
```

하나라도 없으면 "작업 폴더가 아닙니다. 먼저 `/naver-blog-autopilot:blog-setup`으로 작업 폴더를 준비하세요."라고 안내하고 **중단**한다.

산출물: 없음(확인만).

## 1. 입력 수집과 모드 결정

1. `knowledge/business-profile.md`를 읽는다 — 업체정보 표(②·③·⑤·⑥·⑦을 채울 때 쓰는 `톤`·`마무리 블록`·`문의 헤딩 문구`·`고객 지역`·`이미지 소스` 행 포함), "## 꼭 지켜야 할 점", "## 금칙어"(백틱 단어 전부), "## 홍보/정보 비율".
2. `knowledge/source-blogs.json`에서 `design_references[]`(각 `blogId`, `logNo`, `url`, `why`, 선택 `role`)와 `own_blog`(`blogId`, `categories.info`)를 읽는다.
   `role: "own-style"` 항목(자기 글 — 겉모습·구조·분량의 기준)은 **레퍼런스 0**이고 측정 파일은 `own-<logNo>`다. 나머지 레퍼런스 번호 n은 배열 순서(1부터)다. `own-style` 항목이 없으면 아래 「★ 레퍼런스 0 없음」 경로다(자기 글 0편인 블로그도 기준 글이 없어 여기에 든다).
3. 모드 결정 — scaffold가 `knowledge/design-system.md` 템플릿을 미리 복사해 두므로 **파일이 있다고 갱신 모드가 아니다**:
   - 파일이 **없거나 템플릿 초기값이면 → 생성 모드**. 템플릿 초기값 판정: 머리 표의 `버전` 값이 `[버전]`이거나, 제목(첫 줄 `# …`)에 `[업체명]`이 남아 있음(플러그인 템플릿 형식 `{{버전}}`·`{{업체명}}`도 같다).
   - **채워진 문서면(위 둘 다 아님) → 갱신 모드**. 순서가 고정이다:
     1) 기존 `knowledge/design-system.md`를 `work/design-system/design-system.prev-<YYYY-MM-DD>.md`(백업)와 `work/design-system/proposed.md`(작업본) 두 곳에 복사한다.
     2) **작업본 `proposed.md`를 직접 고친다** — 바꾸는 것은 새 측정값에서 나온 **수치(④ 규칙·lint 블록 값·근거 괄호)와 부록 A·B의 행**뿐이다.
     3) 보존: 담당자가 손으로 고친 문장(특히 ② 예시 문장, ⑧ 금칙), 다른 스킬이 lint 블록에 추가한 키(예: `kw_min_body`, `title_min`), 기존 절·문단.
     4) 플러그인 원본 `${CLAUDE_PLUGIN_ROOT}/scaffold/knowledge/design-system.md`는 갱신 모드에서 **헤딩 대조용으로만** 쓴다(누락 헤딩이 있으면 그 헤딩과 절 본문만 추가. 1.1.0 문서의 `## 자기 블로그 기준 측정 절차`는 헤딩만 `## 측정 기록`으로 바꾸고 그 절의 측정 기록 한 줄을 남긴다). 원본으로 새로 쓰지 않는다.
        예외: 7단계 체크리스트가 요구하는 문구(⑦ `type` 키, ⑨ 근거 문구 등)가 prev에 없으면 그 문구만 추가한다.
     5) `knowledge/`는 8단계에서 사용자가 승인한 뒤에만 바꾼다.

```bash
mkdir -p work/design-system   # [ds-mode]
F=knowledge/design-system.md
if [ ! -f "$F" ]; then
  cp "${CLAUDE_PLUGIN_ROOT}/scaffold/knowledge/design-system.md" "$F" && echo "생성 모드(원본 복사)"
elif grep -qE '^# .*(\[업체명\]|\{\{업체명\}\})' "$F" || grep -qE '^\| *버전 *\| *(\[버전\]|\{\{버전\}\}) *\|' "$F"; then
  # 템플릿 초기값 — 지난 버전 플러그인이 복사한 템플릿일 수 있으므로 이번 원본으로 바꾼다(치환 변수 이름이 fill-guide와 맞게, 이전 판은 백업)
  B="work/design-system/design-system.template-prev-$(date +%F).md"
  cmp -s "$F" "${CLAUDE_PLUGIN_ROOT}/scaffold/knowledge/design-system.md" || { cp "$F" "$B" && cp "${CLAUDE_PLUGIN_ROOT}/scaffold/knowledge/design-system.md" "$F" && echo "템플릿 교체: 이전 판 백업 $B"; }
  echo "생성 모드"    # 5단계가 이 파일의 [치환 변수]를 채운다
else
  cp "$F" "work/design-system/design-system.prev-$(date +%F).md" && cp "$F" work/design-system/proposed.md && echo "갱신 모드"
fi
```

산출물: 모드(생성/갱신), `템플릿 교체:` 줄이 나왔으면 그 백업 경로(8단계 보고에 적는다 — 손으로 고친 템플릿이었다면 담당자가 백업에서 옮길 수 있게), 갱신 모드면 `work/design-system/design-system.prev-<날짜>.md`(백업)·`work/design-system/proposed.md`(작업본).

## ★ 「레퍼런스 0 없음」 생성 경로 (자기 기준 글이 없는 블로그)

**판정**: `source-blogs.json`의 `design_references`에 `role: "own-style"` 항목이 **없으면** 이 경로다(자기 글이 0편인 블로그는 기준 글을 고를 수 없으므로 여기에 들어온다). `own-style`이 있으면 그 글 자체가 자기 글이므로 `work/own-posts.json`이 낡아 `[]`이어도 ★가 아니다. 글 수(`자기 글(블로그 전체): N편` — `work/own-posts.json` 길이, 없을 때만 `fetch_posts.py --rss` 결과 길이)는 판정에 쓰지 않고 측정 기록에만 적는다. **카테고리로 거른 측정 대상 수로도 판정하지 않는다**(`fetch_posts.py --all` 목록은 `category`가 비는 블로그가 있어 카테고리 매칭이 0편이 될 수 있다). 2·3단계 스크립트가 같은 규칙으로 판정해 `경로:` 줄을 출력한다. **생성 모드에서만** 적용한다 — 갱신 모드(채워진 문서)는 prev의 값을 보존한다. 측정할 자기 기준이 없다는 사실을 문서에 숨기지 않고 **초기값**으로 표시하는 경로다.

| 단계 | 평소 | 레퍼런스 0 없음 |
|---|---|---|
| 2 측정 | 레퍼런스 + 자기 글 최신 10편 + `own-style` | **외부 레퍼런스(`design_references`)만** 측정한다(`ONLY=ref`). 자기 글 수집·`own-*` 파일 없음. 외부 레퍼런스도 0개면 2~3단계를 건너뛰고 측정표 없이 진행한다(머리 표의 측정표 칸 = `없음`) |
| 3 측정표 | 레퍼런스·자기 글 행 + 중앙값 2행(레퍼런스·자기 글) | 레퍼런스 행 + **레퍼런스 중앙값 1행만**. 스크립트가 경로를 스스로 판정해 지난 측정의 `own-*.json`이 남아 있어도 자기 글 행·자기 글 중앙값 행을 만들지 않는다 |
| 4 추적표 | 레퍼런스 0 기본 쪼개기 7조각 + 레퍼런스 1~n | 레퍼런스 0 행 **없음**. 외부 레퍼런스(1~n) why 조각만 |
| 5 수치 | 5단계 「값 출처 순서」 1→4 | **lint 키는 전부 lint 기본값**(④ 초기값 그대로 — 5단계 「값 출처 순서」의 ★ 규칙). 문장 규칙(이미지당 글자수·소제목당 글자수·굵게·권장 이미지 수)만 「값 출처 순서」 2→4로 정한다 |
| ② 예시 문장 | `own-*.md`에서 그대로 복사(`(logNo)`) | 남긴 판의 `초기 예시` 줄을 그대로 두고 `예시 문장:` 줄을 지운다(fill-guide ②). 문장을 지어내지 않는다 |
| ⑦ · ⑨ · 부록 B · 측정 기록 | 자기 글 측정값 | fill-guide의 ★ 열대로 `측정 전`·「측정 전 초기값 — 첫 글 뒤 갱신 권장」(부록 B는 레퍼런스 중앙값 행만) |
| 7 자체 점검 | `NFRAG` = 레퍼런스 0 기본 7조각 + 레퍼런스 1~n의 why 조각 수 | `NFRAG` = **외부 레퍼런스 why 조각 수만**(0이면 부록 A 행 수 점검 생략). ② 예시 문장 `grep -F` 점검은 초기 예시라 건너뛴다 |
| 8 보고 | 검토 요청 3가지 | 첫 항목을 "② 톤 예시는 초기 예시입니다"로 바꾸고, 첫 글을 임시저장한 뒤 그 글을 `design_references`에 `role: "own-style"`(why = 구조·모습 전체)로 넣고 이 스킬을 다시 실행하면(갱신 모드) 자기 글 기준으로 바뀐다는 안내를 덧붙인다 |

자기 글이 있는데 기준 글(`own-style`)만 고르지 않은 블로그도 이 경로다(리허설: 자기 글 6편, 기준 글 없음). 그 글들은 측정하지 않고, ⑥ 관련글은 글마다 blog-run이 센 자기 글 수로 정한다(문서에 편수를 적지 않는다).

갱신 모드에서 `own-style`이 생기면 위 초기값 표기(⑦·⑨·부록 B·측정 기록의 「측정 전」, 근거 괄호의 "측정 전", ②의 `초기 예시` 줄)를 새 측정값·실제 예시 문장으로 바꾸며 지운다.

## 2. 레퍼런스·자기 글 측정 (읽기 전용 수집)

각 글에 `python3 scripts/fetch_post.py <blogId> <logNo> --json`을 실행한다. **이미 측정한 글은 다시 받지 않는다**: 온보딩(O4·O7a)이 미리 측정해 둔 `work/design-system/own-<logNo>.json`·`ref-<n>-<blogId>.json`이 있고 그 안 `stats`의 `blogId`·`logNo`가 같으면 fetch를 생략하고 그 파일을 재사용한다. 온보딩은 `.json`만 저장하므로 같은 이름의 `.md`가 없으면 JSON의 `markdown` 필드로 `.md`를 만들어 재사용한다(`markdown`도 없으면 다시 받는다). 아래 스크립트가 자동으로 하고 `재사용 n`을 출력한다(logNo가 다르면 다시 받아 덮어쓴다). 출력은 `{"stats": {...}, "markdown": "..."}`이고 stats 키는 정확히 다음과 같다:
`blogId, logNo, title, chars, paragraphs, headings, images, bold_runs, bold_lines, quotes, links_out, links_naver_blog, oglinks`.
(`headings`는 fs24/fs19 글씨 또는 sectionTitle 문단만 센다 — 굵은 줄로 만든 소제목은 `bold_lines`에 들어간다. 3단계에서 보정한다.)

- 레퍼런스: `design_references`(`own-style` 제외) → `work/design-system/ref-<n>-<blogId>.json`(원본 JSON)과 `ref-<n>-<blogId>.md`(markdown만). 실행할 때 기존 `ref-*` 파일은 `work/design-system/_prev/`로 옮겨 재사용 후보로만 쓴다 — 그래서 `work/design-system/`의 `ref-*`는 **이번 `design_references`의 글만** 남고(빠진 레퍼런스는 측정표·중앙값에 들어가지 않는다), 순서가 바뀌어도 서로 덮어쓰지 않는다. `own-style` 레퍼런스 0 → `own-<logNo>.{json,md}`(최신 10편에 없어도 측정).
- 자기 블로그(★ 경로가 아닐 때만): `python3 scripts/fetch_posts.py --rss <own_blog.blogId>`에서 `category == own_blog.categories.info`인 글을(`categories.info`가 비어 있으면 카테고리로 거르지 않는다)
  `date` 내림차순 **최신 10개** → 각각 fetch_post → `work/design-system/own-<logNo>.json`, `own-<logNo>.md`.
  RSS에 해당 카테고리 글이 10개 미만이면 `python3 scripts/fetch_posts.py --all <own_blog.blogId>`로 다시 걸러 채운다(`--all` 목록은 `category`가 빌 수 있다 — 빈 글은 카테고리를 알 수 없어 채우지 않는다). 그래도 모자라면 있는 만큼만 쓰고 개수를 보고에 적는다.
- **자기 글 수** = `work/own-posts.json` 길이(없으면 `--rss` 결과 길이) — 측정 기록에만 쓴다(★ 판정은 `own-style` 유무). 측정 대상(카테고리로 거른 최신 10편)과 다르므로 둘 다 출력한다.

아래 스크립트를 그대로 실행하면 된다(요청 사이 0.5초 간격, 실패한 글은 건너뛰고 목록을 출력):

```bash
ONLY=all python3 - <<'PY'   # [ds-collect] ONLY=ref(레퍼런스만) | own(자기 글만) | all(기본)
import json, subprocess, sys, time, os, glob
sys.path.insert(0, "scripts")
from lint_post import own_posts_count  # work/own-posts.json 글 수 — lint related_links와 같은 셈
ONLY = os.environ.get("ONLY", "all")
D = "work/design-system"; os.makedirs(D, exist_ok=True)
src = json.load(open("knowledge/source-blogs.json", encoding="utf-8"))
own = src.get("own_blog") or {}; own_id = own.get("blogId") or ""; own_cat = (own.get("categories") or {}).get("info") or ""
refs = [r for r in src.get("design_references", []) if r.get("role") != "own-style"]
has_style = any(r.get("role") == "own-style" for r in src.get("design_references", []))

_cache = {}
def posts(flag):
    if not own_id: return []
    if flag not in _cache:
        out = subprocess.run([sys.executable, "scripts/fetch_posts.py", flag, own_id], capture_output=True, text=True, encoding="utf-8")
        _cache[flag] = json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else []
    return _cache[flag]
n_own = own_posts_count("work/own-posts.json")
if n_own is None: n_own = len(posts("--rss"))
star = not has_style  # own-style이 있으면 자기 글이 있다 — 글 수(낡을 수 있음)로 판정하지 않는다
want_own = ONLY in ("own", "all") and not star
jobs = [(r["blogId"], r["logNo"], f"ref-{i}-{r['blogId']}") for i, r in enumerate(refs, 1)] if ONLY in ("ref", "all") else []
match = lambda p: not own_cat or p.get("category") == own_cat  # info 카테고리가 없으면 거르지 않는다(빈 category는 미상 — 채우지 않음)
mine = [p for p in posts("--rss") if match(p)] if want_own else []
if want_own and len(mine) < 10:
    seen = {p["logNo"] for p in mine}
    mine += [p for p in posts("--all") if p["logNo"] not in seen and match(p)]
mine = sorted(mine, key=lambda p: p["date"], reverse=True)[:10]
jobs += [(own_id, p["logNo"], f"own-{p['logNo']}") for p in mine]
if want_own:  # 레퍼런스 0(own-style)은 최신 10편 밖이어도 측정
    jobs += [(r["blogId"], r["logNo"], f"own-{r['logNo']}") for r in src.get("design_references", [])
             if r.get("role") == "own-style" and r["logNo"] not in {p["logNo"] for p in mine}]

PREV = f"{D}/_prev"  # 지난 ref-* 파일 보관 — 번호가 바뀌어도 다른 레퍼런스 파일을 덮어쓰지 않고, 빠진 레퍼런스는 측정표에 안 들어간다
if ONLY in ("ref", "all"):
    os.makedirs(PREV, exist_ok=True)
    for f in glob.glob(f"{D}/ref-*.json") + glob.glob(f"{D}/ref-*.md"):
        os.replace(f, f"{PREV}/{os.path.basename(f)}")

def reuse(blog, log, stem):  # 온보딩(O4·O7a)이 이미 측정한 같은 글(blogId·logNo 일치)은 다시 받지 않는다
    cands = glob.glob(f"{PREV}/ref-*.json") if stem.startswith("ref-") else [f"{D}/{stem}.json"]
    for p in cands:
        try: d = json.load(open(p, encoding="utf-8")); s = d["stats"]
        except (OSError, ValueError, KeyError, TypeError): continue
        if str(s.get("blogId")) != str(blog) or str(s.get("logNo")) != str(log): continue
        md = p[:-5] + ".md"
        if not os.path.isfile(md):  # 온보딩은 .json만 저장한다 — markdown 필드로 .md를 만든다
            if not isinstance(d.get("markdown"), str): continue  # markdown도 없으면 다시 받는다
            open(md, "w", encoding="utf-8").write(d["markdown"])
        if p[:-5] != f"{D}/{stem}":  # 레퍼런스 번호가 바뀌었으면 새 이름으로 옮긴다(같은 글의 중복 파일 방지)
            os.replace(p, f"{D}/{stem}.json"); os.replace(md, f"{D}/{stem}.md")
        return True
    return False

failed, reused = [], 0
for blog, log, stem in jobs:
    if reuse(blog, log, stem):
        reused += 1; continue
    r = subprocess.run([sys.executable, "scripts/fetch_post.py", blog, log, "--json"], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        failed.append(f"{stem}: {r.stderr.strip()[:200]}"); continue
    data = json.loads(r.stdout)
    json.dump(data, open(f"{D}/{stem}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(f"{D}/{stem}.md", "w", encoding="utf-8").write(data["markdown"])
    time.sleep(0.5)
print("수집:", len(jobs) - len(failed), "/", len(jobs), f"(재사용 {reused})",
      f"| 자기 글(블로그 전체): {n_own}편 | 측정한 자기 글: {len(mine)}편")
print("경로:", "★ 레퍼런스 0 없음 — 기준 글(own-style) 없음" if star else "평소")
print("실패:", failed or "없음")
PY
```

**병렬화(선택)**: 이 수집은 읽기 전용이라 메인 세션이 서브에이전트(explore 또는 general-purpose) 2개로 나눠도 된다 —
하나는 첫 줄을 `ONLY=ref python3 - <<'PY'`로, 다른 하나는 `ONLY=own python3 - <<'PY'`로 바꿔 같은 스크립트를 실행한다.
`ref-*`와 `own-*`는 파일 접두어가 달라 **쓰기 경로가 겹치지 않는다**. 둘 다 끝나면 메인이 `ls work/design-system/`로 개수를 확인한다.
레퍼런스 측정이 하나라도 실패하면 그 레퍼런스는 규칙 근거로 쓸 수 없으므로 원인(URL·구형 에디터 등)을 8단계 보고에 적는다.

산출물: `work/design-system/ref-<n>-<blogId>.{json,md}` × 레퍼런스 수, `own-<logNo>.{json,md}` × 최대 10.

## 3. 측정표 작성 → `work/design-system/measurements.md`

먼저 아래 스크립트로 **자동 열**을 계산한다(행 = 글, 레퍼런스 먼저·자기 글 다음, 맨 아래 중앙값 행 — 레퍼런스 중앙값, 자기 글 행이 있을 때만 자기 글 중앙값). 스크립트가 ★ 경로(`own-style` 없음 — 2단계와 같은 규칙)를 스스로 판정해 그때는 `own-*` 파일을 읽지 않는다(지난 측정 파일이 남아 있어도).

자동 열 정의:
| 열 | 계산 |
|---|---|
| chars, headings, bold_lines, images, quotes, links_naver_blog | stats 값 그대로 |
| 이미지당 글자수 | chars ÷ images (images=0이면 `-`) |
| 소제목당 글자수 | chars ÷ 소제목 수 (소제목 수 = headings, 0이면 `-`; 3단계 수동 보정 후 다시 계산) |
| bold_runs/1000자 | bold_runs × 1000 ÷ chars, 소수 1자리 |
| 끝부분 관련글 링크 수 | markdown에서 공백 제외 글자 위치가 전체의 마지막 20% 구간에 있는 `blog.naver.com` 출현 수 |
| 해요체 비율 **참고값(휴리스틱)** | 아래 "문장 나누기" 결과 중 끝이 `요`/`죠`인 문장 비율(%) |
| 평균 문장 길이 **참고값(휴리스틱)** | 같은 문장들의 공백 제외 글자수 평균 |

문장 나누기(네이버 글은 한 문장이 여러 문단으로 끊겨 있으므로 줄바꿈으로 나누지 않는다):
1) markdown을 빈 줄 기준 블록으로 나누고 이미지(`![`)·소제목(`#`)·표(`|`)·구분선(`---`) 블록은 버린다. 남은 블록은 줄 단위(목록 항목·인용 줄 각각)로 보고, 링크만 있는 줄과 줄 전체가 `**굵게**`인 줄(소제목 역할)은 버린다. 인용 `> `·목록 `- ` 접두어, `**`, 링크 문법(`[글](url)`→`글`), 맨 URL은 지운다.
2) 남은 줄을 공백으로 이어 붙이되, 줄 끝(뒤의 `ㅎ ㅋ ㅠ ~ ^ ♡` 이모티콘·문장부호를 떼고 본 끝)이 `다`/`요`/`죠`이면 거기서 문장을 끊는다(단 `보다`로 끝나면 비교 조사이므로 끊지 않는다). 쉼표는 떼지 않는다.
3) 이어 붙인 덩어리 안에서는 숫자 사이가 아닌 `.` `!` `?`(정규식 `(?<!\d)[.!?](?!\d)`)에서만 끊는다 — "1.5배"는 끊지 않는다.
4) 문장 끝의 `ㅎ ㅋ ㅠ ~ ^` 이모티콘·문장부호를 떼고 `요`/`죠`로 끝나면 해요체로 센다. 공백 제외 2자 미만 조각은 버린다.
이 두 열은 **참고값**이다. ②의 규칙은 숫자가 아니라 실제 예시 문장으로 정하고, 숫자는 근거 괄호에만 쓴다.

```bash
python3 - <<'PY'   # [ds-measure]
import json, glob, re, statistics as st, os
D = "work/design-system"
src = json.load(open("knowledge/source-blogs.json", encoding="utf-8"))
star = not any(r.get("role") == "own-style" for r in src.get("design_references", []))  # ★ — 자기 글 행·중앙값 행 없음
TAIL = r"[\sㅎㅋㅠㅜ~^♡♥.!?…;:)\]\-\u2600-\u27BF\U0001F000-\U0001FAFF]+$"
def sentences(md):
    blocks = []
    for blk in md.split("\n\n"):
        blk = blk.strip()
        if not blk or blk.startswith(("![", "#", "|", "---")): continue
        for b in blk.split("\n"):  # 목록 항목·인용 줄은 줄마다 따로 본다
            b = re.sub(r"^(> |- )", "", b.strip())
            if re.fullmatch(r"\*\*[^*]+\*\*", b): continue  # 줄 전체가 굵게 = 소제목 역할 줄
            b = b.replace("**", "")
            if re.fullmatch(r"(\s*(\[[^\]]*\]\([^)]*\)|https?://\S+))+\s*", b): continue  # 링크만 있는 줄
            b = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", b)
            b = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", b)
            b = re.sub(r"https?://\S+", "", b).strip()
            if re.sub(r"\s", "", b): blocks.append(b)
    out, buf = [], ""
    def cut(s):
        return [x.strip() for x in re.split(r"(?<=[.!?])(?<!\d[.!?])(?!\d)", s) if len(re.sub(r"\s", "", x)) >= 2]
    for b in blocks:
        buf = (buf + " " + b).strip()
        end = re.sub(TAIL, "", buf)
        if end.endswith(("다", "요", "죠")) and not end.endswith("보다"):  # "~보다"는 비교 조사
            out += cut(buf); buf = ""
    if buf: out += cut(buf)
    return out
def row(path):
    d = json.load(open(path, encoding="utf-8")); s, md = d["stats"], d["markdown"]
    nows = re.sub(r"\s", "", md); total = len(nows) or 1
    cut, late = total * 0.8, 0
    for m in re.finditer(r"blog\.naver\.com", md):
        if len(re.sub(r"\s", "", md[:m.start()])) >= cut: late += 1
    sents = sentences(md)
    yo = sum(1 for x in sents if re.sub(TAIL, "", x).endswith(("요", "죠")))
    c, h, im = s["chars"], s["headings"], s["images"]
    return {"글": os.path.basename(path)[:-5], "chars": c, "headings": h, "bold_lines": s["bold_lines"], "images": im,
            "이미지당 글자수": round(c / im) if im else "-", "소제목당 글자수": round(c / h) if h else "-",
            "bold_runs/1000자": round(s["bold_runs"] * 1000 / c, 1) if c else "-", "quotes": s["quotes"],
            "links_naver_blog": s["links_naver_blog"], "끝부분 관련글 링크 수": late,
            "해요체 비율(참고)": round(100 * yo / len(sents)) if sents else "-",
            "평균 문장 길이(참고)": round(st.mean(len(re.sub(r"\s", "", x)) for x in sents)) if sents else "-",
            "도입부 유형": "", "구조 유형": "", "소제목(수동)": ""}
refs = [row(p) for p in sorted(glob.glob(f"{D}/ref-*.json"))]
owns = [] if star else [row(p) for p in sorted(glob.glob(f"{D}/own-*.json"))]
if not (refs or owns):
    raise SystemExit("측정 대상 없음 — 측정표를 만들지 않는다(★ 레퍼런스 0 없음 경로)")
cols = list((refs or owns)[0].keys())
def med(rows, k):
    v = [r[k] for r in rows if isinstance(r[k], (int, float))]
    return round(st.median(v), 1) if v else "-"
lines = ["# 측정표", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
for r in refs + owns: lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
for name, rows in (("**중앙값(레퍼런스)**", refs), ("**중앙값(자기 글)**", owns)):
    if not rows: continue  # 없는 쪽 중앙값 행은 만들지 않는다(★ 경로 = 레퍼런스 중앙값 1행)
    lines.append("| " + " | ".join([name] + [str(med(rows, c)) if c not in ("도입부 유형", "구조 유형", "소제목(수동)") else "" for c in cols[1:]]) + " |")
open(f"{D}/measurements.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
print("경로:", "★ 레퍼런스 0 없음 — 자기 글 행 없음" if star else "평소")
PY
```

그다음 각 `ref-*.md`·`own-*.md`를 읽고 **수동 열 3개**를 채운다:

- **도입부 유형**(첫 3문장 기준, 하나만): `질문`(첫 3문장 안에 독자에게 묻는 `?` 문장) / `상황`(독자 처지 묘사 "~하시는 분", "~하려는데") /
  `통계`(숫자·수치로 시작) / `오해`(통념을 바로잡음 "~라고 알고 계신가요", "사실은") / 어느 것도 아니면 `기타:<한 단어>`.
- **구조 유형**(하나만): `절차형`(단계·순서 소제목) / `비교형`(A vs B·기준 비교) / `체크리스트형`(항목 나열 중심) / `Q&A형`(질문형 소제목) / `기타:<한 단어>`.
- **소제목(수동)**: `headings`가 0이거나 markdown을 읽어 보니 굵은 줄(`bold_lines`)이 소제목 역할을 하면, 소제목 역할을 하는 줄 수를 직접 센다.
  그렇지 않으면 `headings` 값을 그대로 쓴다. 이 열이 이후 모든 "소제목 수" 계산의 기준이다 → 값이 바뀐 행은 "소제목당 글자수"를 chars ÷ 소제목(수동)으로 고치고, 레퍼런스·자기 글 중앙값 행도 다시 계산한다.

수동 열을 채운 뒤 아래 스크립트로 "소제목(수동)" 기준 값을 다시 계산한다. 스크립트가 `measurements.md`의 **첫 표(측정표)만 직접 고친다** — 행마다 `소제목당 글자수` = chars ÷ 소제목(수동), 중앙값 행의 `소제목(수동)`·`소제목당 글자수`를 다시 쓰고(표 밖의 관찰 메모는 그대로), 5단계 소제목 수 공식 결과(레퍼런스 0이 있으면 그 값, 없으면 ★라 참고값)를 출력한다. `소제목(수동)` 칸이 빈 행은 건너뛰고 그 행 이름을 출력한다 — 채운 뒤 다시 실행한다.

```bash
python3 - <<'PY'   # [ds-headings]
import statistics as st
P = "work/design-system/measurements.md"
import json
text = open(P, encoding="utf-8").read().split("\n")
head = next(k for k, l in enumerate(text) if l.startswith("| 글 |"))
end = next((k for k in range(head + 1, len(text)) if not text[k].startswith("|")), len(text))
idx = [k for k in range(head, end) if text[k].startswith("| ")]  # 첫 표(측정표)만 — 메모 절의 다른 표는 건드리지 않는다
split = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
cols = split(text[idx[0]])
ci, hi, mi, pi = cols.index("글"), cols.index("chars"), cols.index("소제목(수동)"), cols.index("소제목당 글자수")
groups, empty = {"ref": [], "own": []}, []
for k in idx[1:]:  # 머리 줄 다음부터(구분 줄 `|---|`은 `| `로 시작하지 않아 idx에 없다)
    v = split(text[k])
    if v[ci].startswith("**"): continue
    if not v[mi].isdigit():
        empty.append(v[ci]); continue
    c, h = int(v[hi]), int(v[mi])
    v[pi] = str(round(c / h)) if h else "-"
    text[k] = "| " + " | ".join(v) + " |"
    groups["ref" if v[ci].startswith("ref-") else "own"].append((c, h))
med = lambda xs: round(st.median(xs), 1) if xs else "-"
for k in idx:
    v = split(text[k])
    key = "ref" if v[ci] == "**중앙값(레퍼런스)**" else "own" if v[ci] == "**중앙값(자기 글)**" else None
    if key and groups[key]:
        rows = groups[key]
        v[mi] = str(med([h for _, h in rows])); v[pi] = str(med([round(c / h) for c, h in rows if h]))
        text[k] = "| " + " | ".join(v) + " |"
open(P, "w", encoding="utf-8").write("\n".join(text))
print("고친 행:", len(groups["ref"]) + len(groups["own"]), "| 소제목(수동) 빈 행:", empty or "없음")
style = [r["logNo"] for r in json.load(open("knowledge/source-blogs.json", encoding="utf-8")).get("design_references", [])
         if r.get("role") == "own-style"]
m0 = next((int(split(text[k])[mi]) for k in idx if style and split(text[k])[ci] == f"own-{style[0]}"
           and split(text[k])[mi].isdigit()), None)
if m0 is not None:  # 값 출처 순서 1 — 레퍼런스 0(목차·문의 제외 환산은 3단계 끝에서 따로 확인)
    print("레퍼런스 0 소제목(수동)", m0, "→ 5단계 공식 min_h2 = 4, max_h2 =", max(7, m0))
elif groups["ref"]:
    R = st.median(h for _, h in groups["ref"])
    print("레퍼런스 중앙값 소제목(수동)", R, "→ ★ 경로: lint 키는 기본값 4~7 그대로 — 이 값은 근거 괄호에만")
PY
```

표 아래에 두 절을 덧붙인다(측정값은 measurements.md와 부록 B에만 둔다):

- **수동 열 판정 메모**(해당하는 글마다 한 줄): (a) 인용구 컴포넌트(`> 한 줄`)를 소제목으로 쓴 글은 headings가 0이고 quotes에 섞인다 → 인용구 소제목 줄을 직접 센다. (b) 첫 `##`가 글 제목 반복이면 소제목 수에서 1을 뺀다. (c) quotes 보정: 강조용 인용(요약 박스 등)만 세고 소제목 인용은 뺀다. (d) 끝부분 관련글 링크 수는 링크 하나가 URL 줄·제목 줄로 여러 번 잡힐 수 있다 → 실제 관련글 편수로 고쳐 적는다. (e) 구조 유형이 "기타:<한 단어>"인 홍보성 글(모집·행사 공지 등)은 자기 글 몇 편 중 몇 편인지 적는다(⑨ 근거).
- **관찰 메모**(구조 사실, 글마다 2~4줄): 커버·도입 방식·소제목 형태와 수·이미지 위치·강조 방식·끝 블록(관련글·해시태그·반복되는 고정 문장)의 순서(예, 가상: "도입은 질문 한 줄 + 굵은 결론 한 줄", "절마다 표 대신 ✔️ 줄 목록, 사진은 목록 바로 위"). 이 메모가 부록 A에서 숫자로 못 대는 메모 조각(예: "한눈에 들어오는 구성")의 근거가 된다. 자기 글이 있으면 ⑧ 관련 관찰(금칙어나 그것을 암시하는 표현, 보장·과장 표현이 이미 쓰였는지 — logNo와 함께)도 한 줄씩 적는다(⑧ 보강·검토 요청의 근거).
- 레퍼런스 0이 있으면 그 값을 lint 세는 법으로 환산한다 — chars는 목차 절·해시태그 줄·ㅤ 제외, 소제목은 목차·문의 제외, 이미지는 표지·업체소개 제외. 이 환산값이 5단계의 M0이다(④ `레퍼런스 0 환산(M)` 줄과 부록 B에 원값과 함께 적는다).

산출물: `work/design-system/measurements.md` (자동 열 + 수동 열 + 중앙값 행 + 수동 열 판정 메모 + 관찰 메모).

## 4. 메모 → 측정값 → 규칙 추적표 (부록 A 초안)

`design_references`의 `why`를 의미 단위 조각으로 나눈다. 레퍼런스 0(`own-style`)이 있으면 아래 기본 쪼개기 7조각을 쓰고(★ 레퍼런스 0 없음 경로면 이 7조각은 없다), 레퍼런스 1~n은 각 why를 같은 방식으로 쪼갠다(**모든 조각을 전부 덮어야 한다** — 조각 수를 세어 두고 7단계 점검에 쓴다).
`role: own-style` 레퍼런스 0은 메모가 "구조·모습 전체"이므로 각 조각을 `own-<logNo>.md`의 **관찰 메모(구조 사실)** + lint 세는 법으로 환산한 수치로 댄다. 레퍼런스 1~n의 조각은 종류에 맞는 측정값 열을 고른다 — 아래 `(예)` 행은 가상 메모로 보인 대응 예다:

| 레퍼런스 | 메모 조각 | 대응 측정값(measurements.md 열) | 들어갈 절 |
|---|---|---|---|
| 0 자기 글 | 목차 | 관찰 메모(목차 절·구분선 위치) | ③ |
| 0 자기 글 | 번호 소제목 | headings, 소제목(수동)(목차·문의 제외 환산), 소제목당 글자수 | ③, ④ |
| 0 자기 글 | 표·이모지 목록 | 관찰 메모(표 수·이모지 줄·💡 줄), bold_runs/1000자, quotes | ③, ④ |
| 0 자기 글 | (구조·모습) 절 끝 이미지 | images(표지·업체소개 제외 환산), 이미지당 글자수, 관찰 메모(이미지 위치·캡션) | ④, ⑤ |
| 0 자기 글 | FAQ | 관찰 메모(FAQ 절·문답 수) | ③, ⑥ |
| 0 자기 글 | 업체소개 이미지·지도·해시태그(프로필 `마무리 블록`에 든 항목만) | 관찰 메모(끝 블록 순서·해시태그 수) | ⑤, ⑥ |
| 0 자기 글 | (프로필 `톤` 결정) 합니다체 또는 해요체 | 해요체 비율(참고), ② 예시 문장 | ② |
| (예) 1 | 한눈에 들어오는 구성 | 소제목(수동), 구조 유형, 관찰 메모 | ③ |
| (예) 1 | 핵심 문장이 굵게 눈에 띔 | bold_runs/1000자, bold_lines, quotes | ④ |
| (예) 1 | 글 끝에 같은 블로그 다른 글 링크 | 끝부분 관련글 링크 수, links_naver_blog | ⑥ |
| (예) 2 | 대화하듯 자연스러운 흐름 | 해요체 비율(참고), 평균 문장 길이(참고), 도입부 유형 + ② 예시 문장 | ②, ⑦ |
| (예) 2 | 말을 거는 듯한 느낌 | 해요체 비율(참고), 관찰 메모(말 걸기 표현) | ② |
| (예) 3 | 소제목으로 잘게 나눠 읽기 쉬움 | 소제목(수동), 소제목당 글자수 | ③, ④ |
| (예) 3 | 소제목 바로 뒤 이미지로 먼저 보여 줌 | 관찰 메모(소제목 직후 이미지 여부), images vs 소제목(수동) | ③, ⑤ |
| (예) 3 | 사진과 글 비율이 알맞음 | 이미지당 글자수 | ④ |
| (예) 4 | 글과 사진이 번갈아 나옴 | 이미지당 글자수 | ④ |
| (예) 4 | 현장 사진이 중간중간 들어감 | images, 관찰 메모(현장 사진 위치) | ⑤ |

(같은 측정값을 쓰는 조각이라도 레퍼런스가 다르면 행은 따로 둔다 — 위 예의 3번 "사진과 글 비율"과 4번 "글과 사진이 번갈아"처럼.)
`design_references`가 바뀌었으면(추가·교체) 같은 방식으로 새 why를 쪼개 행을 더한다. why에 없는 내용으로 행을 만들지 않는다.
**자동 기입 why**: 온보딩에서 담당자가 이유를 적지 않은 레퍼런스는 why가 `(자동)`으로 시작한다(예: `(자동) 소제목으로 나눠 읽기 쉬움(소제목 6개) · 사진과 글 비율(이미지 8장 — 약 300자당 1장) · FAQ로 마무리`). ` · `로 나뉜 구절 하나가 조각 하나다 — 위 `(예)` 행의 같은 특징처럼 측정값 열을 고른다(소제목 → 소제목(수동)·소제목당 글자수, 사진과 글 비율 → 이미지당 글자수, FAQ → 관찰 메모). 1.1.0 온보딩의 숫자뿐인 자동 why(`소제목 n개·이미지 n장·FAQ 있음`)도 같은 세 특징으로 읽는다. 부록 A 메모 조각 칸에 `(자동)`을 남기고, 8단계 검토 요청에 "자동 기입 이유 n개 — 왜 이 글을 골랐는지 한 줄씩 알려 주시면 규칙이 더 정확해집니다" 한 줄을 넣는다.

각 행에 (a) **그 레퍼런스의 실제 수치**(예, 가상: "ref-1은 1000자당 굵게 11.5회로 레퍼런스 가운데 가장 많다") 또는 숫자가 없는 조각이면 관찰 메모의 구조 사실,
(b) 그것을 바꾼 **규칙 문장**(5단계에서 정한 수치 포함), (c) **반영 절**을 채운다. 이 표가 결과 문서의 "부록 A"가 된다.

산출물: 부록 A 표(5단계에서 문서에 넣음).

## 5. `[치환 변수]` 채우기 → `knowledge/design-system.md`

**생성 모드**: 작업 폴더의 `knowledge/design-system.md`(1단계에서 확인한 템플릿 초기값 — 없었으면 1단계가 플러그인 원본을 복사해 둠)를 **직접 고친다**. `references/fill-guide.md`의 자리별 표대로 `[치환 변수]`만 바꾸고, 그 밖의 문장·표·헤딩·순서는 바꾸지 않는다(fill-guide가 지우라고 한 줄·행·판만 지운다). 정본 주석, ④의 lint 블록, ④의 수치 원칙 주석은 남긴다.
**갱신 모드**: 1단계의 작업본 `work/design-system/proposed.md`에서 수치(④ 규칙·lint 블록 값·근거 괄호)와 부록 A·B의 행만 바꾼다(★ 표기 지우기는 ★ 절 끝 문단).

### 값 출처 순서 (모든 수치 규칙에 하나로 적용)

각 규칙의 값 V는 아래 순서에서 **처음으로 있는 것**을 쓴다:

1. **M0 — 레퍼런스 0(`own-style`) 환산값**: 구조·분량 특징(글자수·소제목 수·이미지 수·이미지당 글자수·소제목당 글자수·굵게). 다른 레퍼런스 메모와 겹치면 레퍼런스 0이 우선이다. lint 세는 법으로 환산한 값(3단계 끝).
2. **M — 그 특징을 가리키는 메모를 남긴 레퍼런스의 값**(자동 why 구절 포함). 메모 출처 레퍼런스가 둘 이상이면 그 값들의 범위를 쓴다(예: 이미지당 글자수 240·310 → 목표 310). 중앙값으로 희석하지 않는다 — 다른 레퍼런스는 그 특징 때문에 뽑힌 글이 아니다.
3. **R — 외부 레퍼런스 중앙값**(measurements.md `**중앙값(레퍼런스)**` 행, 소제목은 `소제목(수동)` 기준).
4. **초기값** — 아래 표의 「초기값」 열(= scaffold 문서에 이미 적혀 있는 값).

**★ 규칙(레퍼런스 0 없음)**: lint 키(`min_chars` `max_chars` `min_h2` `max_h2` `min_images` `min_sources` `tags_min` `tags_max` `kw_min_body` `kw_max_body` `title_min` `title_max`)는 **항상 초기값(lint 기본값)**이다 — 외부 레퍼런스 값(M·R)으로 lint 키를 바꾸지 않는다(외부 글은 다른 블로그라 분량을 강제할 근거가 아니다). 이때 M·R은 그 lint 키 줄의 근거 괄호에 참고로만 적고, 4~7 밖이면(예: R 소제목 9개) 8단계 검토 요청에 한 줄 올린다. 문장 규칙(아래 표 lint 키가 `—`인 행)은 2→3→4 순서 그대로다.

자기 글 중앙값(O)은 어느 순서에도 들어가지 않고 **근거 괄호에만** 병기한다(자기 글이 짧아도 규칙이 끌려 내려가지 않게). 레퍼런스 값을 측정할 수 없으면(예: 음영 배경색은 fetch_post가 추출하지 못함) 근거 괄호에 "측정 불가"와 대체 방법을 쓴다. 값 V가 `-`(분모 0 등)이면 다음 순서로 내려간다.
모든 수치 뒤 괄호에 근거를 쓴다: `(값 출처 → 공식 → 값)` — 예(가상 값): `(메모 출처 ref-1의 1000자당 굵게 4.0회 → 내림(4.0×0.7)~올림(4.0×1.3) = 2~6)`, `(초기값 = lint 기본값 — 측정 전; 참고 레퍼런스 중앙값 2900자)`.

> **계수는 조정 가능한 기본값이다.** 담당자 검토에서 바꾸면 이 표, ④의 근거 괄호, 부록 A의 해당 행을 **함께** 갱신한다.

| 규칙 | 공식(V = 값 출처 순서의 값) | 초기값(측정 없음) | 계수 근거 | lint 키 |
|---|---|---|---|---|
| 본문 글자수 하한 | max(1500, 100단위 내림(V_chars × 0.7)) | 1500 | 1500 = `lint_post.py` 기본 `min_chars`(바닥값). ×0.7 = 허용폭(플러그인 기본값) | `min_chars` |
| 본문 글자수 상한 | max(min_chars + 1000, 100단위 올림(V_chars × 1.4)) | 4000 | ×1.4 = 허용폭 상단. +1000 = 범위가 너무 좁아지지 않게 하는 최소 폭(플러그인 기본값) | `max_chars` |
| 소제목 수 | min_h2 = 4, max_h2 = max(7, 반올림(V_소제목(수동))) | 4~7 | 4~7 = ③ 소제목 규칙 범위(플러그인 설계값)이자 lint 기본값 | `min_h2`, `max_h2` |
| 이미지 수 하한 | max(3, min_h2 + 1, 올림(min_chars ÷ 이미지당 글자수 상한)) | 3 | 3 = lint 기본 `min_images`. min_h2 + 1 = 절마다 1장 + 1(표지·업체소개 제외). 글자수 항 = 하한 분량에서도 비율 상한을 지키는 장수 | `min_images` |
| 이미지당 글자수 | 목표 = 10단위 반올림(V), 상한 = 목표 × 1.5 | 목표 = 내림10(min_chars ÷ min_images) = 500, 상한 750 | ×1.5 = 허용폭(플러그인 기본값) | — |
| 권장 이미지 수(문장 규칙) | 올림(본문 글자수 ÷ 이미지당 글자수 목표), 단 min_images 이상 | 같은 식 | 계수 없음 | — |
| 소제목당 글자수 | 하한 = min(10단위 내림(V × 0.7), 내림10(max_chars ÷ min_h2)), 상한 = max(10단위 올림(V × 1.3), 올림10(min_chars ÷ max_h2)). ③ `소제목당 본문 <하한>~<상한>자` 형식 유지 — 상한 × max_h2가 min_chars에 못 미치면 글자수 lint를 지킬 수 없으므로 분량 범위에서 자른다 | 내림10(min_chars ÷ max_h2) ~ 올림10(max_chars ÷ min_h2) = 210~1000 | ×0.7~×1.3 = 허용폭(플러그인 기본값) | — |
| 강조(굵게) 빈도 | 1000자당 bold_runs: max(1, 내림(V × 0.7)) ~ max(2, 올림(V × 1.3)) | 1~5 | ×0.7~×1.3 = 허용폭. V = 강조 메모 출처 레퍼런스(또는 레퍼런스 0)의 bold_runs/1000자. 레퍼런스가 굵게를 거의 안 쓰면(V < 1) 초기값 | — |
| 음영 인용 | 글당 0 ~ max(1, V의 강조용 인용 수) | 0~1 | quotes 열은 인용구 소제목이 섞이므로 그대로 쓰지 않는다(3단계 수동 열 판정 메모 (c)의 보정값). "음영" 메모는 측정 불가 → `>` 인용으로 대체 | — |
| 관련글 링크 | ⑥ 문장 그대로(자기 글 2편 이상 + 주제에 맞는 글 2~3개, 맞는 글이 없거나 자기 글 2편 미만이면 생략) | 같음 | 플러그인 고정 규칙. 관련글 메모를 남긴 레퍼런스가 있으면 그 메모와 "끝부분 관련글 링크 수"를 근거로 병기만 | — |
| 출처 각주 | 2 | 2 | `lint_post.py` 기본 `min_sources`. 레퍼런스와 무관 — "지어내기 금지" 원칙 | `min_sources` |
| 태그 수 | 5~10 | 5~10 | lint 기본값. `knowledge/naver-seo-checklist.md`에 태그 기준이 있으면 그 값 | `tags_min`, `tags_max` |
| 제목·본문 키워드 | 20~40자, 3~8회 | 같음 | lint 기본값 = naver-seo-checklist.md | `title_*`, `kw_*` |
| 톤 | **정성 규칙**: 프로필 `톤` 값의 판 하나 + 예시 문장(자기 글 logNo, ★면 초기 예시) | — | 숫자(해요체 비율·평균 문장 길이 참고값)는 근거 괄호에만. 측정한 해요체 비율(참고)이 `톤`과 크게 어긋나면 8단계 검토 요청에 한 줄 | — |
| 정보:홍보 | 정보성 3 : 홍보 1 이하, 최근 4편 중 홍보 ≤ 1편 | 같음 | business-profile.md "## 홍보/정보 비율" 값. "4편" = 3:1 비율의 한 주기 | — |

②의 예시 문장은 `own-*.md`에서 **그대로 복사**하고 `(logNo)`를 붙인다 — 고치거나 지어내지 않는다.
부록 A에는 4단계 표를, 부록 B에는 measurements.md 중앙값 행(+ 레퍼런스 0 행·차이 행)과 "가장 큰 차이 3가지"를 넣는다(fill-guide 부록 A·B).
분량 목표: A4 4~6장. writer가 매번 읽는 문서이므로 길게 설명하지 말고 규칙을 짧은 문장·표로.

산출물: `knowledge/design-system.md` (생성 모드) 또는 `work/design-system/proposed.md` (갱신 모드).

## 6. lint 블록 배치

④ 헤딩 **바로 다음 줄**에 정확히 이 형식으로 한 줄(값은 정수, 5단계 공식 결과, ④ 규칙 문장의 숫자와 동일). scaffold 문서에 이 줄이 lint 기본값으로 이미 있으므로 **값만 바꾼다**(★ 경로면 그대로 둔다):

```
<!-- lint: min_chars=1500 max_chars=4000 min_h2=4 max_h2=7 min_images=3 min_sources=2 tags_min=5 tags_max=10 kw_min_body=3 kw_max_body=8 title_min=20 title_max=40 -->
```

(위 숫자는 lint 기본값을 넣은 형식 예시일 뿐이다. 실제 값은 측정에서 계산한다.)
`scripts/lint_post.py`는 파일에서 **처음 나오는** `<!-- lint:` 주석 하나만 읽고 `키=정수`만 인식한다. 따라서 파일 안 다른 곳(정본 주석·다른 절·부록)에
`<!-- lint:`로 시작하는 주석을 두지 않는다. 다른 스킬이 키를 추가할 수 있으므로(예: SEO 키), 갱신 모드에서는 기존 블록에 있던 다른 키를 지우지 않는다.

산출물: ④의 lint 블록 1줄.

## 7. 자체 점검

아래를 전부 확인하고 하나라도 실패하면 고친 뒤 다시 확인한다(대상 파일 F = `knowledge/design-system.md` 또는 갱신 모드의 proposed 파일).

```bash
F=knowledge/design-system.md   # 갱신 모드: F=work/design-system/proposed.md
NFRAG=<4단계 표의 조각 수>       # 레퍼런스 0 기본 7조각 + 레퍼런스 1~n의 why 조각 수 (★ 레퍼런스 0 없음: 외부 레퍼런스 why 조각 수만 — 0이면 부록 A 행 수 점검 생략)
python3 - "$F" "$NFRAG" <<'PY'   # [ds-check]
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
heads = ["## ① ", "## ② ", "## ③ ", "## ④ ", "## ⑤ ", "## ⑥ ", "## ⑦ ", "## ⑧ ", "## ⑨ ", "## 부록 A", "## 부록 B", "## 측정 기록"]
print("헤딩 누락:", [h for h in heads if h not in t] or "없음")
blocks = re.findall(r"<!--\s*lint:(.*?)-->", t, re.S)
print("lint 블록 수(1이어야 함):", len(blocks))
s4, s5 = t.find("## ④"), t.find("## ⑤")
first = t.find("<!-- lint:")
print("lint 블록이 ④ 안:", s4 < first < s5)
print("lint 값:", dict(re.findall(r"(\w+)=(\d+)", blocks[0])) if blocks else None)
code_free = re.sub(r"`[^`\n]*`", "", t)  # 인라인 코드 안의 [출처 필요] 같은 표기는 치환 변수가 아니다
ph = re.findall(r"(?<![\[!\]])\[(?![\[\]])[^\[\]\n]+\](?![\(\]])", code_free)  # [[…]]·[글](url)·![](…) 제외
print("남은 [치환 변수](0이어야 함):", sorted(set(ph)) or "없음")
print("남은 {{자리표시}}(옛 템플릿):", re.findall(r"\{\{[^}]*\}\}", t) or "없음")
print("톤 판 하나만:", "OK" if ("**합니다체 판**" in t) != ("**해요체 판**" in t) else "실패 — `톤`에 맞지 않는 판을 지울 것")
print("③ '소제목당 본문 N~M자' 문구:", "OK" if re.search(r"소제목당 본문 \d+~\d+자", t) else "없음 — blog-draft-writer 자체 점검이 멈춘다")
words = []
inside = False
for line in open("knowledge/business-profile.md", encoding="utf-8"):
    if line.startswith("## "): inside = line.strip() == "## 금칙어"
    elif inside: words += re.findall(r"`([^`]+)`", line)
sec8 = t[t.find("## ⑧"):t.find("## ⑨")]
print("⑧에 빠진 금칙어:", [w for w in words if w not in sec8] or "없음")
a = t[t.find("## 부록 A"):t.find("## 부록 B")]
rows = [l for l in a.splitlines() if l.startswith("|") and not re.match(r"^\|[\s|:-]+\|$", l)][1:]
need = int(sys.argv[2])
print(f"부록 A 행 수({need} 이상이어야 함):", len(rows), "OK" if len(rows) >= need else "부족") if need else print("부록 A 행 수: 점검 생략(조각 0)")
n = len(re.sub(r"\s", "", t))
print("문서 공백 제외 글자수:", n, "OK" if n <= 12000 else "경고: 12,000자 초과 — A4 4~6장 목표, 설명을 줄일 것")
PY
```

그리고 lint가 실제로 이 값을 읽는지 확인한다(아무 짧은 샘플로 chars 규칙 문자열만 본다):

```bash
mkdir -p work/design-system/_lintcheck && printf -- '---\ntitle: t\n---\n본문\n' > work/design-system/_lintcheck/sample.md
python3 scripts/lint_post.py work/design-system/_lintcheck/sample.md --stage draft --json | python3 -c "import json,sys; print([c['rule'] for c in json.loads(sys.stdin.buffer.read().decode('utf-8'))['checks'] if c['id']=='chars'])"
rm -rf work/design-system/_lintcheck
```
(출력 범위가 lint 블록의 `min_chars~max_chars`와 같아야 한다. lint는 `knowledge/`만 읽으므로 **갱신 모드에서는 이 확인을 8단계 4번(승인·복사) 뒤에 한다.**)

눈으로 확인할 목록:
- [ ] ⑧ 금칙어 절에 business-profile.md 금칙어 **전부**(위 스크립트 "빠진 금칙어: 없음").
- [ ] ⑦ 변주 축: 프로필 `고객 지역`이 있으면 **4개**(도입부 유형·구조 템플릿·지역 키워드 조합·제목 지역 `title_region`), 없으면 2개(도입부 유형·구조 템플릿)이고 region·title_region 행이 없음 + `type`(축 아님), `cta` 축 없음, `title_region` 로테이션(고객 지역이 있을 때: 최근 4편에 안 쓰인 첫 고객 지역), "소제목 수는 변주 축이 아니다", "최근 5편(work/variation-log.md)과 겹치지 않게"(최근 5줄 각각과 4개 축 중 2개 이상 다름 — 고객 지역이 없으면 2개 축 중 1개 이상), 로그 7열(`… | region | title_region` — 고객 지역이 없으면 두 열은 `-`).
- [ ] ⑤에 "텍스트 렌더링 금지"(예외 = 표지 `00-cover.png` 합성 제목, AI 배경엔 글자 없음), "얼굴 클로즈업 금지", "정보성 = AI 허용"(프로필 `이미지 소스`에 `stock`이 있으면 스톡 사진도 허용), "홍보성 = 실사진" 4개 모두 + 본문 이미지 캡션 없음 + 절 끝 배치 + (프로필 `마무리 블록`에 `소개이미지`가 있을 때만) `photos/business-intro.png` 고정 자산(재사용 금지 예외).
- [ ] ⑥ 관련글 항목이 scaffold 문장 그대로(자기 글 **2편 이상**이면 주제에 맞는 글 2~3개 — 맞는 글이 없으면 생략 + `related: none`, 2편 미만이면 생략). **편수를 문서에 적지 않았음**("0편 → 생략"처럼 생성 시점의 수로 바꾸지 않는다 — 자기 글 수는 글마다 blog-run Step 0이 센다) + 고정 마무리 블록 순서 — 프로필 `마무리 블록`에 든 항목만 `문의헤딩`(`## 📞 <문의 헤딩 문구>: <연락처>`) → `소개이미지`(business-intro.png) → `장소카드`(`:::place <장소 검색어>:::`) → `해시태그`(`**#태그…**`) 순서, 줄글 CTA 없음, 장소 검색어는 business-profile.md 표에서(`장소카드`일 때).
- [ ] ⑧에 출처 형식 규칙(`(출처: URL)` 단독 괄호만, 조항·시행일은 문장 본문에, lint `source_format`, 업로드본에서 제거).
- [ ] ⑨에 정보성 3 : 홍보 1 비율 + 근거 "최근 4편(variation-log.md의 type 열) 중 홍보 ≤ 1편; 로그가 없으면 gates.md ## 선택의 유형".
- [ ] ⑦에 `variation:` 기록 키로 `type`(정보|홍보)·`title_region` 포함(고객 지역이 없으면 `title_region: -`).
- [ ] ④ 규칙 문장의 숫자 = lint 블록의 숫자(키마다 대조).
- [ ] 부록 A가 **레퍼런스 전부 × why 조각 전부**를 덮음(4단계 표의 행이 모두 있음), 각 행에 실제 수치 또는 관찰 사실.
- [ ] ② 톤 절에 프로필 `톤`에 맞는 판 하나만 남아 있음(합니다체 판 또는 해요체 판의 허용/금지 종결 표). 예시 문장마다 `(logNo)`가 있고 해당 `own-<logNo>.md`에 그 문장이 그대로 있음(`grep -F`로 확인 — ★ 레퍼런스 0 없음 경로는 초기 예시라 건너뜀).
- [ ] 모든 수치 규칙 뒤에 근거 괄호. ★ 경로면 lint 키 줄의 괄호가 `(초기값 = lint 기본값 — 측정 전…)`이고 lint 블록이 기본값 그대로.
- [ ] scaffold 상세 규칙이 남아 있음: ⑤ 표지 `1000×1000`, ③ `H2_FILLER_LINES`, ⑥ 1~6 순서, ⑦ 로테이션·7열 로그(문서를 새로 쓰지 않고 `[치환 변수]`만 채웠다면 그대로다).

산출물: 점검 통과한 문서.

## 8. 결과 보고 (사용자에게)

다음을 한국어로 보고한다:
1. 모드, 측정한 글 수(레퍼런스 n/전체, 자기 글 n), 수집 실패 목록. 1단계에서 `템플릿 교체:`가 나왔으면 "이전 템플릿은 <백업 경로>에 있습니다" 한 줄.
2. 변경 요약: 핵심 수치(글자수 범위·소제목 수·이미지 하한·이미지당 글자수·관련글) 한 줄씩, 근거 포함.
   갱신 모드면 `diff -u work/design-system/design-system.prev-<날짜>.md work/design-system/proposed.md`를 절 단위로 요약(바뀐 수치·추가/삭제 문장).
3. **담당자 검토 요청** 문구 — 그대로 포함:
   > 담당자님, 디자인 시스템 초안을 확인해 주세요. 특히 세 가지를 봐 주세요.
   > 1) ② 톤 예시 문장이 평소 담당자님 말투가 맞는지 (아니면 바꾸고 싶은 문장을 알려 주세요)
   > 2) ④ 분량 범위(글자수·소제목 수·이미지 수)가 부담스럽지 않은지
   > 3) ⑧ 금칙·주의에 빠진 것이 없는지 (계약·브랜드상 쓰면 안 되는 표현이 더 있다면 알려 주세요)

   레퍼런스 0 없음 경로면 1)을 "② 톤 예시는 초기 예시입니다 — 첫 글을 쓴 뒤 실제 문장으로 바꿀 수 있습니다"로, 2)에 "분량 범위는 측정 전 초기값(lint 기본값)입니다 — 첫 글 뒤 갱신을 권장합니다"를 덧붙인다(★ 절 8행).
4. 갱신 모드: 사용자가 승인하면 `cp work/design-system/proposed.md knowledge/design-system.md` → 7단계의 lint 확인(샘플 chars 규칙) 실행. 승인 전에는 `knowledge/`를 바꾸지 않는다.

담당자의 답을 받아 고친 내용은 `knowledge/design-system.md`에 직접 반영하고 머리말 "담당자 검토"를 날짜로 바꾼다.

산출물: 보고 메시지(+ 갱신 모드 승인 후 `knowledge/design-system.md` 교체).
