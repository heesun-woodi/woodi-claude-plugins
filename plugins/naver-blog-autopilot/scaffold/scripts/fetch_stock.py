#!/usr/bin/env python3
"""fetch_stock.py — image-plan.md의 stock 슬롯을 Pexels 무료 사진으로 받아 images/NN-<slug>.jpg로 저장한다(표준 라이브러리만).

사용 (작업 폴더에서):
    python3 scripts/fetch_stock.py <글 폴더> [--only NN[,NN]] [--dry-run] [--env PATH]
    예) python3 scripts/fetch_stock.py work/posts/003-chain --dry-run

- 대상: <글 폴더>/images/image-plan.md 표에서 `유형`이 stock인 행. 검색어 = 그 행의 프롬프트 칸(영문 2~4단어).
  검색어가 비어 있으면 그 행 `검수`에 `검색어 없음`을 적고 건너뛴다(보류로 셈).
- 키: PEXELS_API_KEY. 탐색 --env → cwd/.env → image-plan.md 상위 폴더들의 .env → 환경변수. 키 값은 어디에도 출력하지 않는다.
- 호출: GET https://api.pexels.com/v1/search?query=<검색어>&orientation=landscape&per_page=8&locale=ko-KR
  (헤더 Authorization: <키>). photos[] 중 width >= 1600인 첫 사진의 src.large2x(없으면 src.large)를 받는다.
  맞는 사진이 없으면 그 행 `파일`=보류, `검수`=검색 결과 없음으로 두고 다음 행.
- 저장: images/NN-<slug>.jpg(slug = gen_image.slug_for(목적)). `파일` 칸에 이미 .jpg 경로가 있으면 그 이름을 다시 쓴다.
  `파일` 칸을 images/NN-<slug>.jpg로 고치고, 출처 `출처: Pexels/<photographer> <photo.url>`를
  표에 `출처` 열이 있으면 그 칸에, 없으면 `검수` 칸에 적는다. 슬롯마다 image-plan.md를 저장한다.
- --dry-run: 네트워크 접속 없이 행별 `슬롯 · 검색어 · 예상 파일명`만 출력(키가 없어도 된다).
- 401·403(키 거부)·429(한도)·네트워크·5xx는 재시도하지 않고 남은 슬롯을 중단한다(완료분은 저장됨).

출력: 시작 줄 `스톡: pexels · 키: <출처 경로 또는 환경변수>` · 끝 줄 `저장 n장 · 보류 n장`
종료 코드: 0=처리 완료(보류 포함) · 2=키 없음·image-plan 없음·표 파싱 실패·잘못된 인자 · 3=키 거부(401·403) ·
           5=네트워크·5xx · 6=요청 한도(429)
"""
import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_image  # noqa: E402 — parse_plan·rewrite_plan·slug_for·redact 공유(표준 출력 UTF-8 설정도 여기서 된다)

KEY_NAME = "PEXELS_API_KEY"
SEARCH_URL = "https://api.pexels.com/v1/search"
PER_PAGE = 8
MIN_WIDTH = 1600
TIMEOUT = 30
UA = "Mozilla/5.0"
KIND = "stock"
NO_KEY_MSG = "스톡 키 없음 — .env에 PEXELS_API_KEY=…"
KEY_HELP = "PEXELS_API_KEY 발급: https://www.pexels.com/api/ (무료) — 키는 .env에만 적고 채팅에 붙여넣지 마세요"
HELD, NO_RESULT, NO_QUERY = "보류", "검색 결과 없음", "검색어 없음"
EXTRA_COLS = {"review": "검수", "source": "출처"}


class StockError(RuntimeError):
    """재시도하지 않고 남은 슬롯까지 중단하는 오류. code = 종료 코드(3·5·6)."""

    def __init__(self, code, msg, hint=""):
        super().__init__(msg)
        self.code, self.hint = code, hint


def find_pexels_key(plan_path=None, env_override=None):
    """(키, 출처). 순서: --env → cwd/.env → plan 상위 폴더들의 .env → 환경변수. 없으면 (None, None)."""
    cands = [env_override] if env_override else []
    cands.append(os.path.join(os.getcwd(), ".env"))
    if plan_path:
        d = os.path.dirname(os.path.abspath(plan_path))
        while True:
            cands.append(os.path.join(d, ".env"))
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    seen = set()
    for p in cands:
        ap = os.path.abspath(p)
        if ap in seen or not os.path.isfile(ap):
            continue
        seen.add(ap)
        key = gen_image.read_env_values(ap, (KEY_NAME,)).get(KEY_NAME)
        if key:
            return key, p
    key = os.environ.get(KEY_NAME, "").strip()
    return (key, "환경변수") if key else (None, None)


