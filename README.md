# FINDY

FINDY는 "Find Your Beauty"를 콘셉트로 한 뷰티 아티스트 탐색, 리뷰, 커뮤니티, 예약 서비스 프로토타입입니다.

현재 앱은 하나의 공통 코드베이스를 기준으로 고객 모드와 아티스트 모드를 분리해서 실행합니다.

## 실행

고객 모드:

```bash
cd /Users/kyoungmin/Desktop/FINDY
python3 python_files/FINDY_customer.py
```

아티스트 모드:

```bash
cd /Users/kyoungmin/Desktop/FINDY
python3 python_files/FINDY_artist.py
```

공통 진입점:

```bash
python3 python_files/FINDY.py
```

커뮤니티형 배포 후보:

```bash
python3 python_files/FINDY2.py
```

웹사이트:

```text
/Users/kyoungmin/Desktop/FINDY/web/index.html
```

FINDY2 커뮤니티 웹사이트를 로컬 서버로 실행:

```bash
cd /Users/kyoungmin/Desktop/FINDY
python3 -m http.server 4173
```

브라우저에서 `http://localhost:4173/web/`을 엽니다.

웹사이트는 FINDY2의 첫 배포 방향을 기준으로 커뮤니티, 스냅, 비디오,
통합 검색, 글쓰기, 좋아요/저장, 나의 FINDY를 구현합니다. 작성 글과
사용자 선택은 브라우저 `localStorage`에 저장됩니다.

## 설치

```bash
python3 -m pip install -r requirements.txt
```

## 검증

수정 후 기본 검증은 아래 명령으로 진행합니다.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/findy_pycache python3 -m py_compile python_files/FINDY.py python_files/FINDY2.py python_files/FINDY_customer.py python_files/FINDY_artist.py
PYTHONPYCACHEPREFIX=/private/tmp/findy_pycache python3 python_files/smoke_test.py
git diff --check
```

수동 QA 기준은 `docs/project/QA_CHECKLIST.md`, 출시 전 기준은 `docs/project/RELEASE_CHECKLIST.md`, 다음 작업 순서는 `docs/project/NEXT_STEPS.md`를 기준으로 확인합니다. 실제 연결 구조는 `docs/project/APP_STRUCTURE.md`, 데이터 기준은 `docs/project/DATA_STRUCTURE.md`, 추천 키워드 기준은 `docs/project/BEAUTY_KEYWORD_TAXONOMY.md`, 화면 튐/비율 기준은 `docs/project/UI_STABILITY_GUIDE.md`를 기준으로 확인합니다.

## 주요 파일

```text
python_files/FINDY.py                  # 메인 예약형 앱
python_files/FINDY2.py                 # 커뮤니티형 배포 후보 앱
python_files/FINDY_customer.py         # 고객 모드 실행 파일
python_files/FINDY_artist.py           # 아티스트 모드 실행 파일
python_files/smoke_test.py             # 컴파일 및 필수 에셋 체크
python_files/generate_placeholders.py  # 플레이스홀더 이미지 생성
assets/              # 앱 로고, 소셜 로그인 이미지, 폰트, 가이드 이미지
components/          # 공통 UI 컴포넌트
core/                # 상태와 라우터
data/                # 더미 데이터
data/beauty_mood_keywords.py # FINDY2 추천 알고리즘 준비용 감성어/키워드 사전
data/review_safety.py # 리뷰 위험어 감지, 개인정보 마스킹, 신고/상태 헬퍼
services/findy2_phone_auth.py # 휴대폰 문자 인증 앱 통신
auth_gateway/app.py # 소셜 로그인, 문자 인증, PASS 본인확인 연결 게이트웨이
pages/               # 일부 모듈화된 페이지
services/            # 예약/아티스트 서비스 로직
web/                 # FINDY2 커뮤니티 웹사이트 (HTML/CSS/JavaScript)
docs/                # 프로젝트 문서
docs/artist/         # 아티스트 정책 문서
```

## 구조 문서

```text
docs/README.md                     # 문서 전체 인덱스
docs/apps/FINDY.md                 # 메인 예약형 앱 기준
docs/apps/FINDY2.md                # 첫 배포용 커뮤니티형 앱 기준
docs/apps/FINDY_customer.md        # 고객 모드 기준
docs/apps/FINDY_artist.md          # 아티스트 모드 기준
docs/project/APP_STRUCTURE.md       # 실제 실행 경로와 보조 파일 구분
docs/project/DATA_STRUCTURE.md      # 데이터 소스, 엔티티, 예약/메시지 기준
docs/project/BEAUTY_KEYWORD_TAXONOMY.md # FINDY2 감성어/추천 키워드 기준
docs/project/UI_STABILITY_GUIDE.md  # 화면 튐 방지, 모바일 비율, 버튼 안정성 기준
```

## 브랜드 기준

- 대표색 / 로고색 / 포인트색: `#8B6B4F`
- 라인 / 구분선 / 카드 테두리: `#E6D7C8`
- 배경 / 카드 배경: `#FFFFFF`
- 강한 텍스트: `#1F1A17`
- 본문 텍스트: `#2B2420`
- 보조 텍스트: `#786A62`

로고는 반드시 `assets/app_logo`의 이미지 파일을 사용합니다. 워드마크나 심볼을 텍스트로 직접 재현하지 않습니다.

## 출시 전 기준

- 고객 모드와 아티스트 모드는 서로 전환하지 않고 분리합니다.
- 아티스트 모드에서는 리뷰 작성 기능을 제공하지 않습니다.
- 아티스트 주요 정보는 운영팀 컨펌 이후 반영합니다.
- 포트폴리오는 가격 메뉴와 연결됩니다. 가격 메뉴를 먼저 만들고, 포트폴리오 등록 시 메뉴를 선택하는 구조입니다.
- 버튼, 칩, 날짜, 토글 클릭 시 화면이 맨 위로 튀거나 전체가 깜빡이면 회귀로 봅니다.
