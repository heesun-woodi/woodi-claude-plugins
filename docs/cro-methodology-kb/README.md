# CRO / Experimentation 방법론 지식베이스 (KB)

우디(Market Fit Lab)의 CRO 코칭용 방법론 레퍼런스. 코칭 주제가 정해지면 해당 챕터를 열어 세션 자료를 구성한다.
여러 코칭 자료를 정본 기준으로 통합했다. 공개판 — 고객 사례와 원본 출처 목록은 제외했습니다.

## CRO 실험 10단계 프로세스 맵

| 단계 | 내용 | 챕터 |
|---|---|---|
| 1 | **문제영역 선정** — 최종 KPI 임팩트 기준 정량분석(경험자 수 × 개선 gap). 지표 미정의 조직은 Goal Metric/NSM 선행 정의 | [01](01_problem-area-selection.md) |
| 2 | **문제정의 + Validation** — 사용자 언어로 문제정의, 진짜/비싼 문제 근거 → 문제 Impact 점수 → 문제 우선순위 | [02](02_problem-definition.md) |
| 3 | **솔루션 아이데이션 + Rationale** — 전술 기반 발산, Variant, 잘될 정량/정성 근거 | [03](03_solution-ideation.md) |
| 4 | **PSR 가설 한문장** — P·S 확정 + Result(선행지표) 목표수치 | [04](04_hypothesis-psr.md) |
| 5 | **ICE 우선순위 평가** — 합산식(최대 30점), QuickWin 규칙 | [05](05_prioritization-ice.md) |
| 6 | **실험 설계 + 설계서 작성** — 지표전략, 샘플사이즈·MDE·기간 | [06](06_experiment-design.md) |
| 7 | **세팅 → 테스트 → 런칭** — 구현 난이도 3레벨, QA | [07](07_setup-launch.md) |
| 8 | **모니터링** — No peeking, SRM 등 신뢰성 체크 | [08](08_monitoring-stopping.md) |
| 9 | **종료 의사결정** — 기간·샘플 도달·조기종료 기준 | [08](08_monitoring-stopping.md) |
| 10 | **결과분석 + 보고서** — 정량/정성 수집, 판정, 원인분석, 보고 | [09](09_analysis-reporting.md) |
| 10+ | **Implement 의사결정 + 학습** — Reforge 매트릭스, 실패학습, 후속가설 | [10](10_decision-learning.md) |

지원 레이어: [00 개요·실험문화](00_overview.md) · [11 스프린트 운영](11_sprint-operations.md) · [12 코칭 프로그램·조직](12_coaching-org.md) · [13 케이스(공개 사례)](13_cases.md)

실행 킷: [kits/problem-area-selection/](kits/problem-area-selection/README.md) — 실험영역(문제영역) 선정 워크숍 표준 킷 (01 챕터의 1일 워크숍 실행판: 골트리·분석 프롬프트 카드 19장·진행안·보고서 템플릿·참가자 가이드·구글시트 8탭 스펙+생성 스크립트. `[치환 변수]`를 고객사 브리프로 채워 배포)

## 핵심 확정 원칙

- **ICE = I + C + E (각 1~10, 최대 30점)**. QuickWin = ICE≥21 또는 (ICE≥15 & Ease≥8)
- **PSR의 Result = 해당 영역의 선행 반응 지표** (최종 KPI 아님). 선행지표→최종 KPI 연결은 Uplift 시뮬레이션
- **문제 우선순위 = 문제 Impact 점수** (진짜 문제 근거 × 비싼 문제 근거)
- 범용 챕터(00~12)는 고객사 실명·실수치 없음. 공개 자료 기반 사례는 13에 수록

## 코칭주제 → 챕터 매핑

### 코칭 점검 대상 5개 프로세스 (예)

| 점검 프로세스 | 1차 챕터 | 보조 챕터 |
|---|---|---|
| ① 사용자 문제를 정의하는 방법 | [02 문제정의·Validation](02_problem-definition.md) | [01 문제영역 선정](01_problem-area-selection.md) |
| ② 가설의 근거를 찾는 그루밍 방법 | [04 PSR 가설·그루밍](04_hypothesis-psr.md) | [02](02_problem-definition.md) (Validation 근거) |
| ③ 실험 솔루션을 근거 기반으로 도출하는 방법 | [03 솔루션 아이데이션·Rationale](03_solution-ideation.md) | [13 케이스](13_cases.md) (레퍼런스 뱅크) |
| ④ 가설 우선순위 평가 방법 | [05 ICE 우선순위](05_prioritization-ice.md) | [02](02_problem-definition.md) (문제 Impact→I 점수) |
| ⑤ 실험 결과 모니터링·결과 분석 방법 | [08 모니터링·종료](08_monitoring-stopping.md) · [09 결과분석·보고](09_analysis-reporting.md) | [10 의사결정·학습](10_decision-learning.md) |

### 자주 쓰는 코칭 주제별 진입점

| 코칭 주제 | 챕터 조합 |
|---|---|
| "어디를 실험해야 할지 모르겠다" (문제영역·지표 정의) | 01 → 02 |
| 가설이 약하다 / 근거가 없다 (가설 품질) | 02 → 04 → 05 |
| 가설 그루밍 워크샵 | 04 + 05 (+ 03 전술 라이브러리, 12의 워크샵 카탈로그·가설 정의 101 목차, [templates/](templates/) 실습 배포물) |
| 실험설계서 작성·리뷰 | 06 (+ 04 PSR, 05 ICE 근거) |
| 지표를 뭘로 잡아야 하나 (Primary/Guardrail/Secondary) | 06 지표전략 + 01 NSM |
| 샘플사이즈·실험 기간 산정 | 06 (+ 09 MDE) |
| 실험 세팅·QA·런칭 (Amplitude Experiment 포함) | 07 |
| "결과를 믿어도 되나" (통계 해석·신뢰성) | 08 + 09 (SRM·피킹·p-value·Bayesian) |
| 저트래픽·저빈도 실험 해석 | 09 + 13(G-6) |
| 결과보고서 작성·리뷰 | 09 + 10 |
| 이 실험, 반영할까 말까 (Implement 의사결정) | 10 |
| 스프린트가 안 돌아간다 (운영·R&R·주기) | 11 |
| 진단 인터뷰·사전질문지·커리큘럼 설계 (코치용) | 12 |
| 조직 설득·실험문화·성숙도 진단 | 00 + 12 |
| 세션에 쓸 사례가 필요하다 | 13 |