def extend_idx(text, idx):
    """parse_plan의 idx에 `검수`(필수)·`출처`(있으면) 열 위치를 더한다."""
    for line in text.splitlines():
        cells = gen_image.split_row(line)
        if cells and cells[0].startswith(gen_image.COLS["slot"]):
            out = dict(idx)
            for key, name in EXTRA_COLS.items():
                j = next((j for j, c in enumerate(cells) if c.startswith(name)), None)
                if j is not None:
                    out[key] = j
            if "review" not in out:
                raise ValueError("image-plan.md 표 머리에 열이 없습니다: 검수")
            return out
    raise ValueError("image-plan.md에서 '| 슬롯 | …' 표 머리를 찾지 못했습니다.")


def select_stock_rows(rows, only=None):
    stock = [r for r in rows if r["kind"] == KIND]
    if only is None:
        return stock
    known = {r["slot"]: r["kind"] for r in rows}
    bad = sorted(s for s in only if s not in known)
    if bad:
        raise ValueError("표에 없는 슬롯 번호: " + ", ".join(bad))
    notstock = sorted(s for s in only if known[s] != KIND)
    if notstock:
        raise ValueError("stock 슬롯이 아닙니다: " + ", ".join(notstock))
    return [r for r in stock if r["slot"] in only]


def target_name(row):
    f = row["file"].strip("` ")
    if f.lower().endswith((".jpg", ".jpeg")):
        return os.path.basename(f)
    return f"{row['slot']}-{gen_image.slug_for(row['purpose'])}.jpg"


def clean_cell(value):
    return " ".join(str(value).replace("|", "/").split())


def rewrite_cells(text, idx, line_no, cells):
    """cells: {col_key: 값}. 해당 행(line_no)의 그 칸들만 바꾼다(gen_image.rewrite_plan과 같은 형식)."""
    lines = text.splitlines()
    row = gen_image.split_row(lines[line_no])
    for key, value in cells.items():
        j = idx[key]
        while len(row) <= j:
            row.append("")
        row[j] = clean_cell(value)
    lines[line_no] = "|" + "|".join(f" {c} " if c else " " for c in row) + "|"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def search_url(query):
    return SEARCH_URL + "?" + urllib.parse.urlencode(
        {"query": query, "orientation": "landscape", "per_page": PER_PAGE, "locale": "ko-KR"})


def _http(req, what):
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise StockError(3, f"Pexels {e.code}: 스톡 키가 거부되었습니다 — PEXELS_API_KEY를 확인하세요", KEY_HELP) from None
        if e.code == 429:
            raise StockError(6, "Pexels 429: 요청 한도 초과 — 재시도하지 않고 중단합니다",
                             "한도가 풀린 뒤 --only로 남은 슬롯만 다시 받으세요") from None
        raise StockError(5, f"Pexels HTTP {e.code}({what})", "잠시 뒤 다시 실행하세요") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise StockError(5, f"네트워크 오류({what}) — {getattr(e, 'reason', e)}", "인터넷 연결을 확인하세요") from None


def search(key, query):
    req = urllib.request.Request(search_url(query), headers={"Authorization": key, "User-Agent": UA})
    body = _http(req, "검색")
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        raise StockError(5, "Pexels 응답을 읽을 수 없습니다(JSON 아님)", "잠시 뒤 다시 실행하세요") from None
    return data if isinstance(data, dict) else {}


def pick_photo(data):
    """(photo, 받을 URL) 또는 (None, None). width >= MIN_WIDTH인 첫 사진의 src.large2x → src.large."""
    for p in data.get("photos") or []:
        if not isinstance(p, dict):
            continue
        try:
            width = int(p.get("width") or 0)
        except (TypeError, ValueError):
            continue
        src = p.get("src") if isinstance(p.get("src"), dict) else {}
        url = src.get("large2x") or src.get("large")
        if width >= MIN_WIDTH and url:
            return p, url
    return None, None


def download(url):
    return _http(urllib.request.Request(url, headers={"User-Agent": UA}), "사진 받기")


