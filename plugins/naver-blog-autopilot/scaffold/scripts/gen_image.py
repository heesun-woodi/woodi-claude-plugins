#!/usr/bin/env python3
"""image-plan.md의 ai 슬롯을 이미지 생성 AI(Gemini 또는 OpenAI GPT 이미지)로 만들어 images/NN-<slug>.png로 저장한다.

실행(작업 폴더에서):
    uv run --with google-genai --with pillow scripts/gen_image.py work/posts/001-x/images/image-plan.md   # Gemini
    uv run --with pillow scripts/gen_image.py <image-plan.md>          # OpenAI(표준 라이브러리 HTTP — google-genai 불필요)
    python3 scripts/gen_image.py <image-plan.md> --dry-run      # 키·패키지 없이 제공자 결정·프롬프트·파일명만 출력

- 표에서 `유형`이 ai·cover인 행만 처리한다(photo·stock 행은 건드리지 않음 — stock은 fetch_stock.py). cover 행은 images/00-bg.png로 저장하고
  `파일` 칸(images/00-cover.png)은 바꾸지 않는다 — 합성은 scripts/make_cover.py. 슬롯 번호 = draft-v2.md의 `![슬롯: …]()` 순서.
- 프롬프트 = 접두 + 표의 프롬프트 + PROMPT_SUFFIX. 접두의 장면구는 프로필 `이미지 기본 장면` 행(없으면 `Korean everyday scene`)이고, 접두·접미 문자열은
  skills/blog-image-director/references/prompt-patterns.md의 "공통 접두/접미"와 글자 그대로 같아야 한다. 제공자와 무관하게 같다.
- 성공한 슬롯은 표의 `파일` 열을 post 폴더 기준 상대경로(images/01-cover.png)로 갱신해 image-plan.md를 다시 쓴다.
- 설정(.env): IMAGE_PROVIDER(gemini|openai, 선택) · GEMINI_API_KEY · OPENAI_API_KEY · IMAGE_MODEL(선택).
  탐색: --env → cwd/.env(= 작업 폴더) → image-plan.md 상위 폴더들의 .env → 환경변수.
  API 키(GEMINI_API_KEY 또는 OPENAI_API_KEY)가 실제로 든 첫 .env를 쓰고, IMAGE_PROVIDER·IMAGE_MODEL도 그 파일에서만 읽는다.
  어느 .env에도 키가 없으면 키는 환경변수, IMAGE_PROVIDER·IMAGE_MODEL은 항목마다 --env 파일 → cwd .env → 환경변수 순.
  파싱: `export KEY=…`, 따옴표, CRLF 허용. 따옴표 없는 값은 공백+`#` 이후가 주석, `#`로 시작하면 빈 값,
  따옴표 안이 공백뿐이면 빈 값. 같은 키가 여러 줄이면 처음 나온 비어 있지 않은 값. 키 값은 어디에도 출력하지 않는다.
  IMAGE_PROVIDER·IMAGE_MODEL 값도 형식 검사(gemini|openai / 모델 이름 형식, 키 모양이면 거부)를 통과해야 출력한다.
- 제공자: --provider > IMAGE_PROVIDER > GEMINI_API_KEY 있음 → gemini > OPENAI_API_KEY 있음 → openai.
  IMAGE_PROVIDER(또는 --provider)가 정한 제공자의 키가 없으면 다른 키로 넘어가지 않고 사용 오류(2).
  모델: --model > IMAGE_MODEL > 제공자 기본값(gemini=gemini-3-pro-image, openai=gpt-image-2).
- 비용: gemini는 장당 COST_PER_IMAGE_USD(추정치, 검증된 단가 아님 — https://ai.google.dev/pricing 확인).
  openai는 OPENAI_PRICING_NOTE(숫자 없음 — 요금 페이지 확인). 재생성도 과금된다.
- 의존: gemini는 google-genai(필수, --dry-run 제외), openai는 표준 라이브러리만.
  pillow(선택: 가로 --size px 리사이즈. 없으면 원본 저장 + 경고).
- HTTP 타임아웃 HTTP_TIMEOUT_MS. 503은 백오프 재시도. Gemini 429(쿼터 초과)·OpenAI 429(insufficient_quota·billing*)·
  OpenAI 401/403(키 거부)은 재시도하지 않고 남은 슬롯을 중단한다. OpenAI의 그 밖 429(속도 제한)·500·502·503은
  지수 백오프 재시도(최대 MAX_RETRIES회, Retry-After 헤더 존중) 후 그 슬롯만 실패.
종료 코드: 0=전부 성공(또는 dry-run), 1=실패 슬롯 있음(429 등 중단 포함), 2=사용 오류(키 없음 포함).
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
for _s in (sys.stdout, sys.stderr):  # Windows 콘솔(cp949)에서도 한글·이모지 출력이 죽지 않게
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_MODEL = "gemini-3-pro-image"  # product-mockup generate_scenes.py와 같은 모델
PROVIDERS = ("gemini", "openai")
DEFAULT_MODELS = {"gemini": DEFAULT_MODEL, "openai": "gpt-image-2"}
KEY_NAMES = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}
ENV_NAMES = ("IMAGE_PROVIDER", "GEMINI_API_KEY", "OPENAI_API_KEY", "IMAGE_MODEL", "PEXELS_API_KEY")  # PEXELS_API_KEY는 fetch_stock용 — 제공자 판정(KEY_NAMES)에는 영향 없음
KEY_HELP = {"gemini": "GEMINI_API_KEY 발급: https://aistudio.google.com/apikey (결제 설정된 프로젝트의 키)",
            "openai": "OPENAI_API_KEY 발급: https://platform.openai.com/api-keys"}
OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
OPENAI_SIZE = "1536x1024"  # 가로 3:2 — 저장 시 --size(기본 1200) 가로로 리사이즈
OPENAI_QUALITY = "medium"
OPENAI_RETRY_STATUS = {429, 500, 502, 503}  # 429는 결제·쿼터(insufficient_quota·billing*)가 아닐 때만
MAX_RETRY_AFTER_SECONDS = 60
OPENAI_PRICING_NOTE = "요금은 OpenAI 요금 페이지(https://openai.com/api/pricing) 확인 — 모델·품질에 따라 다름"
OPENAI_LIMIT_HINT = "OpenAI 사용 한도/결제 문제(요금제·결제 수단 확인)"
OPENAI_VERIFY_HINT = ("이 OpenAI 조직은 GPT 이미지 모델을 쓸 수 없습니다 — "
                      "platform.openai.com에서 조직 인증(Verify Organization)이 필요할 수 있습니다")
MAX_RETRIES = 3
RETRY_STATUS_CODES = {503}
HTTP_TIMEOUT_MS = 120_000  # 응답 없는 소켓에서 무기한 대기하지 않게
QUOTA_HINT = ("Gemini 이미지 모델은 결제(Billing)가 설정된 Google Cloud 프로젝트의 키가 필요합니다 — "
              "https://aistudio.google.com/apikey 에서 결제 설정 확인")
BASE_BACKOFF_SECONDS = 2.0
# 추정치 — gemini-3-pro-image 2K 단가는 요금 페이지에서 확인(https://ai.google.dev/pricing)
COST_PER_IMAGE_USD = 0.04
KINDS = {"ai", "photo", "cover", "stock"}  # stock = Pexels 검색(fetch_stock.py) — photo처럼 여기서는 건너뜀
GEN_KINDS = {"ai", "cover"}  # cover = 표지 배경(00-bg.png). 합성은 make_cover.py

# prompt-patterns.md "공통 접두/접미"와 동일하게 유지할 것(tests/test_gen_image.py가 대조).
# 장면구(DEFAULT_SCENE)만 프로필 `이미지 기본 장면` 행으로 바뀐다. PROMPT_PREFIX = 기본 장면구를 넣은 접두(prompt-patterns.md와 대조).
DEFAULT_SCENE = "Korean everyday scene"
PROMPT_PREFIX_FMT = "photorealistic, {scene}, no text, no letters, no watermark, no close-up faces"
PROMPT_PREFIX = PROMPT_PREFIX_FMT.format(scene=DEFAULT_SCENE)
PROMPT_SUFFIX = ("natural light, wide landscape 3:2 composition, people only seen from behind or far away, "
                 "no brand logos, no readable signs, no license plates, no numbers")

# 목적 → 파일명 slug(앞에서부터 처음 맞는 것). 없으면 목적의 영숫자, 그것도 없으면 "scene".
PURPOSE_SLUGS = [("표지", "cover"), ("커버", "cover"), ("cta", "business"), ("업체", "business"),
                 ("시험", "exam"), ("절차", "steps"), ("제품", "product"), ("상품", "product"),
                 ("현장", "scene"), ("작업", "work"), ("안전", "safety"),
                 ("서류", "documents"), ("자격", "documents"), ("요약", "summary")]

COLS = {"slot": "슬롯", "where": "위치", "purpose": "목적", "kind": "유형",
        "prompt": "프롬프트", "caption": "캡션", "file": "파일"}


def split_row(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    return [c.strip() for c in s.strip("|").split("|")]


def parse_plan(text):
    """표를 파싱해 (header_index, rows) 반환. rows: dict(slot, purpose, kind, prompt, caption, file, line)."""
    lines = text.splitlines()
    idx, rows, ncols = None, [], 0
    for i, line in enumerate(lines):
        if idx is not None and not line.strip():
            break  # 첫 표가 끝난 뒤 빈 줄 → 그 아래는 읽지 않는다
        cells = split_row(line)
        if cells is None:
            continue
        if idx is None:
            if cells and cells[0].startswith(COLS["slot"]):
                idx = {}
                for key, name in COLS.items():
                    for j, c in enumerate(cells):
                        if c.startswith(name):
                            idx[key] = j
                            break
                missing = [COLS[k] for k in COLS if k not in idx]
                if missing:
                    raise ValueError("image-plan.md 표 머리에 열이 없습니다: " + ", ".join(missing))
                ncols = len(cells)
            continue
        if not re.fullmatch(r"\d{1,2}", cells[0]):
            continue  # 구분선(|---|) 등
        if len(cells) > ncols:
            raise ValueError(f"슬롯 {cells[0]} 행의 칸 수({len(cells)})가 표 머리({ncols})보다 많습니다 — 칸 안에 '|'가 있는지 확인하세요.")
        get = lambda k: cells[idx[k]] if idx[k] < len(cells) else ""
        rows.append({"slot": "%02d" % int(cells[0]), "purpose": get("purpose"),
                     "kind": get("kind").lower(), "prompt": get("prompt"),
                     "caption": get("caption"), "file": get("file"), "line": i})
        if rows[-1]["kind"] not in KINDS:
            print(f"경고: 슬롯 {rows[-1]['slot']}의 유형 '{get('kind')}'은 ai/photo/stock/cover가 아니어서 건너뜁니다.", file=sys.stderr)
    if idx is None:
        raise ValueError("image-plan.md에서 '| 슬롯 | …' 표 머리를 찾지 못했습니다.")
    return idx, rows


def parse_only(value):
    if not value:
        return None
    out = set()
    for tok in value.split(","):
        tok = tok.strip()
        if not tok:
            continue
        if not tok.isdigit():
            raise ValueError(f"--only 값은 슬롯 번호여야 합니다: {tok}")
        out.add("%02d" % int(tok))
    return out


def select_ai_rows(rows, only=None):
    """ai·cover 행만 고르고 --only로 거른다. only에 생성 대상이 아닌/없는 번호가 있으면 ValueError."""
    ai = [r for r in rows if r["kind"] in GEN_KINDS]
    if only is None:
        return ai
    known = {r["slot"]: r["kind"] for r in rows}
    bad = sorted(s for s in only if s not in known)
    if bad:
        raise ValueError("표에 없는 슬롯 번호: " + ", ".join(bad))
    notai = sorted(s for s in only if known[s] not in GEN_KINDS)
    if notai:
        raise ValueError("ai 슬롯이 아닙니다(photo는 생성 대상 아님): " + ", ".join(notai))
    return [r for r in ai if r["slot"] in only]


def slug_for(purpose):
    low = purpose.lower()
    for key, slug in PURPOSE_SLUGS:
        if key in low:
            return slug
    ascii_part = re.sub(r"[^a-z0-9]+", "-", low).strip("-")
    return ascii_part[:30] or "scene"


def target_name(row):
    """이미 `파일` 열에 .png 경로가 있으면 그 파일명을 유지(재생성 시 같은 파일 덮어쓰기)."""
    if row["kind"] == "cover":
        return f"{row['slot']}-bg.png"  # `파일` 칸(00-cover.png)은 make_cover.py의 합성 결과 — 배경은 따로 저장
    f = row["file"].strip("` ")
    if f.lower().endswith(".png"):
        return os.path.basename(f)
    return f"{row['slot']}-{slug_for(row['purpose'])}.png"


def build_prompt(scene, base_scene=None):
    """base_scene: 프로필 `이미지 기본 장면` 값(None·빈 값이면 DEFAULT_SCENE)."""
    prefix = PROMPT_PREFIX_FMT.format(scene=(base_scene or "").strip().rstrip(".") or DEFAULT_SCENE)
    return f"{prefix}. {scene.strip().rstrip('.')}. {PROMPT_SUFFIX}."


def load_base_scene(kdir):
    """knowledge/business-profile.md `이미지 기본 장면` 행(없거나 비면 ""). kdir가 None이어도 안전."""
    if not kdir:
        return ""
    try:
        from lint_post import profile_row
    except ImportError:
        return ""
    return profile_row(kdir, "이미지 기본 장면")


def rewrite_plan(text, idx, updates):
    """updates: {line_no: 새 파일 경로}. 해당 행의 `파일` 칸만 바꾼다."""
    lines = text.splitlines()
    for ln, value in updates.items():
        cells = split_row(lines[ln])
        while len(cells) <= idx["file"]:
            cells.append("")
        cells[idx["file"]] = value
        lines[ln] = "|" + "|".join(f" {c} " if c else " " for c in cells) + "|"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def read_env_values(path, names=ENV_NAMES):
    """.env에서 names에 든 값들을 읽어 dict로 반환(빈 값은 넣지 않음). 값은 출력하지 않는다."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            if t.startswith("export "):
                t = t[len("export "):].lstrip()
            k, sep, v = t.partition("=")
            k = k.strip()
            if not sep or k not in names or k in out:
                continue
            v = v.strip()
            if v[:1] in ("'", '"'):
                end = v.find(v[0], 1)
                v = v[1:end] if end != -1 else v[1:]
                if not v.strip():
                    v = ""  # 따옴표 안이 공백뿐 → 빈 값
            elif v.startswith("#"):
                v = ""  # `KEY=#…` → 빈 값(주석)
            else:
                v = re.split(r"\s#", v, maxsplit=1)[0].strip()  # 공백+# 이후는 주석
            if v:
                out[k] = v  # 같은 키가 여러 줄이면 처음 나온 비어 있지 않은 값
    return out


