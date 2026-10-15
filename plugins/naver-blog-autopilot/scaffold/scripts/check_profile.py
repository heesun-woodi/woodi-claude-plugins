#!/usr/bin/env python3
"""작업 폴더 knowledge/business-profile.md의 필수 값 점검 (표준 라이브러리만 사용, 인자 없음).

실행(작업 폴더에서): python3 scripts/check_profile.py
필수 = 업체명·연락처·장소 검색어(값) · 상품·서비스·고객 지역·업체 유형어·업종 일반어(쉼표 목록) · `## 금칙어` 절
(금칙어가 없으면 `- 없음` 한 줄). `[치환 변수]` 그대로인 칸은 비어 있는 것으로 본다 — 판정은 lint_post의
profile_row·profile_list·load_forbidden과 같다(다른 스크립트가 멈추는 조건과 일치).
출력은 정확히 한 줄: `profile: OK`(exit 0) / `profile: MISSING <행>,<행>,…`(exit 2) / `profile: NOFILE`(파일 없음, exit 2).
"""
import os
import sys
for _s in (sys.stdout, sys.stderr):  # Windows 콘솔(cp949)에서도 한글 출력이 죽지 않게
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lint_post import load_forbidden, profile_list, profile_missing, profile_row  # noqa: E402

ROWS = ("업체명", "연락처", "상품·서비스", "고객 지역", "장소 검색어", "업체 유형어", "업종 일반어")
LIST_ROWS = {"상품·서비스", "고객 지역", "업체 유형어", "업종 일반어"}  # 쉼표 목록 — 자리표시 항목을 빼고 하나라도 있어야 함


def main():
    kdir = os.path.join(os.getcwd(), "knowledge")
    if profile_missing(kdir):
        print("profile: NOFILE")
        return 2
    missing = [r for r in ROWS if not (profile_list if r in LIST_ROWS else profile_row)(kdir, r)]
    try:
        load_forbidden(kdir)
    except ValueError:
        missing.append("금칙어")
    print("profile: MISSING " + ",".join(missing) if missing else "profile: OK")
    return 2 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
