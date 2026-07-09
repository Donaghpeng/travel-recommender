#!/usr/bin/env python
"""
generate_destination_code.py — 从 POI 聚合数据生成代码并插入到系统文件

用法：
  python scripts/generate_destination_code.py
"""

import json, os, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POI_PATH = os.path.join(ROOT, "data", "enriched_ai.json")

# ── Same filtering as aggregate_poi_to_destinations.py ──
EXISTING_CITIES = {
    "三亚", "北京", "南京", "厦门", "广州", "杭州", "武汉", "深圳",
    "珠海", "重庆", "长沙", "青岛", "成都", "西安", "香港",
    "黄山", "桂林", "张家界", "昆明", "拉萨", "大理", "丽江",
    "西双版纳", "呼伦贝尔", "喀纳斯", "张掖", "九寨沟",
    "平遥", "北海", "峨眉山", "乐山", "西塘", "乌镇",
    "贵阳", "荔波", "稻城", "顺德",
}

TOURIST_CITIES = {
    "苏州", "扬州", "绍兴", "洛阳", "泉州", "大连", "海口",
    "烟台", "威海", "秦皇岛", "哈尔滨", "长春", "沈阳", "大同",
    "开封", "敦煌", "兰州", "南宁", "景德镇",
    "承德", "泰安", "宜昌", "襄阳", "岳阳",
    "福州", "宁波", "温州", "嘉兴", "湖州", "金华", "台州", "丽水",
    "漳州", "南昌", "九江", "合肥", "芜湖", "济南",
    "太原", "郑州", "徐州", "镇江", "常州", "南通",
    "延边", "牡丹江", "丹东",
    "恩施", "湘西", "红河", "黔东南", "迪庆",
    "汉中", "宝鸡", "上饶",
}

EXCLUDED_CITIES = {
    "东莞", "佛山", "惠州", "中山", "湛江", "汕头",
    "南充", "自贡", "泸州", "绵阳", "德阳", "宜宾", "广元",
    "淮安", "盐城", "沧州", "廊坊",
    "鞍山", "抚顺", "本溪",
    "潍坊", "济宁", "临沂", "枣庄",
    "南阳", "商丘", "周口", "驻马店",
    "淮南", "淮北", "大庆", "齐齐哈尔",
}

POI_TYPE_MAP = {
    "古镇/乡村": "AncientTown",
    "自然风光": "Nature",
    "人文历史": "Culture",
    "都市休闲": "City",
    "主题乐园": "Adventure",
    "度假休闲": "Beach",
    "海岛/海滨": "Beach",
}

PROVINCE_TO_REGION = {
    "北京": "North", "天津": "North", "河北": "North", "山西": "North", "内蒙古": "North",
    "上海": "East", "江苏": "East", "浙江": "East", "安徽": "East", "福建": "East", "江西": "East", "山东": "East",
    "广东": "South", "广西": "South", "海南": "South",
    "湖北": "Central", "湖南": "Central", "河南": "Central",
    "重庆": "Southwest", "四川": "Southwest", "贵州": "Southwest", "云南": "Southwest", "西藏": "Southwest",
    "陕西": "Northwest", "甘肃": "Northwest", "青海": "Northwest", "宁夏": "Northwest", "新疆": "Northwest",
    "辽宁": "Northeast", "吉林": "Northeast", "黑龙江": "Northeast",
}

REGION_COST_TEMPLATE = {
    "South":       (400, 600, 1000, 100, 180, 350, 60, 90, 140),
    "East":        (300, 500, 800,  120, 200, 350, 60, 100, 150),
    "North":       (300, 500, 800,  100, 180, 300, 50, 80, 130),
    "Central":     (300, 500, 800,  80,  150, 280, 50, 80, 120),
    "Southwest":   (400, 600, 1000, 80,  150, 280, 50, 80, 120),
    "Northwest":   (500, 700, 1200, 80,  130, 250, 45, 75, 110),
    "Northeast":   (400, 600, 1000, 80,  140, 250, 50, 80, 120),
}


