#!/usr/bin/env python3
"""check_image_key.py — 이미지 생성 키가 쓸 수 있는지 무료 조회로 확인한다(이미지는 만들지 않음 — 비용 0).

사용 (작업 폴더에서, 표준 라이브러리만):
    python3 scripts/check_image_key.py [--env PATH] [--provider gemini|openai]
    python3 scripts/check_image_key.py --stock [--env PATH]     # 스톡 사진 제공자(Openverse 기본 / Pexels) 확인

- 키 탐색·제공자 결정은 gen_image.py와 같다(find_env·resolve_provider 공유). --env → cwd/.env → 환경변수.
- 확인 방법: 모델 정보 조회(GET). gemini는 x-goog-api-key 헤더, openai는 Authorization: Bearer 헤더.
  키는 URL에 넣지 않고, 어떤 출력에도 키 값을 쓰지 않는다.
- Gemini 결제 미설정·OpenAI 조직 인증 필요 여부는 이 조회로 알 수 없다 — 실제 생성의 429(Gemini)·403(OpenAI)로 드러난다.
- IMAGE_PROVIDER·IMAGE_MODEL이 형식에 맞지 않으면(키를 잘못 넣은 경우 등) 값은 출력하지 않고 종료 코드 2.

종료 코드 (stdout 첫 줄이 사람용 문구):
    0  키 OK — 모델 사용 가능
    2  키 없음 / 설정 오류(IMAGE_PROVIDER가 정한 제공자의 키가 비었음, 알 수 없는 IMAGE_PROVIDER 값, 잘못된 인자)
    3  키 거부(401/403, Gemini의 API_KEY_INVALID 400 포함)
    4  모델 없음 또는 이 키로 접근 권한 없음(404)
    5  네트워크·기타 오류

--stock (스톡 제공자만 확인 — 이미지 생성 키는 보지 않음, --provider·--model과 함께 쓸 수 없음):
    제공자 결정: .env의 STOCK_PROVIDER → 없고 PEXELS_API_KEY가 있으면 pexels → 둘 다 없으면 openverse (fetch_stock.resolve_stock_provider).
    openverse: GET https://api.openverse.org/v1/images/?q=desk&license=cc0,pdm&aspect_ratio=wide&mature=false&page_size=1 (키 없음)
    0  스톡 확인: openverse 사용 가능 (키 불필요)
    5  네트워크·5xx·기타 오류(429 포함 — `요청 한도 — 잠시 뒤 다시`)
    pexels: GET https://api.pexels.com/v1/search?query=test&per_page=1 (헤더 Authorization: <키>)
    0  스톡 키 확인: pexels 사용 가능 (<source>)
    3  키 거부(401/403)
    5  네트워크·기타 오류(429 포함)
    2  STOCK_PROVIDER 값 오류, 또는 pexels인데 PEXELS_API_KEY가 없음
"""
import argparse
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_image  # noqa: E402 — 표준 출력 UTF-8 설정도 여기서 된다

TIMEOUT_SECONDS = 30
GEMINI_MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}"
OPENAI_MODEL_URL = "https://api.openai.com/v1/models/{model}"
GEMINI_BILLING_NOTE = "Gemini 이미지 생성은 결제 설정된 프로젝트 키여야 합니다(429면 결제 확인)"
OPENAI_VERIFY_NOTE = "키 확인이 통과해도 이미지 생성에서 403이 나면 조직 인증(Verify Organization)이 필요합니다"
PEXELS_CHECK_URL = "https://api.pexels.com/v1/search?query=test&per_page=1"


def build_request(provider, key, model):
    if provider == "gemini":
        return urllib.request.Request(GEMINI_MODEL_URL.format(model=model), headers={"x-goog-api-key": key})
    return urllib.request.Request(OPENAI_MODEL_URL.format(model=model), headers={"Authorization": f"Bearer {key}"})


