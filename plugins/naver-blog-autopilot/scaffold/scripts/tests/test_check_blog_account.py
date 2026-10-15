import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import check_blog_account as cba  # noqa: E402  (naver_blog_cli 는 check() 안에서만 import)


class BlogOwnerTest(unittest.TestCase):
    def test_path_and_query(self):
        self.assertEqual(cba.blog_owner("https://blog.naver.com/example_blog?Redirect=Write"), "example_blog")
        self.assertEqual(cba.blog_owner("https://blog.naver.com/other_account"), "other_account")
        self.assertEqual(cba.blog_owner("https://blog.naver.com/PostList.naver?blogId=abc&from=x"), "abc")
        self.assertEqual(cba.blog_owner("https://blog.naver.com/PostWriteForm.naver?blogId=example_blog"), "example_blog")
        self.assertIsNone(cba.blog_owner("https://blog.naver.com/MyBlog.naver"))
        self.assertIsNone(cba.blog_owner("https://nid.naver.com/nidlogin.login"))
        self.assertIsNone(cba.blog_owner(""))


class JudgeTest(unittest.TestCase):
    def test_target_editor_ok(self):
        code, _ = cba.judge("example_blog", "https://blog.naver.com/example_blog?Redirect=Write",
                            "https://blog.naver.com/PostWriteForm.naver?blogId=example_blog")
        self.assertEqual(code, 0)

    def test_case_insensitive(self):
        self.assertEqual(cba.judge("Example_Blog", "https://blog.naver.com/example_blog?Redirect=Write")[0], 0)

    def test_redirect_to_other_blog_measured(self):
        # 실측: 다른 계정 세션으로 대상 블로그 글쓰기를 열면 그 계정 블로그 홈으로 간다
        code, why = cba.judge("example_blog", "https://blog.naver.com/other_account",
                              "https://blog.naver.com/PostList.naver?blogId=other_account")
        self.assertEqual(code, 21)
        self.assertIn("other_account", why)

    def test_frame_owner_mismatch(self):
        code, _ = cba.judge("example_blog", "https://blog.naver.com/example_blog?Redirect=Write",
                            "https://blog.naver.com/PostList.naver?blogId=other_account")
        self.assertEqual(code, 21)

    def test_unknown_page_is_inconclusive(self):
        # 블로그 주인을 알 수 없는 곳(오류·점검·보안 확인)은 계정 문제로 단정하지 않는다
        self.assertEqual(cba.judge("example_blog", "https://section.blog.naver.com/BlogHome.naver")[0], 22)
        self.assertEqual(cba.judge("example_blog", "https://www.naver.com/")[0], 22)

    def test_blank_frame_still_judged_by_page(self):
        self.assertEqual(cba.judge("example_blog", "https://blog.naver.com/example_blog?Redirect=Write", "about:blank")[0], 0)

    def test_login_page(self):
        self.assertEqual(cba.judge("example_blog", "https://nid.naver.com/nidlogin.login?url=x")[0], 20)
        self.assertEqual(cba.judge("example_blog", "https://blog.naver.com/example_blog?Redirect=Write",
                                   "https://nid.naver.com/nidlogin.login")[0], 20)

    def test_usage(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cba.main(["x"]), 2)
            self.assertEqual(cba.main(["x", " "]), 2)
        self.assertIn("사용:", out.getvalue())


class _Loc:
    pass


class _Frame:
    def __init__(self, url):
        self.url = url


class _Page:
    def __init__(self, landing, frame_url):
        self.url, self._landing, self.frame = "", landing, _Frame(frame_url)

    async def goto(self, url, wait_until=None):
        self.url = self._landing


class _Ctx:
    def __init__(self, page):
        self.page = page

    async def new_page(self):
        return self.page


class CheckFlowTest(unittest.TestCase):
    """check() 분기 — naver_blog_cli 를 가짜 모듈로 바꿔 브라우저 없이 돈다."""

    def run_check(self, landing, frame_url="https://blog.naver.com/PostWriteForm.naver?blogId=example_blog",
                  title=True, wait_exc=None, state=True, session_exc=None):
        import asyncio
        import pathlib
        import types
        page = _Page(landing, frame_url)
        calls = {"wait": 0}

        class Session:
            def __init__(self, headless=None):
                assert headless is True

            async def __aenter__(self):
                if session_exc:
                    raise session_exc
                return _Ctx(page)

            async def __aexit__(self, *exc):
                return False

        async def wait_for_editor(p):
            calls["wait"] += 1
            if wait_exc:
                raise wait_exc

        async def get_editor_frame(p):
            return p.frame

        async def first(scope, cands, timeout=3000):
            return _Loc() if title else None

        tmp = self.enterContext(__import__("tempfile").TemporaryDirectory())
        st = pathlib.Path(tmp, "state.json")
        if state:
            st.write_text("{}")
        mods = {
            "naver_blog_cli": types.ModuleType("naver_blog_cli"),
            "naver_blog_cli.selectors": types.SimpleNamespace(
                WRITE_URL="https://blog.naver.com/{blog_id}?Redirect=Write", TITLE=["t"], first=first),
            "naver_blog_cli.editor": types.SimpleNamespace(wait_for_editor=wait_for_editor,
                                                           get_editor_frame=get_editor_frame),
            "naver_blog_cli.session": types.SimpleNamespace(STATE=st, Session=Session),
        }
        mods["naver_blog_cli"].selectors = mods["naver_blog_cli.selectors"]
        saved = {k: sys.modules.get(k) for k in mods}
        sys.modules.update(mods)
        os.environ["NAVER_KEEP_OPEN"] = "1"
        try:
            code, why = asyncio.run(cba.check("example_blog"))
        finally:
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
        self.assertNotIn("NAVER_KEEP_OPEN", os.environ)
        return code, why, calls

    def test_ok(self):
        self.assertEqual(self.run_check("https://blog.naver.com/example_blog?Redirect=Write")[0], 0)

    def test_redirect_other_blog(self):
        code, why, _ = self.run_check("https://blog.naver.com/other_account", title=False)
        self.assertEqual(code, 21)
        self.assertIn("other_account", why)

    def test_no_title_is_inconclusive(self):
        # URL 이 아직 대상 그대로여도 에디터 제목 영역이 안 보이면 통과시키지 않는다
        self.assertEqual(self.run_check("https://blog.naver.com/example_blog?Redirect=Write", title=False)[0], 22)

    def test_wait_error(self):
        code, why, _ = self.run_check("https://blog.naver.com/example_blog?Redirect=Write",
                                      wait_exc=RuntimeError("에디터 프레임이 20초 안에 안 붙었습니다"))
        self.assertEqual(code, 22)
        self.assertIn("에디터가 뜨지 않음", why)

    def test_login_page_skips_wait(self):
        code, _, calls = self.run_check("https://nid.naver.com/nidlogin.login")
        self.assertEqual(code, 20)
        self.assertEqual(calls["wait"], 0)

    def test_no_state_file(self):
        code, why, _ = self.run_check("x", state=False)
        self.assertEqual(code, 20)
        self.assertIn("세션 파일 없음", why)

    def test_browser_failure(self):
        code, why, _ = self.run_check("x", session_exc=RuntimeError(""))
        self.assertEqual(code, 22)
        self.assertIn("RuntimeError", why)


if __name__ == "__main__":
    unittest.main()
