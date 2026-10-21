import os
import contextlib
import io
import re
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import gen_image  # noqa: E402

PLAN = """# 이미지 계획 — posts/001-test
| 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수 |
|---|---|---|---|---|---|---|---|
| 01 | 제목 아래(표지) | 표지 | ai | gift box on a wooden table | 상자 포장 | images/01-cover.png | |
| 02 | ## 업체 소개 | 업체 CTA | photo | photos/a.jpg, photos/b.jpg | 매장 | (게이트 3에서 확정) | |
| 03 | ## 시험 | 시험 | AI | examiner seen from behind | 시험 장면 | | |
"""

PATTERNS = os.path.join(HERE, "..", "..", "..", "skills", "blog-image-director", "references", "prompt-patterns.md")


COVER_PLAN = """| 슬롯 | 위치 | 목적 | 유형 | 프롬프트 | 캡션(alt) | 파일 | 검수 |
|---|---|---|---|---|---|---|---|
| 00 | 표지(대표) | 표지 | cover | empty yard at dawn | 제목: 선물 포장 | images/00-cover.png | |
| 01 | ## 절차 | 절차 | ai | gift box | 절차 | | |
"""


class CoverRowTest(unittest.TestCase):
    def test_cover_row_targets_bg_and_keeps_file_cell(self):
        _, rows = gen_image.parse_plan(COVER_PLAN)
        sel = gen_image.select_ai_rows(rows)
        self.assertEqual([r["slot"] for r in sel], ["00", "01"])
        self.assertEqual(gen_image.target_name(sel[0]), "00-bg.png")
        only = gen_image.select_ai_rows(rows, gen_image.parse_only("00"))
        self.assertEqual([r["slot"] for r in only], ["00"])

    def test_dry_run_shows_cover(self):
        with tempfile.TemporaryDirectory() as d:
            plan = os.path.join(d, "images", "image-plan.md")
            os.makedirs(os.path.dirname(plan))
            with open(plan, "w", encoding="utf-8") as f:
                f.write(COVER_PLAN)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = gen_image.main([plan, "--dry-run", "--only", "00"])
            self.assertEqual(code, 0)
            self.assertIn("images/00-bg.png", buf.getvalue())
            self.assertIn("cover", buf.getvalue())
            with open(plan, encoding="utf-8") as f:
                self.assertEqual(f.read(), COVER_PLAN)


STOCK_PLAN = """| 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 검색어(stock) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수 | 출처 |
|---|---|---|---|---|---|---|---|---|
| 01 | ## 1 | 현장 | ai | gift box on a table | 상자 | | | |
| 02 | ## 2 | 현장 | stock | bicycle chain cleaning closeup | 체인 | | | |
| 03 | ## 3 | 업체 CTA | photo | photos/a.jpg | 매장 | | | |
"""


