#!/usr/bin/env python
"""
aggregate_poi_to_destinations.py — 从 POI 数据聚合城市级目的地

用法：
  python scripts/aggregate_poi_to_destinations.py

产出：
  1. 打印新目的地清单
  2. 可选：写入 destinations_data.py 追加代码
  3. 可选：写入 zh_names.py 更新
"""

import json, os, sys
from collections import Counter, defaultdict

# ── 路径 ──
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POI_PATH = os.path.join(ROOT, "data", "enriched_ai.json")
DEST_PATH = os.path.join(ROOT, "destinations_data.py")
ZH_PATH = os.path.join(ROOT, "zh_names.py")

# ── 现有国内目的地（去重用） ──
# ── 现有国内目的地（去重用） ──
EXISTING_CITIES = {
    "三亚", "北京", "南京", "厦门", "广州", "杭州", "武汉", "深圳",
    "珠海", "重庆", "长沙", "青岛", "成都", "西安", "香港",
    "黄山", "桂林", "张家界", "昆明", "拉萨", "大理", "丽江",
    "西双版纳", "呼伦贝尔", "喀纳斯", "张掖", "九寨沟",
    "平遥", "北海", "峨眉山", "乐山", "西塘", "乌镇",
    "贵阳", "荔波", "稻城", "顺德",
}

# ── 已知旅游城市（即使 POI 评分不突出也保留） ──
TOURIST_CITIES = {
    "苏州", "扬州", "绍兴", "洛阳", "泉州", "大连", "海口", "三亚",
    "烟台", "威海", "秦皇岛", "哈尔滨", "长春", "沈阳", "大同",
    "开封", "洛阳", "敦煌", "兰州", "南宁", "景德镇",
    "承德", "泰安", "宜昌", "襄阳", "岳阳", "湘潭", "衡阳",
    "福州", "宁波", "温州", "嘉兴", "湖州", "金华", "台州", "丽水",
    "漳州", "泉州", "南昌", "九江", "合肥", "芜湖", "济南",
    "太原", "郑州", "洛阳", "徐州", "镇江", "常州", "南通",
    "保定", "延边", "牡丹江", "丹东", "秦皇岛",
    "遵义", "恩施", "湘西", "红河", "黔东南", "迪庆",
    "汉中", "宝鸡", "上饶", "黄山",
}

# ── 明确排除的非旅游城市 ──
EXCLUDED_CITIES = {
    "东莞", "佛山", "惠州", "中山", "湛江", "汕头",
    "南充", "自贡", "泸州", "绵阳", "德阳", "宜宾", "广元",
    "徐州", "淮安", "盐城",
    "保定", "沧州", "廊坊",
    "鞍山", "抚顺", "本溪",
    "潍坊", "济宁", "临沂", "枣庄",
    "南阳", "商丘", "周口", "驻马店",
    "淮南", "淮北",
    "大庆", "齐齐哈尔",
}

# ── POI type → Destination type 映射 ──
POI_TYPE_MAP = {
    "古镇/乡村": "AncientTown",
    "自然风光": "Nature",
    "人文历史": "Culture",
    "都市休闲": "City",
    "主题乐园": "Adventure",
    "度假休闲": "Beach",  # 多数度假休闲在海滨
    "海岛/海滨": "Beach",
}

# ── Region 映射（从省份推断） ──
PROVINCE_TO_REGION = {
    "北京": "North", "天津": "North", "河北": "North", "山西": "North", "内蒙古": "North",
    "上海": "East", "江苏": "East", "浙江": "East", "安徽": "East", "福建": "East", "江西": "East", "山东": "East",
    "广东": "South", "广西": "South", "海南": "South",
    "湖北": "Central", "湖南": "Central", "河南": "Central",
    "重庆": "Southwest", "四川": "Southwest", "贵州": "Southwest", "云南": "Southwest", "西藏": "Southwest",
    "陕西": "Northwest", "甘肃": "Northwest", "青海": "Northwest", "宁夏": "Northwest", "新疆": "Northwest",
    "辽宁": "Northeast", "吉林": "Northeast", "黑龙江": "Northeast",
}

