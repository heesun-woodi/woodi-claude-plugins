#!/usr/bin/env python3
"""주제 중복 판정(blog-topic-research §4). 출처 글 제목을 우리 블로그 전체 글 제목과 비교해 ○/△/×를 출력한다.
제목 비교에서 뺄 말은 knowledge/business-profile.md의 `고객 지역`·`업체 유형어`(제목 토큰에서 제거)·`업종 일반어`(핵심 토큰
겹침 계산에서만 제외)(필수 — 비면 exit 2)와
`제목 정규화`(선택, `띄어 쓴 표기 → 붙인 표기`를 쉼표로 구분)·`홍보 표지어`·`공지 표지어`(선택 — 없거나 자리표시면
업종 중립 기본값 DEFAULT_PROMO·DEFAULT_NOTICE) 행에서 읽는다(load_profile). 우리 글 목록이 비면(새 블로그) ×(우리 글 없음)."""
import argparse
import json
import os
import re
import sys
for _s in (sys.stdout, sys.stderr):  # Windows 콘솔(cp949)에서도 한글·이모지 출력이 죽지 않게
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lint_post import find_knowledge, missing_row, profile_list  # noqa: E402
REGIONS, STRIP, TITLE_NORMALIZE = [], [], []  # load_profile()이 business-profile.md에서 채운다
DEFAULT_PROMO = ["안내","일정안내","모집","모집안내","접수중","마감","이벤트","할인","오픈"]  # 업종 중립 기본값 — profile `홍보 표지어`가 없을 때
DEFAULT_NOTICE = ["일정안내","일정 안내","공지","휴무","모집"]  # 공지 유형 표지어 기본값 — profile `공지 표지어`가 없을 때
PROMO, NOTICE = list(DEFAULT_PROMO), list(DEFAULT_NOTICE)  # load_profile()이 profile 행으로 바꾼다
GENERIC = set()  # 핵심 토큰 겹침 계산에서 제외(너무 흔함) — load_profile()이 `업종 일반어`로 채운다
def load_profile(kdir):
    """`고객 지역` → REGIONS, `업체 유형어` → STRIP, `업종 일반어` → GENERIC, `제목 정규화`(선택) → TITLE_NORMALIZE,
    `홍보 표지어`·`공지 표지어`(선택) → PROMO·NOTICE(없으면 기본값). 필수 행이 비면 ValueError."""
    regions, kinds, common = (profile_list(kdir, n) for n in ("고객 지역", "업체 유형어", "업종 일반어"))
    for name, v in (("고객 지역", regions), ("업체 유형어", kinds), ("업종 일반어", common)):
        if not v: raise ValueError(missing_row(name, kdir))
    REGIONS[:], STRIP[:] = regions, kinds
    GENERIC.clear(); GENERIC.update(common)
    TITLE_NORMALIZE[:] = [tuple(x.strip() for x in re.split(r"→|->", p, maxsplit=1))
                          for p in profile_list(kdir, "제목 정규화") if re.search(r"→|->", p)]
    PROMO[:] = profile_list(kdir, "홍보 표지어") or DEFAULT_PROMO
    NOTICE[:] = profile_list(kdir, "공지 표지어") or DEFAULT_NOTICE
def tokens(title):
    for a, b in TITLE_NORMALIZE:
        title = title.replace(a, b)
    t = re.sub(r"\d{4}\s*년|\d{1,2}\s*월|\d{1,2}\s*일|\([월화수목금토일]\)", " ", title)
    t = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", t)
    words = t.split()
    out = set()
    for w in words:
        if w in REGIONS or w in PROMO or w in STRIP: continue
        if len(w) > 2 and w[-1] in "은는이가을를의에도로과와": w = w[:-1]  # 조사 1글자 제거
        if len(re.findall(r"[가-힣]", w)) >= 2: out.add(w)
    return out
def judge(src, keyword, posts, notice=False):
    if not posts: return (0.0, 0, "×", "", "")  # 우리 글이 없으면(새 블로그) 겹칠 글도 없다
    S, K = tokens(src), tokens(keyword) - GENERIC
    if notice:
        for n in NOTICE:  # 소스 제목에 있는 표지어와 같은 표지어를 가진 우리 글(최신순)
            if n in src:
                for p in sorted(posts, key=lambda p: p["date"], reverse=True):
                    if n in p["title"]:
                        return (0.0, 0, "○", p["title"], p["date"])  # 공지 유형 중복
    best = []
    for p in posts:
        O = tokens(p["title"]); u = S | O
        j = len(S & O) / len(u) if u else 0
        core = len(K & O)
        lab = "○" if (j >= 0.5 or core >= 2) else ("△" if j >= 0.25 else "×")
        best.append((j, core, lab, p["title"], p["date"]))
    best.sort(key=lambda x: ({"○":0,"△":1,"×":2}[x[2]], -x[0], -x[1]))
    return best[0]


def main():
    ap = argparse.ArgumentParser(description="출처 글 제목이 우리 블로그 기존 글과 중복인지 판정한다. ○ 중복 / △ 부분 중복 / × 없음.")
    ap.add_argument("title", help="출처 글 제목")
    ap.add_argument("keyword", help="후보의 핵심 키워드(4어절 이하)")
    ap.add_argument("posts", nargs="?", default="work/own-posts.json", help="우리 글 목록 JSON(기본: work/own-posts.json)")
    ap.add_argument("--notice", action="store_true", help="공지 유형 규칙: 소스 제목의 공지 표지어(profile `공지 표지어`, 기본 일정안내·공지·휴무·모집)와 같은 표지어를 가진 우리 글이 있으면 ○")
    a = ap.parse_args()
    try:
        load_profile(find_knowledge(a.posts))  # knowledge/는 글 목록 JSON 위로 찾는다
    except ValueError as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(2)
    with open(a.posts, encoding="utf-8") as f:
        posts = json.load(f)
    j, core, lab, t, d = judge(a.title, a.keyword, posts, a.notice)
    print(f"{lab}\tjaccard={j:.2f}\tcore={core}\t" + (f"{t} ({d})" if t else "(우리 글 없음)"))


if __name__ == "__main__":
    main()
