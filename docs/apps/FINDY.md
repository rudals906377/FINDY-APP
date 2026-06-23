# FINDY

FINDY는 예약 시스템까지 확장할 메인 앱 기준 파일입니다. FINDY2에서 검증한 커뮤니티/추천 데이터 흐름을 이후 FINDY에 흡수해, 고객 모드와 아티스트 모드가 함께 동작하는 예약형 서비스로 발전시키는 것이 목표입니다.

## 실행

```bash
cd /Users/kyoungmin/Desktop/FINDY
python3 python_files/FINDY.py
```

실제 앱 본문은 `python_files/FINDY.py`에 있습니다.

## 현재 역할

- 고객 모드와 아티스트 모드를 함께 포함하는 공통 메인 앱입니다.
- `python_files/FINDY_customer.py`, `python_files/FINDY_artist.py`가 같은 본문을 모드별로 실행합니다.
- 예약, 아티스트 프로필, 포트폴리오, 가격 메뉴, 리뷰, 스냅, 비디오, 내정보 흐름을 포함합니다.
- FINDY2와 디자인 톤을 맞추되, 기존 예약/아티스트 기능은 지우지 않습니다.

## 수정 기준

- 기능을 크게 바꾸기 전에는 FINDY2에서 먼저 검증합니다.
- 고객 모드와 아티스트 모드가 공유하는 디자인은 `python_files/FINDY.py`에 반영합니다.
- 기존 예약, 가격 메뉴, 포트폴리오, 아티스트 관리 기능은 유지합니다.
- FINDY2의 커뮤니티형 기능을 FINDY에 반영할 때는 겹치는 화면만 수정하고 기존 기능을 삭제하지 않습니다.

## 관련 파일

```text
python_files/FINDY.py       # 실제 메인 앱 본문
python_files/FINDY_customer.py
python_files/FINDY_artist.py
components/                 # 공통 UI
data/                       # 더미 데이터와 리뷰 안전 로직
services/                   # 예약/아티스트 서비스
```
