#!/usr/bin/env python3
"""fetch_stock.py — image-plan.md의 stock 슬롯을 무료 스톡 사진(기본 Openverse, 키 불필요 / 선택 Pexels)으로 받아 images/NN-<slug>.jpg|png로 저장한다(표준 라이브러리만).

사용 (작업 폴더에서):
    python3 scripts/fetch_stock.py <글 폴더> [--only NN[,NN]] [--dry-run] [--env PATH]
    예) python3 scripts/fetch_stock.py work/posts/003-chain --dry-run

- 대상: <글 폴더>/images/image-plan.md 표에서 `유형`이 stock인 행. 검색어 = 그 행의 프롬프트 칸(영문 2~3단어).
  검색어가 비어 있으면 그 행 `검수`에 `검색어 없음`을 적고 건너뛴다(보류로 셈).
- 제공자(1.1.2): .env의 STOCK_PROVIDER(openverse|pexels) → 없고 PEXELS_API_KEY가 있으면 pexels → 둘 다 없으면 openverse.
  STOCK_PROVIDER 값 오류 · pexels인데 키 없음 → 종료 2(다른 제공자로 넘어가지 않음). `resolve_stock_provider(env)`가 결정한다.
- 키(pexels만): PEXELS_API_KEY. 탐색 --env → cwd/.env → image-plan.md 상위 폴더들의 .env → 환경변수(STOCK_PROVIDER도 같은 곳). 키 값은 어디에도 출력하지 않는다.
- Openverse 호출: GET https://api.openverse.org/v1/images/?q=<검색어>&license=cc0,pdm&aspect_ratio=wide&mature=false&page_size=20
  (헤더 User-Agent: naver-blog-autopilot/<버전> (+https://github.com/heesun-woodi/woodi-claude-plugins), 키 없음).
  results[]에서 url이 있고 원본 width>=1200이고 같은 작업 폴더의 다른 글 image-plan 출처 칸에 foreign_landing_url이 없는 첫 결과를 받는다.
  결과의 filetype이 있으면 jpg·jpeg·png만 후보. 슬롯당 사진 받기는 최대 5번(1차 검색과 폴백 재검색을 합친 횟수, 이미 시도한 URL은 다시 받지 않음).
  받을 때 응답 Content-Type이 image/jpeg·image/png면 통과, 다른 형식(image/tiff·text/html 등)이거나 Content-Length가 8,000,000바이트 초과면 본문을 읽지 않고 건너뜀
  (받기 1번으로 셈). 헤더가 없거나 application/octet-stream·binary/octet-stream·image/jpg·image/pjpeg면 본문을 받은 뒤(상한 8,000,000바이트, 길이 헤더가 없으면
  청크로 읽다 초과 즉시 중단) 앞부분 매직 바이트(JPEG FFD8FF · PNG 89504E47)로 판정. Content-Length가 있는데 받은 합계와 다르면(잘린 본문) 받기 오류.
  받은 파일의 실제 가로(JPEG SOF / PNG IHDR)가 800px 미만이거나 JPEG·PNG가 아니면 버리고 다음 결과.
  사진 받기 단계의 오류(403·404·429·5xx·네트워크·잘린 본문·읽기 예외)는 그 후보만 건너뜀. 시도한 받기가 모두 오류면 `보류`·`사진 받기 실패`, 그 외 `검색 결과 없음`.
  결과가 없고 검색어가 3단어 이상이면 마지막 단어를 뺀 검색어로 1회 재검색(슬롯 줄 끝 ` (검색어 줄임: <새 검색어>)`, plan 검색어 칸은 그대로). 1차에서 5번을 다 썼으면 재검색 없음.
  저장 images/NN-<slug>.jpg 또는 .png · 출처 `출처: Openverse/<source> · <creator 또는 작자 미상> · <LICENSE> <foreign_landing_url>`.
- Pexels 경로(1.1.0과 같음):
- 호출: GET https://api.pexels.com/v1/search?query=<검색어>&orientation=landscape&per_page=8&locale=ko-KR
  (헤더 Authorization: <키>). photos[] 중 width >= 1600인 첫 사진의 src.large2x(없으면 src.large)를 받는다.
  맞는 사진이 없으면 그 행 `파일`=보류, `검수`=검색 결과 없음으로 두고 다음 행.
- 저장: images/NN-<slug>.jpg(slug = gen_image.slug_for(목적)). `파일` 칸에 이미 .jpg 경로가 있으면 그 이름을 다시 쓴다.
  `파일` 칸을 images/NN-<slug>.jpg로 고치고, 출처 `출처: Pexels/<photographer> <photo.url>`를
  표에 `출처` 열이 있으면 그 칸에, 없으면 `검수` 칸에 적는다. 슬롯마다 image-plan.md를 저장한다.
- --dry-run: 네트워크 접속 없이 행별 `슬롯 · 검색어 · 예상 파일명`만 출력(키가 없어도 된다).
- 401·403(키 거부)·429(한도)·네트워크·5xx는 재시도하지 않고 남은 슬롯을 중단한다(완료분은 저장됨).

출력: 시작 줄 `스톡: openverse · 키: 필요 없음` 또는 `스톡: pexels · 키: <출처 경로 또는 환경변수>` · 끝 줄 `저장 n장 · 보류 n장`
종료 코드: 0=처리 완료(보류 포함) · 2=STOCK_PROVIDER 값 오류·pexels인데 키 없음·image-plan 없음·표 파싱 실패·잘못된 인자 ·
           3=거부(401·403) · 5=네트워크·5xx·JSON 아님 · 6=요청 한도(429)
"""
import argparse
import glob
import http.client
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_image  # noqa: E402 — parse_plan·rewrite_plan·slug_for·redact 공유(표준 출력 UTF-8 설정도 여기서 된다)

