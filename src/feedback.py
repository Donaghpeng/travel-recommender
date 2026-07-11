# -*- coding: utf-8 -*-
"""
feedback.py — User feedback collection module
Stores thumbs up/down per recommendation in SQLite
"""
import sqlite3, json, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "reviews.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create feedback table if not exists"""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            dest_name   TEXT NOT NULL,
            helpful     INTEGER NOT NULL,  -- 1=useful, 0=not useful, -1=skipped
            score       REAL,              -- total_score of the recommendation
            budget      INTEGER,
            days        INTEGER,
            travel_date TEXT,
            preferences TEXT,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_agent  TEXT,
            session_id  TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_id INTEGER REFERENCES feedback(id),
            comment     TEXT NOT NULL,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_feedback(dest_name: str, helpful: int, score: float,
                  budget: int, days: int, travel_date: str,
                  preferences: list, session_id: str = "") -> int:
    """Save a feedback entry. Returns the feedback ID."""
    conn = _get_conn()
    cur = conn.execute("""
        INSERT INTO feedback(dest_name, helpful, score, budget, days,
                             travel_date, preferences, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (dest_name, helpful, score, budget, days, travel_date,
          json.dumps(preferences), session_id))
    feedback_id = cur.lastrowid
    conn.commit()
    conn.close()
    return feedback_id


def get_feedback_summary() -> dict:
    """Get aggregated feedback stats"""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) as c FROM feedback").fetchone()["c"]
    helpful = conn.execute("SELECT COUNT(*) as c FROM feedback WHERE helpful=1").fetchone()["c"]
    not_helpful = conn.execute("SELECT COUNT(*) as c FROM feedback WHERE helpful=0").fetchone()["c"]
    top_dest = conn.execute("""
        SELECT dest_name, COUNT(*) as c, SUM(helpful) as h
        FROM feedback GROUP BY dest_name ORDER BY c DESC LIMIT 5
    """).fetchall()
    conn.close()
    return {
        "total": total,
        "helpful": helpful,
        "not_helpful": not_helpful,
        "helpful_rate": round(helpful / max(total, 1) * 100, 1),
        "top_destinations": [{"name": r["dest_name"], "count": r["c"],
                              "helpful": r["h"]} for r in top_dest],
    }


def get_recent_feedback(limit: int = 20) -> list[dict]:
    """Get recent feedback entries"""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT * FROM feedback ORDER BY timestamp DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialize on import
init_db()

if __name__ == "__main__":
    print("Feedback DB initialized:", get_feedback_summary())
