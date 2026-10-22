import contextlib
import http.client
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
    def __init__(self, body, headers=None):
        self.body = body if isinstance(body, bytes) else body.encode("utf-8")
        self.headers = {"Content-Type": "image/jpeg"} if headers is None else headers
        self.pos = 0
        self.read_calls = 0

    def read(self, n=-1):
        self.read_calls += 1
        if n is None or n < 0:
            n = len(self.body)
        chunk = self.body[self.pos:self.pos + n]
        self.pos += len(chunk)
        return chunk

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
        rc, _, err, seen = self.run_main([self.post], self.default_responder({}), environ={"STOCK_PROVIDER": "pexels"})
        self.assertEqual((rc, seen), (2, []))
        self.assertIn("Pexels 키가 없습니다 — .env의 STOCK_PROVIDER를 openverse로 고치거나 그 줄을 지우면 키 없이 무료 스톡을 씁니다", err)
        self.assertEqual(len(err.strip().splitlines()), 1)
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
        rc, out, _, _ = self.run_main([self.post, "--dry-run"], environ={"STOCK_PROVIDER": "pexels"})
        self.assertEqual(rc, 0)
        self.assertIn("스톡: pexels · 키: 없음", out)
        rc, out, _, _ = self.run_main([self.post, "--dry-run"])  # 아무 설정도 없으면 openverse
        self.assertEqual(rc, 0)
        self.assertEqual(out.splitlines()[0], "스톡: openverse · 키: 필요 없음")

    def test_help_exit_0(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(fetch_stock.main(["--help"]), 0)


def jpeg_bytes(width, height=600, tag=b""):
    """SOF0 헤더만 있는 최소 JPEG(가로 판정용)."""
    app0 = b"\xff\xe0" + (16).to_bytes(2, "big") + b"JFIF\x00" + b"\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof = b"\xff\xc0" + (17).to_bytes(2, "big") + b"\x08" + height.to_bytes(2, "big") + width.to_bytes(2, "big") + \
        b"\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01"
    return b"\xff\xd8" + app0 + sof + b"\xff\xd9" + tag


def png_bytes(width, height=600):
    ihdr = width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"
    return b"\x89PNG\r\n\x1a\n" + (13).to_bytes(4, "big") + b"IHDR" + ihdr + b"\x00\x00\x00\x00"


OV_PLAN = """# 이미지 계획
| 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 검색어(stock) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수 | 출처 |
|---|---|---|---|---|---|---|---|---|
| 03 | ## 3️⃣ 체인 청소 | 현장 | stock | laptop wooden desk | 책상 | | | |
| 04 | ## 4️⃣ 공기압 | 작업 | stock | bicycle tire pump | 공기 넣기 | | | |
"""


def ov_result(rid, width=2400, creator="Jane Doe", lic="cc0", source="flickr", url=None, landing=None):
    return {"id": f"id{rid}", "url": url if url is not None else f"https://live.staticflickr.com/{rid}/p.jpg",
            "width": width, "height": 1600, "creator": creator, "license": lic, "source": source,
            "provider": source, "foreign_landing_url": landing or f"https://www.flickr.com/photos/x/{rid}"}


def ov_body(results):
    return json.dumps({"result_count": len(results), "page_count": 1, "page_size": 20, "results": results})


class OpenverseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        self.work = os.path.join(self.tmp.name, "work")
        os.makedirs(self.work)
        os.chdir(self.work)
        self.post = self.make_post("003-chain", OV_PLAN)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def make_post(self, name, plan_text):
        post = os.path.join(self.work, "posts", name)
        os.makedirs(os.path.join(post, "images"), exist_ok=True)
        with open(os.path.join(post, "images", "image-plan.md"), "w", encoding="utf-8") as f:
            f.write(plan_text)
        return post

    def read_plan(self, post=None):
        with open(os.path.join(post or self.post, "images", "image-plan.md"), encoding="utf-8") as f:
            return f.read()

    def run_main(self, argv, responder=None, environ=None):
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append(req)
            return responder(req)

        out, err = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as st:
            st.enter_context(mock.patch.dict(os.environ, environ or {}, clear=True))
            st.enter_context(contextlib.redirect_stdout(out))
            st.enter_context(contextlib.redirect_stderr(err))
            if responder is not None:
                st.enter_context(mock.patch("urllib.request.urlopen", fake_urlopen))
            rc = fetch_stock.main(argv)
        text = out.getvalue() + err.getvalue()
        self.assertNotIn(FAKE_KEY, text)
        self.assertNotIn("FAKEKEY", text)
        return rc, out.getvalue(), err.getvalue(), seen

    @staticmethod
    def responder(results_by_query, files):
        """검색 URL → results, 그 외 URL → files[url](bytes) (없으면 JPEG 1600px)."""
        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                q = urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)["q"][0]
                return FakeResp(ov_body(results_by_query.get(q, [])))
            return FakeResp(files.get(req.full_url, jpeg_bytes(1600)))
        return fn

    def test_ok_saves_jpg_png_and_credit(self):
        results = {"laptop wooden desk": [ov_result(1, creator="Kim | Lee", lic="cc0")],
                   "bicycle tire pump": [ov_result(2, creator="", lic="pdm", source="wikimedia")]}
        files = {"https://live.staticflickr.com/1/p.jpg": jpeg_bytes(1600),
                 "https://live.staticflickr.com/2/p.jpg": png_bytes(1280)}
        rc, out, err, seen = self.run_main([self.post], self.responder(results, files))
        self.assertEqual(rc, 0, err)
        lines = out.strip().splitlines()
        self.assertEqual(lines[0], "스톡: openverse · 키: 필요 없음")
        self.assertEqual(lines[-1], "저장 2장 · 보류 0장")
        self.assertEqual(lines[1], "[OK] 03 → images/03-scene.jpg (출처: Openverse/flickr · Kim / Lee · CC0 https://www.flickr.com/photos/x/1)")
        req = seen[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(req.full_url, "https://api.openverse.org/v1/images/?q=laptop%20wooden%20desk"
                                       "&license=cc0,pdm&aspect_ratio=wide&mature=false&page_size=20")
        self.assertRegex(req.get_header("User-agent"),
                         r"^naver-blog-autopilot/\d+\.\d+\.\d+ \(\+https://github\.com/heesun-woodi/woodi-claude-plugins\)$")
        self.assertIsNone(req.get_header("Authorization"))
        with open(os.path.join(self.post, "images", "03-scene.jpg"), "rb") as f:
            self.assertEqual(f.read(), jpeg_bytes(1600))
        with open(os.path.join(self.post, "images", "04-work.png"), "rb") as f:  # PNG는 .png로 저장
            self.assertEqual(f.read(), png_bytes(1280))
        plan = self.read_plan()
        self.assertIn("| images/03-scene.jpg | | 출처: Openverse/flickr · Kim / Lee · CC0 https://www.flickr.com/photos/x/1 |", plan)
        self.assertIn("| images/04-work.png | | 출처: Openverse/wikimedia · 작자 미상 · PDM https://www.flickr.com/photos/x/2 |", plan)

    def test_zero_results_held(self):
        rc, out, _, seen = self.run_main([self.post, "--only", "3"], self.responder({}, {}))
        self.assertEqual(rc, 0)
        self.assertEqual(len(seen), 2)  # 원 검색어 + 줄인 검색어
        self.assertIn("| 03 | ## 3️⃣ 체인 청소 | 현장 | stock | laptop wooden desk | 책상 | 보류 | 검색 결과 없음 | |", self.read_plan())
        self.assertEqual(out.strip().splitlines()[-1], "저장 0장 · 보류 1장")

    def test_skips_small_original_width_and_missing_url(self):
        results = {"laptop wooden desk": [ov_result(1, width=1199), ov_result(2, url=" "), ov_result(3, width=1200)]}
        rc, _, _, seen = self.run_main([self.post, "--only", "3"], self.responder(results, {}))
        self.assertEqual(rc, 0)
        self.assertEqual([r.full_url for r in seen[1:]], ["https://live.staticflickr.com/3/p.jpg"])  # 1·2번은 받지도 않음
        self.assertIn("flickr.com/photos/x/3", self.read_plan())

    def test_skips_downloaded_file_under_800_or_not_jpeg_png(self):
        results = {"laptop wooden desk": [ov_result(1), ov_result(2), ov_result(3), ov_result(4)]}
        files = {"https://live.staticflickr.com/1/p.jpg": jpeg_bytes(799),
                 "https://live.staticflickr.com/2/p.jpg": b"GIF89a....",
                 "https://live.staticflickr.com/3/p.jpg": png_bytes(800)}
        rc, _, _, seen = self.run_main([self.post, "--only", "3"], self.responder(results, files))
        self.assertEqual(rc, 0)
        self.assertEqual(len(seen), 4)  # 검색 1 + 받기 3(799 버림 · GIF 버림 · 800 PNG 채택)
        self.assertTrue(os.path.isfile(os.path.join(self.post, "images", "03-scene.png")))
        self.assertIn("flickr.com/photos/x/3", self.read_plan())

    def test_max_five_downloads_then_held(self):
        results = {"laptop wooden desk": [ov_result(n) for n in range(1, 9)]}
        files = {f"https://live.staticflickr.com/{n}/p.jpg": jpeg_bytes(500) for n in range(1, 9)}
        rc, out, _, seen = self.run_main([self.post, "--only", "3"], self.responder(results, files))
        self.assertEqual(rc, 0)
        self.assertEqual(len(seen), 1 + 5)  # 5번을 다 썼으면 재검색 없음
        self.assertIn("| 보류 | 검색 결과 없음 |", self.read_plan())
        self.assertEqual(os.listdir(os.path.join(self.post, "images")), ["image-plan.md"])

    def test_reuse_prevention_across_posts_and_within_post(self):
        other = OV_PLAN.replace("| 03 | ## 3️⃣ 체인 청소 | 현장 | stock | laptop wooden desk | 책상 | | | |",
                                "| 03 | ## 체인 | 현장 | stock | x | 책상 | images/03-scene.jpg | | 출처: Openverse/flickr · A · CC0 https://www.flickr.com/photos/x/1 |")
        self.make_post("001-other", other)
        results = {"laptop wooden desk": [ov_result(1), ov_result(2)], "bicycle tire pump": [ov_result(2), ov_result(5)]}
        rc, _, _, seen = self.run_main([self.post], self.responder(results, {}))
        self.assertEqual(rc, 0)
        plan = self.read_plan()
        self.assertIn("flickr.com/photos/x/2 |", plan.splitlines()[3])  # 다른 글이 쓴 1번은 건너뛰고 2번
        self.assertIn("flickr.com/photos/x/5 |", plan.splitlines()[4])  # 같은 글 03이 쓴 2번도 건너뜀
        self.assertNotIn("flickr.com/photos/x/1 ", plan)
        # 다시 받아도(자기 행 덮어쓰기) 자기 사진은 허용: 03 행만 다시
        rc, _, _, _ = self.run_main([self.post, "--only", "03"], self.responder(results, {}))
        self.assertEqual(rc, 0)
        self.assertIn("flickr.com/photos/x/2 |", self.read_plan().splitlines()[3])

    def test_shortened_query_retry(self):
        results = {"laptop wooden": [ov_result(1)]}  # 3단어 "laptop wooden desk"는 0건
        rc, out, _, seen = self.run_main([self.post, "--only", "3"], self.responder(results, {}))
        self.assertEqual(rc, 0)
        qs = [urllib.parse.parse_qs(urllib.parse.urlsplit(r.full_url).query)["q"][0]
              for r in seen if r.full_url.startswith(fetch_stock.OPENVERSE_URL)]
        self.assertEqual(qs, ["laptop wooden desk", "laptop wooden"])
        self.assertIn(" (검색어 줄임: laptop wooden)", out)
        self.assertIn("| 03 | ## 3️⃣ 체인 청소 | 현장 | stock | laptop wooden desk | 책상 | images/03-scene.jpg |", self.read_plan())
        # 2단어는 재검색 없음
        self.make_post("005-two", OV_PLAN.replace("laptop wooden desk", "laptop desk"))
        rc, out, _, seen = self.run_main([os.path.join(self.work, "posts", "005-two"), "--only", "3"], self.responder({}, {}))
        self.assertEqual(len(seen), 1)
        self.assertIn("검색 결과 없음", out)

    def test_download_errors_skip_candidate_and_all_failed_held(self):
        results = {"laptop wooden desk": [ov_result(n) for n in range(1, 4)]}

        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                return FakeResp(ov_body(results["laptop wooden desk"]) if "wooden%20desk" in req.full_url else ov_body([]))
            n = req.full_url.split("/")[3]
            if n == "1":
                raise urllib.error.HTTPError(req.full_url, 403, "x", {}, io.BytesIO(b""))
            if n == "2":
                raise urllib.error.URLError("reset")
            return FakeResp(jpeg_bytes(1600))
        rc, out, _, _ = self.run_main([self.post, "--only", "3"], fn)
        self.assertEqual(rc, 0)
        self.assertIn("flickr.com/photos/x/3", self.read_plan())

        def all_fail(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                return FakeResp(ov_body(results["laptop wooden desk"]))
            raise urllib.error.HTTPError(req.full_url, 429, "x", {}, io.BytesIO(b""))
        with open(os.path.join(self.post, "images", "image-plan.md"), "w", encoding="utf-8") as f:
            f.write(OV_PLAN)
        rc, out, _, _ = self.run_main([self.post, "--only", "3"], all_fail)
        self.assertEqual(rc, 0)
        self.assertIn("[보류] 03 사진 받기 실패", out)
        self.assertIn("| 보류 | 사진 받기 실패 |", self.read_plan())

    @staticmethod
    def err403(req):
        return urllib.error.HTTPError(req.full_url, 403, "x", {}, io.BytesIO(b""))

    def downloads(self, seen):
        return [r.full_url for r in seen if not r.full_url.startswith(fetch_stock.OPENVERSE_URL)]

    def test_budget_A_six_download_errors_then_no_fallback_search(self):
        results = {"laptop wooden desk": [ov_result(n) for n in range(1, 7)]}

        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                return FakeResp(ov_body(results.get(urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)["q"][0], [])))
            raise self.err403(req)
        rc, out, _, seen = self.run_main([self.post, "--only", "3"], fn)
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.downloads(seen)), 5)
        self.assertEqual(len(seen), 6)  # 5번을 다 썼으니 재검색 없음
        self.assertIn("[보류] 03 사진 받기 실패", out)
        self.assertIn("| 보류 | 사진 받기 실패 |", self.read_plan())

    def test_budget_A2_fallback_zero_results_after_errors(self):
        results = {"laptop wooden desk": [ov_result(n) for n in range(1, 4)]}

        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                return FakeResp(ov_body(results.get(urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)["q"][0], [])))
            raise self.err403(req)
        rc, out, _, seen = self.run_main([self.post, "--only", "3"], fn)
        self.assertEqual(len(self.downloads(seen)), 3)
        self.assertIn("[보류] 03 사진 받기 실패", out)  # 시도는 모두 받기 오류, 폴백은 0건

    def test_budget_B_small_files_total_five_across_searches(self):
        results = {"laptop wooden desk": [ov_result(n) for n in (1, 2, 3)],
                   "laptop wooden": [ov_result(n) for n in (4, 5, 6, 7)]}
        files = {f"https://live.staticflickr.com/{n}/p.jpg": jpeg_bytes(500) for n in range(1, 8)}
        rc, out, _, seen = self.run_main([self.post, "--only", "3"], self.responder(results, files))
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.downloads(seen)), 5)  # 3 + 2
        self.assertIn("[보류] 03 검색 결과 없음", out)  # 탈락이 섞이면 검색 결과 없음

    def test_budget_C_same_url_not_downloaded_twice(self):
        results = {"laptop wooden desk": [ov_result(1), ov_result(2)], "laptop wooden": [ov_result(1), ov_result(2), ov_result(3)]}
        files = {f"https://live.staticflickr.com/{n}/p.jpg": jpeg_bytes(500) for n in (1, 2)}
        rc, out, _, seen = self.run_main([self.post, "--only", "3"], self.responder(results, files))
        urls = self.downloads(seen)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(urls, [f"https://live.staticflickr.com/{n}/p.jpg" for n in (1, 2, 3)])
        self.assertIn("(검색어 줄임: laptop wooden)", out)

    def test_filetype_prefilter(self):
        tif = ov_result(1); tif["filetype"] = "tiff"
        jpg = ov_result(2); jpg["filetype"] = "JPG"
        results = {"laptop wooden desk": [tif, jpg, ov_result(3)]}
        rc, _, _, seen = self.run_main([self.post, "--only", "3"], self.responder(results, {}))
        self.assertEqual(self.downloads(seen), ["https://live.staticflickr.com/2/p.jpg"])

    def test_header_gate_content_type_and_length_skip_without_reading(self):
        results = {"laptop wooden desk": [ov_result(1), ov_result(2), ov_result(3)]}
        resps = {}

        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                return FakeResp(ov_body(results["laptop wooden desk"]))
            n = req.full_url.split("/")[3]
            hdr = {"1": {"Content-Type": "image/tiff"},
                   "2": {"Content-Type": "image/jpeg", "Content-Length": "8000001"}}.get(n)
            resps[n] = FakeResp(jpeg_bytes(1600), hdr)
            return resps[n]
        rc, out, _, seen = self.run_main([self.post, "--only", "3"], fn)
        self.assertEqual(rc, 0)
        self.assertEqual((resps["1"].read_calls, resps["2"].read_calls), (0, 0))  # 본문 미독
        self.assertGreater(resps["3"].read_calls, 0)
        self.assertIn("flickr.com/photos/x/3", self.read_plan())

    def test_oversize_body_without_length_aborts_early(self):
        results = {"laptop wooden desk": [ov_result(1), ov_result(2)]}
        resps = {}

        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                return FakeResp(ov_body(results["laptop wooden desk"]))
            n = req.full_url.split("/")[3]
            resps[n] = FakeResp(jpeg_bytes(1600, tag=b"0" * 8_100_000) if n == "1" else jpeg_bytes(1600))
            return resps[n]
        rc, _, _, seen = self.run_main([self.post, "--only", "3"], fn)
        self.assertEqual(rc, 0)
        self.assertLess(resps["1"].pos, 8_100_000)  # 상한을 넘는 순간 중단 — 끝까지 읽지 않음
        self.assertIn("flickr.com/photos/x/2", self.read_plan())

    def test_truncated_body_is_download_error_next_candidate(self):
        results = {"laptop wooden desk": [ov_result(1), ov_result(2)]}

        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                return FakeResp(ov_body(results["laptop wooden desk"]))
            if "/1/" in req.full_url:
                return FakeResp(jpeg_bytes(1600, tag=b"0" * 100000), {"Content-Type": "image/jpeg", "Content-Length": "300000"})
            return FakeResp(jpeg_bytes(1600))
        rc, out, _, seen = self.run_main([self.post, "--only", "3"], fn)
        self.assertEqual(rc, 0)
        self.assertIn("flickr.com/photos/x/2", self.read_plan())
        self.assertEqual(len(self.downloads(seen)), 2)
        with open(os.path.join(self.post, "images", "03-scene.jpg"), "rb") as f:
            self.assertEqual(f.read(), jpeg_bytes(1600))  # 잘린 본문은 쓰이지 않음

    def test_chunked_ignores_content_length(self):
        results = {"laptop wooden desk": [ov_result(1)]}

        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                return FakeResp(ov_body(results["laptop wooden desk"]))
            r = FakeResp(jpeg_bytes(1600), {"Content-Type": "image/jpeg", "Content-Length": "999999"})
            r.chunked = True
            return r
        rc, out, _, _ = self.run_main([self.post, "--only", "3"], fn)
        self.assertEqual(rc, 0)
        self.assertIn("[OK] 03", out)

    def test_read_exceptions_skip_candidate(self):
        results = {"laptop wooden desk": [ov_result(1), ov_result(2), ov_result(3)]}

        class Boom(FakeResp):
            def __init__(self, exc):
                super().__init__(jpeg_bytes(1600))
                self.exc = exc

            def read(self, n=-1):
                raise self.exc

        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                return FakeResp(ov_body(results["laptop wooden desk"]))
            if "/1/" in req.full_url:
                return Boom(http.client.IncompleteRead(b"ab", 10))
            if "/2/" in req.full_url:
                return Boom(UnicodeEncodeError("ascii", "é", 0, 1, "bad"))
            return FakeResp(jpeg_bytes(1600))
        rc, out, _, _ = self.run_main([self.post, "--only", "3"], fn)
        self.assertEqual(rc, 0)
        self.assertIn("[OK] 03", out)
        self.assertIn("flickr.com/photos/x/3", self.read_plan())

    def test_ambiguous_headers_use_magic_bytes(self):
        results = {"laptop wooden desk": [ov_result(1)], "bicycle tire pump": [ov_result(2), ov_result(3), ov_result(4)]}
        tiff = b"II*\x00" + b"\x00" * 100

        def fn(req):
            if req.full_url.startswith(fetch_stock.OPENVERSE_URL):
                q = urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)["q"][0]
                return FakeResp(ov_body(results.get(q, [])))
            n = req.full_url.split("/")[3]
            return {"1": FakeResp(jpeg_bytes(1600), {"Content-Type": "image/jpg"}),
                    "2": FakeResp(tiff, {"Content-Type": "application/octet-stream"}),
                    "3": FakeResp(png_bytes(1600), {}),
                    "4": FakeResp(jpeg_bytes(1600))}[n]
        rc, out, _, seen = self.run_main([self.post], fn)
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.post, "images", "03-scene.jpg")))  # image/jpg 헤더 → 받음
        self.assertTrue(os.path.isfile(os.path.join(self.post, "images", "04-work.png")))  # 헤더 없음 PNG → .png
        self.assertEqual(len(self.downloads(seen)), 3)  # octet-stream TIFF는 받은 뒤 건너뜀

    def test_exit6_429_and_exit5_5xx_and_not_json(self):
        def err_resp(status):
            def fn(req):
                raise urllib.error.HTTPError(req.full_url, status, "err", {}, io.BytesIO(b"{}"))
            return fn
        rc, _, err, seen = self.run_main([self.post], err_resp(429))
        self.assertEqual((rc, len(seen)), (6, 1))
        self.assertIn("Openverse 429", err)
        self.assertEqual(self.read_plan(), OV_PLAN)
        rc, _, err, _ = self.run_main([self.post], err_resp(503))
        self.assertEqual(rc, 5)
        self.assertIn("Openverse HTTP 503", err)
        rc, _, err, _ = self.run_main([self.post], err_resp(403))
        self.assertEqual(rc, 3)
        rc, _, err, _ = self.run_main([self.post], lambda req: FakeResp("<html>not json</html>"))
        self.assertEqual(rc, 5)
        self.assertIn("JSON 아님", err)

        def offline(req):
            raise urllib.error.URLError("no route")
        rc, _, err, _ = self.run_main([self.post], offline)
        self.assertEqual(rc, 5)

    def test_provider_errors_exit2(self):
        for bad in ("gemini", "OPENVERSE2", "zzqq"):
            rc, out, err, seen = self.run_main([self.post], self.responder({}, {}), environ={"STOCK_PROVIDER": bad})
            self.assertEqual((rc, seen), (2, []))
            self.assertIn("STOCK_PROVIDER 값이 올바르지 않습니다", err)
            self.assertNotIn(bad, out + err.replace("STOCK_PROVIDER", ""))  # 값은 출력하지 않음
        rc, _, err, seen = self.run_main([self.post], self.responder({}, {}), environ={"STOCK_PROVIDER": "pexels"})
        self.assertEqual((rc, seen), (2, []))  # 다른 제공자로 넘어가지 않음
        self.assertIn("Pexels 키가 없습니다 — .env의 STOCK_PROVIDER를 openverse로 고치거나", err)
        self.assertNotIn("pexels.com", err)
        rc, _, _, seen = self.run_main([self.post, "--dry-run"], environ={"STOCK_PROVIDER": "nope"})
        self.assertEqual((rc, seen), (2, []))

    def test_resolve_stock_provider(self):
        r = fetch_stock.resolve_stock_provider
        self.assertEqual(r({}), ("openverse", None, None))
        self.assertEqual(r({"PEXELS_API_KEY": FAKE_KEY, "key_source": "환경변수"}), ("pexels", FAKE_KEY, "환경변수"))
        self.assertEqual(r({"STOCK_PROVIDER": "openverse", "PEXELS_API_KEY": FAKE_KEY}), ("openverse", None, None))
        self.assertEqual(r({"STOCK_PROVIDER": " Pexels ", "PEXELS_API_KEY": FAKE_KEY, "key_source": "x"})[0], "pexels")
        with self.assertRaises(fetch_stock.ConfigError) as c:
            r({"STOCK_PROVIDER": "pexels"})
        self.assertEqual(c.exception.kind, "nokey")
        with self.assertRaises(fetch_stock.ConfigError) as c:
            r({"STOCK_PROVIDER": "bing", "PEXELS_API_KEY": FAKE_KEY})
        self.assertEqual(c.exception.kind, "invalid")
        self.assertNotIn("bing", str(c.exception))

    def test_env_file_provider_and_search_order(self):
        envfile = os.path.join(self.tmp.name, "k.env")
        with open(envfile, "w") as f:
            f.write(f"STOCK_PROVIDER=openverse\nPEXELS_API_KEY={FAKE_KEY}\n")
        env = fetch_stock.find_stock_env(os.path.join(self.post, "images", "image-plan.md"), envfile)
        self.assertEqual((env["STOCK_PROVIDER"], env["PEXELS_API_KEY"], env["key_source"]), ("openverse", FAKE_KEY, envfile))
        # 키가 있어도 STOCK_PROVIDER=openverse면 Pexels를 부르지 않는다
        rc, out, _, seen = self.run_main([self.post, "--env", envfile], self.responder({}, {}))
        self.assertEqual(rc, 0)
        self.assertEqual(out.splitlines()[0], "스톡: openverse · 키: 필요 없음")
        self.assertTrue(all(r.full_url.startswith(fetch_stock.OPENVERSE_URL) for r in seen))
        # plan 상위 폴더 .env
        with open(os.path.join(self.work, "posts", ".env"), "w") as f:
            f.write("STOCK_PROVIDER=pexels\n")
        env = fetch_stock.find_stock_env(os.path.join(self.post, "images", "image-plan.md"))
        self.assertEqual(env["STOCK_PROVIDER"], "pexels")

    def test_key_present_auto_selects_pexels(self):
        pexels_plan = PLAN_WITH_SOURCE
        post = self.make_post("004-pexels", pexels_plan)
        envfile = os.path.join(self.tmp.name, "k.env")
        with open(envfile, "w") as f:
            f.write(f"PEXELS_API_KEY={FAKE_KEY}\n")

        def fn(req):
            if req.full_url.startswith(fetch_stock.SEARCH_URL):
                return FakeResp(search_body([photo(2, 4000)]))
            return FakeResp(b"\xff\xd8x")
        rc, out, err, seen = self.run_main([post, "--env", envfile, "--only", "03"], fn)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.splitlines()[0], f"스톡: pexels · 키: {envfile}")
        self.assertTrue(seen[0].full_url.startswith(fetch_stock.SEARCH_URL))
        self.assertEqual(seen[0].get_header("Authorization"), FAKE_KEY)

    def test_dry_run_openverse_no_socket_no_write(self):
        counter = mock.MagicMock(side_effect=AssertionError("소켓 사용 금지"))
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(socket, "socket", counter), \
                mock.patch.object(socket, "create_connection", counter), \
                mock.patch.object(socket, "getaddrinfo", counter), \
                mock.patch("urllib.request.urlopen", counter), \
                mock.patch.dict(os.environ, {}, clear=True), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = fetch_stock.main([self.post, "--dry-run"])
        self.assertEqual(rc, 0, err.getvalue())
        self.assertEqual(counter.call_count, 0)
        self.assertEqual(out.getvalue().strip().splitlines(), [
            "스톡: openverse · 키: 필요 없음",
            "03 · laptop wooden desk · images/03-scene.jpg|png",
            "04 · bicycle tire pump · images/04-work.jpg|png",
            "(dry-run) 네트워크 접속 없음 · 대상 2장"])
        self.assertEqual(self.read_plan(), OV_PLAN)
        self.assertEqual(os.listdir(os.path.join(self.post, "images")), ["image-plan.md"])

    def test_key_value_never_printed(self):
        # pexels 경로에서 서버 오류 본문에 키가 섞여도 출력되지 않는다(run_main이 FAKE_KEY 부재를 검사)
        envfile = os.path.join(self.tmp.name, "k.env")
        with open(envfile, "w") as f:
            f.write(f"STOCK_PROVIDER=pexels\nPEXELS_API_KEY={FAKE_KEY}\n")

        def fn(req):
            raise urllib.error.HTTPError(req.full_url, 401, "bad", {}, io.BytesIO(FAKE_KEY.encode()))
        rc, _, err, _ = self.run_main([self.post, "--env", envfile], fn)
        self.assertEqual(rc, 3)

    def test_image_info(self):
        self.assertEqual(fetch_stock.image_info(jpeg_bytes(1234)), (".jpg", 1234))
        self.assertEqual(fetch_stock.image_info(png_bytes(4000)), (".png", 4000))
        self.assertIsNone(fetch_stock.image_info(b"\xff\xd8\xff\xd9"))
        self.assertIsNone(fetch_stock.image_info(b"RIFF....WEBP"))
        self.assertIsNone(fetch_stock.image_info(b""))

    def test_plugin_version_reads_plugin_json_or_constant(self):
        self.assertRegex(fetch_stock.plugin_version(), r"^\d+\.\d+\.\d+$")
        with mock.patch("builtins.open", side_effect=OSError):
            self.assertEqual(fetch_stock.plugin_version(), fetch_stock.PLUGIN_VERSION)


if __name__ == "__main__":
    unittest.main()
