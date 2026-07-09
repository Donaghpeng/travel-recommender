# -*- coding: utf-8 -*-
"""
merge_poi_data.py — 合并新爬取的原始 POI 到 enriched_ai.json

用法：
    python scripts/merge_poi_data.py                                # 合并 data/.raw_new/poi_raw_new.json
    python scripts/merge_poi_data.py --source path/to/raw.json      # 指定源文件
    python scripts/merge_poi_data.py --output data/enriched_new.json # 输出到新文件
"""
import json, os, sys, time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POI_FILE = os.path.join(BASE_DIR, "data", "enriched_ai.json")
RAW_DIR = os.path.join(BASE_DIR, "data", ".raw_new")
DEFAULT_SOURCE = os.path.join(RAW_DIR, "poi_raw_new.json")

def log(m): print(m, flush=True)

def load_poi(path):
    """加载 POI 数据，返回 (meta dict, destinations list)"""
    try:
        d = json.load(open(path, "r", encoding="utf-8"))
    except Exception as e:
        log(f"  [ERR] 加载 {path} 失败: {e}")
        return None, []
    if isinstance(d, list):
        return {"total": len(d), "generated_at": str(time.strftime("%Y-%m-%d %H:%M:%S"))}, d
    meta = d.get("meta", {"total": len(d.get("destinations", []))})
    return meta, d.get("destinations", [])

def dedup_key(dest):
    """去重键：城市 + 名称"""
    city = dest.get("city", "").strip()
    name = dest.get("name", "").strip()
    return (city, name)

def main():
    # 参数解析
    src_path = DEFAULT_SOURCE
    out_path = POI_FILE
    background = False

    for a in sys.argv:
        if a.startswith("--source="):
            src_path = a.split("=", 1)[1]
        elif a.startswith("--output="):
            out_path = a.split("=", 1)[1]
        elif a == "--background":
            background = True
        elif a == "--dry":
            background = True

    # 加载新数据
    if not os.path.exists(src_path):
        log(f"源文件不存在: {src_path}")
        log("请先运行 python scripts/crawl_amap_poi.py --incremental")
        return
    new_meta, new_dests = load_poi(src_path)
    new_total = len(new_dests)
    log(f"新数据: {new_total} 条 POI")

    # 加载现有数据
    existing_meta, existing_dests = load_poi(POI_FILE)
    existing_total = len(existing_dests)
    log(f"现有数据: {existing_total} 条 POI")

    # 建立去重索引
    existing_keys = set()
    for d in existing_dests:
        existing_keys.add(dedup_key(d))

    # 过滤新数据，只保留不重复的
    added = 0
    skipped = 0
    merged_dests = list(existing_dests)

    for nd in new_dests:
        k = dedup_key(nd)
        if k in existing_keys:
            # 已存在：如果现有记录描述为空但有新描述，则补充
            existing_idx = None
            for i, ed in enumerate(existing_dests):
                if dedup_key(ed) == k:
                    existing_idx = i
                    break
            if existing_idx is not None:
                ed = existing_dests[existing_idx]
                nd_desc = nd.get("description", "").strip()
                ed_desc = ed.get("description", "").strip()
                # 如果新数据有描述但旧的没有，更新
                if nd_desc and not ed_desc:
                    ed["description"] = nd_desc
                    log(f"  [UPDATE] {k[0]} / {k[1]}: 补充描述")
            skipped += 1
            continue

        # 新记录，补充元字段
        nd["_from"] = nd.get("_from", "amap_new")
        merged_dests.append(nd)
        added += 1

    # 更新 meta
    merged_meta = {
        "total": len(merged_dests),
        "provinces": sorted(set(d.get("province", "") for d in merged_dests if d.get("province"))),
        "city_count": len(set(d.get("city", "") for d in merged_dests if d.get("city"))),
        "type_stats": {},
        "province_stats": {},
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    for d in merged_dests:
        dt = d.get("dest_type", "其他")
        merged_meta["type_stats"][dt] = merged_meta["type_stats"].get(dt, 0) + 1
        p = d.get("province", "其他")
        merged_meta["province_stats"][p] = merged_meta["province_stats"].get(p, 0) + 1

    # 保留原 meta 中的 enrichment 信息
    for k in ["enriched", "description_source", "description_generated_at"]:
        if k in existing_meta:
            merged_meta[k] = existing_meta[k]

    output = {"meta": merged_meta, "destinations": merged_dests}

    if background:
        log(f"\n{'='*50}")
        log(f"摘要 (--background 模式，仅输出)")
        log(f"  现有: {existing_total}")
        log(f"  新增: {added}")
        log(f"  跳过(已存在): {skipped}")
        log(f"  合并后: {len(merged_dests)}")
        return

    # 写入
    json.dump(output, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    log(f"\n{'='*50}")
    log(f"合并完成!")
    log(f"  现有: {existing_total}")
    log(f"  新增: {added}")
    log(f"  跳过(已存在): {skipped}")
    log(f"  合并后: {len(merged_dests)}")
    log(f"  输出: {out_path}")
    log(f"\n省份统计:")
    for p, n in sorted(merged_meta["province_stats"].items(), key=lambda x: -x[1]):
        log(f"  {p}: {n}")
    log(f"\n类型统计:")
    for t, n in sorted(merged_meta["type_stats"].items(), key=lambda x: -x[1]):
        log(f"  {t}: {n}")

if __name__ == "__main__":
    main()
