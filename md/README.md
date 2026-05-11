# FINDY Project Guide

FINDY는 "Find Your Beauty"를 콘셉트로 한 뷰티 아티스트 탐색, 리뷰, 커뮤니티, 예약 서비스 프로토타입입니다.

현재 프로젝트는 두 흐름을 함께 관리합니다.

- `FINDY324.py`: Flet 기반 모바일 앱 프로토타입
- `web/index.html`: FINDY 앱 초기 사용자를 모으기 위한 리뷰/커뮤니티 기반 웹사이트

## 실행

```bash
cd /Users/kyoungmin/Desktop/FINDY
flet run FINDY324.py
```

웹 모드:

```bash
flet run --web FINDY324.py
```

스모크 테스트:

```bash
python3 smoke_test.py
```

정적 웹페이지는 브라우저에서 바로 열 수 있습니다.

```text
/Users/kyoungmin/Desktop/FINDY/web/index.html
```

## 주요 구조

```text
.
├── FINDY324.py                 # Flet 앱 실행 진입점
├── smoke_test.py               # 컴파일 및 필수 에셋 체크
├── reservation_history.json    # 예약 히스토리 저장 파일
├── assets/                     # 폰트, 로고, 앱용 이미지
├── components/                 # 공통 UI 빌더와 디자인 토큰
├── core/                       # 라우터와 전역 상태
├── data/                       # 정적 더미 데이터
├── pages/                      # 페이지 렌더러
├── services/                   # 예약/아티스트 서비스 로직
├── web/                        # FINDY 웹사이트
└── md/                         # 프로젝트 문서
```

## 앱 아키텍처

FINDY 앱은 Flet의 선언형 UI를 넓게 쓰기보다, 화면을 다시 그리는 명령형 패턴을 중심으로 동작합니다.

```text
page.clean() -> page.add(...) -> page.update()
```

모듈화된 페이지는 `render(page, app_state, rerender)` 시그니처를 기준으로 맞춰져 있습니다. 라우팅은 `app_state["current_page"]`와 `app_state["selected_tab"]`를 변경한 뒤 `rerender(page)`를 호출하는 방식입니다.

중요 파일:

- `core/router.py`: 페이지 이동 상태 변경 함수
- `core/app_state.py`: 전역 앱 상태
- `components/layout.py`: 브랜드 컬러, 폰 프레임, 간격, 반경, 폰트
- `components/cards.py`: 카드/섹션/버튼 UI
- `components/overlays.py`: 카테고리/필터 오버레이
- `services/artist_service.py`: 아티스트 조회와 스케줄 계산
- `services/reservation_service.py`: 예약 저장, 취소, 슬롯 충돌 검사

## 디자인 기준

브랜드 톤은 미니멀 화이트와 베이지 포인트를 기준으로 합니다.

- Main: `#AE8F6F`
- Dark: `#8B6B4F`
- Soft: `#F5EEE7`
- Background: `#FFFFFF`
- Font: Pretendard

웹사이트는 FINDY 앱 출시 전 사용자를 모으는 랜딩/커뮤니티 성격이 강합니다. 첫 화면에서는 검색과 카테고리를 중심에 두고, 이후 리뷰와 커뮤니티 참여로 자연스럽게 이어지게 구성합니다.

## 작업 원칙

### 1. 먼저 확인하기

수정 전에 실제 실행 경로를 확인합니다.

- 앱 기능이면 `FINDY324.py`에 실제 연결되어 있는지 먼저 봅니다.
- 웹 기능이면 `web/index.html`의 HTML, CSS, JS 흐름을 함께 확인합니다.
- 모듈화된 파일이 있어도 현재 실행 경로에 연결되지 않았을 수 있습니다.

### 2. 작게 고치기

요청과 직접 관련 있는 부분만 수정합니다.

- 불필요한 리팩터링을 하지 않습니다.
- 기존 스타일과 구조를 최대한 유지합니다.
- 새 추상화는 중복이나 복잡도를 실제로 줄일 때만 추가합니다.

### 3. 검증하기

앱 또는 웹 변경 후 가능한 검증을 실행합니다.

```bash
python3 smoke_test.py
```

웹 문서 변경 시에는 아래도 함께 확인합니다.

```bash
python3 -m html.parser web/index.html
node -e "const fs=require('fs'); const html=fs.readFileSync('web/index.html','utf8'); const s=html.match(/<script>([\\s\\S]*)<\\/script>/)[1]; new Function(s); console.log('JS OK')"
```

### 4. 새 페이지를 추가할 때

1. `pages/`에 페이지 모듈을 추가합니다.
2. `core/router.py`에 이동 함수를 추가합니다.
3. 실제 실행 경로인 `FINDY324.py`의 렌더링 분기에 연결합니다.
4. `smoke_test.py`의 `files` 리스트에 새 파일을 추가합니다.

## 현재 정리 방향

- `FINDY324.py`는 당장 쪼개기보다 현재 동작을 기준으로 안정화합니다.
- 중복 데이터와 로직은 점진적으로 `data/`, `services/`, `components/`로 옮깁니다.
- 웹사이트는 `web/index.html` 단일 파일 기반이므로, 수정 시 HTML/CSS/JS 연결을 한 번에 확인합니다.
- 예약 히스토리는 `reservation_history.json`에 저장되므로 테스트 중 데이터 변경에 주의합니다.

## 주의

- 사용자 변경사항을 임의로 되돌리지 않습니다.
- 불필요한 파일 삭제는 요청이 있을 때만 합니다.
- 삭제 전에는 남길 파일이 정상적으로 만들어졌는지 먼저 확인합니다.
