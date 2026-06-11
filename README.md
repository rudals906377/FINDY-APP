# FINDY

FINDY는 "Find Your Beauty"를 콘셉트로 한 뷰티 아티스트 탐색, 리뷰, 커뮤니티, 예약 서비스 프로토타입입니다.

현재 앱은 하나의 공통 코드베이스를 기준으로 고객 모드와 아티스트 모드를 분리해서 실행합니다.

## 실행

고객 모드:

```bash
cd /Users/kyoungmin/Desktop/FINDY
python3 FINDY_customer.py
```

아티스트 모드:

```bash
cd /Users/kyoungmin/Desktop/FINDY
python3 FINDY_artist.py
```

공통 진입점:

```bash
python3 FINDY.py
```

웹사이트:

```text
/Users/kyoungmin/Desktop/FINDY/web/index.html
```

## 설치

```bash
python3 -m pip install -r requirements.txt
```

## 검증

수정 후 기본 검증은 아래 명령으로 진행합니다.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/findy_pycache python3 -m py_compile FINDY.py FINDY_customer.py FINDY_artist.py
PYTHONPYCACHEPREFIX=/private/tmp/findy_pycache python3 smoke_test.py
git diff --check
```

수동 QA 기준은 `md/QA_CHECKLIST.md`, 출시 전 기준은 `md/RELEASE_CHECKLIST.md`, 다음 작업 순서는 `md/NEXT_STEPS.md`를 기준으로 확인합니다. 실제 연결 구조는 `md/APP_STRUCTURE.md`, 데이터 기준은 `md/DATA_STRUCTURE.md`, 화면 튐/비율 기준은 `md/UI_STABILITY_GUIDE.md`를 기준으로 확인합니다.

## 주요 파일

```text
FINDY.py             # 공통 앱 진입점과 현재 주요 화면 구현
FINDY_customer.py    # 고객 모드 실행 래퍼
FINDY_artist.py      # 아티스트 모드 실행 래퍼
smoke_test.py        # 컴파일 및 필수 에셋 체크
assets/              # 앱 로고, 소셜 로그인 이미지, 폰트, 가이드 이미지
components/          # 공통 UI 컴포넌트
core/                # 상태와 라우터
data/                # 더미 데이터
pages/               # 일부 모듈화된 페이지
services/            # 예약/아티스트 서비스 로직
web/                 # FINDY 웹사이트
md/                  # 프로젝트 문서
artist/              # 아티스트 정책 문서
```

## 구조 문서

```text
md/APP_STRUCTURE.md       # 실제 실행 경로와 보조 파일 구분
md/DATA_STRUCTURE.md      # 데이터 소스, 엔티티, 예약/메시지 기준
md/UI_STABILITY_GUIDE.md  # 화면 튐 방지, 모바일 비율, 버튼 안정성 기준
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
