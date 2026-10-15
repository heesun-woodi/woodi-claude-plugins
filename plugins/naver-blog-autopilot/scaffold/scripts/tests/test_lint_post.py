import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "lint_post.py")
sys.path.insert(0, os.path.dirname(HERE))
import lint_post  # noqa: E402

DESIGN = "# 디자인 시스템\n\n<!-- lint: min_chars=900 max_chars=6000 min_h2=3 max_h2=5 min_images=2 min_sources=1 tags_min=3 tags_max=6 -->\n"
PROFILE = "# 업체\n\n| 항목 | 내용 |\n|---|---|\n| 고객 지역 | 가나동, 다라동 (고객 많은 순) |\n\n## 금칙어\n\n- `금지어예시` — 변형 `금지어 예시`, `금지어예시 표현`도 금지\n- `무관한단어`\n\n## 다음 절\n\n- `섹션밖단어`\n"
ENV = "NAVER_BLOG_ID=example_blog\n"  # 작업 폴더 .env(knowledge/의 상위) — final·upload의 related_links 기준 블로그


TITLE = "가나동 선물포장 리본 묶기 순서, 처음이라면 이렇게 준비하세요"
FILL = "\u3164"


class LintPostTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = cls._tmp.name
        kd = os.path.join(cls.root, "knowledge")
        os.makedirs(kd)
        for name, body in (("design-system.md", DESIGN), ("business-profile.md", PROFILE), (os.path.join("..", ".env"), ENV)):
            with open(os.path.join(kd, name), "w", encoding="utf-8") as f:
                f.write(body)
        cls.imgs = []
        for i in range(1, 4):
            p = os.path.join(cls.root, f"img{i}.png")
            open(p, "wb").close()
            cls.imgs.append(p)
        cls.intro_img = os.path.join(cls.root, "business-intro.png")
        cls.cover_img = os.path.join(cls.root, "00-cover.png")
        for p in (cls.intro_img, cls.cover_img):
            open(p, "wb").close()
        sections = []
        for s in range(4):
            sents = " ".join(f"리본 묶기는 순서를 익히면 차분하게 해낼 수 있습니다 {s}-{i}." for i in range(14))
            src = f" (출처: https://www.law.go.kr/s{s})" if s < 2 else ""
            h2 = "선물 포장 소제목 1" if s == 0 else f"소제목 {s + 1}"
            sections.append(f"## {h2}\n\n**핵심** 선물 포장 {sents}{src}\n\n> 한 줄 요약\n")
        sections[0] += f"\n![캡션1]({cls.imgs[0]})\n"
        sections[1] += f"\n![캡션2]({cls.imgs[1]})\n"
        sections[2] += f"\n![캡션3]({cls.imgs[2]})\n"
        sections[3] += ("\n[관련글1](https://blog.naver.com/example_blog/1)\n"
                        "[관련글2](https://blog.naver.com/example_blog/2)\n")
        cls.body = "# 선물포장 리본 묶기 순서\n\n" + "\n".join(sections)
        cls.fm = (f"---\ntitle: {TITLE}\nkeyword: 선물 포장\ncategory: 예시상회\n"
                  "tags: [선물포장, 리본묶기, 가나동선물포장, 다라동선물포장, 포장준비물]\n"
                  "variation: {structure: 절차형, intro: 상황, title_region: 가나동}\n---\n")
        cls.good = cls.fm + cls.body

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def write(self, name, text):
        p = os.path.join(self.root, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def run_lint(self, text, stage="final", name="post.md"):
        res, _ = lint_post.lint_file(self.write(name, text), stage)
        return res

    def failed(self, res):
        return sorted(c["id"] for c in res["checks"] if c["result"] == "FAIL")

    def test_good_final_passes(self):
        res = self.run_lint(self.good)
        self.assertEqual(self.failed(res), [], res)
        self.assertTrue(res["pass"])
        self.assertEqual(res["stats"]["images"], 3)

    def test_cli_exit_codes_and_json(self):
        ok = self.write("ok.md", self.good)
        r = subprocess.run([sys.executable, SCRIPT, ok, "--stage", "final", "--json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(json.loads(r.stdout)["pass"])
        bad = self.write("bad.md", self.good + "\n금지어 예시 안내\n")
        r = subprocess.run([sys.executable, SCRIPT, bad, "--stage", "final"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("forbidden", r.stdout)
        r = subprocess.run([sys.executable, SCRIPT, os.path.join(self.root, "none.md"), "--stage", "final"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_cp949_console_does_not_crash(self):
        # Windows 콘솔(cp949)에서 이모지·— 가 든 결과를 출력해도 UnicodeEncodeError 로 죽지 않는다
        p = self.write("cp949.md", self.good.replace("**핵심**", "💡 **핵심**", 1) + "\n금지어 예시 — 안내 📞\n")
        for args in (["--json"], []):
            r = subprocess.run([sys.executable, SCRIPT, p, "--stage", "final", *args], capture_output=True,
                               env=dict(os.environ, PYTHONIOENCODING="cp949"))
            self.assertEqual(r.returncode, 1, r.stderr.decode("utf-8", "replace"))   # 금칙어 FAIL(크래시 아님)
            self.assertNotIn(b"Traceback", r.stderr)
            out = r.stdout.decode("utf-8")
            if args:
                self.assertFalse(json.loads(out)["pass"])
            self.assertIn("forbidden", out)

    def test_forbidden_with_space_variant(self):
        res = self.run_lint(self.good + "\n여기가 금지어 예시 입니다\n")
        self.assertEqual(self.failed(res), ["forbidden"])
        detail = next(c["detail"] for c in res["checks"] if c["id"] == "forbidden")
        self.assertRegex(detail, r"줄 \d+")

    def test_related_placeholder_left(self):
        res = self.run_lint(self.good + "\n[[관련글]]\n")
        self.assertEqual(self.failed(res), ["related_links"])

    def test_empty_image(self):
        res = self.run_lint(self.good.replace(self.imgs[0], ""))
        self.assertEqual(self.failed(res), ["image_paths"])

    def test_frontmatter_missing_key(self):
        res = self.run_lint(self.good.replace("category: 예시상회\n", ""))
        self.assertEqual(self.failed(res), ["frontmatter"])

    def test_source_placeholder(self):
        res = self.run_lint(self.good + "\n포장비는 얼마입니다 [출처 필요]\n")
        self.assertEqual(self.failed(res), ["placeholder_sources"])

    def test_draft_without_frontmatter_passes(self):
        slot_body = self.body.replace(self.imgs[0], "").replace(self.imgs[1], "").replace(self.imgs[2], "")
        slot_body = slot_body.replace("![캡션1]()", "![슬롯: 교육장]()").replace("![캡션2]()", "![슬롯: 실습]()")
        res = self.run_lint(slot_body, stage="draft")
        self.assertEqual(self.failed(res), [], res)
        by = {c["id"]: c["result"] for c in res["checks"]}
        self.assertEqual(by["variation"], "SKIP")
        for cid in ("frontmatter", "title_keyword", "tags_count", "related_links", "image_paths", "h1_once",
                    "seo_keyword_body", "seo_keyword_h2", "seo_image_captions", "seo_title_length",
                    "title_region", "sources_stripped", "captions_empty", "cover_file", "closing_block", "h2_spacing"):
            self.assertEqual(by[cid], "SKIP")
        self.assertEqual((by["tone"], by["source_format"]), ("PASS", "PASS"))

    def test_defaults_without_knowledge(self):
        th = lint_post.load_thresholds(None)
        self.assertEqual(th["min_chars"], 1500)
        with self.assertRaises(ValueError):  # 금칙어는 기본값 없음 — business-profile.md가 없으면 멈춘다
            lint_post.load_forbidden(None)
        res = lint_post.lint_text("## a\n금지어 예시 안내\n", "draft", th, ["금지어예시"])
        self.assertIn("forbidden", self.failed(res))

    def test_forbidden_none_item(self):
        # 금칙어 절의 목록이 「- 없음」 하나뿐이면 금칙어 없음으로 통과, 자리표시만 남은 절·스캐폴드 템플릿은 지금처럼 멈춘다
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "business-profile.md")
            for item in ("- 없음", "- `없음`"):
                with open(p, "w", encoding="utf-8") as f:
                    f.write("# 업체\n\n## 금칙어\n\n금칙어가 없으면 없음 한 줄만 둡니다.\n\n" + item + "\n\n## 다음 절\n\n- `섹션밖단어`\n")
                self.assertEqual(lint_post.load_forbidden(d), [], item)
            with open(p, "w", encoding="utf-8") as f:
                f.write("# 업체\n\n## 금칙어\n\n- `[금칙어 1]`\n")
            with self.assertRaises(ValueError):
                lint_post.load_forbidden(d)
        with self.assertRaises(ValueError):
            lint_post.load_forbidden(os.path.join(os.path.dirname(os.path.dirname(HERE)), "knowledge"))
        res = lint_post.lint_text("## a\n재고 없음 안내\n", "draft", lint_post.load_thresholds(None), [])
        self.assertEqual(self.by_id(res)["forbidden"]["result"], "PASS")

    def test_headings_inside_code_fence_ignored(self):
        res = self.run_lint(self.good + "\n```\n## 코드 안 제목\n# 코드 안 h1\n```\n")
        self.assertEqual(self.failed(res), [])
        self.assertEqual(res["stats"]["h2_count"], 4)

    def test_loaders_apply_custom_values(self):
        kd = os.path.join(self.root, "knowledge")
        th = lint_post.load_thresholds(kd)
        self.assertEqual((th["min_chars"], th["max_h2"], th["tags_min"]), (900, 5, 3))
        fw = lint_post.load_forbidden(kd)
        self.assertIn("무관한단어", fw)
        self.assertNotIn("섹션밖단어", fw)
        self.assertEqual(self.failed(self.run_lint(self.good + "\n무관한단어\n")), ["forbidden"])
        self.assertEqual(self.failed(self.run_lint(self.good + "\n섹션밖단어\n")), [])

    def test_chars_fail(self):
        self.assertEqual(self.failed(self.run_lint(self.good + "\n" + "가" * 6000 + "\n")), ["chars"])

    def test_h2_fail(self):
        self.assertEqual(self.failed(self.run_lint(self.good + "\n## 다섯\n\n## 여섯\n")), ["h2_count"])

    def test_images_fail(self):
        t = self.good.replace(f"![캡션2]({self.imgs[1]})", "").replace(f"![캡션3]({self.imgs[2]})", "")
        self.assertEqual(self.failed(self.run_lint(t)), ["images"])

    def test_sources_fail(self):
        t = self.good.replace(" (출처: https://www.law.go.kr/s0)", "").replace(" (출처: https://www.law.go.kr/s1)", "")
        self.assertEqual(self.failed(self.run_lint(t)), ["sources"])

    def test_h1_fail(self):
        self.assertEqual(self.failed(self.run_lint(self.good + "\n# 두번째 제목\n")), ["h1_once"])
        self.assertEqual(self.failed(self.run_lint(self.good.replace("# 선물포장 리본 묶기 순서\n\n## ", "## ", 1))), ["h1_once"])

    def test_missing_stage_exit_2(self):
        r = subprocess.run([sys.executable, SCRIPT, self.write("s.md", self.good)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_comma_string_tags(self):
        t = self.good.replace(self.good.split("\n")[4], "tags: 가, 나, 다")
        res = self.run_lint(t)
        self.assertEqual(self.failed(res), [])
        self.assertEqual(res["stats"]["tags"], 3)

    def test_multiline_inline_tags(self):
        t = self.good.replace(self.good.split("\n")[4], "tags: [가,\n  나,\n  다]")
        res = self.run_lint(t)
        self.assertEqual(self.failed(res), [])
        self.assertEqual(res["stats"]["tags"], 3)

    def test_non_list_tags_fail(self):
        res = self.run_lint(self.good.replace(self.good.split("\n")[4], "tags: {a: b}"))
        self.assertEqual(self.failed(res), ["tags_count"])
        detail = next(c["detail"] for c in res["checks"] if c["id"] == "tags_count")
        self.assertEqual(detail, "리스트 형식 아님")

    def test_non_string_keyword_fail(self):
        res = self.run_lint(self.good.replace("keyword: 선물 포장", "keyword: [선물, 포장]"))
        self.assertEqual(self.failed(res), ["title_keyword"])

    def test_unclosed_frontmatter(self):
        res = self.run_lint(self.good.replace("---\n# 선물포장", "# 선물포장", 1))
        self.assertIn("frontmatter", self.failed(res))
        detail = next(c["detail"] for c in res["checks"] if c["id"] == "frontmatter")
        self.assertEqual(detail, "닫는 --- 없음")

    def test_bom_stripped(self):
        self.assertEqual(self.failed(self.run_lint("\ufeff" + self.good)), [])

    def test_unique_related_links(self):
        t = self.good.replace("example_blog/2", "example_blog/1")
        self.assertEqual(self.failed(self.run_lint(t)), ["related_links"])

    def test_decode_error_exit_2(self):
        p = os.path.join(self.root, "bin.md")
        with open(p, "wb") as f:
            f.write(b"\xff\xfe\x80\x81 bad")
        r = subprocess.run([sys.executable, SCRIPT, p, "--stage", "draft"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("UTF-8", r.stderr)

    def test_missing_knowledge_file_warning(self):
        with tempfile.TemporaryDirectory() as d:
            kd = os.path.join(d, "knowledge")
            os.makedirs(kd)
            with open(os.path.join(kd, "design-system.md"), "w", encoding="utf-8") as f:
                f.write(DESIGN)
            r = subprocess.run([sys.executable, SCRIPT, self.write("w.md", self.good), "--stage", "final",
                                "--knowledge", kd], capture_output=True, text=True)
            self.assertIn("business-profile.md", r.stderr)
            self.assertNotIn("design-system.md", r.stderr)

    def test_bracket_prefixed_title(self):
        res = self.run_lint(self.good.replace(f"title: {TITLE}", "title: [공지] 가나동 선물포장 리본 묶기 순서, 처음이라면 이렇게"))
        self.assertEqual(self.failed(res), [])

    def test_unclosed_bracket_title_does_not_swallow_keys(self):
        res = self.run_lint(self.good.replace(f"title: {TITLE}", "title: [공지 가나동 선물포장 리본 묶기 순서, 처음이라면 이렇게 준비"))
        self.assertEqual(self.failed(res), [])
        text = self.good.replace(f"title: {TITLE}", "title: [공지 선물포장")
        fm, _, _ = lint_post.parse_frontmatter(text.split("\n"))
        self.assertEqual(fm["title"], "[공지 선물포장")
        self.assertEqual(fm["keyword"], "선물 포장")

    def test_seo_stats(self):
        res = self.run_lint(self.good)
        self.assertEqual(res["stats"]["keyword_hits"], 4)
        self.assertEqual(res["stats"]["title_len"], len(TITLE))

    def test_seo_keyword_body_fail_low(self):
        res = self.run_lint(self.good.replace("**핵심** 선물 포장 ", "**핵심** "))
        self.assertEqual(self.failed(res), ["seo_keyword_body"])

    def test_seo_keyword_body_fail_high(self):
        res = self.run_lint(self.good + "\n" + "선물포장 완성\n\n" * 6)
        self.assertEqual(self.failed(res), ["seo_keyword_body"])

    def test_seo_keyword_body_ignores_urls_images_code(self):
        extra = ("\n<!-- 제목 B안: 선물포장 -->\n[링크](https://example.com/선물포장/선물포장)\n```\n선물포장\n```\n")
        self.assertEqual(self.run_lint(self.good + extra)["stats"]["keyword_hits"], 4)

    def test_seo_keyword_excludes_headings_quotes_inline_code(self):
        # 키워드가 h1/h2에만 + 본문 문단 2회 -> hits=2 (FAIL)
        t = self.good.replace("**핵심** 선물 포장 ", "**핵심** ")
        t = t.replace("**핵심** ", "**핵심** 선물 포장 ", 2)
        res = self.run_lint(t)
        self.assertEqual(res["stats"]["keyword_hits"], 2)
        self.assertEqual(self.failed(res), ["seo_keyword_body"])
        # 인용 줄·인라인 코드 안 키워드는 세지 않는다
        extra = "\n> 선물 포장 요약\n\n`선물포장` 코드\n"
        self.assertEqual(self.run_lint(self.good + extra)["stats"]["keyword_hits"], 4)

    def test_seo_keyword_h2_fail(self):
        res = self.run_lint(self.good.replace("## 선물 포장 소제목 1", "## 소제목 1"))
        self.assertEqual(self.failed(res), ["seo_keyword_h2"])

    def test_seo_image_captions_fail(self):
        self.assertEqual(self.failed(self.run_lint(self.good.replace("![캡션1]", "![]"))), ["seo_image_captions"])
        self.assertEqual(self.failed(self.run_lint(self.good.replace("![캡션1]", "![  ]"))), ["seo_image_captions"])

    def test_seo_title_length_fail(self):
        short = self.good.replace(f"title: {TITLE}", "title: 가나동 선물포장 리본 묶기")
        self.assertEqual(self.failed(self.run_lint(short)), ["seo_title_length"])
        long_t = self.good.replace("처음이라면 이렇게 준비하세요", "처음이라면 이렇게 준비하세요 " * 3)
        self.assertEqual(self.failed(self.run_lint(long_t)), ["seo_title_length"])

    def test_seo_thresholds_from_lint_block(self):
        th = dict(lint_post.DEFAULTS)
        self.assertEqual((th["kw_min_body"], th["kw_max_body"], th["title_min"], th["title_max"]), (3, 8, 20, 40))
        with tempfile.TemporaryDirectory() as d:
            kd = os.path.join(d, "knowledge")
            os.makedirs(kd)
            with open(os.path.join(kd, "design-system.md"), "w", encoding="utf-8") as f:
                f.write(DESIGN.replace("-->", "kw_min_body=1 kw_max_body=2 title_min=10 title_max=15 -->"))
            th = lint_post.load_thresholds(kd)
            self.assertEqual((th["kw_min_body"], th["kw_max_body"], th["title_min"], th["title_max"]), (1, 2, 10, 15))
            res = lint_post.lint_text(self.good, "final", th, [], ["가나동", "다라동"], blog_id="example_blog")
            self.assertEqual(self.failed(res), ["seo_keyword_body", "seo_title_length"])

    # ---- 업로드본(upload) 픽스처: 출처·캡션 제거, 목차·마무리 블록, 모든 ## 앞 ㅤ 줄 ----
    def upload_text(self):
        t = self.good
        for i in range(2):
            t = t.replace(f" (출처: https://www.law.go.kr/s{i})", "")
        for i in (1, 2, 3):
            t = t.replace(f"![캡션{i}]", "![]")
        h1 = "# 선물포장 리본 묶기 순서\n\n"
        head, rest = t.split(h1, 1)
        # 여백 계약: 직전 비어 있지 않은 줄 → ㅤ → 빈 줄 → ##
        rest = FILL + "\n\n" + re.sub(r"\n+(?=## )", "\n" + FILL + "\n\n", rest)
        toc = (f"도입 문단입니다.\n{FILL}\n\n## 📑 목차\n- 선물 포장 소제목 1\n- 소제목 2\n---\n")
        closing = (f"{FILL}\n\n## 📞 문의 안내: 000-0000-0000\n![]({self.intro_img})\n"
                   ":::place 예시상회:::\n\n**#선물포장 #다라동선물포장**\n")
        return head + h1 + toc + rest + closing

    def run_upload(self, text, cover=True):
        d = tempfile.mkdtemp(dir=self.root)
        if cover:
            os.makedirs(os.path.join(d, "images"))
            open(os.path.join(d, "images", "00-cover.png"), "wb").close()
        res, _ = lint_post.lint_file(self.write(os.path.join(d, "final.md"), text), "upload")
        return res

    def by_id(self, res):
        return {c["id"]: c for c in res["checks"]}

    def test_upload_good_passes(self):
        res = self.run_upload(self.upload_text())
        self.assertEqual(self.failed(res), [], res)
        by = self.by_id(res)
        for cid in ("sources", "seo_image_captions"):
            self.assertEqual(by[cid]["result"], "SKIP")
            self.assertIn("upload 단계 제외", by[cid]["detail"])
        for cid in ("sources_stripped", "captions_empty", "cover_file", "closing_block", "h2_spacing",
                    "tone", "source_format", "title_region"):
            self.assertEqual(by[cid]["result"], "PASS", cid)
        # 목차·문의 헤딩, 업체소개 이미지, 목차 안 키워드는 세지 않는다
        self.assertEqual((res["stats"]["h2_count"], res["stats"]["images"], res["stats"]["keyword_hits"]), (4, 3, 4))

    def test_upload_cli_stage(self):
        d = tempfile.mkdtemp(dir=self.root)
        os.makedirs(os.path.join(d, "images"))
        open(os.path.join(d, "images", "00-cover.png"), "wb").close()
        p = self.write(os.path.join(d, "final.md"), self.upload_text())
        r = subprocess.run([sys.executable, SCRIPT, p, "--stage", "upload", "--json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["stage"], "upload")
        r = subprocess.run([sys.executable, SCRIPT, p, "--stage", "publish"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_upload_sources_stripped_fail(self):
        t = self.upload_text().replace("도입 문단입니다.", "도입 문단입니다(출처: https://www.law.go.kr/x).")
        self.assertEqual(self.failed(self.run_upload(t)), ["sources_stripped"])

    def test_upload_captions_empty_fail(self):
        t = self.upload_text().replace(f"![]({self.imgs[0]})", f"![캡션1]({self.imgs[0]})")
        self.assertEqual(self.failed(self.run_upload(t)), ["captions_empty"])
        t = self.upload_text().replace(f"![]({self.intro_img})", f"![업체 소개]({self.intro_img})")
        self.assertEqual(self.failed(self.run_upload(t)), ["captions_empty"])

    def test_upload_cover_file_fail(self):
        res = self.run_upload(self.upload_text(), cover=False)
        self.assertEqual(self.failed(res), ["cover_file"])
        self.assertIn("파일 없음", self.by_id(res)["cover_file"]["detail"])
        t = self.upload_text().replace("도입 문단입니다.", f"![]({self.cover_img})\n도입 문단입니다.")
        res = self.run_upload(t)
        self.assertEqual(self.failed(res), ["cover_file"])
        self.assertEqual(res["stats"]["images"], 3)  # 00-cover는 이미지 수에서 제외

    def test_upload_cover_file_without_post_dir(self):
        res = lint_post.lint_text(self.upload_text(), "upload", lint_post.load_thresholds(None), [])
        self.assertIn("cover_file", self.failed(res))

    def test_upload_closing_block_fail(self):
        place = ":::place 예시상회:::\n"
        self.assertEqual(self.failed(self.run_upload(self.upload_text().replace(place, ""))), ["closing_block"])
        moved = self.upload_text().replace(place, "").replace(f"{FILL}\n\n## 📞", f"{place}{FILL}\n\n## 📞")
        self.assertEqual(self.failed(self.run_upload(moved)), ["closing_block"])
        no_tags = self.upload_text().replace("**#선물포장 #다라동선물포장**\n", "")
        res = self.run_upload(no_tags)
        self.assertEqual(self.failed(res), ["closing_block"])
        self.assertIn("**# 해시태그", self.by_id(res)["closing_block"]["value"])

    def test_upload_h2_spacing_pass_shape(self):
        t = self.upload_text()
        self.assertIn(f"도입 문단입니다.\n{FILL}\n\n## 📑 목차", t)
        self.assertIn(f"example_blog/2)\n{FILL}\n\n## 📞", t)
        self.assertEqual(self.by_id(self.run_upload(t))["h2_spacing"]["result"], "PASS")
        # 빌더 기본값 ㅤ×2(모든 ## 앞) · ㅤ×3도 PASS
        for n in (2, 3):
            tn = t.replace(f"{FILL}\n\n## ", f"{FILL}\n" * n + "\n## ")
            self.assertEqual(tn.count(f"{FILL}\n" * n + "\n## "), 6)  # 목차 + 소제목 4 + 문의
            self.assertEqual(self.failed(self.run_upload(tn)), [], n)

    def test_upload_h2_spacing_fail(self):
        # 구 형태: ㅤ 바로 아래 ## (빈 줄 없음)
        t = self.upload_text().replace(f"{FILL}\n\n## 소제목 2", f"{FILL}\n## 소제목 2")
        res = self.run_upload(t)
        self.assertEqual(self.failed(res), ["h2_spacing"])
        self.assertIn("## 소제목 2", self.by_id(res)["h2_spacing"]["detail"])
        t = self.upload_text().replace(f"{FILL}\n\n## 📑", f"{FILL}\n## 📑")
        self.assertEqual(self.failed(self.run_upload(t)), ["h2_spacing"])
        # ㅤ×2인데 빈 줄 없음
        t = self.upload_text().replace(f"{FILL}\n\n## 소제목 2", f"{FILL}\n{FILL}\n## 소제목 2")
        self.assertEqual(self.failed(self.run_upload(t)), ["h2_spacing"])
        # 빈 줄만 있고 ㅤ 없음
        t = self.upload_text().replace(f"{FILL}\n\n## 소제목 3", "\n## 소제목 3")
        self.assertEqual(self.failed(self.run_upload(t)), ["h2_spacing"])
        # 둘 다 없음
        t = self.upload_text().replace(f"{FILL}\n\n## 📞", "## 📞")
        self.assertEqual(self.failed(self.run_upload(t)), ["h2_spacing"])
        # ㅤ×2와 ## 사이 빈 줄 없음(ㅤ 위에 빈 줄)
        t = self.upload_text().replace(f"{FILL}\n\n## 소제목 3", f"\n{FILL}\n{FILL}\n## 소제목 3")
        self.assertEqual(self.failed(self.run_upload(t)), ["h2_spacing"])
        # 순서 뒤바뀜: 빈 줄 → ㅤ → ##
        t = self.upload_text().replace(f"{FILL}\n\n## 소제목 4", f"\n{FILL}\n## 소제목 4")
        self.assertEqual(self.failed(self.run_upload(t)), ["h2_spacing"])

    def test_final_skips_upload_only_checks(self):
        by = self.by_id(self.run_lint(self.good))
        for cid in ("sources_stripped", "captions_empty", "cover_file", "closing_block", "h2_spacing"):
            self.assertEqual((by[cid]["result"], by[cid]["detail"]), ("SKIP", "upload 단계 전용"))

    # ---- tone ----
    def test_tone_haeyo_fail(self):
        for bad in ("포장은 안전이 먼저예요.", "그렇게 하면 되죠.", "합격하니까요.", "**바로 시작해요**",
                    "제가 알려 드릴게요!", "질문이 있나요? 그럼 바로 물어봐요.", "교환은 7일 안에 받아요(출처: https://www.law.go.kr/x).",
                    "자세한 내용은 https://www.law.go.kr/x 에 있어요."):
            res = self.run_lint(self.body + f"\n{bad}\n", stage="draft")
            self.assertEqual(self.failed(res), ["tone"], bad)
            self.assertRegex(self.by_id(res)["tone"]["detail"], r"(요|죠)\**$")

    def test_tone_allowed_endings(self):
        ok = ("꼭 확인하세요.\n언제 교환해야 할까요?\n무엇을 준비할까요?\n**Q. 포장 없이 보내도 되나요?**\n"
              "매장에 꼭 가야 하나요? 그렇지 않습니다.\n합격 기준은 몇 점인가요?\n수수료는 얼마입니까?\n"
              "준비물이 있습니까?\n시간은 괜찮으세요?\n무엇이 다를까?\n✔️ 시험 시간 약 2시간 소요\n"
              "안전 점검이 필요.\n2.5kg 상자입니다.\n")
        res = self.run_lint(self.body + "\n" + ok, stage="draft")
        self.assertEqual(self.failed(res), [])
        self.assertEqual(res["stats"]["tone_hits"], 0)

    def test_tone_excludes_nonprose(self):
        extra = ("\n## 📑 목차\n- 이렇게 하면 돼요\n---\n\n## 쉬운 방법이에요\n\n> 쉬워요.\n\n| 항목 | 좋아요 |\n|---|---|\n\n"
                 "![쉬워요](x.png)\n\n<!-- 메모: 고쳐요 -->\n\n**#해요 #좋아요**\n\n"
                 "[예전 글: 쉬워요](https://blog.naver.com/example_blog/9)\n\n`쉬워요`\n")
        res = self.run_lint(self.body + extra, stage="draft")
        self.assertEqual(self.by_id(res)["tone"]["result"], "PASS", res)
        self.assertEqual(self.failed(res), [])

    # ---- source_format ----
    def test_source_format_single_paren_passes(self):
        by = self.by_id(self.run_lint(self.good))
        self.assertEqual(by["source_format"]["result"], "PASS")
        self.assertEqual(by["source_format"]["value"], "출처: 2건 / (출처: URL) 2건 / [출처]( 0건")

    def test_source_format_mixed_fail(self):
        for bad in ("제81조를 따릅니다(제81조제1항, 출처: https://www.law.go.kr/x).",
                    "제81조를 따릅니다(출처 : https://www.law.go.kr/x).",
                    "제81조를 따릅니다. 출처: https://www.law.go.kr/x",
                    "두 곳을 봅니다(출처: https://a.kr, https://b.kr).",
                    "링크로 답니다([출처](https://www.law.go.kr/x)).",
                    "괄호 URL입니다(출처: https://ko.wikipedia.org/wiki/상자_(용기))."):
            res = self.run_lint(self.body + f"\n{bad}\n", stage="draft")
            self.assertEqual(self.failed(res), ["source_format"], bad)

    # ---- title_region ----
    def test_title_region_fail_cases(self):
        cases = {"title_region: 마바동": "고객 지역", "title_region: 다라동": "title에", "": "없음"}
        for val, msg in cases.items():
            t = self.good.replace("title_region: 가나동", val) if val else self.good.replace(", title_region: 가나동", "")
            for stage in ("draft", "final"):
                res = self.run_lint(t, stage=stage)
                self.assertEqual(self.failed(res), ["title_region"], (val, stage))
                self.assertIn(msg, self.by_id(res)["title_region"]["detail"])

    def test_title_region_quoted_and_block_variation(self):
        t = self.good.replace("title_region: 가나동", 'title_region: "가나동"')
        self.assertEqual(self.failed(self.run_lint(t)), [])
        t = self.good.replace("variation: {structure: 절차형, intro: 상황, title_region: 가나동}",
                              "variation:\n  structure: 절차형\n  title_region: 가나동")
        self.assertEqual(self.failed(self.run_lint(t)), [])

    def test_load_regions(self):
        self.assertEqual(lint_post.load_regions(os.path.join(self.root, "knowledge")), ["가나동", "다라동"])
        with self.assertRaises(ValueError):  # 고객 지역 행이 없으면 기본값 없이 멈춘다
            lint_post.load_regions(None)

    # ---- 카운트 제외 규칙 ----
    def test_count_exclusions(self):
        base = self.run_lint(self.body, stage="draft")["stats"]
        extra = ("\n## 📑 목차\n- 목차 항목 하나\n- 목차 항목 둘\n---\n\n**#선물 #다라동**\n#태그 #둘\n"
                 + FILL * 3 + "\n![](/x/images/00-cover.png)\n![](/x/photos/business-intro.png)\n")
        st = self.run_lint(self.body + extra, stage="draft")["stats"]
        self.assertEqual((st["chars"], st["h2_count"], st["images"]), (base["chars"], base["h2_count"], base["images"]))
        st = self.run_lint(self.body + "\n## 📞 문의 안내: 000-0000-0000\n", stage="draft")["stats"]
        self.assertEqual(st["h2_count"], base["h2_count"])

    def test_keyword_excludes_toc_and_hashtags(self):
        extra = "\n## 📑 목차\n- 선물 포장 순서\n---\n\n**#선물포장 #다라동**\n"
        res = self.run_lint(self.good + extra)
        self.assertEqual(res["stats"]["keyword_hits"], 4)
        self.assertEqual(self.failed(res), [])

    def test_tone_question_endings(self):
        for ok in ("포장 없이 보내도 되나요?", "어디서 할까요?", "얼마입니까?", "몇 점인가요?", "어떠세요?"):
            res = self.run_lint(self.body + f"\n{ok}\n", stage="draft")
            self.assertEqual(self.failed(res), [], ok)
        for bad in ("해요?", "이거 해요?", "알고 계시죠?", "**Q. 오늘 접수돼요?**"):
            res = self.run_lint(self.body + f"\n{bad}\n", stage="draft")
            self.assertEqual(self.failed(res), ["tone"], bad)

    def test_upload_link_source_not_stripped(self):
        t = self.upload_text().replace("도입 문단입니다.", "도입 문단입니다([출처](https://www.law.go.kr/x)).")
        res = self.run_upload(t)
        self.assertEqual(self.failed(res), ["source_format", "sources_stripped"])
        self.assertEqual(self.by_id(res)["sources_stripped"]["value"], 1)

    def test_img_path_keeps_spaces(self):
        self.assertEqual(lint_post._img_path(' /a b/c d.png "제목 있음" '), "/a b/c d.png")
        self.assertEqual(lint_post._img_path("/a b/c.png"), "/a b/c.png")
        self.assertEqual(lint_post._img_path(""), "")

    def test_folder_with_spaces(self):
        d = os.path.join(self.root, "my photos")
        os.makedirs(d, exist_ok=True)
        spaced_img, spaced_intro = os.path.join(d, "img 1.png"), os.path.join(d, "business-intro.png")
        for p in (spaced_img, spaced_intro):
            open(p, "wb").close()
        t = self.good.replace(f"]({self.imgs[0]})", f"]({spaced_img} \"설명\")")
        self.assertEqual(self.failed(self.run_lint(t)), [])
        missing = os.path.join(d, "없는 파일.png")
        res = self.run_lint(self.good.replace(f"]({self.imgs[0]})", f"]({missing})"))
        self.assertEqual(self.failed(res), ["image_paths"])
        self.assertIn(f"파일 없음: {missing}", self.by_id(res)["image_paths"]["detail"])
        u = self.upload_text().replace(f"![]({self.intro_img})", f"![]({spaced_intro} \"업체\")")
        u = u.replace(f"]({self.imgs[1]})", f"]({spaced_img})")
        res = self.run_upload(u)
        self.assertEqual(self.failed(res), [])
        self.assertEqual((res["stats"]["images"], self.by_id(res)["closing_block"]["result"]), (3, "PASS"))


    # --- learned_avoid (knowledge/learned-preferences.md `## 피할 표현`, WARN 전용) ---
    def test_learned_avoid_skip_without_file(self):
        res = self.run_lint(self.good)
        self.assertEqual(self.by_id(res)["learned_avoid"]["result"], "SKIP")
        self.assertTrue(res["pass"])

    def learned_dir(self, avoid_lines):
        d = tempfile.mkdtemp(dir=self.root)
        kd = os.path.join(d, "knowledge")
        os.makedirs(kd)
        for name, body in (("design-system.md", DESIGN), ("business-profile.md", PROFILE), (os.path.join("..", ".env"), ENV)):
            with open(os.path.join(kd, name), "w", encoding="utf-8") as f:
                f.write(body)
        with open(os.path.join(kd, "learned-preferences.md"), "w", encoding="utf-8") as f:
            f.write("# 학습된 선호\n\n## 적용 중\n\n| id | 범주 | 규칙 | 근거 | 생긴 날 | 마지막 확인 |\n|---|---|---|---|---|---|\n"
                    "| L-001 | 톤 | `순서를 익히면` 표현을 쓰지 않는다. | F-0001 (001, 1회) | 2024-05-01 | 2024-05-01 |\n\n"
                    "## 피할 표현\n<!-- - `주석안표현` (L-999) -->\n" + avoid_lines + "\n## 다른 절\n\n- `절밖표현` (L-002)\n")
        return d

    def test_learned_avoid_warn_keeps_pass(self):
        d = self.learned_dir("- `순서를 익히면` (L-001)\n- `차분하게해낼` (L-003)\n")
        self.assertEqual(lint_post.load_learned_avoid(os.path.join(d, "knowledge")),
                         [("순서를 익히면", "L-001"), ("차분하게해낼", "L-003")])
        res, _ = lint_post.lint_file(self.write(os.path.join(d, "post.md"), self.good), "final")
        c = self.by_id(res)["learned_avoid"]
        self.assertEqual(c["result"], "WARN")
        self.assertEqual(c["value"], 112)  # 문장 56개 × 표현 2개(공백 무시)
        self.assertIn("순서를 익히면 (L-001) 56회", c["detail"])
        self.assertTrue(res["pass"])  # WARN은 pass에 영향 없음
        self.assertEqual(self.failed(res), [])
        r = subprocess.run([sys.executable, SCRIPT, os.path.join(d, "post.md"), "--stage", "draft"],
                           capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("결과: PASS (WARN: learned_avoid)", r.stdout)

    def test_learned_avoid_ignores_frontmatter_comments_and_other_sections(self):
        d = self.learned_dir("- `가나동 선물포장 리본 묶기 순서` (L-004)\n")
        self.assertEqual(lint_post.load_learned_avoid(os.path.join(d, "knowledge")),
                         [("가나동 선물포장 리본 묶기 순서", "L-004")])
        text = self.good + "\n<!-- 주석안표현 절밖표현 -->\n"
        res, _ = lint_post.lint_file(self.write(os.path.join(d, "post.md"), text), "final")
        c = self.by_id(res)["learned_avoid"]
        self.assertEqual((c["result"], c["value"]), ("PASS", 0))  # title(frontmatter)에만 있는 표현은 세지 않음

    def test_learned_avoid_empty_section_passes(self):
        d = self.learned_dir("")
        self.assertEqual(lint_post.load_learned_avoid(os.path.join(d, "knowledge")), [])
        res, _ = lint_post.lint_file(self.write(os.path.join(d, "post.md"), self.good), "draft")
        self.assertEqual(self.by_id(res)["learned_avoid"]["result"], "PASS")

    def test_scaffold_template_has_no_avoid_entries(self):
        kd = os.path.join(os.path.dirname(os.path.dirname(HERE)), "knowledge")
        self.assertEqual(lint_post.load_learned_avoid(kd), [])


    def test_learned_avoid_heading_prefix_first_backtick_short_and_cleanup(self):
        d = self.learned_dir("")
        kd = os.path.join(d, "knowledge")
        with open(os.path.join(kd, "learned-preferences.md"), "w", encoding="utf-8") as f:
            f.write("## 피할 표현 (WARN)\n- `핵심 선물` (L-001) — 예: `두번째백틱`\n- `선물` (L-002)\n"
                    "- `law.go.kr` (L-003)\n- `출처` (L-004)\n")
        self.assertEqual(lint_post.load_learned_avoid(kd),
                         [("핵심 선물", "L-001"), ("선물", "L-002"), ("law.go.kr", "L-003"), ("출처", "L-004")])
        res, _ = lint_post.lint_file(self.write(os.path.join(d, "post.md"), self.good), "final")
        c = self.by_id(res)["learned_avoid"]
        # `**핵심** 선물`은 ** 를 지우고 세며, URL·(출처: …) 안 글자는 세지 않는다
        self.assertEqual((c["result"], c["value"]), ("WARN", 4))
        self.assertIn("핵심 선물 (L-001) 4회", c["detail"])
        self.assertIn("짧아서 무시: 선물, 출처", c["detail"])
        self.assertNotIn("law.go.kr", c["detail"].split("짧아서")[0])
        self.assertTrue(res["pass"])

    def test_learned_avoid_non_utf8_file_skips_with_warning(self):
        d = self.learned_dir("")
        with open(os.path.join(d, "knowledge", "learned-preferences.md"), "wb") as f:
            f.write("## 피할 표현\n- `순서를 익히면` (L-001)\n".encode("cp949"))
        post = self.write(os.path.join(d, "post.md"), self.good)
        r = subprocess.run([sys.executable, SCRIPT, post, "--stage", "final", "--json"], capture_output=True,
                           text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("UTF-8로 읽을 수 없어 learned_avoid", r.stderr)
        c = next(x for x in json.loads(r.stdout)["checks"] if x["id"] == "learned_avoid")
        self.assertEqual(c["result"], "SKIP")


if __name__ == "__main__":
    unittest.main()
