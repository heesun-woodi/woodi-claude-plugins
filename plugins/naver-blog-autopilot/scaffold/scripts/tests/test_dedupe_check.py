import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import dedupe_check  # noqa: E402

# 가상 업체 profile — 고객 지역·업체 유형어·업종 일반어(필수)·제목 정규화·공지 표지어(선택)를 load_profile로 읽는다
PROFILE = ("| 항목 | 내용 |\n|---|---|\n| 고객 지역 | 가나동, 다라동 (고객 많은 순) |\n"
           "| 업체 유형어 | 상회 |\n| 업종 일반어 | 선물 |\n| 제목 정규화 | 선물 상자 → 선물상자 |\n"
           "| 공지 표지어 | 모집, 공지 |\n")  # 홍보 표지어는 기본값
POSTS = [
    {"title": "주문 전에 확인하는 선물상자 배송일정과 포장 옵션", "date": "2025-03-14"},
    {"title": "포장 체험단 모집 공고 — 다라동 예시상회", "date": "2024-11-20"},
    {"title": "가나동·다라동 상회 적립카드 혜택 받는 방법", "date": "2023-06-02"},
    {"title": "리본 고르기 포장 요령 정리", "date": "2022-12-05"},
]


SCRIPT = os.path.join(os.path.dirname(HERE), "dedupe_check.py")
EMPTY_PROFILE = ("| 항목 | 내용 |\n|---|---|\n| 고객 지역 | |\n| 업체 유형어 | [쉼표 목록] |\n| 업종 일반어 | |\n")


class DedupeTest(unittest.TestCase):
    def setUp(self):  # 모듈 전역(REGIONS 등)을 매 테스트 PROFILE로 되돌린다
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "business-profile.md"), "w", encoding="utf-8") as f:
                f.write(PROFILE)
            dedupe_check.load_profile(d)

    def test_jaccard_duplicate(self):
        j, core, lab, title, _ = dedupe_check.judge("리본 고르기와 포장 요령", "리본", POSTS)
        self.assertEqual(lab, "○")
        self.assertGreaterEqual(j, 0.5)
        self.assertIn("리본", title)

    def test_core_token_duplicate(self):
        j, core, lab, title, _ = dedupe_check.judge("올해 달라진 택배 마감 시간", "선물 상자 배송일정", POSTS)
        self.assertLess(j, 0.5)
        self.assertGreaterEqual(core, 2)
        self.assertEqual(lab, "○")
        self.assertIn("배송일정", title)

    def test_partial_band(self):
        j, core, lab, title, _ = dedupe_check.judge("적립카드로 포장비 아끼는 방법", "적립카드", POSTS)
        self.assertEqual(lab, "△")
        self.assertTrue(0.25 <= j < 0.5)
        self.assertIn("적립카드", title)

    def test_no_overlap(self):
        self.assertEqual(dedupe_check.judge("재활용 가능한 포장지 구분법", "포장지 재활용", POSTS)[2], "×")

    def test_notice_marker_matches_same_marker_post(self):
        j, core, lab, title, date = dedupe_check.judge("예시상회 10월 체험단 모집", "체험단 일정", POSTS, notice=True)
        self.assertEqual(lab, "○")
        self.assertIn("모집", title)
        self.assertEqual(date, "2024-11-20")

    def test_notice_off_does_not_force_duplicate(self):
        self.assertNotEqual(dedupe_check.judge("예시상회 10월 체험단 모집", "체험단 일정", POSTS)[3], "")

    def test_empty_posts_is_no_overlap(self):
        # 새 블로그(우리 글 목록 []) — 죽지 않고 ×(우리 글 없음)
        for notice in (False, True):
            self.assertEqual(dedupe_check.judge("예시상회 10월 체험단 모집", "체험단 일정", [], notice=notice),
                             (0.0, 0, "×", "", ""))

    def test_empty_region_kind_generic_rows_give_empty_lists(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "business-profile.md"), "w", encoding="utf-8") as f:
                f.write(EMPTY_PROFILE)
            dedupe_check.load_profile(d)  # ValueError 아님
        self.assertEqual((dedupe_check.REGIONS, dedupe_check.STRIP, dedupe_check.GENERIC), ([], [], set()))
        j, core, lab, title, _ = dedupe_check.judge("리본 고르기와 포장 요령", "리본", POSTS)
        self.assertEqual(lab, "○")

    def test_load_profile_still_stops_without_profile_file(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                dedupe_check.load_profile(d)
            with self.assertRaises(ValueError):
                dedupe_check.load_profile(None)

    def test_cli_empty_rows_exit_0_and_no_profile_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            kd = os.path.join(d, "knowledge")
            os.makedirs(os.path.join(d, "work"))
            posts = os.path.join(d, "work", "own-posts.json")
            with open(posts, "w", encoding="utf-8") as f:
                json.dump(POSTS, f, ensure_ascii=False)
            run = lambda: subprocess.run([sys.executable, SCRIPT, "리본 고르기와 포장 요령", "리본", posts],
                                         capture_output=True, text=True, encoding="utf-8")
            r = run()  # knowledge/ 없음
            self.assertEqual(r.returncode, 2, r.stderr)
            os.makedirs(kd)
            with open(os.path.join(kd, "business-profile.md"), "w", encoding="utf-8") as f:
                f.write(EMPTY_PROFILE)
            r = run()
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(r.stdout.startswith("○"))


if __name__ == "__main__":
    unittest.main()
