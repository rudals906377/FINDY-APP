import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESERVATION_STORAGE_PATH = os.path.join(BASE_DIR, "reservation_history.json")

def normalize_reservation_history_item(item):
    normalized = dict(item or {})
    if normalized.get("status") == "예약 요청 완료":
        normalized["status"] = "예약 완료"
    if not normalized.get("service"):
        normalized["service"] = normalized.get("category") or "기본 시술"
    return normalized

def load_history():
    if not os.path.exists(RESERVATION_STORAGE_PATH):
        return []
    try:
        with open(RESERVATION_STORAGE_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, list):
            return [normalize_reservation_history_item(item) for item in loaded]
    except Exception:
        return []
    return []

def save_history(items):
    try:
        with open(RESERVATION_STORAGE_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        return True
    except Exception as exc:
        print(f"Failed to save reservation history: {exc}")
        return False

def is_reservation_active(item):
    return item.get("status") not in {"예약 취소", "시술 완료"}

def is_time_already_booked(history, artist_id, date_value, time_value):
    for item in history:
        if not is_reservation_active(item):
            continue
        if item.get("artist_id") == artist_id and item.get("date") == date_value and item.get("time") == time_value:
            return True
    return False

def build_slots(start="09:00", end="22:00", slot_minutes=30):
    current = datetime.strptime(start, "%H:%M")
    slot_end = datetime.strptime(end, "%H:%M")
    slots = []
    while current <= slot_end:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=slot_minutes)
    return slots

def build_reservation_item(history, form):
    return {
        "id": f'r{len(history) + 1}',
        "artist_id": form.get("artist_id"),
        "artist_name": form.get("artist_name", ""),
        "job": form.get("job", ""),
        "category": form.get("category", ""),
        "service": form.get("service", "기본 시술"),
        "date": form.get("date"),
        "time": form.get("time"),
        "note": form.get("note", ""),
        "status": "예약 완료",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

def save_reservation(history, form):
    if not form.get("artist_id") or not form.get("date") or not form.get("time"):
        return None, "예약 정보를 다시 확인해주세요."

    if is_time_already_booked(history, form["artist_id"], form["date"], form["time"]):
        return None, "이미 예약이 마감된 시간이에요."

    item = build_reservation_item(history, form)
    history.append(item)
    if not save_history(history):
        history.remove(item)
        return None, "예약 저장에 실패했어요. 다시 시도해주세요."
    return item, None

def cancel_reservation(history, reservation_id):
    for item in history:
        if item.get("id") == reservation_id:
            previous_status = item.get("status")
            previous_cancelled_at = item.get("cancelled_at")
            item["status"] = "예약 취소"
            item["cancelled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            if not save_history(history):
                item["status"] = previous_status
                if previous_cancelled_at is None:
                    item.pop("cancelled_at", None)
                else:
                    item["cancelled_at"] = previous_cancelled_at
                return None
            return item
    return None

def reservation_datetime(date_value, time_value):
    if not date_value or not time_value:
        return None
    try:
        return datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
    except Exception:
        return None

def classify_history_item(item):
    if item.get("status") == "예약 취소":
        return "cancelled"

    dt = reservation_datetime(item.get("date"), item.get("time"))
    if dt and dt < datetime.now():
        return "past"

    return "upcoming"
