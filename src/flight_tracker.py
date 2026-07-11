# -*- coding: utf-8 -*-
"""
flight_tracker.py — 实时低价机票追踪模块
基于距离/季节/提前天数的价格模型 + SQLite 历史记录
"""
import sqlite3, json, os, math, time, random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "reviews.db")
TABLE = "flight_prices"
TABLE_HISTORY = "flight_price_history"

# ─── Database ─────────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = _get_conn()
    conn.executescript(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            route_key   TEXT UNIQUE NOT NULL,
            departure   TEXT NOT NULL,
            destination TEXT NOT NULL,
            dest_lat    REAL,
            dest_lon    REAL,
            distance_km INTEGER,
            base_price  REAL,
            current_price REAL,
            currency    TEXT DEFAULT 'CNY',
            trend       TEXT DEFAULT 'stable',  -- rising/falling/stable
            last_check  DATETIME,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS {TABLE_HISTORY} (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            route_key   TEXT NOT NULL,
            price       REAL NOT NULL,
            checked_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_flight_route ON {TABLE}(route_key);
        CREATE INDEX IF NOT EXISTS idx_flight_history ON {TABLE_HISTORY}(route_key, checked_at);
    """)
    conn.commit()
    conn.close()

init_db()

# ─── City name → coordinates for routing ────────────────
CITY_COORDS = {
    "shanghai": (31.23, 121.47), "beijing": (39.90, 116.40),
    "guangzhou": (23.13, 113.26), "shenzhen": (22.54, 114.06),
    "chengdu": (30.57, 104.07), "hangzhou": (30.27, 120.15),
    "nanjing": (32.06, 118.80), "wuhan": (30.59, 114.31),
    "chongqing": (29.53, 106.55), "xian": (34.34, 108.94),
    "kunming": (25.04, 102.68), "changsha": (28.23, 112.94),
    "shenyang": (41.80, 123.38), "qingdao": (36.07, 120.38),
    "dalian": (38.91, 121.62), "xiamen": (24.48, 118.09),
    "sanya": (18.25, 109.51), "guilin": (25.27, 110.29),
    "lasha": (29.65, 91.12), "hohhot": (40.82, 111.75),
    "urumqi": (43.83, 87.62), "suzhou": (31.30, 120.58),
}

# ─── Price model ──────────────────────────────────────────

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def _get_coords(city: str):
    key = city.strip().lower()
    if key in CITY_COORDS:
        return CITY_COORDS[key]
    for k, v in CITY_COORDS.items():
        if k in key or key in k:
            return v
    return (31.23, 121.47)  # default Shanghai

def _base_price(distance_km: int) -> float:
    """Base round-trip price based on distance (RMB)"""
    if distance_km < 300:
        return 400 + distance_km * 0.8
    elif distance_km < 800:
        return 500 + distance_km * 0.7
    elif distance_km < 1500:
        return 600 + distance_km * 0.6
    elif distance_km < 3000:
        return 800 + distance_km * 0.5
    else:
        return 1200 + distance_km * 0.4

def _season_multiplier(month: int) -> float:
    """Seasonal adjustment"""
    peak = [1, 2, 7, 8, 10]  # Spring Festival, Summer, National Day
    shoulder = [3, 6, 9, 12]
    if month in peak:
        return 1.4
    elif month in shoulder:
        return 1.15
    return 1.0

def _advance_discount(days_before: int) -> float:
    """Earlier booking = cheaper"""
    if days_before >= 60:
        return 0.65
    elif days_before >= 30:
        return 0.80
    elif days_before >= 14:
        return 0.90
    elif days_before >= 7:
        return 0.95
    return 1.0

def estimate_price(departure: str, destination: str,
                   travel_month: int = 7, days_before: int = 30) -> dict:
    """Estimate flight price based on distance + season + advance booking"""
    dep_coords = _get_coords(departure)
    dest_coords = _get_coords(destination)
    dist = _haversine(dep_coords[0], dep_coords[1],
                      dest_coords[0], dest_coords[1])
    dist = max(100, round(dist))

    base = _base_price(dist) * 2  # round trip
    season = _season_multiplier(travel_month)
    advance = _advance_discount(days_before)

    price = base * season * advance
    price += random.uniform(-price * 0.05, price * 0.05)  # daily fluctuation

    low = base * season * 0.65  # best possible (advance + sale)
    high = base * season * 1.4  # worst case (last min + peak)

    return {
        "departure": departure,
        "destination": destination,
        "distance_km": dist,
        "estimated_price": round(price),
        "price_range": {"low": round(low), "high": round(high)},
        "season_multiplier": round(season, 2),
        "advance_discount": round(advance, 2),
        "base_price": round(base),
    }

# ─── Track & Save ─────────────────────────────────────────

def _route_key(dep: str, dest: str) -> str:
    return f"{dep.strip().lower()}->{dest.strip().lower()}"

def track_route(departure: str, destination: str,
                travel_date: str = "2026-07") -> dict:
    """Track price for a route, save to DB"""
    key = _route_key(departure, destination)
    conn = _get_conn()

    try:
        month = int(travel_date.split("-")[1])
    except (IndexError, ValueError, TypeError):
        month = 7

    dest_coords = _get_coords(destination)
    estimate = estimate_price(departure, destination, month)

    # Save or update route
    existing = conn.execute(
        f"SELECT id, current_price FROM {TABLE} WHERE route_key=?",
        (key,)
    ).fetchone()

    price = estimate["estimated_price"]
    trend = "stable"

    if existing:
        old_price = existing["current_price"]
        change = (price - old_price) / max(old_price, 1)
        if change > 0.03:
            trend = "rising"
        elif change < -0.03:
            trend = "falling"
        conn.execute(f"""
            UPDATE {TABLE} SET
                current_price=?, trend=?, last_check=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE route_key=?
        """, (price, trend, key))
    else:
        conn.execute(f"""
            INSERT INTO {TABLE}
            (route_key, departure, destination, dest_lat, dest_lon,
             distance_km, base_price, current_price, trend, last_check)
            VALUES (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        """, (key, departure, destination, round(dest_coords[0], 4),
              round(dest_coords[1], 4), estimate["distance_km"],
              estimate["base_price"], price, trend))

    # Save price history
    conn.execute(f"""
        INSERT INTO {TABLE_HISTORY}(route_key, price) VALUES (?,?)
    """, (key, price))

    conn.commit()
    conn.close()

    return {
        "route": f"{departure} \u2192 {destination}",
        "current_price": price,
        "range": estimate["price_range"],
        "trend": trend,
        "is_low_price": price <= estimate["price_range"]["low"] * 1.1,
    }

def get_route_info(route_key: str) -> dict:
    """Get tracked route info"""
    conn = _get_conn()
    row = conn.execute(
        f"SELECT * FROM {TABLE} WHERE route_key=?", (route_key,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def get_price_history(route_key: str, days: int = 30) -> list:
    """Get price history for a route"""
    conn = _get_conn()
    rows = conn.execute(f"""
        SELECT price, checked_at FROM {TABLE_HISTORY}
        WHERE route_key=? AND checked_at >= datetime('now', ?)
        ORDER BY checked_at DESC
    """, (route_key, f"-{days} days")).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_low_price_alerts(min_drop_pct: float = 15) -> list:
    """Get routes where price dropped significantly"""
    conn = _get_conn()
    rows = conn.execute(f"""
        SELECT route_key, departure, destination, current_price, trend
        FROM {TABLE}
        WHERE trend='falling'
        ORDER BY updated_at DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def batch_track(departure: str, destinations: list[str],
                travel_date: str = "2026-07") -> list:
    """Track prices for multiple routes at once"""
    results = []
    for dest in destinations:
        r = track_route(departure, dest, travel_date)
        results.append(r)
        time.sleep(0.05)
    return results

# ─── Test ─────────────────────────────────────────────────


# ─── Price Alerts ─────────────────────────────────────────

def set_alert(departure: str, destination: str, target_price: float) -> dict:
    key = _route_key(departure, destination)
    conn = _get_conn()
    existing = conn.execute(
        "SELECT id, target_price, triggered FROM flight_alerts WHERE route_key=? AND triggered=0",
        (key,)
    ).fetchone()
    if existing:
        conn.execute("UPDATE flight_alerts SET target_price=? WHERE id=?", (target_price, existing["id"]))
        conn.commit()
        conn.close()
        return {"ok": True, "alert_id": existing["id"], "updated": True}
    cur = conn.execute("INSERT INTO flight_alerts(route_key, departure, destination, target_price) VALUES (?,?,?,?)",
                 (key, departure, destination, target_price))
    aid = cur.lastrowid
    conn.commit()
    conn.close()
    return {"ok": True, "alert_id": aid, "updated": False}

def check_alerts() -> list:
    conn = _get_conn()
    alerts = conn.execute("SELECT * FROM flight_alerts WHERE triggered=0").fetchall()
    triggered = []
    for alert in alerts:
        row = conn.execute(
            "SELECT current_price FROM flight_prices WHERE route_key=? ORDER BY updated_at DESC LIMIT 1",
            (alert["route_key"],)
        ).fetchone()
        if row and row["current_price"] <= alert["target_price"]:
            conn.execute("UPDATE flight_alerts SET triggered=1, notified_at=CURRENT_TIMESTAMP WHERE id=?",
                         (alert["id"],))
            triggered.append({
                "id": alert["id"], "departure": alert["departure"],
                "destination": alert["destination"],
                "target_price": alert["target_price"],
                "current_price": row["current_price"],
                "drop_pct": round((1 - row["current_price"] / alert["target_price"]) * 100, 1)
            })
    conn.commit()
    conn.close()
    return triggered

def get_my_alerts(include_triggered: bool = False) -> list:
    conn = _get_conn()
    if include_triggered:
        rows = conn.execute("SELECT * FROM flight_alerts ORDER BY created_at DESC LIMIT 20").fetchall()
    else:
        rows = conn.execute("SELECT * FROM flight_alerts WHERE triggered=0 ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def remove_alert(alert_id: int) -> bool:
    conn = _get_conn()
    cur = conn.execute("DELETE FROM flight_alerts WHERE id=?", (alert_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


if __name__ == "__main__":
    print("=== Flight Price Tracker ===\n")

    # Test single route
    r = track_route("Shanghai", "Sanya", "2026-07")
    print(f"Shanghai -> Sanya: RMB {r['current_price']:,} ({r['trend']})")

    r2 = track_route("Beijing", "Chengdu", "2026-07")
    print(f"Beijing -> Chengdu: RMB {r2['current_price']:,} ({r2['trend']})")

    # Test multiple
    results = batch_track("Shanghai", ["Beijing", "Guilin", "Xiamen", "Chengdu", "Sanya"])
    print("\nBatch from Shanghai:")
    for r in results:
        flag = "LOW" if r['is_low_price'] else "  "
        print(f"  [{flag}] {r['route']}: RMB {r['current_price']:,}  range: {r['range']['low']}-{r['range']['high']}")

    # Test alerts
    alerts = get_low_price_alerts()
    print(f"\nLow price alerts: {len(alerts)}")
