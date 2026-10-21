#!/usr/bin/env python3
"""verify_blogs.py — 네이버 블로그 ID·URL이 실제로 읽히는지, 얼마나 자주 쓰는지 RSS로 확인한다(표준 라이브러리만).

사용 (작업 폴더에서):
    python3 scripts/verify_blogs.py <blogId 또는 URL …> [--json] [--days 90]

- 입력 형식(5가지): blogId / https://blog.naver.com/<id> / https://blog.naver.com/<id>/<logNo> /
  https://m.blog.naver.com/<id>/<logNo> / https://blog.naver.com/PostView.naver?blogId=<id>&logNo=<n>
  → (id, logNo 또는 없음). ID가 [A-Za-z0-9_-]+ 형식이 아니면 그 항목만 `형식 오류`.
- 블로그마다 RSS(최근 글 최대 50개)를 한 번 읽는다(같은 ID는 한 번만). 요청 사이 0.5초 쉰다.
  UA 헤더는 fetch_posts.UA, 타임아웃 10초. fetch_posts.fetch_rss와 같은 방식으로 파싱하되 오류는 행 단위로 받는다.
- 행: ID | 응답 | 최근 N일 글 수 | 월 추정 | 카테고리 상위 3 | 최근 제목 3
  응답 = OK / 없음(채널 없음·404) / 비공개(RSS 비어 있음) / 네트워크 / 형식 오류
  월 추정 = 최근 N일 글 수 / (N/30), 소수 1자리. 카테고리 상위 3은 RSS 글 전체 기준(많은 순).
  RSS는 최근 50개까지라 아주 자주 쓰는 블로그는 월 추정이 실제보다 작게 나올 수 있다.
- --json: [{"blogId","logNo","status","recent_count","per_month","categories":[…],
           "recent":[{"title","date","logNo","category"}],"error"}]

종료 코드: 0=한 개 이상 OK · 2=인자 없음·전부 형식 오류·OK 없음(없음·비공개) · 5=전부 네트워크 실패
"""
import argparse
import collections
import datetime
import email.utils
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_posts  # noqa: E402 — UA·RSS_URL·SLEEP 공유(표준 출력 UTF-8 설정도 여기서 된다)

TIMEOUT = 10
DEFAULT_DAYS = 90
ID_RE = re.compile(r"[A-Za-z0-9_-]+")
NAVER_HOSTS = {"blog.naver.com", "m.blog.naver.com"}

ST_OK, ST_NONE, ST_PRIVATE, ST_NET, ST_FORMAT = "OK", "없음", "비공개", "네트워크", "형식 오류"


