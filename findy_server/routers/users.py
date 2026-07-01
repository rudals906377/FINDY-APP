from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ..database import connect, now_iso, row_to_dict, rows_to_dicts
from ..schemas import ConsentInput, LocationPreferenceInput, UserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("")
def create_user(payload: UserCreate):
    now = now_iso()
    with connect() as conn:
        existing = conn.execute("SELECT * FROM users WHERE id = ?", (payload.id,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="이미 존재하는 사용자입니다.")
        conn.execute(
            """
            INSERT INTO users (id, phone, real_name, nickname, status, points, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'active', 0, ?, ?)
            """,
            (payload.id, payload.phone, payload.realName, payload.nickname, now, now),
        )
        user = conn.execute("SELECT * FROM users WHERE id = ?", (payload.id,)).fetchone()
    return row_to_dict(user)


@router.get("")
def list_users(status: str = "active"):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    return {"items": rows_to_dicts(rows)}


@router.get("/{user_id}")
def get_user(user_id: str):
    with connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return row_to_dict(user)


@router.post("/consents")
def save_consent(payload: ConsentInput):
    now = now_iso()
    record_id = f"consent_{uuid4().hex}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO consent_records
            (id, user_id, consent_type, is_agreed, policy_version, agreed_at, withdrawn_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                payload.userId,
                payload.consentType,
                1 if payload.isAgreed else 0,
                payload.policyVersion,
                now if payload.isAgreed else None,
                None if payload.isAgreed else now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM consent_records WHERE id = ?", (record_id,)).fetchone()
    return row_to_dict(row)


@router.get("/{user_id}/consents")
def list_consents(user_id: str):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM consent_records WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return {"items": rows_to_dicts(rows)}


@router.put("/{user_id}/location")
def upsert_location_preference(user_id: str, payload: LocationPreferenceInput):
    now = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO location_preferences
            (user_id, location_permission_status, selected_region, location_enabled, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                location_permission_status = excluded.location_permission_status,
                selected_region = excluded.selected_region,
                location_enabled = excluded.location_enabled,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                payload.locationPermissionStatus,
                payload.selectedRegion,
                1 if payload.locationEnabled else 0,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM location_preferences WHERE user_id = ?", (user_id,)).fetchone()
    return row_to_dict(row)

