#!/usr/bin/env python3
"""업로드본 final.md와 실제 발행된 글을 비교해 담당자가 발행 전에 고친 점을 뽑는다 (표준 라이브러리만 사용).

사용 예(작업 폴더에서):
  python3 scripts/fetch_post.py <blogId> <logNo> --json > work/posts/<NNN-slug>/published.json
  python3 scripts/diff_published.py work/posts/<NNN-slug>/final.md work/posts/<NNN-slug>/published.json --json

발행본 입력: fetch_post.py `--json` 출력({"stats": {...}, "markdown": "..."}), fetch_post.py 기본 출력(```json 통계``` + 마크다운),
또는 그냥 마크다운(제목은 frontmatter title 또는 첫 `# ` 줄).
정규화(양쪽 같게): frontmatter·HTML 주석·`# 제목` 줄·이미지·`ㅤ`(U+3164) 줄·`**#…**` 해시태그 줄·`:::place` 줄·표 구분선·빈 줄 제거,
`**`·링크 문법·목록/인용 표시·인라인 코드 표시를 벗기고 공백을 하나로(표 행은 `|` 양옆 공백도 지움). 비교 단위는 줄(소제목 / 문단·목록 항목·표 행).
출력 JSON: title{before,after,changed} · headings{added,removed,renamed:[{before,after}]} ·
  paragraphs{removed,added,changed:[{before,after,ratio}]}(difflib, 각 최대 20개, 문장은 200자에서 자름) ·
  tone{before:{합니다,해요}, after:{...}}(문장 끝 수, 허용 의문문 제외) · length{before,after}(공백 제외 글자수) ·
  images{before,after}(before = final.md 이미지 + 글 폴더 images/00-cover.png가 있으면 표지 1장 — 업로드 도구가 맨 앞에 넣음) ·
  closing_block_kept(발행본에 `📞` 줄이 있고 그 뒤에 해시태그 줄이 있음; 프로필 `마무리 블록`에 `문의헤딩`이 없으면 null=해당 없음) · summary(사람용 한국어 3~6줄).
종료 코드: 0=비교 완료, 2=사용 오류(파일 없음·읽기 실패·JSON이 객체가 아님).
"""
import argparse
import difflib
import json
import os
import re
import sys
for _s in (sys.stdout, sys.stderr):  # Windows 콘솔(cp949)에서도 한글·이모지 출력이 죽지 않게
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lint_post import (HTMLC_RE, IMG_RE, Q_OK, SENT_SPLIT_RE, TRAIL_RE, haeyo_end,  # noqa: E402
                       find_knowledge, is_hashtag_line, load_closing_blocks, parse_frontmatter)

MAX_ITEMS, MAX_LEN = 20, 200
CHANGED_MIN = 0.5  # 이 비율 이상 닮은 문단 쌍은 "수정", 아래면 삭제+추가
FILLER_LINE_RE = re.compile(r"^\s*ㅤ+\s*$")
HEADING_RE = re.compile(r"^\s*#{2,6}\s+")
H1_RE = re.compile(r"^\s*#\s+")
TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|>\s*)+")
FENCE_JSON_RE = re.compile(r"^\s*```json\s*\n(.*?)\n```\s*\n?", re.S)
CONTACT = "📞"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")


