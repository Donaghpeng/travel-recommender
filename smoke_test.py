#!/usr/bin/env python
"""
smoke_test.py — API 冒烟测试

用途：
  - 确认所有 API 端点正常工作
  - 检测新代码是否破坏了现有功能
  - 每次修改代码后运行：python smoke_test.py

运行要求：
  - 服务器已在 http://127.0.0.1:8000 运行
  - 或指定 --start-server 自动启动

用法：
  python smoke_test.py                    # 测试已运行的服务器
  python smoke_test.py --start-server     # 自动启动服务器再测试
  python smoke_test.py --verbose          # 显示完整响应
  python smoke_test.py --quick            # 只测试核心 API（F1-F5）
"""

import sys, os, json, time, subprocess, urllib.request, urllib.error, signal

BASE_URL = "http://127.0.0.1:8000"
VERBOSE = False
QUICK = False
SERVER_PROC = None

# ── 测试结果统计 ──
passed = 0
failed = 0
results = []


def log_result(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        mark = "✅ PASS"
    else:
        failed += 1
        mark = "❌ FAIL"
    print(f"  {mark}  {name}")
    if detail and (not ok or VERBOSE):
        for line in detail.strip().split("\n"):
            print(f"       {line}")
    results.append((name, ok, detail))


_last_data = {}


def api_get(path, expect_status=200, expect_fields=None):
    """调用 API 并验证，返回 (ok, detail_str)"""
    global _last_data
    # Properly encode the URL for Chinese characters
    from urllib.parse import urlencode, urlparse, parse_qs, quote
    # Split URL to encode the path and query parts
    if "?" in path:
        base, qs = path.split("?", 1)
        # Parse query string and re-encode properly
        params = {}
        for part in qs.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                params[k] = v
        encoded_qs = urlencode(params)
        url = BASE_URL + quote(base, safe="/:@") + "?" + encoded_qs
    else:
        url = BASE_URL + quote(path, safe="/:@")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            data = json.loads(body)
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

    if status != expect_status:
        return False, f"Expected status {expect_status}, got {status}"

    if expect_fields:
        missing = [f for f in expect_fields if f not in data]
        if missing:
            return False, f"Missing fields: {missing} | Keys: {list(data.keys())}"

    _last_data = data
    if VERBOSE:
        return True, json.dumps(data, ensure_ascii=False, indent=2)[:500]
    return True, ""


# ═══════════════════════════════════════════════
# 测试用例
# ═══════════════════════════════════════════════

def test_health():
    """F31: 健康检查"""
    ok, detail = api_get("/health", expect_fields=["status"])
    log_result("/health", ok, detail if isinstance(detail, str) else "")


def test_recommend():
    """F1: 目的地推荐"""
    ok, detail = api_get(
        "/api/recommend?budget=4000&days=5&departure=Shanghai&preferences=beach,food&travelers=couple",
        expect_fields=["results", "input"]
    )
    if ok:
        results_list = _last_data.get("results", [])
        if len(results_list) != 5:
            ok = False
            detail = f"Expected 5 results, got {len(results_list)}"
        else:
            r0 = results_list[0]
            required = ["name", "name_cn", "total_score", "scores", "type", "latitude", "longitude"]
            missing = [f for f in required if f not in r0]
            if missing:
                ok = False
                detail = f"Result missing fields: {missing}"
            else:
                scores = r0.get("scores", {})
                for dim in ["cost", "route", "review", "weather", "preference"]:
                    if dim not in scores:
                        ok = False
                        detail = f"Missing score dimension: {dim}"
                        break
    log_result("/api/recommend", ok, detail)


def test_recommend_with_chinese():
    """F1: 中文出发地"""
    ok, detail = api_get(
        "/api/recommend?budget=3000&days=3&departure=上海&preferences=海滩&travelers=solo",
        expect_fields=["results"]
    )
    log_result("/api/recommend (中文出发)", ok, detail if isinstance(detail, str) else "")


def test_poi_search():
    """F4: POI 景点搜索"""
    ok, detail = api_get(
        "/api/poi-search?q=西湖&limit=2",
        expect_fields=["results", "total", "page", "pages", "meta"]
    )
    if ok:
        if len(_last_data.get("results", [])) == 0:
            ok = False
            detail = "Expected at least 1 result for '西湖', got 0"
    log_result("/api/poi-search", ok, detail)


def test_poi_search_empty():
    """F4: POI 空搜索"""
    ok, detail = api_get(
        "/api/poi-search?limit=1",
        expect_fields=["results", "total", "meta"]
    )
    log_result("/api/poi-search (空关键词)", ok, detail if isinstance(detail, str) else "")


def test_poi_city_brief():
    """F5: 城市摘要"""
    ok, detail = api_get(
        "/api/poi/city-brief?city=杭州",
        expect_fields=["found", "city"]
    )
    if ok:
        if not _last_data.get("found"):
            ok = False
            detail = "杭州 should be found"
    log_result("/api/poi/city-brief", ok, detail)


def test_multi_city():
    """F8: 联游方案"""
    ok, detail = api_get(
        "/api/multi-city?budget=4000&days=5&departure=上海&preferences=海滩,美食&travelers=couple",
        expect_fields=["routes", "input"]
    )
    log_result("/api/multi-city", ok, detail if isinstance(detail, str) else "")


def test_reviews():
    """F15: 评价查询"""
    ok, detail = api_get(
        "/api/reviews?destination=杭州&limit=2",
        expect_fields=None
    )
    # Reviews may return empty list or have different structure
    log_result("/api/reviews", ok, detail if isinstance(detail, str) else "")


def test_review_stats():
    """F16: 评价统计"""
    ok, detail = api_get(
        "/api/reviews/stats?destination=杭州",
        expect_fields=None
    )
    log_result("/api/reviews/stats", ok, detail if isinstance(detail, str) else "")


def test_flight_estimate():
    """F10: 航班价格估算"""
    ok, detail = api_get(
        "/api/flight/estimate?departure=Shanghai&destination=Sanya",
        expect_fields=["estimated_price", "price_range"]
    )
    log_result("/api/flight/estimate", ok, detail if isinstance(detail, str) else "")


def test_flight_trend():
    """F12: 价格趋势"""
    ok, detail = api_get(
        "/api/flight/trend?departure=Shanghai&destination=Sanya&days=7",
        expect_fields=["current_price", "price_range", "history"]
    )
    log_result("/api/flight/trend", ok, detail if isinstance(detail, str) else "")


def test_flight_alerts():
    """F13: 航班提醒"""
    ok, detail = api_get("/api/flight/alerts", expect_fields=["alerts"])
    log_result("/api/flight/alerts", ok, detail if isinstance(detail, str) else "")


def test_weather_warning():
    """F20: 天气预警"""
    ok, detail = api_get(
        "/api/weather/warning?lat=31.23&lon=121.47&month=7",
        expect_fields=["warnings"]
    )
    log_result("/api/weather/warning", ok, detail if isinstance(detail, str) else "")


def test_dest_image():
    """F22: 目的地图片"""
    ok, detail = api_get(
        "/api/dest-image?name=Sanya&name_cn=三亚&dest_type=Beach",
        expect_fields=["url"]
    )
    log_result("/api/dest-image", ok, detail if isinstance(detail, str) else "")


def test_geocode():
    """F27: 地理编码"""
    ok, detail = api_get("/api/geocode?address=杭州", expect_fields=["ok"])
    log_result("/api/geocode", ok, detail if isinstance(detail, str) else "")


def test_booking():
    """F25: 预订链接"""
    ok, detail = api_get(
        "/api/booking?departure=上海&destination=三亚",
        expect_fields=["platforms"]
    )
    log_result("/api/booking", ok, detail if isinstance(detail, str) else "")


def test_ctrip_checklist():
    """F26: 携程出行清单"""
    ok, detail = api_get("/api/ctrip/checklist", expect_fields=["checklist"])
    log_result("/api/ctrip/checklist", ok, detail if isinstance(detail, str) else "")


def test_feedback_stats():
    """F29: 反馈统计"""
    ok, detail = api_get("/api/feedback/stats")
    log_result("/api/feedback/stats", ok, detail if isinstance(detail, str) else "")


def test_memory_status():
    """F30: 记忆系统状态"""
    ok, detail = api_get("/api/memory", expect_fields=["short_term", "medium_term", "long_term"])
    log_result("/api/memory", ok, detail if isinstance(detail, str) else "")


def test_amap_config():
    """F28: 高德配置"""
    ok, detail = api_get("/api/amap-config", expect_fields=["key"])
    log_result("/api/amap-config", ok, detail if isinstance(detail, str) else "")


def test_frontend_html():
    """首页 HTML"""
    url = BASE_URL + "/"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            checks = [
                ("Tab 导航", 'tab-btn' in body),
                ("推荐搜索表单", 'id="searchBtn"' in body),
                ("POI 搜索", 'id="poiSearchBtn"' in body),
                ("联游 Tab", 'tab-multi' in body),
                ("侧滑抽屉", 'drawer-overlay' in body),
                ("天气预警弹窗", 'weatherModal' in body),
                ("全局工具栏", 'global-toolbar' in body),
            ]
            for name, found in checks:
                log_result(f"  HTML: {name}", found)
    except Exception as e:
        log_result(f"  HTML: /", False, str(e))


def test_static_js():
    """JS 文件可访问"""
    url = BASE_URL + "/js/app.js"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            checks = [
                ("renderResults", "function renderResults" in body),
                ("doPOISearch", "function doPOISearch" in body),
                ("goToRecommendFromPOI", "function goToRecommendFromPOI" in body),
                ("showMultiCityCard", "function showMultiCityCard" in body),
                ("renderDrawer", "function renderDrawer" in body),
                ("initTabs", "function initTabs" in body),
                ("showWeatherModal", "function showWeatherModal" in body),
                ("Tab 状态管理", "var tabStates" in body),
            ]
            for name, found in checks:
                log_result(f"  app.js: {name}", found)
    except Exception as e:
        log_result(f"  /js/app.js", False, str(e))


# ═══════════════════════════════════════════════
# 服务器管理
# ═══════════════════════════════════════════════

def check_server():
    """检查服务器是否已运行"""
    try:
        req = urllib.request.Request(BASE_URL + "/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return data.get("status") == "ok"
    except Exception:
        return False


def start_server():
    """启动服务器"""
    global SERVER_PROC
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"  Starting server from {project_dir}...")
    SERVER_PROC = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=project_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # 等待服务器启动（最多 15 秒）
    for i in range(30):
        if check_server():
            print(f"  Server started (pid={SERVER_PROC.pid})")
            return True
        time.sleep(0.5)
    print("  ❌ Server failed to start")
    return False


def stop_server():
    """停止服务器"""
    global SERVER_PROC
    if SERVER_PROC:
        print(f"  Stopping server (pid={SERVER_PROC.pid})...")
        if sys.platform == "win32":
            os.kill(SERVER_PROC.pid, signal.CTRL_C_EVENT)
            time.sleep(1)
            SERVER_PROC.terminate()
        else:
            SERVER_PROC.terminate()
        SERVER_PROC.wait(timeout=5)
        SERVER_PROC = None
        print("  Server stopped")
    # 确保端口释放
    time.sleep(1)


# ═══════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════

def main():
    global VERBOSE, QUICK

    # 解析参数
    start_server_flag = False
    for arg in sys.argv[1:]:
        if arg == "--verbose":
            VERBOSE = True
        elif arg == "--quick":
            QUICK = True
        elif arg == "--start-server":
            start_server_flag = True
        elif arg in ("-h", "--help"):
            print(__doc__)
            return

    print()
    print("=" * 54)
    print("  🧭 旅行推荐系统 · 冒烟测试")
    print("=" * 54)
    print()

    # 确保服务器运行
    if not check_server():
        if start_server_flag:
            if not start_server():
                print("  ❌ 无法启动服务器，测试终止")
                return 1
        else:
            print("  ❌ 服务器未运行！")
            print("  请先启动：python app.py")
            print("  或加 --start-server 参数自动启动")
            print()
            return 1
    else:
        print("  ✅ 服务器运行中")

    print()
    print("─" * 40)
    print("  API 端点测试")
    print("─" * 40)
    print()

    # ── P0 核心 ──
    test_health()
    test_recommend()
    test_recommend_with_chinese()
    test_poi_search()
    test_poi_search_empty()
    test_poi_city_brief()

    if not QUICK:
        test_multi_city()
        test_reviews()
        test_review_stats()
        test_flight_estimate()
        test_flight_trend()
        test_flight_alerts()
        test_weather_warning()
        test_dest_image()
        test_geocode()
        test_booking()
        test_ctrip_checklist()
        test_feedback_stats()
        test_memory_status()
        test_amap_config()

    print()
    print("─" * 40)
    print("  前端文件测试")
    print("─" * 40)
    print()

    test_frontend_html()
    if not QUICK:
        test_static_js()

    print()
    print("=" * 54)

    total = passed + failed
    if failed == 0:
        print(f"  🎉 全部通过！({passed}/{total})")
    else:
        print(f"  ⚠️  {failed}/{total} 个测试失败")
        print()
        print("  失败列表：")
        for name, ok, _ in results:
            if not ok:
                print(f"    ❌ {name}")

    print("=" * 54)
    print()

    # 清理
    if SERVER_PROC:
        stop_server()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