KEY_NAME = "PEXELS_API_KEY"
PROVIDER_NAME = "STOCK_PROVIDER"
PROVIDERS = ("openverse", "pexels")
PLUGIN_VERSION = "1.1.2"  # plugin.json이 스크립트 옆에 없을 때(작업 폴더에 복사된 경우)의 값
OPENVERSE_URL = "https://api.openverse.org/v1/images/"
OPENVERSE_QUERY = "&license=cc0,pdm&aspect_ratio=wide&mature=false&page_size=20"
OV_MIN_WIDTH = 1200  # Openverse 원본 가로 하한
OV_MIN_FILE_WIDTH = 800  # 받은 파일의 실제 가로 하한
OV_MAX_DOWNLOADS = 5  # 슬롯당 사진 받기 최대 횟수(1차 검색과 폴백 재검색 합계)
OV_MAX_BYTES = 8_000_000  # 받을 파일 크기 상한
OV_TYPES = ("image/jpeg", "image/png")
OV_AMBIGUOUS = ("", "application/octet-stream", "binary/octet-stream", "image/jpg", "image/pjpeg")  # 헤더로는 판정 못 함 → 매직 바이트
OV_FILETYPES = ("jpg", "jpeg", "png")
REPO_URL = "https://github.com/heesun-woodi/woodi-claude-plugins"
SEARCH_URL = "https://api.pexels.com/v1/search"
PER_PAGE = 8
MIN_WIDTH = 1600
TIMEOUT = 30
UA = "Mozilla/5.0"
KIND = "stock"
NO_KEY_MSG = "스톡 키 없음 — .env에 PEXELS_API_KEY=…"
NO_PEXELS_KEY_MSG = "Pexels 키가 없습니다 — .env의 STOCK_PROVIDER를 openverse로 고치거나 그 줄을 지우면 키 없이 무료 스톡을 씁니다"
KEY_HELP = "PEXELS_API_KEY 발급: https://www.pexels.com/api/ (무료) — 키는 .env에만 적고 채팅에 붙여넣지 마세요"
HELD, NO_RESULT, NO_QUERY = "보류", "검색 결과 없음", "검색어 없음"
DL_FAILED = "사진 받기 실패"
EXTRA_COLS = {"review": "검수", "source": "출처"}


class ConfigError(ValueError):
    """제공자 결정 오류. kind = "invalid"(STOCK_PROVIDER 값 오류) | "nokey"(pexels인데 키 없음)."""

    def __init__(self, kind, msg):
        super().__init__(msg)
        self.kind = kind


class StockError(RuntimeError):
    """재시도하지 않고 남은 슬롯까지 중단하는 오류. code = 종료 코드(3·5·6)."""

    def __init__(self, code, msg, hint=""):
        super().__init__(msg)
        self.code, self.hint = code, hint


