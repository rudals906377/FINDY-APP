import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
import uuid
from datetime import datetime, timezone


AUTH_SCHEMA_VERSION = 1
PASSWORD_ITERATIONS = 240_000
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REAL_NAME_RE = re.compile(r"^[가-힣A-Za-z][가-힣A-Za-z .·'’-]{1,29}$")


class AuthError(ValueError):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_write(path, document):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=".findy2-auth-",
            suffix=".tmp",
            delete=False,
        ) as file:
            temp_path = file.name
            json.dump(document, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
        return True
    except (OSError, TypeError, ValueError):
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return False


def _load_auth_document(path):
    if not os.path.exists(path):
        return {"schemaVersion": AUTH_SCHEMA_VERSION, "users": []}
    try:
        with open(path, "r", encoding="utf-8") as file:
            document = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise AuthError("회원 정보를 불러올 수 없습니다.") from error
    if not isinstance(document, dict) or not isinstance(document.get("users"), list):
        raise AuthError("회원 정보 형식이 올바르지 않습니다.")
    if int(document.get("schemaVersion", 0)) > AUTH_SCHEMA_VERSION:
        raise AuthError("더 최신 버전에서 생성된 회원 정보입니다.")
    return document


def _normalize_email(email):
    return str(email or "").strip().lower()


def _normalize_username(username):
    return str(username or "").strip().lower()


def normalize_korean_phone(phone_number):
    digits = "".join(char for char in str(phone_number or "") if char.isdigit())
    if digits.startswith("82"):
        digits = "0" + digits[2:]
    if len(digits) not in {10, 11} or not digits.startswith("01"):
        raise AuthError("올바른 대한민국 휴대폰 번호를 입력해주세요.")
    return digits


def mask_phone_number(phone_number):
    digits = "".join(char for char in str(phone_number or "") if char.isdigit())
    if not digits:
        return ""
    if len(digits) == 11:
        return f"{digits[:3]}-****-{digits[-4:]}"
    return f"{digits[:3]}-***-{digits[-4:]}"


def _phone_hash(phone_number):
    return hashlib.sha256(normalize_korean_phone(phone_number).encode("utf-8")).hexdigest()


def _validate_registration(email, real_name, nickname, password):
    email = _normalize_email(email)
    real_name = " ".join(str(real_name or "").strip().split())
    nickname = str(nickname or "").strip()
    password = str(password or "")
    if email and not EMAIL_RE.match(email):
        raise AuthError("올바른 이메일 주소를 입력해주세요.")
    if not REAL_NAME_RE.match(real_name):
        raise AuthError("이름은 한글 또는 영문 2~30자로 입력해주세요.")
    if not 2 <= len(nickname) <= 20:
        raise AuthError("닉네임은 2~20자로 입력해주세요.")
    if len(password) < 8 or not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
        raise AuthError("비밀번호는 영문과 숫자를 포함해 8자 이상이어야 합니다.")
    return email, real_name, nickname, password


def _hash_password(password, salt=None):
    salt_bytes = bytes.fromhex(salt) if salt else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PASSWORD_ITERATIONS,
    )
    return salt_bytes.hex(), digest.hex()


def _public_user(user):
    return {
        "id": user["id"],
        "email": user["email"],
        "username": user["username"],
        "realName": user.get("realName") or user.get("username") or "",
        "realNameVerified": bool(user.get("realNameVerified")),
        "nickname": user["nickname"],
        "role": user.get("role", "user"),
        "provider": user.get("provider", "email"),
        "provider_label": user.get("provider_label", "이메일"),
        "identities": list(user.get("identities") or []),
        "remoteUserId": user.get("remoteUserId"),
        "phoneNumber": mask_phone_number(user.get("phoneNumber")),
        "phoneVerified": bool(user.get("phoneVerified")),
        "phoneVerificationMethod": user.get("phoneVerificationMethod"),
        "createdAt": user.get("createdAt"),
        "profile": dict(user.get("profile") or {}),
    }


def _unique_username(document, candidate):
    cleaned = re.sub(r"[^a-z0-9._]", "", _normalize_username(candidate))
    cleaned = cleaned.strip("._")[:20]
    if len(cleaned) < 3:
        cleaned = f"findy_{secrets.token_hex(3)}"
    username = cleaned
    suffix = 1
    existing = {item.get("username") for item in document["users"]}
    while username in existing:
        tail = str(suffix)
        username = f"{cleaned[:20 - len(tail)]}{tail}"
        suffix += 1
    return username


