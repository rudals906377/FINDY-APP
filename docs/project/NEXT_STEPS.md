# FINDY 다음 작업 순서

FINDY는 현재 화면 프로토타입, FINDY2 커뮤니티 운영 기능, 로컬 API 서버 기본 검증 단계입니다. 이후 완성도를 높일 때는 화면 안정화, 운영 데이터 연결, 출시 준비, 실제 사업자/외부 API 계약 순서로 진행합니다.

## 0. 지금 바로 필요한 작업

1. GitHub 인증을 완료하고 현재 커밋을 원격 저장소에 푸시합니다.
2. `python3 python_files/FINDY2.py`로 앱을 실행해 커뮤니티, 리뷰, 스냅, 비디오, 내정보, 약관 동의, 운영 관리 화면을 수동 확인합니다.
3. `./findy_server/run_local.sh`로 서버를 켜고 `FINDY2_API_URL=http://localhost:8790` 환경에서 운영 관리 연결 상태를 확인합니다.
4. 앱 제출 전에는 로컬 SQLite 대신 Supabase/PostgreSQL 같은 운영 DB를 결정합니다.

## 1. 흐름 안정화

- 모든 뒤로가기 버튼을 이전 화면 기준으로 통일합니다.
- 토글, 필터, 날짜 선택, 액션 버튼 클릭 시 화면이 튀거나 깜빡이지 않게 유지합니다.
- FINDY에서는 고객 모드와 아티스트 모드를 완전히 분리합니다.
- FINDY2에서는 고객/아티스트 구분 없이 커뮤니티형 흐름을 유지합니다.
- 아티스트 모드에서는 리뷰 작성 기능을 막고, 스냅/비디오/커뮤니티 작성만 허용합니다.

## 2. 핵심 기능 완성

- 고객 모드: 검색, 리뷰 작성, 스냅 작성, 비디오 작성, 커뮤니티 작성, 좋아요, 저장, 댓글을 연결합니다.
- 아티스트 모드: 프로필 관리, 포트폴리오 관리, 가격 메뉴 관리, 예약 관리, 리뷰 관리, 트렌드 분석을 연결합니다.
- FINDY2: 인기글, 리뷰, 질문, 자유게시판, FINDY 스냅, FINDY 비디오, 나의 FINDY를 커뮤니티형 데이터 수집 흐름으로 안정화합니다.
- 포트폴리오는 가격 메뉴와 연동합니다.
- 예약 변경/취소 요청은 문자 메시지처럼 고객에게 전달되는 구조로 정리합니다.
- 메모는 예약별 내부 메모로 저장합니다.

## 3. 데이터 구조 정리

- 더미 데이터와 화면 상태를 분리합니다.
- 고객 데이터, 아티스트 데이터, 예약 데이터, 리뷰 데이터, 콘텐츠 데이터를 별도 구조로 관리합니다.
- 아티스트 주요 정보는 회사 컨펌 후 반영되는 필드로 구분합니다.
- 이미지, 영상, 로고 에셋은 역할별 폴더에 유지합니다.

## 4. 출시 준비

- 소셜 로그인 API 연결 방식을 결정합니다.
- 이미지/영상 업로드 저장소를 연결합니다.
- 예약 데이터 저장소와 알림 시스템을 연결합니다.
- 아티스트 승인 프로세스와 운영툴을 준비합니다.
- 개인정보처리방침, 이용약관, 신고/숨김 정책을 준비합니다.

## 5. 운영 서버 연결

1. 로컬 FastAPI 서버는 `findy_server/`에 있습니다.
2. 개발 중 실행은 `./findy_server/run_local.sh`를 사용합니다.
3. 앱 연결은 아래 환경 변수로 합니다.

```bash
export FINDY2_API_URL=http://localhost:8790
export FINDY2_ADMIN_API_KEY=dev-admin-key
python3 python_files/FINDY2.py
```

4. 운영 배포 전에는 `FINDY_ADMIN_API_KEY`를 반드시 변경합니다.
5. 실제 출시 전에는 관리자 화면, 요청 제한, 사용자 인증 토큰 검증, 이미지/영상 스토리지, 푸시 알림을 연결합니다.

## 6. 전문성 강화 우선순위

1. 예약 관리 화면을 실제 업무 캘린더처럼 안정화
2. 아티스트 포트폴리오와 가격 메뉴 연결 고도화
3. 리뷰와 커뮤니티 상세 화면의 신뢰도 정보 강화
4. 트렌드 분석 페이지를 카테고리별 데이터 중심으로 정리
5. 빈 상태, 오류 상태, 작성 완료 상태를 모두 일관된 톤으로 정리
6. 데이터 저장 방식 결정
7. 소셜 로그인과 권한 분리 연결
8. 이미지 업로드와 미리보기 연결
9. 실제 배포 환경 검토
10. QA 체크리스트 기반 전체 회귀 테스트

## 7. 매 수정 후 기본 검증

```bash
PYTHONPYCACHEPREFIX=/private/tmp/findy_pycache python3 -m py_compile python_files/FINDY.py python_files/FINDY2.py python_files/FINDY_customer.py python_files/FINDY_artist.py
PYTHONPYCACHEPREFIX=/private/tmp/findy_pycache python3 python_files/smoke_test.py
PYTHONPYCACHEPREFIX=/private/tmp/findy_pycache python3 python_files/test_findy2_services.py
git diff --check
```

문서 기준도 함께 확인합니다.

```text
docs/apps/
docs/project/
```
