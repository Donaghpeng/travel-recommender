# -*- coding: utf-8 -*-
"""
travel_recommender.py — Travel Recommendation Engine MVP
========================================================
5-dimension scoring: cost, route, review, weather, preference
Supports dynamic weight adjustment & diversified ranking
"""

from dataclasses import dataclass, field
from typing import Optional
import math
import json
from zh_names import CN_NAMES

# Optional real-data services (graceful fallback if unavailable)
try:
    from weather_service import compute_monthly_avg as _real_weather
    _HAS_REAL_WEATHER = True
except ImportError:
    _HAS_REAL_WEATHER = False

try:
    from transport import estimate_all as _estimate_transport
    _HAS_TRANSPORT = True
except ImportError:
    _HAS_TRANSPORT = False


# ─── Data Models ────────────────────────────────────────────

@dataclass
class Destination:
    id: int
    name: str
    country: str
    region: str
    dest_type: str
    latitude: float
    longitude: float
    description: str
    keywords: list[str]
    image_url: str = ""

    cost_flight: tuple = (0, 0, 0)
    cost_hotel_per_night: tuple = (0, 0, 0)
    cost_food_per_day: tuple = (0, 0, 0)
    cost_ticket: int = 0
    cost_local_transport: tuple = (0, 0, 0)

    rating_overall: float = 0.0
    rating_count: int = 0

    weather: dict = field(default_factory=dict)


# ─── Seed Data (30 destinations) ───────────────────────────

def load_destinations() -> list[Destination]:
    try:
        from destinations_data import load_all as _load_all
        dests = _load_all()
        try:
            from review_seed import get_aggregated_rating as _db_review
            for d in dests:
                r = _db_review(d.name)
                if r:
                    d.rating_overall = r["rating"]
                    d.rating_count = r["count"]
        except Exception:
            pass
        return dests
    except ImportError:
        return []





# ─── Scoring Functions ──────────────────────────────────────

SEASON_OFF = [1, 2, 3, 11, 12]
SEASON_MID = [4, 5, 9, 10]
SEASON_PEAK = [6, 7, 8]


def _season_index(month: int) -> int:
    if month in SEASON_OFF: return 0
    if month in SEASON_MID: return 1
    return 2


def _month_from_date(date_str: str) -> int:
    try:
        parts = date_str.split("-")
        return int(parts[1])
    except (IndexError, ValueError, TypeError):
        return 7


def _total_estimate(dest: Destination, days: int, si: int,
                     departure: str = "Shanghai") -> tuple:
    """Returns (total_estimate, flight_cost, local_cost, transport_detail)"""
    h = dest.cost_hotel_per_night[si] * (days - 1)
    d = dest.cost_food_per_day[si] * days
    t = dest.cost_ticket

    # Try dynamic transport estimation
    if _HAS_TRANSPORT:
        try:
            te = _estimate_transport(departure, dest, days, si)
            f = te["flight"] * 2
            l = te["local_total"]
            detail = {"flight": f, "local": l, "distance_km": te["distance_km"],
                      "duration_h": te["duration_h"], "local_mode": te["local_mode"]}
            return f + h + d + t + l, f, l, detail
        except (KeyError, TypeError, Exception):
            pass

    # Fallback to hardcoded data
    f = dest.cost_flight[si]
    l = dest.cost_local_transport[si] * days
    detail = {"flight": f, "local": l, "distance_km": None,
              "duration_h": None, "local_mode": "N/A"}
    return f + h + d + t + l, f, l, detail


def score_cost(dest: Destination, budget: int, days: int, si: int,
               departure: str = "Shanghai") -> tuple:
    """Returns (score, estimate_total)"""
    est_tuple = _total_estimate(dest, days, si, departure)
    est = est_tuple[0]  # total estimate
    r = est / max(budget, 1)
    if r <= 0.4: return 5.0
    if r <= 0.6: return 4.5
    if r <= 0.8: return 4.0
    if r <= 1.0: return 3.0
    if r <= 1.3: return 2.0
    if r <= 1.6: return 1.5
    return 1.0