def gen_desc(city, pois):
    top = sorted(pois, key=lambda p: p.get("rating", 0), reverse=True)[:3]
    for p in top:
        d = p.get("description", "")
        if len(d) > 20:
            return d[:80].rstrip("，。") + "。"
    return f"{city}，值得一去的旅游目的地。"


def main():
    with open(POI_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    dests = data["destinations"]

    city_groups = defaultdict(list)
    for d in dests:
        city = d.get("city", "未知").strip()
        city_groups[city].append(d)

    # Filter
    candidates = []
    for city in sorted(city_groups.keys()):
        if any(e in city or city in e for e in EXISTING_CITIES):
            continue
        if any(e in city or city in e for e in EXCLUDED_CITIES):
            continue
        pois = city_groups[city]
        has_ratings = [p for p in pois if p.get("rating", 0) > 0]
        avg_r = sum(p["rating"] for p in has_ratings) / len(has_ratings) if has_ratings else 0
        if city in TOURIST_CITIES:
            if len(pois) >= 20:
                candidates.append((city, avg_r, len(pois)))
        else:
            if len(has_ratings) >= 50 and avg_r >= 3.8:
                candidates.append((city, avg_r, len(pois)))
    candidates.sort(key=lambda x: -x[1])

    # Generate entries
    dest_code_lines = []
    zh_lines = []
    
    for i, (city, _, _) in enumerate(candidates):
        new_id = 62 + i
        pois = city_groups[city]
        province = pois[0].get("province", "")
        region = PROVINCE_TO_REGION.get(province, "Central")
        type_counts = Counter(p.get("dest_type", "") for p in pois)
        top_type = type_counts.most_common(1)[0][0]
        dest_type = POI_TYPE_MAP.get(top_type, "City")
        
        ratings = [p.get("rating", 0) for p in pois if p.get("rating", 0) > 0]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 3.5
        rating_count = len(ratings)
        
        all_kw = []
        for p in pois:
            all_kw.extend(p.get("keywords", []))
        top_kw = [kw for kw, _ in Counter(all_kw).most_common(8)]
        
        coords_list = [(p.get("coords", {}).get("lat", 0), p.get("coords", {}).get("lng", 0))
                       for p in pois if p.get("coords")]
        if coords_list:
            avg_lat = round(sum(c[0] for c in coords_list) / len(coords_list), 4)
            avg_lng = round(sum(c[1] for c in coords_list) / len(coords_list), 4)
        else:
            avg_lat, avg_lng = 0, 0
        
        desc = gen_desc(city, pois)
        cost_t = REGION_COST_TEMPLATE.get(region, REGION_COST_TEMPLATE["Central"])
        
        kw_str = ", ".join(f'"{k}"' for k in top_kw[:6])
        
        dest_code_lines.append(
            f'        Destination({new_id}, "{city}", "China", "{region}", "{dest_type}",\n'
            f'            {avg_lat}, {avg_lng}, "{desc}",\n'
            f'            [{kw_str}],\n'
            f'            cost_flight=({cost_t[0]}, {cost_t[1]}, {cost_t[2]}), '
            f'cost_hotel_per_night=({cost_t[3]}, {cost_t[4]}, {cost_t[5]}),\n'
            f'            cost_food_per_day=({cost_t[6]}, {cost_t[7]}, {cost_t[8]}), '
            f'cost_ticket=100, cost_local_transport=(30, 50, 80),\n'
            f'            rating_overall={avg_rating}, rating_count={rating_count}),'
        )
        zh_lines.append(f'    "{city}": "{city}",')

    print("=" * 60)
    print("  以下代码请添加到 destinations_data.py 的 load_all() 中")
    print("  (在最后一个 Destination 条目后面，] 之前)")
    print("=" * 60)
    print()
    for line in dest_code_lines:
        print(line)
    print()
    print("=" * 60)
    print("  以下代码请添加到 zh_names.py 的 CN_NAMES 中")
    print("  (在最后一个条目后面，} 之前)")
    print("=" * 60)
    print()
    for line in zh_lines:
        print(line)
    print()
    print(f"  共 {len(dest_code_lines)} 个新目的地，ID: 62 ~ {61+len(dest_code_lines)}")


if __name__ == "__main__":
    main()
