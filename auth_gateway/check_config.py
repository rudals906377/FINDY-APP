import os
import sys
from urllib.parse import urlparse


PROVIDERS = {
    "NAVER": ("CLIENT_ID", "CLIENT_SECRET"),
    "KAKAO": ("CLIENT_ID", "CLIENT_SECRET"),
    "GOOGLE": ("CLIENT_ID", "CLIENT_SECRET"),
    "APPLE": ("CLIENT_ID", "TEAM_ID", "KEY_ID", "PRIVATE_KEY"),
}


def configured(name):
    return bool(str(os.environ.get(name) or "").strip())


def main():
    public_url = str(os.environ.get("FINDY_AUTH_PUBLIC_URL") or "").strip()
    parsed = urlparse(public_url)
    production_url = parsed.scheme == "https" and bool(parsed.netloc)

    print("FINDY Auth Gateway configuration")
    print(f"- Public URL: {'configured' if public_url else 'missing'}")
    if public_url:
        print(f"- HTTPS ready: {'yes' if production_url else 'no (local development only)'}")

    complete = True
    for provider, suffixes in PROVIDERS.items():
        missing = [
            f"{provider}_{suffix}"
            for suffix in suffixes
            if not configured(f"{provider}_{suffix}")
        ]
        if missing:
            complete = False
            print(f"- {provider}: missing {', '.join(missing)}")
        else:
            print(f"- {provider}: configured")

    auth_env = str(os.environ.get("FINDY_AUTH_ENV") or "development").strip().lower()
    sms_provider = str(os.environ.get("FINDY_SMS_PROVIDER") or "console").strip().lower()
    otp_secret_ready = configured("FINDY_OTP_SECRET") and len(
        str(os.environ.get("FINDY_OTP_SECRET") or "")
    ) >= 24
    sms_ready = sms_provider != "console"
    print(f"- SMS provider: {sms_provider}")
    print(f"- OTP secret: {'configured' if otp_secret_ready else 'missing or too short'}")
    print(
        f"- PASS identity provider: "
        f"{os.environ.get('FINDY_IDENTITY_PROVIDER') or 'not configured'}"
    )
    if auth_env == "production" and (not sms_ready or not otp_secret_ready):
        complete = False

    if not public_url:
        complete = False
    if complete and production_url:
        print("OK: production provider configuration is complete")
        return 0
    print("NOT READY: fill missing values before real OAuth testing")
    return 1


if __name__ == "__main__":
    sys.exit(main())
