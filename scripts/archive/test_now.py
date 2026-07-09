import requests, time

# Test both endpoints
urls = [
    ("/", "http://127.0.0.1:8000/"),
    ("/api/recommend", "http://127.0.0.1:8000/api/recommend?budget=3000&days=3&departure=Shanghai&travel_date=2026-07"),
    ("/api/meituan/preload-status", "http://127.0.0.1:8000/api/meituan/preload-status"),
]

for name, url in urls:
    try:
        t0 = time.time()
        r = requests.get(url, timeout=3)
        t = time.time() - t0
        print(f"[{name}] {r.status_code} in {t:.3f}s, len={len(r.text)}")
    except Exception as e:
        print(f"[{name}] FAILED: {type(e).__name__}")
