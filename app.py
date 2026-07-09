"""\napp.py — Final optimized version\n"""
import os, json, uvicorn, threading, time, logging, base64
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 配置文件
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from travel_recommender import TravelRecommender
from itinerary import add_itinerary_to_results
from cache_manager import result_cache, run_periodic_cleanup
from memory import short_term, medium_term, long_term
from feedback import save_feedback, init_db, get_feedback_summary
from flight_tracker import track_route, batch_track, get_route_info, get_low_price_alerts, estimate_price, set_alert, check_alerts, get_my_alerts, remove_alert, get_price_history, track_route as _track_route
from zh_names import CN_NAMES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ─── 出发城市名汉化映射 ─────────────────────────
CITY_MAP = {
    "上海": "Shanghai",
    "北京": "Beijing",
    "广州": "Guangzhou",
    "深圳": "Shenzhen",
    "成都": "Chengdu",
    "杭州": "Hangzhou",
    "南京": "Nanjing",
    "武汉": "Wuhan",
    "重庆": "Chongqing",
    "西安": "Xi'an",
    "昆明": "Kunming",
    "长沙": "Changsha",
    "沈阳": "Shenyang",
    "青岛": "Qingdao",
    "大连": "Dalian",
    "厦门": "Xiamen",
    "三亚": "Sanya",
    "桂林": "Guilin",
    "拉萨": "Lhasa",
    "呼和浩特": "Hohhot",
    "乌鲁木齐": "Urumqi",
    "苏州": "Suzhou",
    "天津": "Tianjin",
    "郑州": "Zhengzhou",
    "合肥": "Hefei",
    "贵阳": "Guiyang",
    "南宁": "Nanning",
    "前佛": "Haikou",
}


def _normalize_city(city: str) -> str:
    """Convert Chinese city name to English for scoring"""
    trimmed = city.strip()
    if trimmed in CITY_MAP:
        return CITY_MAP[trimmed]
    return trimmed  # Already English or unknown


def _build_discovery_result(city_name: str, parsed_data: dict) -> dict:
    """从美团解析数据构建临时目的地推荐结果"""
    all_keywords = []
    for cat in parsed_data.get("categories", []):
        for attr in cat.get("attractions", []):
            all_keywords.extend(attr.get("keywords", []))
    all_keywords = list(dict.fromkeys(all_keywords))[:8]  # 去重，限制
    total_attrs = sum(len(cat.get("attractions", [])) for cat in parsed_data.get("categories", []))
    # 从关键词推断目的地类型
    kw_text = " ".join(all_keywords).lower() + " " + " ".join(c["name"] for c in parsed_data.get("categories", []))
    _type = "General"
    if any(k in kw_text for k in ("海", "沙滩", "海滩", "岛", "湾", "滨海")):
        _type = "Beach"
    elif any(k in kw_text for k in ("山", "峰", "峡谷", "瀑布", "登")):
        _type = "Mountain"
    elif any(k in kw_text for k in ("古城", "古镇", "古村")):
        _type = "Ancient Town"
    elif any(k in kw_text for k in ("温泉")):
        _type = "Hot Spring"
    elif any(k in kw_text for k in ("湖", "水乡", "江")):
        _type = "Lake"
    return {
        "name": city_name,
        "name_cn": city_name,
        "type": _type,
        "country": "China",
        "region": "East China",
        "description": f"美团发现 · {len(parsed_data.get('categories', []))}个分类 {total_attrs}个景点",
        "keywords": all_keywords,
        "total_score": 4.0,
        "scores": {"cost": 4.0, "route": 3.5, "review": 4.0, "weather": 4.0, "preference": 4.0},
        "estimate": 0,
        "latitude": 31.0,
        "longitude": 121.0,
    }


init_db()
app = FastAPI()
recommender = TravelRecommender()
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# ─── 搜索缓存磁盘持久化 ─────────────────────────
RESULT_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "result_cache.json")
result_cache.load_from_file(RESULT_CACHE_FILE)

