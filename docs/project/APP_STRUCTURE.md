# FINDY 앱 구조 기준

이 문서는 FINDY 프로젝트에서 실제 실행에 연결된 파일과, 보조/실험 성격으로 남아 있는 파일을 구분하기 위한 기준입니다. 새 기능을 수정할 때는 먼저 이 문서 기준으로 실제 실행 경로를 확인합니다.

## 1. 실제 실행 진입점

```text
python_files/FINDY.py
python_files/FINDY2.py
python_files/FINDY_customer.py
python_files/FINDY_artist.py
web/index.html
```

- `python_files/FINDY.py`: 메인 예약형 앱입니다.
- `python_files/FINDY2.py`: 첫 배포용 커뮤니티형 앱입니다.
- `python_files/FINDY_customer.py`: 고객 전용 런타임 모드로 `python_files/FINDY.py`를 실행합니다.
- `python_files/FINDY_artist.py`: 아티스트 전용 런타임 모드로 `python_files/FINDY.py`를 실행합니다.
- `web/index.html`: 앱과 별개로 실행되는 정적 웹사이트 프로토타입입니다.

## 2. 실제 앱에 연결된 주요 폴더

```text
assets/
components/
data/
docs/apps/
docs/artist/
docs/project/
python_files/
```

- `assets/`: 로고, 소셜 로그인 이미지, 폰트, 브랜드 가이드 이미지가 들어 있습니다.
- `components/`: 현재 앱에서 재사용하는 카드, 레이아웃, 오버레이 컴포넌트가 들어 있습니다.
- `data/`: 카테고리, 아티스트, 리뷰, 스냅 더미 데이터가 들어 있습니다.
- `docs/apps/`: FINDY, FINDY2, 고객 모드, 아티스트 모드 기준 문서가 들어 있습니다.
- `docs/artist/`: 아티스트 운영 정책과 컨펌 기준 문서가 들어 있습니다.
- `docs/project/`: QA, 출시 기준, 구조 기준 등 프로젝트 문서가 들어 있습니다.
- `python_files/`: 실제 파이썬 앱 본문과 보조 스크립트가 들어 있습니다.

## 3. 확인 후 수정해야 하는 보조 폴더

```text
core/
pages/
services/
```

이 폴더들은 모듈화 또는 보조 로직을 위해 존재하지만, 모든 파일이 현재 화면에 직접 연결되어 있다고 보면 안 됩니다.

- `core/`: 상태와 라우팅 보조 코드입니다. 실제 라우팅은 아직 `python_files/FINDY.py` 중심입니다.
- `pages/`: 일부 페이지 모듈 파일입니다. 현재 화면 대부분은 여전히 `python_files/FINDY.py` 안에서 렌더링됩니다.
- `services/`: 예약/아티스트 서비스 보조 로직입니다.

이 폴더를 수정할 때는 반드시 `python_files/FINDY.py`에서 import 또는 호출되는지 먼저 확인합니다.

## 4. 화면 이동 기준

- 실제 페이지 이동은 라우팅/히스토리 흐름을 사용합니다.
- 뒤로가기 버튼은 `safe_go_back` 또는 현재 페이지 히스토리 흐름으로 연결합니다.
- 고객 모드와 아티스트 모드는 서로 전환하지 않습니다.
- 고객 모드의 기본 복귀 지점은 홈입니다.
- 아티스트 모드의 기본 복귀 지점은 아티스트 메인입니다.
- FINDY2는 고객/아티스트 구분 없이 커뮤니티형 앱 흐름을 사용합니다.

## 5. 버튼 동작 기준

모든 버튼은 아래 네 가지 중 하나를 반드시 수행해야 합니다.

```text
1. 페이지 이동
2. 현재 카드/영역 상태 변경
3. 입력창/다이얼로그/오버레이 열기
4. 명확한 피드백 표시
```

아무 반응이 없는 버튼은 출시 전 회귀로 봅니다. 기능을 아직 구현하지 않을 버튼은 숨기거나, 준비 중 피드백을 명확하게 표시합니다.

## 6. 로고 사용 기준

- 로고는 반드시 `assets/app_logo` 또는 정리된 로고 이미지 파일을 사용합니다.
- `FINDY` 워드마크나 심볼을 텍스트로 직접 그리지 않습니다.
- 로고 색상은 브랜드 기준과 일치해야 합니다.