def env_candidates(plan_path=None, env_override=None):
    """.env 후보 경로(중복 없이, 존재하는 파일만). 순서: --env → cwd/.env → plan 상위 폴더들의 .env."""
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
    out, seen = [], set()
    for p in cands:
        ap = os.path.abspath(p)
        if ap in seen or not os.path.isfile(ap):
            continue
        seen.add(ap)
        out.append(p)
    return out


def find_stock_env(plan_path=None, env_override=None):
    """{"STOCK_PROVIDER": 값|None, "PEXELS_API_KEY": 값|None, "key_source": 경로|"환경변수"|None}.
    항목마다 --env → cwd/.env → plan 상위 .env → 환경변수 중 처음 값이 있는 곳. 값은 출력하지 않는다."""
    files = env_candidates(plan_path, env_override)
    out = {PROVIDER_NAME: None, KEY_NAME: None, "key_source": None}
    for p in files:
        vals = gen_image.read_env_values(p, (PROVIDER_NAME, KEY_NAME))
        if out[PROVIDER_NAME] is None and vals.get(PROVIDER_NAME):
            out[PROVIDER_NAME] = vals[PROVIDER_NAME]
        if out[KEY_NAME] is None and vals.get(KEY_NAME):
            out[KEY_NAME], out["key_source"] = vals[KEY_NAME], p
    if out[PROVIDER_NAME] is None:
        v = os.environ.get(PROVIDER_NAME, "").strip()
        out[PROVIDER_NAME] = v or None
    if out[KEY_NAME] is None:
        v = os.environ.get(KEY_NAME, "").strip()
        if v:
            out[KEY_NAME], out["key_source"] = v, "환경변수"
    return out


def resolve_stock_provider(env):
    """(provider, key, source). env = find_stock_env() 결과(또는 같은 모양의 dict).
    STOCK_PROVIDER가 있으면 그 값 → 없고 PEXELS_API_KEY가 있으면 pexels → 둘 다 없으면 openverse.
    값이 openverse/pexels가 아니면 ConfigError("invalid"), pexels인데 키가 없으면 ConfigError("nokey").
    openverse는 (openverse, None, None). 오류 문구에 설정 값은 넣지 않는다."""
    raw = env.get(PROVIDER_NAME)
    key, source = env.get(KEY_NAME) or None, env.get("key_source")
    if raw:
        provider = str(raw).strip().lower()
        if provider not in PROVIDERS:
            raise ConfigError("invalid", "STOCK_PROVIDER 값이 올바르지 않습니다 — openverse 또는 pexels 중 하나여야 합니다(값은 출력하지 않음)")
    else:
        provider = "pexels" if key else "openverse"
    if provider == "pexels":
        if not key:
            raise ConfigError("nokey", NO_PEXELS_KEY_MSG)
        return "pexels", key, source
    return "openverse", None, None


def find_pexels_key(plan_path=None, env_override=None):
    """(키, 출처). 순서: --env → cwd/.env → plan 상위 폴더들의 .env → 환경변수. 없으면 (None, None)."""
    env = find_stock_env(plan_path, env_override)
    return (env[KEY_NAME], env["key_source"]) if env[KEY_NAME] else (None, None)


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


def target_name(row, ext=None):
    """저장 파일명. ext(".jpg"|".png")가 없으면 .jpg(Pexels). ext가 있으면 `파일` 칸의 이름 줄기(stem)를 재사용한다."""
    f = os.path.basename(row["file"].strip("` "))
    if ext is None:
        if f.lower().endswith((".jpg", ".jpeg")):
            return f
        return f"{row['slot']}-{gen_image.slug_for(row['purpose'])}.jpg"
    if f.lower().endswith((".jpg", ".jpeg", ".png")):
        return os.path.splitext(f)[0] + ext
    return f"{row['slot']}-{gen_image.slug_for(row['purpose'])}{ext}"


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


