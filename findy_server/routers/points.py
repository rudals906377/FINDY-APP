from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from ..database import connect, now_iso, rows_to_dicts
from ..dependencies import require_admin
from ..schemas import PointAdjustInput
from ..services.points import apply_point_transaction

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/{user_id}")
def get_wallet(user_id: str):
    with connect() as conn:
        user = conn.execute("SELECT id, points FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        rows = conn.execute(
            """
            SELECT * FROM point_transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (user_id,),
        ).fetchall()
    return {"userId": user["id"], "balance": user["points"], "transactions": rows_to_dicts(rows)}


@router.post("/admin/adjust", dependencies=[Depends(require_admin)])
def adjust_points(payload: PointAdjustInput):
    tx_type = "admin_adjustment" if payload.amount >= 0 else "revoke"
    result = apply_point_transaction(
        tx_id=f"point_admin_{uuid4().hex}",
        user_id=payload.userId,
        tx_type=tx_type,
        amount=payload.amount,
        reason=payload.reason,
        source_type=payload.sourceType,
        related_id=payload.relatedId,
    )
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO admin_action_logs
            (id, admin_user_id, action_type, target_type, target_id, reason, created_at)
            VALUES (?, ?, 'point_adjust', 'user', ?, ?, ?)
            """,
            (
                f"admin_log_point_{payload.userId}_{result['transactionId']}",
                payload.adminUserId,
                payload.userId,
                payload.reason,
                now_iso(),
            ),
        )
    return result