def _save_result_cache():
    """后台定期保存搜索结果缓存到磁盘"""
    while True:
        time.sleep(120)  # 每 2 分钟保存一次
        result_cache.save_to_file(RESULT_CACHE_FILE)

threading.Thread(target=_save_result_cache, daemon=True).start()
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles as _StaticFiles
class NoCacheStaticFiles(_StaticFiles):
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        if path.endswith(".js"):
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
        return resp

app.mount("/js", NoCacheStaticFiles(directory=os.path.join(STATIC_DIR, "js")), name="js")
import threading
threading.Thread(target=run_periodic_cleanup, args=(300,), daemon=True).start()


# ─── 缓存版本号 ─────────────────────────
# 当目的地数据变更时，修改此版本号使旧缓存自动失效
CACHE_DATA_VERSION = "v2"  # v2: 126 destinations (was 58)


from reviews_api import get_reviews, get_review_stats, get_top_reviews, add_review


def _cache_key(inp: dict) -> str:
    """生成带版本号的缓存键"""
    return CACHE_DATA_VERSION + "|" + str(sorted((str(k), str(v)) for k, v in inp.items()))


def _get(inp):
    k = _cache_key(inp)
    cached = result_cache.get(k)
    if cached is not None:
        return cached
    r = recommender.recommend(inp)
    result_cache.set(k, r, ttl=3600)
    return r


def _enrich_ctrip(key, results, inp):
    """Background: add Ctrip travel advice to results"""
    try:
        from ctrip_integration import enrich_with_ctrip
        results = enrich_with_ctrip(results, inp)
        result_cache.set(key, results, ttl=300)
        logger.info("[ctrip] enriched %s", str(inp)[:30])
    except Exception as e:
        logger.warning("[ctrip] error: %s", str(e)[:60])

def _warn_weather(key, results, inp):
    """Background: add weather warnings"""
    try:
        from weather_service import enrich_with_warnings
        results = enrich_with_warnings(results, inp)
        result_cache.set(key, results, ttl=300)
        logger.info("[warn] enriched %s", str(inp)[:40])
    except Exception as e:
        logger.warning("[warn] error: %s", str(e)[:60])

def _track_results(departure, results):
    # Background: track prices for top results
    try:
        names = [r["name"].split(" (")[0].split("/")[0] for r in results[:5]]
        batch_track(departure, names)
    except Exception as e:
        logger.warning("[track] error: %s", str(e)[:60])


def _enrich_weather(key, results, inp):
    """Background: fetch real Open-Meteo weather for top results"""
    try:
        from weather_service import compute_monthly_avg
        month = int(inp.get("travel_date", "2026-07").split("-")[1])
        for res in results:
            lat = res.get("latitude")
            lon = res.get("longitude")
            if lat and lon:
                wd = compute_monthly_avg(lat, lon, month)
                if wd and wd.get("source") in ("api", "memory"):
                    res["weather_detail"] = {
                        "temp_hi": wd["temp_hi"],
                        "temp_lo": wd["temp_lo"],
                        "rain": wd["rain"],
                        "comfort": wd.get("comfort", 3.5),
                        "source": "open-meteo"
                    }
        result_cache.set(key, results, ttl=300)
        logger.info("[weather] enriched " + key[:30])
    except Exception as e:
        logger.warning("[weather] enrich error: %s", str(e)[:60])


def _enrich_ai(key, results, inp):
    """Generate AI blurbs in background, update cache"""
    try:
        need_ai = sum(1 for r in results if not r.get("ai_blurb"))
        if need_ai == 0:
            return
        time.sleep(0.1)  # let the response go out first
        from ai_writer import batch_generate
        enriched = batch_generate(results, inp["budget"], inp["days"], inp.get("preferences", []))
        if enriched:
            result_cache.set(key, enriched, ttl=300)
            logger.info("[ai] enriched " + key[:30])
    except Exception as e:
        logger.error("[ai] error: %s", str(e)[:60])

