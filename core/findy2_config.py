import json
import os
from typing import Optional


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
PUBLIC_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "findy2_public_config.json",
)


def _load_public_config():
    try:
        with open(PUBLIC_CONFIG_PATH, "r", encoding="utf-8") as file:
            document = json.load(file)
        return document if isinstance(document, dict) else {}
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


PUBLIC_CONFIG = _load_public_config()
RESERVATION_STORAGE_PATH = os.path.join(PROJECT_ROOT, "reservation_history.json")
FINDY2_USER_DATA_PATH = os.environ.get(
    "FINDY2_USER_DATA_PATH",
    os.path.join(os.path.expanduser("~"), ".findy", "FINDY2", "user_data.json"),
)
FINDY2_AUTH_DATA_PATH = os.environ.get(
    "FINDY2_AUTH_DATA_PATH",
    os.path.join(os.path.expanduser("~"), ".findy", "FINDY2", "users.json"),
)
FINDY2_SESSION_PATH = os.environ.get(
    "FINDY2_SESSION_PATH",
    os.path.join(os.path.expanduser("~"), ".findy", "FINDY2", "session.json"),
)
FINDY2_MEDIA_DIR = os.environ.get(
    "FINDY2_MEDIA_DIR",
    os.path.join(os.path.expanduser("~"), ".findy", "FINDY2", "media"),
)
FINDY2_AUTH_API_URL = os.environ.get(
    "FINDY2_AUTH_API_URL",
    str(PUBLIC_CONFIG.get("authApiUrl") or ""),
).rstrip("/")
FINDY2_API_URL = os.environ.get(
    "FINDY2_API_URL",
    str(PUBLIC_CONFIG.get("apiUrl") or ""),
).rstrip("/")
FINDY2_ADMIN_API_KEY = os.environ.get(
    "FINDY2_ADMIN_API_KEY",
    str(PUBLIC_CONFIG.get("adminApiKey") or ""),
)
FINDY2_SOCIAL_AUTH_TIMEOUT_SECONDS = int(
    os.environ.get("FINDY2_SOCIAL_AUTH_TIMEOUT_SECONDS", "180")
)
FINDY2_DEMO_LOGIN_ENABLED = os.environ.get(
    "FINDY2_DEMO_LOGIN_ENABLED",
    "true",
).strip().lower() in {"1", "true", "yes", "on"}

# FINDY2 is the community-first release. The implementations remain available
# for the future FINDY service, while current entry points stay disabled.
FINDY2_RESERVATION_ENABLED = False
FINDY2_DIRECT_MESSAGE_ENABLED = False


def resolve_asset_file(name: str) -> Optional[str]:
    candidates = [
        name,
        name + ".png" if not name.lower().endswith(".png") else name + ".png",
        name[:-4] if name.lower().endswith(".png.png") else None,
    ]
    cleaned = []
    for item in candidates:
        if item and item not in cleaned:
            cleaned.append(item)

    search_dirs = [
        ASSETS_DIR,
        os.path.join(PROJECT_ROOT, "assets"),
        os.path.join(os.getcwd(), "assets"),
    ]
    for folder in search_dirs:
        for candidate in cleaned:
            path = os.path.join(folder, candidate)
            if os.path.exists(path):
                return path
    return None
