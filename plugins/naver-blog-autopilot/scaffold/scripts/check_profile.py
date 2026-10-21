#!/usr/bin/env python3
"""작업 폴더 knowledge/business-profile.md의 필수 값 점검 (표준 라이브러리만 사용, 인자 없음).

실행(작업 폴더에서): python3 scripts/check_profile.py
필수 = 블로그 유형·업체명·톤·`마무리 블록`·`이미지 소스`(값 또는 쉼표 목록) · 상품·서비스(쉼표 목록) · `## 금칙어` 절
(금칙어가 없으면 `- 없음` 한 줄). 조건 필수 = `연락처`(`마무리 블록`에 `문의헤딩`이 있을 때) · `장소 검색어`(`장소카드`가 있을 때).
`[치환 변수]` 그대로인 칸은 비어 있는 것으로 본다 — 판정은 lint_post의 profile_row·profile_list·load_forbidden과 같다
(다른 스크립트가 멈추는 조건과 일치).
출력은 정확히 한 줄(exit 0 / 2):
  `profile: OK` · `profile: NOFILE`(knowledge/·프로필 파일 없음)
  `profile: MISSING <행>,<행>,…` — 순서: 블로그 유형, 업체명, 상품·서비스, 톤, 마무리 블록, 이미지 소스, 연락처(조건), 장소 검색어(조건), 금칙어
  `profile: INVALID <행>=<값>` — MISSING이 없을 때만 검사. 열거값 위반(블로그 유형·톤·마무리 블록 항목·이미지 소스 항목)과
  `마무리 블록`에 `해시태그` 없음(`INVALID 마무리 블록=해시태그 없음`). 여러 개여도 첫 번째만.
조건 행 판정은 `마무리 블록` 값이 유효할 때만 한다(아니면 조건 행은 건너뛰고 INVALID가 먼저).
"""
import os
import sys
for _s in (sys.stdout, sys.stderr):  # Windows 콘솔(cp949)에서도 한글 출력이 죽지 않게
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lint_post import (BLOG_TYPES, CLOSING_ORDER, IMAGE_SOURCES, TONES, load_forbidden, profile_list,  # noqa: E402
                       profile_missing, profile_row)


def main():
    kdir = os.path.join(os.getcwd(), "knowledge")
    if profile_missing(kdir):
        print("profile: NOFILE")
        return 2
    blocks = profile_list(kdir, "마무리 블록")
    sources = profile_list(kdir, "이미지 소스")
    missing = [r for r, v in (("블로그 유형", profile_row(kdir, "블로그 유형")), ("업체명", profile_row(kdir, "업체명")),
                              ("상품·서비스", profile_list(kdir, "상품·서비스")), ("톤", profile_row(kdir, "톤")),
                              ("마무리 블록", blocks), ("이미지 소스", sources)) if not v]
    closing_ok = bool(blocks) and all(b in CLOSING_ORDER for b in blocks) and "해시태그" in blocks
    if closing_ok:  # 조건 행은 `마무리 블록` 값이 유효할 때만 판정한다
        if "문의헤딩" in blocks and not profile_row(kdir, "연락처"):
            missing.append("연락처")
        if "장소카드" in blocks and not profile_row(kdir, "장소 검색어"):
            missing.append("장소 검색어")
    try:
        load_forbidden(kdir)
    except ValueError:
        missing.append("금칙어")
    if missing:
        print("profile: MISSING " + ",".join(missing))
        return 2
    invalid = None
    for name, val, ok in (("블로그 유형", profile_row(kdir, "블로그 유형"), lambda v: v in BLOG_TYPES),
                          ("톤", profile_row(kdir, "톤"), lambda v: v in TONES)):
        if not ok(val):
            invalid = f"{name}={val}"
            break
    if invalid is None:
        bad = next((b for b in blocks if b not in CLOSING_ORDER), None)
        if bad is not None:
            invalid = f"마무리 블록={bad}"
        elif "해시태그" not in blocks:
            invalid = "마무리 블록=해시태그 없음"
    if invalid is None:
        bad = next((i for i in sources if i not in IMAGE_SOURCES), None)
        if bad is not None:
            invalid = f"이미지 소스={bad}"
    if invalid:
        print("profile: INVALID " + invalid)
        return 2
    print("profile: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
