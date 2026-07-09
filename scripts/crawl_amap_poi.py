# -*- coding: utf-8 -*-
"""
crawl_amap_poi.py — 高德地图 POI 爬虫（精简版）
每城只搜"景点"关键词 + 多页，～1 分钟/城

用法：
    python scripts/crawl_amap_poi.py                          # 全量爬
    python scripts/crawl_amap_poi.py --incremental            # 增量（续爬）
    python scripts/crawl_amap_poi.py --dry                    # 预览
    python scripts/crawl_amap_poi.py --city=北京,济南         # 指定城市
    python scripts/crawl_amap_poi.py --batch=10               # 每批爬 N 城后暂停
"""
import json, os, sys, time, hashlib, urllib.request, urllib.parse, urllib.error
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AMAP_KEY = "511195cf2c2e3524ae2ae6d236cc9a23"
RAW_DIR = os.path.join(BASE_DIR, "data", ".raw_new")
CACHE_DIR = os.path.join(BASE_DIR, ".amap_cache")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
OFFSET = 25
MAX_PAGES = 12  # 最多 12 页 = 300 POI

# 只用最精准的关键词
KEYWORDS = ["景点"]

# 目标扩展省份和城市
NEW_TARGETS = {
    "北京": ["北京"],
    "山东": ["济南", "青岛", "烟台", "威海", "潍坊", "泰安", "济宁"],
    "福建": ["福州", "厦门", "泉州", "漳州", "南平", "宁德"],
    "湖南": ["长沙", "张家界", "湘西", "衡阳", "岳阳", "湘潭"],
    "云南": ["昆明", "大理", "丽江", "迪庆", "西双版纳", "红河"],
    "安徽": ["合肥", "黄山", "池州", "安庆", "芜湖"],
    "广西": ["桂林", "南宁", "北海", "柳州", "防城港"],
    "湖北": ["武汉", "宜昌", "恩施", "十堰", "襄阳"],
    "海南": ["海口", "三亚", "万宁", "陵水"],
    "重庆": ["重庆"],
    "河南": ["郑州", "洛阳", "开封", "焦作"],
    "陕西": ["西安", "汉中", "宝鸡"],
    "江西": ["南昌", "九江", "景德镇", "上饶", "赣州"],
    "贵州": ["贵阳", "黔东南", "安顺", "黔南"],
    "河北": ["承德", "秦皇岛", "保定"],
    "山西": ["太原", "大同", "晋中", "平遥"],
    "辽宁": ["大连", "沈阳", "丹东"],
    "黑龙江": ["哈尔滨", "牡丹江"],
    "吉林": ["长春", "延边"],
    "甘肃": ["兰州", "张掖", "敦煌"],
}

EXISTING_CITIES = set()
def load_existing():
    p = os.path.join(BASE_DIR, "data", "enriched_ai.json")
    if os.path.exists(p):
        for d in json.load(open(p, "r", encoding="utf-8")).get("destinations", []):
            c = d.get("city", "")
            if c: EXISTING_CITIES.add(c)

def log(m): print(m, flush=True)

def _amap_search(city, keyword, page=1):
    """调用高德 Places Text Search API"""
    params = urllib.parse.urlencode({
        "key": AMAP_KEY, "keywords": keyword, "city": city,
        "offset": OFFSET, "page": page, "output": "JSON",
    })
    url = f"https://restapi.amap.com/v3/place/text?{params}"
    ck = hashlib.md5(url.encode()).hexdigest()
    cp = os.path.join(CACHE_DIR, f"{ck}.json")
    if os.path.exists(cp):
        try: return json.load(open(cp, "r", encoding="utf-8"))
        except: pass
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") != "1":
            log(f"  [WARN] {city}/{keyword} p{page}: {data.get('info','?')}")
            return None
        result = {"ok": True, "pois": data.get("pois", []), "total": int(data.get("count", 0))}
        json.dump(result, open(cp, "w", encoding="utf-8"), ensure_ascii=False)
        return result
    except Exception as e:
        log(f"  [SKIP] {city}/{keyword} p{page}: {e}")
        return None

def crawl_city(city, province):
    all_pois, seen = [], set()
    for kw in KEYWORDS:
        for page in range(1, MAX_PAGES + 1):
            r = _amap_search(city, kw, page)
            if r is None: break
            pois, total = r["pois"], r["total"]
            if not pois: break
            new_in_page = 0
            for p in pois:
                name = p.get("name", "").strip()
                if not name or name in seen: continue
                seen.add(name)
                ptype = p.get("type", "")
                loc = p.get("location", "").split(",")
                if len(loc) < 2: continue
                dt = _infer_dest_type(ptype, name)
                all_pois.append({
                    "name": name, "name_cn": name, "city": city,
                    "province": province, "region": _infer_region(province),
                    "dest_type": dt, "keywords": _infer_keywords(ptype, name, dt),
                    "description": "",
                    "rating": float(p.get("biz_ext", {}).get("rating", "0") or 0),
                    "address": p.get("address", ""),
                    "coords": {"lat": float(loc[1]), "lng": float(loc[0])}
                })
                new_in_page += 1
            if new_in_page == 0: break
            if len(pois) < OFFSET: break
            if page * OFFSET >= min(total, OFFSET * MAX_PAGES): break
            time.sleep(0.5)
    log(f"  [OK] {city} ({province}): {len(all_pois)} POI (unique: {len(seen)})")
    return all_pois

