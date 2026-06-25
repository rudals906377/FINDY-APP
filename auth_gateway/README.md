# FINDY 통합 로그인 게이트웨이

네이버, 카카오, Google, Apple의 비밀키를 모바일 앱에 포함하지 않기 위한 서버입니다.

문자 인증번호를 이용한 회원가입·아이디 찾기·비밀번호 재설정과 PASS 본인확인 공급자 연결 경계도 함께 제공합니다. 상세 설계는 `docs/project/PHONE_IDENTITY_RECOVERY.md`를 참고합니다.

## 제공 흐름

1. 앱이 `POST /v1/oauth/start`로 공급자 로그인을 시작합니다.
2. 서버는 공급자 인증 URL과 일회용 폴링 토큰을 반환합니다.
3. 사용자가 브라우저에서 인증을 완료합니다.
4. 공급자가 `/v1/oauth/callback/{provider}`로 인가 코드를 전달합니다.
5. 서버가 코드를 토큰으로 교환하고 사용자 정보를 검증합니다.
6. 앱이 `GET /v1/oauth/status/{flowId}`로 완료 결과를 받습니다.

공급자 액세스 토큰과 Client Secret은 앱으로 전달하지 않습니다.

## 휴대폰 인증

- `POST /v1/phone/otp/request`
- `POST /v1/phone/otp/verify`
- `POST /v1/identity/start` (PASS 공급자 계약 후 어댑터 연결)

개발 환경에서는 `FINDY_SMS_PROVIDER=console`로 서버 콘솔에서 인증번호를 확인합니다. 운영 환경에서는 Webhook 또는 실제 문자 공급자 API를 연결해야 합니다.

## 통합회원 기준

- 공급자와 공급자 사용자 ID가 같으면 기존 FINDY 계정을 사용합니다.
- 검증된 이메일이 같으면 다른 공급자도 같은 FINDY 계정에 연결합니다.
- 이메일이 없거나 검증되지 않으면 별도 계정으로 생성합니다.
- Apple의 이메일 가리기를 사용하면 다른 이메일 계정과 자동 통합되지 않을 수 있습니다.

## 로컬 실행

```bash
cd auth_gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a && source .env && set +a
uvicorn app:app --host 0.0.0.0 --port 8787
```

또는 자동 준비 스크립트를 사용합니다.

```bash
cp .env.example .env
./run_local.sh
```

앱 실행 전 공개 주소를 설정합니다.

```bash
export FINDY2_AUTH_API_URL=http://localhost:8787
python3 main.py
```

실제 모바일 로그인에는 공급자 콜백이 접근할 수 있는 HTTPS 주소가 필요합니다.

## 설정 검사

비밀값을 출력하지 않고 필요한 키의 존재 여부만 확인합니다.

```bash
set -a && source .env && set +a
python3 check_config.py
```

## Docker 실행

```bash
cp .env.example .env
docker compose up --build
```

운영 환경에서는 `/data`를 영구 볼륨으로 연결하고 플랫폼의 Secret Manager로 환경 변수를 주입합니다.

## 운영 전 보강

- 메모리 기반 OAuth flow를 Redis 등 만료 저장소로 교체
- 계정 연결 시 기존 FINDY 세션 재검증
- 공급자 토큰 폐기 및 회원 탈퇴 연동
- 요청 제한, 감사 로그, 비정상 로그인 탐지
- SQLite를 운영 데이터베이스로 교체
- 비밀키를 환경 변수 대신 Secret Manager에 저장