def _http(req, what, label="Pexels"):
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            if label == "Pexels":
                raise StockError(3, f"Pexels {e.code}: 스톡 키가 거부되었습니다 — PEXELS_API_KEY를 확인하세요", KEY_HELP) from None
            raise StockError(3, f"{label} {e.code}: 요청이 거부되었습니다({what})",
                             "잠시 뒤 다시 실행하거나 STOCK_PROVIDER를 확인하세요") from None
        if e.code == 429:
            raise StockError(6, f"{label} 429: 요청 한도 초과 — 재시도하지 않고 중단합니다",
                             "한도가 풀린 뒤 --only로 남은 슬롯만 다시 받으세요") from None
        raise StockError(5, f"{label} HTTP {e.code}({what})", "잠시 뒤 다시 실행하세요") from None
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


def plugin_version():
    """plugin.json(스크립트 위치 기준 ../../.claude-plugin/plugin.json)의 version. 없으면 PLUGIN_VERSION."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude-plugin", "plugin.json")
    try:
        with open(path, encoding="utf-8") as f:
            v = json.load(f).get("version")
        if isinstance(v, str) and re.fullmatch(r"[0-9A-Za-z.+-]{1,32}", v):
            return v
    except (OSError, ValueError, AttributeError):
        pass
    return PLUGIN_VERSION


def openverse_ua():
    return f"naver-blog-autopilot/{plugin_version()} (+{REPO_URL})"


def openverse_url(query):
    return OPENVERSE_URL + "?q=" + urllib.parse.quote(query, safe="") + OPENVERSE_QUERY


def openverse_search(query):
    req = urllib.request.Request(openverse_url(query), headers={"User-Agent": openverse_ua(), "Accept": "application/json"})
    body = _http(req, "검색", "Openverse")
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        raise StockError(5, "Openverse 응답을 읽을 수 없습니다(JSON 아님)", "잠시 뒤 다시 실행하세요") from None
    return data if isinstance(data, dict) else {}


def openverse_download(url):
    """bytes, 또는 건너뛸 후보면 None(Content-Type이 다른 형식 · 크기 OV_MAX_BYTES 초과 · 매직 바이트 불일치).
    jpeg/png 헤더면 통과, 헤더가 없거나 OV_AMBIGUOUS면 받은 뒤 매직 바이트(JPEG FFD8FF · PNG 89504E47)로 판정.
    헤더만 보고 거르면 본문은 읽지 않는다. Content-Length가 숫자인데 받은 합계와 다르면 IncompleteRead.
    오류는 urllib/http.client 예외 그대로(호출부가 후보만 건너뜀)."""
    req = urllib.request.Request(url, headers={"User-Agent": openverse_ua()})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype not in OV_TYPES and ctype not in OV_AMBIGUOUS:
            return None
        length = None
        raw = resp.headers.get("Content-Length")
        try:
            length = int(raw) if raw is not None else None
        except ValueError:
            length = None
        if length is not None and length > OV_MAX_BYTES:
            return None
        chunks, total = [], 0
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > OV_MAX_BYTES:
                return None
            chunks.append(chunk)
        # chunked 응답이면 Content-Length는 무시한다(RFC 9112 §6.3) — 끊긴 chunked는 read가 IncompleteRead를 낸다
        if length is not None and not getattr(resp, "chunked", False) and total != length:
            raise http.client.IncompleteRead(b"".join(chunks)[:0], length - total)
        body = b"".join(chunks)
        if ctype not in OV_TYPES and not (body[:3] == b"\xff\xd8\xff" or body[:4] == b"\x89PNG"):
            return None
        return body


def image_info(data):
    """(확장자, 가로) 또는 None. JPEG는 SOF 마커, PNG는 IHDR을 읽는다. JPEG·PNG가 아니거나 헤더가 깨졌으면 None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        if len(data) >= 24 and data[12:16] == b"IHDR":
            return ".png", int.from_bytes(data[16:20], "big")
        return None
    if data[:2] != b"\xff\xd8":
        return None
    i, n = 2, len(data)
    while i + 4 <= n:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker == 0xFF:  # 채움 바이트
            i += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:  # 길이 없는 마커
            i += 2
            continue
        if marker == 0xD9:
            return None
        seglen = int.from_bytes(data[i + 2:i + 4], "big")
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            if i + 9 > n:
                return None
            return ".jpg", int.from_bytes(data[i + 7:i + 9], "big")
        if seglen < 2:
            return None
        i += 2 + seglen
    return None


URL_RE = re.compile(r"https?://[^\s|]+")


def landing_urls(text):
    return set(URL_RE.findall(text))