def score_route(dest: Destination, departure: str, si: int) -> float:
    east = ["East", "North", "Central", "Northeast"]
    west = ["Southwest", "Northwest", "South"]
    if dest.country != "China":
        return 2.5
    if departure in ["Shanghai", "Hangzhou", "Nanjing"] and dest.region in east:
        return 4.5
    if departure in ["Beijing", "Tianjin"] and dest.region in east:
        return 4.0
    if departure in ["Guangzhou", "Shenzhen", "Chengdu"] and dest.region in west:
        return 4.0
    if dest.region == "SE Asia":
        return 3.0
    return 3.5


def score_review(dest: Destination) -> float:
    base = dest.rating_overall
    bonus = min(dest.rating_count / 50000, 1.0) * 0.3
    return min(base + bonus, 5.0)


def score_weather(dest: Destination, month: int) -> float:
    """Fast weather estimation: latitude + month (no API calls)"""
    if month in dest.weather:
        return dest.weather[month][3]
    lat = abs(dest.latitude)
    is_north = dest.latitude > 0
    is_summer = month in [5, 6, 7, 8, 9]
    is_tropical = lat < 23.5
    is_temperate = 23.5 <= lat < 45
    is_cold = lat >= 45
    if is_tropical:
        base = 4.5 if not is_summer else 3.5
        if month in [6, 7, 8] and dest.dest_type in ("Beach", "Island"):
            base += 0.5
    elif is_temperate:
        base = 4.5 if is_summer else 2.5
        if month in [6, 7, 8] and dest.dest_type == "Beach":
            base += 1.0
    else:
        base = 3.5 if is_summer else 1.5
    if dest.dest_type in ("City",) and month in [6, 7, 8]:
        base -= 0.5
    return min(max(base, 1.0), 5.0)


# ─── Chinese preference keyword mapping ──────────────────
CN_PREF_MAP = {
    "海滩": ["beach", "Beach", "海滨", "海岛", "沙滩", "海"],
    "美食": ["food", "Food", "美食", "餐饮", "海鲜", "小吃"],
    "自然": ["nature", "Nature", "自然", "山水", "风景", "风光"],
    "历史": ["history", "Historical", "历史", "文化", "古迹", "古都"],
    "人文": ["culture", "Culture", "人文", "艺术"],
    "城市": ["city", "City", "都市", "繁华"],
    "古镇": ["AncientTown", "古镇", "水乡", "乡村"],
    "乡村": ["AncientTown", "Countryside", "乡村", "古镇"],
    "摄影": ["photography", "photography", "摄影"],
    "徒步": ["hiking", "徒步", "登山", "户外", "outdoor"],
    "登山": ["hiking", "Mountain", "登山", "山"],
    "冒险": ["adventure", "Adventure", "冒险"],
    "浪漫": ["romantic", "浪漫"],
    "家庭": ["family", "Family", "家庭", "亲子"],
    "购物": ["shopping", "购物"],
    "滑雪": ["ski", "winter", "滑雪"],
    "海岛": ["Island", "Beach", "海岛", "岛"],
    "温泉": ["spa", "温泉", "休闲"],
    "休闲": ["leisure", "度假", "休闲"],
}


def score_preference(dest: Destination, prefs: list[str],
                         month: int = 7) -> float:
    if not prefs:
        return 3.0

    # Build searchable text: English keywords + Chinese keywords + type + description
    search_text = " ".join(dest.keywords).lower() + " " + dest.dest_type.lower()
    search_text += " " + dest.description.lower()

    matches = 0
    for p in prefs:
        p_lower = p.lower().strip()
        # Direct check against keywords, type, and description
        if p_lower in search_text:
            matches += 1
            continue
        # Check bilingual mapping
        mapped = CN_PREF_MAP.get(p, [])
        for kw in mapped:
            if kw.lower() in search_text:
                matches += 1
                break

    base = min(3.0 + matches * 1.0, 5.0)

    # Type matching bonus: if preference describes the destination type
    pref_types = " ".join(prefs).lower()
    dt = dest.dest_type.lower()
    type_keywords = {
        "beach": ["海滩", "海滨", "海岛", "沙滩", "海边"],
        "food": ["美食", "吃饭"],
        "nature": ["自然", "山水", "风景"],
        "mountain": ["山", "登山", "徒步"],
        "city": ["城市", "都市", "繁华"],
        "culture": ["文化", "人文", "历史", "古迹"],
        "ancient": ["古镇", "水乡", "古村"],
    }
    for dest_type_name, cn_kws in type_keywords.items():
        if dest_type_name in dt:
            for cn_kw in cn_kws:
                if cn_kw in pref_types:
                    base += 0.5  # Type match bonus
                    break
    season = {12:"winter",1:"winter",2:"winter",3:"spring",4:"spring",5:"spring",
              6:"summer",7:"summer",8:"summer",9:"autumn",10:"autumn",11:"autumn"}.get(month)
    seasonal_boost = {
        "summer": ["Beach", "Island", "Nature", "Mountain"],
        "winter": ["Beach", "City", "Food", "Culture", "Adventure"],
        "spring": ["City", "Nature", "AncientTown", "Culture"],
        "autumn": ["Nature", "AncientTown", "City", "Food"],
    }
    dt = dest.dest_type
    if season == "summer" and dt == "City" and "summer" not in str(dest.keywords):
        base -= 0.3
    elif season == "winter" and dt == "Beach" and dest.country != "China":
        base += 0.5
    boost = seasonal_boost.get(season, [])
    if dt in boost:
        base += 0.4 if season in ("summer", "autumn") else 0.3
    return round(min(base, 5.0), 1)


