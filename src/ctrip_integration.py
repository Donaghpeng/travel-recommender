"""
ctrip_integration.py — 携程旅行知识整合
将 ctrip skill 的参考数据转化为结构化推荐增强
"""
import os, json

REF_DIR = os.path.join(os.path.dirname(__file__), "..", "..",
                       ".openclaw", "workspace", "skills", "china-travel", "references")
# Falls back to the actual path
REF_DIR = os.path.expanduser(r"C:\Users\Donaghy\.openclaw\workspace\skills\china-travel\references")

# ─── 知识库 ────────────────────────────────

HOTEL_TYPES = {
    "商务": {"label": "商务酒店", "desc": "差旅短住，交通网络便利", "icon": "🏢"},
    "度假": {"label": "度假村/全包酒店", "desc": "家庭蜜月放松，含餐食活动", "icon": "🏖️"},
    "民宿": {"label": "民宿/公寓", "desc": "长住多人，体验当地生活", "icon": "🏡"},
    "精品": {"label": "精品/设计酒店", "desc": "追求特色体验，预算宽松", "icon": "✨"},
}

FLIGHT_TIPS = {
    "直飞": "时间紧、带老人小孩优先选直飞，省时省心",
    "转机": "预算有限可选转机，适合无直飞目的地",
    "廉航": "短途轻装可选廉航，注意行李额和餐食",
    "提前预订": "国际线提前2-3个月关注，旺季更早",
    "比价": "周二周三及错峰日期常有低价，看清含税价",
}

SIGHT_TIPS = {
    "自然": "关注天气季节，避开旺季人流",
    "文化": "留意着装要求（宗教场所），提前预约",
    "乐园": "确认开放时间和限流政策，带好预约凭证",
    "市集": "适合深度游和美食探索，半天游览即可",
}

TRAVELER_TIPS = {
    "单人": {"advice": "灵活自由，可选青旅或经济酒店", "hotel": "商务/青旅"},
    "情侣": {"advice": "推荐精品酒店或度假村，注重氛围", "hotel": "精品/度假"},
    "朋友": {"advice": "民宿或公寓性价比高，分摊费用", "hotel": "民宿"},
    "家庭": {"advice": "选儿童友好路线，含餐全包省心", "hotel": "度假/全包"},
    "带娃": {"advice": "注意景点体力要求和安全设施", "hotel": "度假/亲子"},
    "老人": {"advice": "行程宽松，住宿选无障碍设施", "hotel": "商务/度假"},
}

# ─── 核心函数 ────────────────────────────────

def get_flight_advice(departure, destination, budget, days):
    """根据行程给出机票建议"""
    advice = []
    budget_per_person = budget // max(days, 1)
    if budget_per_person < 200:
        advice.append({"tip": "关注廉航和转机", "detail": FLIGHT_TIPS["廉航"]})
        advice.append({"tip": "提前预订锁定低价", "detail": FLIGHT_TIPS["提前预订"]})
    elif budget_per_person < 500:
        advice.append({"tip": "直飞+比价", "detail": FLIGHT_TIPS["直飞"]})
        advice.append({"tip": "错峰出行更划算", "detail": FLIGHT_TIPS["比价"]})
    else:
        advice.append({"tip": "优先直飞", "detail": FLIGHT_TIPS["直飞"]})
        advice.append({"tip": "提前预订优惠多", "detail": FLIGHT_TIPS["提前预订"]})
    return advice


def get_hotel_advice(travelers, dest_type):
    """根据出行人数和目的地类型推荐酒店"""
    tip = TRAVELER_TIPS.get(travelers, TRAVELER_TIPS["单人"])
    hotel_type = tip["hotel"]
    return {
        "type": hotel_type,
        "label": HOTEL_TYPES.get(hotel_type, {}).get("label", hotel_type),
        "desc": HOTEL_TYPES.get(hotel_type, {}).get("desc", ""),
        "icon": HOTEL_TYPES.get(hotel_type, {}).get("icon", ""),
        "advice": tip["advice"],
    }


def get_sight_advice(dest_type):
    """根据目的地类型给出游玩建议"""
    key_map = {
        "Beach": "自然", "Mountain": "自然", "Nature": "自然",
        "City": "文化", "Culture": "文化", "AncientTown": "文化",
        "Island": "自然", "Food": "市集", "Adventure": "自然",
    }
    tip_key = key_map.get(dest_type, "自然")
    tip = SIGHT_TIPS.get(tip_key, SIGHT_TIPS["自然"])
    return {"category": tip_key, "advice": tip}


def get_booking_checklist():
    """出行前核对清单"""
    return [
        "确认起降机场/航站楼与时间",
        "核对姓名证件号是否一致",
        "确认行李额度与随身/托运行李规定",
        "备好预订确认单与有效证件",
        "确认酒店入住/退房时间与取消政策",
        "核对房型人数与加床费用",
        "查看交通方式与周边便利度",
        "确认景点开放时间与是否需要预约",
        "了解着装要求（宗教场所等）",
    ]


def enrich_with_ctrip(results, inp):
    """给推荐结果添加上下文旅行建议"""
    travelers = inp.get("travelers", "solo")
    days = inp.get("days", 5)
    budget = inp.get("budget", 4000)
    departure = inp.get("departure", "Shanghai")

    for res in results:
        dest_type = res.get("type", "City")
        dest_name = res.get("name_cn") or res.get("name", "")

        # 酒店建议
        res["hotel_advice"] = get_hotel_advice(travelers, dest_type)

        # 游玩建议
        res["sight_advice"] = get_sight_advice(dest_type)

        # 机票建议
        res["flight_advice"] = get_flight_advice(departure, dest_name, budget, days)

    return results


def get_checklist():
    return get_booking_checklist()
