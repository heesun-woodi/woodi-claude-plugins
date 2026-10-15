# naver-blog-autopilot 작업 폴더

- 이 폴더가 정본입니다. `knowledge/` 안의 파일(디자인 시스템·업체정보·공신 출처·SEO 체크리스트)은 여기서 직접 고쳐도 됩니다. `[치환 변수]`로 남은 칸은 처음 쓰기 전에 채웁니다 — 필수 칸이 비어 있으면 스크립트가 기본값 없이 오류로 멈춥니다(확인: `python3 scripts/check_profile.py` → `profile: OK`).
- `photos/`에 업체 실사진(매장·작업·제품 등)을 넣어 두면 글에 실사진 슬롯으로 쓰입니다. 글 끝 마무리 블록의 업체소개 이미지 `photos/business-intro.png`도 여기에 둡니다.
- `work/`는 주제 후보·초안·팩트체크·이미지·업로드 로그 등 산출물이 쌓이는 곳입니다.
- `.env`에 이미지 AI 키(`GEMINI_API_KEY` 또는 `OPENAI_API_KEY`)와 블로그 아이디(`NAVER_BLOG_ID`)를 넣으세요(`.env.example` 참고). `.env`와 `playwright-state/`는 git에 올리지 않습니다.
