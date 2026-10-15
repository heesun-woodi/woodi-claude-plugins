#!/usr/bin/env python3
"""콘텐츠 피드백 기록 work/feedback-log.md 관리 (표준 라이브러리만 사용).

사용 예(작업 폴더에서):
  python3 scripts/feedback_log.py add --post 002-<slug> --stage 게이트2 --category 톤 --scope "앞으로 계속" --text "<원문>"
      → 새 id(F-0001 …)를 한 줄로 출력
  python3 scripts/feedback_log.py pending            → 처리=대기 행을 JSON 배열로(없으면 [])
  python3 scripts/feedback_log.py mark F-0003 L-005
  python3 scripts/feedback_log.py mark F-0004 "반영 안 함: 이번 글 한정"
  python3 scripts/feedback_log.py list [--post 002] [--json]

표(8열): | id | 일시 | 글 | 단계 | 범주 | 적용 범위 | 요청 원문 | 처리 |
  단계 ∈ 게이트1·게이트2·게이트3·발행후·직접, 범주 ∈ 제목·톤·구조·분량·내용·사실·이미지·표지·주제·SEO·기타,
  적용 범위 ∈ 이번 글만·앞으로 계속, 처리 ∈ 대기·L-NNN·반영 안 함: <사유>.
  칸 안의 백슬래시·`|`·`<`는 앞에 백슬래시를 붙여, 줄바꿈은 `<br>`로 바꿔 저장하고, pending·list --json은 원문으로 되돌려 낸다.
  손으로 고치다 원문에 이스케이프 안 된 `|`가 들어가 칸이 9개 이상이면 7번째~끝에서 두 번째 칸을 원문으로 합치고 마지막 칸을 처리로 읽는다.
id는 머리 주석 `<!-- next-id: N -->`(다음에 쓸 번호)와 표의 가장 큰 번호+1 중 큰 값으로 매겨, 행을 지워도 번호를 다시 쓰지 않는다.
같은 id 행이 둘 이상이면 stderr에 줄 번호와 함께 경고한다(mark는 그 id면 exit 2 — 사람이 고칠 것).
파일이 없으면 머리를 만들어 생성한다. 저장은 임시 파일 + os.replace.
종료 코드: 0=성공, 1=없는 id, 2=사용 오류(잘못된 단계·범주·범위·처리 값, 빈 원문, 중복 id mark).
"""
import argparse
import datetime
import json
import os
import re
import sys
import tempfile
for _s in (sys.stdout, sys.stderr):  # Windows 콘솔(cp949)에서도 한글 출력이 죽지 않게
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_FILE = os.path.join("work", "feedback-log.md")
COLS = ["id", "일시", "글", "단계", "범주", "적용 범위", "요청 원문", "처리"]
STAGES = ["게이트1", "게이트2", "게이트3", "발행후", "직접"]
CATEGORIES = ["제목", "톤", "구조", "분량", "내용", "사실", "이미지", "표지", "주제", "SEO", "기타"]
SCOPES = ["이번 글만", "앞으로 계속"]
HEADER = ("# 피드백 기록\n"
          "<!-- 정본: 작업 폴더 work/feedback-log.md. scripts/feedback_log.py가 행을 더하고(add) 처리 칸을 바꾼다(mark).\n"
          "     blog-learn 스킬이 처리=대기 행을 knowledge/learned-preferences.md 규칙으로 정리한다. 직접 고쳐도 되지만 8열 표 형식을 유지한다. -->\n"
          "<!-- next-id: 1 -->\n\n"
          "| " + " | ".join(COLS) + " |\n"
          "|" + "---|" * len(COLS) + "\n")
ID_RE = re.compile(r"^F-(\d+)$")
NEXT_RE = re.compile(r"<!--\s*next-id:\s*(\d+)\s*-->")
MARK_RE = re.compile(r"^(대기|L-\d{3,}|반영 안 함:\s*\S.*)$")


class UsageError(Exception):
    pass


def esc(text):
    """칸 값 안전화: \\ → \\\\, | → \\|, < → \\<, 줄바꿈 → <br>."""
    t = str(text).replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\\", "\\\\").replace("|", "\\|").replace("<", "\\<")
    return t.replace("\n", "<br>").strip()