def check(provider, key, model):
    """(종료 코드, 사람용 문구 줄들). 키 값은 문구에 넣지 않는다."""
    try:
        with urllib.request.urlopen(build_request(provider, key, model), timeout=TIMEOUT_SECONDS) as resp:
            resp.read()
        return 0, []
    except urllib.error.HTTPError as e:
        status, code, etype, message = gen_image.read_http_error(e)
        blob = f"{code} {etype} {message}"
        if provider == "gemini" and (status in (401, 403) or (status == 400 and (
                "API_KEY_INVALID" in blob or "API key not valid" in blob))):
            return 3, [f"이미지 키 거부: Gemini {status} — GEMINI_API_KEY가 올바르지 않거나 이 키로 Gemini API를 쓸 수 없습니다",
                       gen_image.KEY_HELP["gemini"]]
        if provider == "openai" and status == 401:
            return 3, ["이미지 키 거부: OpenAI 401 — OpenAI 키가 올바르지 않습니다", gen_image.KEY_HELP["openai"]]
        if provider == "openai" and status == 403:
            return 3, [f"이미지 키 거부: OpenAI 403 — {gen_image.OPENAI_VERIFY_HINT}"]
        if status == 404:
            return 4, [f"모델 없음: {provider} 모델 {model}을 찾을 수 없거나 이 키로 접근할 수 없습니다(404)",
                       "IMAGE_MODEL(또는 --model 없이 기본 모델)을 확인하세요"]
        extra = [gen_image.OPENAI_LIMIT_HINT] if provider == "openai" and status == 429 else []
        if provider == "gemini" and status == 429:
            extra = [gen_image.QUOTA_HINT]
        summary = gen_image.redact(message, key)[:200] or "(응답 메시지 없음)"
        return 5, [f"확인 실패: {provider} HTTP {status} — {summary}"] + extra
    except urllib.error.URLError as e:
        return 5, [f"확인 실패: 네트워크 오류 — {gen_image.redact(getattr(e, 'reason', e), key)}"]
    except Exception as e:  # noqa: BLE001 — 타임아웃 등
        return 5, [f"확인 실패: {type(e).__name__} — {gen_image.redact(e, key)}"]


