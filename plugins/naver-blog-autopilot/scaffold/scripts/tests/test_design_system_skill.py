"""blog-design-system 스킬(SKILL.md에 든 스크립트)과 디자인 시스템 정본 템플릿(scaffold knowledge/design-system.md)
· 채우기 안내(references/fill-guide.md)의 계약 테스트.

SKILL.md의 `# [ds-…]` 표시가 붙은 heredoc 스크립트를 그대로 꺼내 임시 작업 폴더에서 실행한다(네트워크 없음 —
scripts/fetch_post.py·fetch_posts.py는 가짜로 바꾼다)."""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
PLUGIN = os.path.dirname(os.path.dirname(SCRIPTS))
SKILL = os.path.join(PLUGIN, "skills", "blog-design-system", "SKILL.md")
FILL = os.path.join(PLUGIN, "skills", "blog-design-system", "references", "fill-guide.md")
SCAFFOLD_DS = os.path.join(PLUGIN, "scaffold", "knowledge", "design-system.md")
DRAFT_SKILL = os.path.join(PLUGIN, "skills", "blog-draft-writer", "SKILL.md")
sys.path.insert(0, SCRIPTS)
import lint_post  # noqa: E402

# SKILL 7단계 자체 점검과 같은 치환 변수 판정(인라인 코드 밖의 [..] — [[..]]·[글](url)·![](..) 제외)
PH_RE = re.compile(r"(?<![\[!\]])\[(?![\[\]])[^\[\]\n]+\](?![\(\]])")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def placeholders(text):
    return list(dict.fromkeys(PH_RE.findall(re.sub(r"`[^`\n]*`", "", text))))


def skill_script(label):
    """SKILL.md에서 `# [label]` 표시가 붙은 heredoc 본문(다음 `PY` 줄 전까지)."""
    lines = read(SKILL).split("\n")
    start = next(i for i, ln in enumerate(lines) if f"# [{label}]" in ln and "<<'PY'" in ln)
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "PY")
    return "\n".join(lines[start + 1:end]) + "\n"


FAKE_FETCH_POSTS = """import json, os, sys
flag = sys.argv[1]
path = os.environ.get("FAKE_RSS" if flag == "--rss" else "FAKE_ALL", "")
print(open(path, encoding="utf-8").read() if path else "[]")
"""
FAKE_FETCH_POST = """import json, os, sys
open(os.environ["FAKE_LOG"], "a", encoding="utf-8").write(" ".join(sys.argv[1:3]) + "\\n")
if os.environ.get("FAKE_POST_FAIL"):
    sys.exit(1)
md = "## 소제목\\n\\n본문입니다. 다음 줄이에요.\\n"
print(json.dumps({"stats": {"blogId": sys.argv[1], "logNo": sys.argv[2], "title": "t", "chars": 1200, "paragraphs": 5,
                            "headings": 4, "images": 3, "bold_runs": 6, "bold_lines": 0, "quotes": 1, "links_out": 0,
                            "links_naver_blog": 0, "oglinks": 0}, "markdown": md}, ensure_ascii=False))
"""


def stats(blog, log, chars=1000, headings=4, images=2):
    return {"blogId": blog, "logNo": log, "title": "t", "chars": chars, "paragraphs": 5, "headings": headings,
            "images": images, "bold_runs": 4, "bold_lines": 0, "quotes": 0, "links_out": 0, "links_naver_blog": 0,
            "oglinks": 0}


def post(log, cat="", date="2026-10-01"):
    return {"blogId": "me", "title": f"글 {log}", "category": cat, "date": date, "logNo": log,
            "link": f"https://blog.naver.com/me/{log}"}


