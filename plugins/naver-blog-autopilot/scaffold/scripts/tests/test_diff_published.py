import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "diff_published.py")
sys.path.insert(0, os.path.dirname(HERE))
import diff_published  # noqa: E402

F = "ㅤ"
TITLE = "가나동 선물포장 리본 묶기 순서, 처음이라면 이렇게 준비하세요"
P1 = "선물 포장은 상자 고르기와 리본 묶기 두 가지로 나뉩니다. 처음이라면 순서를 먼저 익히는 것이 좋습니다."
P2 = "포장 시간은 4분입니다. 시간 안에 끝내지 못하면 다시 묶습니다."
P3 = "연습은 하루 2시간씩 꾸준히 하는 것이 좋습니다. 무리하면 오히려 실수가 늘어납니다."
P4 = "주문은 예시상회 홈페이지에서 합니다. 원하는 날짜를 고르면 됩니다."

FINAL = f"""---
title: {TITLE}
keyword: 선물포장
category: 예시상회
tags: [선물포장, 가나동선물포장]
variation: {{type: 정보, structure: 절차형, intro: 상황, region: [가나동, 다라동], title_region: 가나동}}
---
<!-- 제목 B안: 다른 제목 -->
# {TITLE}

{P1}

![](/abs/images/01.png)

{F}
{F}

## 1️⃣ 포장 순서

**{P2}**

- 상자 고르기
- 리본 묶기

{F}
{F}

## 2️⃣ 연습 방법

{P3}

| 항목 | 시간 |
|---|---|
| 포장 | 2분 |

{F}
{F}

## 3️⃣ 주문 방법

{P4} [관련글](https://blog.naver.com/example_blog/1)

{F}
{F}

## 📞 문의 안내: 000-0000-0000

![](/abs/photos/business-intro.png)

:::place 예시상회:::

**#선물포장 #가나동선물포장**
"""

# 발행본: 제목 변경, 소제목 1개 이름 변경·1개 삭제·1개 추가, P2 수정(해요체), P3 삭제, 새 문단 추가(해요체), 마무리 유지
PUB_MD = f"""![](https://postfiles.pstatic.net/cover.png)

{P1}

![](https://postfiles.pstatic.net/01.png)

## 1️⃣ 포장 순서

**포장 시간은 4분이에요. 시간 안에 끝내지 못하면 다시 묶어요.**

- 상자 고르기
- 리본 묶기

## 2️⃣ 주문하는 방법

{P4} [선물 포장 준비물](https://blog.naver.com/example_blog/1)

## 3️⃣ 자주 묻는 질문

처음 오시는 분도 걱정하지 않으셔도 돼요.

| 항목 | 시간 |
| --- | --- |
| 포장 | 2분 |

## 📞 문의 안내: 000-0000-0000

![](https://postfiles.pstatic.net/intro.png)

**#선물포장 #가나동선물포장**
"""
PUB_TITLE = "가나동 선물포장 리본 묶기 순서 총정리"


class DiffPublishedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = cls._tmp.name
        cls.post = os.path.join(cls.root, "work", "posts", "002-선물-포장")
        os.makedirs(os.path.join(cls.post, "images"))
        open(os.path.join(cls.post, "images", "00-cover.png"), "wb").close()
        cls.final = cls.write("final.md", FINAL)
        cls.pub_json = cls.write("published.json", json.dumps(
            {"stats": {"blogId": "example_blog", "logNo": "1", "title": PUB_TITLE, "images": 3}, "markdown": PUB_MD},
            ensure_ascii=False, indent=2))
        cls.pub_md = cls.write("published.md", "```json\n" + json.dumps({"title": PUB_TITLE, "images": 3},
                                                                       ensure_ascii=False) + "\n```\n\n" + PUB_MD)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    @classmethod
    def write(cls, name, text):
        p = os.path.join(cls.post, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def test_title_and_headings(self):
        r = diff_published.compare(self.final, self.pub_json)
        self.assertEqual(r["title"], {"before": TITLE, "after": PUB_TITLE, "changed": True})
        h = r["headings"]
        self.assertEqual(h["renamed"], [{"before": "3️⃣ 주문 방법", "after": "2️⃣ 주문하는 방법"}])
        self.assertEqual(h["removed"], ["2️⃣ 연습 방법"])
        self.assertEqual(h["added"], ["3️⃣ 자주 묻는 질문"])

    def test_paragraphs_added_removed_changed(self):
        p = diff_published.compare(self.final, self.pub_json)["paragraphs"]
        self.assertEqual(p["removed"], [P3])
        self.assertEqual(p["added"], ["처음 오시는 분도 걱정하지 않으셔도 돼요."])
        changed = {x["before"]: x for x in p["changed"]}
        self.assertEqual(set(changed), {P2, P4 + " 관련글"})
        self.assertTrue(changed[P2]["after"].startswith("포장 시간은 4분이에요"))
        self.assertGreaterEqual(changed[P2]["ratio"], 0.5)
        # 자리를 옮기고 링크 글자만 바뀐 P4는 삭제+추가가 아니라 수정 한 건(링크 문법은 벗기고 글자만 비교)
        self.assertEqual(changed[P4 + " 관련글"]["after"], P4 + " 선물 포장 준비물")
        # 그대로인 목록·표 행은 변경에 나오지 않는다
        self.assertFalse(any("상자 고르기" in x for x in p["added"] + p["removed"]))
        self.assertFalse(any("포장|2분" in x for x in p["added"] + p["removed"]))

    def test_tone_length_images_closing(self):
        r = diff_published.compare(self.final, self.pub_json)
        self.assertEqual(r["tone"]["before"], {"합니다": 8, "해요": 0})
        self.assertEqual(r["tone"]["after"]["해요"], 3)
        self.assertGreater(r["tone"]["after"]["해요"], r["tone"]["before"]["해요"])
        self.assertLess(r["length"]["after"], r["length"]["before"])
        self.assertEqual(r["images"], {"before": 3, "after": 3})  # final 2장 + 표지 1장
        self.assertTrue(r["closing_block_kept"])
        self.assertIn("해요체가 늘었습니다", r["summary"])
        self.assertTrue(3 <= len(r["summary"].split("\n")) <= 6)

    def test_closing_block_missing(self):
        pub = self.write("pub-noclose.json", json.dumps(
            {"stats": {"title": TITLE}, "markdown": PUB_MD.split("## 📞")[0]}, ensure_ascii=False))
        r = diff_published.compare(self.final, pub)
        self.assertFalse(r["closing_block_kept"])
        self.assertFalse(r["title"]["changed"])
        self.assertIn("찾지 못함", r["summary"])

    def test_md_input_same_as_json(self):
        a = diff_published.compare(self.final, self.pub_json)
        b = diff_published.compare(self.final, self.pub_md)
        self.assertEqual(a, b)

    def test_plain_markdown_input_uses_h1_title(self):
        pub = self.write("plain.md", f"# {PUB_TITLE}\n\n" + PUB_MD)
        r = diff_published.compare(self.final, pub)
        self.assertEqual(r["title"]["after"], PUB_TITLE)
        self.assertEqual(r["images"]["after"], 3)

    def test_identical_has_no_changes(self):
        same = self.write("same.md", FINAL)
        r = diff_published.compare(self.final, same)
        self.assertFalse(r["title"]["changed"])
        self.assertEqual(r["headings"], {"added": [], "removed": [], "renamed": []})
        self.assertEqual(r["paragraphs"], {"removed": [], "added": [], "changed": []})
        self.assertEqual(r["length"]["before"], r["length"]["after"])

    def test_long_text_truncated_and_capped(self):
        long_p = "가" * 300 + "입니다."
        many = "\n\n".join(f"새 문단 {i}번째 내용입니다." for i in range(30))
        pub = self.write("long.json", json.dumps({"stats": {"title": TITLE}, "markdown": long_p + "\n\n" + many},
                                                 ensure_ascii=False))
        p = diff_published.compare(self.final, pub)["paragraphs"]
        self.assertEqual(len(p["added"]), 20)
        self.assertTrue(all(len(x) <= 200 for x in p["added"] + p["removed"]))

    def test_cli_json_and_errors(self):
        env = dict(os.environ, PYTHONUTF8="1")
        run = lambda *a: subprocess.run([sys.executable, SCRIPT, *a], capture_output=True, text=True,
                                        encoding="utf-8", env=env)
        p = run(self.final, self.pub_json, "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        d = json.loads(p.stdout)
        for k in ("title", "headings", "paragraphs", "tone", "length", "images", "closing_block_kept", "summary"):
            self.assertIn(k, d)
        p = run(self.final, self.pub_json)
        self.assertEqual(p.returncode, 0)
        self.assertIn("제목: 바뀜", p.stdout)
        self.assertEqual(run(self.final, os.path.join(self.post, "nope.json")).returncode, 2)
        bad = self.write("bad.json", "{ not json")
        self.assertEqual(run(self.final, bad).returncode, 2)
        for name, body in (("list.json", "[1, 2]"), ("str.json", '"text"')):
            p = run(self.final, self.write(name, body))
            self.assertEqual(p.returncode, 2, name)
            self.assertIn("객체가 아닙니다", p.stderr)

    def test_table_cell_spacing_ignored(self):
        pub = self.write("table.md", FINAL.replace("| 포장 | 2분 |", "|포장|   2분|").replace("| 항목 | 시간 |", "| 항목|시간 |"))
        r = diff_published.compare(self.final, pub)
        self.assertEqual(r["paragraphs"], {"removed": [], "added": [], "changed": []})


if __name__ == "__main__":
    unittest.main()
