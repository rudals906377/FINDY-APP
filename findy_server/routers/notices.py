from uuid import uuid4

from fastapi import APIRouter, Depends

from ..database import connect, now_iso, row_to_dict, rows_to_dicts
from ..dependencies import require_admin
from ..schemas import EventInput, NoticeInput

router = APIRouter(tags=["notices"])


@router.get("/notices")
def list_notices(status: str = "visible"):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM notices WHERE status = ? ORDER BY pinned DESC, created_at DESC",
            (status,),
        ).fetchall()
    return {"items": rows_to_dicts(rows)}


@router.post("/admin/notices", dependencies=[Depends(require_admin)])
def create_notice(payload: NoticeInput):
    now = now_iso()
    notice_id = f"notice_{uuid4().hex}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO notices (id, title, body, status, pinned, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (notice_id, payload.title, payload.body, payload.status, 1 if payload.pinned else 0, now, now),
        )
        row = conn.execute("SELECT * FROM notices WHERE id = ?", (notice_id,)).fetchone()
    return row_to_dict(row)


@router.patch("/admin/notices/{notice_id}", dependencies=[Depends(require_admin)])
def update_notice(notice_id: str, payload: NoticeInput):
    now = now_iso()
    with connect() as conn:
        conn.execute(
            """
            UPDATE notices
            SET title = ?, body = ?, status = ?, pinned = ?, updated_at = ?
            WHERE id = ?
            """,
            (payload.title, payload.body, payload.status, 1 if payload.pinned else 0, now, notice_id),
        )
        row = conn.execute("SELECT * FROM notices WHERE id = ?", (notice_id,)).fetchone()
    return row_to_dict(row)


@router.get("/events")
def list_events(status: str = "visible"):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    return {"items": rows_to_dicts(rows)}


@router.post("/admin/events", dependencies=[Depends(require_admin)])
def create_event(payload: EventInput):
    now = now_iso()
    event_id = f"event_{uuid4().hex}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO events (id, title, body, status, starts_at, ends_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, payload.title, payload.body, payload.status, payload.startsAt, payload.endsAt, now, now),
        )
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return row_to_dict(row)

