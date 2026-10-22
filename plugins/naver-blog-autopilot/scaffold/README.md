# naver-blog-autopilot 작업 폴더

- 이 폴더가 정본입니다. `knowledge/` 안의 파일(디자인 시스템·업체정보·공신 출처·SEO 체크리스트·주제 씨앗)은 `/naver-blog-autopilot:blog-onboard`가 대화로 채워 주고, 여기서 직접 고쳐도 됩니다. 필수 칸이 비어 있으면 스크립트가 기본값 없이 오류로 멈춥니다(확인: `python3 scripts/check_profile.py` → `profile: OK`).
- `photos/`에 실사진(매장·작업·제품 등)을 넣어 두면 글에 실사진 슬롯으로 쓰입니다(프로필 `이미지 소스`에 `photo`가 있을 때). 프로필 `마무리 블록`에 `소개이미지`를 넣었다면 글 끝 소개 이미지 `photos/business-intro.png`도 여기에 둡니다.
- `work/`는 주제 후보·초안·팩트체크·이미지·업로드 로그 등 산출물이 쌓이는 곳입니다.
- `.env`에 블로그 아이디(`NAVER_BLOG_ID`)와 이미지 소스별 키 — AI 생성 `GEMINI_API_KEY` 또는 `OPENAI_API_KEY` — 를 넣으세요(`.env.example` 참고, 온보딩이 안내합니다). 무료 스톡 사진은 키가 필요 없습니다(기본 Openverse — Pexels 키가 이미 있을 때만 `PEXELS_API_KEY`, 선택). `.env`와 `playwright-state/`는 git에 올리지 않습니다.
