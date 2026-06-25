# FINDY 통합회원 소셜 로그인 설정

기준일: 2026년 6월 25일

## 구현 범위

FINDY2는 다음 로그인 방식을 하나의 FINDY 통합회원으로 처리합니다.

- 네이버
- 카카오
- Google
- Apple
- 기존 이메일/비밀번호

공급자 비밀키는 모바일 앱에 포함하지 않습니다. `auth_gateway/` 서버가 OAuth 인가 코드를 토큰으로 교환하고, 앱에는 검증된 공개 프로필과 FINDY 사용자 ID만 반환합니다.

## 통합 기준

1. 같은 공급자 사용자 ID는 항상 같은 FINDY 계정입니다.
2. 공급자가 검증한 이메일이 기존 FINDY 계정과 같으면 자동 연결합니다.
3. 서로 다른 공급자라도 인증 서버의 `findyUserId`가 같으면 같은 계정입니다.
4. 이메일이 없거나 검증되지 않으면 별도 계정으로 생성합니다.
5. Apple의 이메일 가리기 주소는 일반 이메일과 자동 병합되지 않을 수 있습니다.
6. 설정의 `연결된 계정`에서 현재 FINDY 계정에 새 로그인 수단을 추가할 수 있습니다.
7. 이미 다른 FINDY 계정에 연결된 공급자 계정은 충돌로 처리해 병합을 중단합니다.

## 앱 설정

인증 게이트웨이를 배포한 뒤 `core/findy2_public_config.json`에 공개 HTTPS 주소를 입력합니다.

```json
{
  "authApiUrl": "https://auth.example.com"
}
```

로컬 개발에서는 환경 변수로 덮어쓸 수 있습니다.

```bash
export FINDY2_AUTH_API_URL=http://localhost:8787
python3 main.py
```

## 공급자 공통 콜백

게이트웨이 공개 주소가 `https://auth.example.com`이면 다음 주소를 각 개발자 콘솔에 등록합니다.

```text
https://auth.example.com/v1/oauth/callback/naver
https://auth.example.com/v1/oauth/callback/kakao
https://auth.example.com/v1/oauth/callback/google
https://auth.example.com/v1/oauth/callback/apple
```

## 필요한 공급자 정보

### 네이버

- Client ID
- Client Secret
- 회원 프로필의 식별자와 이메일 권한

### 카카오

- REST API 키를 Client ID로 사용
- Client Secret
- OpenID Connect 활성화
- 닉네임, 프로필 이미지, 카카오계정 이메일 동의항목

### Google

- Web application OAuth Client ID
- Client Secret
- `openid`, `email`, `profile` 범위
- OAuth 동의 화면과 앱 브랜드 검증

### Apple

- Services ID 또는 앱 로그인 Client ID
- Team ID
- Key ID
- Sign in with Apple `.p8` Private Key
- Apple 로그인 활성화와 Return URL 등록

Apple OAuth Client Secret은 `.p8` 키로 서버에서 생성하며 앱에 포함하지 않습니다.

## 게이트웨이 실행

```bash
cd auth_gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a && source .env && set +a
uvicorn app:app --host 0.0.0.0 --port 8787
```

간단 실행:

```bash
auth_gateway/run_local.sh
```

상태 확인:

```bash
curl https://auth.example.com/health
```

Docker:

```bash
cd auth_gateway
docker compose up --build
```

## 공개 배포 전 필수 작업

- 인증 서버를 HTTPS 환경에 배포
- 비밀키를 Secret Manager에 저장
- 메모리 OAuth flow 저장소를 Redis로 교체
- SQLite 계정 저장소를 운영 DB로 교체
- 계정 연결·해제 시 기존 FINDY 세션 재확인
- 회원 탈퇴 시 공급자 토큰 폐기, 특히 Apple revoke 처리
- 로그인 실패, 취소, 만료, 공급자 점검 상태 QA
- 개인정보 처리방침에 소셜 로그인 데이터와 제공자를 고지

현재 게이트웨이는 FINDY 계정과 모든 연결 식별자를 삭제하는 API를 제공합니다. 다만 공급자 측 동의 철회와 Apple 토큰 revoke는 운영 배포 전 추가해야 합니다.
