import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx


SOCIAL_PROVIDERS = {
    "naver": {
        "label": "네이버",
        "asset": "naver.png",
        "background": "#03C75A",
        "foreground": "#FFFFFF",
    },
    "kakao": {
        "label": "카카오",
        "asset": "kakao.png",
        "background": "#FEE500",
        "foreground": "#191919",
    },
    "google": {
        "label": "Google",
        "asset": "google.png",
        "background": "#FFFFFF",
        "foreground": "#202124",
    },
    "apple": {
        "label": "Apple",
        "asset": "apple.png",
        "background": "#111111",
        "foreground": "#FFFFFF",
    },
}


class SocialAuthError(ValueError):
    pass


@dataclass(frozen=True)
class SocialAuthFlow:
    provider: str
    flow_id: str
    poll_token: str
    authorization_url: str


def social_auth_is_configured(base_url):
    return bool(str(base_url or "").strip())


def _provider(provider):
    normalized = str(provider or "").strip().lower()
    if normalized not in SOCIAL_PROVIDERS:
        raise SocialAuthError("지원하지 않는 소셜 로그인 방식입니다.")
    return normalized


async def start_social_auth(
    base_url,
    provider,
    remote_session_token=None,
    link_account=False,
):
    provider = _provider(provider)
    if not social_auth_is_configured(base_url):
        raise SocialAuthError("FINDY 통합 로그인 서버 주소가 설정되지 않았습니다.")

    payload = {
        "provider": provider,
        "client": "findy2",
        "platform": "flet",
    }
    payload["linkAccount"] = bool(link_account)
    headers = {}
    if remote_session_token:
        headers["Authorization"] = f"Bearer {remote_session_token}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{base_url}/v1/oauth/start",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise SocialAuthError("통합 로그인 서버에 연결하지 못했습니다.") from error

    required = ("flowId", "pollToken", "authorizationUrl")
    if not all(data.get(key) for key in required):
        raise SocialAuthError("통합 로그인 서버 응답 형식이 올바르지 않습니다.")
    return SocialAuthFlow(
        provider=provider,
        flow_id=str(data["flowId"]),
        poll_token=str(data["pollToken"]),
        authorization_url=str(data["authorizationUrl"]),
    )


async def wait_for_social_auth(
    base_url,
    flow,
    timeout_seconds=180,
    poll_interval=1.2,
):
    elapsed = 0.0
    headers = {"Authorization": f"Bearer {flow.poll_token}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        while elapsed < timeout_seconds:
            try:
                response = await client.get(
                    f"{base_url}/v1/oauth/status/{flow.flow_id}",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
            except (httpx.HTTPError, ValueError) as error:
                raise SocialAuthError("로그인 결과를 확인하지 못했습니다.") from error

            status = str(data.get("status") or "").lower()
            if status == "completed":
                identity = data.get("identity")
                if not isinstance(identity, dict):
                    raise SocialAuthError("회원 정보 응답이 올바르지 않습니다.")
                identity["provider"] = _provider(
                    identity.get("provider") or flow.provider
                )
                if not identity.get("providerUserId"):
                    raise SocialAuthError("소셜 계정 식별자를 확인하지 못했습니다.")
                return identity
            if status in {"failed", "cancelled", "expired"}:
                message = data.get("message") or "소셜 로그인이 취소되었거나 만료되었습니다."
                raise SocialAuthError(str(message))

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

    raise SocialAuthError("로그인 시간이 초과되었습니다. 다시 시도해주세요.")


async def delete_social_account(base_url, session_token):
    if not social_auth_is_configured(base_url) or not session_token:
        raise SocialAuthError("통합 로그인 서버 세션을 확인할 수 없습니다.")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.delete(
                f"{base_url}/v1/account",
                headers={"Authorization": f"Bearer {session_token}"},
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise SocialAuthError("통합회원 계정을 삭제하지 못했습니다.") from error
    if not data.get("deleted"):
        raise SocialAuthError("통합회원 계정 삭제 결과를 확인하지 못했습니다.")
    return True