def social_login_or_register(path, identity, link_user_id=None):
    """Resolve a verified provider identity into one FINDY integrated account."""
    identity = dict(identity or {})
    provider = str(identity.get("provider") or "").strip().lower()
    provider_user_id = str(identity.get("providerUserId") or "").strip()
    remote_user_id = str(identity.get("findyUserId") or "").strip()
    if not provider or not provider_user_id:
        raise AuthError("소셜 계정 식별 정보가 올바르지 않습니다.")

    provider_labels = {
        "naver": "네이버",
        "kakao": "카카오",
        "google": "Google",
        "apple": "Apple",
    }
    if provider not in provider_labels:
        raise AuthError("지원하지 않는 소셜 로그인 방식입니다.")

    document = _load_auth_document(path)
    email = _normalize_email(identity.get("email"))
    email_verified = bool(identity.get("emailVerified"))
    nickname = str(identity.get("nickname") or "").strip() or f"{provider_labels[provider]} 회원"
    avatar_url = str(identity.get("avatarUrl") or "").strip()

    user = None
    if link_user_id:
        user = next(
            (item for item in document["users"] if item.get("id") == link_user_id),
            None,
        )
        if not user:
            raise AuthError("연결할 FINDY 계정을 찾을 수 없습니다.")

    if user is None and remote_user_id:
        user = next(
            (
                item
                for item in document["users"]
                if item.get("remoteUserId") == remote_user_id
                or item.get("id") == remote_user_id
            ),
            None,
        )

    if user is None:
        user = next(
            (
                item
                for item in document["users"]
                if any(
                    linked.get("provider") == provider
                    and linked.get("providerUserId") == provider_user_id
                    for linked in item.get("identities", [])
                )
            ),
            None,
        )

    if user is None and email and email_verified:
        user = next(
            (item for item in document["users"] if item.get("email") == email),
            None,
        )

    identity_record = {
        "provider": provider,
        "providerUserId": provider_user_id,
        "email": email,
        "emailVerified": email_verified,
        "linkedAt": _now(),
    }

    if user is None:
        internal_email = email if email else f"{provider}_{provider_user_id}@social.findy.local"
        username_seed = email.split("@")[0] if email else f"{provider}_{provider_user_id}"
        username = _unique_username(document, username_seed)
        user = {
            "id": remote_user_id or f"user_{uuid.uuid4().hex}",
            "remoteUserId": remote_user_id or None,
            "email": internal_email,
            "username": username,
            "nickname": nickname,
            "role": "user",
            "provider": provider,
            "provider_label": provider_labels[provider],
            "createdAt": _now(),
            "updatedAt": _now(),
            "identities": [identity_record],
            "profile": {
                "name": nickname,
                "username": username,
                "avatarUrl": avatar_url,
            },
        }
        document["users"].append(user)
    else:
        identities = list(user.get("identities") or [])
        existing_identity = next(
            (
                item
                for item in identities
                if item.get("provider") == provider
                and item.get("providerUserId") == provider_user_id
            ),
            None,
        )
        if existing_identity:
            existing_identity.update(identity_record)
        else:
            identities.append(identity_record)
        user["identities"] = identities
        if remote_user_id:
            user["remoteUserId"] = remote_user_id
        user["provider"] = provider
        user["provider_label"] = provider_labels[provider]
        user["updatedAt"] = _now()
        if email and email_verified and user.get("email", "").endswith("@social.findy.local"):
            user["email"] = email
        if avatar_url:
            user.setdefault("profile", {})["avatarUrl"] = avatar_url

    if not _atomic_write(path, document):
        raise AuthError("통합회원 정보를 저장하지 못했습니다.")
    return _public_user(user)


def get_or_create_demo_user(path):
    """Return a local-only account used while external auth is not configured."""
    document = _load_auth_document(path)
    user = next(
        (item for item in document["users"] if item.get("isDemoAccount")),
        None,
    )
    if user is None:
        username = _unique_username(document, "findy_demo")
        user = {
            "id": "user_findy2_demo",
            "email": "",
            "username": username,
            "realName": "FINDY 체험회원",
            "realNameVerified": False,
            "nickname": "FINDY 회원",
            "role": "user",
            "provider": "demo",
            "provider_label": "체험 로그인",
            "phoneNumber": "",
            "phoneHash": "",
            "phoneVerified": False,
            "phoneVerificationMethod": None,
            "isDemoAccount": True,
            "createdAt": _now(),
            "updatedAt": _now(),
            "profile": {
                "name": "FINDY 회원",
                "username": "FINDY 회원",
                "realName": "FINDY 체험회원",
            },
        }
        document["users"].append(user)
        if not _atomic_write(path, document):
            raise AuthError("체험 계정을 준비하지 못했습니다.")
    return _public_user(user)


