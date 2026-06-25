import json
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
import uuid
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlencode

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parent
DATABASE_PATH = Path(
    os.environ.get("FINDY_AUTH_DATABASE_PATH", ROOT / "findy_auth.db")
).expanduser()
PUBLIC_URL = os.environ.get("FINDY_AUTH_PUBLIC_URL", "http://localhost:8787").rstrip("/")
FLOW_TTL_SECONDS = int(os.environ.get("FINDY_AUTH_FLOW_TTL_SECONDS", "300"))
AUTH_ENV = os.environ.get("FINDY_AUTH_ENV", "development").strip().lower()
OTP_TTL_SECONDS = int(os.environ.get("FINDY_OTP_TTL_SECONDS", "180"))
OTP_RESEND_SECONDS = int(os.environ.get("FINDY_OTP_RESEND_SECONDS", "60"))
OTP_MAX_ATTEMPTS = int(os.environ.get("FINDY_OTP_MAX_ATTEMPTS", "5"))
OTP_SECRET = os.environ.get("FINDY_OTP_SECRET", "findy-development-otp-secret")
SMS_PROVIDER = os.environ.get("FINDY_SMS_PROVIDER", "console").strip().lower()
PHONE_PURPOSES = {"signup", "login", "find_id", "reset_password", "change_phone"}

PROVIDER_LABELS = {
    "naver": "네이버",
    "kakao": "카카오",
    "google": "Google",
    "apple": "Apple",
}


@dataclass
class PendingFlow:
    flow_id: str
    poll_token: str
    provider: str
    state: str
    expires_at: float
    link_account_id: Optional[str] = None
    status: str = "pending"
    identity: Optional[dict] = None
    message: str = ""


class StartRequest(BaseModel):
    provider: str
    client: str = "findy2"
    platform: str = "flet"
    linkAccount: bool = False


class PhoneOtpRequest(BaseModel):
    phoneNumber: str
    purpose: str


class PhoneOtpVerifyRequest(BaseModel):
    requestId: str
    code: str


flows: dict[str, PendingFlow] = {}
states: dict[str, str] = {}
phone_challenges: dict[str, dict] = {}
app = FastAPI(title="FINDY Social Auth Gateway", version="0.1.0")