class SkillScriptsTest(unittest.TestCase):
    """2·3단계 스크립트: 자기 글 수 판정·.json 재사용·★ 경로 측정표·소제목 재계산."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        for d in ("knowledge", "scripts", os.path.join("work", "design-system")):
            os.makedirs(os.path.join(self.root, d), exist_ok=True)
        shutil.copy(os.path.join(SCRIPTS, "lint_post.py"), os.path.join(self.root, "scripts"))
        self.put("scripts/fetch_posts.py", FAKE_FETCH_POSTS)
        self.put("scripts/fetch_post.py", FAKE_FETCH_POST)
        self.log = os.path.join(self.root, "fetch.log")
        self.env = dict(os.environ, FAKE_LOG=self.log, PYTHONIOENCODING="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def put(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text if isinstance(text, str) else json.dumps(text, ensure_ascii=False))
        return p

    def sources(self, refs, own_style=None, info=""):
        dr = ([{"blogId": "me", "logNo": own_style, "url": "", "role": "own-style", "why": "구조·모습 전체"}]
              if own_style else []) + refs
        self.put("knowledge/source-blogs.json",
                 {"own_blog": {"blogId": "me", "categories": {"info": info}}, "design_references": dr})

    def run_script(self, label, only=None):
        env = dict(self.env, **({"ONLY": only} if only else {}))
        r = subprocess.run([sys.executable, "-"], input=skill_script(label), cwd=self.root, env=env,
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def fetched(self):
        return read(self.log).split("\n")[:-1] if os.path.isfile(self.log) else []

    # ---- 2단계 수집 ----
    def test_reuse_builds_md_from_onboarding_json(self):
        self.sources([{"blogId": "other", "logNo": "11", "url": "", "why": "(자동) FAQ로 마무리"}])
        self.put("work/design-system/ref-1-other.json", {"stats": stats("other", "11"), "markdown": "## 가\n\n본문\n"})
        out = self.run_script("ds-collect", only="ref")
        self.assertIn("재사용 1", out)
        self.assertEqual(self.fetched(), [])  # 다시 받지 않는다
        self.assertEqual(read(os.path.join(self.root, "work/design-system/ref-1-other.md")), "## 가\n\n본문\n")

    def test_reuse_refetches_when_json_has_no_markdown(self):
        self.sources([{"blogId": "other", "logNo": "11", "url": "", "why": "w"}])
        self.put("work/design-system/ref-1-other.json", {"stats": stats("other", "11")})
        out = self.run_script("ds-collect", only="ref")
        self.assertIn("재사용 0", out)
        self.assertEqual(self.fetched(), ["other 11"])

    def test_reuse_renames_when_reference_number_changed(self):
        self.sources([{"blogId": "a", "logNo": "1", "url": "", "why": "w"},
                      {"blogId": "other", "logNo": "11", "url": "", "why": "w"}])
        self.put("work/design-system/ref-1-other.json", {"stats": stats("other", "11"), "markdown": "m"})
        self.env["FAKE_POST_FAIL"] = "1"  # a/1은 받기 실패 — other/11만 재사용
        out = self.run_script("ds-collect", only="ref")
        self.assertIn("재사용 1", out)
        self.assertTrue(os.path.isfile(os.path.join(self.root, "work/design-system/ref-2-other.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.root, "work/design-system/ref-2-other.md")))

    def test_reuse_swapped_order_same_blog_keeps_both(self):
        # 같은 블로그의 레퍼런스 둘이 순서를 바꿔도 서로 덮어쓰지 않는다(재사용 2, 다시 받기 0)
        self.sources([{"blogId": "x", "logNo": "B", "url": "", "why": "w"},
                      {"blogId": "x", "logNo": "A", "url": "", "why": "w"}])
        self.put("work/design-system/ref-1-x.json", {"stats": stats("x", "A"), "markdown": "글 A"})
        self.put("work/design-system/ref-2-x.json", {"stats": stats("x", "B"), "markdown": "글 B"})
        out = self.run_script("ds-collect", only="ref")
        self.assertIn("재사용 2", out)
        self.assertEqual(self.fetched(), [])
        d = os.path.join(self.root, "work/design-system")
        self.assertEqual(json.loads(read(os.path.join(d, "ref-1-x.json")))["stats"]["logNo"], "B")
        self.assertEqual(read(os.path.join(d, "ref-2-x.md")), "글 A")

    def test_dropped_reference_leaves_measurement_table(self):
        # 재온보딩에서 빠진 레퍼런스의 지난 파일은 _prev/로 옮겨져 측정표·중앙값에 들어가지 않는다
        self.sources([{"blogId": "r", "logNo": "1", "url": "", "why": "w"}])
        self.put("work/design-system/ref-1-r.json", {"stats": stats("r", "1"), "markdown": "새 글이에요."})
        self.put("work/design-system/ref-2-old.json", {"stats": stats("old", "9"), "markdown": "옛 글이에요."})
        self.run_script("ds-collect", only="ref")
        self.run_script("ds-measure")
        t = read(os.path.join(self.root, "work/design-system/measurements.md"))
        self.assertIn("| ref-1-r |", t)
        self.assertNotIn("ref-2-old", t)
        self.assertTrue(os.path.isfile(os.path.join(self.root, "work/design-system/_prev/ref-2-old.json")))

    def test_own_count_uses_own_posts_json_not_category_match(self):
        # 리허설: --all 목록의 category가 비어 categories.info 매칭이 0편 — 그래도 자기 글은 6편이다
        self.sources([], own_style="5", info="정보")
        self.put("work/own-posts.json", [post(str(i)) for i in range(6)])
        out = self.run_script("ds-collect")
        self.assertIn("자기 글(블로그 전체): 6편", out)
        self.assertIn("경로: 평소", out)  # own-style이 있고 자기 글이 있으면 ★가 아니다
        self.assertEqual(self.fetched(), ["me 5"])  # 레퍼런스 0은 최신 10편 밖이어도 측정(--all 카테고리 빈 글은 채우지 않음)

    def test_star_when_no_own_style_even_with_posts(self):
        self.sources([{"blogId": "other", "logNo": "11", "url": "", "why": "w"}])
        self.put("work/own-posts.json", [post(str(i), "정보") for i in range(6)])
        self.put("rss.json", [post(str(i), "정보") for i in range(6)])
        self.env["FAKE_RSS"] = os.path.join(self.root, "rss.json")
        out = self.run_script("ds-collect")
        self.assertIn("경로: ★ 레퍼런스 0 없음 — 기준 글(own-style) 없음", out)
        self.assertIn("측정한 자기 글: 0편", out)
        self.assertEqual(self.fetched(), ["other 11"])  # 자기 글은 받지 않는다

    def test_stale_empty_own_posts_does_not_force_star(self):
        # 리뷰: ★로 시작한 블로그가 첫 글 뒤 own-style을 넣고 다시 돌렸는데 own-posts.json이 낡아 [] — 그래도 평소 경로
        self.sources([], own_style="5")
        self.put("work/own-posts.json", [])
        out = self.run_script("ds-collect")
        self.assertIn("경로: 평소", out)
        self.assertEqual(self.fetched(), ["me 5"])  # 기준 글은 측정한다

    def test_zero_posts_without_own_style_is_star(self):
        self.sources([{"blogId": "r", "logNo": "1", "url": "", "why": "w"}])
        self.put("work/own-posts.json", [])
        out = self.run_script("ds-collect")
        self.assertIn("경로: ★ 레퍼런스 0 없음 — 기준 글(own-style) 없음", out)
        self.assertIn("자기 글(블로그 전체): 0편", out)

    def test_collect_and_measure_agree_without_own_posts_file(self):
        # own-posts.json이 없어도 두 스크립트의 판정이 같다(own-style 유무만 본다)
        for style, want in ((None, "★"), ("7", "평소")):
            self.sources([{"blogId": "r", "logNo": "1", "url": "", "why": "w"}], own_style=style)
            self.put("work/design-system/ref-1-r.json", {"stats": stats("r", "1"), "markdown": "글이에요."})
            self.put("work/design-system/own-7.json", {"stats": stats("me", "7"), "markdown": "글입니다."})
            self.env["FAKE_POST_FAIL"] = "1"
            a = self.run_script("ds-collect")
            b = self.run_script("ds-measure")
            self.assertIn(f"경로: {want}", a)
            self.assertIn(f"경로: {want}", b)

    def test_own_count_falls_back_to_rss_and_empty_info_means_no_filter(self):
        self.sources([], own_style="9", info="")
        self.put("rss.json", [post("1", "일상"), post("2", "리뷰")])
        self.env["FAKE_RSS"] = os.path.join(self.root, "rss.json")
        out = self.run_script("ds-collect")
        self.assertIn("자기 글(블로그 전체): 2편 | 측정한 자기 글: 2편", out)
        self.assertEqual(sorted(self.fetched()), ["me 1", "me 2", "me 9"])

    def test_all_fallback_skips_unknown_category(self):
        self.sources([], own_style="9", info="정보")
        self.put("work/own-posts.json", [post(str(i)) for i in range(3)])
        self.put("rss.json", [post("1", "정보")])
        self.put("all.json", [post("1", "정보"), post("2", ""), post("3", "정보")])
        self.env.update(FAKE_RSS=os.path.join(self.root, "rss.json"), FAKE_ALL=os.path.join(self.root, "all.json"))
        out = self.run_script("ds-collect")
        self.assertIn("측정한 자기 글: 2편", out)  # 빈 category(2)는 카테고리 미상 — 채우지 않는다
        self.assertNotIn("me 2", self.fetched())

    # ---- 3단계 측정표 ----
    def measure_fixture(self, own_style):
        self.sources([{"blogId": "r", "logNo": "1", "url": "", "why": "w"}], own_style=own_style)
        self.put("work/own-posts.json", [post("1"), post("2")])
        self.put("work/design-system/ref-1-r.json", {"stats": stats("r", "1", 3000, 6, 10), "markdown": "본문이에요.\n"})
        self.put("work/design-system/own-7.json", {"stats": stats("me", "7", 1500, 4, 3), "markdown": "본문입니다.\n"})
        return os.path.join(self.root, "work/design-system/measurements.md")

    def test_measure_star_has_only_reference_median(self):
        out_path = self.measure_fixture(own_style=None)  # own-7.json은 지난 측정의 남은 파일
        out = self.run_script("ds-measure")
        t = read(out_path)
        self.assertIn("**중앙값(레퍼런스)**", t)
        self.assertNotIn("**중앙값(자기 글)**", t)
        self.assertNotIn("| own-7 |", t)
        self.assertIn("경로: ★", out)

    def test_measure_normal_has_both_medians(self):
        out_path = self.measure_fixture(own_style="7")
        self.run_script("ds-measure")
        t = read(out_path)
        self.assertIn("**중앙값(레퍼런스)**", t)
        self.assertIn("**중앙값(자기 글)**", t)
        self.assertIn("| own-7 |", t)

    def test_headings_script_rewrites_table(self):
        out_path = self.measure_fixture(own_style="7")
        self.run_script("ds-measure")
        t = read(out_path)
        cols = [c.strip() for c in t.split("\n")[2].strip().strip("|").split("|")]
        mi, pi = cols.index("소제목(수동)"), cols.index("소제목당 글자수")

        def set_manual(text, name, value):
            out = []
            for ln in text.split("\n"):
                v = [c.strip() for c in ln.strip().strip("|").split("|")] if ln.startswith("| ") else None
                if v and v[0] == name:
                    v[mi] = value
                    ln = "| " + " | ".join(v) + " |"
                out.append(ln)
            return "\n".join(out)
        t = set_manual(t, "ref-1-r", "10")  # chars 3000 ÷ 10 = 300
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(t + "\n## 관찰 메모\n- 그대로 남아야 함\n")
        out = self.run_script("ds-headings")
        rows = {r[0]: r for r in ([c.strip() for c in ln.strip().strip("|").split("|")]
                                  for ln in read(out_path).split("\n") if ln.startswith("| "))}
        self.assertEqual(rows["ref-1-r"][pi], "300")
        self.assertEqual((rows["**중앙값(레퍼런스)**"][mi], rows["**중앙값(레퍼런스)**"][pi]), ("10", "300"))
        self.assertIn("own-7", out)  # 소제목(수동)이 빈 행은 이름을 알려 준다
        self.assertIn("- 그대로 남아야 함", read(out_path))
        # 레퍼런스 0(own-7)의 소제목(수동)이 있으면 max_h2는 M0에서(레퍼런스 중앙값이 아니라) — 메모 절의 다른 표는 건드리지 않음
        t = set_manual(read(out_path), "own-7", "9") + "\n| 글 번호 | 메모 |\n|---|---|\n| 1 | 다른 표 |\n"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(t)
        out = self.run_script("ds-headings")
        self.assertIn("레퍼런스 0 소제목(수동) 9", out)
        self.assertIn("max_h2 = 9", out)
        self.assertIn("| 1 | 다른 표 |", read(out_path))

    def test_headings_star_prints_reference_median_as_reference_only(self):
        out_path = self.measure_fixture(own_style=None)
        self.run_script("ds-measure")
        t = read(out_path).replace("| ref-1-r | 3000 | 6 |", "| ref-1-r | 3000 | 6 |", 1)
        cols = [c.strip() for c in t.split("\n")[2].strip().strip("|").split("|")]
        mi = cols.index("소제목(수동)")
        rows = t.split("\n")
        for k, ln in enumerate(rows):
            if ln.startswith("| ref-1-r |"):
                v = [c.strip() for c in ln.strip().strip("|").split("|")]
                v[mi] = "9"
                rows[k] = "| " + " | ".join(v) + " |"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(rows))
        out = self.run_script("ds-headings")
        self.assertIn("★ 경로: lint 키는 기본값 4~7 그대로", out)


def skill_bash(label):
    """SKILL.md의 ```bash 블록 중 `# [label]` 줄이 든 것."""
    blocks = re.findall(r"```bash\n(.*?)```", read(SKILL), re.S)
    return next(b for b in blocks if f"# [{label}]" in b)


