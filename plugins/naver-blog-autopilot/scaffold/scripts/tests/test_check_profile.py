import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "check_profile.py")
TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(HERE)), "knowledge", "business-profile.md")
# 가상 업체 — 필수 행을 모두 채운 profile
FILLED = ("# 업체 기본정보\n\n| 항목 | 내용 |\n|---|---|\n| 업체명 | 예시상회 |\n| 연락처 | 000-0000-0000 |\n"
          "| 상품·서비스 | 선물 포장, 단체 주문 |\n| 고객 지역 | 가나동, 다라동 |\n| 장소 검색어 | 예시상회 가나동 |\n"
          "| 업체 유형어 | 상회 |\n| 업종 일반어 | 선물 |\n\n## 금칙어\n\n- `금지어예시`\n")


class CheckProfileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def run_check(self, profile=None):
        """작업 폴더(cwd)의 knowledge/business-profile.md를 점검한다. profile=None이면 파일을 만들지 않는다."""
        if profile is not None:
            os.makedirs(os.path.join(self.root, "knowledge"), exist_ok=True)
            with open(os.path.join(self.root, "knowledge", "business-profile.md"), "w", encoding="utf-8") as f:
                f.write(profile)
        p = subprocess.run([sys.executable, SCRIPT], cwd=self.root, capture_output=True, text=True,
                           encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
        return p.returncode, p.stdout, p.stderr

    def test_ok(self):
        self.assertEqual(self.run_check(FILLED), (0, "profile: OK\n", ""))

    def test_missing_lists_unfilled_rows_of_scaffold_template(self):
        with open(TEMPLATE, encoding="utf-8") as f:
            template = f.read()
        self.assertEqual(self.run_check(template),
                         (2, "profile: MISSING 업체명,연락처,상품·서비스,고객 지역,장소 검색어,업체 유형어,업종 일반어,금칙어\n", ""))

    def test_nofile(self):
        self.assertEqual(self.run_check(), (2, "profile: NOFILE\n", ""))

    def test_forbidden_none_is_ok(self):
        self.assertEqual(self.run_check(FILLED.replace("- `금지어예시`", "- 없음")), (0, "profile: OK\n", ""))


if __name__ == "__main__":
    unittest.main()
