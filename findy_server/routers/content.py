from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ..database import connect, now_iso, row_to_dict, rows_to_dicts, to_json
from ..schemas import CommentInput, PostInput, ReviewInput
from ..services.points import POINT_REWARDS, apply_point_transaction
from ..services.safety import validate_content

router = APIRouter(tags=["content"])


@router.get("/posts")
def list_posts(postType: str = "전체", category: str = "전체", status: str = "visible"):
    filters = ["status = ?"]
    values = [status]
    if postType != "전체":
        filters.append("post_type = ?")
        values.append(postType)
    if category != "전체":
        filters.append("category = ?")
        values.append(category)
    where = " AND ".join(filters)
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM community_posts WHERE {where} ORDER BY created_at DESC",
            values,
        ).fetchall()
    return {"items": rows_to_dicts(rows)}


@router.post("/posts")
def create_post(payload: PostInput):
    safety = validate_content(f"{payload.title}\n{payload.body}")
    if not safety["canSubmit"]:
        raise HTTPException(status_code=400, detail={"message": "위험 표현이 포함되어 제출할 수 없습니다.", **safety})

    now = now_iso()
    post_id = f"post_{uuid4().hex}"
    saved_status = "pending" if safety["status"] == "pending" else "visible"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO community_posts
            (id, user_id, post_type, category, title, body, tags, status, risk_score, risk_types, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post_id,
                payload.userId,
                payload.postType,
                payload.category,
                payload.title,
                safety["maskedText"].split("\n", 1)[1] if "\n" in safety["maskedText"] else payload.body,
                to_json(payload.tags),
                saved_status,
                safety["riskScore"],
                to_json(safety["riskTypes"]),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM community_posts WHERE id = ?", (post_id,)).fetchone()

    if saved_status == "visible":
        apply_point_transaction(
            tx_id=f"point_post_{post_id}",
            user_id=payload.userId,
            tx_type="earn",
            amount=POINT_REWARDS["post"],
            reason="게시글 작성 보상",
            source_type="post",
            related_id=post_id,
        )
    return row_to_dict(row)


@router.get("/posts/{post_id}")
def get_post(post_id: str):
    with connect() as conn:
        row = conn.execute("SELECT * FROM community_posts WHERE id = ?", (post_id,)).fetchone()
        comments = conn.execute(
            "SELECT * FROM comments WHERE post_id = ? AND status = 'visible' ORDER BY created_at ASC",
            (post_id,),
        ).fetchall()
    if not row:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    data = row_to_dict(row)
    data["comments"] = rows_to_dicts(comments)
    return data


@router.post("/comments")
def create_comment(payload: CommentInput):
    safety = validate_content(payload.body)
    if not safety["canSubmit"]:
        raise HTTPException(status_code=400, detail={"message": "댓글을 제출할 수 없습니다.", **safety})
    now = now_iso()
    comment_id = f"comment_{uuid4().hex}"
    saved_status = "pending" if safety["status"] == "pending" else "visible"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO comments
            (id, post_id, user_id, body, status, risk_score, risk_types, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                comment_id,
                payload.postId,
                payload.userId,
                safety["maskedText"],
                saved_status,
                safety["riskScore"],
                to_json(safety["riskTypes"]),
                now,
                now,
            ),
        )
        conn.execute(
            "UPDATE community_posts SET comment_count = comment_count + 1, updated_at = ? WHERE id = ?",
            (now, payload.postId),
        )
        row = conn.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
    if saved_status == "visible" and len(payload.body.strip()) >= 5:
        apply_point_transaction(
            tx_id=f"point_comment_{comment_id}",
            user_id=payload.userId,
            tx_type="earn",
            amount=POINT_REWARDS["comment"],
            reason="댓글 작성 보상",
            source_type="comment",
            related_id=comment_id,
        )
    return row_to_dict(row)


@router.get("/reviews")
def list_reviews(serviceCategory: str = "전체", status: str = "visible"):
    filters = ["status = ?"]
    values = [status]
    if serviceCategory != "전체":
        filters.append("service_category = ?")
        values.append(serviceCategory)
    where = " AND ".join(filters)
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM reviews WHERE {where} ORDER BY created_at DESC",
            values,
        ).fetchall()
    return {"items": rows_to_dicts(rows)}


@router.post("/reviews")
def create_review(payload: ReviewInput):
    safety = validate_content(f"{payload.placeName}\n{payload.artistName or ''}\n{payload.body}")
    if not safety["canSubmit"]:
        raise HTTPException(status_code=400, detail={"message": "리뷰를 제출할 수 없습니다.", **safety})
    now = now_iso()
    review_id = f"review_{uuid4().hex}"
    saved_status = "pending" if safety["status"] == "pending" else "visible"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO reviews
            (id, user_id, place_name, artist_name, service_category, rating, body, tags, status,
             verified_visit, risk_score, risk_types, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                payload.userId,
                payload.placeName,
                payload.artistName,
                payload.serviceCategory,
                payload.rating,
                safety["maskedText"].split("\n")[-1],
                to_json(payload.tags),
                saved_status,
                1 if payload.verifiedVisit else 0,
                safety["riskScore"],
                to_json(safety["riskTypes"]),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    if saved_status == "visible":
        apply_point_transaction(
            tx_id=f"point_review_{review_id}",
            user_id=payload.userId,
            tx_type="earn",
            amount=POINT_REWARDS["review"],
            reason="리뷰 작성 보상",
            source_type="review",
            related_id=review_id,
        )
    return row_to_dict(row)

