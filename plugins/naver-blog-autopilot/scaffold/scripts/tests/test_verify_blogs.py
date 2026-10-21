import contextlib
import datetime
import io
import json
import os
import sys
import unittest
import urllib.error
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import verify_blogs  # noqa: E402

TODAY = datetime.date(2026, 10, 21)


def rss(items, title="테스트 블로그"):
    body = "".join(
        f"<item><title>{t}</title><link>https://blog.naver.com/gana_bike/{n}?fromRss=true</link>"
        f"<guid>https://blog.naver.com/gana_bike/{n}</guid><category>{c}</category>"
        f"<pubDate>{d}</pubDate></item>" for t, n, c, d in items)
    return f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{title}</title>{body}</channel></rss>'


ITEMS = [
    ("체인 청소 방법", "224000000005", "정비 팁", "Mon, 19 Oct 2026 10:00:00 +0900"),
    ("브레이크 점검", "224000000004", "정비 팁", "Thu, 01 Oct 2026 10:00:00 +0900"),
    ("가을 라이딩 코스", "224000000003", "코스", "Tue, 15 Sep 2026 10:00:00 +0900"),
    ("타이어 공기압 | 기준", "224000000002", "정비 팁", "Mon, 10 Aug 2026 10:00:00 +0900"),
    ("매장 휴무 안내", "224000000001", "공지", "Mon, 01 Jun 2026 10:00:00 +0900"),
]


class FakeResp:
    def __init__(self, body):
        self.body = body.encode("utf-8")

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(status):
    return urllib.error.HTTPError("https://rss.blog.naver.com/x.xml", status, "err", {}, io.BytesIO(b""))


class NormalizeTest(unittest.TestCase):
    def test_five_forms(self):
        cases = {
            "gana_bike": ("gana_bike", None),
            "https://blog.naver.com/gana_bike": ("gana_bike", None),
            "https://blog.naver.com/gana_bike/": ("gana_bike", None),
            "https://blog.naver.com/gana_bike/224000000005": ("gana_bike", "224000000005"),
            "https://m.blog.naver.com/gana_bike/224000000005": ("gana_bike", "224000000005"),
            "https://blog.naver.com/PostView.naver?blogId=gana_bike&logNo=224000000005": ("gana_bike", "224000000005"),
            "blog.naver.com/gana-bike2": ("gana-bike2", None),
            "http://m.blog.naver.com/PostView.naver?blogId=gana_bike&logNo=7&redirect=Dlog": ("gana_bike", "7"),
        }
        for raw, want in cases.items():
            self.assertEqual(verify_blogs.normalize(raw), want, raw)

    def test_bad_forms(self):
        for raw in ("가나자전거", "https://cafe.naver.com/gana", "https://blog.naver.com/gana/bike/1",
                    "https://blog.naver.com/PostView.naver?logNo=1", "https://blog.naver.com/gana/abc", "a b", ""):
            with self.assertRaises(ValueError, msg=raw):
                verify_blogs.normalize(raw)


