from fastapi import APIRouter, Depends, HTTPException

from ..database import connect, now_iso, row_to_dict, rows_to_dicts
from ..dependencies import require_admin
from ..schemas import StatusUpdateInput

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


TARGET_TABLES = {
    "post": "community_posts",
    "comment": "comments",
    "review": "reviews",
    "user": "users",
}


@router.get("/dashboard")
def dashboard():
    with connect() as conn:
        stats = {
            "users": conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"],
            "posts": conn.execute("SELECT COUNT(*) AS count FROM community_posts").fetchone()["count"],
            "reviews": conn.execute("SELECT COUNT(*) AS count FROM reviews").fetchone()["count"],
            "pendingReports": conn.execute(
                "SELECT COUNT(*) AS count FROM content_reports WHERE status = 'pending'"
            ).fetchone()["count"],
            "pendingContent": conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM community_posts WHERE status IN ('pending', 'reported')) +
                    (SELECT COUNT(*) FROM comments WHERE status IN ('pending', 'reported')) +
                    (SELECT COUNT(*) FROM reviews WHERE status IN ('pending', 'reported')) AS count
                """
            ).fetchone()["count"],
        }
    return stats


@router.get("/content")
def list_flagged_content(status: str = "pending"):
    with connect() as conn:
        posts = rows_to_dicts(
            conn.execute(
                "SELECT 'post' AS target_type, * FROM community_posts WHERE status = ? ORDER BY updated_at DESC",
                (status,),
            ).fetchall()
        )
        comments = rows_to_dicts(
            conn.execute(
                "SELECT 'comment' AS target_type, * FROM comments WHERE status = ? ORDER BY updated_at DESC",
                (status,),
            ).fetchall()
        )
        reviews = rows_to_dicts(
            conn.execute(
                "SELECT 'review' AS target_type, * FROM reviews WHERE status = ? ORDER BY updated_at DESC",
                (status,),
            ).fetchall()
        )
    return {"items": posts + comments + reviews}


@router.patch("/content/{target_type}/{target_id}/status")
def update_content_status(target_type: str, target_id: str, payload: StatusUpdateInput):
    if target_type not in TARGET_TABLES:
        raise HTTPException(status_code=400, detail="지원하지 않는 대상입니다.")
    table = TARGET_TABLES[target_type]
    id_column = "id"
    now = now_iso()
    with connect() as conn:
        conn.execute(
            f"UPDATE {table} SET status = ?, updated_at = ? WHERE {id_column} = ?",
            (payload.status, now, target_id),
        )
        conn.execute(
            """
            INSERT INTO admin_action_logs
            (id, admin_user_id, action_type, target_type, target_id, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"admin_log_{target_type}_{target_id}_{now}",
                payload.adminUserId,
                f"status:{payload.status}",
                target_type,
                target_id,
                payload.reason or payload.adminMemo,
                now,
            ),
        )
        row = conn.execute(f"SELECT * FROM {table} WHERE {id_column} = ?", (target_id,)).fetchone()
    return row_to_dict(row)


@router.get("/logs")
def list_admin_logs():
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM admin_action_logs ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    return {"items": rows_to_dicts(rows)}

