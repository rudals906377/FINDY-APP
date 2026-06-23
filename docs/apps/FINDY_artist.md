# FINDY Artist

FINDY Artist는 FINDY 메인 앱을 아티스트 전용 모드로 실행하는 흐름입니다. 아티스트가 프로필, 포트폴리오, 가격 메뉴, 예약, 리뷰를 관리하는 운영 화면을 기준으로 합니다.

## 실행

```bash
cd /Users/kyoungmin/Desktop/FINDY
python3 python_files/FINDY_artist.py
```

아티스트 모드 실행 파일은 `python_files/FINDY_artist.py`이고, 최종 앱 본문은 `python_files/FINDY.py`를 사용합니다.

## 현재 역할

- `FINDY_APP_MODE=artist` 환경값으로 FINDY를 실행합니다.
- 아티스트 로그인, 아티스트 메인, 프로필 관리, 포트폴리오 관리, 가격 메뉴 관리, 예약 관리, 리뷰 관리 흐름을 확인합니다.
- 고객 모드로 전환하는 버튼은 두지 않는 것이 기준입니다.

## 수정 기준

- 아티스트 모드에서는 리뷰 작성 기능을 제공하지 않습니다.
- 아티스트 주요 정보는 운영팀 컨펌 이후 반영되는 구조를 유지합니다.
- 포트폴리오는 가격 메뉴와 연결합니다.
- 예약 변경/취소 요청, 내부 메모는 고객 노출 정보와 분리합니다.
- FINDY2에서 만든 디자인을 반영하더라도 아티스트 관리 기능은 삭제하지 않습니다.

## 관련 문서

- `docs/artist/README.md`: 아티스트 프로필 승인/컨펌 정책

## 관련 파일

```text
python_files/FINDY_artist.py
python_files/FINDY.py
services/artist_service.py
services/reservation_service.py
```