# ─── Score Explanation Functions ──────────────────────────

def _explain_cost(score: float, budget: int, estimate: int, days: int) -> str:
    ratio = estimate / max(budget, 1)
    if score >= 4.5: return f"非常性价比：¥{estimate} 远低于预算 ¥{budget}（仅占预算{int(ratio*100)}%）"
    elif score >= 4.0: return f"性价比不错：¥{estimate} {days}天行程低于预算 ¥{budget}"
    elif score >= 3.0: return f"费用合理：¥{estimate} 接近预算限额 ¥{budget}（{int(ratio*100)}%）"
    elif score >= 2.0: return f"稍超预算：¥{estimate} 超出预算{int((ratio-1)*100)}%，建议缩短行程"
    else: return f"超预算较多：¥{estimate} 超出预算{int((ratio-1)*100)}%，考虑缩短行程或换目的地"


def _explain_route(score: float, departure: str, dest_name: str, region: str) -> str:
    if score >= 4.0: return f"从{departure}出发很方便：前往{dest_name}的交通网络发达"
    elif score >= 3.0: return f"从{departure}出发可达：前往{dest_name}交通时间适中"
    elif score >= 2.0: return f"路线稍远：{dest_name}离{departure}较远，需提前规划"
    else: return f"交通较少：{departure}到{dest_name}的连接有限，建议预留更多时间"


def _explain_review(score: float, rating: float, count: int) -> str:
    pts = []
    if rating >= 4.5: pts.append(f"评分极佳：{rating}/5")
    elif rating >= 4.0: pts.append(f"评分很高：{rating}/5")
    elif rating >= 3.5: pts.append(f"评分不错：{rating}/5")
    else: pts.append(f"评分一般：{rating}/5")
    if count >= 50000: pts.append(f"非常受欢迎（{count:,}条评价）")
    elif count >= 20000: pts.append(f"评价不错（{count:,}条评价）")
    elif count >= 5000: pts.append(f"已有{count:,}条评价")
    else: pts.append(f"评价较少（{count:,}条）")
    return "，".join(pts) + "。"


def _explain_weather(score: float, dest, month: int) -> str:
    sj = {12:"冬",1:"冬",2:"冬",3:"春",4:"春",5:"春",
              6:"夏",7:"夏",8:"夏",9:"秋",10:"秋",11:"秋"}.get(month, "夏")
    wd = dest.weather.get(month)
    if wd and len(wd) >= 4:
        hi, lo, rain, comfort = wd
        if comfort >= 4.5: ct = "天气极佳"
        elif comfort >= 4.0: ct = "天气良好"
        elif comfort >= 3.0: ct = "天气一般"
        elif comfort >= 2.0: ct = "天气较差"
        else: ct = "天气恶劣"
        return f"{ct}：约{hi}/{lo}°C，降水{rain}mm。评分：{comfort}/5"
    if score >= 4.0: return f"{sj}季天气优良，温度舒适"
    elif score >= 3.0: return f"{sj}季天气可以，建议出行前查看预报"
    else: return f"{sj}季天气不佳，建议考虑更换时间"


