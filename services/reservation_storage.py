import json
import os


def save_reservation_history(path, history):
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(history or [], file, ensure_ascii=False, indent=2)
        return True
    except (OSError, TypeError, ValueError) as error:
        print(f"Failed to save reservation history: {error}")
        return False


def load_reservation_history(path, normalizer=None):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as file:
            loaded = json.load(file)
        if not isinstance(loaded, list):
            return []
        if normalizer is None:
            return loaded
        return [normalizer(item) for item in loaded]
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"Failed to load reservation history: {error}")
        return []
