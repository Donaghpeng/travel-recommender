# -*- coding: utf-8 -*-
"""
review_scraper.py — Polite review scraping from Chinese travel platforms
Targets: 马蜂窝 (mafengwo.cn), 携程 (ctrip.com)
Rate-limited, cached in SQLite
"""
import urllib.request, urllib.error, json, re, time, random, os
from src.review_db import init_db, upsert_dest, save_review_summary, get_review_summary

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
]

MIN_DELAY = 2.0   # seconds between requests
MAX_DELAY = 4.0

# Destination name -> Mafengwo URL path mapping
MAFENGWO_PATHS = {
    "Sanya": "/travel-scenic-spot/mafengwo/10125.html",
    "Qingdao": "/travel-scenic-spot/mafengwo/10154.html",
    "Xiamen": "/travel-scenic-spot/mafengwo/10121.html",
    "Zhangjiajie": "/travel-scenic-spot/mafengwo/10085.html",
    "Guilin/Yangshuo": "/travel-scenic-spot/mafengwo/10122.html",
    "Xi'an": "/travel-scenic-spot/mafengwo/10105.html",
    "Beijing": "/travel-scenic-spot/mafengwo/10088.html",
    "Chengdu + Sichuan": "/travel-scenic-spot/mafengwo/10123.html",
    "Chongqing": "/travel-scenic-spot/mafengwo/10124.html",
    "Guizhou (Libo/Miao Village)": "/travel-scenic-spot/mafengwo/10389.html",
    "Changsha": "/travel-scenic-spot/mafengwo/10153.html",
    "Lhasa (Tibet)": "/travel-scenic-spot/mafengwo/10090.html",
    "Dali/Lijiang (Yunnan)": "/travel-scenic-spot/mafengwo/10119.html",
    "Water Towns (Xitang/Wuzhen)": "/travel-scenic-spot/mafengwo/10412.html",
    "Hangzhou": "/travel-scenic-spot/mafengwo/10120.html",
    "Nanjing": "/travel-scenic-spot/mafengwo/10103.html",
    "Huangshan (Yellow Mountain)": "/travel-scenic-spot/mafengwo/10118.html",
    "Jiuzhaigou": "/travel-scenic-spot/mafengwo/10084.html",
    "Chiang Mai (Thailand)": "/travel-scenic-spot/mafengwo/10512.html",
    "Bangkok (Thailand)": "/travel-scenic-spot/mafengwo/10511.html",
    "Phuket (Thailand)": "/travel-scenic-spot/mafengwo/10513.html",
    "Bali (Indonesia)": "/travel-scenic-spot/mafengwo/10520.html",
    "Osaka (Japan)": "/travel-scenic-spot/mafengwo/10530.html",
    "Kyoto (Japan)": "/travel-scenic-spot/mafengwo/10531.html",
    "Hong Kong": "/travel-scenic-spot/mafengwo/10089.html",
    "Jeju Island (South Korea)": "/travel-scenic-spot/mafengwo/10540.html",
    "Siem Reap/Angkor (Cambodia)": "/travel-scenic-spot/mafengwo/10560.html",
    "Luang Prabang (Laos)": "/travel-scenic-spot/mafengwo/10570.html",
    "Penang (Malaysia)": "/travel-scenic-spot/mafengwo/10580.html",
    "Sabah (Malaysia)": "/travel-scenic-spot/mafengwo/10581.html",
}

# Ctrip destination IDs (place to visit ID)
CTRIP_IDS = {
    "Sanya": "115",
    "Qingdao": "193",
    "Xiamen": "118",
    "Zhangjiajie": "164",
    "Guilin/Yangshuo": "117",
    "Xi'an": "138",
    "Beijing": "1",
    "Chengdu + Sichuan": "141",
    "Chongqing": "140",
    "Changsha": "165",
    "Dali/Lijiang (Yunnan)": "173",
    "Hangzhou": "39",
    "Nanjing": "37",
    "Huangshan (Yellow Mountain)": "127",
    "Hong Kong": "39",
    "Chiang Mai (Thailand)": "170",
    "Bangkok (Thailand)": "169",
}