def clean_inline(s):
    s = IMG_RE.sub("", s)
    s = LINK_RE.sub(r"\1", s)
    s = s.replace("**", "").replace("`", "").replace("​", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def split_doc(md):
    """마크다운 본문 → (소제목 목록, 문단 목록, 원본 줄 목록). 정규화 규칙은 모듈 docstring."""
    raw = HTMLC_RE.sub("", md).split("\n")
    heads, paras = [], []
    for ln in raw:
        s = ln.strip()
        if (not s or FILLER_LINE_RE.match(s) or H1_RE.match(s) or s.startswith(":::")
                or TABLE_SEP_RE.match(s) or s.startswith("```") or is_hashtag_line(s)):
            continue
        if HEADING_RE.match(s):
            t = clean_inline(HEADING_RE.sub("", s))
            if t:
                heads.append(t)
            continue
        t = clean_inline(LIST_RE.sub("", s))
        if t.startswith("|"):  # 표 행: 칸 사이 공백 차이를 없앤다
            t = re.sub(r"\s*\|\s*", "|", t)
        if t:
            paras.append(t)
    return heads, paras, raw


def load_final(path):
    lines = read(path).split("\n")
    fm, start, _ = parse_frontmatter(lines)
    body = lines[start:] if fm is not None else lines
    title = (fm or {}).get("title") if fm else None
    if not isinstance(title, str) or not title:
        title = next((H1_RE.sub("", ln).strip() for ln in body if H1_RE.match(ln)), "")
    return title, "\n".join(body)


def load_published(path):
    """(제목, 마크다운, stats.images 또는 None)."""
    text = read(path)
    head = text.lstrip()[:1]
    data = None
    if head in ("{", "[") or path.lower().endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            if head == "{" or path.lower().endswith(".json"):
                raise ValueError(f"JSON을 읽을 수 없습니다: {e}")
        else:
            if not isinstance(data, dict):
                raise ValueError("JSON이 객체가 아닙니다 — fetch_post.py --json 출력({\"stats\", \"markdown\"})을 넣으세요")
    if isinstance(data, dict):
        stats = data.get("stats") or {}
        return str(stats.get("title") or ""), str(data.get("markdown") or ""), stats.get("images")
    m = FENCE_JSON_RE.match(text)
    if m:  # fetch_post.py 기본 출력(통계 블록 + 마크다운)
        try:
            stats = json.loads(m.group(1))
        except json.JSONDecodeError:
            stats = {}
        return str(stats.get("title") or ""), text[m.end():], stats.get("images")
    title, body = load_final(path)
    return title, body, None


def cut(s):
    return s if len(s) <= MAX_LEN else s[:MAX_LEN - 1] + "…"


def tone_counts(paras):
    out = {"합니다": 0, "해요": 0}
    for p in paras:
        parts = SENT_SPLIT_RE.split(p)
        for j in range(0, len(parts), 2):
            question = (parts[j + 1] if j + 1 < len(parts) else "") == "?"
            s = TRAIL_RE.sub("", parts[j])
            if not s:
                continue
            if s.endswith("니다"):
                out["합니다"] += 1
            elif question and s.endswith(Q_OK):
                continue
            elif haeyo_end(s):
                out["해요"] += 1
    return out


def chars(heads, paras):
    return len(re.sub(r"\s+", "", "".join(heads + paras)))


def pair_block(a, b):
    """가장 닮은 쌍부터 짝짓는다(ratio>=CHANGED_MIN → changed). 남는 것은 removed/added."""
    cands = sorted(((difflib.SequenceMatcher(None, x, y, autojunk=False).ratio(), i, j)
                    for i, x in enumerate(a) for j, y in enumerate(b)), key=lambda t: (-t[0], t[1], t[2]))
    ua, ub, pairs = set(), set(), []
    for r, i, j in cands:
        if r < CHANGED_MIN:
            break
        if i not in ua and j not in ub:
            ua.add(i)
            ub.add(j)
            pairs.append((i, j, r))
    changed = [(a[i], b[j], r) for i, j, r in sorted(pairs)]
    removed = [x for i, x in enumerate(a) if i not in ua]
    added = [y for j, y in enumerate(b) if j not in ub]
    return changed, removed, added


def diff_lists(a, b):
    """순서 비교(difflib)로 빠진 것·새로 생긴 것을 모은 뒤, 그 둘을 한꺼번에 짝지어 수정(옮겨진 것 포함)을 찾는다."""
    removed, added = [], []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace"):
            removed += a[i1:i2]
        if op in ("insert", "replace"):
            added += b[j1:j2]
    return pair_block(removed, added)


def closing_kept(raw):
    k = max((i for i, ln in enumerate(raw) if CONTACT in ln), default=None)
    return k is not None and any(is_hashtag_line(ln) for ln in raw[k + 1:])


def count_images(md):
    return len(IMG_RE.findall(HTMLC_RE.sub("", md)))


def closing_applicable(final_path, knowledge=None):
    """프로필 `마무리 블록`에 `문의헤딩`이 있으면 True, 없으면 False(비교 대상 아님). 프로필을 못 읽으면 True(현행 동작)."""
    try:
        return "문의헤딩" in load_closing_blocks(knowledge or find_knowledge(final_path))
    except (ValueError, OSError):
        return True


def compare(final_path, published_path, knowledge=None):
    t_before, body_before = load_final(final_path)
    t_after, body_after, pub_images = load_published(published_path)
    hb, pb, _ = split_doc(body_before)
    ha, pa, raw_a = split_doc(body_after)
    norm = lambda s: re.sub(r"\s+", "", s or "")
    # 표지 1장은 발행본(fetch_post 출력 — stats.images가 있음)과 비교할 때만 더한다.
    # 초안 대 초안(직접 수정 비교)이면 양쪽 모두 표지가 본문에 없다.
    cover = isinstance(pub_images, int) and os.path.isfile(
        os.path.join(os.path.dirname(os.path.abspath(final_path)), "images", "00-cover.png"))

    h_changed, h_removed, h_added = diff_lists(hb, ha)
    p_changed, p_removed, p_added = diff_lists(pb, pa)
    res = {
        "title": {"before": t_before, "after": t_after, "changed": bool(t_after) and norm(t_before) != norm(t_after)},
        "headings": {"added": [cut(x) for x in h_added[:MAX_ITEMS]],
                     "removed": [cut(x) for x in h_removed[:MAX_ITEMS]],
                     "renamed": [{"before": cut(x), "after": cut(y)} for x, y, _ in h_changed[:MAX_ITEMS]]},
        "paragraphs": {"removed": [cut(x) for x in p_removed[:MAX_ITEMS]],
                       "added": [cut(x) for x in p_added[:MAX_ITEMS]],
                       "changed": [{"before": cut(x), "after": cut(y), "ratio": round(r, 2)}
                                   for x, y, r in p_changed[:MAX_ITEMS]]},
        "tone": {"before": tone_counts(pb), "after": tone_counts(pa)},
        "length": {"before": chars(hb, pb), "after": chars(ha, pa)},
        "images": {"before": count_images(body_before) + (1 if cover else 0),
                   "after": pub_images if isinstance(pub_images, int) else count_images(body_after)},
        "closing_block_kept": closing_kept(raw_a) if closing_applicable(final_path, knowledge) else None,
    }
    counts = {"h": (len(h_added), len(h_removed), len(h_changed)),
              "p": (len(p_removed), len(p_added), len(p_changed))}
    res["summary"] = summarize(res, counts)
    return res


def summarize(r, counts):
    lines = []
    t = r["title"]
    if not t["after"]:
        lines.append("제목: 발행본 제목을 읽지 못했습니다(마크다운 입력 — 비교 생략).")
    elif t["changed"]:
        lines.append(f"제목: 바뀜 — \"{t['before']}\" → \"{t['after']}\"")
    else:
        lines.append("제목: 그대로입니다.")
    ha, hr, hc = counts["h"]
    pr, pa, pc = counts["p"]
    lines.append("소제목: " + (f"추가 {ha} · 삭제 {hr} · 이름 바뀜 {hc}" if ha or hr or hc else "변화 없음")
                 + " / 문단: " + (f"삭제 {pr} · 추가 {pa} · 수정 {pc}" if pr or pa or pc else "변화 없음"))
    lb, la = r["length"]["before"], r["length"]["after"]
    pct = f" ({(la - lb) * 100 / lb:+.0f}%)" if lb else ""
    lines.append(f"분량(공백 제외): {lb}자 → {la}자{pct}")
    tb, ta = r["tone"]["before"], r["tone"]["after"]
    tone = f"말투(문장 끝): 합니다체 {tb['합니다']} → {ta['합니다']}, 해요체 {tb['해요']} → {ta['해요']}"
    if ta["해요"] > tb["해요"]:
        tone += " — 해요체가 늘었습니다"
    lines.append(tone)
    lines.append(f"이미지: {r['images']['before']}장 → {r['images']['after']}장 · 마무리 블록(📞→해시태그): "
                 + ("해당 없음" if r["closing_block_kept"] is None else "유지" if r["closing_block_kept"] else "발행본에서 찾지 못함"))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="업로드본 final.md와 발행된 글(fetch_post.py 출력)을 비교해 바뀐 점을 요약한다.",
                                 epilog="종료 코드: 0=비교 완료, 2=사용 오류(파일 없음·읽기 실패)")
    ap.add_argument("final", help="업로드본 final.md")
    ap.add_argument("published", help="발행본: fetch_post.py --json 출력(.json) 또는 마크다운(.md)")
    ap.add_argument("--knowledge", metavar="DIR", help="knowledge 폴더(기본: final.md에서 위로 올라가며 knowledge/ 탐색). "
                    "프로필 `마무리 블록`에 `문의헤딩`이 없으면 closing_block_kept는 null(해당 없음)")
    ap.add_argument("--json", action="store_true", help="JSON만 출력")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    for p in (a.final, a.published):
        if not os.path.isfile(p):
            print(f"오류: 파일을 찾을 수 없습니다: {p}", file=sys.stderr)
            return 2
    try:
        res = compare(a.final, a.published, a.knowledge)
    except (ValueError, UnicodeDecodeError) as e:
        print(f"오류: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    print(res["summary"])
    for key, label in (("removed", "삭제된 문단"), ("added", "추가된 문단")):
        for x in res["paragraphs"][key]:
            print(f"- {label}: {x}")
    for x in res["paragraphs"]["changed"]:
        print(f"- 수정({x['ratio']}): {x['before']} → {x['after']}")
    for x in res["headings"]["renamed"]:
        print(f"- 소제목 바뀜: {x['before']} → {x['after']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
