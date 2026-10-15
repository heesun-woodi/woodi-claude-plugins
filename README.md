# woodi-claude-plugins

CRO(전환율 최적화)·그로스 코칭에서 쓰는 Claude Code 플러그인 모음입니다. 핵심은 비개발자 PM이 Claude와 1:1로 대화하며 **문제정의 → 가설 → 그루밍 → 실험설계 → 모니터링 → 종료 판단 → 결과 보고서**까지 한 흐름으로 진행하는 CRO 플러그인 5종이고, 이커머스 그로스 디스커버리와 네이버 정보성 블로그 자동화 플러그인, 그리고 이 플러그인들이 기대는 **CRO 방법론 KB**(`docs/cro-methodology-kb/`)를 함께 담았습니다.

각 플러그인은 단계마다 **하드 게이트**를 두어, 화면에 없는 요소나 측정하지 않은 수치를 Claude가 지어내지 못하게 합니다. 산출물은 표 이름·열 순서·공식이 고정된 **출력 계약**(`references/output-contract.md`)을 따릅니다.

## 설치

Claude Code에서:

```
/plugin marketplace add heesun-woodi/woodi-claude-plugins
/plugin install cro-problem-definition@woodi-claude-plugins
```

다른 플러그인도 `/plugin install {이름}@woodi-claude-plugins`로 설치합니다.

## 플러그인

### CRO 실험 흐름

| 순서 | 플러그인 | 하는 일 |
|---|---|---|
| 1 | `cro-problem-area-selection` | Amplitude 데이터로 실험할 문제영역 고르기 (퍼널 · 선행지표 · Gap × 트래픽) |
| 2 | `cro-problem-definition` | 화면 스크린샷으로 사용자 문제 정의 (BIAS 27항목 · CRO 체크리스트 · Impact) |
| 3 | `cro-hypothesis-backlog` | 솔루션 아이데이션 → PSR 가설 → 1차 ICE → 가설 백로그 |
| 4 | `cro-hypothesis-grooming` | 가설 근거 보강 (Problem Validation · Uplift · Target · Rationale) → ICE 재산정 |
| 5 | `cro-experiment-design` | 실험설계서 구체화 + 스킬 4개 동봉: 모니터링 · 종료 의사결정 · 결과 보고서 · AI variant 시안 초안 |

### 그로스·콘텐츠

| 플러그인 | 하는 일 |
|---|---|
| `ecommerce-growth-discovery` | GA4·Meta 광고 MCP로 자기 몰의 baseline·전환율·채널 효율을 탐색하고, 상품·랜딩 화면 문제를 정리해 PSR 가설과 ICE까지 만들기 (이커머스판 시작점) |
| `naver-blog-autopilot` | 네이버 정보성 블로그 글을 주제 리서치 → 초안 → 공신 출처 팩트체크 → SEO → 이미지·표지 → 임시저장까지 자동화. 업종 무관 — 업체 정보·금칙어·공신 출처는 `blog-setup`이 만드는 템플릿에 직접 채웁니다. 발행은 사람이 직접 합니다 |

## 필요한 것

- **Amplitude MCP** — 문제영역 선정·그루밍·모니터링에서 실데이터를 조회합니다.
  `claude mcp add --transport http amplitude https://mcp.amplitude.com/mcp` 후 OAuth 로그인 (EU 프로젝트는 `https://mcp.eu.amplitude.com/mcp`)