def find_env(plan_path=None, env_override=None):
    """순서: --env → cwd/.env → plan 상위 폴더들의 .env → 환경변수.

    키: API 키(GEMINI_API_KEY/OPENAI_API_KEY)가 든 첫 .env 파일의 값. 어느 파일에도 없으면 환경변수.
    IMAGE_PROVIDER·IMAGE_MODEL: 키를 찾은 .env의 값(그 파일에 없으면 미지정).
    키를 환경변수에서 읽을 때는 항목마다 --env 파일(지정 시) → cwd .env → 환경변수 중 처음 값이 있는 곳.
    반환: ENV_NAMES 중 값이 있는 것 + "_source"(파일 경로 / "환경변수" / None)."""
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
        vals = read_env_values(ap)
        if any(vals.get(n) for n in KEY_NAMES.values()):
            vals["_source"] = p
            return vals
    vals = {n: os.environ[n].strip() for n in KEY_NAMES.values() if os.environ.get(n, "").strip()}
    settings = [os.path.join(os.getcwd(), ".env")]
    if env_override:
        settings.insert(0, env_override)
    file_vals = [read_env_values(p, ("IMAGE_PROVIDER", "IMAGE_MODEL")) for p in settings if os.path.isfile(p)]
    for n in ("IMAGE_PROVIDER", "IMAGE_MODEL"):
        v = next((fv[n] for fv in file_vals if fv.get(n)), None) or os.environ.get(n, "").strip()
        if v:
            vals[n] = v
    vals["_source"] = "환경변수" if any(vals.get(n) for n in KEY_NAMES.values()) else None
    return vals