def _explain_preference(score: float, prefs: list[str], keywords: list[str],
                        dest_type: str, month: int) -> str:
    if not prefs:
        return "未指定特定偏好"
    kw = [k for k in keywords if k in " ".join(prefs).lower()]
    type_ok = any(p.lower() in dest_type.lower() for p in prefs)
    pts = []
    if kw:
        pts.append(f"符合您的兴趣：{', '.join(kw[:3])}")
    if type_ok:
        pts.append(f"{dest_type}类目的地与偏好匹配")
    if not kw and not type_ok:
        pts.append("与您的偏好有一定关联")
    if score >= 4.5:
        pts.append("非常匹配！")
    elif score >= 3.5:
        pts.append("匹配度较高")
    return "，".join(pts) + "。"


def _generate_why_text(name: str, score: float, scores: dict, explanations: dict,
                       estimate: int, budget: int, prefs: list[str]) -> str:
    """Generate a concise 'why this destination' summary"""
    budget_ok = estimate <= budget
    strongest = max(scores.items(), key=lambda x: x[1])
    weakest = min(scores.items(), key=lambda x: x[1])

    parts = [f"Rated {score:.2f}/5 overall."]
    if budget_ok:
        parts.append(f"Affordable at RMB{estimate} (under budget)")
    else:
        parts.append(f"RMB{estimate} estimate ({'over' if not budget_ok else 'under'} budget)")

    if strongest[1] >= 4.0:
        parts.append(f"Best in {strongest[0]}: {explanations[strongest[0]][:30]}...")
    if weakest[1] <= 3.0:
        parts.append(f"Weaker in {weakest[0]} - {explanations[weakest[0]][:30]}...")

    return " ".join(parts)


# ─── Recommender Engine ─────────────────────────────────────