@app.on_event("startup")
async def startup():
    # Init long-term memory
    try:
        from travel_recommender import TravelRecommender
        _rec = TravelRecommender()
        from zh_names import CN_NAMES
        dests = [{"name": d.name, "name_cn": CN_NAMES.get(d.name, d.name),
                  "description": d.description, "keywords": d.keywords, "type": d.dest_type}
                 for d in _rec.destinations]
        long_term.build_index(dests)
        logger.info("[memory] long-term index: %d destinations", len(dests))
    except Exception as e:
        logger.warning("[memory] init: %s", str(e)[:60])

@app.get("/", response_class=HTMLResponse)
async def index():
    p = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            html = f.read()
        import re
        import time
        ts = str(int(time.time()))
        html = re.sub(r'app\.js\?v=\d+', 'app.js?v=' + ts, html)
        html = re.sub(r'map\.js\?v=\d+', 'map.js?v=' + ts, html)
        return HTMLResponse(content=html, headers={"Cache-Control": "no-cache, no-store, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"})
    return "<h1>Travel Recommender</h1>"

@app.get("/learning-os", response_class=HTMLResponse)
async def learning_os():
    p = os.path.join(STATIC_DIR, "learning-os.html")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            html = f.read()
        return HTMLResponse(content=html, headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"})
    return "<h1>Not Found</h1>"

@app.get("/api/recommend", response_class=JSONResponse)
async def api_recommend(
    budget: float = Query(4000),
    days: int = Query(5),
    travel_date: str = Query("2026-07"),
    departure: str = Query("Shanghai"),
    preferences: str = Query(""),
    travelers: str = Query("solo"),
    region: str = Query("all"),
):
    import asyncio
    pl = [p.strip() for p in preferences.split(",") if p.strip()]
    departure = _normalize_city(departure)
    inp = {
        "budget": int(budget), "days": int(days),
        "travel_date": travel_date, "departure": departure,
        "preferences": pl, "travelers": travelers, "region": region,
    }
    results = await asyncio.get_event_loop().run_in_executor(None, _get, inp)
    for r in results:
        try:
            stats = get_review_stats(r.get("name_cn", ""))
            if stats and stats.total_count > 0:
                r["review_summary"] = stats.to_dict()
                top = get_top_reviews(r.get("name_cn", ""), limit=2)
                r["review_summary"]["top_reviews"] = top
        except Exception:
            pass

    # ── 后台增强（非阻塞，daemon 线程） ──
    cache_k = _cache_key(inp)
    threading.Thread(target=_enrich_ai, args=(cache_k, results, inp), daemon=True).start()
    threading.Thread(target=_enrich_weather, args=(cache_k, results, inp), daemon=True).start()
    threading.Thread(target=_warn_weather, args=(cache_k, results, inp), daemon=True).start()
    threading.Thread(target=_track_results, args=(departure, results), daemon=True).start()

    return {"results": results, "input": inp}


@app.get("/api/feedback", response_class=JSONResponse)
async def fb(dest="", helpful=1, score=0, budget=0, days=0, travel_date="", preferences=""):
    i = save_feedback(dest, helpful, score, budget, days, travel_date,
        [p.strip() for p in preferences.split(",") if p.strip()])
    return {"ok": True, "id": i}

@app.get("/api/feedback/stats")
async def fbs():
    return get_feedback_summary()


@app.get("/api/flight/estimate")
async def flight_estimate(departure="Shanghai", destination="Sanya", travel_date="2026-07"):
    return estimate_price(departure, destination, int(travel_date.split("-")[1]) if "-" in travel_date else 7)


@app.get("/api/flight/track")
async def flight_track(departure="Shanghai", destinations="Sanya") -> JSONResponse:
    dests = [d.strip() for d in destinations.split(",") if d.strip()]
    results = batch_track(departure, dests)
    return {"routes": results}


@app.get("/api/flight/alerts")
async def flight_alerts():
    return {"alerts": get_low_price_alerts()}


@app.get("/api/flight/set-alert")
async def set_flight_alert(departure="Shanghai", destination="Sanya", target_price: float = 3000):
    return set_alert(departure, destination, target_price)


@app.get("/api/flight/my-alerts")
async def my_alerts():
    return {"alerts": get_my_alerts()}


@app.get("/api/flight/check-alerts")
async def run_check():
    triggered = check_alerts()
    if triggered:
        for t in triggered:
            logger.info(f"[alert] {t['departure']}->{t['destination']} now RMB {t['current_price']}")
    return {"triggered": triggered, "count": len(triggered)}


@app.get("/api/flight/remove-alert")
async def remove_flight_alert(alert_id: int = 0):
    ok = remove_alert(alert_id)
    return {"ok": ok}


@app.get("/api/dest-image")
async def dest_image(name="", name_cn="", dest_type=""):
    """Get destination image (local file or SVG)"""
    from dest_images import get_dest_image
    result = get_dest_image(name, name_cn, dest_type)
    return {"url": result["url"], "name": name, "name_cn": name_cn,
            "source": result.get("source", "svg")}


@app.get("/api/ctrip/checklist")
async def ctrip_checklist():
    """出行前核对清单"""
    from ctrip_integration import get_checklist
    return {"checklist": get_checklist()}


# 热门出发地（用于启动预热搜索缓存）
HOT_DEPARTURE_CITIES = ["上海", "北京", "广州", "深圳", "杭州", "成都", "武汉", "南京"]

# 前端默认参数（精确匹配缓存 key）
FRONTEND_DEFAULTS = {
    "travel_date": "2026-07",
    "preferences": ["海滩", "美食"],  # 前端默认
    "travelers": "情侣",  # 前端默认
    "region": "all",
}


def _startup_warm_search_cache():
    """后台预热热门出发地的搜索缓存（直接匹配前端默认值）"""
    import time as t
    total = len(HOT_DEPARTURE_CITIES)
    done = 0
    for dep in HOT_DEPARTURE_CITIES:
        inp = {
            "budget": 4000, "days": 5,
            "travel_date": FRONTEND_DEFAULTS["travel_date"],
            "departure": dep,
            "preferences": FRONTEND_DEFAULTS["preferences"],
            "travelers": FRONTEND_DEFAULTS["travelers"],
            "region": FRONTEND_DEFAULTS["region"],
        }
        k = _cache_key(inp)
        cached = result_cache.get(k)
        if cached is not None:
            done += 1
            continue
        done += 1
        logger.info("[warm-cache] %s 前端默认 (%d/%d)", dep, done, total)
        try:
            results = _get(inp)
            # 预热同时触发后台 enrichment
            threading.Thread(target=_enrich_ai, args=(k, results, inp), daemon=True).start()
            threading.Thread(target=_enrich_weather, args=(k, results, inp), daemon=True).start()
        except Exception as e:
            logger.warning("[warm-cache] %s failed: %s", dep, str(e)[:80])
        if done < total:
            t.sleep(5)
    logger.info("[warm-cache] all %d departures warmed", total)
    # 预热后存盘
    result_cache.save_to_file(RESULT_CACHE_FILE)


@app.get("/api/reviews")
async def api_get_reviews(
    destination: str = Query(...),
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1, le=20),
    sort: str = Query("newest"),
    traveler_type: str = Query(""),
):
    """获取目的地评价列表"""
    return get_reviews(destination, page, limit, sort, traveler_type)