def register_user(
    path,
    email,
    username,
    nickname,
    password,
    phone_number="",
    phone_verified=False,
    phone_verification_method="sms",
):
    email, real_name, nickname, password = _validate_registration(email, username, nickname, password)
    document = _load_auth_document(path)
    if email and any(user.get("email") == email for user in document["users"]):
        raise AuthError("이미 가입된 이메일입니다.")
    normalized_phone = ""
    phone_hash = ""
    if phone_number:
        normalized_phone = normalize_korean_phone(phone_number)
        if not phone_verified:
            raise AuthError("휴대폰 인증을 완료해주세요.")
        phone_hash = _phone_hash(normalized_phone)
        if any(user.get("phoneHash") == phone_hash for user in document["users"]):
            raise AuthError("이미 가입에 사용된 휴대폰 번호입니다.")
    if not normalized_phone:
        raise AuthError("휴대폰 인증을 완료해주세요.")

    salt, password_hash = _hash_password(password)
    username = _unique_username(
        document,
        f"findy_{normalized_phone[-4:]}_{secrets.token_hex(2)}",
    )
    user = {
        "id": f"user_{uuid.uuid4().hex}",
        "email": email,
        "username": username,
        "realName": real_name,
        "realNameVerified": phone_verification_method == "pass",
        "nickname": nickname,
        "role": "user",
        "provider": "email",
        "provider_label": "이메일",
        "passwordSalt": salt,
        "passwordHash": password_hash,
        "passwordIterations": PASSWORD_ITERATIONS,
        "phoneNumber": normalized_phone,
        "phoneHash": phone_hash,
        "phoneVerified": bool(normalized_phone and phone_verified),
        "phoneVerificationMethod": (
            str(phone_verification_method or "sms")
            if normalized_phone and phone_verified
            else None
        ),
        "createdAt": _now(),
        "updatedAt": _now(),
        "profile": {
            "name": nickname,
            "username": username,
            "realName": real_name,
        },
    }
    document["users"].append(user)
    if not _atomic_write(path, document):
        raise AuthError("회원가입 정보를 저장하지 못했습니다.")
    return _public_user(user)


def find_usernames_by_phone(path, phone_number):
    phone_hash = _phone_hash(phone_number)
    document = _load_auth_document(path)
    matches = [
        user
        for user in document["users"]
        if user.get("phoneVerified") and user.get("phoneHash") == phone_hash
    ]
    return [
        {
            "username": user.get("username", ""),
            "realName": user.get("realName") or user.get("username", ""),
            "email": _mask_email(user.get("email", "")),
            "providerLabel": user.get("provider_label", "이메일"),
        }
        for user in matches
    ]


def find_user_by_phone(path, phone_number):
    phone_hash = _phone_hash(phone_number)
    document = _load_auth_document(path)
    user = next(
        (
            item
            for item in document["users"]
            if item.get("phoneVerified") and item.get("phoneHash") == phone_hash
        ),
        None,
    )
    if not user:
        raise AuthError("인증된 휴대폰 번호로 가입한 계정을 찾을 수 없습니다.")
    return _public_user(user)


def _mask_email(email):
    local, separator, domain = str(email or "").partition("@")
    if not separator:
        return ""
    visible = local[:2] if len(local) >= 2 else local[:1]
    return f"{visible}{'*' * max(2, len(local) - len(visible))}@{domain}"


def reset_password_by_phone(path, phone_number, new_password):
    phone_hash = _phone_hash(phone_number)
    new_password = str(new_password or "")
    if len(new_password) < 8 or not any(char.isalpha() for char in new_password) or not any(char.isdigit() for char in new_password):
        raise AuthError("비밀번호는 영문과 숫자를 포함해 8자 이상이어야 합니다.")
    document = _load_auth_document(path)
    user = next(
        (
            item
            for item in document["users"]
            if item.get("phoneVerified") and item.get("phoneHash") == phone_hash
        ),
        None,
    )
    if not user:
        raise AuthError("인증된 휴대폰 번호로 가입한 계정을 찾을 수 없습니다.")
    salt, password_hash = _hash_password(new_password)
    user["passwordSalt"] = salt
    user["passwordHash"] = password_hash
    user["passwordIterations"] = PASSWORD_ITERATIONS
    user["updatedAt"] = _now()
    if not _atomic_write(path, document):
        raise AuthError("비밀번호를 변경하지 못했습니다.")
    return _public_user(user)


def authenticate_user(path, identifier, password):
    raw_identifier = str(identifier or "").strip()
    document = _load_auth_document(path)
    user = None
    try:
        phone_hash = _phone_hash(raw_identifier)
        user = next(
            (
                item
                for item in document["users"]
                if item.get("phoneVerified") and item.get("phoneHash") == phone_hash
            ),
            None,
        )
    except AuthError:
        email = _normalize_email(raw_identifier)
        user = next(
            (item for item in document["users"] if item.get("email") == email),
            None,
        )
    if not user:
        raise AuthError("휴대폰 번호 또는 비밀번호가 올바르지 않습니다.")
    if not user.get("passwordSalt") or not user.get("passwordHash"):
        raise AuthError(f"{user.get('provider_label', '소셜')} 로그인으로 가입한 계정입니다.")
    _, candidate_hash = _hash_password(str(password or ""), user.get("passwordSalt"))
    if not hmac.compare_digest(candidate_hash, user.get("passwordHash", "")):
        raise AuthError("휴대폰 번호 또는 비밀번호가 올바르지 않습니다.")
    return _public_user(user)


