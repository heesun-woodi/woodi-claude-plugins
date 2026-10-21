import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "check_profile.py")
TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(HERE)), "knowledge", "business-profile.md")
FIXTURES = os.path.join(HERE, "fixtures")
# 가상 업체 — 1.0.0 필수 행을 모두 채운 profile(v1.1 신규 행 없음)
OLD = ("# 업체 기본정보\n\n| 항목 | 내용 |\n|---|---|\n| 업체명 | 예시상회 |\n| 연락처 | 000-0000-0000 |\n"
          "| 상품·서비스 | 선물 포장, 단체 주문 |\n| 고객 지역 | 가나동, 다라동 |\n| 장소 검색어 | 예시상회 가나동 |\n"
          "| 업체 유형어 | 상회 |\n| 업종 일반어 | 선물 |\n\n## 금칙어\n\n- `금지어예시`\n")
# v1.1 필수 행을 더한 profile
NEW_ROWS = "| 블로그 유형 | 업체 |\n| 톤 | 합니다체 |\n| 마무리 블록 | 문의헤딩, 소개이미지, 장소카드, 해시태그 |\n| 이미지 소스 | ai, photo |\n"
FILLED = OLD.replace("| 업체명 |", NEW_ROWS + "| 업체명 |")


def set_row(profile, name, value):
    """`| name | … |` 행의 값을 바꾼다."""
    import re
    out, n = re.subn(r"^\| " + re.escape(name) + r" \|.*$", f"| {name} | {value} |", profile, flags=re.M)
    assert n == 1, name
    return out


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
        # 스캐폴드 템플릿은 비어 있다 — 업체명·상품·서비스·금칙어는 항상 MISSING(고객 지역·업체 유형어·업종 일반어는 더 이상 필수 아님)
        with open(TEMPLATE, encoding="utf-8") as f:
            template = f.read()
        code, out, err = self.run_check(template)
        self.assertEqual((code, err), (2, ""))
        self.assertRegex(out, r"^profile: MISSING (블로그 유형,)?업체명,상품·서비스,(톤,마무리 블록,이미지 소스,)?.*금칙어\n$")
        for gone in ("고객 지역", "업체 유형어", "업종 일반어"):
            self.assertNotIn(gone, out)

    def test_1_0_0_profile_reports_new_rows(self):
        self.assertEqual(self.run_check(OLD), (2, "profile: MISSING 블로그 유형,톤,마무리 블록,이미지 소스\n", ""))

    def test_old_optional_rows_may_be_empty(self):
        p = FILLED
        for name in ("고객 지역", "업체 유형어", "업종 일반어"):
            p = set_row(p, name, "")
        self.assertEqual(self.run_check(p), (0, "profile: OK\n", ""))

    def test_missing_order_and_conditional_rows(self):
        p = FILLED
        for name in ("블로그 유형", "업체명", "상품·서비스", "톤", "이미지 소스"):
            p = set_row(p, name, "")
        p = set_row(p, "마무리 블록", "문의헤딩, 장소카드, 해시태그")
        p = set_row(p, "연락처", "")
        p = set_row(p, "장소 검색어", "")
        p = p.replace("- `금지어예시`", "")
        self.assertEqual(self.run_check(p), (2, "profile: MISSING 블로그 유형,업체명,상품·서비스,톤,이미지 소스,연락처,장소 검색어,금칙어\n", ""))

    def test_contact_required_only_with_inquiry_heading(self):
        p = set_row(FILLED, "연락처", "")
        self.assertEqual(self.run_check(p), (2, "profile: MISSING 연락처\n", ""))  # 문의헤딩 있음
        p2 = set_row(p, "마무리 블록", "소개이미지, 장소카드, 해시태그")
        self.assertEqual(self.run_check(p2), (0, "profile: OK\n", ""))
        p3 = set_row(set_row(FILLED, "장소 검색어", ""), "마무리 블록", "문의헤딩, 해시태그")
        self.assertEqual(self.run_check(p3), (0, "profile: OK\n", ""))  # 장소카드 없으면 장소 검색어 불필요
        p4 = set_row(set_row(FILLED, "장소 검색어", ""), "마무리 블록", "문의헤딩, 장소카드, 해시태그")
        self.assertEqual(self.run_check(p4), (2, "profile: MISSING 장소 검색어\n", ""))

    def test_invalid_values(self):
        cases = [("블로그 유형", "기업", "블로그 유형=기업"), ("톤", "반말", "톤=반말"),
                 ("마무리 블록", "문의헤딩, 푸터, 해시태그", "마무리 블록=푸터"),
                 ("마무리 블록", "문의헤딩, 장소카드", "마무리 블록=해시태그 없음"),
                 ("이미지 소스", "ai, video", "이미지 소스=video")]
        for name, val, shown in cases:
            with self.subTest(name=name, val=val):
                self.assertEqual(self.run_check(set_row(FILLED, name, val)), (2, f"profile: INVALID {shown}\n", ""))

    def test_invalid_reports_first_only_and_yields_to_missing(self):
        p = set_row(set_row(FILLED, "톤", "반말"), "이미지 소스", "video")
        self.assertEqual(self.run_check(p), (2, "profile: INVALID 톤=반말\n", ""))
        # 마무리 블록이 올바르지 않으면 조건 행(연락처)은 보지 않는다 → INVALID가 먼저
        p = set_row(set_row(FILLED, "마무리 블록", "문의헤딩, 푸터, 해시태그"), "연락처", "")
        self.assertEqual(self.run_check(p), (2, "profile: INVALID 마무리 블록=푸터\n", ""))
        # MISSING이 있으면 INVALID는 검사하지 않는다
        p = set_row(set_row(FILLED, "톤", "반말"), "업체명", "")
        self.assertEqual(self.run_check(p), (2, "profile: MISSING 업체명\n", ""))

    def test_fixtures_are_ok(self):
        for name in ("profile-business.md", "profile-personal.md"):
            with self.subTest(name=name):
                with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
                    self.assertEqual(self.run_check(f.read()), (0, "profile: OK\n", ""))

    def test_nofile(self):
        self.assertEqual(self.run_check(), (2, "profile: NOFILE\n", ""))

    def test_forbidden_none_is_ok(self):
        self.assertEqual(self.run_check(FILLED.replace("- `금지어예시`", "- 없음")), (0, "profile: OK\n", ""))


if __name__ == "__main__":
    unittest.main()