@app.get("/api/reviews/stats")
async def api_get_review_stats(destination: str = Query(...)):
    """获取目的地评分统计"""
    stats = get_review_stats(destination)
    return stats.to_dict()


@app.post("/api/reviews")
async def api_post_review(data: dict):
    """提交新评价"""
    from fastapi import Body
    # FastAPI will parse Body automatically
    try:
        review = add_review(data)
        return {"status": "ok", "id": review.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/multi-city")
async def multi_city(
    budget: float = Query(4000),
    days: int = Query(5),
    travel_date: str = Query("2026-07"),
    departure: str = Query("上海"),
    preferences: str = Query(""),
    travelers: str = Query("solo"),
    region: str = Query("all"),
):
    """多城市联游推荐（联动单城市推荐结果）"""
    pl = [p.strip() for p in preferences.split(",") if p.strip()]
    dep = _normalize_city(departure)
    inp = {
        "budget": int(budget), "days": days,
        "travel_date": travel_date, "departure": dep,
        "preferences": pl, "travelers": travelers, "region": region,
    }

    # 联动：先获取单城市推荐结果，提取城市名传给联游引擎
    recommended_cities = []
    try:
        rec_results = _get(inp)
        for r in rec_results[:5]:
            name_cn = r.get("name_cn", r.get("name", ""))
            recommended_cities.append(name_cn)
    except Exception:
        pass

    # 将推荐城市名传入联游引擎
    inp["recommended_cities"] = recommended_cities

    from route_planner import recommend_routes
    routes = recommend_routes(inp)
    return {"routes": routes, "input": inp, "recommended_cities": recommended_cities}


@app.get("/api/memory/short")
async def memory_short(n: int = 3):
    """短期记忆：最近 N 轮会话"""
    return {"rounds": short_term.get_recent(n), "size": short_term.size}


@app.get("/api/memory/medium")
async def memory_medium():
    """中期记忆：用户偏好"""
    data = medium_term.get()
    # Make JSON serializable
    return {k: v for k, v in data.items()}


@app.get("/api/memory/long")
async def memory_long(q: str = "", top_k: int = 5, type_filter: str = ""):
    """长期记忆：语义搜索目的地"""
    if type_filter:
        results = long_term.search_by_type(type_filter, top_k)
    elif q:
        results = long_term.search(q, top_k)
    else:
        results = []
    return {"query": q, "results": results, "ready": long_term._ready}


@app.get("/api/memory")
async def memory_status():
    """三层记忆状态"""
    med = medium_term.get()
    return {
        "short_term": {"size": short_term.size, "ttl": short_term.ttl},
        "medium_term": {k: v for k, v in med.items() if k != "preferences" or v},
        "long_term": {"ready": long_term._ready, "index_size": len(long_term._index) if long_term._ready else 0},
    }

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/test")
async def test_page():
    p = os.path.join(STATIC_DIR, "minimal.html")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Test page not found</h1>")


@app.get("/diag")
async def diag_page():
    p = os.path.join(STATIC_DIR, "diag.html")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Diag page not found</h1>")

# ─── 高德地图 API ──────────────────────────────────────

AMAP_KEY = "c3f42783f3081dab7f5235ba4d1903d2"
AMAP_SECRET = "3ca9456394bc116e4f286728d0ddf470"


@app.get("/api/geocode")
async def geocode(address: str = "上海"):
    """高德地理编码：城市名 → 坐标"""
    import urllib.request
    url = f"https://restapi.amap.com/v3/geocode/geo?key={AMAP_KEY}&address={address}&output=JSON"
    try:
        r = urllib.request.urlopen(url, timeout=5)
        data = json.loads(r.read().decode())
        if data.get("status") == "1" and data.get("geocodes"):
            g = data["geocodes"][0]
            loc = g["location"].split(",")
            return {"ok": True, "name": g.get("formatted_address", address),
                    "lng": float(loc[0]), "lat": float(loc[1]),
                    "adcode": g.get("adcode", ""), "level": g.get("level", "")}
    except Exception as e:
        logger.warning(f"[geocode] error: {e}")
    return {"ok": False, "name": address}


@app.get("/api/amap-config")
async def amap_config():
    return {"key": AMAP_KEY, "jscode": AMAP_SECRET}


# ─── POI 景点搜索 ─────────────────────────
_POI_DATA = None  # lazy loaded
_POI_CITIES = []
_POI_TYPES = []

def _load_poi_data():
    global _POI_DATA, _POI_CITIES, _POI_TYPES
    if _POI_DATA is not None:
        return _POI_DATA
    poi_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "enriched_ai.json")
    if not os.path.exists(poi_path):
        logger.warning("[poi] enriched_ai.json not found")
        _POI_DATA = {"destinations": []}
        return _POI_DATA
    with open(poi_path, "r", encoding="utf-8") as f:
        _POI_DATA = json.load(f)
    cities = set()
    types = set()
    for d in _POI_DATA["destinations"]:
        if d.get("city"): cities.add(d["city"])
        if d.get("dest_type"): types.add(d["dest_type"])
    _POI_CITIES = sorted(cities, key=lambda x: {"上海":0,"浙江":1,"江苏":2,"广东":3,"四川":4,"北京":5}.get(x,9))
    _POI_TYPES = sorted(types)
    logger.info("[poi] loaded %d destinations, %d cities, %d types",
                len(_POI_DATA["destinations"]), len(_POI_CITIES), len(_POI_TYPES))
    return _POI_DATA

