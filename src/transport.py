# -*- coding: utf-8 -*-
"""
transport.py — Dynamic transportation cost estimation
Uses Haversine distance + empirical pricing models
"""
import math, json, os

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".transport_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ─── City coordinate database ──────────────────────────────

CITIES = {
    # Chinese cities (departure hubs)
    "beijing":       (39.90, 116.40, 22_000_000),
    "shanghai":      (31.23, 121.47, 25_000_000),
    "guangzhou":     (23.13, 113.26, 19_000_000),
    "shenzhen":      (22.54, 114.06, 18_000_000),
    "chengdu":       (30.57, 104.07, 16_000_000),
    "hangzhou":      (30.27, 120.15, 12_000_000),
    "wuhan":         (30.59, 114.31, 11_000_000),
    "nanjing":       (32.06, 118.80, 9_500_000),
    "chongqing":     (29.53, 106.55, 32_000_000),
    "xian":          (34.34, 108.94, 13_000_000),
    "kunming":       (25.04, 102.68, 8_500_000),
    "changsha":      (28.23, 112.94, 10_000_000),
    "zhengzhou":     (34.75, 113.63, 13_000_000),
    "tianjin":       (39.13, 117.20, 14_000_000),
    "shenyang":      (41.80, 123.38, 9_000_000),
    "qingdao":       (36.07, 120.38, 10_000_000),
    "suzhou":        (31.30, 120.58, 12_000_000),
    "xiamen":        (24.48, 118.09, 5_000_000),
    "dalian":        (38.91, 121.62, 7_500_000),
    "hefei":         (31.82, 117.23, 9_000_000),

    # International departure hubs
    "hong kong":     (22.32, 114.17, 7_500_000),
    "macau":         (22.20, 113.55, 700_000),
    "taipei":        (25.03, 121.57, 7_000_000),
    "tokyo":         (35.68, 139.69, 37_000_000),
    "seoul":         (37.57, 126.98, 10_000_000),
    "bangkok":       (13.75, 100.50, 11_000_000),
    "singapore":     (1.35, 103.82, 6_000_000),
    "kuala lumpur":  (3.14, 101.69, 8_000_000),

    # Destinations not in the list above
    "guilin":        (25.27, 110.29, 5_000_000),
    "guiyang":       (26.65, 106.63, 6_000_000),
    "lanzhou":       (36.06, 103.79, 4_000_000),
    "nanning":       (22.82, 108.37, 8_000_000),
    "hohhot":        (40.82, 111.75, 3_000_000),
    "urumqi":        (43.83, 87.62, 4_000_000),
    "lasha":         (29.65, 91.12, 1_000_000),
}

# Destination-to-city name mapping (for lookup fallback)
DEST_ALIASES = {
    "water towns (xitang/wuzhen)": "shanghai",
    "dali/lijiang (yunnan)": "kunming",
    "chengdu + sichuan": "chengdu",
    "guilin/yangshuo": "guilin",
    "guizhou (libo/miao village)": "guiyang",
    "daocheng yading (sichuan)": "chengdu",
    "changbai mountain": "shenyang",
    "lhasa (tibet)": "lasha",
    "hulunbuir (inner mongolia)": "hohhot",
    "xi'an": "xian",
    "chongqing": "chongqing",
    "qingdao": "qingdao",
    "xiamen": "xiamen",
    "changsha": "changsha",
}


# ─── Haversine distance ────────────────────────────────────

