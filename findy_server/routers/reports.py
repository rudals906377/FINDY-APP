from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from ..database import connect, now_iso, row_to_dict, rows_to_dicts
from ..dependencies import require_admin
from ..schemas import ReportInput, StatusUpdateInput

router = APIRouter(tags=["reports"])


TARGET_TABLES = {
    "post": "community_posts",
    "comment": "comments",
    "review": "reviews",
    "image": "community_posts",
    "profile": "users",
}


@router.post("/reports")
def report_content(payload: ReportInput):
    if payload.targetType not in TARGET_TABLES:
        raise HTTPException(status_code=400, detail="지원하지 않는 신고 대상입니다.")
    now = now_iso()
    report_id = f"report_{uuid4().hex}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO content_reports
            (id, reporter_user_id, target_type, target_id, reason, detail, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                report_id,
                payload.reporterUserId,
                payload.targetType,
                payload.targetId,
                payload.reason,
                payload.detail,
                now,
            ),
        )
        report_count = conn.execute(
            """
            SELECT COUNT(*) AS count FROM content_reports
            WHERE target_type = ? AND target_id = ? AND status = 'pending'
            """,
            (payload.targetType, payload.targetId),
        ).fetchone()["count"]
        table_name = TARGET_TABLES[payload.targetType]
        if report_count >= 3 and payload.targetType in {"post", "comment", "review"}:
            conn.execute(
                f"UPDATE {table_name} SET status = 'reported', updated_at = ? WHERE id = ?",
                (now, payload.targetId),
            )
        row = conn.execute("SELECT * FROM content_reports WHERE id = ?", (report_id,)).fetchone()
    return {"report": row_to_dict(row), "reportCount": report_count}


@router.get("/admin/reports", dependencies=[Depends(require_admin)])
def list_reports(targetType: str = "전체", status: str = "pending"):
    filters = []
    values = []
    if targetType != "전체":
        filters.append("target_type = ?")
        values.append(targetType)
    if status != "전체":
        filters.append("status = ?")
        values.append(status)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM content_reports {where} ORDER BY created_at DESC",
            values,
        ).fetchall()
    return {"items": rows_to_dicts(rows)}


@router.patch("/admin/reports/{report_id}", dependencies=[Depends(require_admin)])
def update_report(report_id: str, payload: StatusUpdateInput):
    now = now_iso()
    with connect() as conn:
        conn.execute(
            """
            UPDATE content_reports
            SET status = ?, admin_memo = ?, resolved_at = ?
            WHERE id = ?
            """,
            (payload.status, payload.adminMemo, now if payload.status != "pending" else None, report_id),
        )
        row = conn.execute("SELECT * FROM content_reports WHERE id = ?", (report_id,)).fetchone()
    return row_to_dict(row)

