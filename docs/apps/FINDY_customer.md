# FINDY Customer

FINDY Customer는 FINDY 메인 앱을 고객 전용 모드로 실행하는 흐름입니다. 고객이 아티스트/샵을 탐색하고, 리뷰/스냅/비디오를 보고, 예약까지 이어지는 사용자를 기준으로 합니다.

## 실행

```bash
cd /Users/kyoungmin/Desktop/FINDY
python3 python_files/FINDY_customer.py
```

고객 모드 실행 파일은 `python_files/FINDY_customer.py`이고, 최종 앱 본문은 `python_files/FINDY.py`를 사용합니다.

## 현재 역할

- `FINDY_APP_MODE=customer` 환경값으로 FINDY를 실행합니다.
- 고객 로그인, 홈, 카테고리, 검색, 아티스트 상세, 예약, 리뷰/스냅/비디오, 내정보 흐름을 확인합니다.
- 아티스트 관리 화면으로 직접 전환하지 않는 것이 기준입니다.

## 수정 기준

- 고객 모드에서 보이는 화면은 예약과 탐색 경험 중심으로 유지합니다.
- FINDY2의 커뮤니티 UI를 반영하더라도 예약 흐름은 제거하지 않습니다.
- 고객이 작성하는 리뷰는 안전 필터와 신고 흐름을 기준으로 확장합니다.
- 내정보 페이지 변경은 FINDY2와 디자인 톤을 맞추되, 예약 내역 등 고객 기능은 유지합니다.

## 관련 파일

```text
python_files/FINDY_customer.py
python_files/FINDY.py
services/reservation_service.py
reservation_history.json
```
