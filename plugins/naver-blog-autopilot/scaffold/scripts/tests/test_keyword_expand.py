import contextlib
import io
import json
import os
import sys
import unittest
import urllib.error
import urllib.parse
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import keyword_expand  # noqa: E402

# SPEC 부록 B — 네이버 자동완성 응답 샘플(2026-10-21 실측, q=자전거 수리)
SAMPLE_B = """{
"query" : ["자전거 수리"],
"answer" : [],
"intend" : [],
"items" : [
[["자전거 수리점", "0"],["근처 자전거 수리점", "0"],["전기자전거 수리", "0"],["전기자전거 수리점", "0"],["자전거 수리", "0"],["자전거 수리키트", "0"],["근처 자전거 수리", "0"],["평택 자전거 수리", "0"],["청주 자전거 수리", "0"],["잠실 자전거 수리", "0"]]
]
}"""
SAMPLE_B_KEYWORDS = ["자전거 수리점", "근처 자전거 수리점", "전기자전거 수리", "전기자전거 수리점", "자전거 수리키트",
                     "근처 자전거 수리", "평택 자전거 수리", "청주 자전거 수리", "잠실 자전거 수리"]


def ac_body(keywords):
    return json.dumps({"query": ["x"], "answer": [], "intend": [], "items": [[[k, "0"] for k in keywords]]},
                      ensure_ascii=False)


class FakeResp:
    def __init__(self, body):
        self.body = body.encode("utf-8")

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def query_of(req):
    return urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)["q"][0]


class KeywordExpandTest(unittest.TestCase):
    def run_main(self, argv, bodies):
        """bodies: {질의: 응답 본문 또는 예외}. 없는 질의는 빈 items."""
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append((req, timeout))
            got = bodies.get(query_of(req), '{"items": []}')
            if isinstance(got, Exception):
                raise got
            return FakeResp(got)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch("urllib.request.urlopen", fake_urlopen), mock.patch("time.sleep"), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = keyword_expand.main(argv)
        return rc, out.getvalue(), err.getvalue(), seen

    def test_parse_sample_b(self):
        got = keyword_expand.parse_items(json.loads(SAMPLE_B))
        self.assertEqual(got[0], "자전거 수리점")
        self.assertEqual(len(got), 10)
        self.assertEqual(keyword_expand.parse_items({"items": []}), [])
        self.assertEqual(keyword_expand.parse_items({}), [])

    def test_request_url_headers_timeout(self):
        rc, out, _, seen = self.run_main(["자전거 수리"], {"자전거 수리": SAMPLE_B})
        self.assertEqual(rc, 0)
        req, timeout = seen[0]
        self.assertTrue(req.full_url.startswith("https://ac.search.naver.com/nx/ac?q=%EC%9E%90%EC%A0%84%EA%B1%B0%20%EC%88%98%EB%A6%AC&con=1&frm=nv&ans=2"))
        self.assertTrue(req.full_url.endswith("&r_format=json&r_enc=UTF-8&r_unicode=0&t_koreng=1&run=2&rev=4&q_enc=UTF-8&st=100"))
        self.assertEqual(req.get_header("User-agent"), "Mozilla/5.0")
        self.assertEqual(timeout, 5)
        self.assertEqual(len(seen), 1)  # depth 1 = 씨앗당 1회

    def test_depth1_table_excludes_seed(self):
        rc, out, _, _ = self.run_main(["자전거 수리"], {"자전거 수리": SAMPLE_B})
        lines = out.strip().splitlines()
        self.assertEqual(lines[:2], ["| 키워드 | 씨앗 |", "|---|---|"])
        self.assertEqual([l.split(" | ")[0][2:] for l in lines[2:]], SAMPLE_B_KEYWORDS)
        self.assertNotIn("| 자전거 수리 | 자전거 수리 |", out)

    def test_depth2_top5_requeried_dedupe_json(self):
        bodies = {"자전거 수리": SAMPLE_B,
                  "자전거 수리점": ac_body(["자전거 수리점 추천", "근처 자전거 수리점", "자전거  수리"]),
                  "근처 자전거 수리점": ac_body(["근처 자전거 수리점 24시"]),
                  "전기자전거 수리점": ac_body(["전기자전거 수리점 추천"])}
        rc, out, _, seen = self.run_main(["자전거 수리", "--depth", "2", "--json"], bodies)
        self.assertEqual(rc, 0)
        queried = [query_of(r) for r, _ in seen]
        self.assertEqual(queried, ["자전거 수리", "자전거 수리점", "근처 자전거 수리점", "전기자전거 수리",
                                   "전기자전거 수리점", "자전거 수리키트"])
        data = json.loads(out)
        self.assertEqual(set(data[0]), {"keyword", "seed", "depth"})
        self.assertEqual([d["keyword"] for d in data if d["depth"] == 1], SAMPLE_B_KEYWORDS)
        d2 = [(d["keyword"], d["seed"]) for d in data if d["depth"] == 2]
        self.assertEqual(d2, [("자전거 수리점 추천", "자전거 수리"), ("근처 자전거 수리점 24시", "자전거 수리"),
                              ("전기자전거 수리점 추천", "자전거 수리")])  # 중복·공백 변형·씨앗 제외
        kws = [d["keyword"] for d in data]
        self.assertEqual(len(kws), len(set(kws)))

    def test_max_and_multiple_seeds(self):
        bodies = {"자전거 수리": SAMPLE_B, "자전거 점검": ac_body(["자전거 점검 비용", "자전거 수리점", "자전거 수리"])}
        rc, out, _, _ = self.run_main(["자전거 수리", "자전거 점검", "--json", "--max", "10"], bodies)
        data = json.loads(out)
        self.assertEqual(len(data), 10)
        self.assertEqual(data[-1], {"keyword": "자전거 점검 비용", "seed": "자전거 점검", "depth": 1})

    def test_zero_results_exit0_empty_table(self):
        rc, out, err, _ = self.run_main(["없는말"], {"없는말": '{"query":["없는말"],"answer":[],"intend":[],"items":[]}'})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip().splitlines(), ["| 키워드 | 씨앗 |", "|---|---|"])
        self.assertIn("연관 검색어가 없습니다", err)

    def test_partial_failure_warns_and_continues(self):
        bodies = {"자전거 수리": SAMPLE_B, "자전거 점검": urllib.error.URLError("timed out")}
        rc, out, err, _ = self.run_main(["자전거 점검", "자전거 수리"], bodies)
        self.assertEqual(rc, 0)
        self.assertIn("경고: '자전거 점검' 자동완성 조회 실패", err)
        self.assertIn("| 자전거 수리점 | 자전거 수리 |", out)

    def test_all_fail_exit5_and_no_args_exit2(self):
        err5 = urllib.error.URLError("offline")
        rc, _, err, _ = self.run_main(["a", "b"], {"a": err5, "b": urllib.error.HTTPError("u", 500, "x", {}, io.BytesIO(b""))})
        self.assertEqual(rc, 5)
        rc, _, _, _ = self.run_main(["a"], {"a": "<html>blocked</html>"})
        self.assertEqual(rc, 5)
        rc, _, _, seen = self.run_main([], {})
        self.assertEqual((rc, seen), (2, []))
        rc, _, _, seen = self.run_main(["  "], {})
        self.assertEqual((rc, seen), (2, []))
        rc, _, _, _ = self.run_main(["a", "--depth", "3"], {})
        self.assertEqual(rc, 2)

    def test_help_exit_0(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(keyword_expand.main(["--help"]), 0)


if __name__ == "__main__":
    unittest.main()