@unittest.skipIf(shutil.which("bash") is None or shutil.which("cmp") is None, "bash·cmp 없음")
class ModeScriptTest(unittest.TestCase):
    """1단계 [ds-mode]: 없음 → 원본 복사 / 지난 판 템플릿 → 원본으로 교체(백업 경로 출력) / 채운 문서 → 갱신 모드."""

    def run_mode(self, current):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "knowledge"))
            f = os.path.join(d, "knowledge", "design-system.md")
            if current is not None:
                with open(f, "w", encoding="utf-8") as fh:
                    fh.write(current)
            r = subprocess.run(["bash", "-c", skill_bash("ds-mode")], cwd=d, capture_output=True, text=True,
                               encoding="utf-8", env=dict(os.environ, CLAUDE_PLUGIN_ROOT=PLUGIN))
            self.assertEqual(r.returncode, 0, r.stderr)
            after = read(f)
            backups = sorted(os.listdir(os.path.join(d, "work", "design-system")))
        return r.stdout, after, backups

    def test_missing_copies_scaffold(self):
        out, after, _ = self.run_mode(None)
        self.assertIn("생성 모드(원본 복사)", out)
        self.assertEqual(after, read(SCAFFOLD_DS))

    def test_old_template_replaced_with_backup(self):
        old = "# [업체명] 블로그 콘텐츠 디자인 시스템\n\n| 버전 | [버전] |\n- 소제목당 본문 글자수: [레퍼런스 0 …]\n"
        out, after, backups = self.run_mode(old)
        self.assertIn("템플릿 교체: 이전 판 백업 work/design-system/design-system.template-prev-", out)
        self.assertIn("생성 모드", out)
        self.assertEqual(after, read(SCAFFOLD_DS))
        self.assertEqual(len([b for b in backups if b.startswith("design-system.template-prev-")]), 1)

    def test_current_template_untouched(self):
        out, after, backups = self.run_mode(read(SCAFFOLD_DS))
        self.assertNotIn("템플릿 교체", out)
        self.assertEqual(backups, [])

    def test_filled_document_is_update_mode(self):
        out, after, backups = self.run_mode("# 예시 블로그 콘텐츠 디자인 시스템\n\n| 버전 | 0.1 |\n")
        self.assertIn("갱신 모드", out)
        self.assertIn("proposed.md", backups)


