import os
import subprocess
import sys
import tempfile
import ntpath
import re
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "build_final.py")
sys.path.insert(0, os.path.dirname(HERE))
import build_final  # noqa: E402

F = "ㅤ"
TITLE = "가나동 선물 포장 순서와 준비물"
PROFILE = ("# 업체 기본정보\n\n| 항목 | 내용 |\n|---|---|\n| 업체명 | 예시상회 |\n"
           "| 장소 검색어 | 예시상회 가나동 |\n")
HEAD = "| 슬롯 | 위치(소제목) | 목적 | 유형 | 프롬프트(ai) / 후보 파일(photo) | 캡션(alt) | 파일 | 검수 |\n|---|---|---|---|---|---|---|---|\n"


def cover_row(title=TITLE):
    return (f"| 00 | 표지(대표) | 표지 | cover | bg prompt | 제목: {title}; 줄바꿈: 가나동 선물; 포장 순서 "
            "| images/00-cover.png | PASS |\n")


def row(slot, file, kind="ai"):
    return f"| {slot} | 위치 | 목적 | {kind} | prompt | 캡션 {slot} | {file} | PASS |\n"


DRAFT = f"""---
title: {TITLE}
keyword: 선물 포장
category: 예시상회
tags: [선물 포장, 가나동 선물, 포장준비물]
variation: {{type: 정보, structure: 절차형, intro: 상황, region: [가나동], title_region: 가나동}}
---
<!-- 제목 B안: 다른 제목 -->
# {TITLE}
![슬롯: 표지 아래 장면]()
도입 문단입니다(출처: https://www.law.go.kr/법령/소비자기본법).

## 📑 목차
1. 첫째
2. 둘째

---

## 1️⃣ 문단 뒤 소제목
본문 문단입니다 (출처: https://example.com/a). 둘째 문장입니다.


## 2️⃣ 이미지 뒤 소제목
![슬롯: 이미지 장면]()

## 3️⃣ 목록 뒤 소제목
- 항목 하나
- 항목 둘
## 4️⃣ 제거 슬롯
![슬롯: 제거될 장면]()
문단입니다.
![슬롯: 보류 장면]()
![슬롯: 실사진]()

## 📞 문의 안내: 000-0000-0000
"""


class BuildFinalTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._tmp.name)
        os.makedirs(os.path.join(self.root, "knowledge"))
        os.makedirs(os.path.join(self.root, "photos"))
        self.post = os.path.join(self.root, "work", "posts", "001-test")
        os.makedirs(os.path.join(self.post, "images"))
        self.write("knowledge/business-profile.md", PROFILE)
        for p in ("photos/business-intro.png", "photos/yard.jpg"):
            open(os.path.join(self.root, p), "wb").close()
        for name in ("00-cover.png", "01-cover.png", "02-scene.png", "03-x.png"):
            open(os.path.join(self.post, "images", name), "wb").close()
        self.plan = ("# 이미지 계획\n" + HEAD + cover_row() + row("01", "images/01-cover.png")
                     + row("02", "images/02-scene.png") + row("03", "제거") + row("04", "보류")
                     + row("05", "photos/yard.jpg", "photo"))
        self.draft = DRAFT

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        with open(os.path.join(self.root, rel), "w", encoding="utf-8") as f:
            f.write(text)

    def run_build(self, extra=()):
        with open(os.path.join(self.post, "draft-v2.md"), "w", encoding="utf-8") as f:
            f.write(self.draft)
        with open(os.path.join(self.post, "images", "image-plan.md"), "w", encoding="utf-8") as f:
            f.write(self.plan)
        p = subprocess.run([sys.executable, SCRIPT, self.post, *extra], cwd=self.root,
                           capture_output=True, text=True)
        out = os.path.join(self.post, "final.md")
        text = None
        if os.path.exists(out):
            with open(out, encoding="utf-8") as f:
                text = f.read()
        return p, text

    def lines_before(self, text, heading, k):
        ls = text.splitlines()
        i = ls.index(heading)
        return ls[i - k:i]

    # --- 정상 변환 ---
    def test_md_path_uses_forward_slashes(self):
        # Windows 에서 본문 이미지 경로는 C:/... (lint image_paths·naver_upload 는 os.path.isabs 로 판정 — ntpath 에선 절대경로)
        with mock.patch.object(build_final.os, "sep", "\\"):
            self.assertEqual(build_final.md_path("C:\\Users\\me\\img.png"), "C:/Users/me/img.png")
        self.assertEqual(build_final.md_path("/Users/me/img.png"), "/Users/me/img.png")   # macOS 그대로
        self.assertTrue(ntpath.isabs("C:/Users/me/img.png"))

    def test_text_writes_force_lf(self):
        # Windows 에서 텍스트 파일이 CRLF 로 써지지 않게, 쓰기 모드 open/fdopen 은 모두 newline="\n"
        scripts = os.path.dirname(HERE)
        for name in sorted(os.listdir(scripts)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(scripts, name), encoding="utf-8") as f:
                for ln, line in enumerate(f, 1):
                    if re.search(r"\b(open|fdopen)\(.*[\"']w[\"']", line):
                        self.assertIn('newline="\\n"', line, f"{name}:{ln}")

    def test_normal_build(self):
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("슬롯 5개(제거 1개, 보류 1개)", p.stdout)
        self.assertIn("출처 제거 2개", p.stdout)
        img = os.path.join(self.post, "images")
        self.assertIn(f"![]({img}/01-cover.png)", text)
        self.assertIn(f"![]({img}/02-scene.png)", text)
        self.assertIn(f"![]({self.root}/photos/yard.jpg)", text)
        self.assertNotIn("슬롯:", text)
        self.assertNotIn("출처", text)
        self.assertNotIn("03-x.png", text)
        self.assertIn("도입 문단입니다.", text)
        self.assertIn("본문 문단입니다. 둘째 문장입니다.", text)
        # 캡션 비움: 모든 이미지 alt가 빈칸
        for ln in text.splitlines():
            if ln.startswith("!["):
                self.assertTrue(ln.startswith("![]("), ln)
        # ① 머리 보존
        self.assertTrue(text.startswith("---\ntitle: " + TITLE + "\n"))
        self.assertIn("<!-- 제목 B안: 다른 제목 -->\n# " + TITLE + "\n", text)
        # ⑥ 마무리 블록 순서·해시태그
        tail = text.splitlines()[-5:]
        self.assertEqual(tail, [
            "## 📞 문의 안내: 000-0000-0000",
            f"![]({self.root}/photos/business-intro.png)",
            ":::place 예시상회 가나동:::",
            "",
            "**#선물포장 #가나동선물 #포장준비물**",
        ])
        self.assertTrue(text.endswith("**\n") and not text.endswith("\n\n"))
        self.assertNotIn("\n\n\n", text)

    def test_place_required_without_profile_row(self):
        # 장소 검색어 행이 없으면 기본값 없이 변환 불가(조용한 기본값 금지)
        self.write("knowledge/business-profile.md", "# 업체 기본정보\n\n| 항목 | 내용 |\n|---|---|\n| 장소 검색어 | [장소 검색어] |\n")
        self.assertFails("`장소 검색어` 행이 비어 있습니다")

    # --- ④ 여백 ---
    def test_spacing_after_paragraph(self):
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.lines_before(text, "## 2️⃣ 이미지 뒤 소제목", 4),
                         ["본문 문단입니다. 둘째 문장입니다.", F, F, ""])

    def test_spacing_after_image(self):
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        img = os.path.join(self.post, "images", "02-scene.png")
        self.assertEqual(self.lines_before(text, "## 3️⃣ 목록 뒤 소제목", 4), [f"![]({img})", F, F, ""])

    def test_spacing_after_list(self):
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.lines_before(text, "## 4️⃣ 제거 슬롯", 4), ["- 항목 둘", F, F, ""])
        # 제목·문단 뒤는 '그 밖' 규칙
        self.assertEqual(self.lines_before(text, "## 📑 목차", 4), ["도입 문단입니다.", F, F, ""])
        # 실사진 뒤 마무리 소제목 → ㅤ 2줄
        self.assertEqual(self.lines_before(text, "## 📞 문의 안내: 000-0000-0000", 4),
                         [f"![]({self.root}/photos/yard.jpg)", F, F, ""])

    def test_filler_lines_constant(self):
        self.run_build()  # 초안·계획 파일 쓰기
        old = build_final.H2_FILLER_LINES
        build_final.H2_FILLER_LINES = 1
        try:
            text, summary, errs = build_final.build(self.post, os.path.join(self.root, "photos"),
                                                    os.path.join(self.root, "knowledge"))
        finally:
            build_final.H2_FILLER_LINES = old
        self.assertEqual(errs, [])
        self.assertEqual(self.lines_before(text, "## 2️⃣ 이미지 뒤 소제목", 3),
                         ["본문 문단입니다. 둘째 문장입니다.", F, ""])
        self.assertIn("필러 삽입 6줄", summary)

    def test_spacing_after_divider(self):
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.lines_before(text, "## 1️⃣ 문단 뒤 소제목", 4), ["---", F, F, ""])

    def test_fenced_h2_untouched(self):
        self.draft = DRAFT.replace("본문 문단입니다 (출처", "```\n문단\n\n## 펜스 안 소제목\n```\n본문 문단입니다 (출처")
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        ls = text.splitlines()
        i = ls.index("## 펜스 안 소제목")
        self.assertEqual(ls[i - 2:i + 2], ["문단", "", "## 펜스 안 소제목", "```"])

    def test_body_comments_removed(self):
        self.draft = DRAFT.replace("## 📑 목차\n", "## 📑 목차\n<!-- 메모: 지울 것 -->\n").replace(
            "둘째 문장입니다.", "둘째 문장입니다.<!-- 인라인 -->\n<!-- 여러\n줄 주석 -->\n셋째 줄입니다.")
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("<!-- 제목 B안: 다른 제목 -->\n# " + TITLE, text)
        self.assertEqual(text.count("<!--"), 1)
        self.assertNotIn("줄 주석", text)
        self.assertIn("## 📑 목차\n1. 첫째", text)
        self.assertIn("본문 문단입니다. 둘째 문장입니다.\n셋째 줄입니다.\n", text)

    def test_hashtag_normalized(self):
        self.draft = DRAFT.replace("tags: [선물 포장, 가나동 선물, 포장준비물]",
                                   "tags: [#선물 포장, '#가나동', 포장 준비물]")
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(text.endswith("**#선물포장 #가나동 #포장준비물**\n"), text[-80:])
        self.assertNotIn("##가나동", text)

    def test_idempotent(self):
        p1, t1 = self.run_build()
        p2, t2 = self.run_build()
        self.assertEqual((p1.returncode, p2.returncode), (0, 0))
        self.assertEqual(t1, t2)
        # 초안에 이미 ㅤ 줄이 있어도 중복 삽입하지 않음
        # 이미 ㅤ+빈 줄(새 형태)·ㅤ 2줄(옛 형태)·빈 줄+ㅤ(옛 형태)이 있어도 같은 배치로 정규화
        self.draft = (DRAFT.replace("\n\n## 3️⃣", f"\n{F}\n{F}\n## 3️⃣")
                      .replace("\n\n\n## 2️⃣", f"\n\n{F}\n## 2️⃣")
                      .replace("- 항목 둘\n## 4️⃣", f"- 항목 둘\n{F}\n\n## 4️⃣"))
        p3, t3 = self.run_build()
        self.assertEqual(p3.returncode, 0, p3.stderr)
        self.assertEqual(t3, t1)

    # --- 오류(exit 1) ---
    def assertFails(self, needle):
        p, text = self.run_build()
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn(needle, p.stderr)
        self.assertIsNone(text)
        self.assertFalse(os.path.exists(os.path.join(self.post, "final.md")))

    def test_mixed_source_fails(self):
        self.draft = DRAFT.replace("본문 문단입니다 (출처: https://example.com/a).",
                                   "본문 문단입니다(제10조, 시행 2025-01-01, 출처: https://example.com/a).")
        ln = self.draft.splitlines().index(
            "본문 문단입니다(제10조, 시행 2025-01-01, 출처: https://example.com/a). 둘째 문장입니다.") + 1
        self.assertFails("혼합 출처 괄호 — lint source_format 참고")
        p, _ = self.run_build()
        self.assertIn(f"{ln}행", p.stderr)

    def test_link_source_fails(self):
        self.draft = DRAFT.replace("둘째 문장입니다.", "둘째 문장입니다 [출처](https://example.com/b).")
        self.assertFails("링크형 출처 [출처](URL) — lint source_format 참고")

    def test_failure_removes_stale_final(self):
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.post, "final.md")))
        self.plan = self.plan.replace(cover_row(), "")
        p, text = self.run_build()
        self.assertEqual(p.returncode, 1)
        self.assertIn("이전 final.md 삭제", p.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.post, "final.md")))

    def test_cover_title_mismatch_fails(self):
        self.plan = self.plan.replace(cover_row(), cover_row("다라동 선물 포장 순서"))
        self.assertFails("표지 재생성 필요")

    def test_cover_title_whitespace_ignored(self):
        self.plan = self.plan.replace(cover_row(), cover_row(TITLE.replace(" ", "")))
        p, _ = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_no_cover_row_fails(self):
        self.plan = self.plan.replace(cover_row(), "")
        self.assertFails("표지(00) 행 없음")

    def test_slot_count_mismatch_fails(self):
        self.plan += row("06", "images/03-x.png")
        self.assertFails("슬롯 수 불일치")

    def test_unconfirmed_and_missing_file_fail(self):
        self.plan = self.plan.replace("images/02-scene.png", "").replace("photos/yard.jpg", "photos/none.jpg")
        p, _ = self.run_build()
        self.assertEqual(p.returncode, 1)
        self.assertIn("02: 파일 칸 미확정(빈칸)", p.stderr)
        self.assertIn("05: 파일 없음", p.stderr)

    def test_removed_and_held_lines_deleted(self):
        p, text = self.run_build()
        self.assertEqual(p.returncode, 0, p.stderr)
        ls = text.splitlines()
        i = ls.index("## 4️⃣ 제거 슬롯")
        self.assertEqual(ls[i + 1:i + 2], ["문단입니다."])
        self.assertEqual(ls[i + 2], f"![]({self.root}/photos/yard.jpg)")
        self.assertEqual(sum(1 for x in ls if x.startswith("![")), 4)  # 01·02·05 + 업체소개

    def test_last_h2_not_contact_fails(self):
        self.draft = DRAFT + "\n## 5️⃣ 덧붙임\n문단입니다.\n"
        self.assertFails("마지막 소제목이 '## 📞 문의'로 시작하지 않음")

    def test_missing_intro_image_fails(self):
        os.remove(os.path.join(self.root, "photos", "business-intro.png"))
        self.assertFails("업체소개 이미지 없음")

    def test_photos_option_sets_base(self):
        alt = os.path.join(self.root, "alt", "photos")
        os.makedirs(alt)
        for n in ("business-intro.png", "yard.jpg"):
            open(os.path.join(alt, n), "wb").close()
        p, text = self.run_build(["--photos", alt])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(f"![]({alt}/yard.jpg)", text)
        self.assertIn(f"![]({alt}/business-intro.png)", text)

    def test_usage_error(self):
        p = subprocess.run([sys.executable, SCRIPT, os.path.join(self.root, "nope")],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_cover_title_helper(self):
        self.assertEqual(build_final.cover_title("제목: 가 나; 줄바꿈: 가; 나"), "가 나")
        self.assertIsNone(build_final.cover_title("캡션만"))


if __name__ == "__main__":
    unittest.main()
