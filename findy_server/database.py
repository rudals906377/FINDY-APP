import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .config import settings


def _sqlite_path() -> Path:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        raise RuntimeError("현재 개발 서버는 sqlite:/// 데이터베이스 URL만 지원합니다.")
    return Path(settings.database_url[len(prefix):])


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@contextmanager
def connect():
    path = _sqlite_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [row_to_dict(row) for row in rows]


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    data = dict(row)
    for key in ("tags", "risk_types", "metadata", "consents"):
        if key in data and isinstance(data[key], str):
            try:
                data[key] = json.loads(data[key]) if data[key] else ([] if key != "metadata" else {})
            except json.JSONDecodeError:
                data[key] = [] if key != "metadata" else {}
    return data


def to_json(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                phone TEXT,
                real_name TEXT,
                nickname TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                points INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS consent_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                consent_type TEXT NOT NULL,
                is_agreed INTEGER NOT NULL,
                policy_version TEXT NOT NULL,
                agreed_at TEXT,
                withdrawn_at TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS location_preferences (
                user_id TEXT PRIMARY KEY,
                location_permission_status TEXT NOT NULL DEFAULT 'not_requested',
                selected_region TEXT,
                location_enabled INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notices (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'visible',
                pinned INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'visible',
                starts_at TEXT,
                ends_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS community_posts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                post_type TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'visible',
                risk_score INTEGER NOT NULL DEFAULT 0,
                risk_types TEXT NOT NULL DEFAULT '[]',
                like_count INTEGER NOT NULL DEFAULT 0,
                save_count INTEGER NOT NULL DEFAULT 0,
                comment_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                post_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'visible',
                risk_score INTEGER NOT NULL DEFAULT 0,
                risk_types TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                place_name TEXT NOT NULL,
                artist_name TEXT,
                service_category TEXT NOT NULL,
                rating INTEGER NOT NULL,
                body TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'visible',
                verified_visit INTEGER NOT NULL DEFAULT 0,
                risk_score INTEGER NOT NULL DEFAULT 0,
                risk_types TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS content_reports (
                id TEXT PRIMARY KEY,
                reporter_user_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                detail TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                admin_memo TEXT,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS point_transactions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                reason TEXT NOT NULL,
                source_type TEXT NOT NULL,
                related_id TEXT,
                status TEXT NOT NULL DEFAULT 'completed',
                created_at TEXT NOT NULL,
                expires_at TEXT
            );

            CREATE TABLE IF NOT EXISTS admin_action_logs (
                id TEXT PRIMARY KEY,
                admin_user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            );
            """
        )


def seed_db() -> None:
    now = now_iso()
    with connect() as conn:
        user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        if user_count == 0:
            conn.execute(
                """
                INSERT INTO users (id, phone, real_name, nickname, status, points, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("user_demo", "01000000000", "오경민", "FINDY 회원", "active", 1200, now, now),
            )

        notice_count = conn.execute("SELECT COUNT(*) AS count FROM notices").fetchone()["count"]
        if notice_count == 0:
            conn.execute(
                """
                INSERT INTO notices (id, title, body, status, pinned, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "notice_welcome",
                    "FINDY2 커뮤니티가 열렸어요",
                    "리뷰, 질문, 자유게시판에서 뷰티 경험을 먼저 모아볼게요.",
                    "visible",
                    1,
                    now,
                    now,
                ),
            )

