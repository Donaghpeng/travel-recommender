"""
route_planner.py — 多城市路线规划引擎
根据输入参数，生成排序后的联游方案
支持通过 recommended_cities 与单城市推荐结果联动
"""
import random, math
from city_clusters import CLUSTERS, match_clusters


from risk_checker import assess_route_risks


def _calc_path_cost(route, edges, budget):
    """计算路线总成本"""
    total = 0
    details = []
    for i in range(len(route) - 1):
        a, b = route[i], route[i + 1]
        # 查找边
        edge = None
        for e in edges:
            if (e[0] == a and e[1] == b) or (e[0] == b and e[1] == a):
                edge = e[2]
                break
        if edge:
            total += edge["cost"]
            details.append({"from": a, "to": b, "mode": edge["mode"],
                            "time_h": edge["time_h"], "cost": edge["cost"]})
        else:
            default_cost = max(100, int(budget * 0.02))
            total += default_cost
            details.append({"from": a, "to": b, "mode": "预估", "time_h": 2, "cost": default_cost})
    total_transport = total
    return total_transport, details


def _allocate_days(num_cities, total_days):
    """给每个城市分配天数（大城市多分）"""
    if num_cities == 2:
        return [max(2, total_days - 2), max(2, total_days - 2)] if total_days >= 4 else [1, total_days - 1]
    if num_cities == 3:
        return [max(2, total_days // 3 + 1), max(1, total_days // 3), total_days - max(2, total_days // 3 + 1) - max(1, total_days // 3)]
    if num_cities == 4:
        return [2, 2, 2, total_days - 6] if total_days >= 6 else [1, 1, 1, total_days - 3]
    return [total_days // num_cities] * num_cities


def _score_route(cluster, route, budget, days, departure, preferences):
    """给路线方案打分"""
    score = 0.0

    # 1. 路线合理性 - 按推荐顺序的匹配度
    rec = cluster["recommended_order"]
    order_score = 0
    for i in range(len(route) - 1):
        a, b = route[i], route[i + 1]
        if a in rec and b in rec:
            ai, bi = rec.index(a), rec.index(b)
            order_score += 0.2 if ai < bi else 0
    score += order_score

    # 2. 出发地衔接
    if departure and departure in cluster["cities"]:
        score += 0.3

    # 3. 预算匹配
    per_day = budget / max(days, 1)
    if 300 <= per_day <= 1000:
        score += 0.2
    elif per_day >= 1500:
        score += 0.1

    # 4. 城市数量（2-3个城市最优）
    if 2 <= len(route) <= 3:
        score += 0.2

    return round(min(score, 1.5), 2)


def recommend_routes(inp: dict) -> list[dict]:
    """
    主入口：根据输入返回联游方案
    支持 inp.recommended_cities: list[str] 从单城市推荐结果联动
    """
    budget = inp.get("budget", 4000)
    days = inp.get("days", 5)
    departure = inp.get("departure", "上海")
    preferences = inp.get("preferences", [])
    recommended_cities = inp.get("recommended_cities", None)

    clusters = match_clusters(preferences, departure, budget, days,
                               recommended_cities=recommended_cities)
    results = []

    for cl in clusters[:5]:
        rec = cl["recommended_order"]
        edges = cl["edges"]
        # 根据出发地调整路线起点
        start_idx = 0
        if departure in rec:
            start_idx = rec.index(departure)
        route = rec[start_idx:]
        # 最多取4个城市
        num_cities = min(len(route), max(2, min(4, int(days * 0.6 + 0.5))))
        route = route[:num_cities]
        if len(route) < 2 and len(cl["cities"]) >= 2:
            route = cl["cities"][:3]
        if len(route) < 2:
            continue

        # 分配天数
        day_alloc = _allocate_days(len(route), days)

        # 交通成本
        trans_cost, trans_detail = _calc_path_cost(route, edges, budget)

        # 各城市预算
        per_day_budget = (budget - trans_cost) // max(sum(day_alloc), 1)
        city_budgets = [d * per_day_budget for d in day_alloc]
        total_used = sum(city_budgets) + trans_cost

        # 评分
        route_score = _score_route(cl, route, budget, days, departure, preferences)

        # 日均预算
        daily_avg = budget / max(days, 1)

        # 风险检查
        risk = assess_route_risks(route, trans_detail, day_alloc)

        results.append({
            "cluster_id": cl["id"],
            "cluster_name": cl["name"],
            "theme": cl["theme"],
            "icon": cl["icon"],
            "route": route,
            "day_allocation": day_alloc,
            "total_days": sum(day_alloc),
            "transport_cost": trans_cost,
            "transport_details": trans_detail,
            "city_budgets": city_budgets,
            "total_budget_used": total_used,
            "remaining": budget - total_used,
            "daily_avg": round(daily_avg),
            "score": route_score,
            "match_tags": [p for p in preferences if p.lower() in cl["theme"].lower()],
            "risk": risk,
        })

    # 按评分排序
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:5]