def attach_verified_phone(
    path,
    user_id,
    phone_number,
    verification_method="sms",
    real_name="",
):
    document = _load_auth_document(path)
    user = next((item for item in document["users"] if item.get("id") == user_id), None)
    if not user:
        raise AuthError("회원 정보를 찾을 수 없습니다.")
    normalized_phone = normalize_korean_phone(phone_number)
    phone_hash = _phone_hash(normalized_phone)
    if any(
        item.get("id") != user_id and item.get("phoneHash") == phone_hash
        for item in document["users"]
    ):
        raise AuthError("이미 다른 FINDY 계정에 연결된 휴대폰 번호입니다.")
    user["phoneNumber"] = normalized_phone
    user["phoneHash"] = phone_hash
    user["phoneVerified"] = True
    user["phoneVerificationMethod"] = verification_method
    if real_name:
        normalized_name = " ".join(str(real_name).strip().split())
        if not REAL_NAME_RE.match(normalized_name):
            raise AuthError("이름은 한글 또는 영문 2~30자로 입력해주세요.")
        user["realName"] = normalized_name
        user["realNameVerified"] = verification_method == "pass"
        user.setdefault("profile", {})["realName"] = normalized_name
    user["updatedAt"] = _now()
    if not _atomic_write(path, document):
        raise AuthError("휴대폰 정보를 저장하지 못했습니다.")
    return _public_user(user)


def create_session(path, user, remote_session_token=None):
    session = {
        "schemaVersion": 1,
        "sessionToken": secrets.token_urlsafe(32),
        "userId": user["id"],
        "createdAt": _now(),
    }
    if remote_session_token:
        session["remoteSessionToken"] = str(remote_session_token)
    if not _atomic_write(path, session):
        raise AuthError("로그인 상태를 저장하지 못했습니다.")
    return session


def restore_session(auth_path, session_path):
    if not os.path.exists(session_path):
        return None
    try:
        with open(session_path, "r", encoding="utf-8") as file:
            session = json.load(file)
        user_id = session.get("userId")
        if not user_id or not session.get("sessionToken"):
            return None
        document = _load_auth_document(auth_path)
        user = next((item for item in document["users"] if item.get("id") == user_id), None)
        return _public_user(user) if user else None
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def clear_session(path):
    try:
        if os.path.exists(path):
            os.remove(path)
        return True
    except OSError:
        return False


def read_remote_session_token(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return str(json.load(file).get("remoteSessionToken") or "")
    except (OSError, ValueError, json.JSONDecodeError):
        return ""


def update_user_profile(path, user_id, profile):
    document = _load_auth_document(path)
    user = next((item for item in document["users"] if item.get("id") == user_id), None)
    if not user:
        raise AuthError("회원 정보를 찾을 수 없습니다.")
    clean_profile = dict(profile or {})
    clean_profile["realName"] = user.get("realName") or clean_profile.get("realName", "")
    clean_profile["username"] = clean_profile.get("name") or user.get("nickname", "FINDY 회원")
    nickname = str(clean_profile.get("name") or "").strip()
    if not 2 <= len(nickname) <= 20:
        raise AuthError("닉네임은 2~20자로 입력해주세요.")
    clean_profile["name"] = nickname
    clean_profile["username"] = nickname
    user["profile"] = clean_profile
    user["nickname"] = nickname
    user["updatedAt"] = _now()
    if not _atomic_write(path, document):
        raise AuthError("프로필을 저장하지 못했습니다.")
    return _public_user(user)


def delete_user(path, user_id, password=None, verified_social=False):
    """Delete an email account after verifying its password."""
    document = _load_auth_document(path)
    user = next((item for item in document["users"] if item.get("id") == user_id), None)
    if not user:
        raise AuthError("회원 정보를 찾을 수 없습니다.")
    if user.get("provider", "email") != "email":
        if not verified_social:
            raise AuthError("소셜 로그인 재확인이 필요합니다.")
    else:
        _, candidate_hash = _hash_password(str(password or ""), user.get("passwordSalt"))
        if not hmac.compare_digest(candidate_hash, user.get("passwordHash", "")):
            raise AuthError("비밀번호가 올바르지 않습니다.")

    document["users"] = [
        item for item in document["users"] if item.get("id") != user_id
    ]
    if not _atomic_write(path, document):
        raise AuthError("계정을 삭제하지 못했습니다.")
    return True