def used_landing_urls(plan_path):
    """같은 작업 폴더(글 폴더들의 부모)의 다른 글 image-plan.md에 적힌 URL 모음. 이 글 자신의 plan은 제외."""
    posts_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(plan_path))))
    own = os.path.abspath(plan_path)
    urls = set()
    for p in glob.glob(os.path.join(glob.escape(posts_dir), "*", "images", "image-plan.md")):
        if os.path.abspath(p) == own:
            continue
        try:
            with open(p, encoding="utf-8") as f:
                urls |= landing_urls(f.read())
        except OSError:
            continue
    return urls


def openverse_candidates(data, used):
    """조건에 맞는 results[]를 순서대로: url 있음 · 원본 width >= OV_MIN_WIDTH · foreign_landing_url이 used에 없음."""
    for r in data.get("results") or []:
        if not isinstance(r, dict):
            continue
        url = r.get("url")
        if not isinstance(url, str) or not url.strip():
            continue
        ft = r.get("filetype")
        if isinstance(ft, str) and ft.strip() and ft.strip().lower().lstrip(".") not in OV_FILETYPES:
            continue
        try:
            width = int(r.get("width") or 0)
        except (TypeError, ValueError):
            continue
        if width < OV_MIN_WIDTH:
            continue
        landing = r.get("foreign_landing_url")
        landing = landing.strip() if isinstance(landing, str) else ""
        if landing and landing in used:
            continue
        yield r, url.strip(), landing


def openverse_credit(r, landing):
    source = clean_cell(r.get("source") or r.get("provider") or "알 수 없음")
    creator = clean_cell(r.get("creator") or "") or "작자 미상"
    lic = clean_cell(r.get("license") or "").upper() or "알 수 없음"
    return f"출처: Openverse/{source} · {creator} · {lic} {clean_cell(landing)}".rstrip()


class DlState:
    """슬롯 단위 받기 예산. 1차 검색과 폴백 재검색이 합쳐서 OV_MAX_DOWNLOADS번, 시도한 URL은 다시 받지 않는다."""

    def __init__(self):
        self.tries = self.errors = 0
        self.tried = set()

    @property
    def left(self):
        return OV_MAX_DOWNLOADS - self.tries

    @property
    def all_errors(self):
        return self.tries > 0 and self.errors == self.tries


def pick_openverse(data, used, state):
    """(ext, bytes, credit, landing) 또는 None. 받은 파일이 JPEG·PNG가 아니거나 가로 < 800, 또는 헤더로 걸러지면 다음 결과.
    사진 받기 단계의 오류(403·404·429·5xx·네트워크)는 그 후보만 건너뛴다."""
    for r, url, landing in openverse_candidates(data, used):
        if state.left <= 0:
            break
        if url in state.tried:
            continue
        state.tried.add(url)
        state.tries += 1
        try:
            body = openverse_download(url)
        except (StockError, OSError, TimeoutError, http.client.HTTPException, ValueError):  # HTTPError·URLError는 OSError, IncompleteRead는 HTTPException
            state.errors += 1
            continue
        if body is None:
            continue
        info = image_info(body)
        if info is None or info[1] < OV_MIN_FILE_WIDTH:
            continue
        return info[0], body, openverse_credit(r, landing), landing
    return None


def shorten_query(q):
    """3단어 이상이면 마지막 단어를 뺀 검색어, 아니면 None."""
    words = q.split()
    return " ".join(words[:-1]) if len(words) >= 3 else None


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


def start_line(provider, source, key):
    if provider == "openverse":
        return "스톡: openverse · 키: 필요 없음"
    return gen_image.redact(f"스톡: pexels · 키: {source or '없음'}", key)


