#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""워크숍 구글시트 생성·재구축 스크립트 (범용판) — 실험영역(문제영역) 선정 워크숍 킷.

무엇을 만드나
    8개 탭(0_HOME / 1_공통퍼널_분모 / 2_구간A_분석 / 3_구간B_분석 / 4_영역선정_순위 /
    5_정의서 / 6_골트리_NSM / 7_프롬프트_가이드)을 값·서식·수식·드롭다운·보호까지
    한 번에 구성한다. 각 섹션의 컬럼 순서는 분석 프롬프트 카드(02)의 TSV 출력 컬럼과
    1:1로 맞춰져 있다. **구조 정본은 `../06_workshop-sheet-spec.md`** 이며,
    이 스크립트는 그 스펙의 실행본이다. 구조를 바꿀 때는 스펙 문서를 먼저 고친다.

사전 요건
    - gws CLI가 설치되어 있고 구글 계정 인증이 끝나 있을 것
      (인증 확인: `gws sheets spreadsheets get --params '{"spreadsheetId":"<아무_시트_ID>"}'`)
    - 대상 스프레드시트에 대한 편집 권한

실행법
    1) 파일 상단 CONFIG 블록을 고객사 브리프(`../00_client-brief-template.md`) 값으로 수정한다.
    2) `python3 build_workshop_sheet.py`
    3) CONFIG["ssid"]가 비어 있으면 새 스프레드시트를 만들고 ID를 출력한다.
       출력된 ID를 CONFIG["ssid"]에 넣어두면 이후 실행은 **URL을 유지한 채** 재구축한다.

주의
    - 재구축은 기존 탭을 삭제 후 재생성한다. 이미 워크숍 데이터가 입력된 시트에
      다시 실행하면 입력값이 사라진다. 워크숍 시작 전에만 실행할 것.
    - 고객사별 수정은 CONFIG 블록만으로 끝나야 한다. CONFIG 아래 본문에
      고객사 실명·실수치를 직접 적지 않는다.
