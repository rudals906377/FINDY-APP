from dataclasses import dataclass

import httpx


class PhoneAuthError(ValueError):
    pass


@dataclass(frozen=True)
class PhoneOtpFlow:
    request_id: str
    masked_phone_number: str
    expires_in: int
    resend_after: int


def phone_auth_is_configured(base_url):
    return bool(str(base_url or "").strip())


def _error_message(response, fallback):
    try:
        detail = response.json().get("detail")
        return str(detail or fallback)
    except (ValueError, AttributeError):
        return fallback


async def request_phone_otp(base_url, phone_number, purpose):
    if not phone_auth_is_configured(base_url):
        raise PhoneAuthError("FINDY 인증 서버 주소가 설정되지 않았습니다.")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{base_url}/v1/phone/otp/request",
                json={"phoneNumber": phone_number, "purpose": purpose},
            )
    except httpx.HTTPError as error:
        raise PhoneAuthError("휴대폰 인증 서버에 연결하지 못했습니다.") from error
    if response.is_error:
        raise PhoneAuthError(_error_message(response, "인증번호를 발송하지 못했습니다."))
    try:
        data = response.json()
        return PhoneOtpFlow(
            request_id=str(data["requestId"]),
            masked_phone_number=str(data["maskedPhoneNumber"]),
            expires_in=int(data["expiresIn"]),
            resend_after=int(data["resendAfter"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise PhoneAuthError("휴대폰 인증 서버 응답 형식이 올바르지 않습니다.") from error


async def verify_phone_otp(base_url, flow, code):
    if not phone_auth_is_configured(base_url):
        raise PhoneAuthError("FINDY 인증 서버 주소가 설정되지 않았습니다.")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{base_url}/v1/phone/otp/verify",
                json={"requestId": flow.request_id, "code": code},
            )
    except httpx.HTTPError as error:
        raise PhoneAuthError("휴대폰 인증 결과를 확인하지 못했습니다.") from error
    if response.is_error:
        raise PhoneAuthError(_error_message(response, "인증번호를 확인하지 못했습니다."))
    try:
        data = response.json()
    except ValueError as error:
        raise PhoneAuthError("휴대폰 인증 서버 응답 형식이 올바르지 않습니다.") from error
    if not data.get("verified") or not data.get("phoneNumber"):
        raise PhoneAuthError("휴대폰 인증이 완료되지 않았습니다.")
    return data