class DesignSystemTemplateTest(unittest.TestCase):
    """정본 템플릿 하나(scaffold) + 채우기 안내 하나(fill-guide) — 둘이 어긋나지 않는지."""

    @classmethod
    def setUpClass(cls):
        cls.ds = read(SCAFFOLD_DS)
        cls.fill = read(FILL)
        cls.skill = read(SKILL)

    def test_single_template(self):
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(FILL), "design-system-template.md")))
        for root, dirs, files in os.walk(PLUGIN):
            dirs[:] = [d for d in dirs if not d.startswith(".")]  # .omc 같은 도구 폴더는 플러그인 내용이 아니다
            for name in files:
                if name.endswith((".md", ".py", ".sh", ".json")) and name != os.path.basename(__file__):
                    self.assertNotIn("design-system-template", read(os.path.join(root, name)), os.path.join(root, name))
        self.assertIn("references/fill-guide.md", self.skill)
        self.assertIn("scaffold/knowledge/design-system.md", self.skill)

    def test_every_placeholder_is_documented_in_fill_guide(self):
        ph = placeholders(self.ds)
        self.assertGreater(len(ph), 30)
        missing = [p for p in ph if f"`{p}`" not in self.fill]
        self.assertEqual(missing, [], "fill-guide.md에 안내가 없는 치환 변수")

    def test_fill_guide_mentions_only_real_placeholders(self):
        ph = set(placeholders(self.ds))
        named = set(re.findall(r"`(\[[^\]`]+\])`", self.fill)) - {"[출처 필요]", "[…]", "[치환 변수]"}  # 안내 문장 속 일반 표기
        self.assertEqual(sorted(named - ph), [], "scaffold에 없는 치환 변수를 안내함")

    def test_template_detection_and_headings(self):
        self.assertRegex(self.ds, r"(?m)^# .*\[업체명\]")
        self.assertRegex(self.ds, r"(?m)^\| *버전 *\| *\[버전\] *\|")
        heads = ["## ① ", "## ② ", "## ③ ", "## ④ ", "## ⑤ ", "## ⑥ ", "## ⑦ ", "## ⑧ ", "## ⑨ ",
                 "## 부록 A", "## 부록 B", "## 측정 기록"]
        self.assertEqual([h for h in heads if h not in self.ds], [])
        for h in heads:  # SKILL 7단계 점검의 헤딩 목록과 같다
            self.assertIn(f'"{h}"', self.skill)

    def test_lint_block_is_lint_defaults_inside_section4(self):
        blocks = re.findall(r"<!--\s*lint:(.*?)-->", self.ds, re.S)
        self.assertEqual(len(blocks), 1)
        self.assertTrue(self.ds.find("## ④") < self.ds.find("<!-- lint:") < self.ds.find("## ⑤"))
        kdir = os.path.dirname(SCAFFOLD_DS)
        self.assertEqual(lint_post.load_thresholds(kdir), lint_post.DEFAULTS)
        self.assertEqual(dict((k, int(v)) for k, v in re.findall(r"(\w+)=(\d+)", blocks[0])), lint_post.DEFAULTS)

    def test_section_length_phrase_readable_by_draft_writer(self):
        # blog-draft-writer 자체 점검이 쓰는 정규식으로 상한을 읽을 수 있어야 한다(채우기 전에도)
        pat = re.search(r're\.search\(r"(소제목당 본문[^"]+)"', read(DRAFT_SKILL)).group(1)
        m = re.search(pat, self.ds)
        self.assertIsNotNone(m)
        d = lint_post.DEFAULTS  # 초기값 = 내림10(min_chars ÷ max_h2) ~ 올림10(max_chars ÷ min_h2)
        lo, hi = re.search(r"소제목당 본문 (\d+)~(\d+)자", self.ds).groups()
        self.assertEqual((int(lo), int(hi)), (d["min_chars"] // d["max_h2"] // 10 * 10,
                                              math.ceil(d["max_chars"] / d["min_h2"] / 10) * 10))

    def test_image_ratio_initial_value_matches_formula(self):
        d = lint_post.DEFAULTS
        target = d["min_chars"] // d["min_images"] // 10 * 10
        self.assertIn(f"목표 {target}자 이하, 상한 {int(target * 1.5)}자", self.ds)

    def test_detail_rules_kept_in_template(self):
        for s in ("1000×1000", "H2_FILLER_LINES", "make_cover.py", ":::place", "variation-log.md", "related: none",
                  "초기 예시", "**합니다체 판**", "**해요체 판**"):
            self.assertIn(s, self.ds)

    def test_section6_related_rule_is_conditional_not_a_count(self):
        s6 = self.ds[self.ds.find("## ⑥"):self.ds.find("## ⑦")]
        self.assertIn("2편 이상", s6)
        self.assertIn("2편 미만", s6)
        self.assertIn("related: none", s6)
        self.assertNotRegex(s6, r"\d+편\s*(→|->)")  # "0편 → 생략" 같은 생성 시점 편수 금지

    def test_initial_examples_per_tone(self):
        for pan, ending in (("**합니다체 판**", "니다."), ("**해요체 판**", "요.")):
            seg = self.ds[self.ds.find(pan):]
            line = next(ln for ln in seg.split("\n") if ln.startswith("- 초기 예시"))
            self.assertIn(ending, line)