"""
import json
import subprocess
import sys

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG — 고객사별로 여기만 수정한다
# ═══════════════════════════════════════════════════════════════════════════

DAY_WORKSHOP = "Day 1"          # 워크숍 당일 라벨
DAY_VERIFY = "Day 2"            # 선행지표 상관성 검증(개별 과제) 라벨
UNVERIFIED = f"미확인({DAY_VERIFY} 검증 예정)"

CONFIG = {
    # ── 기본 정보 ──────────────────────────────────────────────────────────
    "client_name": "[고객사명]",
    "workshop_title": "문제영역 선정 워크숍",
    "analytics_tool": "[분석도구]",          # Amplitude / GA4 / Mixpanel
    "day_workshop_label": DAY_WORKSHOP,
    "day_verify_label": DAY_VERIFY,

    # 빈 문자열이면 새 스프레드시트를 만들고 ID를 출력한다.
    # 값이 있으면 그 시트를 URL 유지한 채 재구축한다.
    "ssid": "",

    # ── 공통 용어 ──────────────────────────────────────────────────────────
    "conversion_value_label": "[전환 가치 단가]",   # 예: 주문당 평균 마진 / 결제 1건당 가치
    "backup_label_note": "백업 전환 시 이후 결론 셀에 '⚠️ [백업 데이터 기준 시점] 기준 잠정' 라벨",
    "segment_axes": ["AOS", "iOS"],  # S5 세그먼트 축 2개. 웹이면 ["데스크톱", "모바일웹"] 등으로 교체
    "correlation_caveat_note": (
        "참고: 선행지표 → 최종 KPI 상관은 시차 보정 전 수치입니다. "
        "값이 낮아도 '지표를 바꾸자 / 유지하자' 양쪽 해석이 모두 가능하므로, "
        "수치와 표본 수(n)·측정 시점을 함께 적고 단독 근거로 쓰지 않습니다."
    ),

    # ── 탭1: 최종 KPI까지 전체 여정 퍼널 (행 순서 = 실제 여정 순서) ────────
    "journey_funnel_stages": [
        "[설치/방문]",
        "[회원가입 완료]",
        "[핵심 기능 진입]",
        "[핵심 기능 완료]",
        "[구간 A 핵심 전환 직전 단계]",
        "[구간 A 핵심 전환]",
        "[구간 B 시작 단계]",
        "[구간 B 중간 단계 1] ※계측 공백 가능",
        "[구간 B 중간 단계 2] ※계측 공백 가능",
        "[최종 전환 직전 단계] ※계측 공백 가능",
        "[최종 KPI 전환 완료]",
    ],

    # ── 구간 정의 (2구간 고정. 구간이 1개면 구간 B 탭을 지우고, 구간이 3개 이상이면 구간 탭 복제) ──
    "axes": [
        {
            "key": "A",
            "sheet_title": "2_구간A_분석",
            "name": "[구간 A명]",
            "owners": "[구간 A 담당]",
            "kpi_name": "[구간 A 핵심지표]",
            "kpi_line": "핵심 지표: [구간 A 핵심지표]  /  범위: [구간 A 여정 범위]",
            "lead_indicator": "[구간 A 선행지표 후보]",
            # 탭1 분모 후보 3개 (당일 확정 전 후보군)
            "denominator_candidates": ["[분모 후보 A-1]", "[분모 후보 A-2]", "[분모 후보 A-3]"],
            # S1 이벤트 매핑 행 = 구간 여정 단계 (5~8개 권장, 순서 = 실제 여정 순서)
            "s1_stages": [
                "[A 단계 1]", "[A 단계 2]", "[A 단계 3]", "[A 단계 4]",
                "[A 단계 5]", "[A 단계 6]", "[A 단계 7]", "[구간 A 핵심 전환]",
            ],
            # S9 선행지표 상관성 검증 행 (선행지표 / 연결 KPI / 상관 / 시차 보정 / 판정)
            "s9_rows": [
                ["[구간 A 선행지표 후보]", "[구간 A 핵심지표]", "", "1/2/4주 시차 재계산 예정", UNVERIFIED],
            ],
        },
        {
            "key": "B",
            "sheet_title": "3_구간B_분석",
            "name": "[구간 B명]",
            "owners": "[구간 B 담당]",
            "kpi_name": "[구간 B 핵심지표]",
            "kpi_line": (
                "핵심 KPI: [구간 B 핵심지표]  /  선행지표 후보: [구간 B 선행지표 후보] "
                f"— 고객사 가정, 상관성은 {DAY_VERIFY}에 검증"
            ),
            "lead_indicator": "[구간 B 선행지표 후보] — 고객사 가정",
            "denominator_candidates": ["[분모 후보 B-1]", "[분모 후보 B-2]", "[분모 후보 B-3]"],
            "s1_stages": [
                "[B 단계 1]", "[B 단계 2]", "[B 단계 3]", "[B 단계 4]",
                "[B 단계 5]", "[B 단계 6]", "[B 단계 7]", "[최종 KPI 전환]",
            ],
            "s9_rows": [
                ["[구간 B 선행지표 후보]", "[구간 B 핵심지표]", "", "", UNVERIFIED],
            ],
        },
    ],
}

# ═══════════════════════════════════════════════════════════════════════════
#  이 아래는 고객사별 수정 불필요 (구조 = 06_workshop-sheet-spec.md)
# ═══════════════════════════════════════════════════════════════════════════

AXES = CONFIG["axes"]
assert len(AXES) == 2, "이 스크립트는 2구간(A/B) 구조를 전제한다. 구간 수를 바꾸려면 스펙 문서 먼저 수정."
AX_A, AX_B = AXES
SEG_A, SEG_B = CONFIG["segment_axes"]
TOOL = CONFIG["analytics_tool"]
VALUE_LABEL = CONFIG["conversion_value_label"]
TMP_SHEET_ID = 999


def gws(args, body=None, params=None, check=True):
    """gws CLI 호출 — 원형과 동일한 --params / --json 패턴."""
    cmd = ["gws"] + args
    if params is not None:
        cmd += ["--params", json.dumps(params, ensure_ascii=False)]
    if body is not None:
        cmd += ["--json", json.dumps(body, ensure_ascii=False)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("[중단] gws CLI를 찾을 수 없습니다. 설치·인증 후 다시 실행하세요.")
        sys.exit(1)
    if r.returncode != 0:
        if not check:
            return None
        print("STDERR:", r.stderr[:3000])
        print("STDOUT:", r.stdout[:2000])
        sys.exit(1)
    out = r.stdout
    idx = out.find("{")
    return json.loads(out[idx:]) if idx >= 0 else {}


def resolve_spreadsheet_id():
    """CONFIG['ssid']가 있으면 그대로, 없으면 새로 만들고 ID를 출력한다."""
    if CONFIG["ssid"]:
        return CONFIG["ssid"]
    title = f'{CONFIG["client_name"]} {CONFIG["workshop_title"]} 워크스페이스'
    res = gws(["sheets", "spreadsheets", "create"],
              body={"properties": {"title": title}}, check=False)
    ssid = (res or {}).get("spreadsheetId")
    if not ssid:
        print("[중단] 새 스프레드시트 생성에 실패했습니다.")
        print("       구글시트를 직접 하나 만든 뒤, URL의 시트 ID를")
        print("       CONFIG[\"ssid\"] 에 넣고 다시 실행하세요.")
        print("       (URL 형태: https://docs.google.com/spreadsheets/d/<이 부분이 ID>/edit)")
        sys.exit(1)
    print("새 스프레드시트를 만들었습니다. 아래 ID를 CONFIG[\"ssid\"]에 넣어두세요:")
    print("  ", ssid)
    return ssid


PURPLE = {"red": 0.91, "green": 0.89, "blue": 0.95}
DARK = {"red": 0.16, "green": 0.10, "blue": 0.30}
YELLOW = {"red": 1.0, "green": 0.95, "blue": 0.80}
GRAY = {"red": 0.95, "green": 0.95, "blue": 0.95}
HEADER = {"red": 0.85, "green": 0.85, "blue": 0.90}
WHITE = {"red": 1, "green": 1, "blue": 1}

TAB_COLORS = {
    "0_HOME": {"red": 0.4, "green": 0.3, "blue": 0.6},
    "1_공통퍼널_분모": {"red": 0.5, "green": 0.5, "blue": 0.5},
    "2_구간A_분석": {"red": 0.2, "green": 0.4, "blue": 0.8},
    "3_구간B_분석": {"red": 0.1, "green": 0.6, "blue": 0.4},
    "4_영역선정_순위": {"red": 0.9, "green": 0.6, "blue": 0.1},
    "5_정의서": {"red": 0.7, "green": 0.3, "blue": 0.3},
    "6_골트리_NSM": {"red": 0.3, "green": 0.3, "blue": 0.3},
    "7_프롬프트_가이드": {"red": 0.6, "green": 0.6, "blue": 0.9},
}


class TabBuilder:
    """행을 순서대로 쌓으면서 서식 대상 행 인덱스를 함께 기록한다.

    add()는 추가된 행의 0-based 인덱스를 반환한다. 위치 의존 인덱스
    (`header_rows[1]` 같은 것) 대신 anchor= 로 이름을 붙여 쓴다.
    """

    def __init__(self, sheet_id, title):
        self.sid = sheet_id
        self.title = title
        self.rows = []
        self.title_rows = []
        self.section_rows = []
        self.header_rows = []
        self.yellow = []
        self.gray = []
        self.anchors = {}

    def add(self, row=None, kind=None, yellow_cols=None, gray_cols=None, anchor=None):
        i = len(self.rows)
        self.rows.append(row or [])
        if kind == "title":
            self.title_rows.append(i)
        elif kind == "section":
            self.section_rows.append(i)
        elif kind == "header":
            self.header_rows.append(i)
        if yellow_cols:
            for c in yellow_cols:
                self.yellow.append((i, c))
        if gray_cols:
            self.gray.append((i, gray_cols[0], gray_cols[1]))
        if anchor:
            self.anchors[anchor] = i
        return i

    def blank(self, n=1):
        for _ in range(n):
            self.rows.append([])

    def anchor(self, name):
        return self.anchors[name]


# ==================== 탭 0 HOME ====================
t0 = TabBuilder(0, "0_HOME")
t0.add([f'{CONFIG["client_name"]} {CONFIG["workshop_title"]} — 진행 현황 ({CONFIG["day_workshop_label"]})'], "title")
t0.blank()
t0.add(["■ 사용 규칙 (전원 필독)"], "section")
t0.add(["1. 시트가 정본입니다 — 클로드 창은 스크래치. 각 카드의 마지막 TSV 블록만 시트에 붙입니다."])
t0.add(["2. 클로드 출력은 \"헤더 포함, 탭 구분 TSV\"로 받아 붙입니다. 안 되면 붙인 뒤 [데이터 > 텍스트를 열로 분리]."])
t0.add([f'3. 자기 구간 탭만 편집합니다 (구간 {AX_A["key"]} 담당 → {AX_A["sheet_title"]} / '
        f'구간 {AX_B["key"]} 담당 → {AX_B["sheet_title"]}). 공용 탭 기록은 코치·기록 담당이 합니다.'])
t0.add(["4. 노란 셀만 입력, 회색 셀은 수식(덮어쓰기 금지). Gap은 %p가 아니라 배수로 씁니다. 정렬·필터 사용 금지."])
t0.blank()
t0.add(["■ 정본 공식"], "section")
t0.add(["영역 임팩트 ≈ (그 영역을 경험하는 사용자 수) × (그 영역의 개선 Gap)      /      Gap 배수 = 벤치마크 전환율 ÷ 현재 전환율"])
t0.add([f'기회손실 3식:  ① 개선 대상 인원 = 트래픽 × (목표 전환율 − 현재 전환율)   '
        f'② 증분 전환 수 = ① × 이후 퍼널 잔여 전환율   ③ 금액 = ② × {VALUE_LABEL} × 기간 배수'])
t0.add(["임팩트 4렌즈 = 볼륨 · 누수 · Gap · 비용(CAC)"])
t0.blank()
t0.add(["■ 데이터 소스 판별 (블록 2 시작 15분 내 — 실패 시 분석 카드 부록 B 백업 경로로 전환)"], "section")
t0.add(["구간", "판별 결과 (MCP 정상 / 백업 전환)", "판별 시각", "비고"], "header", anchor="datasource_header")
for i, ax in enumerate(AXES):
    t0.add([f'구간 {ax["key"]}', "", "", CONFIG["backup_label_note"] if i == 0 else ""], yellow_cols=[1, 2])
t0.add(["데이터 최신 날짜 (카드 0-1)", "", "", "최근 4주 완전주 기간도 함께"], yellow_cols=[1, 2])
t0.blank()
t0.add(["■ 라이브 기록지 (코치/기록 담당 기입)"], "section")
t0.add(["항목", f'구간 {AX_A["key"]} 상태', f'구간 {AX_B["key"]} 상태', "비고"], "header")
for _item, _note in [
    ("분모 확정", "탭1에서 — 공통"),
    ("목표(핵심지표)", ""),
    ("선행지표", ""),
    ("상관성 판정", f'{CONFIG["day_workshop_label"]}에는 \'미확인\' 기본'),
    ("문제 근거(정성)", "정성 카드 인용 1건+"),
    ("영향 사용자 규모", ""),
    ("개선 여지(Gap 배수)", ""),
    ("선정 근거 3줄", ""),
    ("골트리 완성 여부", "탭6 — 공통"),
    ("북극성 지표 논의", "결론 미확정 시 다음 일정 기재"),
    ("보류 항목 + 담당 + 마감일", "가설 백로그 워크숍 전까지 해소"),
]:
    t0.add([_item, "", "", _note])
t0.blank()
t0.add(["■ 파킹랏 — 계측 공백 / 정성조사 필요 / 보류 항목"], "section")
t0.add(["유형", "내용", "발견 위치(카드/탭)", "담당", "마감일"], "header")
for _ in range(10):
    t0.add(["", "", "", "", ""])

# ==================== 탭 1 공통퍼널_분모 ====================
t1 = TabBuilder(1, "1_공통퍼널_분모")
t1.add(["공통 퍼널과 분모 확정 — 블록 2 시작 5분 (다른 논의보다 먼저)"], "title")
t1.blank()
t1.add(["■ 구간별 목표지표 분모 확정 (분모가 다르면 이후 모든 Gap·기회손실 계산이 갈립니다)"], "section")
t1.add(["목표지표", "분모 후보 1", "분모 후보 2", "분모 후보 3", "당일 확정", "확정 근거 (카드 2-2 결과)"],
       "header", anchor="denominator_header")
for ax in AXES:
    cands = (list(ax["denominator_candidates"]) + ["", "", ""])[:3]
    t1.add([f'{ax["key"]}. {ax["kpi_name"]}'] + cands + ["", ""], yellow_cols=[4, 5])
t1.blank()
t1.add(["■ 최종 KPI까지 전체 여정 퍼널 — 카드 1-1 결과로 숫자만 채움 (단계 행 순서 변경 금지)"], "section")
t1.add(["여정 단계", "매핑 이벤트명 (카드 0-2)", "도달 사용자 수(월)", "전 단계 대비 %", "첫 단계 대비 %", "데이터 출처"], "header")
for _stage in CONFIG["journey_funnel_stages"]:
    t1.add([_stage, "", "", "", "", ""])


# ==================== 탭 2/3 구간 분석 ====================
def build_axis(sheet_id, ax):
    t = TabBuilder(sheet_id, ax["sheet_title"])
    t.add([f'구간 {ax["key"]} 분석 — {ax["name"]} (담당: {ax["owners"]})'], "title")
    t.add([ax["kpi_line"]])
    t.add(["※ 맨 오른쪽 K열부터는 RAW 붙여넣기 존 — 정리 전 클로드 원출력은 그쪽에 버립니다. 섹션 표 아래 버퍼 3행을 침범하지 않게 붙이세요."])
    raw_row = len(t.rows)          # 아래 blank()가 채울 행 — RAW 존 라벨 자리
    t.blank()

    t.add(["S1. 이벤트 매핑 (카드 0-2·0-3 — 헤더 포함 TSV를 아래 헤더 행에 겹쳐 붙이기. 여정 단계 행 순서 변경 금지)"], "section")
    t.add(["여정 단계", "1순위 이벤트", "확신도", "분해 가능 축", "주의 1줄"], "header", anchor="s1_header")
    for s in ax["s1_stages"]:
        t.add([s, "", "", "", ""])
    t.blank(3)

    t.add(["S2. 퍼널 Depth 3 (카드 1-1·2-1 — 6열 TSV. 재현용 쿼리 조건 2열 TSV는 RAW 존에)"], "section")
    t.add(["단계", "도달 수", "전 단계 대비", "첫 단계 대비", "이탈률", "이탈 인원"], "header", anchor="s2_header")
    for _ in range(8):
        t.add(["", "", "", "", "", ""])
    t.add(["분모 정의 1문장:", ""], yellow_cols=[1])
    t.blank(3)

    t.add(["S3. 코호트 분해 (카드 1-2 — '분해 축' 열이 붙은 단일 TSV)"], "section")
    t.add(["분해 축", "코호트", "진입자 수", "전체 대비 비중", "최종 전환율", "전체 평균 대비 배수"], "header", anchor="s3_header")
    for _ in range(10):
        t.add(["", "", "", "", "", ""])
    t.blank(3)

    t.add(["S4. 모집단 분리 판정 (카드 2-2 — 4행 고정. 결과를 탭1 '확정 근거' 칸에도 옮깁니다)"], "section")
    for label in ["신규 코호트 전환율", "기존 유저 재진입 수", "합산 시 차이 (배수)",
                  "판정 1문장 (현행 지표는 어느 쪽인가)"]:
        t.add([label, ""], yellow_cols=[1])
    t.blank(3)

    t.add([f"S5. {SEG_A}/{SEG_B} 갭 검증 (카드 2-3 — A블록: '기준' 열 단일 TSV / B블록: 아래 2행)"], "section")
    t.add(["기준", "단계", f"{SEG_A} 전환율", f"{SEG_B} 전환율", "갭(배수)", f"{SEG_A} 인원"],
          "header", anchor="s5_header")
    for _ in range(8):
        t.add(["", "", "", "", "", ""])
    t.add(["갭 최대 구간", ""], yellow_cols=[1])
    t.add(["원인 판별 (행동/계측/믹스)", ""], yellow_cols=[1])
    t.blank(3)

    t.add(["S6. 벤치마크 (카드 4-1 — A블록: 4행 고정 / B블록: 대표 벤치마크 3행)"], "section")
    t.add(["순위", "소스", "벤치마크 값", "분모 정의", "신뢰도", "주의 1줄"], "header", anchor="s6_header")
    for i in range(4):
        t.add([str(i + 1), "", "", "", "", ""])
    t.add(["대표 벤치마크 (카드 4-1 B블록 — 항목/내용 2열)"], "header")
    for label in ["대표 벤치마크 값", "소스", "선정 사유"]:
        t.add([label, ""], yellow_cols=[1])
    t.blank(3)

    t.add(["S7. Gap 배수 (카드 4-2 — 7열 TSV를 A열에 붙이면 H열 수식이 배수를 자동 계산. 교차검증 값과 다르면 분모부터 의심)"], "section")
    hdr = t.add(["후보 구간", "기준", "현재 전환율", "벤치마크", "진입자 수", "분모 일치 여부",
                 "Gap 배수(교차검증)", "Gap 배수(자동·수식)"], "header", anchor="s7_header")
    for k in range(8):
        r = hdr + 2 + k          # 1-based 시트 행 번호
        t.add(["", "", "", "", "", "", "",
               f"=IF(OR(C{r}=\"\",D{r}=\"\"),\"\",ROUND(D{r}/C{r},2))"], gray_cols=(7, 7))
    t.add(["해석 (한 문장 — \"전체 기준 ○배, 코호트 기준 △배\")", ""], yellow_cols=[1])
    t.blank(3)

    t.add(["S8. 기회손실 계산기 (카드 4-3 — A블록 TSV를 아래 헤더 행에 겹쳐 붙이기. 시나리오는 수식이 자동 계산)"], "section")
    t.add(["입력값 항목", "값", "출처", "가정"], "header", anchor="s8_input_header")
    base = len(t.rows) + 1       # 첫 입력 행의 1-based 시트 행 번호
    for label, note in [
        ("영역 트래픽(월)", ""),
        ("현재 전환율", ""),
        ("대표 벤치마크", "S6 대표 선택과 일치"),
        ("이후 퍼널 잔여 전환율", "개선 지점 이후 단계들의 곱"),
        (VALUE_LABEL, ""),
    ]:
        t.add([label, "", "", note], yellow_cols=[1, 2, 3])
    t.add(["기간 배수 (카드 TSV 밖 — 수동. 기본 1, 배수 사용 시 가정 칸에 '미검증 가정')", "1", "", ""],
          yellow_cols=[1, 3])
    TR, CU, BM, RES, VAL, MUL = base, base + 1, base + 2, base + 3, base + 4, base + 5
    t.blank()
    t.add(["시나리오 (자동)", "목표 전환율", "개선 대상 인원(월)", "증분 전환 수(월)", "증분 가치(월, 원)", "연환산(원)"],
          "header", anchor="s8_scenario_header")
    scen = [
        ("보수 (Gap의 1/3) — 대표값",
         f"=IF(OR($B${CU}=\"\",$B${BM}=\"\"),\"\",ROUND($B${CU}+($B${BM}-$B${CU})/3,2))"),
        ("중도 (Gap의 1/2)",
         f"=IF(OR($B${CU}=\"\",$B${BM}=\"\"),\"\",ROUND($B${CU}+($B${BM}-$B${CU})/2,2))"),
        ("낙관 (벤치마크 도달)",
         f"=IF($B${BM}=\"\",\"\",$B${BM})"),
    ]
    for label, tf in scen:
        r = len(t.rows) + 1
        t.add([label, tf,
               f"=IF(OR($B${TR}=\"\",B{r}=\"\"),\"\",ROUND($B${TR}*(B{r}-$B${CU})/100,0))",
               f"=IF(OR(C{r}=\"\",$B${RES}=\"\"),\"\",ROUND(C{r}*$B${RES}/100,0))",
               f"=IF(OR(D{r}=\"\",$B${VAL}=\"\"),\"\",ROUND(D{r}*$B${VAL}*IF($B${MUL}=\"\",1,$B${MUL}),0))",
               f"=IF(E{r}=\"\",\"\",E{r}*12)"], gray_cols=(1, 5))
    t.add(["(대조용) 클로드 계산 3시나리오 — 카드 4-3 B블록 TSV를 아래 헤더 행에 겹쳐 붙이기. "
           "위 수식 결과와 다르면 입력값을 의심하고 멈춥니다"], "header")
    t.add(["시나리오 (대조용)", "목표 전환율", "증분 전환수(월)", "연환산"], "header", anchor="s8_control_header")
    for _ in range(3):
        t.add(["", "", "", ""])
    t.blank(3)

    t.add([f'S9. {CONFIG["day_verify_label"]} 과제 — 선행지표 상관성 검증 '
           f'(카드 3-1~3-3 TSV 블록은 이 아래 빈 영역에 이어 붙입니다). '
           f'{CONFIG["day_workshop_label"]}에는 \'{UNVERIFIED}\'으로 둡니다'], "section")
    t.add(["선행지표", "연결 대상 KPI", "상관(자사 데이터)", "시차 보정", "판정"], "header", anchor="s9_header")
    for row in ax["s9_rows"]:
        t.add(list(row))
    for _ in range(4):
        t.add(["", "", "", "", ""])

    # RAW 존 라벨 — K열(인덱스 10)
    t.rows[raw_row] = t.rows[raw_row] + [""] * (10 - len(t.rows[raw_row])) + \
        ["RAW 붙여넣기 존 ↓ (정리 전 원출력·재현용 쿼리 조건)"]
    return t


axis_tabs = [build_axis(2 + i, ax) for i, ax in enumerate(AXES)]
t2, t3 = axis_tabs

# ==================== 탭 4 영역선정_순위 ====================
t4 = TabBuilder(4, "4_영역선정_순위")
t4.add(["영역 선정 — 순위표와 4렌즈 (블록 3 후반, 구간 교차 토론용 화면)"], "title")
t4.blank()
t4.add(["■ 후보 순위표 (교차 토론에서 코치가 정리 — 기회손실은 구간 탭 S8 '보수' 행 값. 실험 방향 확정은 가설 백로그 워크숍)"], "section")
t4.add(["순위", "구간", "후보 영역(퍼널 구간)", "타겟 세그먼트·코호트", "현재 전환율", "볼륨(월)",
        "기회손실(월, 보수)", "판정", "선정 사유(3줄)"], "header", anchor="rank_header")
for i in range(6):
    t4.add([str(i + 1), "", "", "", "", "", "", "", ""])
t4.blank()
t4.add([f'■ 임팩트 4렌즈 종합 (카드 5-1 A블록 — 7열 TSV를 A열에 붙이고, H열 \'구간\'만 손으로 '
        f'{AX_A["key"]}/{AX_B["key"]} 기입. \'선정\'은 구간당 최대 2행)'], "section")
t4.add(["후보 구간", "볼륨(명·월)", "이탈률", "이탈 인원", "Gap 배수", "비용 특성", "선정 여부",
        f'구간({AX_A["key"]}/{AX_B["key"]} 수동)'], "header", anchor="lens_header")
for _ in range(6):
    t4.add(["", "", "", "", "", "", "", ""])
t4.blank()
t4.add(["■ 제외 사유표 (카드 5-1 B블록 — 탈락 후보도 근거를 남깁니다)"], "section")
t4.add(["제외한 구간", "근거 데이터", "제외 사유"], "header", anchor="exclude_header")
for _ in range(4):
    t4.add(["", "", ""])
t4.blank()
t4.add([f'■ 세그먼트 유의성 5체크 (카드 5-1 C블록 — 현장 눈금, 정본 아님. '
        f'구간 {AX_A["key"]}는 A열에, 구간 {AX_B["key"]}는 E열에 각자 3열 TSV 붙여넣기)'], "section")
t4.add([f'[구간 {AX_A["key"]}] 체크 항목', "판정", "근거", "",
        f'[구간 {AX_B["key"]}] 체크 항목', "판정", "근거"], "header", anchor="significance_header")
SIGNIFICANCE_CHECKS = [
    "① 전체 대비 5~10% 이상 규모",
    "② 실험군/대조군 분리 가능",
    "③ 행동 기반 정의",
    "④ 반복 측정 시 같은 패턴",
    "⑤ 전략 설계 가능",
]
for c in SIGNIFICANCE_CHECKS:
    t4.add([c, "", "", "", c, "", ""])
t4.add(["현장 눈금(정본 아님)", "", "", "", "현장 눈금(정본 아님)", "", ""])
t4.blank()
t4.add([f'■ 토론 안건 (카드 5-2 — 2열 TSV 7행. 구간 {AX_A["key"]}는 A열에, 구간 {AX_B["key"]}는 D열에 붙여넣기)'], "section")
t4.add([f'[구간 {AX_A["key"]}] 섹션', "내용", "", f'[구간 {AX_B["key"]}] 섹션', "내용"], "header", anchor="agenda_header")
for s in ["결론 한 줄", "근거 3줄", "기회손실 (보수 기준)", "이 결론이 틀릴 수 있는 이유 3가지",
          "팀에 묻고 싶은 질문 3개", "정성조사가 필요한 것", "확정하지 못한 정의 목록"]:
    t4.add([s, "", "", s, ""])

# ==================== 탭 5 정의서 ====================
t5 = TabBuilder(5, "5_정의서")
t5.add(["문제영역 정의서 — 행: 항목 / 열: 구간 (각 담당은 자기 구간 열만 입력)"], "title")
t5.blank()
t5.add(["절", "항목", f'구간 {AX_A["key"]} 내용', f'{AX_A["key"]} 합의상태',
        f'구간 {AX_B["key"]} 내용', f'{AX_B["key"]} 합의상태', "보류 시 담당·마감"],
       "header", anchor="definition_header")
DEF_ITEMS = [
    ("0. 기본", "담당 2인", AX_A["owners"], "", AX_B["owners"], "", ""),
    ("0. 기본", "데이터 소스 (MCP 정상/백업 전환)", "", "", "", "", ""),
    ("1. 목표", "핵심지표", AX_A["kpi_name"], "", AX_B["kpi_name"], "", ""),
    ("1. 목표", "분모 (당일 확정 — 탭1과 일치)", "", "", "", "", ""),
    ("1. 목표", "관련 퍼널 구간", "", "", "", "", ""),
    ("1. 목표", "NSM과의 관계", "", "", "", "", ""),
    ("2. 선행지표", "관찰할 선행지표", AX_A["lead_indicator"], "", AX_B["lead_indicator"], "", ""),
    ("2. 선행지표", "선택 이유 (왜 지면과 가장 가까운가)", "", "", "", "", ""),
    ("3. 상관성", "선행지표→핵심 KPI 상관 (자사 데이터)", UNVERIFIED, "", UNVERIFIED, "", ""),
    ("3. 상관성", "판정 근거 ⚠️ 상관이 낮게 나오면 낙관 판정 금지 (수치·n·시점 그대로 기록)", "", "", "", "", ""),
    ("4. 정성 근거", "VOC/인터뷰 인용 최소 1건", "", "", "", "", ""),
    ("4. 정성 근거", "정량 결과와 같은 지점을 가리키는가", "", "", "", "", ""),
    ("5. 규모", "월간 사용자 수 / 전체 대비 비중", "", "", "", "", ""),
    ("5. 규모", f"코호트 분해 결과 ({SEG_A}·{SEG_B}/매체/신규기존)", "", "", "", "", ""),
    ("6. 개선 여지", "현재값 / 벤치마크(출처) / Gap 배수", "", "", "", "", ""),
    ("7. 선정 근거", "① 경험 사용자 수", "", "", "", "", ""),
    ("7. 선정 근거", "② 개선 Gap", "", "", "", "", ""),
    ("7. 선정 근거", "③ 전략적 사유 (비용/조직 우선순위)", "", "", "", "", ""),
]
for row in DEF_ITEMS:
    t5.add(list(row))
t5.blank()
t5.add(["■ 완료 판정 체크 (핵심 7개 — 채웠으면 O)"], "section")
t5.add(["체크 항목", f'구간 {AX_A["key"]}', f'구간 {AX_B["key"]}'], "header", anchor="completion_header")
COMPLETION_CHECKS = [
    "분해된 단위로 근거 제시 (전체 지표 아님)",
    "Gap을 배수로 표현 (%p 아님)",
    "상관성 확인 또는 '미확인' 정직 기록",
    "정성 근거 1건 이상",
    "벤치마크 분모가 우리와 같은지 확인",
    "트래픽 획득 비용 특성(CAC) 확인",
    "항목별 합의 상태 표기 완료",
]
for c in COMPLETION_CHECKS:
    t5.add([c, "", ""])
t5.blank()
t5.add(["■ 예상 임팩트 3시나리오 (구간 탭 S8 계산기 결과를 복사)"], "section")
t5.add(["시나리오", f'구간 {AX_A["key"]}: 목표 전환율 / 월간 증분 / 연환산',
        f'구간 {AX_B["key"]}: 목표 전환율 / 월간 증분 / 연환산'], "header")
for s in ["보수 (대표값)", "중도", "낙관"]:
    t5.add([s, "", ""])

# ==================== 탭 6 골트리_NSM ====================
t6 = TabBuilder(6, "6_골트리_NSM")
t6.add(["골트리 완성 + NSM 토론 (블록 4, 40분 — 전체 토론, 기록 담당 1인 타이핑)"], "title")
t6.blank()
t6.add(["■ 골트리 완성 조건 표 (빈칸이 하나라도 남으면 미완성. 상관성만 '미확인' 허용)"], "section")
t6.add(["구간", "목표 (지표+분모)", "선행지표", "상관성", "영향 사용자 규모",
        "개선 여지 (Gap 배수+소스)", "그래서 중요한 영역"], "header", anchor="goaltree_header")
for ax in AXES:
    t6.add([f'구간 {ax["key"]}', f'{ax["kpi_name"]} / 분모:', ax["lead_indicator"], UNVERIFIED, "", "", ""])
t6.blank()
t6.add(["■ NSM 후보 평가표 (각 칸 O/△/X — 실측 숫자를 본 뒤에 논의합니다)"], "section")
t6.add(["후보", "가치 정합성", "선행성", "측정 가능성", "단일성", "종합 판정", "근거 메모"],
       "header", anchor="nsm_header")
NSM_CANDIDATES = [
    "후보 1. 현행 북극성 지표 (유지)",
    f'후보 2. {AX_B["kpi_name"]} ※ 구간 {AX_B["key"]} 목표지표와 동일',
    "후보 3. [당일 제안]",
]
for c in NSM_CANDIDATES:
    t6.add([c, "", "", "", "", "", ""])
t6.add([CONFIG["correlation_caveat_note"]])
t6.blank()
t6.add(["■ NSM 결정 기록란 (비워두고 세션을 끝내지 않습니다 — 결론 미확정이면 '미확정 + 다음 논의 일정'을 적습니다)"], "section")
for label in ["선정된 NSM", "정의 (분자 / 분모 / 집계 단위)", "선정 사유 3줄", "탈락 후보와 탈락 사유", "재검토 시점"]:
    t6.add([label, ""], yellow_cols=[1])

# ==================== 탭 7 프롬프트_가이드 ====================
t7 = TabBuilder(7, "7_프롬프트_가이드")
t7.add(["클로드 프롬프트 가이드 — 복사해서 자기 클로드에 붙여넣으세요 (전체 카드: 분석 프롬프트 카드 문서 / 1페이지 요령: 참가자용 AI 가이드)"], "title")
t7.add(["공통 규칙 ① 결과는 반드시 \"위 표를 헤더 포함, 탭(tab) 문자로 구분된 TSV 코드블록으로만 다시 출력해줘\"로 받아 시트에 붙입니다  "
        "② 환각 방지: \"추정하지 말고 실제 쿼리 결과만 사용해줘. 실행이 실패하면 실패했다고 말해줘\"를 붙입니다  "
        "③ 헤더 포함 TSV는 시트의 해당 표 헤더 행에 겹쳐 붙입니다"])
t7.blank()
t7.add(["순서", "착지 위치", "무엇을 알아내는가", "복붙 프롬프트 (── [대괄호]는 치환 ──)", "믿기 전 확인", "막힐 때 재프롬프트"],
       "header", anchor="guide_header")
GUIDE_ROWS = [
    ["0", "0_HOME 데이터소스", "MCP 연결·데이터 최신성",
     f"연결된 {TOOL} 프로젝트 이름과, 데이터가 적재된 가장 최근 날짜를 알려줘. "
     f"실제 쿼리를 실행해서 확인하고, 최근 4주 완전주 기간도 제안해줘.",
     "최근 날짜가 이번 주인가 (아니면 코치 호출)",
     "응답 없으면 15분 내 백업 전환 — 코치 판단"],

    ["1", "구간 탭 S1", "여정 단계별 실제 이벤트명",
     f"우리 서비스의 [구간 {AX_A['key']}: {AX_A['name']} / 구간 {AX_B['key']}: {AX_B['name']}] 여정을 분석하려고 해. "
     f"다음 여정 단계 각각에 해당하는 {TOOL} 이벤트를 찾아줘: [시트 S1의 단계 전부 붙여넣기]. "
     f"단계별로 1순위 이벤트·확신도(상/중/하)·분해 가능 축(신규기존/채널/{SEG_A}·{SEG_B})·주의 1줄을 정리해줘. "
     "후보가 없는 단계는 '후보 없음'으로 정직하게 표시해줘. "
     "마지막에 여정 단계/1순위 이벤트/확신도/분해 가능 축/주의 1줄 5열 헤더 포함 탭 구분 TSV로 출력해줘 (단계 순서 그대로).",
     "이벤트 정의를 되물어 확인 (\"이 이벤트는 언제 찍히는 거야?\")",
     "이벤트명에 [핵심 키워드]가 포함된 이벤트를 모두 나열해줘"],

    ["2", "구간 탭 S2", "퍼널 단계별 전환·이탈",
     "최근 4주 완전주 기준으로, [S1에서 확정한 이벤트 순서]로 퍼널 분석을 실행해줘. "
     "단계/도달 수/전 단계 대비/첫 단계 대비/이탈률/이탈 인원 6열 헤더 포함 탭 구분 TSV로 출력하고, "
     "이 퍼널의 분모(첫 단계 모집단) 정의를 1문장으로 따로 말해줘. "
     "재현용 쿼리 조건(기간·플랫폼·세그먼트·전환 윈도우)은 항목/값 2열 TSV로 따로.",
     "분모 확인 · 도달 수가 단계마다 감소하는가",
     "방금 쿼리의 조건(기간·필터·분모)을 그대로 보여줘"],

    ["3", "구간 탭 S3", "코호트별 차이",
     "위 퍼널의 목표 전환율을 신규·기존 / 유입 채널 / 플랫폼 세 축으로 각각 분해한 뒤, "
     "맨 앞에 '분해 축' 열을 붙여 하나의 표로 합쳐줘. "
     "분해 축/코호트/진입자 수/전체 대비 비중/최종 전환율/전체 평균 대비 배수 6열 헤더 포함 탭 구분 TSV로 출력해줘.",
     "코호트 합 ≒ 전체인지 검산",
     "비중이 5% 미만인 코호트는 '기타'로 묶어줘"],

    ["4", "구간 탭 S4 + 탭1 확정근거", "모집단 혼입 검증",
     "[목표지표]의 분자에 기존 유저 재방문(CRM 리터치)이 섞여 있는지 확인하고 싶어. "
     "신규 코호트만의 전환율 / 기존 유저 재진입 수 / 합산 시 차이(배수) / "
     "'현행 지표는 어느 쪽 모집단인가' 판정 1문장 — 항목/값 2열 TSV 4행으로 정리해줘.",
     "전환율이 100%를 넘는 기간이 하나라도 있으면 모집단 혼입 확정 — 그 지표는 그대로 쓰지 않습니다",
     "신규의 정의를 '해당 기간 첫 설치/첫 방문'으로 고정하고 다시 계산해줘"],

    ["5", "구간 탭 S5", f"{SEG_A}/{SEG_B} 갭",
     f"퍼널 각 단계를 {SEG_A}와 {SEG_B}로 나눠 전체 기준과 신규 코호트 기준 두 가지로 비교해줘. "
     f"맨 앞에 '기준' 열을 붙여 기준/단계/{SEG_A} 전환율/{SEG_B} 전환율/갭(배수)/{SEG_A} 인원 "
     "6열 헤더 포함 탭 구분 TSV 하나로 합쳐 출력하고, "
     "'갭 최대 구간'과 '원인 판별(행동/계측/믹스)' 2행을 항목/내용 2열 TSV로 따로 출력해줘.",
     "한쪽이 99% 같은 극단값이면 모집단 혼입 의심 — 상한으로 삼지 않기",
     f"{SEG_B}만 따로, 신규 사용자 기준으로 다시 계산해줘"],

    ["6", "구간 탭 S6", "벤치마크 후보",
     "[목표 전환율]의 벤치마크 후보를 정리해줘. 우선순위 ①자사 인접 세그먼트 ②자사 과거 시점 ③업계 리포트 ④경쟁사 관측치. "
     "순위/소스/벤치마크 값/분모 정의/신뢰도/주의 1줄 6열 헤더 포함 TSV 4행 고정(확보 못 한 순위는 '확보 필요')으로 출력하고, "
     "대표 벤치마크 1개를 대표 벤치마크 값/소스/선정 사유 — 항목/내용 2열 TSV 3행으로 따로 출력해줘.",
     "벤치마크의 분모가 우리와 같은 정의인지",
     "자사 데이터 안에서 이 구간 전환율이 가장 높은 코호트를 찾아줘"],

    ["7", "구간 탭 S7", "Gap 입력값",
     "문제영역 후보 구간별로 Gap 계산 입력값을 정리해줘. 후보마다 '전체' 행과 편차가 컸던 코호트 행을 각각 만들어, "
     "후보 구간/기준/현재 전환율/벤치마크/진입자 수/분모 일치 여부/Gap 배수(교차검증) 7열 헤더 포함 탭 구분 TSV로 출력해줘. "
     "최종 배수는 시트 수식이 계산하니 네 배수는 교차검증 열에만. "
     "마지막에 \"전체 기준 ○배, [코호트] 기준 △배\" 한 문장.",
     "분모 일치 여부에 '불일치'가 있으면 그 행은 무효 · 시트 자동 배수와 교차검증이 같은지",
     "현재 전환율과 벤치마크 각각의 분모에 어떤 사용자가 포함되는지 다시 말해줘"],

    ["8", "구간 탭 S8", "기회손실 입력값 5개",
     "선정한 문제영역 [구간명]의 기회손실 계산 입력값 5개를 정리해줘: "
     f"영역 트래픽(월) → 현재 전환율 → 대표 벤치마크 → 이후 퍼널 잔여 전환율(개선 지점 이후 단계들의 곱) → {VALUE_LABEL}. "
     "입력값 항목/값/출처/가정 4열 헤더 포함 탭 구분 TSV 5행 고정으로 출력해줘 "
     "(출처 불명이면 '출처 불명', 기간 배수를 썼으면 가정에 '미검증 가정'). "
     "금액 계산은 시트가 하고, 네가 계산한 보수/중도/낙관은 시나리오/목표 전환율/증분 전환수(월)/연환산 4열 (대조용) TSV로 따로.",
     "잔여 전환율의 구간 정의가 맞는지 · 시트 수식과 대조용 값이 같은지 (다르면 멈춤)",
     "잔여 전환율은 [구간 다음 단계]→[최종 전환] 퍼널로 다시 뽑아줘"],

    ["9", "탭4", "구간 결론 요약 (카드 5-1·5-2)",
     "지금까지의 분석으로 ① 4렌즈 종합표(후보 구간/볼륨/이탈률/이탈 인원/Gap 배수/비용 특성/선정 여부 — '선정' 최대 2행) "
     "② 제외 사유표(제외한 구간/근거 데이터/제외 사유) "
     "③ 세그먼트 유의성 5체크(체크 항목/판정 O·X·미확인/근거) "
     "④ 토론 안건 7행(결론 한 줄/근거 3줄/기회손실 보수/틀릴 수 있는 이유 3/묻고 싶은 질문 3/정성조사 필요/미확정 정의 — 섹션/내용 2열)"
     "을 각각 헤더 포함 탭 구분 TSV 코드블록으로 출력해줘.",
     "'틀릴 수 있는 이유'가 비어 있으면 재요청",
     "각 섹션을 2문장 이내로 줄여줘"],
]
for row in GUIDE_ROWS:
    t7.add(row)
t7.blank()
t7.add(["15분 룰: 한 지점에서 15분 이상 막히면 코치를 호출하세요. 완벽한 숫자보다 '출처가 명확한 숫자'가 우선입니다."])

tabs = [t0, t1] + axis_tabs + [t4, t5, t6, t7]


# ==================== 재구축: 탭 삭제 후 재생성 (URL 유지) ====================
def main():
    ssid = resolve_spreadsheet_id()

    meta = gws(["sheets", "spreadsheets", "get"], params={"spreadsheetId": ssid}, check=False)
    if meta and meta.get("sheets"):
        existing = [s["properties"]["sheetId"] for s in meta["sheets"]]
    else:
        existing = [t.sid for t in tabs]     # 조회 실패 시 킷 표준 탭 구성을 가정

    req = [{"addSheet": {"properties": {"sheetId": TMP_SHEET_ID, "title": "_tmp"}}}]
    for sid in existing:
        if sid != TMP_SHEET_ID:
            req.append({"deleteSheet": {"sheetId": sid}})
    for t in tabs:
        req.append({"addSheet": {"properties": {
            "sheetId": t.sid, "title": t.title,
            "tabColor": TAB_COLORS.get(t.title, {"red": 0.5, "green": 0.5, "blue": 0.5}),
            "index": t.sid,
            "gridProperties": {"rowCount": max(150, len(t.rows) + 20), "columnCount": 14}}}})
    req.append({"deleteSheet": {"sheetId": TMP_SHEET_ID}})
    gws(["sheets", "spreadsheets", "batchUpdate"], params={"spreadsheetId": ssid}, body={"requests": req})
    print("tabs rebuilt")

    # ==================== 값 입력 ====================
    data = [{"range": f"'{t.title}'!A1", "majorDimension": "ROWS",
             "values": [r if r else [""] for r in t.rows]} for t in tabs]
    gws(["sheets", "spreadsheets", "values", "batchUpdate"], params={"spreadsheetId": ssid},
        body={"valueInputOption": "USER_ENTERED", "data": data})
    print("values written")

    # ==================== 서식·검증·보호 ====================
    req = []

    def fmt(sid, r1, r2, c1, c2, bg=None, bold=False, fg=None, wrap=None):
        cell = {"userEnteredFormat": {}}
        f = []
        if bg:
            cell["userEnteredFormat"]["backgroundColor"] = bg
            f.append("userEnteredFormat.backgroundColor")
        tf = {}
        if bold:
            tf["bold"] = True
        if fg:
            tf["foregroundColor"] = fg
        if tf:
            cell["userEnteredFormat"]["textFormat"] = tf
            f.append("userEnteredFormat.textFormat")
        if wrap:
            cell["userEnteredFormat"]["wrapStrategy"] = wrap
            f.append("userEnteredFormat.wrapStrategy")
        req.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2,
                                             "startColumnIndex": c1, "endColumnIndex": c2},
                                   "cell": cell, "fields": ",".join(f)}})

    for t in tabs:
        for i in t.title_rows:
            fmt(t.sid, i, i + 1, 0, 10, bg=DARK, bold=True, fg=WHITE)
        for i in t.section_rows:
            fmt(t.sid, i, i + 1, 0, 10, bg=PURPLE, bold=True)
        for i in t.header_rows:
            fmt(t.sid, i, i + 1, 0, 10, bg=HEADER, bold=True)
        for (r, c) in t.yellow:
            fmt(t.sid, r, r + 1, c, c + 1, bg=YELLOW)
        for (r, c1, c2) in t.gray:
            fmt(t.sid, r, r + 1, c1, c2 + 1, bg=GRAY)

    def width(sid, c1, c2, px):
        req.append({"updateDimensionProperties": {
            "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c1, "endIndex": c2},
            "properties": {"pixelSize": px}, "fields": "pixelSize"}})

    for t in tabs:
        width(t.sid, 0, 1, 240)
        width(t.sid, 1, 8, 160)
    width(t7.sid, 3, 4, 520)
    width(t7.sid, 1, 3, 150)
    width(t7.sid, 4, 6, 260)
    width(t5.sid, 1, 2, 300)
    width(t5.sid, 2, 3, 260)
    width(t5.sid, 4, 5, 260)
    fmt(t7.sid, 0, len(t7.rows), 0, 6, wrap="WRAP")
    fmt(t5.sid, 0, len(t5.rows), 0, 7, wrap="WRAP")

    def dropdown(sid, r1, r2, c1, c2, values):
        req.append({"setDataValidation": {
            "range": {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2,
                      "startColumnIndex": c1, "endColumnIndex": c2},
            "rule": {"condition": {"type": "ONE_OF_LIST",
                                   "values": [{"userEnteredValue": v} for v in values]},
                     "showCustomUi": True, "strict": False}}})

    # 탭5 정의서 — 구간별 합의상태 (D열 / F열)
    first_def = t5.anchor("definition_header") + 1
    dropdown(t5.sid, first_def, first_def + len(DEF_ITEMS), 3, 4, ["합의됨", "보류", "논의중"])
    dropdown(t5.sid, first_def, first_def + len(DEF_ITEMS), 5, 6, ["합의됨", "보류", "논의중"])
    # 탭5 완료 판정 체크 — O/X
    chk = t5.anchor("completion_header")
    dropdown(t5.sid, chk + 1, chk + 1 + len(COMPLETION_CHECKS), 1, 3, ["O", "X"])
    # 탭4 세그먼트 유의성 5체크 — O/X/미확인 (구간 A B열, 구간 B F열)
    sig = t4.anchor("significance_header")
    dropdown(t4.sid, sig + 1, sig + 1 + len(SIGNIFICANCE_CHECKS), 1, 2, ["O", "X", "미확인"])
    dropdown(t4.sid, sig + 1, sig + 1 + len(SIGNIFICANCE_CHECKS), 5, 6, ["O", "X", "미확인"])
    # 탭6 NSM 후보 평가 — O/△/X
    nsm = t6.anchor("nsm_header")
    dropdown(t6.sid, nsm + 1, nsm + 1 + len(NSM_CANDIDATES), 1, 6, ["O", "△", "X"])
    # 탭0 데이터 소스 판별 — MCP 정상/백업 전환
    ds = t0.anchor("datasource_header")
    dropdown(t0.sid, ds + 1, ds + 1 + len(AXES), 1, 2, ["MCP 정상", "백업 전환"])

    # 구간 탭 수식 셀 보호(경고) + 탭7 전체 보호(참조 전용)
    for t in axis_tabs:
        for (r, c1, c2) in t.gray:
            req.append({"addProtectedRange": {"protectedRange": {
                "range": {"sheetId": t.sid, "startRowIndex": r, "endRowIndex": r + 1,
                          "startColumnIndex": c1, "endColumnIndex": c2 + 1},
                "warningOnly": True, "description": "수식 — 덮어쓰기 주의"}}})
    req.append({"addProtectedRange": {"protectedRange": {
        "range": {"sheetId": t7.sid}, "warningOnly": True,
        "description": "프롬프트 가이드 — 참조 전용"}}})

    gws(["sheets", "spreadsheets", "batchUpdate"], params={"spreadsheetId": ssid}, body={"requests": req})
    print("formatting done —", len(req), "requests")

    for t in axis_tabs:
        print(t.title, "gray(수식) rows:", sorted(set(r + 1 for (r, _, _) in t.gray)))
    print("DONE. URL: https://docs.google.com/spreadsheets/d/" + ssid)


if __name__ == "__main__":
    main()