_SECRET_RE = re.compile(r"\b(sk-[A-Za-z0-9_\-*.]{4,}|AIza[A-Za-z0-9_\-]{10,})")
_MODEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")


def resolve_provider(env, provider=None, model=None):
    """(provider, key, model, source). 키가 하나도 없으면 (None, None, None, None).

    provider 인자(--provider) > IMAGE_PROVIDER > GEMINI_API_KEY > OPENAI_API_KEY.
    지정된 제공자의 키가 없으면 ValueError(다른 키로 넘어가지 않음).
    IMAGE_PROVIDER·IMAGE_MODEL 값은 형식을 검사한 뒤에만 메시지에 쓴다(키를 잘못 넣은 경우 대비)."""
    origin = "--provider"
    if not provider:
        provider, origin = (env.get("IMAGE_PROVIDER") or "").strip().lower(), "IMAGE_PROVIDER"
    if provider:
        if provider not in PROVIDERS:
            raise ValueError(f"{origin} 값이 알 수 없는 값입니다(gemini 또는 openai만 가능 — 키를 잘못 넣었는지 확인).")
        key = env.get(KEY_NAMES[provider])
        if not key:
            raise ValueError(f"{origin}={provider}인데 {KEY_NAMES[provider]}가 없습니다 — {KEY_HELP[provider]}")
    else:
        provider = next((p for p in PROVIDERS if env.get(KEY_NAMES[p])), None)
        if provider is None:
            return None, None, None, None
        key = env[KEY_NAMES[provider]]
    model_origin = "--model" if model else "IMAGE_MODEL"
    model = model or env.get("IMAGE_MODEL") or DEFAULT_MODELS[provider]
    if not _MODEL_RE.fullmatch(model) or _SECRET_RE.search(model) or key in model:
        raise ValueError(f"{model_origin} 값이 모델 이름 형식이 아닙니다(키를 잘못 넣었는지 확인)")
    return provider, key, model, env.get("_source")