# ── 区域均价模板（基于现有国内目的地统计） ──
# (flight_low, flight_mid, flight_high, hotel_low, hotel_mid, hotel_high, food_low, food_mid, food_high)
REGION_COST_TEMPLATE = {
    "South":       (400, 600, 1000, 100, 180, 350, 60, 90, 140),
    "East":        (300, 500, 800,  120, 200, 350, 60, 100, 150),
    "North":       (300, 500, 800,  100, 180, 300, 50, 80, 130),
    "Central":     (300, 500, 800,  80,  150, 280, 50, 80, 120),
    "Southwest":   (400, 600, 1000, 80,  150, 280, 50, 80, 120),
    "Northwest":   (500, 700, 1200, 80,  130, 250, 45, 75, 110),
    "Northeast":   (400, 600, 1000, 80,  140, 250, 50, 80, 120),
}


def load_poi_data():
    with open(POI_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_dominant_type(type_counts):
    """取 POI 数量最多的类型，映射为 Destination type"""
    if not type_counts:
        return "City"
    top_type = type_counts.most_common(1)[0][0]
    return POI_TYPE_MAP.get(top_type, "City")


def generate_description(city, poi_list, top_type):
    """从 POI 描述合成城市描述"""
    # 收集前 3 个最高评分 POI 的描述片段
    top_pois = sorted(poi_list, key=lambda p: p.get("rating", 0), reverse=True)[:3]
    names = [p.get("name_cn", p.get("name", "")) for p in top_pois if p.get("rating", 0) > 0]
    desc = f"{city}，拥有"
    if names:
        desc += "、".join(names[:3]) + "等"
    desc += f"著名景点，以{top_type}为特色"
    
    # 尝试从 POI 描述中提取第一个有意义的句子
    for p in top_pois:
        d = p.get("description", "")
        if len(d) > 20:
            # 取前 40 个字
            short = d[:60]
            desc = f"{city}。{short}"
            break
    
    return desc[:120]


def main():
    print("=" * 60)
    print("  POI → 城市级目的地聚合")
    print("=" * 60)
    
    data = load_poi_data()
    dests = data["destinations"]
    print(f"\n  POI 总数: {len(dests)}")
    
    # 按城市分组
    city_groups = defaultdict(list)
    for d in dests:
        city = d.get("city", "未知").strip()
        city_groups[city].append(d)
    
    print(f"  城市数: {len(city_groups)}")
    
    # 过滤：去掉已在 EXISTING_CITIES 中的城市
    new_cities = []
    for city in sorted(city_groups.keys()):
        # 是否已存在
        is_existing = False
        for exist in EXISTING_CITIES:
            if exist in city or city in exist:
                is_existing = True
                break
        if is_existing:
            continue
        
        # 是否明确排除
        is_excluded = False
        for exc in EXCLUDED_CITIES:
            if exc in city or city in exc:
                is_excluded = True
                break
        if is_excluded:
            continue
        
        # 质量过滤
        pois = city_groups[city]
        has_ratings = [p for p in pois if p.get("rating", 0) > 0]
        avg_rating = sum(p["rating"] for p in has_ratings) / len(has_ratings) if has_ratings else 0
        
        if city in TOURIST_CITIES:
            # 已知旅游城市：宽松过滤
            if len(pois) >= 20:
                new_cities.append((city, avg_rating, len(pois)))
        else:
            # 未知城市：严格过滤
            if len(has_ratings) >= 50 and avg_rating >= 3.8:
                new_cities.append((city, avg_rating, len(pois)))
    
    # 按评分排序
    new_cities.sort(key=lambda x: -x[1])
    
    print(f"\n  新候选城市: {len(new_cities)}")
    print()
    
    # 为每个城市生成目的地
    results = []
    for i, (city, avg_rating_val, poi_count) in enumerate(new_cities):
        pois = city_groups[city]
        province = pois[0].get("province", "")
        region = PROVINCE_TO_REGION.get(province, "Central")
        
        # 统计类型
        type_counts = Counter(p.get("dest_type", "") for p in pois)
        dest_type = get_dominant_type(type_counts)
        
        # 聚合评分
        ratings = [p.get("rating", 0) for p in pois if p.get("rating", 0) > 0]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 3.5
        rating_count = len(ratings)
        
        # 聚合关键词
        all_kw = []
        for p in pois:
            all_kw.extend(p.get("keywords", []))
        top_kw = [kw for kw, _ in Counter(all_kw).most_common(8)]
        
        # 坐标（取所有 POI 的中心）
        coords_list = [(p.get("coords", {}).get("lat", 0), p.get("coords", {}).get("lng", 0))
                       for p in pois if p.get("coords")]
        if coords_list:
            avg_lat = round(sum(c[0] for c in coords_list) / len(coords_list), 4)
            avg_lng = round(sum(c[1] for c in coords_list) / len(coords_list), 4)
        else:
            avg_lat, avg_lng = 0, 0
        
        # 描述
        description = generate_description(city, pois, dest_type)
        
        # 价格（区域模板）
        cost_t = REGION_COST_TEMPLATE.get(region, REGION_COST_TEMPLATE["Central"])
        
        # 英文名（拼音转写，简化处理）
        eng_name = city
        
        # 确定 region 字段（兼容现有系统）
        dest_region = {
            "North": "North", "East": "East", "South": "South",
            "Central": "Central", "Southwest": "Southwest",
            "Northwest": "Northwest", "Northeast": "Northeast",
        }.get(region, "Central")
        
        new_id = 100 + i + 1  # 避开现有 ID（1-61）
        
        results.append({
            "id": new_id,
            "name": city,
            "country": "China",
            "region": dest_region,
            "type": dest_type,
            "lat": avg_lat,
            "lng": avg_lng,
            "desc": description,
            "keywords": top_kw,
            "cost_flight": (cost_t[0], cost_t[1], cost_t[2]),
            "cost_hotel": (cost_t[3], cost_t[4], cost_t[5]),
            "cost_food": (cost_t[6], cost_t[7], cost_t[8]),
            "ticket": 100,
            "local_transport": (30, 50, 80),
            "rating": avg_rating,
            "rating_count": rating_count,
            "poi_count": len(pois),
            "type_distribution": dict(type_counts.most_common(5)),
        })
    
    # ── 输出结果 ──
    print(f"\n  {'='*58}")
    print(f"  聚合结果：{len(results)} 个新目的地")
    print(f"  {'='*58}")
    print()
    
    # 按类型统计
    type_counter = Counter(r["type"] for r in results)
    print("  类型分布：")
    for t, c in type_counter.most_common():
        print(f"    {t:15s}: {c}")
    print()
    
    # 按省份/地区统计
    region_counter = Counter(r["region"] for r in results)
    print("  地区分布：")
    for r, c in region_counter.most_common():
        print(f"    {r:15s}: {c}")
    print()
    
    # 打印详细信息
    print(f"  {'─'*58}")
    print(f"  {'#':>3s} {'城市':12s} {'类型':12s} {'评分':6s} {'POI数':6s} {'地区':10s}")
    print(f"  {'─'*58}")
    for r in results:
        print(f"  {r['id']:3d} {r['name']:12s} {r['type']:12s} {r['rating']:4.2f}  {r['poi_count']:4d}  {r['region']:10s}")
    
    print()
    print(f"  {'='*58}")
    print(f"  总计：现有 58 + 新增 {len(results)} = {58 + len(results)} 个目的地")
    print(f"  {'='*58}")
    print()


if __name__ == "__main__":
    main()