def unesc(cell):
    """esc의 역. 이스케이프 안 된 `<br>`만 줄바꿈(예전에 `<`를 이스케이프하지 않고 저장한 행도 그대로 읽힌다)."""
    out, i = [], 0
    while i < len(cell):
        if cell[i] == "\\" and i + 1 < len(cell) and cell[i + 1] in "\\|<":
            out.append(cell[i + 1])
            i += 2
        elif cell.startswith("<br>", i):
            out.append("\n")
            i += 4
        else:
            out.append(cell[i])
            i += 1
    return "".join(out)


def split_row(line):
    """`| a | b\\|c |` → ['a', 'b\\|c'] (이스케이프된 | 는 칸을 나누지 않음, 값은 이스케이프 상태 그대로)."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    cells, cur, i = [], [], 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            cur.append(s[i:i + 2])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    tail = "".join(cur).strip()
    if tail:
        cells.append(tail)
    return cells


def canon(value, allowed, what):
    """공백 무시로 허용값과 맞추고 정식 표기로 돌려준다(예: '게이트 2' → '게이트2')."""
    key = re.sub(r"\s+", "", value or "")
    for a in allowed:
        if re.sub(r"\s+", "", a) == key:
            return a
    raise UsageError(f"{what} 값이 잘못됐습니다: {value!r} (가능: {', '.join(allowed)})")


def save(path, lines):
    """임시 파일에 쓴 뒤 os.replace(중간에 죽어도 원본이 반쯤 쓰이지 않게)."""
    text = "\n".join(lines).rstrip("\n") + "\n"
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), prefix=".feedback-log.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def load(path):
    if not os.path.isfile(path):
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        save(path, HEADER.split("\n"))
    with open(path, encoding="utf-8") as f:
        return f.read().lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def rows(lines):
    """(줄 번호, 칸 8개(이스케이프 상태)) — id가 F-숫자인 행만. 칸이 9개 이상이면 원문 칸으로 합친다."""
    out = []
    for n, ln in enumerate(lines):
        if ln.lstrip().startswith("|"):
            cells = split_row(ln)
            if not cells or not ID_RE.match(cells[0]):
                continue
            if len(cells) > len(COLS):
                cells = cells[:6] + ["\\|".join(cells[6:-1]), cells[-1]]
            out.append((n, (cells + [""] * len(COLS))[:len(COLS)]))
    return out


def warn_dups(path, rs):
    """같은 id 행이 둘 이상이면 stderr 경고. {id: [줄 번호(1부터)…]}를 돌려준다."""
    seen = {}
    for n, c in rs:
        seen.setdefault(c[0], []).append(n + 1)
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    for fid, ns in sorted(dups.items()):
        print(f"경고: {path}에 {fid} 행이 {len(ns)}개 있습니다(줄 {', '.join(map(str, ns))}) — 하나만 남기고 고치세요",
              file=sys.stderr)
    return dups


def as_dict(cells):
    return {k: unesc(v) for k, v in zip(COLS, cells)}


def fmt_row(cells):
    return "| " + " | ".join(cells) + " |"


def cmd_add(path, a):
    stage = canon(a.stage, STAGES, "단계")
    cat = canon(a.category, CATEGORIES, "범주")
    scope = canon(a.scope, SCOPES, "적용 범위")
    text = esc(a.text or "")
    post = esc(a.post or "")
    if not text:
        raise UsageError("요청 원문(--text)이 비어 있습니다")
    if not post:
        raise UsageError("글(--post)이 비어 있습니다")
    lines = load(path)
    rs = rows(lines)
    warn_dups(path, rs)
    k = next((i for i, ln in enumerate(lines) if NEXT_RE.search(ln)), None)
    nxt = max(max((int(ID_RE.match(c[0]).group(1)) for _, c in rs), default=0) + 1,
              int(NEXT_RE.search(lines[k]).group(1)) if k is not None else 0)
    fid = f"F-{nxt:04d}"
    when = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    new = fmt_row([fid, when, post, stage, cat, scope, text, "대기"])
    hdr = next((n for n, ln in enumerate(lines) if ln.lstrip().startswith("|")
                and split_row(ln)[:1] == ["id"]), None)
    if hdr is None:  # 표 머리가 지워졌으면 끝에 다시 만든다
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", fmt_row(COLS), "|" + "---|" * len(COLS)]
        hdr = len(lines) - 2
    end = hdr
    while end + 1 < len(lines) and lines[end + 1].lstrip().startswith("|"):
        end += 1
    lines.insert(end + 1, new)
    stamp = f"<!-- next-id: {nxt + 1} -->"
    if k is not None:
        lines[k] = NEXT_RE.sub(stamp, lines[k], count=1)
    else:  # 주석이 없던 예전 파일 — 첫 줄(제목) 아래, 제목이 없으면 맨 위에 넣는다
        lines.insert(1 if lines and lines[0].startswith("# ") else 0, stamp)
    save(path, lines)
    print(fid)


def cmd_pending(path, a):
    rs = rows(load(path))
    warn_dups(path, rs)
    out = [as_dict(c) for _, c in rs if unesc(c[7]).strip() == "대기"]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_mark(path, a):
    value = re.sub(r"\s+", " ", a.value.replace("\r", " ").replace("\n", " ")).strip()
    if not MARK_RE.match(value):
        raise UsageError(f"처리 값이 잘못됐습니다: {a.value!r} (가능: 대기 · L-NNN · '반영 안 함: <사유>')")
    if not ID_RE.match(a.id):
        raise UsageError(f"id 형식이 잘못됐습니다: {a.id!r} (예: F-0003)")
    lines = load(path)
    rs = rows(lines)
    dups = warn_dups(path, rs)
    if a.id in dups:
        raise UsageError(f"{a.id} 행이 여러 개라 어느 행을 바꿀지 모릅니다(줄 {', '.join(map(str, dups[a.id]))}) — "
                         "파일에서 하나만 남긴 뒤 다시 실행하세요")
    for n, cells in rs:
        if cells[0] == a.id:
            cells[7] = esc(value)
            lines[n] = fmt_row(cells)
            save(path, lines)
            print(f"{a.id} → {value}")
            return 0
    print(f"오류: {a.id} 행이 없습니다 ({path})", file=sys.stderr)
    return 1


def cmd_list(path, a):
    rs = rows(load(path))
    warn_dups(path, rs)
    sel = [c for _, c in rs if not a.post or unesc(c[2]).startswith(a.post)]
    if a.json:
        print(json.dumps([as_dict(c) for c in sel], ensure_ascii=False, indent=2))
        return
    print(fmt_row(COLS))
    print("|" + "---|" * len(COLS))
    for c in sel:
        print(fmt_row(c))
    print(f"({len(sel)}건)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="콘텐츠 피드백 기록(work/feedback-log.md)을 더하고·읽고·처리 표시한다.",
                                 epilog="종료 코드: 0=성공, 1=없는 id, 2=사용 오류")
    ap.add_argument("--file", default=DEFAULT_FILE, help=f"기록 파일(기본: {DEFAULT_FILE}, 작업 폴더 기준)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add", help="피드백 한 건 추가 → id 출력")
    p.add_argument("--post", required=True, help="글 폴더 이름(NNN-slug)")
    p.add_argument("--stage", required=True, help=" · ".join(STAGES))
    p.add_argument("--category", required=True, help=" · ".join(CATEGORIES))
    p.add_argument("--scope", required=True, help=" · ".join(SCOPES))
    p.add_argument("--text", required=True, help="요청 원문(그대로)")
    sub.add_parser("pending", help="처리=대기 행을 JSON 배열로")
    p = sub.add_parser("mark", help="처리 칸 바꾸기")
    p.add_argument("id", help="F-NNNN")
    p.add_argument("value", help="L-NNN · '반영 안 함: <사유>' · 대기")
    p = sub.add_parser("list", help="행 보기")
    p.add_argument("--post", help="글 번호·이름 앞부분(예: 002)")
    p.add_argument("--json", action="store_true", help="JSON 배열로")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    try:
        if a.cmd == "add":
            return cmd_add(a.file, a) or 0
        if a.cmd == "pending":
            return cmd_pending(a.file, a) or 0
        if a.cmd == "mark":
            return cmd_mark(a.file, a)
        return cmd_list(a.file, a) or 0
    except UsageError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print(f"오류: UTF-8로 읽을 수 없는 파일입니다: {a.file}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
