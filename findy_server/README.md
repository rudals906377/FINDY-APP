# FINDY 서버 API

FINDY2 커뮤니티 운영을 위한 로컬 API 서버입니다.

현재 단계에서는 앱 출시 전 운영 준비를 위해 다음 기능을 제공합니다.

- 사용자 기본 정보
- 회원가입 약관 동의 기록
- 위치정보 사용 설정
- 공지사항/이벤트
- 게시글/댓글/리뷰
- 콘텐츠 위험 표현 감지와 개인정보 마스킹
- 신고
- 포인트 지갑/관리자 지급·회수
- 관리자 콘텐츠 상태 변경
- 관리자 처리 로그

## API는 누가 만들 수 있나?

API 서버 코드와 앱 연동 코드는 Codex가 만들어줄 수 있습니다.

다만 아래 작업은 사용자가 직접 해야 합니다.

- 카카오/네이버/Google/Apple 개발자 콘솔 앱 등록
- 문자 발송 업체 계약과 발신번호 등록
- NICE/KCB/다날/KCP 등 PASS 본인확인 계약
- 서비스 도메인과 HTTPS 서버 준비
- 발급받은 운영 키를 `.env`에 입력

## 로컬 실행

```bash
cd /Users/kyoungmin/Desktop/FINDY
cp findy_server/.env.example findy_server/.env
./findy_server/run_local.sh
```

서버가 켜지면 아래 주소에서 문서를 볼 수 있습니다.

- http://localhost:8790/docs
- http://localhost:8790/health

## 관리자 API 인증

관리자 API는 헤더가 필요합니다.

```text
X-FINDY-ADMIN-KEY: change-me-admin-key
```

운영 전에는 반드시 `findy_server/.env`의 `FINDY_ADMIN_API_KEY`를 바꿔야 합니다.

## 주요 API

### 사용자

- `POST /v1/users`
- `GET /v1/users`
- `GET /v1/users/{userId}`
- `POST /v1/users/consents`
- `GET /v1/users/{userId}/consents`
- `PUT /v1/users/{userId}/location`

### 공지/이벤트

- `GET /v1/notices`
- `POST /v1/admin/notices`
- `PATCH /v1/admin/notices/{noticeId}`
- `GET /v1/events`
- `POST /v1/admin/events`

### 커뮤니티

- `GET /v1/posts`
- `POST /v1/posts`
- `GET /v1/posts/{postId}`
- `POST /v1/comments`

### 리뷰

- `GET /v1/reviews`
- `POST /v1/reviews`

### 신고/관리자

- `POST /v1/reports`
- `GET /v1/admin/reports`
- `PATCH /v1/admin/reports/{reportId}`
- `GET /v1/admin/dashboard`
- `GET /v1/admin/content`
- `PATCH /v1/admin/content/{targetType}/{targetId}/status`
- `GET /v1/admin/logs`

### 포인트

- `GET /v1/points/{userId}`
- `POST /v1/points/admin/adjust`

## 앱 연결 방향

FINDY2 앱에서는 추후 `FINDY2_API_URL=http://localhost:8790` 같은 환경 변수를 두고,
공지사항/게시글/리뷰/신고/포인트 데이터를 이 서버에서 불러오도록 연결하면 됩니다.

현재 앱에는 선택 API 클라이언트가 들어가 있습니다.

```bash
export FINDY2_API_URL=http://localhost:8790
export FINDY2_ADMIN_API_KEY=change-me-admin-key
python3 python_files/FINDY2.py
```

앱 안에서는 `설정 > 운영 관리`에서 서버 상태를 확인하고 공지 등록, 신고 처리,
포인트 지급/회수 흐름을 테스트할 수 있습니다. 환경 변수가 없으면 앱은 로컬 모드로
계속 동작합니다.

## 운영 전 해야 할 일

- SQLite를 PostgreSQL 또는 Supabase로 교체
- 이미지/영상 업로드 스토리지 연결
- 사용자 인증 토큰 검증 추가
- 관리자 웹페이지 제작
- 요청 제한과 감사 로그 강화
- 실서비스 개인정보처리방침/위치정보 약관 URL 연결
- 푸시 알림 연동