class SelfCheckScriptTest(unittest.TestCase):
    """7단계 [ds-check]: 채우기 전 템플릿은 치환 변수가 남았다고 알리고, 다 채운 문서는 0이라고 알린다."""

    def run_check(self, text, words="- 없음\n"):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "knowledge"))
            with open(os.path.join(d, "knowledge", "business-profile.md"), "w", encoding="utf-8") as f:
                f.write("## 금칙어\n" + words)
            path = os.path.join(d, "ds.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            r = subprocess.run([sys.executable, "-", path, "0"], input=skill_script("ds-check"), cwd=d,
                               capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_unfilled_template_reports_placeholders(self):
        out = self.run_check(read(SCAFFOLD_DS))
        self.assertIn("[업체명]", out)
        self.assertIn("톤 판 하나만: 실패", out)
        self.assertIn("lint 블록 수(1이어야 함): 1", out)

    def test_filled_document_passes(self):
        t = read(SCAFFOLD_DS)
        t = t[:t.find("**해요체 판**")] + t[t.find("공통:"):]  # 합니다체 판만 남김
        for p in placeholders(t):
            t = t.replace(p, "값")
        out = self.run_check(t, words="- `보장`\n")
        self.assertIn("남은 [치환 변수](0이어야 함): 없음", out)
        self.assertIn("톤 판 하나만: OK", out)
        self.assertIn("'소제목당 본문 N~M자' 문구: OK", out)
        self.assertIn("헤딩 누락: 없음", out)
        self.assertIn("⑧에 빠진 금칙어: ['보장']", out)  # [금칙어 목록]을 실제 단어로 채우지 않으면 잡힌다
        self.assertIn("부록 A 행 수: 점검 생략", out)


if __name__ == "__main__":
    unittest.main()
