import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check_image_key  # noqa: E402

FAKE_OPENAI = "sk-test-FAKEKEY0123456789abcdef"
FAKE_GEMINI = "AIzaFAKEKEY0123456789abcdef"


class FakeResp:
    def read(self):
        return b'{"id": "m"}'

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(status, payload):
    return urllib.error.HTTPError("https://example.invalid", status, "err", {},
                                  io.BytesIO(json.dumps(payload).encode("utf-8")))


class CheckImageKeyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)  # cwd/.env 없음

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def run_check(self, env_text=None, urlopen=None, argv=()):
        args = list(argv)
        if env_text is not None:
            path = os.path.join(self.tmp.name, "keys.env")
            with open(path, "w") as f:
                f.write(env_text)
            args += ["--env", path]
        seen = []

        def default_urlopen(req, timeout=None):
            seen.append(req)
            return FakeResp()

        def wrapped(req, timeout=None):
            seen.append(req)
            return urlopen(req, timeout)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch("urllib.request.urlopen", wrapped if urlopen else default_urlopen), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = check_image_key.main(args)
        text = out.getvalue() + err.getvalue()
        self.assertNotIn("FAKEKEY", text)
        return rc, text, seen

    def test_ok_gemini_header_not_url(self):
        rc, text, seen = self.run_check(f"GEMINI_API_KEY={FAKE_GEMINI}\n")
        self.assertEqual(rc, 0)
        req = seen[0]
        self.assertEqual(req.full_url, "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image")
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(req.get_header("X-goog-api-key"), FAKE_GEMINI)
        self.assertNotIn(FAKE_GEMINI, req.full_url)
        self.assertIn("이미지 키 확인: gemini · 모델 gemini-3-pro-image 사용 가능 (", text)
        self.assertIn("결제 설정된 프로젝트 키", text)

    def test_ok_openai(self):
        rc, text, seen = self.run_check(f"IMAGE_PROVIDER=openai\nOPENAI_API_KEY={FAKE_OPENAI}\nIMAGE_MODEL=gpt-image-2\n")
        self.assertEqual(rc, 0)
        self.assertEqual(seen[0].full_url, "https://api.openai.com/v1/models/gpt-image-2")
        self.assertEqual(seen[0].get_header("Authorization"), f"Bearer {FAKE_OPENAI}")
        self.assertIn("이미지 키 확인: openai · 모델 gpt-image-2 사용 가능", text)
        self.assertNotIn("결제 설정된 프로젝트 키", text)
        self.assertIn("이미지 생성에서 403이 나면 조직 인증(Verify Organization)이 필요합니다", text)

    def test_provider_flag(self):
        rc, _, seen = self.run_check(f"GEMINI_API_KEY={FAKE_GEMINI}\nOPENAI_API_KEY={FAKE_OPENAI}\n",
                                     argv=["--provider", "openai"])
        self.assertEqual(rc, 0)
        self.assertIn("api.openai.com", seen[0].full_url)

    def test_exit_2_no_key(self):
        rc, text, seen = self.run_check()
        self.assertEqual((rc, seen), (2, []))
        self.assertIn("aistudio.google.com/apikey", text)
        self.assertIn("platform.openai.com/api-keys", text)

    def test_exit_2_provider_conflict_and_unknown(self):
        rc, text, seen = self.run_check(f"IMAGE_PROVIDER=openai\nGEMINI_API_KEY={FAKE_GEMINI}\n")
        self.assertEqual((rc, seen), (2, []))
        self.assertIn("IMAGE_PROVIDER=openai인데 OPENAI_API_KEY가 없습니다", text)
        rc, _, _ = self.run_check(f"IMAGE_PROVIDER=dalle\nOPENAI_API_KEY={FAKE_OPENAI}\n")
        self.assertEqual(rc, 2)
        rc, _, _ = self.run_check(argv=["--env", os.path.join(self.tmp.name, "nope.env")])
        self.assertEqual(rc, 2)

    def test_key_pasted_into_provider_or_model_never_printed(self):
        fake_model = "sk-proj-FAKEKEY0123456789abcdef"
        for env_text in (f"IMAGE_PROVIDER={FAKE_GEMINI}\nOPENAI_API_KEY={FAKE_OPENAI}\n",
                         f"IMAGE_MODEL={fake_model}\nOPENAI_API_KEY={FAKE_OPENAI}\n"):
            rc, text, seen = self.run_check(env_text)
            self.assertEqual((rc, seen), (2, []))
            for frag in (FAKE_GEMINI[:6], FAKE_OPENAI[:6], fake_model[:6]):
                self.assertNotIn(frag, text)
        self.assertIn("IMAGE_MODEL 값이 모델 이름 형식이 아닙니다(키를 잘못 넣었는지 확인)", text)

    def test_exit_3_rejected(self):
        rc, text, _ = self.run_check(f"OPENAI_API_KEY={FAKE_OPENAI}\n", lambda r, t: (_ for _ in ()).throw(
            http_error(401, {"error": {"message": f"Incorrect API key provided: {FAKE_OPENAI[:10]}***"}})))
        self.assertEqual(rc, 3)
        self.assertIn("OpenAI 키가 올바르지 않습니다", text)
        rc, text, _ = self.run_check(f"OPENAI_API_KEY={FAKE_OPENAI}\n", lambda r, t: (_ for _ in ()).throw(
            http_error(403, {"error": {"message": "forbidden"}})))
        self.assertEqual(rc, 3)
        self.assertIn("조직 인증(Verify Organization)", text)
        rc, text, _ = self.run_check(f"GEMINI_API_KEY={FAKE_GEMINI}\n", lambda r, t: (_ for _ in ()).throw(
            http_error(400, {"error": {"code": 400, "message": "API key not valid. Please pass a valid API key.",
                                       "status": "INVALID_ARGUMENT"}})))
        self.assertEqual(rc, 3)

    def test_exit_4_model_missing(self):
        rc, text, _ = self.run_check(f"OPENAI_API_KEY={FAKE_OPENAI}\n", lambda r, t: (_ for _ in ()).throw(
            http_error(404, {"error": {"message": "The model does not exist"}})))
        self.assertEqual(rc, 4)
        self.assertIn("gpt-image-2", text)

    def test_exit_5_network_and_other(self):
        rc, text, _ = self.run_check(f"GEMINI_API_KEY={FAKE_GEMINI}\n", lambda r, t: (_ for _ in ()).throw(
            urllib.error.URLError("no route")))
        self.assertEqual(rc, 5)
        self.assertIn("네트워크", text)
        rc, text, _ = self.run_check(f"OPENAI_API_KEY={FAKE_OPENAI}\n", lambda r, t: (_ for _ in ()).throw(
            http_error(500, {"error": {"message": f"oops {FAKE_OPENAI}"}})))
        self.assertEqual(rc, 5)
        self.assertIn("HTTP 500", text)