@app.get("/api/poi-search")
async def poi_search(
    q: str = Query(""),
    city: str = Query(""),
    dest_type: str = Query(""),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """搜索具体的 POI 景点（10,997 条 AI 增强版）"""
    import asyncio
    import re
    data = _load_poi_data()
    dests = data["destinations"]
    
    q = q.strip().lower()
    city = city.strip()
    dest_type = dest_type.strip()
    
    # 过滤
    results = []
    for d in dests:
        if city and d.get("city", "") != city:
            continue
        if dest_type and d.get("dest_type", "") != dest_type:
            continue
        if q:
            name_cn = (d.get("name_cn", "") or "").lower()
            desc = (d.get("description", "") or "").lower()
            city_name = (d.get("city", "") or "").lower()
            keywords = " ".join(d.get("keywords", [])).lower()
            if not (q in name_cn or q in desc or q in city_name or q in keywords):
                continue
        results.append(d)
    
    total = len(results)
    start = (page - 1) * limit
    end = min(start + limit, total)
    page_dests = results[start:end]
    # 如果有关键词，按描述含有关键词的优先排序
    if q:
        page_dests.sort(key=lambda x: (q in (x.get("description","") or "").lower(),
                                        q in (x.get("name_cn","") or "").lower()), reverse=True)
    
    return {
        "results": page_dests,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "meta": {
            "total_destinations": len(dests),
            "cities": _POI_CITIES,
            "types": _POI_TYPES,
        }
    }


@app.get("/api/poi/city-brief")
async def poi_city_brief(city: str = Query("")):
    """获取城市旅行摘要（天气、评分、价格）用于 POI 搜索结果"""
    if not city:
        return {"found": False}
    try:
        import zh_names
        import time as tm
        rec = recommender
        city_stripped = city.strip()
        
        best = None
        best_score = 0
        for d in rec.destinations:
            cn = zh_names.CN_NAMES.get(d.name, d.name)
            # 精确匹配
            if cn == city_stripped or d.name.lower() == city_stripped.lower():
                best = d
                best_score = 100
                break
            # 包含匹配：如 "杭州" in "杭州" 或 "杭州" in "杭州 (China)"
            if city_stripped in cn or city_stripped in d.name or cn in city_stripped:
                score = len(city_stripped) / max(len(cn), 1)
                if score > best_score:
                    best = d
                    best_score = score
        
        if best:
            now = tm.localtime()
            month = now.tm_mon
            weather = best.weather.get(str(month), [28, 20, 60, 3.5]) if best.weather else [28, 20, 60, 3.5]
            cn_best = zh_names.CN_NAMES.get(best.name, best.name)
            return {
                "found": True,
                "city": cn_best,
                "weather": {
                    "hi": weather[0], "lo": weather[1],
                    "rain": weather[2], "comfort": weather[3]
                },
                "rating": best.rating_overall,
                "rating_count": best.rating_count,
                "hotel_range": best.cost_hotel_per_night,
                "food_range": best.cost_food_per_day,
                "flight_range": best.cost_flight,
                "lat": best.latitude,
                "lon": best.longitude,
                "dest_type": best.dest_type,
            }
    except Exception as e:
        logger.warning("[poi/brief] %s: %s", city, str(e)[:60])
    
    # --- 降级方案：从 POI 数据中获取城市坐标做天气估算 ---
    try:
        data = _load_poi_data()
        lat, lon = None, None
        for d in data["destinations"]:
            c = d.get("city", "")
            if c == city_stripped and d.get("coords"):
                lat = d["coords"].get("lat")
                lon = d["coords"].get("lng")
                break
        if lat and lon:
            from weather_service import _latitude_estimate
            import time as tm
            now = tm.localtime()
            est = _latitude_estimate(lat, now.tm_mon)
            return {
                "found": True,
                "city": city_stripped,
                "weather": {
                    "hi": est["temp_hi"], "lo": est["temp_lo"],
                    "rain": est.get("rain", 60), "comfort": est.get("comfort", 3.5)
                },
                "rating": 0,
                "rating_count": 0,
                "note": "基于纬度估算",
            }
    except Exception as e:
        logger.warning("[poi/brief] fallback %s: %s", city, str(e)[:60])
    
    return {"found": False, "city": city}


@app.get("/api/weather/warning")
async def weather_warning(lat: float = 31.23, lon: float = 121.47, month: int = 7):
    """Get weather warnings for a location"""
    try:
        from weather_service import get_forecast, check_weather_warnings
        fc = get_forecast(lat, lon, days=7)
        if fc and fc.get("temp_hi") is not None:
            hi, lo, rain = fc["temp_hi"], fc.get("temp_lo", 20), fc.get("rain", 0)
        else:
            from weather_service import _latitude_estimate
            est = _latitude_estimate(lat, month)
            hi, lo, rain = est["temp_hi"], est["temp_lo"], est.get("rain", 0)
        warnings = check_weather_warnings(lat, lon, month, hi, lo, rain)
        return {"warnings": warnings, "temp_hi": hi, "temp_lo": lo, "rain": rain, "forecast_days": 7}
    except Exception as e:
        return {"warnings": [], "error": str(e)[:60]}


@app.get("/api/booking")
async def booking_links(departure="上海", destination="三亚", travel_date="2026-07"):
    """Get booking links for a destination"""
    from booking_links import generate_links
    return {"platforms": generate_links(departure, destination, travel_date)}


@app.get("/api/flight/trend")
async def flight_trend(departure="Shanghai", destination="Sanya", travel_date="2026-07", days: int = 30):
    """Get price trend data for a route"""
    key = departure.strip().lower() + "->" + destination.strip().lower()
    history = get_price_history(key, days)
    route = get_route_info(key)
    estimate = estimate_price(departure, destination,
        int(travel_date.split("-")[1]) if "-" in travel_date else 7)
    current_price = route["current_price"] if route else estimate["estimated_price"]

    # If not enough real history, generate synthetic data
    real = [{"price": h["price"], "date": h["checked_at"][:10]} for h in history[-30:]]
    if len(real) < 3:
        import random
        from datetime import datetime, timedelta
        now = datetime.now()
        synthetic = []
        lo = estimate["price_range"]["low"]
        hi = estimate["price_range"]["high"]
        base = max(lo, current_price * 0.85)
        for day in range(min(30, 30 - len(real))):
            d = now - timedelta(days=29 - day)
            p = round(base + random.uniform(-0.15, 0.15) * (hi - lo) + (day / 30) * (current_price - base))
            p = max(lo * 0.9, min(hi * 1.1, p))
            synthetic.append({"price": p, "date": d.strftime("%Y-%m-%d")})
        history_data = synthetic + real
    else:
        history_data = real

    prices = [h["price"] for h in history_data]
    return {
        "route": f"{departure} -> {destination}",
        "current_price": current_price,
        "price_range": estimate["price_range"],
        "lowest_price": min(prices),
        "highest_price": max(prices),
        "trend": route["trend"] if route else "stable",
        "history": history_data[-30:],
        "points": len(history_data),
        "real_points": len(real),
    }


@app.get("/api/flight/track-search")
async def track_search(departure="Shanghai", destinations="Sanya"):
    """Track prices for search results"""
    dests = [d.strip() for d in destinations.split(",") if d.strip()]
    from flight_tracker import batch_track
    results = batch_track(departure, dests)
    return {"tracked": len(results), "routes": results}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