def _infer_dest_type(ptype, name):
    t = (ptype + " " + name).lower()
    if any(x in t for x in ["古镇","古村","古街","老街","民俗","村寨"]): return "古镇/乡村"
    if any(x in t for x in ["历史","古迹","遗址","故居","博物","纪念馆"]): return "人文历史"
    if any(x in t for x in ["海滨","海滩","沙滩","海岛","岛屿","海岸"]): return "海岛/海滨"
    if any(x in t for x in ["主题","乐园","游乐","迪士尼"]): return "主题乐园"
    if any(x in t for x in ["度假","温泉","休闲","度假区"]): return "度假休闲"
    if any(x in t for x in ["公园","自然","山","湖","森林","生态","景区","峡谷","瀑布"]): return "自然风光"
    return "都市休闲"

def _infer_keywords(ptype, name, dt):
    base = [dt]
    kw = {"古镇/乡村":["古镇","乡村","民俗","历史"],"人文历史":["历史","文化","古迹","人文"],
          "主题乐园":["主题乐园","游乐","亲子"],"度假休闲":["度假","休闲","温泉"],
          "海岛/海滨":["海岛","海滨","沙滩"],"自然风光":["自然","风光","户外","徒步"],
          "都市休闲":["都市","休闲","购物","美食"]}
    base.extend(kw.get(dt, ["休闲"]))
    return base[:5]

def _infer_region(province):
    m = {"北京":"华北","天津":"华北","河北":"华北","山西":"华北","内蒙古":"华北",
         "辽宁":"东北","吉林":"东北","黑龙江":"东北",
         "上海":"华东","江苏":"华东","浙江":"华东","安徽":"华东",
         "福建":"华东","江西":"华东","山东":"华东",
         "河南":"华中","湖北":"华中","湖南":"华中",
         "广东":"华南","广西":"华南","海南":"华南",
         "重庆":"西南","四川":"西南","贵州":"西南","云南":"西南","西藏":"西南",
         "陕西":"西北","甘肃":"西北","青海":"西北","宁夏":"西北","新疆":"西北"}
    return m.get(province, "其他")

def main():
    load_existing()

    only_cities = None
    batch_size = None
    for a in sys.argv:
        if a.startswith("--city="):
            only_cities = set(a.split("=", 1)[1].split(","))
        if a.startswith("--batch="):
            batch_size = int(a.split("=", 1)[1])
    is_dry = "--dry" in sys.argv
    incremental = "--incremental" in sys.argv

    raw_path = os.path.join(RAW_DIR, "poi_raw_new.json")

    all_raw = []
    if incremental and os.path.exists(raw_path):
        all_raw = json.load(open(raw_path, "r", encoding="utf-8"))
        log(f"[增量] 加载已有 {len(all_raw)} 条 POI")

    log("======== 高德 POI 爬虫 ========")
    log(f"Key: {AMAP_KEY[:8]}...{AMAP_KEY[-4:]}  |  已有 {len(EXISTING_CITIES)} 城")

    crawled_cities = set()
    for p in all_raw:
        c = p.get("city", "")
        if c: crawled_cities.add(c)

    if crawled_cities and incremental:
        log(f"已爬取: {sorted(crawled_cities)}")

    stats, skip_count, crawl_count = {}, 0, 0

    for province, cities in NEW_TARGETS.items():
        for city in cities:
            if only_cities and city not in only_cities:
                continue
            if city in EXISTING_CITIES:
                log(f"  [SKIP] {city} (已在 enriched_ai.json)")
                skip_count += 1
                continue
            if city in crawled_cities and incremental:
                log(f"  [SKIP] {city} (已爬取过)")
                skip_count += 1
                continue
            if is_dry:
                log(f"  [TODO] {city} ({province})")
                crawl_count += 1
                continue
            log(f"  [CRAWL] {city} ({province})...")
            t0 = time.time()
            pois = crawl_city(city, province)
            elapsed = time.time() - t0
            for p in pois:
                p["_from"] = "amap"
            all_raw.extend(pois)
            stats[province] = stats.get(province, 0) + len(pois)
            crawl_count += 1
            log(f"  [DONE] {city}: {len(pois)} POI, {elapsed:.0f}s")

            if incremental:
                json.dump(all_raw, open(raw_path, "w", encoding="utf-8"), ensure_ascii=False)
                log(f"  [SAVE] {len(all_raw)} 条 -> {raw_path}")

            # 批模式：每 N 城后暂停
            if batch_size and crawl_count % batch_size == 0:
                log(f"\n[PAUSE] 已完成 {crawl_count} 城 / 累计 {len(all_raw)} 条")
                log("[PAUSE] 重新运行 --incremental 继续爬取")
                break

            time.sleep(0.5)

        if batch_size and crawl_count % batch_size == 0 and crawl_count > 0:
            break

    if is_dry:
        log(f"\n预览: {crawl_count} 城待爬, {skip_count} 城跳过")
        return

    json.dump(all_raw, open(raw_path, "w", encoding="utf-8"), ensure_ascii=False)

    log(f"\n{'='*50}")
    log(f"爬取完成! 累计 {len(all_raw)} POI -> {raw_path}")
    log(f"新增: {crawl_count} 城")
    if stats:
        for p, n in sorted(stats.items(), key=lambda x: -x[1]):
            log(f"  {p}: {n}")
    log("\n下一步: python scripts/merge_poi_data.py 合并到 enriched_ai.json")

if __name__ == "__main__":
    main()