class TravelRecommender:
    def __init__(self):
        self.destinations = load_destinations()

    def _adjust_weights(self, inp: dict) -> dict:
        """Dynamic weight adjustment based on user input and seasonal factors"""
        w = {'cost': 0.30, 'route': 0.20, 'review': 0.25, 'weather': 0.15, 'pref': 0.10}

        budget = inp.get('budget', 4000)
        month = _month_from_date(inp.get('travel_date', '2026-07'))
        travelers = inp.get('travelers', '')
        days = inp.get('days', 5)
        prefs = inp.get('preferences', [])
        region = inp.get('region', 'all')

        # ─── Budget-based adjustments ──────────────────────────
        if budget <= 2000:
            w['cost'] += 0.15
            w['weather'] -= 0.07
            w['pref'] -= 0.05
            w['route'] -= 0.03
        elif budget <= 3000:
            w['cost'] += 0.10
            w['weather'] -= 0.05
            w['pref'] -= 0.05
        elif budget <= 5000:
            pass  # balanced
        elif budget <= 8000:
            w['cost'] -= 0.05
            w['weather'] += 0.03
            w['pref'] += 0.02
        else:
            w['cost'] -= 0.10
            w['pref'] += 0.05
            w['review'] += 0.05

        # ─── Seasonal factors ──────────────────────────────────
        season_name = {12: "winter", 1: "winter", 2: "winter",
                       3: "spring", 4: "spring", 5: "spring",
                       6: "summer", 7: "summer", 8: "summer",
                       9: "autumn", 10: "autumn", 11: "autumn"}.get(month, "summer")

        if season_name == "summer":
            # Summer: weather matters more (heat/rain/typhoon)
            w['weather'] += 0.15
            w['cost'] -= 0.08
            w['route'] -= 0.04
            w['pref'] -= 0.03
        elif season_name == "winter":
            # Winter: cost matters less (peak season), route matters more
            w['weather'] += 0.10  # cold destinations vs warm
            w['cost'] += 0.05     # peak season prices
            w['route'] += 0.03
            w['pref'] -= 0.03
        elif season_name == "spring":
            w['weather'] += 0.05
            w['review'] += 0.03
        elif season_name == "autumn":
            w['weather'] += 0.08
            w['pref'] += 0.02

        # ─── Preference-driven adjustments ─────────────────────
        pref_types = " ".join(prefs).lower()
        # When user specifies concrete preferences, boost preference weight
        if len(prefs) >= 1:
            w['pref'] += 0.08
            w['weather'] -= 0.05
            w['review'] -= 0.03
        if "summer" in pref_types:
            w['weather'] += 0.05
        if "winter" in pref_types:
            w['weather'] += 0.05
        if "budget" in pref_types or "cheap" in pref_types:
            w['cost'] += 0.10
            w['pref'] -= 0.05
        if "luxury" in pref_types:
            w['cost'] -= 0.10
            w['review'] += 0.05
            w['pref'] += 0.05
        if "nature" in pref_types or "outdoor" in pref_types:
            w['weather'] += 0.05
            w['route'] += 0.03

        # Limited preferences -> preference carries more weight
        if len(prefs) <= 1:
            w['pref'] += 0.08
            w['cost'] -= 0.04
            w['review'] -= 0.04
        elif len(prefs) >= 4:
            w['pref'] -= 0.03
            w['review'] += 0.03

        # ─── Traveler type adjustments ─────────────────────────
        if travelers in ['family', 'kids', 'elderly']:
            w['review'] += 0.12
            w['cost'] -= 0.06
            w['route'] -= 0.06
        elif travelers in ['couple', 'honeymoon']:
            w['pref'] += 0.08
            w['review'] += 0.04
            w['weather'] += 0.03
        elif travelers in ['solo', 'friends']:
            w['cost'] += 0.05
            w['route'] += 0.03
            w['pref'] += 0.02

        # ─── Trip duration adjustments ─────────────────────────
        if days <= 2:
            w['route'] += 0.10
            w['cost'] -= 0.05
            w['weather'] -= 0.05
        elif days <= 4:
            w['route'] += 0.05
        elif days >= 7:
            w['route'] += 0.05
            w['cost'] += 0.05
            w['weather'] -= 0.05
            w['pref'] += 0.03
        elif days >= 10:
            w['route'] += 0.08
            w['cost'] += 0.08
            w['weather'] -= 0.08

        # ─── Region adjustments ────────────────────────────────
        if region == "international":
            w['cost'] -= 0.05
            w['route'] += 0.05
        elif region == "domestic":
            w['route'] += 0.03

        # ─── Season + Preference combo (synergy bonuses) ──────
        if season_name == "summer" and ("beach" in pref_types or "summer" in pref_types):
            w['weather'] += 0.05
        if season_name == "winter" and ("ski" in pref_types or "winter" in pref_types):
            w['weather'] += 0.05
            w['pref'] += 0.05
        if season_name == "summer" and ("mountain" in pref_types or "nature" in pref_types):
            # Summer mountain escapes
            w['weather'] += 0.08
        if season_name == "summer" and ("food" in pref_types):
            w['weather'] -= 0.02  # food destinations might be hot

        # Normalize to ensure sum = 1.0
        total = sum(w.values())
        if abs(total - 1.0) > 0.01:
            factor = 1.0 / total
            for k in w:
                w[k] = round(w[k] * factor, 4)

        return w

    def recommend(self, inp: dict) -> list[dict]:
        w = self._adjust_weights(inp)
        month = _month_from_date(inp.get('travel_date', '2026-07'))
        si = _season_index(month)
        budget = inp.get('budget', 4000)
        days = inp.get('days', 5)
        prefs = inp.get('preferences', [])
        departure = inp.get('departure', 'Shanghai')
        region_filter = inp.get('region', 'all')

        results = []
        for d in self.destinations:
            if region_filter == 'domestic' and d.country != 'China':
                continue
            if region_filter == 'international' and d.country == 'China':
                continue

            cs = score_cost(d, budget, days, si, departure)
            rs = score_route(d, departure, si)
            vs = score_review(d)
            ws = score_weather(d, month)
            ps = score_preference(d, prefs, month)

            total = cs * w['cost'] + rs * w['route'] + vs * w['review'] + ws * w['weather'] + ps * w['pref']
            # 🆕 探索加分：让新聚合的目的地有机会进入推荐结果
            if d.id >= 62:
                total += 0.3
            est_data = _total_estimate(d, days, si, departure)
            est = est_data[0]
            flight_cost = est_data[1]
            local_cost = est_data[2]
            trans_detail = est_data[3]

            # Build score explanations
            cost_why = _explain_cost(cs, budget, est, days)
            route_why = _explain_route(rs, departure, d.name, d.region)
            review_why = _explain_review(vs, d.rating_overall, d.rating_count)
            weather_why = _explain_weather(ws, d, month)
            pref_why = _explain_preference(ps, prefs, d.keywords, d.dest_type, month)

            results.append({
                'id': d.id,
                'name': d.name,
                'name_cn': CN_NAMES.get(d.name, d.name),
                'type': d.dest_type,
                'country': d.country,
                'region': d.region,
                'latitude': d.latitude,
                'longitude': d.longitude,
                'description': d.description,
                'keywords': d.keywords,
                'total_score': round(total, 2),
                'scores': {
                    'cost': round(cs, 1),
                    'route': round(rs, 1),
                    'review': round(vs, 1),
                    'weather': round(ws, 1),
                    'preference': round(ps, 1),
                },
                'estimate': est,
                'estimate_detail': {
                    'flight': flight_cost,
                    'hotel': d.cost_hotel_per_night[si] * (days - 1),
                    'food': d.cost_food_per_day[si] * days,
                    'ticket': d.cost_ticket,
                    'transport': local_cost,
                },
                'weather_detail': _get_weather_detail(d, month) if _HAS_REAL_WEATHER else None,
                'review_detail': {
                    'rating': d.rating_overall,
                    'count': d.rating_count,
                },
                'transport_detail': trans_detail,
                'score_explanations': {
                    'cost': cost_why,
                    'route': route_why,
                    'review': review_why,
                    'weather': weather_why,
                    'preference': pref_why,
                },
                'why_text': _generate_why_text(d.name, total, {
                    'cost': round(cs, 1), 'route': round(rs, 1),
                    'review': round(vs, 1), 'weather': round(ws, 1),
                    'preference': round(ps, 1),
                }, {
                    'cost': cost_why, 'route': route_why,
                    'review': review_why, 'weather': weather_why,
                    'preference': pref_why,
                }, est, budget, prefs),
            })

        results.sort(key=lambda r: r['total_score'], reverse=True)
        return self._diversify(results, top_k=5)

    def _diversify(self, results: list[dict], top_k: int = 5) -> list[dict]:
        if len(results) <= top_k:
            return results[:top_k]

        selected = [results.pop(0)]
        while len(selected) < top_k and results:
            best_i, best_s = 0, -float('inf')
            for i, c in enumerate(results):
                sim = sum(1 for s in selected if c['type'] == s['type'])
                db = 1.0 - (sim * 0.2)
                mmr = c['total_score'] * db
                if mmr > best_s:
                    best_s = mmr
                    best_i = i
            selected.append(results.pop(best_i))

        return selected