def _database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        create table if not exists accounts (
            id text primary key,
            email text,
            nickname text not null,
            created_at integer not null
        )
        """
    )
    connection.execute(
        """
        create unique index if not exists accounts_verified_email
        on accounts(lower(email))
        where email is not null and email <> ''
        """
    )
    connection.execute(
        """
        create table if not exists identities (
            provider text not null,
            provider_user_id text not null,
            account_id text not null references accounts(id),
            email text,
            email_verified integer not null default 0,
            created_at integer not null,
            primary key(provider, provider_user_id)
        )
        """
    )
    connection.execute(
        """
        create table if not exists sessions (
            token_hash text primary key,
            account_id text not null references accounts(id),
            expires_at integer not null,
            created_at integer not null
        )
        """
    )
    return connection


def _clean_expired_flows():
    now = time.time()
    for flow_id, flow in list(flows.items()):
        if flow.expires_at <= now:
            flow.status = "expired"
            states.pop(flow.state, None)
            if flow.expires_at + 60 <= now:
                flows.pop(flow_id, None)


def _provider_config(provider):
    prefix = provider.upper()
    client_id = os.environ.get(f"{prefix}_CLIENT_ID", "").strip()
    client_secret = os.environ.get(f"{prefix}_CLIENT_SECRET", "").strip()
    if not client_id:
        raise HTTPException(503, f"{PROVIDER_LABELS[provider]} Client ID가 설정되지 않았습니다.")
    if provider != "apple" and not client_secret:
        raise HTTPException(503, f"{PROVIDER_LABELS[provider]} Client Secret이 설정되지 않았습니다.")
    return client_id, client_secret


def _callback_url(provider):
    return f"{PUBLIC_URL}/v1/oauth/callback/{provider}"


def _authorization_url(provider, state):
    client_id, _ = _provider_config(provider)
    callback = _callback_url(provider)
    if provider == "google":
        endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": client_id,
            "redirect_uri": callback,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
        }
    elif provider == "kakao":
        endpoint = "https://kauth.kakao.com/oauth/authorize"
        params = {
            "client_id": client_id,
            "redirect_uri": callback,
            "response_type": "code",
            "scope": "openid account_email profile_nickname profile_image",
            "state": state,
        }
    elif provider == "naver":
        endpoint = "https://nid.naver.com/oauth2.0/authorize"
        params = {
            "client_id": client_id,
            "redirect_uri": callback,
            "response_type": "code",
            "state": state,
        }
    else:
        endpoint = "https://appleid.apple.com/auth/authorize"
        params = {
            "client_id": client_id,
            "redirect_uri": callback,
            "response_type": "code",
            "response_mode": "form_post",
            "scope": "name email",
            "state": state,
        }
    return f"{endpoint}?{urlencode(params)}"


def _apple_client_secret():
    try:
        import jwt
    except ImportError as error:
        raise RuntimeError("Apple 로그인을 위해 PyJWT[crypto] 설치가 필요합니다.") from error
    team_id = os.environ.get("APPLE_TEAM_ID", "").strip()
    key_id = os.environ.get("APPLE_KEY_ID", "").strip()
    private_key = os.environ.get("APPLE_PRIVATE_KEY", "").replace("\\n", "\n").strip()
    client_id = os.environ.get("APPLE_CLIENT_ID", "").strip()
    if not all((team_id, key_id, private_key, client_id)):
        raise RuntimeError("Apple Team ID, Key ID, Private Key, Client ID 설정이 필요합니다.")
    now = int(time.time())
    return jwt.encode(
        {
            "iss": team_id,
            "iat": now,
            "exp": now + 60 * 60,
            "aud": "https://appleid.apple.com",
            "sub": client_id,
        },
        private_key,
        algorithm="ES256",
        headers={"kid": key_id},
    )


async def _exchange_code(provider, code, state=""):
    client_id, client_secret = _provider_config(provider)
    callback = _callback_url(provider)
    async with httpx.AsyncClient(timeout=20.0) as client:
        if provider == "google":
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": callback,
                    "grant_type": "authorization_code",
                },
            )
        elif provider == "kakao":
            response = await client.post(
                "https://kauth.kakao.com/oauth/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": callback,
                    "grant_type": "authorization_code",
                },
            )
        elif provider == "naver":
            response = await client.post(
                "https://nid.naver.com/oauth2.0/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": callback,
                    "grant_type": "authorization_code",
                    "state": state,
                },
            )
        else:
            response = await client.post(
                "https://appleid.apple.com/auth/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": _apple_client_secret(),
                    "redirect_uri": callback,
                    "grant_type": "authorization_code",
                },
            )
        response.raise_for_status()
        return response.json()


async def _fetch_identity(provider, tokens):
    access_token = tokens.get("access_token")
    async with httpx.AsyncClient(timeout=20.0) as client:
        if provider == "google":
            response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "provider": provider,
                "providerUserId": str(data["sub"]),
                "email": data.get("email", ""),
                "emailVerified": bool(data.get("email_verified")),
                "nickname": data.get("name") or "Google 회원",
                "avatarUrl": data.get("picture", ""),
            }
        if provider == "kakao":
            response = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()
            account = data.get("kakao_account") or {}
            profile = account.get("profile") or {}
            return {
                "provider": provider,
                "providerUserId": str(data["id"]),
                "email": account.get("email", ""),
                "emailVerified": bool(account.get("is_email_verified")),
                "nickname": profile.get("nickname") or "카카오 회원",
                "avatarUrl": profile.get("profile_image_url", ""),
            }
        if provider == "naver":
            response = await client.get(
                "https://openapi.naver.com/v1/nid/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json().get("response") or {}
            return {
                "provider": provider,
                "providerUserId": str(data["id"]),
                "email": data.get("email", ""),
                "emailVerified": bool(data.get("email")),
                "nickname": data.get("nickname") or data.get("name") or "네이버 회원",
                "avatarUrl": data.get("profile_image", ""),
            }

    try:
        import jwt
    except ImportError as error:
        raise RuntimeError("Apple 로그인을 위해 PyJWT[crypto] 설치가 필요합니다.") from error
    id_token = tokens.get("id_token")
    if not id_token:
        raise RuntimeError("Apple ID 토큰이 없습니다.")
    key_client = jwt.PyJWKClient("https://appleid.apple.com/auth/keys")
    signing_key = key_client.get_signing_key_from_jwt(id_token)
    claims = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=os.environ["APPLE_CLIENT_ID"],
        issuer="https://appleid.apple.com",
    )
    verified = claims.get("email_verified")
    if isinstance(verified, str):
        verified = verified.lower() == "true"
    return {
        "provider": provider,
        "providerUserId": str(claims["sub"]),
        "email": claims.get("email", ""),
        "emailVerified": bool(verified),
        "nickname": "Apple 회원",
        "avatarUrl": "",
    }


def _resolve_findy_account(identity, preferred_account_id=None):
    provider = identity["provider"]
    provider_user_id = identity["providerUserId"]
    email = str(identity.get("email") or "").strip().lower()
    verified = bool(identity.get("emailVerified"))
    nickname = str(identity.get("nickname") or PROVIDER_LABELS[provider] + " 회원")
    now = int(time.time())

    with _database() as connection:
        account_id = None
        if preferred_account_id:
            preferred = connection.execute(
                "select id from accounts where id = ?",
                (preferred_account_id,),
            ).fetchone()
            if not preferred:
                raise RuntimeError("연결할 FINDY 계정을 찾을 수 없습니다.")
            account_id = preferred["id"]

        existing = connection.execute(
            """
            select a.id from accounts a
            join identities i on i.account_id = a.id
            where i.provider = ? and i.provider_user_id = ?
            """,
            (provider, provider_user_id),
        ).fetchone()
        if existing and account_id and existing["id"] != account_id:
            raise RuntimeError("이미 다른 FINDY 계정에 연결된 소셜 계정입니다.")
        if not account_id:
            account_id = existing["id"] if existing else None

        if not account_id and email and verified:
            account = connection.execute(
                "select id from accounts where lower(email) = ?",
                (email,),
            ).fetchone()
            account_id = account["id"] if account else None

        if not account_id:
            account_id = f"user_{uuid.uuid4().hex}"
            connection.execute(
                "insert into accounts(id, email, nickname, created_at) values (?, ?, ?, ?)",
                (account_id, email if verified else None, nickname, now),
            )

        connection.execute(
            """
            insert into identities(
                provider, provider_user_id, account_id, email, email_verified, created_at
            ) values (?, ?, ?, ?, ?, ?)
            on conflict(provider, provider_user_id) do update set
                email = excluded.email,
                email_verified = excluded.email_verified
            """,
            (provider, provider_user_id, account_id, email, int(verified), now),
        )
    return account_id


def _create_session(account_id):
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = int(time.time())
    with _database() as connection:
        connection.execute(
            "delete from sessions where expires_at <= ?",
            (now,),
        )
        connection.execute(
            "insert into sessions(token_hash, account_id, expires_at, created_at) values (?, ?, ?, ?)",
            (token_hash, account_id, now + 60 * 60 * 24 * 30, now),
        )
    return raw_token


def _account_from_authorization(authorization):
    raw_token = (authorization or "").removeprefix("Bearer ").strip()
    if not raw_token:
        raise HTTPException(401, "FINDY 로그인 세션이 필요합니다.")
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = int(time.time())
    with _database() as connection:
        session = connection.execute(
            "select account_id, expires_at from sessions where token_hash = ?",
            (token_hash,),
        ).fetchone()
        if not session or session["expires_at"] <= now:
            raise HTTPException(401, "FINDY 로그인 세션이 만료되었습니다.")
        return session["account_id"]


def _normalize_korean_phone(phone_number):
    digits = "".join(char for char in str(phone_number or "") if char.isdigit())
    if digits.startswith("82"):
        digits = "0" + digits[2:]
    if len(digits) not in {10, 11} or not digits.startswith("01"):
        raise HTTPException(400, "올바른 대한민국 휴대폰 번호를 입력해주세요.")
    return digits


def _masked_phone(phone_number):
    if len(phone_number) == 11:
        return f"{phone_number[:3]}-****-{phone_number[-4:]}"
    return f"{phone_number[:3]}-***-{phone_number[-4:]}"


def _otp_digest(request_id, phone_number, purpose, code):
    payload = f"{request_id}:{phone_number}:{purpose}:{code}".encode("utf-8")
    return hmac.new(OTP_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _clean_phone_challenges():
    now = time.time()
    for request_id, challenge in list(phone_challenges.items()):
        if challenge["expiresAt"] + 60 <= now or challenge.get("verified"):
            phone_challenges.pop(request_id, None)


async def _send_sms(phone_number, code):
    if SMS_PROVIDER == "console":
        if AUTH_ENV == "production":
            raise HTTPException(503, "운영 환경 문자 발송 공급자가 설정되지 않았습니다.")
        print(f"[FINDY OTP] {_masked_phone(phone_number)} verification code: {code}")
        return

    if SMS_PROVIDER == "webhook":
        webhook_url = os.environ.get("FINDY_SMS_WEBHOOK_URL", "").strip()
        webhook_token = os.environ.get("FINDY_SMS_WEBHOOK_TOKEN", "").strip()
        if not webhook_url:
            raise HTTPException(503, "문자 발송 Webhook 주소가 설정되지 않았습니다.")
        headers = {"Authorization": f"Bearer {webhook_token}"} if webhook_token else {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json={
                        "phoneNumber": phone_number,
                        "message": f"[FINDY] 인증번호는 {code}입니다. 3분 안에 입력해주세요.",
                    },
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise HTTPException(503, "인증 문자를 발송하지 못했습니다.") from error
        return

    raise HTTPException(503, "지원하지 않는 문자 발송 공급자입니다.")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "providers": {
            provider: bool(os.environ.get(f"{provider.upper()}_CLIENT_ID"))
            for provider in PROVIDER_LABELS
        },
        "phoneVerification": {
            "smsProvider": SMS_PROVIDER,
            "identityProvider": bool(
                os.environ.get("FINDY_IDENTITY_PROVIDER", "").strip()
            ),
        },
    }


@app.post("/v1/phone/otp/request")
async def request_phone_otp(request: PhoneOtpRequest):
    _clean_phone_challenges()
    phone_number = _normalize_korean_phone(request.phoneNumber)
    purpose = request.purpose.strip().lower()
    if purpose not in PHONE_PURPOSES:
        raise HTTPException(400, "지원하지 않는 휴대폰 인증 목적입니다.")

    now = time.time()
    recent = next(
        (
            challenge
            for challenge in phone_challenges.values()
            if challenge["phoneNumber"] == phone_number
            and challenge["purpose"] == purpose
            and now - challenge["createdAt"] < OTP_RESEND_SECONDS
        ),
        None,
    )
    if recent:
        retry_after = max(1, int(OTP_RESEND_SECONDS - (now - recent["createdAt"])))
        raise HTTPException(
            429,
            f"인증번호는 {retry_after}초 후 다시 요청할 수 있습니다.",
        )

    request_id = secrets.token_urlsafe(24)
    code = f"{secrets.randbelow(1_000_000):06d}"
    phone_challenges[request_id] = {
        "phoneNumber": phone_number,
        "purpose": purpose,
        "codeDigest": _otp_digest(request_id, phone_number, purpose, code),
        "createdAt": now,
        "expiresAt": now + OTP_TTL_SECONDS,
        "attempts": 0,
        "verified": False,
    }
    await _send_sms(phone_number, code)
    return {
        "requestId": request_id,
        "maskedPhoneNumber": _masked_phone(phone_number),
        "expiresIn": OTP_TTL_SECONDS,
        "resendAfter": OTP_RESEND_SECONDS,
    }


@app.post("/v1/phone/otp/verify")
def verify_phone_otp(request: PhoneOtpVerifyRequest):
    _clean_phone_challenges()
    challenge = phone_challenges.get(request.requestId)
    if not challenge:
        raise HTTPException(404, "인증 요청을 찾을 수 없거나 만료되었습니다.")
    if challenge["expiresAt"] <= time.time():
        phone_challenges.pop(request.requestId, None)
        raise HTTPException(410, "인증번호가 만료되었습니다. 다시 요청해주세요.")
    if challenge["attempts"] >= OTP_MAX_ATTEMPTS:
        phone_challenges.pop(request.requestId, None)
        raise HTTPException(429, "인증 시도 횟수를 초과했습니다. 다시 요청해주세요.")

    challenge["attempts"] += 1
    candidate = _otp_digest(
        request.requestId,
        challenge["phoneNumber"],
        challenge["purpose"],
        str(request.code or "").strip(),
    )
    if not secrets.compare_digest(candidate, challenge["codeDigest"]):
        remaining = OTP_MAX_ATTEMPTS - challenge["attempts"]
        raise HTTPException(400, f"인증번호가 올바르지 않습니다. 남은 횟수 {remaining}회")

    challenge["verified"] = True
    verification_token = secrets.token_urlsafe(32)
    return {
        "verified": True,
        "verificationToken": verification_token,
        "phoneNumber": challenge["phoneNumber"],
        "maskedPhoneNumber": _masked_phone(challenge["phoneNumber"]),
        "purpose": challenge["purpose"],
    }


@app.post("/v1/identity/start")
def start_identity_verification():
    provider = os.environ.get("FINDY_IDENTITY_PROVIDER", "").strip().lower()
    if not provider:
        raise HTTPException(
            503,
            "PASS 본인확인은 NICE, KCB, 다날, KCP 등 본인확인기관 계약 후 사용할 수 있습니다.",
        )
    raise HTTPException(
        501,
        f"{provider} 본인확인 어댑터의 발급 키와 콜백 설정이 필요합니다.",
    )


@app.post("/v1/oauth/start")
def start_oauth(
    request: StartRequest,
    authorization: Optional[str] = Header(default=None),
):
    _clean_expired_flows()
    provider = request.provider.strip().lower()
    if provider not in PROVIDER_LABELS:
        raise HTTPException(400, "지원하지 않는 로그인 방식입니다.")

    flow_id = secrets.token_urlsafe(24)
    poll_token = secrets.token_urlsafe(32)
    state = secrets.token_urlsafe(32)
    flow = PendingFlow(
        flow_id=flow_id,
        poll_token=poll_token,
        provider=provider,
        state=state,
        expires_at=time.time() + FLOW_TTL_SECONDS,
        link_account_id=(
            _account_from_authorization(authorization)
            if request.linkAccount
            else None
        ),
    )
    flows[flow_id] = flow
    states[state] = flow_id
    return {
        "flowId": flow_id,
        "pollToken": poll_token,
        "authorizationUrl": _authorization_url(provider, state),
        "expiresIn": FLOW_TTL_SECONDS,
    }


async def _callback_values(request: Request):
    if request.method == "POST":
        body = (await request.body()).decode("utf-8")
        return {key: values[-1] for key, values in parse_qs(body).items()}
    return dict(request.query_params)


@app.api_route("/v1/oauth/callback/{provider}", methods=["GET", "POST"])
async def oauth_callback(provider: str, request: Request):
    _clean_expired_flows()
    values = await _callback_values(request)
    state = values.get("state", "")
    flow_id = states.pop(state, None)
    flow = flows.get(flow_id or "")
    if not flow or flow.provider != provider:
        raise HTTPException(400, "로그인 요청을 확인할 수 없습니다.")

    error = values.get("error")
    if error:
        flow.status = "failed"
        flow.message = values.get("error_description") or str(error)
    else:
        try:
            tokens = await _exchange_code(
                provider,
                values.get("code", ""),
                state,
            )
            identity = await _fetch_identity(provider, tokens)
            identity["findyUserId"] = _resolve_findy_account(
                identity,
                preferred_account_id=flow.link_account_id,
            )
            identity["findySessionToken"] = _create_session(
                identity["findyUserId"]
            )
            flow.identity = identity
            flow.status = "completed"
        except Exception as callback_error:
            flow.status = "failed"
            flow.message = "인증 정보를 확인하지 못했습니다."
            print(f"OAuth callback failed for {provider}: {callback_error}")

    label = escape(PROVIDER_LABELS.get(provider, provider))
    result = "완료" if flow.status == "completed" else "실패"
    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="ko">
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width,initial-scale=1">
          <title>FINDY 로그인 {result}</title>
          <body style="font-family:sans-serif;text-align:center;padding:64px 20px;color:#2B2522">
            <h1 style="color:#8B6B4F">FINDY</h1>
            <p>{label} 로그인이 {result}되었습니다.</p>
            <p>이 창을 닫고 FINDY 앱으로 돌아가세요.</p>
          </body>
        </html>
        """
    )


@app.get("/v1/oauth/status/{flow_id}")
def oauth_status(flow_id: str, authorization: Optional[str] = Header(default=None)):
    _clean_expired_flows()
    flow = flows.get(flow_id)
    if not flow:
        raise HTTPException(404, "로그인 요청을 찾을 수 없습니다.")
    supplied_token = (authorization or "").removeprefix("Bearer ").strip()
    if not secrets.compare_digest(supplied_token, flow.poll_token):
        raise HTTPException(401, "로그인 요청 토큰이 올바르지 않습니다.")

    response = {
        "status": flow.status,
        "message": flow.message,
    }
    if flow.status == "completed":
        response["identity"] = flow.identity
        flows.pop(flow_id, None)
    return response


@app.delete("/v1/account")
def delete_account(authorization: Optional[str] = Header(default=None)):
    account_id = _account_from_authorization(authorization)
    with _database() as connection:
        connection.execute(
            "delete from sessions where account_id = ?",
            (account_id,),
        )
        connection.execute(
            "delete from identities where account_id = ?",
            (account_id,),
        )
        connection.execute(
            "delete from accounts where id = ?",
            (account_id,),
        )
    return {"deleted": True}