def redact(text, key=None):
    """서버 오류 문구에 키(일부라도)가 섞여 나오면 지운다 — 마스킹해 보여 주지 않고 아예 뺀다."""
    text = str(text)
    if key:
        text = text.replace(key, "")
    return _SECRET_RE.sub("[키 생략]", text)


def retry_after_seconds(e):
    """Retry-After 헤더(초)가 있으면 그 값(최대 MAX_RETRY_AFTER_SECONDS), 없거나 읽을 수 없으면 None."""
    try:
        v = float((getattr(e, "headers", None) or {}).get("Retry-After"))
    except (TypeError, ValueError):
        return None
    return min(max(v, 0.0), MAX_RETRY_AFTER_SECONDS)


def read_http_error(e):
    """HTTPError → (status, error.code, error.type, error.message). 본문이 JSON이 아니어도 죽지 않는다."""
    status = getattr(e, "code", None)
    try:
        body = json.loads(e.read().decode("utf-8", "replace") or "{}")
    except Exception:  # noqa: BLE001
        body = {}
    err = body.get("error") if isinstance(body, dict) else None
    if not isinstance(err, dict):
        err = {}
    return status, str(err.get("code") or ""), str(err.get("type") or err.get("status") or ""), str(err.get("message") or "")


def write_plan_atomic(path, content):
    """같은 폴더 임시 파일에 쓰고 os.replace — 중간에 끊겨도 image-plan.md가 반쯤 쓰이지 않는다."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".image-plan-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def save_image(data, out_path, width):
    try:
        from PIL import Image
    except ImportError:
        print(f"경고: pillow가 없어 리사이즈 없이 원본을 저장합니다: {out_path}", file=sys.stderr)
        with open(out_path, "wb") as f:
            f.write(data)
        return "원본"
    with Image.open(io.BytesIO(data)) as im:
        im = im.convert("RGB")
        w, h = im.size
        if w != width:
            im = im.resize((width, round(h * width / w)), Image.LANCZOS)
        im.save(out_path, "PNG")
        return "%dx%d" % im.size


class StopRemaining(RuntimeError):
    """재시도해도 풀리지 않는 오류(한도·키 거부) — 남은 슬롯까지 중단한다. reason·hint는 stderr 안내용."""

    def __init__(self, msg, reason, hint):
        super().__init__(msg)
        self.reason, self.hint = reason, hint


class QuotaExceeded(StopRemaining):
    """Gemini 429 RESOURCE_EXHAUSTED."""

    def __init__(self, msg):
        super().__init__(msg, "쿼터 초과(429)", QUOTA_HINT)


def generate_one(client, model, prompt):
    from google.genai import errors as genai_errors
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            it = client.interactions.create(model=model, input=[{"type": "text", "text": prompt}],
                                            response_format={"type": "image", "image_size": "2K"})
            img = it.output_image
            if img is None or not img.data:
                raise RuntimeError("응답에 이미지가 없습니다(output_image 비어 있음)")
            return base64.b64decode(img.data)
        except genai_errors.APIError as e:
            code = getattr(e, "code", None)
            msg = redact(getattr(e, "message", e))
            if code == 429:
                raise QuotaExceeded(f"APIError 429: {msg}") from None
            last = RuntimeError(f"APIError {code}: {msg}")
            if code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                time.sleep(BASE_BACKOFF_SECONDS * 2 ** (attempt - 1))
                continue
            raise last
    raise last


def _is_safety_rejection(code, etype, message):
    blob = f"{code} {etype}".lower()
    return any(w in blob for w in ("safety", "moderation", "content_policy")) or \
        "safety system" in message.lower()


def generate_openai(key, model, prompt):
    """OpenAI Images API(표준 라이브러리). 키는 Authorization 헤더에만 넣는다. 반환: PNG 바이트."""
    body = json.dumps({"model": model, "prompt": prompt, "size": OPENAI_SIZE, "quality": OPENAI_QUALITY,
                       "n": 1, "output_format": "png"}).encode("utf-8")
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(OPENAI_IMAGES_URL, data=body, method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_MS / 1000) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            status, code, etype, message = read_http_error(e)
            if status == 401:
                raise StopRemaining("OpenAI 401: OpenAI 키가 올바르지 않습니다", "키 거부(401)",
                                    "OPENAI_API_KEY를 확인하세요 — https://platform.openai.com/api-keys") from None
            if status == 403:
                raise StopRemaining(f"OpenAI 403: {OPENAI_VERIFY_HINT}", "권한 없음(403)", OPENAI_VERIFY_HINT) from None
            if status == 429 and any(c.lower().startswith(("insufficient_quota", "billing")) for c in (code, etype)):
                raise StopRemaining(f"OpenAI 429: {OPENAI_LIMIT_HINT}", "사용 한도·결제(429)", OPENAI_LIMIT_HINT) from None
            if status == 400 and _is_safety_rejection(code, etype, message):
                raise RuntimeError("OpenAI 400: 안전 정책으로 거절 — 프롬프트를 바꿔 재생성") from None
            if status == 429:
                last = RuntimeError(f"OpenAI 429: 요청 속도 제한 — {MAX_RETRIES}회 시도 후 실패, 잠시 뒤 --only로 재생성")
            else:
                last = RuntimeError(f"OpenAI {status}: {redact(message, key)[:200] or '(응답 메시지 없음)'}")
            if status in OPENAI_RETRY_STATUS and attempt < MAX_RETRIES:
                wait = retry_after_seconds(e)
                time.sleep(wait if wait is not None else BASE_BACKOFF_SECONDS * 2 ** (attempt - 1))
                continue
            raise last from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"OpenAI 네트워크 오류: {redact(getattr(e, 'reason', e), key)}") from None
        data = payload.get("data") if isinstance(payload, dict) else None
        b64 = data[0].get("b64_json") if isinstance(data, list) and data and isinstance(data[0], dict) else None
        if not b64:
            raise RuntimeError("응답에 이미지가 없습니다(data[0].b64_json 비어 있음)")
        return base64.b64decode(b64)
    raise last


def cost_line(provider, n):
    if provider == "openai":
        return f"이미지 {n}장 — {OPENAI_PRICING_NOTE}"
    return (f"예상 비용(추정치): 약 ${COST_PER_IMAGE_USD * n:.2f}"
            f" (장당 ${COST_PER_IMAGE_USD:.2f} 가정 — https://ai.google.dev/pricing 확인)")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="image-plan.md 표의 ai 슬롯을 Gemini 또는 OpenAI(GPT 이미지)로 생성해 NN-<slug>.png로 저장하고 `파일` 열을 갱신합니다.",
        epilog=(f"종료 코드: 0=성공(또는 --dry-run), 1=실패 슬롯 있음, 2=사용 오류(키 없음 포함). "
                f"비용 — gemini: 장당 약 ${COST_PER_IMAGE_USD:.2f}(추정치) · openai: {OPENAI_PRICING_NOTE}."),
        add_help=False)
    ap._positionals.title, ap._optionals.title = "인자", "옵션"
    ap.add_argument("-h", "--help", action="help", help="도움말을 보여주고 종료")
    ap.add_argument("plan", help="images/image-plan.md 경로")
    ap.add_argument("--only", metavar="01,03", help="이 슬롯 번호만 (재)생성(쉼표 구분)")
    ap.add_argument("--out-dir", metavar="DIR", help="저장 폴더(기본: image-plan.md가 있는 폴더 = posts/NNN/images)")
    ap.add_argument("--size", type=int, default=1200, help="저장 가로 픽셀(기본 1200, pillow 필요)")
    ap.add_argument("--provider", choices=PROVIDERS, help="이미지 제공자(기본: IMAGE_PROVIDER → 있는 키 순 gemini, openai)")
    ap.add_argument("--model", help=f"이미지 모델(기본: IMAGE_MODEL → gemini={DEFAULT_MODELS['gemini']}, "
                                    f"openai={DEFAULT_MODELS['openai']})")
    ap.add_argument("--env", metavar="PATH", help="키가 든 .env 경로를 직접 지정")
    ap.add_argument("--knowledge", metavar="DIR", help="knowledge 폴더(기본: image-plan.md 위로 찾음) — 프로필 `이미지 기본 장면`을 읽음")
    ap.add_argument("--dry-run", action="store_true", help="API 호출 없이 제공자 결정·슬롯·프롬프트·파일명만 출력")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2

    if a.size <= 0:
        print("오류: --size는 0보다 커야 합니다.", file=sys.stderr)
        return 2
    if not os.path.isfile(a.plan):
        print(f"오류: 파일을 찾을 수 없습니다: {a.plan}", file=sys.stderr)
        return 2
    with open(a.plan, encoding="utf-8") as f:
        text = f.read()
    try:
        idx, rows = parse_plan(text)
        targets = select_ai_rows(rows, parse_only(a.only))
    except ValueError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 2

    plan_dir = os.path.dirname(os.path.abspath(a.plan))
    out_dir = os.path.abspath(a.out_dir) if a.out_dir else plan_dir
    post_dir = os.path.dirname(plan_dir)
    n_photo = sum(1 for r in rows if r["kind"] == "photo")
    n_stock = sum(1 for r in rows if r["kind"] == "stock")
    stock_txt = f", stock {n_stock}" if n_stock else ""  # stock이 없으면 1.0.0 출력 그대로
    print(f"슬롯 {len(rows)}개 (ai {sum(1 for r in rows if r['kind'] == 'ai')}, photo {n_photo}{stock_txt}) → 이번 대상 ai {len(targets)}개")
    if not targets:
        print("생성할 ai 슬롯이 없습니다.")
        return 0
    for r in targets:
        if not r["prompt"]:
            print(f"오류: 슬롯 {r['slot']}의 프롬프트 칸이 비어 있습니다.", file=sys.stderr)
            return 2
    if a.knowledge:
        kdir = a.knowledge
    else:
        try:
            from lint_post import find_knowledge
            kdir = find_knowledge(a.plan)
        except ImportError:
            kdir = None
    base_scene = load_base_scene(kdir)

    env = find_env(a.plan, a.env)
    try:
        provider, key, model, src = resolve_provider(env, a.provider, a.model)
        perr = None
    except ValueError as e:
        provider = key = model = src = None
        perr = str(e)

    if a.dry_run:
        if perr:
            print(f"제공자: 결정 실패 — {redact(perr, key)}")
        elif provider is None:
            print("제공자: 없음(키 없음)")
        else:
            print(redact(f"키: {src}에서 읽음 · 제공자: {provider} · 모델: {model}", key))
        for r in targets:
            out = os.path.join(out_dir, target_name(r))
            tag = " (cover: 표지 배경 → make_cover.py로 합성)" if r["kind"] == "cover" else ""
            print(f"\n[{r['slot']}] 목적: {r['purpose']}{tag} | 캡션: {r['caption']}")
            print(f"  파일: {os.path.relpath(out, post_dir)}")
            print(f"  프롬프트: {build_prompt(r['prompt'], base_scene)}")
        print(f"\n(dry-run) API 호출 없음. {cost_line(provider, len(targets))}")
        return 0

    if perr:
        print(f"오류: {redact(perr)}", file=sys.stderr)
        return 2
    if provider is None:
        print("오류: 이미지 키가 없습니다. 작업 폴더 .env에 GEMINI_API_KEY=… 또는 OPENAI_API_KEY=… 중 하나를 넣으세요"
              "(채팅에 키를 붙여넣지 마세요).\n  " + "\n  ".join(KEY_HELP[p] for p in PROVIDERS), file=sys.stderr)
        return 2
    if provider == "gemini":
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError:
            print("오류: google-genai가 없습니다. `uv run --with google-genai --with pillow scripts/gen_image.py …`로 실행하세요.",
                  file=sys.stderr)
            return 2
        client = genai.Client(api_key=key, http_options=genai_types.HttpOptions(timeout=HTTP_TIMEOUT_MS))

        def gen(prompt):
            return generate_one(client, model, prompt)
    else:
        def gen(prompt):
            return generate_openai(key, model, prompt)
    print(redact(f"키: {src}에서 읽음 · 제공자: {provider} · 모델: {model}", key))
    print(cost_line(provider, len(targets)))
    os.makedirs(out_dir, exist_ok=True)

    updates, ok, fail = {}, [], []

    def persist():
        if updates:
            write_plan_atomic(a.plan, rewrite_plan(text, idx, updates))

    try:
        for r in targets:
            out = os.path.join(out_dir, target_name(r))
            try:
                data = gen(build_prompt(r["prompt"], base_scene))
                res = save_image(data, out, a.size)
            except StopRemaining as e:
                rest = [t["slot"] for t in targets[targets.index(r):]]
                print(f"[FAIL] {r['slot']} {redact(e, key)}\n중단: {e.reason} — 남은 슬롯 {', '.join(rest)}은 생성하지 않았습니다.\n"
                      f"{e.hint}", file=sys.stderr)
                fail.extend(rest)
                break
            except Exception as e:  # noqa: BLE001 — 실패 슬롯은 보고하고 다음으로
                print(f"[FAIL] {r['slot']} {type(e).__name__}: {redact(e, key)}", file=sys.stderr)
                fail.append(r["slot"])
                continue
            rel = os.path.relpath(out, post_dir)
            if r["kind"] != "cover":  # cover 행의 `파일` 칸은 00-cover.png 그대로 둔다
                updates[r["line"]] = rel
            ok.append(r["slot"])
            persist()  # 슬롯마다 저장 — 중간에 끊겨도 완료분은 남는다
            print(f"[OK] {r['slot']} → {rel} ({res})")
    finally:
        persist()  # KeyboardInterrupt 등으로 빠져나가도 완료분 보존
    print(f"\n요약: 성공 {len(ok)} ({', '.join(ok) or '-'}) · 실패 {len(fail)} ({', '.join(fail) or '-'})")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