class VerifyBlogsTest(unittest.TestCase):
    def run_main(self, argv, responder):
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append((req, timeout))
            return responder(req)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch("urllib.request.urlopen", fake_urlopen), mock.patch("time.sleep"), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = verify_blogs.main(argv, today=TODAY)
        return rc, out.getvalue(), err.getvalue(), seen

    def test_ok_table_counts_categories_titles(self):
        rc, out, _, seen = self.run_main(["https://blog.naver.com/gana_bike/224000000005"],
                                         lambda r: FakeResp(rss(ITEMS)))
        self.assertEqual(rc, 0)
        req, timeout = seen[0]
        self.assertEqual(req.full_url, "https://rss.blog.naver.com/gana_bike.xml")
        self.assertEqual(req.get_header("User-agent"), verify_blogs.fetch_posts.UA)
        self.assertEqual(timeout, 10)
        lines = out.strip().splitlines()
        self.assertEqual(lines[0], "| ID | 응답 | 최근 90일 글 수 | 월 추정 | 카테고리 상위 3 | 최근 제목 3 |")
        # 90일 이내(2026-07-23 이후): 10/19, 10/01, 09/15, 08/10 → 4편, 월 추정 4/3 = 1.3
        self.assertEqual(lines[2], "| gana_bike | OK | 4 | 1.3 | 정비 팁, 코스, 공지 | 체인 청소 방법 / 브레이크 점검 / 가을 라이딩 코스 |")

    def test_json_shape_and_days(self):
        rc, out, _, _ = self.run_main(["gana_bike", "--json", "--days", "30"], lambda r: FakeResp(rss(ITEMS)))
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(len(data), 1)
        row = data[0]
        self.assertEqual(set(row), {"blogId", "logNo", "status", "recent_count", "per_month", "categories", "recent", "error"})
        self.assertEqual((row["blogId"], row["logNo"], row["status"], row["error"]), ("gana_bike", None, "OK", None))
        self.assertEqual((row["recent_count"], row["per_month"]), (2, 2.0))
        self.assertEqual(row["recent"][0], {"title": "체인 청소 방법", "date": "2026-10-19",
                                            "logNo": "224000000005", "category": "정비 팁"})
        self.assertEqual(len(row["recent"]), 3)

    def test_pipe_in_title_escaped(self):
        items = [ITEMS[3]]
        rc, out, _, _ = self.run_main(["gana_bike"], lambda r: FakeResp(rss(items)))
        self.assertEqual(rc, 0)
        self.assertIn("타이어 공기압 \\| 기준", out)

    def test_statuses_per_row(self):
        def responder(req):
            url = req.full_url
            if "/okblog." in url:
                return FakeResp(rss(ITEMS))
            if "/gone." in url:
                raise http_error(404)
            if "/nochan." in url:
                return FakeResp("<html>not found</html>")
            if "/private." in url:
                return FakeResp(rss([]))
            raise urllib.error.URLError("no route")
        rc, out, err, seen = self.run_main(["okblog", "gone", "nochan", "private", "netfail", "가나", "--json"], responder)
        self.assertEqual(rc, 0)
        st = [(r["blogId"], r["status"]) for r in json.loads(out)]
        self.assertEqual(st, [("okblog", "OK"), ("gone", "없음"), ("nochan", "없음"), ("private", "비공개"),
                              ("netfail", "네트워크"), ("가나", "형식 오류")])
        self.assertEqual(len(seen), 5)  # 형식 오류는 요청하지 않음
        self.assertIn("경고: gone — 없음", err)

    def test_same_blog_fetched_once(self):
        rc, out, _, seen = self.run_main(["gana_bike", "https://m.blog.naver.com/gana_bike/224000000004", "--json"],
                                         lambda r: FakeResp(rss(ITEMS)))
        self.assertEqual(rc, 0)
        self.assertEqual(len(seen), 1)
        self.assertEqual([r["logNo"] for r in json.loads(out)], [None, "224000000004"])

    def test_exit_codes(self):
        rc, _, err, seen = self.run_main([], lambda r: FakeResp(""))
        self.assertEqual((rc, seen), (2, []))
        rc, _, _, seen = self.run_main(["가나", "https://cafe.naver.com/x"], lambda r: FakeResp(""))
        self.assertEqual((rc, seen), (2, []))

        def netfail(req):
            raise urllib.error.URLError("offline")
        rc, out, _, _ = self.run_main(["a1", "b2", "가나"], netfail)
        self.assertEqual(rc, 5)
        self.assertIn("| a1 | 네트워크 | - | - | - | - |", out)

        def server_error(req):
            raise http_error(503)
        rc, _, _, _ = self.run_main(["a1"], server_error)
        self.assertEqual(rc, 5)

        def gone(req):
            raise http_error(404)
        rc, _, _, _ = self.run_main(["a1"], gone)
        self.assertEqual(rc, 2)

    def test_help_exit_0(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify_blogs.main(["--help"]), 0)


if __name__ == "__main__":
    unittest.main()