def end_line(saved, held):
    return f"저장 {saved}장 · 보류 {held}장"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="image-plan.md의 stock 슬롯을 무료 스톡 사진(기본 Openverse·키 불필요, 선택 Pexels)으로 받아 images/NN-<slug>.jpg|png로 저장하고 `파일`·출처 칸을 갱신합니다.",
        epilog="종료 코드: 0=처리 완료(보류 포함), 2=STOCK_PROVIDER 값 오류·pexels인데 키 없음·image-plan 없음·표 파싱 실패, "
               "3=거부(401·403), 5=네트워크·5xx, 6=요청 한도(429).")
    ap.add_argument("post", metavar="글_폴더", help="글 폴더(예: work/posts/003-chain) — 그 안의 images/image-plan.md를 읽는다")
    ap.add_argument("--only", metavar="NN[,NN]", help="이 슬롯 번호만 받기(쉼표 구분)")
    ap.add_argument("--dry-run", action="store_true", help="네트워크 접속 없이 슬롯 · 검색어 · 예상 파일명만 출력")
    ap.add_argument("--env", metavar="PATH", help="STOCK_PROVIDER·PEXELS_API_KEY가 든 .env 경로를 직접 지정")
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

    env = find_stock_env(plan, a.env)
    key_err = None
    try:
        provider, key, source = resolve_stock_provider(env)
    except ConfigError as e:
        if e.kind == "invalid":
            print(f"오류: {e}", file=sys.stderr)
            return 2
        provider, key, source, key_err = "pexels", None, None, e  # 키 없음은 대상 슬롯이 있을 때만 오류(dry-run은 통과)
    openverse = provider == "openverse"

    if a.dry_run:
        print(start_line(provider, source, key))
        for r in targets:
            q = r["prompt"].strip()
            name = f"images/{os.path.splitext(target_name(r, '.jpg'))[0]}.jpg|png" if openverse else f"images/{target_name(r)}"
            print(f"{r['slot']} · {q or '(검색어 없음)'} · " + (name if q else "건너뜀"))
        print(f"(dry-run) 네트워크 접속 없음 · 대상 {len(targets)}장")
        return 0
    if not targets:
        print("stock 슬롯이 없습니다.")
        print(end_line(0, 0))
        return 0
    if key_err is not None:
        print(key_err, file=sys.stderr)
        return 2

    print(start_line(provider, source, key))
    cur, saved, held, code = text, 0, 0, 0
    used = used_landing_urls(plan) if openverse else set()

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
        note = ""
        try:
            if openverse:
                # 이 글 안의 다른 슬롯에 이미 적힌 원본 페이지도 피한다(자기 행은 제외 — 다시 받을 때 같은 사진을 허용)
                own_lines = cur.splitlines()
                others = "\n".join(l for n, l in enumerate(own_lines) if n != r["line"])
                skip = used | landing_urls(others)
                state = DlState()
                picked = pick_openverse(openverse_search(q), skip, state)
                short = None
                if picked is None and state.left > 0 and shorten_query(q):
                    short = shorten_query(q)
                    picked = pick_openverse(openverse_search(short), skip, state)
                dl_fail = state.all_errors
                if picked is None:
                    reason = DL_FAILED if dl_fail else NO_RESULT
                    apply(rewrite_cells(cur, idx, r["line"], {"file": HELD, "review": reason}))
                    held += 1
                    print(f"[보류] {r['slot']} {reason} ({q})")
                    continue
                ext, data, credit, _landing = picked
                note = f" (검색어 줄임: {short})" if short else ""
                name = target_name(r, ext)
            else:
                photo, url = pick_photo(search(key, q))
                if photo is None:
                    apply(rewrite_cells(cur, idx, r["line"], {"file": HELD, "review": NO_RESULT}))
                    held += 1
                    print(f"[보류] {r['slot']} {NO_RESULT} ({q})")
                    continue
                data = download(url)
                name = target_name(r)
                credit = f"출처: Pexels/{clean_cell(photo.get('photographer') or '알 수 없음')} {clean_cell(photo.get('url') or '')}".rstrip()
        except StockError as e:
            rest = [t["slot"] for t in targets[i:]]
            print(gen_image.redact(f"[FAIL] {r['slot']} {e}\n중단: 남은 슬롯 {', '.join(rest)}은 받지 않았습니다.\n{e.hint}",
                                   key), file=sys.stderr)
            code = e.code
            break
        os.makedirs(images_dir, exist_ok=True)
        write_bytes_atomic(os.path.join(images_dir, name), data)
        rel = f"images/{name}"
        new = gen_image.rewrite_plan(cur, idx, {r["line"]: rel})
        apply(rewrite_cells(new, idx, r["line"], {"source" if "source" in idx else "review": credit}))
        saved += 1
        print(gen_image.redact(f"[OK] {r['slot']} → {rel} ({credit}){note}", key))
    print(end_line(saved, held))
    return code


if __name__ == "__main__":
    sys.exit(main())
