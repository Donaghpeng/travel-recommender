# -*- coding: utf-8 -*-
"""
review_db.py — Local SQLite review database
Schema + CRUD for storing scraped destination reviews
"""
import sqlite3, os, json, time

DB_PATH = os.path.join(os.path.dirname(__file__), "reviews.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist"""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS destinations (
            id          INTEGER PRIMARY KEY,
            name        TEXT UNIQUE NOT NULL,
            name_cn     TEXT,           -- Chinese name for URL matching
            platform_id TEXT,           -- platform-specific ID (mafengwo ID etc)
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            dest_id         INTEGER NOT NULL REFERENCES destinations(id),
            source          TEXT NOT NULL,       -- 'mafengwo', 'ctrip', etc
            overall_rating  REAL DEFAULT 0,      -- 1-5
            review_count    INTEGER DEFAULT 0,
            excellent_pct   REAL DEFAULT 0,      -- percentage of 5-star
            good_pct        REAL DEFAULT 0,
            average_pct     REAL DEFAULT 0,
            poor_pct        REAL DEFAULT 0,
            terrible_pct    REAL DEFAULT 0,
            summary         TEXT,                -- crawled summary text
            tags            TEXT,                -- JSON array of tag strings
            recommendations TEXT,                -- top recommended things
            fetched_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS review_details (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            dest_id     INTEGER NOT NULL REFERENCES destinations(id),
            source      TEXT NOT NULL,
            reviewer    TEXT,
            rating      REAL,
            title       TEXT,
            content     TEXT,
            date        TEXT,
            helpful_count INTEGER DEFAULT 0,
            fetched_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_reviews_dest ON reviews(dest_id, source);
        CREATE INDEX IF NOT EXISTS idx_details_dest ON review_details(dest_id, source);
    """)
    conn.commit()
    conn.close()
    print(f"[db] initialized: {DB_PATH}")


# ─── Destinations ──────────────────────────────────────────

def upsert_dest(name: str, name_cn: str = "", platform_id: str = "") -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT OR IGNORE INTO destinations(name, name_cn, platform_id) VALUES (?, ?, ?)",
        (name, name_cn, platform_id)
    )
    if cur.rowcount == 0:
        row = conn.execute("SELECT id FROM destinations WHERE name = ?", (name,)).fetchone()
        dest_id = row["id"]
    else:
        dest_id = cur.lastrowid
    conn.commit()
    conn.close()
    return dest_id


def get_dest_id(name: str) -> int:
    conn = get_conn()
    row = conn.execute("SELECT id FROM destinations WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row["id"] if row else 0


# ─── Reviews ───────────────────────────────────────────────

def save_review_summary(dest_id: int, source: str, data: dict):
    """Save or update review summary for a destination"""
    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM reviews WHERE dest_id = ? AND source = ?",
        (dest_id, source)
    ).fetchone()

    if existing:
        conn.execute("""
            UPDATE reviews SET
                overall_rating=?, review_count=?, excellent_pct=?, good_pct=?,
                average_pct=?, poor_pct=?, terrible_pct=?, summary=?,
                tags=?, recommendations=?, fetched_at=CURRENT_TIMESTAMP
            WHERE dest_id=? AND source=?
        """, (
            data.get("rating", 0), data.get("count", 0),
            data.get("excellent_pct", 0), data.get("good_pct", 0),
            data.get("average_pct", 0), data.get("poor_pct", 0),
            data.get("terrible_pct", 0), data.get("summary", ""),
            json.dumps(data.get("tags", [])),
            json.dumps(data.get("recommendations", [])),
            dest_id, source
        ))
    else:
        conn.execute("""
            INSERT INTO reviews(dest_id, source, overall_rating, review_count,
                excellent_pct, good_pct, average_pct, poor_pct, terrible_pct,
                summary, tags, recommendations)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            dest_id, source,
            data.get("rating", 0), data.get("count", 0),
            data.get("excellent_pct", 0), data.get("good_pct", 0),
            data.get("average_pct", 0), data.get("poor_pct", 0),
            data.get("terrible_pct", 0), data.get("summary", ""),
            json.dumps(data.get("tags", [])),
            json.dumps(data.get("recommendations", [])),
        ))
    conn.commit()
    conn.close()


def get_review_summary(dest_id: int) -> list[dict]:
    """Get review summaries for a destination"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM reviews WHERE dest_id = ? ORDER BY review_count DESC",
        (dest_id,)
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        if d["tags"]:
            try:
                d["tags"] = json.loads(d["tags"])
            except (json.JSONDecodeError, TypeError):
                d["tags"] = []
        if d["recommendations"]:
            try:
                d["recommendations"] = json.loads(d["recommendations"])
            except (json.JSONDecodeError, TypeError):
                d["recommendations"] = []
        results.append(d)
    return results


# ─── Review Details (individual reviews) ───────────────────

def save_review_detail(dest_id: int, source: str, review: dict):
    """Save an individual review"""
    conn = get_conn()
    conn.execute("""
        INSERT INTO review_details(dest_id, source, reviewer, rating,
            title, content, date, helpful_count)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        dest_id, source,
        review.get("reviewer", ""), review.get("rating", 0),
        review.get("title", ""), review.get("content", ""),
        review.get("date", ""), review.get("helpful", 0)
    ))
    conn.commit()
    conn.close()


def get_recent_reviews(dest_id: int, source: str = "", limit: int = 20) -> list[dict]:
    """Get recent individual reviews"""
    conn = get_conn()
    if source:
        rows = conn.execute(
            "SELECT * FROM review_details WHERE dest_id=? AND source=? ORDER BY fetched_at DESC LIMIT ?",
            (dest_id, source, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM review_details WHERE dest_id=? ORDER BY fetched_at DESC LIMIT ?",
            (dest_id, limit)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Stats ─────────────────────────────────────────────────

def get_db_stats() -> dict:
    conn = get_conn()
    dests = conn.execute("SELECT COUNT(*) as c FROM destinations").fetchone()["c"]
    summaries = conn.execute("SELECT COUNT(*) as c FROM reviews").fetchone()["c"]
    details = conn.execute("SELECT COUNT(*) as c FROM review_details").fetchone()["c"]
    conn.close()
    return {"destinations": dests, "summaries": summaries, "details": details}


if __name__ == "__main__":
    init_db()
    print("DB stats:", get_db_stats())
