from typing import Optional

from ..database import connect, now_iso


POINT_REWARDS = {
    "signup": 1000,
    "post": 20,
    "comment": 5,
    "review": 30,
    "event": 100,
    "report_reward": 20,
}


def apply_point_transaction(
    *,
    tx_id: str,
    user_id: str,
    tx_type: str,
    amount: int,
    reason: str,
    source_type: str,
    related_id: Optional[str] = None,
) -> dict:
    now = now_iso()
    signed_amount = amount if tx_type in {"earn", "admin_adjustment"} else -abs(amount)
    with connect() as conn:
        existing = conn.execute("SELECT id FROM point_transactions WHERE id = ?", (tx_id,)).fetchone()
        if existing:
            return {"duplicated": True, "transactionId": tx_id}

        conn.execute(
            """
            INSERT INTO point_transactions
            (id, user_id, type, amount, reason, source_type, related_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', ?)
            """,
            (tx_id, user_id, tx_type, signed_amount, reason, source_type, related_id, now),
        )
        conn.execute(
            """
            UPDATE users
            SET points = MAX(0, points + ?), updated_at = ?
            WHERE id = ?
            """,
            (signed_amount, now, user_id),
        )
    return {"duplicated": False, "transactionId": tx_id, "amount": signed_amount}

