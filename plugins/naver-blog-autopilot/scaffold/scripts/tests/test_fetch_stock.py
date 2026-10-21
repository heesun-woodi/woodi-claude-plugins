import contextlib
import io
import json
import os
import socket
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import fetch_stock  # noqa: E402

FAKE_KEY = "PexelsFAKEKEY563f2b8c0a9e4d71b6c5a0f9e8d7c6b5a4f3e2d1c0b9a8"

PLAN_WITH_SOURCE = """# 이미지 계획
| 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 검색어(stock) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수 | 출처 |
|---|---|---|---|---|---|---|---|---|
| 01 | 제목 아래(표지) | 표지 | ai | bicycle shop at dawn | 매장 | images/01-cover.png | | |
| 03 | ## 3️⃣ 체인 청소 | 현장 | stock | bicycle chain cleaning closeup | 체인을 닦는 장면 | | | |
| 04 | ## 4️⃣ 공기압 | 작업 | stock | bicycle tire pump | 공기 넣기 | | | |
| 05 | ## 5️⃣ 마무리 | 요약 | stock | | 정리 | | | |
| 06 | ## 업체 소개 | 업체 CTA | photo | photos/a.jpg | 매장 | | | |
"""

PLAN_NO_SOURCE = """| 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수 |
|---|---|---|---|---|---|---|---|
| 03 | ## 체인 | 현장 | stock | bicycle chain | 체인 | | |
"""


def photo(pid, width, photographer="Jane Doe", large2x=True):
    src = {"original": f"https://images.pexels.com/{pid}/o.jpeg", "large": f"https://images.pexels.com/{pid}/l.jpeg",
           "medium": f"https://images.pexels.com/{pid}/m.jpeg"}
    if large2x:
        src["large2x"] = f"https://images.pexels.com/{pid}/l2x.jpeg"
    return {"id": pid, "width": width, "height": 1000, "url": f"https://www.pexels.com/photo/{pid}/",
            "photographer": photographer, "photographer_url": "https://www.pexels.com/@jane", "alt": "", "src": src}


def search_body(photos):
    return json.dumps({"total_results": len(photos), "page": 1, "per_page": 8, "photos": photos})


class FakeResp:
    def __init__(self, body):
        self.body = body if isinstance(body, bytes) else body.encode("utf-8")

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(status):
    return urllib.error.HTTPError("https://api.pexels.com/v1/search", status, "err", {},
                                  io.BytesIO(json.dumps({"error": f"bad {FAKE_KEY}"}).encode("utf-8")))


class FetchStockTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        self.work = os.path.join(self.tmp.name, "work")
        os.makedirs(self.work)
        os.chdir(self.work)  # cwd/.env 없음
        self.post = os.path.join(self.work, "posts", "003-chain")
        os.makedirs(os.path.join(self.post, "images"))
        self.write_plan(PLAN_WITH_SOURCE)
        self.envfile = os.path.join(self.tmp.name, "keys.env")
        with open(self.envfile, "w") as f:
            f.write(f"PEXELS_API_KEY={FAKE_KEY}\n")

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    @property
    def plan_path(self):
        return os.path.join(self.post, "images", "image-plan.md")

    def write_plan(self, text):
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write(text)

    def read_plan(self):
        with open(self.plan_path, encoding="utf-8") as f:
            return f.read()

    def run_main(self, argv, responder=None, environ=None):
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append(req)
            return responder(req)

        out, err = io.StringIO(), io.StringIO()
        patches = [mock.patch.dict(os.environ, environ or {}, clear=True),
                   contextlib.redirect_stdout(out), contextlib.redirect_stderr(err)]
        if responder is not None:
            patches.append(mock.patch("urllib.request.urlopen", fake_urlopen))
        with contextlib.ExitStack() as st:
            for p in patches:
                st.enter_context(p)
            rc = fetch_stock.main(argv)
        text = out.getvalue() + err.getvalue()
        self.assertNotIn(FAKE_KEY, text)
        self.assertNotIn("FAKEKEY", text)
        return rc, out.getvalue(), err.getvalue(), seen

    def default_responder(self, photos_by_query):
        def responder(req):
            if req.full_url.startswith(fetch_stock.SEARCH_URL):
                q = urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)["query"][0]
                return FakeResp(search_body(photos_by_query.get(q, [])))
            return FakeResp(b"\xff\xd8JPEGDATA:" + req.full_url.encode())
        return responder

    def test_ok_saves_jpg_updates_file_and_source(self):
        resp = self.default_responder({
            "bicycle chain cleaning closeup": [photo(1, 1200), photo(2, 4000, "Kim | Lee"), photo(3, 5000)],
            "bicycle tire pump": [photo(4, 2000, "Park", large2x=False)]})
        rc, out, err, seen = self.run_main([self.post, "--env", self.envfile], resp)
        self.assertEqual(rc, 0, err)
        lines = out.strip().splitlines()
        self.assertEqual(lines[0], f"스톡: pexels · 키: {self.envfile}")
        self.assertEqual(lines[-1], "저장 2장 · 보류 1장")
        req = seen[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(req.get_header("Authorization"), FAKE_KEY)
        self.assertNotIn(FAKE_KEY, req.full_url)
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)
        self.assertEqual(q, {"query": ["bicycle chain cleaning closeup"], "orientation": ["landscape"],
                             "per_page": ["8"], "locale": ["ko-KR"]})
        self.assertEqual(seen[1].full_url, "https://images.pexels.com/2/l2x.jpeg")  # width>=1600 첫 장, large2x
        self.assertIsNone(seen[1].get_header("Authorization"))
        self.assertEqual(seen[3].full_url, "https://images.pexels.com/4/l.jpeg")  # large2x 없으면 large
        with open(os.path.join(self.post, "images", "03-scene.jpg"), "rb") as f:
            self.assertTrue(f.read().startswith(b"\xff\xd8"))
        self.assertTrue(os.path.isfile(os.path.join(self.post, "images", "04-work.jpg")))
        plan = self.read_plan()
        self.assertIn("| 03 | ## 3️⃣ 체인 청소 | 현장 | stock | bicycle chain cleaning closeup | 체인을 닦는 장면 | "
                      "images/03-scene.jpg | | 출처: Pexels/Kim / Lee https://www.pexels.com/photo/2/ |", plan)
        self.assertIn("| images/04-work.jpg | | 출처: Pexels/Park https://www.pexels.com/photo/4/ |", plan)
        self.assertIn("| 05 | ## 5️⃣ 마무리 | 요약 | stock | | 정리 | | 검색어 없음 | |", plan)
        self.assertIn("| 01 | 제목 아래(표지) | 표지 | ai | bicycle shop at dawn | 매장 | images/01-cover.png | | |", plan)

    def test_no_source_column_credit_goes_to_review(self):
        self.write_plan(PLAN_NO_SOURCE)
        rc, out, _, _ = self.run_main([self.post, "--env", self.envfile],
                                      self.default_responder({"bicycle chain": [photo(9, 3000, "Jane Doe")]}))
        self.assertEqual(rc, 0)
        self.assertIn("| 03 | ## 체인 | 현장 | stock | bicycle chain | 체인 | images/03-scene.jpg | "
                      "출처: Pexels/Jane Doe https://www.pexels.com/photo/9/ |", self.read_plan())

    def test_zero_results_held(self):
        rc, out, _, seen = self.run_main([self.post, "--env", self.envfile, "--only", "3"],
                                         self.default_responder({}))
        self.assertEqual(rc, 0)
        self.assertEqual(len(seen), 1)
        self.assertIn("| 03 | ## 3️⃣ 체인 청소 | 현장 | stock | bicycle chain cleaning closeup | 체인을 닦는 장면 | "
                      "보류 | 검색 결과 없음 | |", self.read_plan())
        self.assertEqual(out.strip().splitlines()[-1], "저장 0장 · 보류 1장")
        # 1600px 이상이 하나도 없어도 보류
        rc, out, _, _ = self.run_main([self.post, "--env", self.envfile, "--only", "04"],
                                      self.default_responder({"bicycle tire pump": [photo(1, 1200)]}))
        self.assertEqual(rc, 0)
        self.assertIn("| 보류 | 검색 결과 없음 |", self.read_plan().splitlines()[4])

    def test_only_validation(self):
        rc, _, err, seen = self.run_main([self.post, "--env", self.envfile, "--only", "06"], self.default_responder({}))
        self.assertEqual((rc, seen), (2, []))
        self.assertIn("stock 슬롯이 아닙니다: 06", err)
        rc, _, err, _ = self.run_main([self.post, "--env", self.envfile, "--only", "09"], self.default_responder({}))
        self.assertEqual(rc, 2)
        self.assertIn("표에 없는 슬롯 번호: 09", err)

    def test_exit3_401_403_stops_and_keeps_done(self):
        for status in (401, 403):
            self.write_plan(PLAN_WITH_SOURCE)
            calls = {"n": 0}

            def responder(req):
                if req.full_url.startswith(fetch_stock.SEARCH_URL):
                    calls["n"] += 1
                    if calls["n"] == 2:
                        raise http_error(status)
                    return FakeResp(search_body([photo(2, 4000)]))
                return FakeResp(b"\xff\xd8")
            rc, out, err, seen = self.run_main([self.post, "--env", self.envfile], responder)
            self.assertEqual(rc, 3)
            self.assertIn(f"Pexels {status}", err)
            self.assertIn("남은 슬롯 04, 05", err)
            self.assertIn("images/03-scene.jpg", self.read_plan())
            self.assertNotIn("images/04-work.jpg", self.read_plan())
            self.assertEqual(out.strip().splitlines()[-1], "저장 1장 · 보류 0장")

    def test_exit6_429_no_retry(self):
        def responder(req):
            raise http_error(429)
        rc, _, err, seen = self.run_main([self.post, "--env", self.envfile], responder)
        self.assertEqual(rc, 6)
        self.assertEqual(len(seen), 1)  # 재시도 없음
        self.assertIn("429", err)
        self.assertEqual(self.read_plan(), PLAN_WITH_SOURCE)

    def test_exit5_network_and_5xx(self):
        def offline(req):
            raise urllib.error.URLError("no route")
        rc, _, err, _ = self.run_main([self.post, "--env", self.envfile], offline)
        self.assertEqual(rc, 5)
        self.assertIn("네트워크 오류", err)

        def server(req):
            raise http_error(502)
        rc, _, err, _ = self.run_main([self.post, "--env", self.envfile], server)
        self.assertEqual(rc, 5)
        self.assertIn("HTTP 502", err)

        def download_fails(req):
            if req.full_url.startswith(fetch_stock.SEARCH_URL):
                return FakeResp(search_body([photo(2, 4000)]))
            raise urllib.error.URLError("reset")
        rc, _, _, _ = self.run_main([self.post, "--env", self.envfile], download_fails)
        self.assertEqual(rc, 5)
        self.assertEqual(self.read_plan(), PLAN_WITH_SOURCE)

    def test_exit2_no_key_no_plan_bad_table(self):
        rc, _, err, seen = self.run_main([self.post], self.default_responder({}))
        self.assertEqual((rc, seen), (2, []))
        self.assertIn("스톡 키 없음 — .env에 PEXELS_API_KEY=…", err)
        rc, _, err, _ = self.run_main([os.path.join(self.work, "posts", "nope"), "--env", self.envfile])
        self.assertEqual(rc, 2)
        self.assertIn("image-plan.md가 없습니다", err)
        self.write_plan("# 표 없음\n")
        rc, _, err, _ = self.run_main([self.post, "--env", self.envfile])
        self.assertEqual(rc, 2)
        self.write_plan("| 슬롯 | 위치 | 목적 | 유형 | 프롬프트 | 캡션 | 파일 |\n|---|---|---|---|---|---|---|\n")
        rc, _, err, _ = self.run_main([self.post, "--env", self.envfile])
        self.assertEqual(rc, 2)
        self.assertIn("검수", err)
        rc, _, _, _ = self.run_main([self.post, "--env", os.path.join(self.tmp.name, "nope.env")])
        self.assertEqual(rc, 2)

    def test_key_search_order(self):
        # plan 상위 폴더(.env in work/posts)
        with open(os.path.join(self.work, "posts", ".env"), "w") as f:
            f.write(f"OTHER=1\nexport PEXELS_API_KEY=\"{FAKE_KEY}\"\n")
        key, src = fetch_stock.find_pexels_key(self.plan_path)
        self.assertEqual((key, src), (FAKE_KEY, os.path.join(self.work, "posts", ".env")))
        # cwd/.env가 plan 상위보다 먼저
        with open(os.path.join(self.work, ".env"), "w") as f:
            f.write("PEXELS_API_KEY=cwdKEY123\n")
        self.assertEqual(fetch_stock.find_pexels_key(self.plan_path)[0], "cwdKEY123")
        # --env가 가장 먼저
        self.assertEqual(fetch_stock.find_pexels_key(self.plan_path, self.envfile), (FAKE_KEY, self.envfile))
        os.remove(os.path.join(self.work, ".env"))
        os.remove(os.path.join(self.work, "posts", ".env"))
        with mock.patch.dict(os.environ, {"PEXELS_API_KEY": FAKE_KEY}, clear=True):
            self.assertEqual(fetch_stock.find_pexels_key(self.plan_path), (FAKE_KEY, "환경변수"))
            rc, out, _, _ = self.run_main([self.post, "--dry-run"], environ={"PEXELS_API_KEY": FAKE_KEY})
        self.assertIn("스톡: pexels · 키: 환경변수", out)

    def test_dry_run_opens_no_socket_and_does_not_write(self):
        counter = mock.MagicMock(side_effect=AssertionError("소켓 사용 금지"))
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(socket, "socket", counter), \
                mock.patch.object(socket, "create_connection", counter), \
                mock.patch.object(socket, "getaddrinfo", counter), \
                mock.patch.dict(os.environ, {}, clear=True), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = fetch_stock.main([self.post, "--dry-run", "--env", self.envfile])
        self.assertEqual(rc, 0, err.getvalue())
        self.assertEqual(counter.call_count, 0)
        text = out.getvalue()
        self.assertNotIn(FAKE_KEY, text + err.getvalue())
        self.assertEqual(text.strip().splitlines(), [
            f"스톡: pexels · 키: {self.envfile}",
            "03 · bicycle chain cleaning closeup · images/03-scene.jpg",
            "04 · bicycle tire pump · images/04-work.jpg",
            "05 · (검색어 없음) · 건너뜀",
            "(dry-run) 네트워크 접속 없음 · 대상 3장"])
        self.assertEqual(self.read_plan(), PLAN_WITH_SOURCE)
        self.assertEqual(sorted(os.listdir(os.path.join(self.post, "images"))), ["image-plan.md"])

    def test_dry_run_without_key(self):
        rc, out, _, _ = self.run_main([self.post, "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertIn("스톡: pexels · 키: 없음", out)

    def test_help_exit_0(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(fetch_stock.main(["--help"]), 0)


if __name__ == "__main__":
    unittest.main()