class RowError(Exception):
    """행 하나의 실패. status = ST_NONE / ST_PRIVATE / ST_NET."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def normalize(raw):
    """입력 한 개 → (blogId, logNo 또는 None). 형식이 맞지 않으면 ValueError."""
    s = (raw or "").strip()
    if not s:
        raise ValueError("빈 값")
    if ID_RE.fullmatch(s):
        return s, None
    if not re.match(r"^https?://", s, re.I):
        s = "https://" + s if re.match(r"^(m\.)?blog\.naver\.com/", s, re.I) else s
    u = urllib.parse.urlsplit(s)
    if u.scheme.lower() not in ("http", "https") or (u.hostname or "").lower() not in NAVER_HOSTS:
        raise ValueError("blog.naver.com 주소나 블로그 ID가 아닙니다")
    parts = [p for p in u.path.split("/") if p]
    if parts and parts[0].lower() in ("postview.naver", "postview.nhn"):
        q = urllib.parse.parse_qs(u.query)
        blog_id = (q.get("blogId") or [""])[0].strip()
        log_no = (q.get("logNo") or [""])[0].strip() or None
    elif 1 <= len(parts) <= 2:
        blog_id = parts[0]
        log_no = parts[1] if len(parts) == 2 else None
    else:
        raise ValueError("알 수 없는 주소 형식")
    if not ID_RE.fullmatch(blog_id):
        raise ValueError("블로그 ID 형식이 아닙니다")
    if log_no is not None and not log_no.isdigit():
        raise ValueError("글 번호(logNo) 형식이 아닙니다")
    return blog_id, log_no


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": fetch_posts.UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RowError(ST_NONE, "HTTP 404") from None
        raise RowError(ST_NET, f"HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise RowError(ST_NET, f"네트워크 실패({getattr(e, 'reason', e)})") from None


def rss_summary(blog_id):
    """RSS를 읽어 글 목록(date 내림차순)을 반환. 실패는 RowError(행 단위)."""
    xml_text = http_get(fetch_posts.RSS_URL.format(blog_id=blog_id))
    try:
        root = ET.fromstring(xml_text.lstrip())
    except ET.ParseError:
        raise RowError(ST_NONE, "RSS를 읽을 수 없음(존재하지 않는 블로그일 수 있음)") from None
    if root.find("channel") is None or not (root.findtext("channel/title") or "").strip():
        raise RowError(ST_NONE, "RSS 채널 없음(존재하지 않는 블로그)")
    posts = []
    for item in root.iter("item"):
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        m = re.search(r"(\d+)(?:\?|$)", guid or link.split("?")[0])
        if not m:
            continue
        try:
            date = email.utils.parsedate_to_datetime(item.findtext("pubDate")).date().isoformat()
        except (TypeError, ValueError):
            continue
        posts.append({"title": (item.findtext("title") or "").strip(), "date": date,
                      "logNo": m.group(1), "category": (item.findtext("category") or "").strip()})
    if not posts:
        raise RowError(ST_PRIVATE, "RSS에 글이 없음(비공개이거나 글 없음)")
    posts.sort(key=lambda p: (p["date"], p["logNo"]), reverse=True)
    return posts


def summarize(posts, days, today):
    since = (today - datetime.timedelta(days=days)).isoformat()
    recent_count = sum(1 for p in posts if p["date"] >= since)
    counts = collections.Counter(p["category"] for p in posts if p["category"])
    order = {c: i for i, c in reversed(list(enumerate(p["category"] for p in posts)))}
    cats = sorted(counts, key=lambda c: (-counts[c], order[c]))[:3]
    return {"recent_count": recent_count, "per_month": round(recent_count / (days / 30), 1),
            "categories": cats, "recent": posts[:3]}


def empty_row(blog_id, log_no, status, error):
    return {"blogId": blog_id, "logNo": log_no, "status": status, "recent_count": None, "per_month": None,
            "categories": [], "recent": [], "error": error}


def verify(inputs, days=DEFAULT_DAYS, today=None):
    today = today or datetime.date.today()
    cache, rows, fetched = {}, [], 0
    for raw in inputs:
        try:
            blog_id, log_no = normalize(raw)
        except ValueError as e:
            rows.append(empty_row(raw, None, ST_FORMAT, str(e)))
            continue
        if blog_id not in cache:
            if fetched:
                time.sleep(fetch_posts.SLEEP)
            fetched += 1
            try:
                cache[blog_id] = rss_summary(blog_id)
            except RowError as e:
                cache[blog_id] = e
        got = cache[blog_id]
        if isinstance(got, RowError):
            rows.append(empty_row(blog_id, log_no, got.status, str(got)))
            continue
        row = empty_row(blog_id, log_no, ST_OK, None)
        row.update(summarize(got, days, today))
        rows.append(row)
    return rows


def exit_code(rows):
    if any(r["status"] == ST_OK for r in rows):
        return 0
    valid = [r for r in rows if r["status"] != ST_FORMAT]
    if valid and all(r["status"] == ST_NET for r in valid):
        return 5
    return 2


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_table(rows, days):
    out = [f"| ID | 응답 | 최근 {days}일 글 수 | 월 추정 | 카테고리 상위 3 | 최근 제목 3 |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        if r["status"] == ST_OK:
            vals = [r["blogId"], r["status"], r["recent_count"], f"{r['per_month']:.1f}",
                    ", ".join(r["categories"]) or "-", " / ".join(p["title"] for p in r["recent"]) or "-"]
        else:
            vals = [r["blogId"], r["status"], "-", "-", "-", "-"]
        out.append("| " + " | ".join(cell(v) for v in vals) + " |")
    return "\n".join(out)


def main(argv=None, today=None):
    ap = argparse.ArgumentParser(
        description="네이버 블로그 ID·URL을 RSS로 확인하고 최근 글 수·월 추정·카테고리·최근 제목을 표(또는 JSON)로 보여 줍니다.",
        epilog="종료 코드: 0=한 개 이상 OK, 2=인자 없음·전부 형식 오류·OK 없음, 5=전부 네트워크 실패.")
    ap.add_argument("inputs", nargs="*", metavar="blogId_또는_URL",
                    help="blogId · blog.naver.com/<id>[/<logNo>] · m.blog.naver.com/<id>/<logNo> · PostView.naver?blogId=…&logNo=…")
    ap.add_argument("--json", action="store_true", help="표 대신 JSON 배열로 출력")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS, metavar="N", help=f"최근 며칠을 셀지(기본 {DEFAULT_DAYS})")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    inputs = [s for s in a.inputs if s.strip()]
    if not inputs:
        print("오류: 확인할 블로그 ID 또는 URL을 하나 이상 주세요.", file=sys.stderr)
        return 2
    if a.days <= 0:
        print("오류: --days는 1 이상이어야 합니다.", file=sys.stderr)
        return 2
    rows = verify(inputs, a.days, today)
    for r in rows:
        if r["status"] != ST_OK:
            print(f"경고: {r['blogId']} — {r['status']}({r['error']})", file=sys.stderr)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(render_table(rows, a.days))
    return exit_code(rows)


if __name__ == "__main__":
    sys.exit(main())
