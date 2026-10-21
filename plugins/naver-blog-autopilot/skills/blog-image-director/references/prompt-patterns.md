# 프롬프트 패턴 — 블로그 AI 이미지

`scripts/gen_image.py`가 표의 프롬프트 앞뒤에 아래 공통 접두/접미를 **자동으로** 붙인다. 표의 `프롬프트` 칸에는 장면 설명만 쓴다(영어, 한 문장~두 문장, `|` 문자 금지).

## 공통 접두/접미 (gen_image.py `PROMPT_PREFIX`·`PROMPT_SUFFIX`와 글자 그대로 같아야 함)

- 접두: `photorealistic, Korean everyday scene, no text, no letters, no watermark, no close-up faces` — 접두의 장면구(`Korean everyday scene`)는 프로필 `이미지 기본 장면` 행의 영문 장면구로 바뀐다(행이 비면 이 기본값). `photorealistic`과 금지구는 고정.
- 접미: `natural light, wide landscape 3:2 composition, people only seen from behind or far away, no brand logos, no readable signs, no license plates, no numbers`

최종 프롬프트 = `<접두>. <장면 설명>. <접미>.` (`gen_image.build_prompt(scene, base_scene=None)`) — 둘 중 하나를 바꾸면 스크립트 상수도 함께 바꾼다(`tests/test_gen_image.py`가 대조한다).

## 장면 유형별 패턴

`{…}`는 글마다 바꾸는 변주 슬롯이다(아래 "변주 지침"). `{product}`·`{task}`·`{part}`는 글 주제에 맞는 사물·작업·부위를 영어로 채우는 자리다.

| # | 장면 유형 | 쓰는 슬롯(목적) | 패턴 |
|---|---|---|---|
| 1 | 매장·작업 공간 전경 | 표지(`00` 배경), 절차 장면 | `a tidy small shop interior with a workbench and neatly arranged shelves, {time}, {weather}, {angle}` (간판·상품 라벨 글자 없음) |
| 2 | 상담·안내 장면(멀리) | 이용 절차 절 요약 | `a staff member explaining something to a customer at a counter, both seen from behind or far away, {time}, {angle}` (두 사람 모두 뒷모습·원거리, 손에 든 종이에 글자 없음) |
| 3 | 제품·상품 | 제품·상품 소개, 종류 비교 | `a {product} placed on a clean wooden table in a bright room, {angle}, {time}` (로고·모델명 없음) |
| 4 | 작업 과정 | 중간 작업 장면(⑤에 현장 장면 규칙이 있으면 최소 1장) | `hands working on {task} at a workbench, person seen from behind, {angle}, {time}` / `a delivery cart being loaded in front of a shop entrance, {weather}` |
| 5 | 서류·준비물(글자 없이 추상화) | 신청·서류·요건 절 | `a neat desk with a blank card, a closed folder and a pen, soft {time} light, shallow depth of field, blank paper with no writing` |
| 6 | 안전·보호 장비 | 안전·준비물 절 | `gloved hands putting on protective gear next to a work area, {angle}` / `a person seen from behind wearing a safety vest walking toward a work area` |
| 7 | 점검·관리(선택) | 사용 전 점검·관리 절 | `close-up of {part} during a routine check, gloved hand pointing, {time}` |

## 변주 지침 (같은 글 안, 그리고 글마다)

- 축 3개를 슬롯마다 바꾼다: **시간대**(`early morning`, `bright midday`, `late afternoon golden hour`, `overcast day`) · **앵글**(`eye-level wide shot`, `high-angle view`, `low-angle view from the ground`, `over-the-shoulder from behind the person`) · **날씨/계절**(`clear autumn day`, `light drizzle with wet pavement`, `winter morning with breath visible`, `summer haze`).
- 한 글 안에서 같은 패턴 번호를 두 번 쓰면 시간대·앵글 둘 다 달라야 한다. 같은 장면 반복은 검수 불합격.
- 이전 글과의 반복을 줄이려고 `work/variation-log.md` 최근 글과 다른 표지 패턴(1~7)을 고른다.

## 금지

