#!/usr/bin/env python3
"""keyword_expand.py — 씨앗 키워드를 네이버 자동완성으로 넓혀 연관 검색어 목록을 만든다(표준 라이브러리만).

사용 (작업 폴더에서):
    python3 scripts/keyword_expand.py <씨앗 …> [--depth 1|2] [--json] [--max 60]

- 호출: 네이버 자동완성(ac.search.naver.com/nx/ac) 씨앗당 1회. 헤더 User-Agent: Mozilla/5.0, 타임아웃 5초. 재시도 없음.
- 결과: 응답 items[0]의 각 원소 [키워드, 플래그] 중 키워드.
  depth 2면 씨앗마다 1차 결과 상위 5개(씨앗 자신 제외)를 다시 조회한다(2차 결과의 씨앗 = 원래 씨앗).
- 중복 제거(공백 정규화), 씨앗 자체 제외, 1차 결과가 먼저 오고 --max개에서 자른다.
- 표: | 키워드 | 씨앗 |  ·  --json: [{"keyword","seed","depth"}]
- 일부 요청이 실패하면 stderr에 경고를 쓰고 계속한다. 결과 0개여도 exit 0(빈 표 + stderr 안내).

종료 코드: 0=완료(결과 0개 포함) · 2=인자 없음·잘못된 인자 · 5=모든 요청 네트워크 실패
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
for _s in (sys.stdout, sys.stderr):  # Windows 콘솔(cp949)에서도 한글 출력이 죽지 않게
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

UA = "Mozilla/5.0"
TIMEOUT = 5
SLEEP = 0.3
DEPTH2_TOP = 5
DEFAULT_MAX = 60
AC_URL = ("https://ac.search.naver.com/nx/ac?q={q}&con=1&frm=nv&ans=2&r_format=json&r_enc=UTF-8"
          "&r_unicode=0&t_koreng=1&run=2&rev=4&q_enc=UTF-8&st=100")


class FetchError(Exception):
    """요청 하나의 실패(네트워크·HTTP 오류·JSON 아님)."""


def norm(text):
    return " ".join(str(text).split())


def build_url(seed):
    return AC_URL.format(q=urllib.parse.quote(seed, safe=""))


def parse_items(data):
    """자동완성 응답(dict) → 키워드 목록(응답 순서). items가 비었거나 items[0]이 없으면 []."""
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list) or not items or not isinstance(items[0], list):
        return []
    out = []
    for el in items[0]:
        if isinstance(el, list) and el and isinstance(el[0], str):
            out.append(el[0])
        elif isinstance(el, str):
            out.append(el)
    return out


def fetch_suggestions(seed):
    req = urllib.request.Request(build_url(seed), headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise FetchError(f"HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise FetchError(f"네트워크 실패({getattr(e, 'reason', e)})") from None
    try:
        return parse_items(json.loads(body))
    except ValueError:
        raise FetchError("JSON이 아닌 응답") from None


def expand(seeds, depth=1, max_items=DEFAULT_MAX):
    """(결과 목록, 요청 수, 실패 수). 결과: [{"keyword","seed","depth"}]."""
    seeds = [norm(s) for s in seeds if norm(s)]
    seen = set(seeds)
    queried = set()
    results, stats = [], {"requests": 0, "failed": 0}

    def query(q):
        if stats["requests"]:
            time.sleep(SLEEP)
        stats["requests"] += 1
        queried.add(q)
        try:
            return [norm(k) for k in fetch_suggestions(q) if norm(k)]
        except FetchError as e:
            stats["failed"] += 1
            print(f"경고: '{q}' 자동완성 조회 실패 — {e}. 이 키워드는 건너뜁니다.", file=sys.stderr)
            return []

    first = {}
    for seed in seeds:
        if seed in queried:
            continue
        got = query(seed)
        first[seed] = [k for k in got if k != seed]
        for k in got:
            if k not in seen:
                seen.add(k)
                results.append({"keyword": k, "seed": seed, "depth": 1})
    if depth >= 2:
        for seed in seeds:
            for k in first.get(seed, [])[:DEPTH2_TOP]:
                if k in queried:
                    continue
                for k2 in query(k):
                    if k2 not in seen:
                        seen.add(k2)
                        results.append({"keyword": k2, "seed": seed, "depth": 2})
    return results[:max_items], stats["requests"], stats["failed"]


def cell(text):
    return str(text).replace("|", "\\|")


def render_table(results):
    out = ["| 키워드 | 씨앗 |", "|---|---|"]
    out += [f"| {cell(r['keyword'])} | {cell(r['seed'])} |" for r in results]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="씨앗 키워드를 네이버 자동완성으로 넓혀 연관 검색어 표(또는 JSON)를 만듭니다.",
        epilog="종료 코드: 0=완료(결과 0개 포함), 2=인자 없음, 5=모든 요청 네트워크 실패.")
    ap.add_argument("seeds", nargs="*", metavar="씨앗", help="씨앗 키워드(띄어쓰기가 있으면 따옴표로 묶기)")
    ap.add_argument("--depth", type=int, choices=(1, 2), default=1,
                    help=f"1=씨앗만 조회(기본), 2=1차 결과 상위 {DEPTH2_TOP}개도 다시 조회")
    ap.add_argument("--json", action="store_true", help="표 대신 JSON 배열로 출력")
    ap.add_argument("--max", type=int, default=DEFAULT_MAX, metavar="N", help=f"최대 결과 수(기본 {DEFAULT_MAX})")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    seeds = [norm(s) for s in a.seeds if norm(s)]
    if not seeds:
        print("오류: 씨앗 키워드를 하나 이상 주세요.", file=sys.stderr)
        return 2
    if a.max <= 0:
        print("오류: --max는 1 이상이어야 합니다.", file=sys.stderr)
        return 2
    results, requests, failed = expand(seeds, a.depth, a.max)
    if requests and failed == requests:
        print("오류: 모든 자동완성 요청이 실패했습니다(네트워크 확인 후 다시 실행).", file=sys.stderr)
        return 5
    if not results:
        print("안내: 연관 검색어가 없습니다 — 씨앗을 더 짧거나 일반적인 말로 바꿔 보세요.", file=sys.stderr)
    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(render_table(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