def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points in km"""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_city_coords(name: str):
    """Find city coordinates by name (case-insensitive)"""
    key = name.strip().lower()
    if key in CITIES:
        return CITIES[key]
    # Try partial match
    for city, coords in CITIES.items():
        if key in city or city in key:
            return coords
    # Try destination alias
    if key in DEST_ALIASES:
        return CITIES.get(DEST_ALIASES[key])
    return None


# ─── Flight cost estimation ────────────────────────────────

def estimate_flight(departure: str, dest_lat: float, dest_lon: float,
                    season_idx: int = 1, is_international: bool = False) -> dict:
    """
    Estimate flight cost based on distance.

    Returns: { 'cost': int, 'distance_km': int, 'duration_h': float }
    """
    dep_coords = find_city_coords(departure)
    if dep_coords is None:
        dep_coords = (31.23, 121.47, 0)  # default Shanghai

    dep_lat, dep_lon = dep_coords[0], dep_coords[1]
    dist = haversine_km(dep_lat, dep_lon, dest_lat, dest_lon)

    # Season multiplier
    season_mult = {0: 0.8, 1: 1.0, 2: 1.5}.get(season_idx, 1.0)

    # Base price per km for domestic flights (RMB/km)
    if dist < 500:
        base_per_km = 1.2   # Short haul
    elif dist < 1500:
        base_per_km = 0.9   # Medium haul
    elif dist < 3000:
        base_per_km = 0.7   # Long haul domestic
    else:
        base_per_km = 0.5   # International / ultra-long

    # International flight adjustment
    if is_international or dist > 2000:
        base_per_km *= 1.3

    # Minimum flight price (even very short)
    base_cost = max(300, dist * base_per_km * season_mult)

    # Duration estimate (cruising speed ~800 km/h + 1h overhead)
    duration_h = dist / 800 + 1.0

    return {
        "cost": round(base_cost),
        "distance_km": round(dist),
        "duration_h": round(duration_h, 1),
    }


# ─── Local transport cost estimation ───────────────────────

def estimate_local(dest_type: str, country: str, days: int,
                   region: str = "") -> dict:
    """
    Estimate daily local transportation costs.

    Returns: { 'daily': int, 'total': int, 'mode': str }
    """
    # Base daily transport cost by country
    country_rates = {
        "China": 40,
        "Thailand": 25,
        "Vietnam": 20,
        "Cambodia": 20,
        "Malaysia": 25,
        "Japan": 80,
        "South Korea": 50,
        "Laos": 15,
    }
    base = country_rates.get(country, 30)

    # Type adjustments
    type_adj = {
        "Beach": 1.0,      # walkable
        "Nature": 1.3,     # need longer travel
        "City": 1.2,       # subway/taxi
        "Ancient Town": 0.8,  # compact
        "Food": 1.1,
    }
    adj = type_adj.get(dest_type, 1.0)

    daily = round(base * adj)
    total = daily * days

    # Transport mode recommendation
    if daily <= 20:
        mode = "walking + tuk-tuk"
    elif daily <= 40:
        mode = "bus + metro + occasional taxi"
    elif daily <= 60:
        mode = "metro + taxi"
    else:
        mode = "taxi + ride-hailing"

    return {"daily": daily, "total": total, "mode": mode}


# ─── Complete estimate for a destination ───────────────────

def estimate_all(departure: str, dest, days: int, season_idx: int = 1) -> dict:
    """
    Complete transportation estimate for a destination.

    Returns dict with flight, local, and total costs.
    """
    # Determine if destination is international
    is_intl = dest.country != "China"

    # Flight estimate
    flight = estimate_flight(departure, dest.latitude, dest.longitude,
                             season_idx, is_intl)

    # Local transport
    local = estimate_local(dest.dest_type, dest.country, days, dest.region)

    total = flight["cost"] + local["total"]

    return {
        "flight": flight["cost"],
        "flight_details": flight,
        "local_daily": local["daily"],
        "local_total": local["total"],
        "local_mode": local["mode"],
        "total_transport": total,
        "distance_km": flight["distance_km"],
        "duration_h": flight["duration_h"],
    }


# ─── Batch test ────────────────────────────────────────────

def batch_test(departure: str = "Shanghai", season_idx: int = 1):
    """Test cost estimation for all destinations"""
    from src.travel_recommender import load_destinations

    dests = load_destinations()
    print(f"\nTransport estimates from {departure}:")
    print("=" * 80)
    print(f"{'Destination':30s} {'Dist':>6s} {'Flight':>8s} {'Local':>6s} {'Total':>8s}  {'Mode'}")
    print("-" * 80)

    for d in dests:
        e = estimate_all(departure, d, 5, season_idx)
        print(f"{d.name:30s} {e['distance_km']:>5}km {e['flight']:>6}RMB "
              f"{e['local_total']:>5}RMB {e['total_transport']:>7}RMB  {e['local_mode']}")


if __name__ == "__main__":
    batch_test("Shanghai", season_idx=1)