# ─── CLI Entry ────────────────────────────────────────────


def _get_weather_detail(dest, month: int) -> dict:
    """Weather details - uses latitude-based estimate (no API)"""
    if month in dest.weather:
        w = dest.weather[month]
        return {"comfort": w[3], "temp_hi": w[0], "temp_lo": w[1], "rain": w[2]}
    lat = abs(dest.latitude)
    if lat < 23.5:
        hi, lo, rain = 32, 24, 80
    elif lat < 35:
        hi, lo, rain = 28, 18, 60
    elif lat < 45:
        hi, lo, rain = 22, 12, 40
    else:
        hi, lo, rain = 15, 5, 30
    return {"comfort": 3.5, "temp_hi": hi, "temp_lo": lo, "rain": rain}



def main():
    rec = TravelRecommender()
    inp = {
        'budget': 4000, 'days': 5, 'travel_date': '2026-07',
        'departure': 'Shanghai', 'preferences': ['beach', 'food'],
        'region': 'all',
    }

    res = rec.recommend(inp)
    print("=" * 60)
    print("Travel Recommendation Results")
    print(f"Budget: {inp['budget']} | {inp['days']} days | {inp['travel_date']} | from {inp['departure']}")
    print(f"Prefs: {', '.join(inp['preferences'])}")
    print("=" * 60 + "\n")

    for i, r in enumerate(res, 1):
        s = r['scores']
        print(f"#{i}  {r['name']}  [{r['type']}]  Score: {r['total_score']}")
        print(f"   Cost={s['cost']} Route={s['route']} Review={s['review']} Weather={s['weather']} Pref={s['preference']}")
        print(f"   Estimate: RMB {r['estimate']:,}")
        print(f"   Desc: {r['description']}\n")


if __name__ == '__main__':
    main()
