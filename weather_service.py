# -*- coding: utf-8 -*-
"""
weather_service.py — Open-Meteo 天气集成 (v3)
- 使用内存缓存（CacheManager）+ 文件缓存双层
- 支持实时7天预报 + 月度历史查询
- 优雅降级：API 失败时返回纬度估算
"""
import json, time, os, urllib.request
from datetime import datetime

from cache_manager import weather_cache as mem_cache

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".weather_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
FILE_CACHE_TTL = 21600  # 6 小时

USER_AGENT = "TravelRecommender/2.0"


def _file_cache_path(lat, lon, label):
    fname = f"{lat:.2f}_{lon:.2f}_{label}.json"
    return os.path.join(CACHE_DIR, fname)


def _file_get(path):
    if os.path.exists(path) and (time.time() - os.path.getmtime(path)) < FILE_CACHE_TTL:
        with open(path, "r") as f:
            return json.load(f)
    return None


def _file_set(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, socket.timeout) as e:
        print(f"  [weather] fetch error: {e}")
        return {}


def _latitude_estimate(lat, month):
    """纬度估算（降级方案）"""
    import math
    is_summer = month in [5, 6, 7, 8, 9]
    is_tropical = abs(lat) < 23.5
    if is_tropical:
        hi, lo, rain = 32, 24, 80
    elif abs(lat) < 35:
        hi, lo, rain = 28, 18, 60
    elif abs(lat) < 45:
        hi, lo, rain = 22, 12, 40
    else:
        hi, lo, rain = 15, 5, 30
    comfort = 3.5
    if is_summer and is_tropical:
        comfort = 4.0 if lat < 20 else 3.0
    return {"comfort": comfort, "temp_hi": hi, "temp_lo": lo, "rain": rain, "source": "estimate"}