def check_openverse():
    """--stock, openverse: 검색 1회(q=desk, page_size=1)로 확인. (종료 코드, 사람용 문구 줄들)."""
    import fetch_stock  # 같은 폴더 — 요청 URL·User-Agent 공유
    url = fetch_stock.OPENVERSE_URL + "?q=desk" + fetch_stock.OPENVERSE_QUERY.replace("page_size=20", "page_size=1")
    req = urllib.request.Request(url, headers={"User-Agent": fetch_stock.openverse_ua(), "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            resp.read()
        return 0, ["스톡 확인: openverse 사용 가능 (키 불필요)"]
    except urllib.error.HTTPError as e:
        status = getattr(e, "code", None)
        return 5, [f"확인 실패: openverse HTTP {status}" + (" — 요청 한도 — 잠시 뒤 다시" if status == 429 else "")]
    except urllib.error.URLError as e:
        return 5, [f"확인 실패: 네트워크 오류 — {gen_image.redact(getattr(e, 'reason', e))}"]
    except Exception as e:  # noqa: BLE001 — 타임아웃 등
        return 5, [f"확인 실패: {type(e).__name__} — {gen_image.redact(e)}"]


def check_stock(env_override):
    """--stock: 제공자를 결정해 확인. (종료 코드, 사람용 문구 줄들, 키). 키 값은 문구에 넣지 않는다."""
    import fetch_stock  # 같은 폴더 — 제공자 결정·키 탐색·안내 문구 공유
    try:
        provider, key, source = fetch_stock.resolve_stock_provider(fetch_stock.find_stock_env(None, env_override))
    except fetch_stock.ConfigError as e:
        if e.kind == "invalid":
            return 2, [f"스톡 설정 오류: {e}"], None
        return 2, [fetch_stock.NO_PEXELS_KEY_MSG], None
    if provider == "openverse":
        code, lines = check_openverse()
        return code, lines, None
    req = urllib.request.Request(PEXELS_CHECK_URL, headers={"Authorization": key, "User-Agent": fetch_stock.UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            resp.read()
        return 0, [f"스톡 키 확인: pexels 사용 가능 ({source})"], key
    except urllib.error.HTTPError as e:
        status = getattr(e, "code", None)
        if status in (401, 403):
            return 3, [f"스톡 키 거부: Pexels {status} — PEXELS_API_KEY가 올바르지 않습니다", fetch_stock.KEY_HELP], key
        return 5, [f"확인 실패: pexels HTTP {status}" + (" — 요청 한도 초과, 잠시 뒤 다시 확인" if status == 429 else "")], key
    except urllib.error.URLError as e:
        return 5, [f"확인 실패: 네트워크 오류 — {gen_image.redact(getattr(e, 'reason', e), key)}"], key
    except Exception as e:  # noqa: BLE001 — 타임아웃 등
        return 5, [f"확인 실패: {type(e).__name__} — {gen_image.redact(e, key)}"], key


def main(argv=None):
    ap = argparse.ArgumentParser(description="이미지 생성 키(Gemini/OpenAI)를 무료 조회로 확인합니다(이미지 생성 없음).",
                                 epilog="종료 코드: 0=OK, 2=키 없음·설정 오류, 3=키 거부, 4=모델 없음, 5=네트워크·기타.")
    ap.add_argument("--env", metavar="PATH", help="키가 든 .env 경로를 직접 지정")
    ap.add_argument("--provider", choices=gen_image.PROVIDERS, help="확인할 제공자(기본: IMAGE_PROVIDER → 있는 키 순)")
    ap.add_argument("--model", help="확인할 모델(기본: IMAGE_MODEL → 제공자 기본 모델)")
    ap.add_argument("--stock", action="store_true",
                    help="스톡 사진 제공자 확인 — 기본 openverse(키 불필요), STOCK_PROVIDER=pexels면 PEXELS_API_KEY(0=OK, 2=설정 오류, 3=키 거부, 5=네트워크)")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2

    if a.stock:
        if a.provider or a.model:
            print("오류: --stock은 --provider·--model과 함께 쓸 수 없습니다(이미지 생성 키는 --stock 없이 따로 확인).")
            return 2
        if a.env and not os.path.isfile(a.env):
            print(f"스톡 키 없음 — --env 파일을 찾을 수 없습니다: {a.env}")
            return 2
        code, lines, key = check_stock(a.env)
        for line in lines:
            print(gen_image.redact(line, key))
        return code

    if a.env and not os.path.isfile(a.env):
        print(f"이미지 키 없음: --env 파일을 찾을 수 없습니다: {a.env}")
        return 2
    env = gen_image.find_env(None, a.env)
    try:
        provider, key, model, source = gen_image.resolve_provider(env, a.provider, a.model)
    except ValueError as e:
        print(f"이미지 키 없음: {gen_image.redact(e)}")
        return 2
    if provider is None:
        print("이미지 키 없음: 작업 폴더 .env에 GEMINI_API_KEY 또는 OPENAI_API_KEY 중 하나를 넣으세요(채팅에 붙여넣지 마세요)")
        for p in gen_image.PROVIDERS:
            print(gen_image.KEY_HELP[p])
        return 2

    code, lines = check(provider, key, model)
    if code == 0:
        lines = [f"이미지 키 확인: {provider} · 모델 {model} 사용 가능 ({source})",
                 GEMINI_BILLING_NOTE if provider == "gemini" else OPENAI_VERIFY_NOTE]
    for line in lines:
        print(gen_image.redact(line, key))
    return code


if __name__ == "__main__":
    sys.exit(main())
