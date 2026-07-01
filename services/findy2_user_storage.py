import json
import os
import shutil
import tempfile
from copy import deepcopy


SCHEMA_VERSION = 1

PERSISTED_KEYS = (
    "saved_ids",
    "community_posts",
    "content_comments",
    "comment_liked_ids",
    "answered_question_ids",
    "content_reports",
    "admin_action_logs",
    "community_liked_ids",
    "community_saved_ids",
    "written_snaps",
    "snap_liked_ids",
    "snap_saved_ids",
    "snap_followed_creators",
    "written_videos",
    "video_comments",
    "video_liked_keys",
    "video_saved_keys",
    "video_followed_creators",
    "video_reposted_keys",
    "written_reviews",
    "review_reports",
    "admin_notices",
    "reported_content_ids",
    "hidden_content_ids",
    "user_profile",
    "location_state",
    "recent_searches",
    "app_settings",
    "consent_records",
    "point_wallets",
    "point_transactions",
)

SET_KEYS = {
    "saved_ids",
    "community_liked_ids",
    "community_saved_ids",
    "comment_liked_ids",
    "answered_question_ids",
    "snap_liked_ids",
    "snap_saved_ids",
    "snap_followed_creators",
    "video_liked_keys",
    "video_saved_keys",
    "video_followed_creators",
    "video_reposted_keys",
    "reported_content_ids",
    "hidden_content_ids",
}


def user_scoped_data_path(base_path, user_id):
    """Return a stable per-user JSON path without changing configured folders."""
    base = os.path.abspath(os.path.expanduser(base_path))
    root, extension = os.path.splitext(base)
    safe_user_id = "".join(
        char if char.isalnum() or char in {"-", "_"} else "_"
        for char in str(user_id or "guest")
    )
    return f"{root}.{safe_user_id}{extension or '.json'}"


def _json_value(value):
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def build_user_data_document(state):
    return {
        "schemaVersion": SCHEMA_VERSION,
        "data": {
            key: _json_value(state.get(key))
            for key in PERSISTED_KEYS
            if key in state
        },
    }


def save_findy2_user_data(path, state):
    """Atomically persist user-generated FINDY2 data with a last-good backup."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    document = build_user_data_document(state)
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=".findy2-",
            suffix=".tmp",
            delete=False,
        ) as file:
            temp_path = file.name
            json.dump(document, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())

        if os.path.exists(path):
            shutil.copy2(path, path + ".bak")
        os.replace(temp_path, path)
        return True
    except (OSError, TypeError, ValueError) as error:
        print(f"Failed to save FINDY2 user data: {error}")
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return False


def _read_document(path):
    with open(path, "r", encoding="utf-8") as file:
        document = json.load(file)
    if not isinstance(document, dict):
        raise ValueError("FINDY2 user data must be a JSON object.")
    if int(document.get("schemaVersion", 0)) > SCHEMA_VERSION:
        raise ValueError("FINDY2 user data was created by a newer app version.")
    data = document.get("data", {})
    if not isinstance(data, dict):
        raise ValueError("FINDY2 user data payload must be a JSON object.")
    return data


def _merge_profile(default_profile, saved_profile):
    merged = deepcopy(default_profile or {})
    if isinstance(saved_profile, dict):
        merged.update(saved_profile)
    return merged


def load_findy2_user_data(path, default_state):
    """Load persisted fields only, falling back to the backup on corruption."""
    data = None
    for candidate in (path, path + ".bak"):
        if not os.path.exists(candidate):
            continue
        try:
            data = _read_document(candidate)
            break
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            print(f"Failed to load FINDY2 user data from {candidate}: {error}")

    if data is None:
        return {}

    restored = {}
    for key in PERSISTED_KEYS:
        if key not in data:
            continue
        value = data[key]
        if key in SET_KEYS:
            restored[key] = set(value or [])
        elif key == "user_profile":
            restored[key] = _merge_profile(default_state.get(key), value)
        else:
            restored[key] = deepcopy(value)
    return restored


def delete_findy2_user_data(path):
    """Remove a user's local data document and its last-good backup."""
    removed = False
    for candidate in (path, path + ".bak"):
        try:
            if os.path.exists(candidate):
                os.remove(candidate)
                removed = True
        except OSError:
            return False
    return removed or not any(os.path.exists(item) for item in (path, path + ".bak"))