- (선택) AI 시안 초안 — Gemini 또는 OpenAI API 키. 없어도 나머지 기능은 모두 동작합니다.
- `ecommerce-growth-discovery` — uv, gcloud와 ADC(`analytics.readonly`), 조회할 GA4 속성의 뷰 권한. Meta 광고 연결은 선택입니다. 자세한 세팅은 플러그인 README를 보세요.
- `naver-blog-autopilot` — uv·Python 3.11+, Playwright Chromium, 외부 도구 [naver-blog-cli](https://github.com/spegas/naver-blog-cli)(MIT · 이 저장소에 포함하지 않음 · 별도 설치), 이미지 생성 API 키 1개(Gemini 또는 OpenAI). 자세한 세팅은 플러그인 README를 보세요.

## 동봉 데이터는 샘플입니다

골트리(`data/goal-tree-nodes.json`) 같은 동봉 데이터는 **가상 데모 서비스(보험 상담 앱)** 기준의 형식 샘플입니다. 실제 프로젝트에서는 같은 형식으로 자기 파일을 만들어 경로를 알려주세요. 샘플 수치는 실제 판단(Baseline·Target·지표 선택)에 쓰지 않으며, 실측값은 Amplitude 쿼리나 사용자 입력으로만 채웁니다.

## CRO 방법론 KB

`docs/cro-methodology-kb/`는 플러그인의 규칙(ICE 합산식·PSR·BIAS·샘플사이즈·판정 기준 등)이 나온 방법론 노트입니다. 00장(개요·실험문화)부터 10장(Implement 의사결정·학습)까지 CRO 실험 10단계를 따라가고, 11~13장은 스프린트 운영·코칭 프로그램·공개 사례를 다룹니다. `kits/problem-area-selection/`은 문제영역 선정 워크숍을 그대로 진행할 수 있는 킷(`[치환 변수]` 템플릿)이고, `templates/`에는 PSR 그루밍 워크시트·ICE 시트·Uplift 시뮬레이션 양식이 있습니다.

공개판에서는 고객 코칭 사례와 원본 출처 목록을 뺐습니다. 공개 자료로 확인한 사례와 참고 문헌만 남아 있습니다.

## 출력 계약 별칭

문서 본문은 계약을 짧은 이름으로 서로 가리킵니다. 실제 파일은 각 스킬의 `references/output-contract.md`입니다.

| 별칭 | 실제 파일 |
|---|---|
| `pa-output-contract.md` | `plugins/cro-problem-area-selection/skills/cro-problem-area-selection/references/output-contract.md` |
| `pd-output-contract.md` | `plugins/cro-problem-definition/skills/cro-problem-definition/references/output-contract.md` |
| `hb-output-contract.md` | `plugins/cro-hypothesis-backlog/skills/cro-hypothesis-backlog/references/output-contract.md` |
| `hg-output-contract.md` | `plugins/cro-hypothesis-grooming/skills/cro-hypothesis-grooming/references/output-contract.md` |
| `ed-output-contract.md` | `plugins/cro-experiment-design/skills/cro-experiment-design/references/output-contract.md` |
| `em-output-contract.md` | `plugins/cro-experiment-design/skills/cro-experiment-monitoring/references/output-contract.md` |
| `dc-output-contract.md` | `plugins/cro-experiment-design/skills/cro-experiment-decision/references/output-contract.md` |
| `er-output-contract.md` | `plugins/cro-experiment-design/skills/cro-experiment-report/references/output-contract.md` |

`wd-output-contract.md`(실험 결과 디브리프)는 별도 합성 리서치 플러그인의 계약으로, 이 저장소에는 포함되지 않습니다.

## 문서 안의 출처 표기

플러그인 본문의 `KB06`·`KB09 §③`·`cro-methodology-kb/0x_*.md` 같은 표기는 위 방법론 KB를 가리킵니다 — `KB06`은 `docs/cro-methodology-kb/06_experiment-design.md`, `KB09 §③`은 그 장의 ③절입니다. `Slides2 S10`·`온보딩101` 같은 표기는 코칭 교육 자료의 장 번호로, 이 저장소에는 포함되지 않습니다. 플러그인이 이 파일들을 실행 중에 읽지는 않으며, 규칙의 출처 표기로 남겨 두었습니다.

## 라이선스

© heesun-woodi · [CC BY-NC 4.0](LICENSE) — 출처를 표기하면 자유롭게 쓰고 고칠 수 있습니다. 상업적 이용(유료 서비스·판매 등)은 허용하지 않습니다.
