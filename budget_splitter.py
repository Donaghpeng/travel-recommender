"""
budget_splitter.py — 跨城市预算分配
为联游方案生成各城市详细的费用拆解
"""
from route_planner import _allocate_days


def split_budget(budget: int, days: int, route: list[str],
                 transport_cost: int = 0) -> dict:
    """为多城市路线生成详细的预算拆解"""
    num = len(route)
    day_alloc = _allocate_days(num, days)
    remaining_for_cities = budget - transport_cost
    total_days = sum(day_alloc)

    cities = []
    for i, city in enumerate(route):
        city_days = day_alloc[i]
        if total_days > 0:
            city_share = int(remaining_for_cities * (city_days / total_days))
        else:
            city_share = remaining_for_cities // num

        # 费用拆解
        hotel = int(city_share * 0.40)
        food = int(city_share * 0.25)
        local = int(city_share * 0.15)
        ticket = int(city_share * 0.10)
        reserve = city_share - hotel - food - local - ticket

        cities.append({
            "name": city,
            "days": city_days,
            "total": city_share,
            "breakdown": {
                "hotel": hotel,
                "food": food,
                "local_transport": local,
                "ticket": ticket,
                "reserve": reserve,
            },
        })

    total_used = sum(c["total"] for c in cities) + transport_cost

    return {
        "route": route,
        "total_budget": budget,
        "total_days": sum(day_alloc),
        "transport_cost": transport_cost,
        "cities": cities,
        "total_used": total_used,
        "remaining": budget - total_used,
        "daily_avg": round(budget / max(sum(day_alloc), 1)),
    }