def write_bytes_atomic(path, data):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".stock-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def start_line(source, key):
    return gen_image.redact(f"스톡: pexels · 키: {source or '없음'}", key)


def end_line(saved, held):
    return f"저장 {saved}장 · 보류 {held}장"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="image-plan.md의 stock 슬롯을 Pexels 무료 사진으로 받아 images/NN-<slug>.jpg로 저장하고 `파일`·출처 칸을 갱신합니다.",
        epilog="종료 코드: 0=처리 완료(보류 포함), 2=키 없음·image-plan 없음·표 파싱 실패, 3=키 거부(401·403), "
               "5=네트워크·5xx, 6=요청 한도(429).")
    ap.add_argument("post", metavar="글_폴더", help="글 폴더(예: work/posts/003-chain) — 그 안의 images/image-plan.md를 읽는다")
    ap.add_argument("--only", metavar="NN[,NN]", help="이 슬롯 번호만 받기(쉼표 구분)")
    ap.add_argument("--dry-run", action="store_true", help="네트워크 접속 없이 슬롯 · 검색어 · 예상 파일명만 출력")
    ap.add_argument("--env", metavar="PATH", help="PEXELS_API_KEY가 든 .env 경로를 직접 지정")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2

    images_dir = os.path.join(a.post, "images")
    plan = os.path.join(images_dir, "image-plan.md")
    if not os.path.isfile(plan):
        print(f"오류: image-plan.md가 없습니다: {plan}", file=sys.stderr)
        return 2
    if a.env and not os.path.isfile(a.env):
        print(f"{NO_KEY_MSG} (--env 파일을 찾을 수 없습니다: {a.env})", file=sys.stderr)
        return 2
    with open(plan, encoding="utf-8") as f:
        text = f.read()
    try:
        idx, rows = gen_image.parse_plan(text)
        idx = extend_idx(text, idx)
        targets = select_stock_rows(rows, gen_image.parse_only(a.only))
    except ValueError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 2

    key, source = find_pexels_key(plan, a.env)
    if a.dry_run:
        print(start_line(source, key))
        for r in targets:
            q = r["prompt"].strip()
            print(f"{r['slot']} · {q or '(검색어 없음)'} · " + (f"images/{target_name(r)}" if q else "건너뜀"))
        print(f"(dry-run) 네트워크 접속 없음 · 대상 {len(targets)}장")
        return 0
    if not targets:
        print("stock 슬롯이 없습니다.")
        print(end_line(0, 0))
        return 0
    if not key:
        print(NO_KEY_MSG, file=sys.stderr)
        print(KEY_HELP, file=sys.stderr)
        return 2

    print(start_line(source, key))
    cur, saved, held, code = text, 0, 0, 0

    def apply(new_text):
        nonlocal cur
        cur = new_text
        gen_image.write_plan_atomic(plan, cur)

    for i, r in enumerate(targets):
        q = r["prompt"].strip()
        if not q:
            apply(rewrite_cells(cur, idx, r["line"], {"review": NO_QUERY}))
            held += 1
            print(f"[보류] {r['slot']} {NO_QUERY}")
            continue
        try:
            photo, url = pick_photo(search(key, q))
            if photo is None:
                apply(rewrite_cells(cur, idx, r["line"], {"file": HELD, "review": NO_RESULT}))
                held += 1
                print(f"[보류] {r['slot']} {NO_RESULT} ({q})")
                continue
            data = download(url)
        except StockError as e:
            rest = [t["slot"] for t in targets[i:]]
            print(gen_image.redact(f"[FAIL] {r['slot']} {e}\n중단: 남은 슬롯 {', '.join(rest)}은 받지 않았습니다.\n{e.hint}",
                                   key), file=sys.stderr)
            code = e.code
            break
        name = target_name(r)
        os.makedirs(images_dir, exist_ok=True)
        write_bytes_atomic(os.path.join(images_dir, name), data)
        rel = f"images/{name}"
        credit = f"출처: Pexels/{clean_cell(photo.get('photographer') or '알 수 없음')} {clean_cell(photo.get('url') or '')}".rstrip()
        new = gen_image.rewrite_plan(cur, idx, {r["line"]: rel})
        apply(rewrite_cells(new, idx, r["line"], {"source" if "source" in idx else "review": credit}))
        saved += 1
        print(gen_image.redact(f"[OK] {r['slot']} → {rel} ({credit})", key))
    print(end_line(saved, held))
    return code


if __name__ == "__main__":
    sys.exit(main())