FAKE_PEXELS = "PexelsFAKEKEY563f2b8c0a9e4d71b6c5a0f9e8d7c6b5a4f3e2d1c0b9a8"


class CheckStockKeyTest(unittest.TestCase):
    """--stock: PEXELS_API_KEY만 확인(이미지 생성 키 경로와 섞이지 않음)."""

    setUp = CheckImageKeyTest.setUp
    tearDown = CheckImageKeyTest.tearDown
    run_check = CheckImageKeyTest.run_check

    def assert_no_pexels_key(self, text):
        self.assertNotIn(FAKE_PEXELS, text)

    def test_stock_ok_header_and_url(self):
        rc, text, seen = self.run_check(f"GEMINI_API_KEY={FAKE_GEMINI}\nPEXELS_API_KEY={FAKE_PEXELS}\n", argv=["--stock"])
        self.assertEqual(rc, 0)
        self.assertEqual(len(seen), 1)  # Pexels만 확인 — Gemini 조회 없음
        req = seen[0]
        self.assertEqual(req.full_url, "https://api.pexels.com/v1/search?query=test&per_page=1")
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(req.get_header("Authorization"), FAKE_PEXELS)
        self.assertIn("스톡 키 확인: pexels 사용 가능 (", text)
        self.assert_no_pexels_key(text)

    def test_stock_env_var_source(self):
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"PEXELS_API_KEY": FAKE_PEXELS}, clear=True), \
                mock.patch("urllib.request.urlopen", lambda req, timeout=None: FakeResp()), \
                contextlib.redirect_stdout(out):
            rc = check_image_key.main(["--stock"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.getvalue().strip(), "스톡 키 확인: pexels 사용 가능 (환경변수)")

    def test_stock_exit_2_no_key_and_conflicts(self):
        rc, text, seen = self.run_check(f"GEMINI_API_KEY={FAKE_GEMINI}\n", argv=["--stock"])
        self.assertEqual((rc, seen), (2, []))
        self.assertIn("스톡 키 없음 — .env에 PEXELS_API_KEY=…", text)
        self.assertIn("https://www.pexels.com/api/", text)
        rc, _, seen = self.run_check(f"PEXELS_API_KEY={FAKE_PEXELS}\n", argv=["--stock", "--provider", "openai"])
        self.assertEqual((rc, seen), (2, []))
        rc, _, seen = self.run_check(argv=["--stock", "--env", os.path.join(self.tmp.name, "nope.env")])
        self.assertEqual((rc, seen), (2, []))

    def test_stock_exit_3_rejected(self):
        for status in (401, 403):
            rc, text, _ = self.run_check(f"PEXELS_API_KEY={FAKE_PEXELS}\n", lambda r, t: (_ for _ in ()).throw(
                http_error(status, {"error": f"bad key {FAKE_PEXELS}"})), argv=["--stock"])
            self.assertEqual(rc, 3)
            self.assertIn(f"스톡 키 거부: Pexels {status}", text)
            self.assert_no_pexels_key(text)

    def test_stock_exit_5_network_and_429(self):
        rc, text, _ = self.run_check(f"PEXELS_API_KEY={FAKE_PEXELS}\n", lambda r, t: (_ for _ in ()).throw(
            urllib.error.URLError(f"no route {FAKE_PEXELS}")), argv=["--stock"])
        self.assertEqual(rc, 5)
        self.assertIn("네트워크", text)
        self.assert_no_pexels_key(text)
        rc, text, _ = self.run_check(f"PEXELS_API_KEY={FAKE_PEXELS}\n", lambda r, t: (_ for _ in ()).throw(
            http_error(429, {"error": "rate limit"})), argv=["--stock"])
        self.assertEqual(rc, 5)
        self.assertIn("HTTP 429", text)

    def test_without_stock_flag_ignores_pexels(self):
        rc, text, seen = self.run_check(f"PEXELS_API_KEY={FAKE_PEXELS}\n")
        self.assertEqual((rc, seen), (2, []))  # 1.0.0 동작: 이미지 생성 키 없음
        self.assertIn("이미지 키 없음", text)


if __name__ == "__main__":
    unittest.main()