- 글자·숫자 렌더링(간판·현수막·자막·제품 문구·번호판·서류 내용) — 글자는 본문으로.
- 얼굴 클로즈업, 정면 인물 — 뒷모습·원거리·손·사물 중심.
- 브랜드 로고·제조사 이름(자기 업체명 포함)·실제 번호판.
- 실존 장소·업체 외관 재현, 금칙어가 가리키는 장소·표지(금칙어 규칙과 같은 이유).
- 홍보 슬롯(업체 소개(실사진)·`type=홍보` 글)에는 AI 이미지를 쓰지 않는다 → photo.

## 표지용 배경 패턴 (`00` cover 행)

- 패턴 1·3·4 중에서 고른다. 프롬프트는 **글자 없는 배경 장면**만 쓴다(글자·로고·번호판 금지는 그대로). 제목·배지·전화번호는 `scripts/make_cover.py`가 위에 합성한다.
- 표지는 1:1 중앙 크롭으로 쓰이므로 **피사체를 화면 가운데에** 두는 변주 문구를 넣는다. 예: `..., subject centered in the frame, empty space above and below for text overlay` / `the main object in the middle of the frame, symmetrical composition`.
- 배경 파일은 `images/00-bg.png`에 저장되고 합성 결과가 `images/00-cover.png`다. 배경을 실사진으로 대체하려면 make_cover.py `--bg photos/<파일>`.

## 캡션(alt) 규칙 — 내부 메모

- 캡션은 내부 메모용이며 본문에 노출되지 않는다(업로드본은 캡션 없음). 한 줄로 무엇을 보여주는지만 적는다.
- "이미지는 AI 생성" 표기 여부는 `knowledge/design-system.md` ⑤를 따른다(규정이 없으면 표기하지 않는다).
- 캡션에 수치·일정·법령을 새로 넣지 않는다.

## stock 검색어 패턴 (Pexels — image-plan `유형` stock 행)

이 절은 위 AI 프롬프트 절과 따로 쓴다. stock 행의 프롬프트 칸(`프롬프트(ai) / 검색어(stock) / 후보 파일(photo)`)에는 **검색어만** 적는다. 위의 공통 접두/접미는 stock에 붙지 않는다. `scripts/fetch_stock.py`는 칸의 검색어를 **그대로** Pexels에 보낸다. 프로필 `이미지 기본 장면`도 자동으로 붙이지 않는다. 그래서 장면구의 핵심 명사 1개는 이 스킬이 검색어 안에 직접 넣는다.

- 형식: 영문 **2~4단어 명사구**. 쉼표·문장·`|`·한글은 쓰지 않는다. `{noun}` 자리에 `이미지 기본 장면`의 핵심 명사(또는 글 주제의 사물 명사)를 넣고, 넣은 뒤에도 4단어 이하로 맞춘다.
- 넣지 않을 말: `sign` `logo` `poster` `menu` `portrait` `face` `smiling` `selfie` `screen` `brand`. 글자·로고·얼굴이 나오기 쉬운 말이다.
- 한 글 안에서 같은 패턴은 한 번만 쓴다. 이전 글과 같은 검색어도 쓰지 않는다(같은 검색어는 같은 사진을 돌려준다).

| # | 쓰는 슬롯(목적) | 패턴 | 예(업종 중립) |
|---|---|---|---|
| 1 | 소제목 요약·분위기 | `laptop wooden desk morning` | `laptop wooden desk morning` |
| 2 | 작업 장면 | `{noun} hands closeup` | `notebook hands closeup` |
| 3 | 제품·상품 | `{noun} top view` | `coffee beans top view` |
| 4 | 현장(실내) | `empty {noun} interior` | `empty classroom interior` |
| 5 | 절차 장면 | `{noun} tools workbench` | `garden tools workbench` |
| 6 | 현장(사람, 원거리) | `person from behind {noun}` | `person from behind bicycle` |
| 7 | 서류·준비물 | `blank notebook pen desk` | `blank notebook pen desk` |
| 8 | 안전 | `safety gloves {noun}` | `safety gloves toolbox` |
| 9 | 현장(야외·계절) | `{noun} street autumn morning` | `quiet street autumn morning` |
| 10 | 표지(`00`) 배경 | `{noun} centered minimal background` | `plant centered minimal background` |

표지 배경(`00` 행이 stock일 때)은 패턴 10처럼 피사체가 가운데 있고 위아래가 비는 장면을 고른다. 받은 사진은 `images/00-bg.jpg`이고, 제목·배지는 `make_cover.py --bg`가 그 위에 얹는다.