def get_forecast(lat, lon, days=7):
    """获取实时天气预报（Open-Meteo）"""
    mk = f"forecast_{lat:.2f}_{lon:.2f}_{days}d"

    # 1. 查内存缓存
    mem = mem_cache.get(mk)
    if mem:
        return {**mem, "source": "memory"}

    # 2. 查文件缓存
    fp = _file_cache_path(lat, lon, f"forecast_{days}d")
    file_data = _file_get(fp)
    if file_data:
        mem_cache.set(mk, file_data, ttl=3600)
        return {**file_data, "source": "file_cache"}

    # 3. 查月度历史（从 destinations weather dict 提取）
    #    实际调用 Open-Meteo
    params = (
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&current_weather=true&timezone=auto&forecast_days={days}"
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    data = _fetch(url)
    if not data or "daily" not in data:
        return None  # 让调用方用降级

    daily = data["daily"]
    result = {
        "temp_hi": max(daily["temperature_2m_max"]),
        "temp_lo": min(daily["temperature_2m_min"]),
        "rain": sum(daily["precipitation_sum"]),
        "forecast": [
            {"date": daily["time"][i], "hi": daily["temperature_2m_max"][i],
             "lo": daily["temperature_2m_min"][i], "rain": daily["precipitation_sum"][i]}
            for i in range(min(len(daily["time"]), days))
        ],
        "current": data.get("current_weather", {}),
        "source": "api",
    }
    # 估算舒适度
    avg_temp = (result["temp_hi"] + result["temp_lo"]) / 2
    if avg_temp > 32:
        result["comfort"] = 2.5
    elif avg_temp > 28:
        result["comfort"] = 3.0
    elif avg_temp > 22:
        result["comfort"] = 4.0
    elif avg_temp > 10:
        result["comfort"] = 4.5
    else:
        result["comfort"] = 2.0

    # 写入两级缓存
    mem_cache.set(mk, result, ttl=1800)
    _file_set(fp, result)
    return result


def compute_monthly_avg(lat, lon, month, year=None):
    """获取月度平均天气（用于历史评分）"""
    if year is None:
        year = datetime.now().year

    mk = f"monthly_{lat:.2f}_{lon:.2f}_{year}_{month}"
    mem = mem_cache.get(mk)
    if mem:
        return {**mem, "source": "memory"}

    fp = _file_cache_path(lat, lon, f"monthly_{year}_{month}")
    file_data = _file_get(fp)
    if file_data:
        mem_cache.set(mk, file_data, ttl=7200)
        return {**file_data, "source": "file_cache"}

    # Open-Meteo 预报 API (含历史 = past_days)
    params = (
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&past_days=30&forecast_days=0&timezone=auto"
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    data = _fetch(url)
    if not data or "daily" not in data:
        return _latitude_estimate(lat, month)

    daily = data["daily"]
    temps = daily["temperature_2m_max"]
    if not temps:
        return _latitude_estimate(lat, month)

    result = {
        "temp_hi": round(max(temps), 1),
        "temp_lo": round(min(daily["temperature_2m_min"]), 1),
        "rain": round(sum(r for r in daily["precipitation_sum"] if r is not None), 0),
        "source": "api",
    }
    avg = (result["temp_hi"] + result["temp_lo"]) / 2
    if avg > 32: result["comfort"] = 2.5
    elif avg > 28: result["comfort"] = 3.0
    elif avg > 22: result["comfort"] = 4.0
    elif avg > 10: result["comfort"] = 4.5
    else: result["comfort"] = 2.0

    mem_cache.set(mk, result, ttl=7200)
    _file_set(fp, result)
    return result


# ─── Weather Warning System ───────────────────────────────

def check_weather_warnings(lat, lon, month, temp_hi=None, temp_lo=None, rain=None):
    """Check weather conditions and return list of warnings."""
    warnings = []
    if temp_hi is not None:
        if temp_hi >= 38:
            warnings.append({"level": 2, "label": "\u9ad8\u6e29\u66b4\u6652", "icon": "\u2600\ufe0f",
                             "advice": "\u907f\u514d\u4e2d\u5348\u6237\u5916\u6d3b\u52a8\uff0c\u6ce8\u610f\u9632\u66ec"})
        elif temp_hi >= 35:
            warnings.append({"level": 1, "label": "\u708e\u70ed", "icon": "\u2600\ufe0f",
                             "advice": "\u5efa\u8bae\u907f\u5f00\u4e2d\u5348\u66b4\u6652"})
        if temp_hi < 10:
            warnings.append({"level": 2, "label": "\u5bd2\u51b7", "icon": "\u2744\ufe0f",
                             "advice": "\u6ce8\u610f\u4fdd\u6696\uff0c\u53ef\u80fd\u4e0d\u9002\u5408\u6e38\u73a9"})
        elif temp_hi < 18:
            warnings.append({"level": 1, "label": "\u5fae\u51c9", "icon": "\u2744\ufe0f",
                             "advice": "\u5efa\u8bae\u52a0\u4ef6\u5916\u5957"})
    if rain is not None:
        if rain >= 100:
            warnings.append({"level": 2, "label": "\u66b4\u96e8", "icon": "\u2614",
                             "advice": "\u5f53\u5fc3\u66b4\u96e8\u5f71\u54cd\u884c\u7a0b"})
        elif rain >= 50:
            warnings.append({"level": 1, "label": "\u591a\u96e8", "icon": "\u2614",
                             "advice": "\u5efa\u8bae\u643a\u5e26\u96e8\u5177"})
    abs_lat = abs(lat)
    is_coastal = 18 <= abs_lat <= 35 and 108 <= lon <= 125
    is_seasia = abs_lat <= 20 and 95 <= lon <= 115
    is_schina = abs_lat <= 25 and 100 <= lon <= 120
    if month in [7, 8, 9] and (is_coastal or is_seasia):
        warnings.append({"level": 2, "label": "\u53f0\u98ce\u5b63", "icon": "\U0001f300",
                         "advice": "7-9\u6708\u53f0\u98ce\u9ad8\u53d1\uff0c\u5173\u6ce8\u5929\u6c14\u9884\u62a5"})
    if month in [5, 6, 7, 8, 9] and is_schina:
        warnings.append({"level": 1, "label": "\u96e8\u5b63", "icon": "\U0001f327\ufe0f",
                         "advice": "\u96e8\u5b63\u5f53\u5fc3\u66b4\u96e8\u95f4\u6b47\u6027\u79ef\u6c34"})
    if month in [6, 7, 8] and abs_lat > 35:
        warnings.append({"level": 1, "label": "\u907f\u66ec\u80dc\u5730", "icon": "\U0001f332",
                         "advice": "\u590f\u5b63\u6e05\u723d\uff0c\u9002\u5408\u907f\u66ec"})
    return warnings


def enrich_with_warnings(results, inp):
    """Add weather warnings to each result (background thread)"""
    import weather_service
    month = int(inp.get("travel_date", "2026-07").split("-")[1])
    for res in results:
        lat = res.get("latitude")
        lon = res.get("longitude")
        if not lat or not lon:
            continue
        fc = None
        try:
            fc = weather_service.get_forecast(lat, lon, days=3)
        except Exception:
            pass
        if fc and fc.get("temp_hi") is not None:
            hi, lo, rain = fc["temp_hi"], fc.get("temp_lo", 20), fc.get("rain", 0)
        else:
            est = weather_service._latitude_estimate(lat, month)
            hi, lo, rain = est["temp_hi"], est["temp_lo"], est.get("rain", 0)
        warnings = check_weather_warnings(lat, lon, month, hi, lo, rain)
        if warnings:
            res["weather_warnings"] = warnings
    return results
