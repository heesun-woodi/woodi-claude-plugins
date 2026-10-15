# 참고 법령·기관

업종별 공신 출처(법령 DB·공공기관·업체 프로필)를 등록하는 곳입니다. fact-checker는 이 표에 있는 출처로 사실 주장을 확인합니다. `[치환 변수]`는 업종에 맞게 채웁니다.

| 번호 | 구분 | 이름 | URL |
|---|---|---|---|
| 1 | 법령 | [<법령명>] | 상세(사람용): https://www.law.go.kr/법령/<법령명> · API: `https://www.law.go.kr/DRF/lawService.do?OC=test&target=law&LM=<법령명>&type=XML` |
| 2 | 법령 | [<법령명> 시행규칙] | 상세(사람용): https://www.law.go.kr/법령/<법령명>시행규칙 · API: `https://www.law.go.kr/DRF/lawService.do?OC=test&target=law&LM=<법령명>시행규칙&type=XML` |
| 3 | 기관 | [소관 부처] | [기관 URL] |
| 4 | 기관 | [자격·인증·시험 시행 기관] | [기관 URL] |
| 5 | 기관 | [지원 제도 안내 기관] | [기관 URL] |
| 6 | 기관 | [민원·분쟁 사례 기관] | [기관 URL] |
| 7 | 업체 | 업체 프로필 | knowledge/business-profile.md (업체 정보·강점 주장의 출처) |

## 주장 유형 → 확인 출처

| 주장 유형 | 확인 출처 |
|---|---|
| 가격·수수료 | [공식 요금·수수료 안내 페이지] |
| 일정·기한 | [시행 기관 공지·일정 페이지] |
| 자격·요건 | [소관 법령·시행규칙(law.go.kr DRF API: `https://www.law.go.kr/DRF/lawSearch.do?OC=test&target=law&type=XML&query=<법령명>` → `https://www.law.go.kr/DRF/lawService.do?OC=test&target=law&MST=<법령일련번호>&type=XML`) + 소관 기관] |
| 법령·규정 | law.go.kr DRF API(아래 호출 방법) |
| 통계·수치 | [공공 통계·기관 발표 자료] |
| 업체 정보 | knowledge/business-profile.md |

## 접근성 기록

확인 일자: [YYYY-MM-DD]. 방법: `curl -sL -A "Mozilla/5.0" --max-time 20`. 상태 정의 - 본문 가능: curl 응답에 필요한 텍스트·표가 들어 있음 / 껍데기만: 200이지만 JS가 채우는 빈 틀 / 차단: 4xx·루프.

### 법령 API 호출 방법 (law.go.kr DRF, `OC=test`)

| 용도 | URL 템플릿 | 비고 |
|---|---|---|
| 법령 검색 | `https://www.law.go.kr/DRF/lawSearch.do?OC=test&target=law&type=XML&query=<법령명>` | `<법령일련번호>`(MST), `<시행일자>`, `<현행연혁코드>` 반환 |
| 법령 본문 (이름으로) | `https://www.law.go.kr/DRF/lawService.do?OC=test&target=law&LM=<법령명>&type=XML` | `LM=`은 시행 예정본을 반환할 수 있음 → `lawSearch.do`로 MST 확인 후 시행일자가 미래면 현행 MST로 재조회. 조문은 `<조문단위>`/`<조문내용>` |
| 법령 본문 (MST로) | `https://www.law.go.kr/DRF/lawService.do?OC=test&target=law&MST=<법령일련번호>&type=XML` | 특정 시점 판본 고정 시 |

응답은 `text/xml;charset=UTF-8`이다. 주의: MST와 시행일은 개정되면 바뀐다. 글에 법령을 인용할 때는 검색 응답의 `시행일자`를 같이 적는다.

### 출처별 접근성

| 출처 | URL | 상태 | 비고 (쓸 수 있는 주장 유형 / 안 될 때 대안) |
|---|---|---|---|
| law.go.kr DRF API | `https://www.law.go.kr/DRF/lawSearch.do?OC=test&target=law&type=XML&query=<법령명>` , `…/lawService.do?OC=test&target=law&LM=<법령명>&type=XML` | [확인 후 기록] | 법령 조문 인용. 단 `LM=`은 시행 예정본을 반환할 수 있음 → `lawSearch.do`로 MST 확인 후 시행일자가 미래면 현행 MST로 재조회 |
| law.go.kr 상세 페이지 | `https://www.law.go.kr/법령/<법령명>` | [확인 후 기록] | 독자에게 보여줄 링크로만 쓰고, 사실 확인은 위 API로 한다 |
| [출처 이름] | [URL] | [본문 가능 / 껍데기만 / 차단] | [쓸 수 있는 주장 유형 / 안 될 때 대안] |

### 주장 유형별 결론

- 법령 조문·규정: law.go.kr DRF API로 자동 확인 가능(가장 신뢰).
- [주장 유형]: [확인 가능한 출처와 방법, 단정하면 안 되는 조건]
- 일정·기한처럼 자주 바뀌는 값: 단정 금지, 「[기관]에서 최신 일정 확인」 문구 + 시점 명시, 필요하면 담당자 확인.
- 웹 팬/WebFetch에서 막히는 곳이 있어도 위 URL은 curl 기준 결과다. fact-checker가 WebFetch를 쓸 때 실패하면 curl(Bash)로 재시도한다.