class SceneAndStockTest(unittest.TestCase):
    def test_default_scene_prefix(self):
        self.assertEqual(gen_image.DEFAULT_SCENE, "Korean everyday scene")
        self.assertTrue(gen_image.PROMPT_PREFIX.startswith("photorealistic, Korean everyday scene, no text"))
        p = gen_image.build_prompt("gift box on a table.")
        self.assertEqual(p, f"{gen_image.PROMPT_PREFIX}. gift box on a table. {gen_image.PROMPT_SUFFIX}.")
        self.assertEqual(gen_image.build_prompt("x", None), gen_image.build_prompt("x", ""))

    def test_profile_scene_replaces_only_scene_phrase(self):
        p = gen_image.build_prompt("gift box", "Korean neighborhood bicycle repair shop")
        self.assertTrue(p.startswith("photorealistic, Korean neighborhood bicycle repair shop, no text, no letters, "
                                     "no watermark, no close-up faces. gift box. natural light"), p)
        self.assertNotIn("Korean everyday scene", p)

    def test_load_base_scene_from_profile(self):
        with tempfile.TemporaryDirectory() as d:
            k = os.path.join(d, "knowledge")
            os.makedirs(k)
            self.assertEqual(gen_image.load_base_scene(k), "")  # 파일 없음
            self.assertEqual(gen_image.load_base_scene(None), "")
            prof = os.path.join(k, "business-profile.md")
            with open(prof, "w", encoding="utf-8") as f:
                f.write("| 항목 | 내용 |\n|---|---|\n| 이미지 기본 장면 | Korean neighborhood bicycle repair shop |\n")
            self.assertEqual(gen_image.load_base_scene(k), "Korean neighborhood bicycle repair shop")
            with open(prof, "w", encoding="utf-8") as f:
                f.write("| 항목 | 내용 |\n|---|---|\n| 이미지 기본 장면 | |\n")
            self.assertEqual(gen_image.load_base_scene(k), "")

    def _dry(self, profile_text=None, extra=()):
        with tempfile.TemporaryDirectory() as d:
            if profile_text is not None:
                os.makedirs(os.path.join(d, "knowledge"))
                with open(os.path.join(d, "knowledge", "business-profile.md"), "w", encoding="utf-8") as f:
                    f.write(profile_text)
            plan = os.path.join(d, "work", "posts", "001", "images", "image-plan.md")
            os.makedirs(os.path.dirname(plan))
            with open(plan, "w", encoding="utf-8") as f:
                f.write(STOCK_PLAN)
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                cwd = os.getcwd()
                os.chdir(d)
                try:
                    rc = gen_image.main([plan, "--dry-run", *extra])
                finally:
                    os.chdir(cwd)
            return rc, out.getvalue(), err.getvalue()

    def test_dry_run_uses_profile_scene(self):
        rc, out, _ = self._dry("| 항목 | 내용 |\n|---|---|\n| 이미지 기본 장면 | Korean home office desk |\n")
        self.assertEqual(rc, 0)
        self.assertIn("프롬프트: photorealistic, Korean home office desk, no text", out)

    def test_dry_run_default_scene_without_profile(self):
        rc, out, _ = self._dry(None)
        self.assertEqual(rc, 0)
        self.assertIn("프롬프트: photorealistic, Korean everyday scene, no text", out)

    def test_knowledge_option(self):
        with tempfile.TemporaryDirectory() as k:
            with open(os.path.join(k, "business-profile.md"), "w", encoding="utf-8") as f:
                f.write("| 항목 | 내용 |\n|---|---|\n| 이미지 기본 장면 | Korean cafe interior |\n")
            rc, out, _ = self._dry(None, ["--knowledge", k])
            self.assertEqual(rc, 0)
            self.assertIn("photorealistic, Korean cafe interior, no text", out)

    def test_stock_row_skipped_without_warning(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            _, rows = gen_image.parse_plan(STOCK_PLAN)
        self.assertEqual(err.getvalue(), "")
        self.assertIn("stock", gen_image.KINDS)
        self.assertEqual([r["kind"] for r in rows], ["ai", "stock", "photo"])
        self.assertEqual([r["slot"] for r in gen_image.select_ai_rows(rows)], ["01"])  # stock은 ai로 보지 않음
        with self.assertRaises(ValueError):
            gen_image.select_ai_rows(rows, gen_image.parse_only("02"))

    def test_dry_run_counts_stock_and_targets_only_ai(self):
        rc, out, err = self._dry(None)
        self.assertEqual(rc, 0)
        self.assertIn("슬롯 3개 (ai 1, photo 1, stock 1) → 이번 대상 ai 1개", out)
        self.assertNotIn("bicycle chain", out)
        self.assertNotIn("경고", err)

    def test_pexels_key_name_read_but_provider_unchanged(self):
        self.assertIn("PEXELS_API_KEY", gen_image.ENV_NAMES)
        self.assertNotIn("PEXELS_API_KEY", gen_image.KEY_NAMES.values())
        with tempfile.TemporaryDirectory() as d:
            env = os.path.join(d, ".env")
            with open(env, "w", encoding="utf-8") as f:
                f.write("PEXELS_API_KEY=pexels-fake-value\nOPENAI_API_KEY=sk-fake-openai-value-1234\n")
            vals = gen_image.read_env_values(env)
            self.assertEqual(vals["PEXELS_API_KEY"], "pexels-fake-value")
            provider, _, _, _ = gen_image.resolve_provider(gen_image.find_env(None, env))
            self.assertEqual(provider, "openai")
            with open(env, "w", encoding="utf-8") as f:
                f.write("PEXELS_API_KEY=pexels-fake-value\n")
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual(gen_image.resolve_provider(gen_image.find_env(None, env))[0], None)  # Pexels 키만으로는 제공자 없음


class GenImagePlanTest(unittest.TestCase):
    def test_parse_splits_ai_and_photo_and_only_filter(self):
        idx, rows = gen_image.parse_plan(PLAN)
        self.assertEqual([r["slot"] for r in rows], ["01", "02", "03"])
        ai = gen_image.select_ai_rows(rows)
        self.assertEqual([r["slot"] for r in ai], ["01", "03"])
        self.assertEqual([gen_image.target_name(r) for r in ai], ["01-cover.png", "03-exam.png"])
        only = gen_image.select_ai_rows(rows, gen_image.parse_only("3"))
        self.assertEqual([r["slot"] for r in only], ["03"])
        with self.assertRaises(ValueError):
            gen_image.select_ai_rows(rows, gen_image.parse_only("02"))  # photo
        with self.assertRaises(ValueError):
            gen_image.select_ai_rows(rows, gen_image.parse_only("09"))  # 없음
        out = gen_image.rewrite_plan(PLAN, idx, {ai[1]["line"]: "images/03-exam.png"})
        self.assertIn("| 03 | ## 시험 | 시험 | AI | examiner seen from behind | 시험 장면 | images/03-exam.png | |", out)
        self.assertIn("(게이트 3에서 확정)", out)

    @unittest.skipUnless(os.path.isfile(PATTERNS), "플러그인 밖(작업 폴더)에서는 prompt-patterns.md가 없음")
    def test_prefix_suffix_match_prompt_patterns(self):
        with open(PATTERNS, encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(re.search(r"- 접두: `([^`]+)`", text).group(1), gen_image.PROMPT_PREFIX)
        self.assertEqual(re.search(r"- 접미: `([^`]+)`", text).group(1), gen_image.PROMPT_SUFFIX)


    def test_parser_stops_at_blank_line_and_rejects_extra_cells(self):
        _, rows = gen_image.parse_plan(PLAN + "\n| 09 | x | 표지 | ai | p | c | | |\n")
        self.assertEqual(len(rows), 3)
        bad = PLAN.replace("| 03 | ## 시험 |", "| 03 | ## 시 | 험 |")
        with self.assertRaises(ValueError):
            gen_image.parse_plan(bad)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            _, rows = gen_image.parse_plan(PLAN.replace("| photo |", "| 사진 |"))
        self.assertIn("02", err.getvalue())
        self.assertEqual([r["slot"] for r in gen_image.select_ai_rows(rows)], ["01", "03"])


class EnvKeyTest(unittest.TestCase):
    def test_env_order_and_parsing(self):
        with tempfile.TemporaryDirectory() as d:
            work = os.path.join(d, "work")
            plan_dir = os.path.join(work, "posts", "001", "images")
            os.makedirs(plan_dir)
            plan = os.path.join(plan_dir, "image-plan.md")
            # plan 바로 위 .env에는 키가 없음 → 계속 찾아 작업 폴더 .env를 써야 함
            with open(os.path.join(work, "posts", ".env"), "w") as f:
                f.write("OTHER=1\n")
            with open(os.path.join(work, ".env"), "w") as f:
                f.write("# c\nexport GEMINI_API_KEY='abc 123' # note\n")
            cwd = os.getcwd()
            try:
                os.chdir(d)  # cwd/.env 없음
                with mock.patch.dict(os.environ, {}, clear=True):
                    env = gen_image.find_env(plan)
                    self.assertEqual(env["GEMINI_API_KEY"], "abc 123")
                    self.assertTrue(env["_source"].endswith(os.path.join("work", ".env")))
                    with open(os.path.join(d, ".env"), "w", newline="") as f:
                        f.write("GEMINI_API_KEY=xyz # inline\r\nIMAGE_PROVIDER=\"gemini\"\r\n")
                    env = gen_image.find_env(plan)
                    self.assertEqual(env["GEMINI_API_KEY"], "xyz")  # cwd가 plan 상위보다 먼저(CRLF도 허용)
                    self.assertEqual(env["IMAGE_PROVIDER"], "gemini")
            finally:
                os.chdir(cwd)


class PersistTest(unittest.TestCase):
    def test_partial_success_persists_after_exception_on_slot2(self):
        fake_google = types.ModuleType("google")
        fake_genai = types.ModuleType("google.genai")
        fake_genai.Client = lambda api_key, http_options=None: object()
        fake_genai.types = types.SimpleNamespace(HttpOptions=lambda **kw: kw)
        fake_google.genai = fake_genai
        with tempfile.TemporaryDirectory() as d:
            img = os.path.join(d, "posts", "001", "images")
            os.makedirs(img)
            plan = os.path.join(img, "image-plan.md")
            with open(plan, "w", encoding="utf-8") as f:
                f.write(PLAN.replace("images/01-cover.png", ""))
            env = os.path.join(d, ".env")
            with open(env, "w") as f:
                f.write("GEMINI_API_KEY=k\n")
            calls = []

            def fake_gen(client, model, prompt):
                calls.append(prompt)
                if len(calls) == 2:
                    raise KeyboardInterrupt
                return b"png"

            def fake_save(data, out, width):
                with open(out, "wb") as f:
                    f.write(data)
                return "원본"

            with mock.patch.dict(sys.modules, {"google": fake_google, "google.genai": fake_genai}), \
                    mock.patch.object(gen_image, "generate_one", fake_gen), \
                    mock.patch.object(gen_image, "save_image", fake_save), \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(KeyboardInterrupt):
                    gen_image.main([plan, "--env", env])
            with open(plan, encoding="utf-8") as f:
                text = f.read()
            self.assertIn("| 01 | 제목 아래(표지) | 표지 | ai | gift box on a wooden table | 상자 포장 | images/01-cover.png | |", text)
            self.assertNotIn("03-exam.png", text)
            self.assertTrue(os.path.isfile(os.path.join(img, "01-cover.png")))
            self.assertEqual([n for n in os.listdir(img) if n.endswith(".tmp")], [])


class QuotaTest(unittest.TestCase):
    def test_429_stops_remaining_slots_without_retry(self):
        class APIError(Exception):
            def __init__(self, code, message):
                super().__init__(message)
                self.code, self.message = code, message

        calls, seen_opts = [], {}

        class FakeClient:
            def __init__(self, api_key, http_options=None):
                seen_opts["http_options"] = http_options
                self.interactions = self

            def create(self, **kw):
                calls.append(kw)
                raise APIError(429, "RESOURCE_EXHAUSTED")

        fake_google = types.ModuleType("google")
        fake_genai = types.ModuleType("google.genai")
        fake_genai.Client = FakeClient
        fake_genai.types = types.SimpleNamespace(HttpOptions=lambda **kw: kw)
        fake_genai.errors = types.SimpleNamespace(APIError=APIError)
        fake_google.genai = fake_genai
        with tempfile.TemporaryDirectory() as d:
            img = os.path.join(d, "posts", "001", "images")
            os.makedirs(img)
            plan = os.path.join(img, "image-plan.md")
            with open(plan, "w", encoding="utf-8") as f:
                f.write(PLAN)
            env = os.path.join(d, ".env")
            with open(env, "w") as f:
                f.write("GEMINI_API_KEY=k\n")
            err = io.StringIO()
            with mock.patch.dict(sys.modules, {"google": fake_google, "google.genai": fake_genai}), \
                    mock.patch.object(gen_image.time, "sleep") as sleep, \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                rc = gen_image.main([plan, "--env", env])
            self.assertEqual(rc, 1)
            self.assertEqual(len(calls), 1)          # 재시도 없음, 슬롯 03은 시도하지 않음
            sleep.assert_not_called()
            self.assertEqual(seen_opts["http_options"], {"timeout": gen_image.HTTP_TIMEOUT_MS})
            self.assertIn("결제(Billing)", err.getvalue())
            self.assertIn("01, 03", err.getvalue())
            with open(plan, encoding="utf-8") as f:
                self.assertEqual(f.read(), PLAN)     # 성공 슬롯이 없으면 image-plan.md 그대로





FAKE_OPENAI = "sk-test-FAKEKEY0123456789abcdef"
FAKE_GEMINI = "AIzaFAKEKEY0123456789abcdef"


def tiny_png(w=30, h=20):
    """표준 라이브러리로 만든 RGB PNG(테스트용)."""
    import struct
    import zlib
    raw = b"".join(b"\x00" + b"\x80\x90\xa0" * w for _ in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class FakeResp:
    def __init__(self, payload):
        self._body = gen_image.json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(status, payload):
    import urllib.error
    body = gen_image.json.dumps(payload).encode("utf-8")
    return urllib.error.HTTPError("https://example.invalid", status, "err", {}, io.BytesIO(body))


class ResolveProviderTest(unittest.TestCase):
    def test_priority_table(self):
        both = {"GEMINI_API_KEY": FAKE_GEMINI, "OPENAI_API_KEY": FAKE_OPENAI, "_source": "x/.env"}
        r = gen_image.resolve_provider
        self.assertEqual(r(both), ("gemini", FAKE_GEMINI, "gemini-3-pro-image", "x/.env"))
        self.assertEqual(r(dict(both, IMAGE_PROVIDER="openai"))[:3], ("openai", FAKE_OPENAI, "gpt-image-2"))
        self.assertEqual(r(dict(both, IMAGE_PROVIDER="OpenAI"), provider="gemini")[0], "gemini")  # 인자 > .env
        self.assertEqual(r({"OPENAI_API_KEY": FAKE_OPENAI})[:3], ("openai", FAKE_OPENAI, "gpt-image-2"))
        self.assertEqual(r({"GEMINI_API_KEY": FAKE_GEMINI})[0], "gemini")
        self.assertEqual(r({}), (None, None, None, None))
        self.assertEqual(r({"OPENAI_API_KEY": FAKE_OPENAI, "IMAGE_MODEL": "m1"})[2], "m1")
        self.assertEqual(r({"OPENAI_API_KEY": FAKE_OPENAI, "IMAGE_MODEL": "m1"}, model="m2")[2], "m2")

    def test_named_provider_without_key_is_error_not_fallback(self):
        with self.assertRaises(ValueError) as cm:
            gen_image.resolve_provider({"IMAGE_PROVIDER": "openai", "GEMINI_API_KEY": FAKE_GEMINI})
        self.assertIn("IMAGE_PROVIDER=openai인데 OPENAI_API_KEY가 없습니다", str(cm.exception))
        self.assertNotIn(FAKE_GEMINI, str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            gen_image.resolve_provider({"GEMINI_API_KEY": FAKE_GEMINI}, provider="openai")
        self.assertIn("--provider=openai", str(cm.exception))
        with self.assertRaises(ValueError):
            gen_image.resolve_provider({"IMAGE_PROVIDER": "dalle", "OPENAI_API_KEY": FAKE_OPENAI})

    def test_file_with_key_wins_over_environment(self):
        with tempfile.TemporaryDirectory() as d:
            env_path = os.path.join(d, ".env")
            with open(env_path, "w") as f:
                f.write("IMAGE_PROVIDER=\nOPENAI_API_KEY='%s'\n" % FAKE_OPENAI)
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": FAKE_GEMINI, "IMAGE_PROVIDER": "gemini"}, clear=True):
                env = gen_image.find_env(None, env_path)
                self.assertNotIn("GEMINI_API_KEY", env)
                self.assertEqual(gen_image.resolve_provider(env)[0], "openai")
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": FAKE_GEMINI}, clear=True):
                cwd = os.getcwd()
                try:
                    empty = os.path.join(d, "empty")  # .env 없는 cwd
                    os.makedirs(empty)
                    os.chdir(empty)
                    env = gen_image.find_env(None, None)
                finally:
                    os.chdir(cwd)
                self.assertEqual(env["_source"], "환경변수")


class OpenAIBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.img = os.path.join(d, "posts", "001", "images")
        os.makedirs(self.img)
        self.plan = os.path.join(self.img, "image-plan.md")
        with open(self.plan, "w", encoding="utf-8") as f:
            f.write(PLAN.replace("images/01-cover.png", ""))
        self.env = os.path.join(d, ".env")
        with open(self.env, "w") as f:
            f.write(f"IMAGE_PROVIDER=openai\nOPENAI_API_KEY={FAKE_OPENAI}\n")
        self.cwd = os.getcwd()
        os.chdir(d)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def run_main(self, urlopen, argv=()):
        out, err = io.StringIO(), io.StringIO()
        # google 패키지가 없어도(import 시 ImportError) openai 경로는 돌아야 한다
        with mock.patch.dict(sys.modules, {"google": None, "google.genai": None}), \
                mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch("urllib.request.urlopen", urlopen), \
                mock.patch.object(gen_image.time, "sleep"), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = gen_image.main([self.plan, "--env", self.env, *argv])
        for text in (out.getvalue(), err.getvalue()):
            self.assertNotIn("FAKEKEY", text)
        return rc, out.getvalue(), err.getvalue()

    def _stop_case(self, status, payload, expect):
        calls = []

        def urlopen(req, timeout=None):
            calls.append(req)
            raise http_error(status, payload)

        rc, _, err = self.run_main(urlopen)
        self.assertEqual(rc, 1)
        self.assertEqual(len(calls), 1)  # 재시도 없음, 남은 슬롯 중단
        self.assertIn(expect, err)
        self.assertIn("01, 03", err)
        with open(self.plan, encoding="utf-8") as f:
            self.assertNotIn("images/03-exam.png", f.read())


class OpenAIPathTest(OpenAIBase):
    def test_request_shape_and_b64_save(self):
        seen = []
        png = tiny_png()

        def urlopen(req, timeout=None):
            seen.append((req, timeout))
            return FakeResp({"data": [{"b64_json": gen_image.base64.b64encode(png).decode()}]})

        rc, out, _ = self.run_main(urlopen)
        self.assertEqual(rc, 0)
        self.assertEqual(len(seen), 2)
        req, timeout = seen[0]
        self.assertEqual(req.full_url, "https://api.openai.com/v1/images/generations")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.get_header("Authorization"), f"Bearer {FAKE_OPENAI}")
        self.assertEqual(req.get_header("Content-type"), "application/json")
        self.assertEqual(timeout, gen_image.HTTP_TIMEOUT_MS / 1000)
        body = gen_image.json.loads(req.data.decode("utf-8"))
        self.assertEqual(body, {"model": "gpt-image-2", "prompt": gen_image.build_prompt("gift box on a wooden table"),
                                "size": "1536x1024", "quality": "medium", "n": 1, "output_format": "png"})
        self.assertIn("wide landscape 3:2", body["prompt"])
        self.assertNotIn("response_format", body)
        self.assertNotIn(FAKE_OPENAI, req.data.decode("utf-8"))
        self.assertNotIn(FAKE_OPENAI, req.full_url)
        self.assertIn("제공자: openai · 모델: gpt-image-2", out)
        self.assertIn("openai.com/api/pricing", out)
        saved = os.path.join(self.img, "01-cover.png")
        self.assertTrue(os.path.isfile(saved))
        try:
            from PIL import Image
        except ImportError:
            with open(saved, "rb") as f:
                self.assertEqual(f.read(), png)  # pillow 없으면 원본 그대로
        else:
            with Image.open(saved) as im:
                self.assertEqual(im.size[0], 1200)
        with open(self.plan, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("images/01-cover.png", text)
        self.assertIn("images/03-exam.png", text)

    def test_model_flag_overrides_default(self):
        seen = []

        def urlopen(req, timeout=None):
            seen.append(gen_image.json.loads(req.data.decode("utf-8"))["model"])
            return FakeResp({"data": [{"b64_json": gen_image.base64.b64encode(tiny_png()).decode()}]})

        rc, _, _ = self.run_main(urlopen, ["--model", "gpt-image-1", "--only", "1"])
        self.assertEqual((rc, seen), (0, ["gpt-image-1"]))

    def test_401(self):
        self._stop_case(401, {"error": {"message": f"Incorrect API key provided: {FAKE_OPENAI[:8]}****cdef",
                                        "code": "invalid_api_key"}}, "OpenAI 키가 올바르지 않습니다")

    def test_403(self):
        self._stop_case(403, {"error": {"message": "organization must be verified"}}, "조직 인증(Verify Organization)")

    def test_429(self):
        self._stop_case(429, {"error": {"message": "billing hard limit", "code": "billing_hard_limit_reached"}},
                        "OpenAI 사용 한도/결제 문제(요금제·결제 수단 확인)")

    def test_400_safety_fails_slot_and_continues(self):
        calls = []

        def urlopen(req, timeout=None):
            calls.append(req)
            if len(calls) == 1:
                raise http_error(400, {"error": {"message": "Your request was rejected by the safety system.",
                                                 "code": "moderation_blocked"}})
            return FakeResp({"data": [{"b64_json": gen_image.base64.b64encode(tiny_png()).decode()}]})

        rc, out, err = self.run_main(urlopen)
        self.assertEqual((rc, len(calls)), (1, 2))
        self.assertIn("안전 정책으로 거절 — 프롬프트를 바꿔 재생성", err)
        self.assertIn("[OK] 03", out)

    def test_other_error_summarizes_message_without_key(self):
        def urlopen(req, timeout=None):
            raise http_error(500, {"error": {"message": f"server exploded near {FAKE_OPENAI}"}})

        rc, _, err = self.run_main(urlopen, ["--only", "1"])
        self.assertEqual(rc, 1)
        self.assertIn("OpenAI 500: server exploded near", err)

    def test_503_retries_with_backoff(self):
        calls = []

        def urlopen(req, timeout=None):
            calls.append(req)
            if len(calls) < 3:
                raise http_error(503, {"error": {"message": "busy"}})
            return FakeResp({"data": [{"b64_json": gen_image.base64.b64encode(tiny_png()).decode()}]})

        rc, _, _ = self.run_main(urlopen, ["--only", "1"])
        self.assertEqual((rc, len(calls)), (0, 3))


class DryRunProviderTest(unittest.TestCase):
    def _dry(self, env_text=None, argv=()):
        with tempfile.TemporaryDirectory() as d:
            plan = os.path.join(d, "images", "image-plan.md")
            os.makedirs(os.path.dirname(plan))
            with open(plan, "w", encoding="utf-8") as f:
                f.write(PLAN)
            args = [plan, "--dry-run", *argv]
            if env_text is not None:
                env = os.path.join(d, ".env")
                with open(env, "w") as f:
                    f.write(env_text)
                args += ["--env", env]
            out, err = io.StringIO(), io.StringIO()
            cwd = os.getcwd()
            try:
                os.chdir(d)
                with mock.patch.dict(os.environ, {}, clear=True), \
                        mock.patch("urllib.request.urlopen", side_effect=AssertionError("네트워크 금지")), \
                        contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    rc = gen_image.main(args)
            finally:
                os.chdir(cwd)
            self.assertNotIn("FAKEKEY", out.getvalue() + err.getvalue())
            return rc, out.getvalue()

    def test_no_key(self):
        rc, out = self._dry()
        self.assertEqual(rc, 0)
        self.assertIn("제공자: 없음(키 없음)", out)
        self.assertIn(gen_image.build_prompt("examiner seen from behind"), out)

    def test_openai_key(self):
        rc, out = self._dry(f"OPENAI_API_KEY={FAKE_OPENAI}\n")
        self.assertEqual(rc, 0)
        self.assertIn("제공자: openai · 모델: gpt-image-2", out)
        self.assertIn("openai.com/api/pricing", out)

    def test_gemini_key_shows_estimate(self):
        rc, out = self._dry(f"GEMINI_API_KEY={FAKE_GEMINI}\n")
        self.assertIn("제공자: gemini · 모델: gemini-3-pro-image", out)
        self.assertIn("$0.08", out)

    def test_provider_conflict_still_previews(self):
        rc, out = self._dry(f"IMAGE_PROVIDER=openai\nGEMINI_API_KEY={FAKE_GEMINI}\n")
        self.assertEqual(rc, 0)
        self.assertIn("IMAGE_PROVIDER=openai인데 OPENAI_API_KEY가 없습니다", out)


class ReviewRulesTest(unittest.TestCase):
    FAKE_MODEL = "sk-proj-FAKEKEY0123456789abcdef"

    def assert_no_fragments(self, text):
        for frag in ("FAKEKEY", FAKE_GEMINI[:6], FAKE_OPENAI[:6], self.FAKE_MODEL[:6]):
            self.assertNotIn(frag, text)

    def run_main(self, env_text, argv):
        with tempfile.TemporaryDirectory() as d:
            plan = os.path.join(d, "images", "image-plan.md")
            os.makedirs(os.path.dirname(plan))
            with open(plan, "w", encoding="utf-8") as f:
                f.write(PLAN)
            env = os.path.join(d, "keys.env")
            with open(env, "w") as f:
                f.write(env_text)
            out, err = io.StringIO(), io.StringIO()
            cwd = os.getcwd()
            try:
                os.chdir(d)
                with mock.patch.dict(os.environ, {}, clear=True), \
                        mock.patch("urllib.request.urlopen", side_effect=AssertionError("네트워크 금지")), \
                        contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    rc = gen_image.main([plan, "--env", env, *argv])
            finally:
                os.chdir(cwd)
            text = out.getvalue() + err.getvalue()
            self.assert_no_fragments(text)
            return rc, text

    def test_key_pasted_into_provider_and_model_never_printed(self):
        bad = f"IMAGE_PROVIDER={FAKE_GEMINI}\nIMAGE_MODEL={self.FAKE_MODEL}\nOPENAI_API_KEY={FAKE_OPENAI}\n"
        rc, text = self.run_main(bad, ["--dry-run"])
        self.assertEqual(rc, 0)
        self.assertIn("IMAGE_PROVIDER 값이 알 수 없는 값입니다", text)
        rc, text = self.run_main(bad, [])
        self.assertEqual(rc, 2)
        rc, text = self.run_main(f"IMAGE_MODEL={self.FAKE_MODEL}\nOPENAI_API_KEY={FAKE_OPENAI}\n", ["--dry-run"])
        self.assertIn("IMAGE_MODEL 값이 모델 이름 형식이 아닙니다(키를 잘못 넣었는지 확인)", text)
        rc, text = self.run_main(f"IMAGE_MODEL={self.FAKE_MODEL}\nOPENAI_API_KEY={FAKE_OPENAI}\n", [])
        self.assertEqual(rc, 2)
        rc, text = self.run_main(f"OPENAI_API_KEY={FAKE_OPENAI}\n", ["--model", "gpt image/2", "--dry-run"])
        self.assertIn("--model 값이 모델 이름 형식이 아닙니다", text)

    def test_model_name_format(self):
        r = gen_image.resolve_provider
        for ok in ("gpt-image-2", "my-task-model", "gemini-3-pro-image-preview", "models.v1:latest"):
            self.assertEqual(r({"OPENAI_API_KEY": FAKE_OPENAI, "IMAGE_MODEL": ok})[2], ok)
        for bad in ("sk-abcd1234", "AIzaSyABCDEFGHIJKLMN", "-x", "a b", "x" * 65, FAKE_OPENAI):
            with self.assertRaises(ValueError):
                r({"OPENAI_API_KEY": FAKE_OPENAI, "IMAGE_MODEL": bad})

    def test_settings_fallback_when_key_from_environment(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = os.getcwd()
            try:
                os.chdir(d)
                with open(".env", "w") as f:
                    f.write("IMAGE_PROVIDER=openai\n")
                with mock.patch.dict(os.environ, {"GEMINI_API_KEY": FAKE_GEMINI, "OPENAI_API_KEY": FAKE_OPENAI,
                                                  "IMAGE_PROVIDER": "gemini", "IMAGE_MODEL": "env-model"}, clear=True):
                    env = gen_image.find_env(None)
                    self.assertEqual(env["_source"], "환경변수")
                    self.assertEqual(env["IMAGE_PROVIDER"], "openai")  # cwd .env > 환경변수
                    self.assertEqual(env["IMAGE_MODEL"], "env-model")  # cwd .env에 없으면 환경변수
                    with open(".env", "a") as f:
                        f.write("OPENAI_API_KEY=%s\n" % FAKE_OPENAI)
                    env = gen_image.find_env(None)  # 키가 든 .env → 그 파일 값만
                    self.assertEqual(env["_source"], os.path.join(os.getcwd(), ".env"))
                    self.assertNotIn("IMAGE_MODEL", env)
            finally:
                os.chdir(cwd)

    def test_env_parsing_rules(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, ".env")
            with open(p, "w") as f:
                f.write("GEMINI_API_KEY=#notakey\nOPENAI_API_KEY=\"   \"\nIMAGE_MODEL=\nIMAGE_MODEL=m-1 # c\n"
                        "IMAGE_MODEL=m-2\nIMAGE_PROVIDER=a#b\n")
            vals = gen_image.read_env_values(p)
            self.assertNotIn("GEMINI_API_KEY", vals)
            self.assertNotIn("OPENAI_API_KEY", vals)
            self.assertEqual(vals["IMAGE_MODEL"], "m-1")  # 처음 나온 비어 있지 않은 값
            self.assertEqual(vals["IMAGE_PROVIDER"], "a#b")  # 공백 없는 #는 값의 일부


class OpenAIRetryTest(OpenAIBase):
    def test_rate_limit_retries_with_retry_after_then_fails_slot_only(self):
        import urllib.error
        calls = []

        def urlopen(req, timeout=None):
            calls.append(req)
            if len(calls) <= 3:
                body = gen_image.json.dumps({"error": {"code": "rate_limit_exceeded", "message": "slow down"}})
                raise urllib.error.HTTPError("u", 429, "err", {"Retry-After": "7"}, io.BytesIO(body.encode()))
            return FakeResp({"data": [{"b64_json": gen_image.base64.b64encode(tiny_png()).decode()}]})

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(sys.modules, {"google": None, "google.genai": None}), \
                mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch("urllib.request.urlopen", urlopen), \
                mock.patch.object(gen_image.time, "sleep") as sleep, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = gen_image.main([self.plan, "--env", self.env])
        self.assertEqual((rc, len(calls)), (1, 4))  # 01: 3회 시도 후 실패, 03: 성공
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [7.0, 7.0])
        self.assertIn("요청 속도 제한", err.getvalue())
        self.assertIn("[OK] 03", out.getvalue())

    def test_insufficient_quota_stops(self):
        self._stop_case(429, {"error": {"message": "quota", "type": "insufficient_quota", "code": "insufficient_quota"}},
                        "OpenAI 사용 한도/결제 문제")

    def test_500_retries_with_exponential_backoff(self):
        calls = []

        def urlopen(req, timeout=None):
            calls.append(req)
            raise http_error(500, {"error": {"message": "boom"}})

        with mock.patch.object(gen_image.time, "sleep") as sleep:
            rc, _, err = self.run_main(urlopen, ["--only", "1"])
        self.assertEqual((rc, len(calls)), (1, 3))
        self.assertIn("OpenAI 500: boom", err)


class NoKeyRunTest(unittest.TestCase):
    def test_real_run_without_key_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            plan = os.path.join(d, "images", "image-plan.md")
            os.makedirs(os.path.dirname(plan))
            with open(plan, "w", encoding="utf-8") as f:
                f.write(PLAN)
            err = io.StringIO()
            cwd = os.getcwd()
            try:
                os.chdir(d)
                with mock.patch.dict(os.environ, {}, clear=True), \
                        contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                    rc = gen_image.main([plan])
            finally:
                os.chdir(cwd)
            self.assertEqual(rc, 2)
            self.assertIn("aistudio.google.com/apikey", err.getvalue())
            self.assertIn("platform.openai.com/api-keys", err.getvalue())


if __name__ == "__main__":
    unittest.main()
