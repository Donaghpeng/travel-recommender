"""
city_clusters.py — 多城市联游集群映射
定义可组合的城市群、交通衔接、主题标签
"""
from typing import Optional

# ─── 集群定义 ────────────────────────────────

CLUSTERS = [
    {
        "id": "east_water",
        "name": "华东水乡线",
        "theme": "水乡·园林·古都",
        "icon": "🏯",
        "cities": ["上海", "杭州", "苏州", "南京", "乌镇"],
        "transport": "高铁0.5-1.5h",
        "days_range": (3, 7),
        "keywords": ["水乡", "古镇", "园林", "文化", "city", "food"],
        "recommended_order": ["上海", "苏州", "乌镇", "杭州", "南京"],
        "edges": [
            ("上海", "苏州", {"mode": "高铁", "time_h": 0.5, "cost": 50}),
            ("苏州", "乌镇", {"mode": "大巴", "time_h": 1.5, "cost": 40}),
            ("乌镇", "杭州", {"mode": "大巴", "time_h": 1.5, "cost": 40}),
            ("杭州", "南京", {"mode": "高铁", "time_h": 1.5, "cost": 120}),
            ("上海", "杭州", {"mode": "高铁", "time_h": 1.0, "cost": 80}),
            ("南京", "上海", {"mode": "高铁", "time_h": 1.5, "cost": 150}),
        ],
    },
    {
        "id": "sichuan_food",
        "name": "川渝美食线",
        "theme": "美食·熊猫·山城",
        "icon": "🐼",
        "cities": ["成都", "重庆", "乐山"],
        "transport": "高铁1-2h",
        "days_range": (3, 6),
        "keywords": ["美食", "火锅", "熊猫", "自然", "food", "adventure"],
        "recommended_order": ["成都", "乐山", "重庆"],
        "edges": [
            ("成都", "重庆", {"mode": "高铁", "time_h": 1.5, "cost": 150}),
            ("成都", "乐山", {"mode": "高铁", "time_h": 1.0, "cost": 60}),
            ("乐山", "重庆", {"mode": "高铁", "time_h": 2.0, "cost": 200}),
        ],
    },
    {
        "id": "hainan_beach",
        "name": "海南度假线",
        "theme": "海滩·热带·度假",
        "icon": "🏖️",
        "cities": ["三亚", "海口", "万宁"],
        "transport": "环岛高铁1-2h",
        "days_range": (4, 7),
        "keywords": ["海滩", "度假", "热带", "海岛", "beach", "island"],
        "recommended_order": ["海口", "万宁", "三亚"],
        "edges": [
            ("海口", "万宁", {"mode": "高铁", "time_h": 1.0, "cost": 80}),
            ("万宁", "三亚", {"mode": "高铁", "time_h": 1.0, "cost": 60}),
            ("海口", "三亚", {"mode": "高铁", "time_h": 1.5, "cost": 120}),
        ],
    },
    {
        "id": "yunnan_scenic",
        "name": "云南风情线",
        "theme": "古镇·雪山·洱海",
        "icon": "🏔️",
        "cities": ["大理", "丽江", "昆明"],
        "transport": "高铁2-3h",
        "days_range": (5, 8),
        "keywords": ["古镇", "雪山", "自然", "摄影", "nature", "ancient"],
        "recommended_order": ["昆明", "大理", "丽江"],
        "edges": [
            ("昆明", "大理", {"mode": "高铁", "time_h": 2.0, "cost": 150}),
            ("大理", "丽江", {"mode": "高铁", "time_h": 1.5, "cost": 80}),
            ("昆明", "丽江", {"mode": "高铁", "time_h": 3.0, "cost": 200}),
        ],
    },
    {
        "id": "south_scenery",
        "name": "华南山水线",
        "theme": "山水·美食·都市",
        "icon": "🌊",
        "cities": ["桂林", "阳朔", "广州"],
        "transport": "高铁2-3h",
        "days_range": (4, 6),
        "keywords": ["山水", "美食", "城市", "nature", "food"],
        "recommended_order": ["广州", "桂林", "阳朔"],
        "edges": [
            ("广州", "桂林", {"mode": "高铁", "time_h": 2.5, "cost": 180}),
            ("桂林", "阳朔", {"mode": "大巴", "time_h": 1.0, "cost": 30}),
        ],
    },
    {
        "id": "beijing_heritage",
        "name": "北京周边线",
        "theme": "古都·皇家园林",
        "icon": "🏛️",
        "cities": ["北京", "天津", "承德"],
        "transport": "高铁0.5-2h",
        "days_range": (4, 7),
        "keywords": ["古都", "文化", "历史", "city", "culture"],
        "recommended_order": ["北京", "天津", "承德"],
        "edges": [
            ("北京", "天津", {"mode": "高铁", "time_h": 0.5, "cost": 60}),
            ("北京", "承德", {"mode": "高铁", "time_h": 2.0, "cost": 100}),
        ],
    },
]


def find_cluster_by_city(city_name: str) -> list:
    """查找包含某城市的集群"""
    results = []
    for cl in CLUSTERS:
        if city_name in cl["cities"]:
            results.append(cl)
    return results


def find_clusters_by_recommended(city_names: list[str]) -> dict:
    """
    根据推荐结果中的城市名，找出匹配的集群。
    返回 { cluster_id: matched_city_count }
    """
    matches = {}
    for name in city_names:
        name_clean = name.strip()
        for cl in CLUSTERS:
            for c in cl["cities"]:
                if c == name_clean or c in name_clean or name_clean in c:
                    matches[cl["id"]] = matches.get(cl["id"], 0) + 1
                    break
    return matches


def match_clusters(preferences: list[str], departure: str = "",
                   budget: int = 4000, days: int = 5,
                   recommended_cities: list[str] = None) -> list:
    """
    根据偏好、出发地、推荐结果匹配最佳集群。
    recommended_cities 是单城市推荐结果中的城市名列表（中文），
    用于提升包含这些城市的集群的优先级。
    """
    scored = []
    kw_set = set(k.lower() for k in preferences)
    dep_clean = departure.strip().lower()

    # 推荐城市匹配索引
    rec_matches = {}
    if recommended_cities:
        rec_matches = find_clusters_by_recommended(recommended_cities)

    for cl in CLUSTERS:
        min_d, max_d = cl["days_range"]
        if not (min_d <= days <= max_d):
            continue

        # 偏好匹配
        cluster_kws = set(k.lower() for k in cl["keywords"])
        kw_match = len(kw_set & cluster_kws)
        theme_match = sum(1 for p in preferences if p.lower() in cl["theme"].lower())

        # 出发地就近匹配
        dep_match = 0
        if dep_clean:
            for city in cl["cities"]:
                if dep_clean in city.lower() or city.lower() in dep_clean:
                    dep_match = 1
                    break

        # 推荐城市匹配（核心新增逻辑）
        rec_match = rec_matches.get(cl["id"], 0)
        # 每匹配一个推荐城市 +0.4，上限 1.0
        rec_bonus = min(rec_match * 0.4, 1.0)

        score = kw_match * 0.3 + theme_match * 0.3 + dep_match * 0.2 + rec_bonus
        scored.append((score, cl))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [cl for score, cl in scored if score > 0] or CLUSTERS[:3]