def _fetch(url: str, timeout: int = 10) -> str:
    """Fetch with rate limiting and user agent rotation"""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"  [scraper] HTTP {e.code} for {url}")
        return ""
    except Exception as e:
        print(f"  [scraper] error: {e} for {url}")
        return ""


def parse_mafengwo_rating(html: str) -> dict:
    """Extract rating data from Mafengwo page"""
    result = {"rating": 0, "count": 0, "summary": "", "tags": []}

    # Rating number
    m = re.search(r'class="score">\s*([\d.]+)', html)
    if m:
        result["rating"] = float(m.group(1))

    # Review count
    m = re.search(r'(\d+)\s*条点评', html)
    if m:
        result["count"] = int(m.group(1))

    # Tags / highlights
    tags = re.findall(r'class="tag">([^<]+)<', html)
    result["tags"] = tags[:10]

    # Summary text
    m = re.search(r'class="summary"[^>]*>([^<]+)', html)
    if m:
        result["summary"] = m.group(1).strip()

    return result


def parse_ctrip_rating(html: str) -> dict:
    """Extract rating data from Ctrip page"""
    result = {"rating": 0, "count": 0, "summary": "", "tags": []}

    # Overall score
    m = re.search(r'综合[^\d]*([\d.]+)', html)
    if m:
        result["rating"] = float(m.group(1))

    # Review count
    m = re.search(r'(\d+)\s*条点评', html)
    if m:
        result["count"] = int(m.group(1))

    # Tags
    tags = re.findall(r'class="label"[^>]*>([^<]+)<', html)
    result["tags"] = tags[:10]

    return result


def scrape_mafengwo(dest_name: str) -> dict:
    """Scrape review summary from Mafengwo"""
    path = MAFENGWO_PATHS.get(dest_name)
    if not path:
        return None

    url = f"https://www.mafengwo.cn{path}"
    print(f"  [mafengwo] fetching {dest_name}...")
    html = _fetch(url)
    if not html:
        return None

    data = parse_mafengwo_rating(html)
    if data["rating"] == 0 and data["count"] == 0:
        return None

    data["source"] = "mafengwo"
    return data


def scrape_ctrip(dest_name: str) -> dict:
    """Scrape review summary from Ctrip"""
    cid = CTRIP_IDS.get(dest_name)
    if not cid:
        return None

    url = f"https://you.ctrip.com/sight/{cid}.html"
    print(f"  [ctrip] fetching {dest_name}...")
    html = _fetch(url)
    if not html:
        return None

    data = parse_ctrip_rating(html)
    if data["rating"] == 0 and data["count"] == 0:
        return None

    data["source"] = "ctrip"
    return data


def scrape_destination(dest_name: str):
    """Scrape all available platforms for one destination, save to DB"""
    dest_id = upsert_dest(dest_name)
    all_data = []

    # Try Mafengwo
    data = scrape_mafengwo(dest_name)
    if data:
        save_review_summary(dest_id, "mafengwo", data)
        all_data.append(data)

    # Try Ctrip
    data = scrape_ctrip(dest_name)
    if data:
        save_review_summary(dest_id, "ctrip", data)
        all_data.append(data)

    return all_data


def batch_scrape(dest_names: list[str], max_count: int = 0):
    """Scrape multiple destinations with rate limiting"""
    init_db()
    results = {"success": 0, "failed": 0, "total": len(dest_names)}

    for i, name in enumerate(dest_names):
        if max_count and i >= max_count:
            print(f"[batch] stopping at {max_count} (max_count limit)")
            break

        print(f"[{i+1}/{len(dest_names)}] {name}")
        try:
            data = scrape_destination(name)
            if data:
                results["success"] += 1
                print(f"  -> got {len(data)} sources")
            else:
                results["failed"] += 1
                print(f"  -> no data")
        except Exception as e:
            results["failed"] += 1
            print(f"  -> error: {e}")

    print(f"\nDone: {results['success']} ok, {results['failed']} failed / {results['total']}")
    return results


if __name__ == "__main__":
    from src.travel_recommender import load_destinations
    dests = load_destinations()
    names = [d.name for d in dests]
    print(f"Scraping {len(names)} destinations (rate limited)...")
    print("Running in test mode (first 5 destinations)")
    batch_scrape(names, max_count=5)
