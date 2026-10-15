import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "feedback_log.py")
sys.path.insert(0, os.path.dirname(HERE))
import feedback_log  # noqa: E402


class FeedbackLogTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.log = os.path.join(self.root, "work", "feedback-log.md")

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *args, cwd=None):
        env = dict(os.environ, PYTHONUTF8="1")
        p = subprocess.run([sys.executable, SCRIPT, *args], cwd=cwd or self.root, env=env,
                           capture_output=True, text=True, encoding="utf-8")
        return p.returncode, p.stdout, p.stderr

    def add(self, text="제목을 질문형으로", post="002-선물-포장", stage="게이트2", cat="제목", scope="앞으로 계속"):
        return self.run_cli("add", "--post", post, "--stage", stage, "--category", cat, "--scope", scope, "--text", text)

    def pending(self):
        rc, out, err = self.run_cli("pending")
        self.assertEqual(rc, 0, err)
        return json.loads(out)

    def test_add_creates_file_with_header_and_increments_id(self):
        self.assertFalse(os.path.exists(self.log))
        rc, out, err = self.add()
        self.assertEqual((rc, out.strip()), (0, "F-0001"), err)
        rc, out, _ = self.add(text="두 번째", stage="직접", cat="톤", scope="이번 글만")
        self.assertEqual(out.strip(), "F-0002")
        with open(self.log, encoding="utf-8", newline="") as f:
            text = f.read()
        self.assertNotIn("\r", text)
        self.assertIn("| id | 일시 | 글 | 단계 | 범주 | 적용 범위 | 요청 원문 | 처리 |", text)
        rows = [ln for ln in text.split("\n") if ln.startswith("| F-")]
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0].endswith("| 대기 |"))
        self.assertRegex(rows[0], r"^\| F-0001 \| \d{4}-\d\d-\d\d \d\d:\d\d \| 002-선물-포장 \| 게이트2 \| 제목 \| 앞으로 계속 \|")

    def test_pending_empty_is_empty_array(self):
        self.assertEqual(self.pending(), [])
        self.assertTrue(os.path.isfile(self.log))

    def test_pipe_and_newline_round_trip(self):
        raw = "A|B 형식으로\n줄을 바꿔서\\끝"
        self.add(text=raw)
        with open(self.log, encoding="utf-8") as f:
            row = next(ln for ln in f.read().split("\n") if ln.startswith("| F-0001"))
        self.assertIn("A\\|B", row)
        self.assertIn("<br>", row)
        self.assertEqual(len(feedback_log.split_row(row)), 8)
        items = self.pending()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["요청 원문"], raw)
        self.assertEqual(items[0]["id"], "F-0001")
        self.assertEqual(set(items[0]), set(feedback_log.COLS))

    def test_mark_and_pending(self):
        self.add()
        self.add(text="이번만", scope="이번 글만")
        self.add(text="세 번째")
        self.assertEqual(self.run_cli("mark", "F-0001", "L-005")[0], 0)
        self.assertEqual(self.run_cli("mark", "F-0002", "반영 안 함: 이번 글 한정")[0], 0)
        ids = [x["id"] for x in self.pending()]
        self.assertEqual(ids, ["F-0003"])
        rc, out, _ = self.run_cli("list", "--json")
        marks = {x["id"]: x["처리"] for x in json.loads(out)}
        self.assertEqual(marks, {"F-0001": "L-005", "F-0002": "반영 안 함: 이번 글 한정", "F-0003": "대기"})

    def test_mark_errors(self):
        self.add()
        self.assertEqual(self.run_cli("mark", "F-0009", "L-001")[0], 1)
        self.assertEqual(self.run_cli("mark", "F-0001", "적용")[0], 2)
        self.assertEqual(self.run_cli("mark", "F-0001", "반영 안 함:")[0], 2)
        self.assertEqual(self.run_cli("mark", "X-1", "L-001")[0], 2)

    def test_invalid_values_exit_2(self):
        for kw in ({"stage": "게이트4"}, {"cat": "말투"}, {"scope": "가끔"}, {"text": ""}):
            rc, out, err = self.add(**kw)
            self.assertEqual(rc, 2, (kw, out, err))
            self.assertIn("오류", err)
        self.assertFalse(os.path.exists(self.log) and "| F-" in open(self.log, encoding="utf-8").read())

    def test_stage_space_variant_normalized(self):
        self.add(stage="게이트 2", scope="앞으로계속")
        item = self.pending()[0]
        self.assertEqual((item["단계"], item["적용 범위"]), ("게이트2", "앞으로 계속"))

    def test_list_filter_by_post(self):
        self.add(post="002-선물-포장")
        self.add(post="003-리본-묶기")
        rc, out, _ = self.run_cli("list", "--post", "003")
        self.assertEqual(rc, 0)
        self.assertIn("003-리본-묶기", out)
        self.assertNotIn("002-선물-포장", out)
        self.assertIn("(1건)", out)

    def test_custom_file_and_crlf_file(self):
        path = os.path.join(self.root, "log.md")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(feedback_log.HEADER.replace("\n", "\r\n")
                    + "| F-0007 | 2025-01-01 10:00 | 001-a | 직접 | 톤 | 이번 글만 | 원문 | 대기 |\r\n\r\n메모 줄\r\n")
        rc, out, _ = self.run_cli("--file", path, "add", "--post", "001-a", "--stage", "발행후",
                                  "--category", "SEO", "--scope", "이번 글만", "--text", "태그")
        self.assertEqual(out.strip(), "F-0008")
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        self.assertNotIn("\r", text)
        lines = text.split("\n")
        i = lines.index(next(ln for ln in lines if ln.startswith("| F-0008")))
        self.assertTrue(lines[i - 1].startswith("| F-0007"))  # 표 끝(메모 줄 앞)에 붙음
        self.assertIn("메모 줄", text)


    def write_log(self, body, header=None):
        os.makedirs(os.path.dirname(self.log), exist_ok=True)
        with open(self.log, "w", encoding="utf-8") as f:
            f.write((feedback_log.HEADER if header is None else header) + body)

    def test_unescaped_pipe_in_hand_edited_row(self):
        self.write_log("| F-0001 | 2025-01-01 10:00 | 001-a | 직접 | 톤 | 이번 글만 | A | B | C | 대기 |\n")
        items = self.pending()
        self.assertEqual((items[0]["요청 원문"], items[0]["처리"]), ("A|B|C", "대기"))
        self.assertEqual(self.run_cli("mark", "F-0001", "L-001")[0], 0)
        rc, out, _ = self.run_cli("list", "--json")
        item = json.loads(out)[0]
        self.assertEqual((item["요청 원문"], item["처리"]), ("A|B|C", "L-001"))
        with open(self.log, encoding="utf-8") as f:
            row = next(ln for ln in f.read().split("\n") if ln.startswith("| F-0001"))
        self.assertEqual(len(feedback_log.split_row(row)), 8)  # mark가 이스케이프해 8칸으로 다시 씀

    def test_id_not_reused_after_row_deleted(self):
        self.add()
        self.add()
        with open(self.log, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("<!-- next-id: 3 -->", text)
        self.write_log("", header="\n".join(ln for ln in text.split("\n") if not ln.startswith("| F-0002")) + "\n")
        self.assertEqual(self.add()[1].strip(), "F-0003")

    def test_old_file_without_next_id_comment(self):
        old = "# 피드백 기록\n\n| " + " | ".join(feedback_log.COLS) + " |\n|" + "---|" * 8 + "\n"
        self.write_log("| F-0004 | 2025-01-01 10:00 | 001-a | 직접 | 톤 | 이번 글만 | 원문 | 대기 |\n", header=old)
        self.assertEqual(self.add()[1].strip(), "F-0005")
        with open(self.log, encoding="utf-8") as f:
            lines = f.read().split("\n")
        self.assertEqual(lines[1], "<!-- next-id: 6 -->")
        self.assertEqual(self.add()[1].strip(), "F-0006")

    def test_duplicate_id_warns_and_mark_exit_2(self):
        row = "| F-0001 | 2025-01-01 10:00 | 001-a | 직접 | 톤 | 이번 글만 | 원문 | 대기 |\n"
        self.write_log(row + row)
        rc, out, err = self.run_cli("pending")
        self.assertEqual(rc, 0)
        self.assertEqual(len(json.loads(out)), 2)
        self.assertIn("F-0001 행이 2개", err)
        self.assertRegex(err, r"줄 \d+, \d+")
        rc, out, err = self.run_cli("mark", "F-0001", "L-001")
        self.assertEqual(rc, 2)
        self.assertIn("여러 개", err)
        rc, out, err = self.add()
        self.assertEqual((rc, out.strip()), (0, "F-0002"))
        self.assertIn("경고", err)

    def test_literal_br_and_angle_round_trip(self):
        raw = "<br> 태그나 <b>굵게</b>를 쓰지 말기\n둘째 줄"
        self.add(text=raw)
        self.assertEqual(self.pending()[0]["요청 원문"], raw)
        # 예전 형식(< 이스케이프 없음)으로 저장된 행의 <br>는 줄바꿈으로 읽힌다
        self.write_log("| F-0001 | 2025-01-01 10:00 | 001-a | 직접 | 톤 | 이번 글만 | 첫 줄<br>둘째 줄 | 대기 |\n")
        self.assertEqual(self.pending()[0]["요청 원문"], "첫 줄\n둘째 줄")

    def test_atomic_save_leaves_no_temp_files(self):
        self.add()
        self.run_cli("mark", "F-0001", "L-001")
        self.assertEqual(sorted(os.listdir(os.path.dirname(self.log))), ["feedback-log.md"])


if __name__ == "__main__":
    unittest.main()
