import sys, time
sys.path.insert(0, r'C:\Users\Donaghy\Desktop\travel-recommender')

# Don't import the server (no uvicorn)
from cache_manager import result_cache
from app import _get, _startup_warm_search_cache, RESULT_CACHE_FILE

# Test _get for each city with frontend defaults
cities = ["上海", "北京", "广州", "深圳", "杭州", "成都", "武汉", "南京"]
print("Testing _get for frontend defaults...")
for dep in cities:
    inp = {
        "budget": 4000, "days": 5,
        "travel_date": "2026-07", "departure": dep,
        "preferences": ["海滩", "美食"],
        "travelers": "情侣",
        "region": "all",
    }
    k = str(sorted((str(k), str(v)) for k, v in inp.items()))
    cached = result_cache.get(k)
    if cached is not None:
        print("  {} {}s (cached)".format(dep, time.time() - t0 if 't0' in dir() else 0))
        continue
    t0 = time.time()
    try:
        result = _get(inp)
        t = time.time() - t0
        print("  {} {:.3f}s ({} results)".format(dep, t, len(result)))
    except Exception as e:
        t = time.time() - t0
        print("  {} {:.3f}s FAILED: {}".format(dep, t, str(e)[:80]))

print("Done! Cache size:", len(result_cache))
result_cache.save_to_file(RESULT_CACHE_FILE)
print("Saved to disk")
