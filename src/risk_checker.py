"""
risk_checker.py v2 — 联游方案交通风险评估（重写）

核心逻辑：
1. 每段交通评估：出发时间 09:00 → 到达时间 = 09:00 + duration
2. 转乘评级基于合理铁路/公路衔接，而非错误地使用"转机算法"
3. 深夜到达检查：到达 > 21:00 时检查地铁/打车
4. 给出具体可操作的建议
"""
import math


# ────────────────────────────────────────────
# 城市地铁末班车时间（近似值）
# ────────────────────────────────────────────
_METRO_LAST = {
    "北京": "23:00", "上海": "22:30", "广州": "23:00", "深圳": "23:00",
    "成都": "22:30", "杭州": "22:30", "南京": "22:00", "重庆": "22:30",
    "武汉": "22:30", "西安": "23:00", "长沙": "23:00", "苏州": "22:00",
    "天津": "22:30", "郑州": "22:30", "昆明": "22:00", "青岛": "22:00",
    "大连": "22:00", "厦门": "22:30", "宁波": "22:00", "合肥": "22:00",
    "三亚": "21:00", "海口": "21:30", "桂林": "21:00", "阳朔": "21:00",
    "万宁": "20:30", "乌镇": "21:00", "乐山": "21:00",
    "default": "22:00",
}

# 城市类型（影响到达时间和交通建议）
_CITY_TYPE = {
    "上海": "big", "北京": "big", "广州": "big", "深圳": "big",
    "成都": "big", "重庆": "big", "西安": "big", "武汉": "big",
    "杭州": "big", "南京": "big", "长沙": "big", "天津": "big",
    "青岛": "big", "郑州": "big", "昆明": "big", "大连": "big",
    "default": "small",
}

# 交通方式的合理性和建议
_TRANSPORT_TIPS = {
    "高铁": {"comfort": "high", "punctual": True, "suggest": "准时舒适，推荐首选"},
    "动车": {"comfort": "high", "punctual": True, "suggest": "舒适快捷，推荐首选"},
    "大巴": {"comfort": "low", "punctual": False, "suggest": "受路况影响，建议预留缓冲时间"},
    "公交": {"comfort": "low", "punctual": False, "suggest": "绕路较多，不推荐长途"},
    "地铁": {"comfort": "mid", "punctual": True, "suggest": "稳定准时，适合短途"},
    "出租车": {"comfort": "mid", "punctual": False, "suggest": "直达便捷，费用较高"},
    "网约车": {"comfort": "mid", "punctual": False, "suggest": "随叫随到，费用较高"},
    "轮船": {"comfort": "mid", "punctual": True, "suggest": "慢节奏体验，适合不赶时间的游客"},
    "飞机": {"comfort": "mid", "punctual": False, "suggest": "适合远距离，需算上机场往返时间"},
    "预估": {"comfort": "mid", "punctual": False, "suggest": "常规出行，建议提前查时间"},
}


def _str_to_min(s: str) -> int:
    """'HH:MM' → 分钟数"""
    try:
        h, m = [int(x) for x in s.split(":")]
        return h * 60 + m
    except Exception:
        return 9 * 60  # default 09:00


def _min_to_str(m: int) -> str:
    """分钟数 → 'HH:MM'"""
    m = max(0, m)
    return f"{m // 60:02d}:{m % 60:02d}"


def assess_segment(transport_mode: str, time_h: float, from_city: str,
                   to_city: str, days_at_to_city: int) -> dict:
    """
    评估一段城市间交通的合理性

    假设出发时间 09:00，计算到达时间
    根据到达时间和目的地类型给出评级和建议
    """
    minutes = int(time_h * 60)
    dep_time = 9 * 60  # 09:00 出发
    arr_time = dep_time + minutes
    city_type = _CITY_TYPE.get(to_city, _CITY_TYPE["default"])

    # 基础数据
    tip = _TRANSPORT_TIPS.get(transport_mode, {"comfort": "mid", "punctual": False, "suggest": ""})
    arr_str = _min_to_str(arr_time)

    # ── 时长合理性判断 ──
    if transport_mode in ("高铁", "动车"):
        if minutes > 300:
            dur_issue = "远距离"
            dur_label = "偏长"
            dur_color = "warning"
        elif minutes > 180:
            dur_issue = "中长途"
            dur_label = "适中"
            dur_color = "caution"
        else:
            dur_issue = "短途"
            dur_label = "轻松"
            dur_color = "safe"
    elif transport_mode == "飞机":
        minutes_effective = minutes + 120  # 算上机场往返+安检
        arr_effective = dep_time + minutes_effective
        if minutes_effective > 360:
            dur_issue = "耗时较长"
            dur_label = "偏长"
            dur_color = "warning"
        else:
            dur_issue = "远距离飞行"
            dur_label = "适中"
            dur_color = "caution"
        minutes = minutes_effective
        arr_time = arr_effective
        arr_str = _min_to_str(arr_time)
    else:
        if minutes > 240:
            dur_issue = "耗时较长"
            dur_label = "偏长"
            dur_color = "warning"
        elif minutes > 120:
            dur_issue = "中距离"
            dur_label = "适中"
            dur_color = "caution"
        else:
            dur_issue = "短距离"
            dur_label = "轻松"
            dur_color = "safe"

    # 天数充足性
    if days_at_to_city >= 2:
        day_ok = True
        day_note = f"{days_at_to_city}天充裕"
    else:
        day_ok = True if minutes < 120 else False
        day_note = f"仅{days_at_to_city}天，路途耗时{minutes}分钟" if minutes >= 120 else f"{days_at_to_city}天还可以"

    # ── 深夜到达判断 ──
    last_str = _METRO_LAST.get(to_city, _METRO_LAST["default"])
    last_min = _str_to_min(last_str)

    if arr_time >= 22 * 60:
        late_level = "danger"
        late_label = "深夜"
        late_icon = ""
        late_advice = f"预计{arr_str}到达，地铁已停运（末班{last_str}），建议预约接站/网约车"
    elif arr_time >= 21 * 60:
        late_level = "warning"
        late_label = "偏晚"
        late_icon = ""
        late_advice = f"预计{arr_str}到达，地铁{last_str}末班，注意抓紧时间"
    elif arr_time >= 18 * 60:
        late_level = "caution"
        late_label = "下午到"
        late_icon = ""
        late_advice = f"预计{arr_str}到达，下午可安排半天活动"
    else:
        late_level = "safe"
        late_label = "上午到"
        late_icon = ""
        late_advice = f"预计{arr_str}到达，全天可自由安排"

    # ── 综合评级 ──
    levels = {"safe": 0, "caution": 1, "warning": 2, "danger": 3}
    if late_level == "danger":
        overall = "danger"
    elif late_level == "warning":
        overall = "warning"
    elif dur_color == "warning":
        overall = "warning"
    elif late_level == "caution" or dur_color == "caution":
        overall = "caution"
    else:
        overall = "safe"

    icons = {"danger": "", "warning": "", "caution": "", "safe": ""}
    labels = {"danger": "注意", "warning": "留意", "caution": "还行", "safe": "顺利"}

    # 生成建议文案
    advice_parts = []
    if overall == "danger":
        advice_parts.append(late_advice)
        advice_parts.append("建议调整出发时间或选择早班车次")
    elif overall == "warning":
        if late_level == "warning":
            advice_parts.append(f"到达偏晚，建议提前查好酒店位置")
        else:
            advice_parts.append(f"路途较长，建议提前备好干粮和水")
    elif overall == "caution":
        if late_level == "caution":
            advice_parts.append(f"到达时间还可以，下午可安排逛吃")
        else:
            advice_parts.append(f"距离适中，半路可以休息一下")

    if not day_ok:
        advice_parts.append(f"在{to_city}只住{days_at_to_city}晚，建议提前规划景点")
    elif days_at_to_city >= 2:
        advice_parts.append(f"在{to_city}有{days_at_to_city}天，行程从容")

    return {
        "from": from_city,
        "to": to_city,
        "mode": transport_mode,
        "duration": minutes,
        "duration_display": f"{minutes}分钟" if minutes < 60 else f"{minutes//60}h{minutes%60}分钟",
        "departure": "09:00",
        "arrival": arr_str,
        "level": overall,
        "icon": icons[overall],
        "label": labels[overall],
        "arrival_level": late_level,
        "arrival_label": late_label,
        "day_note": day_note,
        "transport_tip": tip["suggest"],
        "advice": "；".join(advice_parts) if advice_parts else "出行顺利",
        "comfort": tip["comfort"],
    }


def check_last_mile(city: str, arrival_time: str, day_count: int) -> dict | None:
    """
    检查联游方案最后一天的深夜到达情况
    只在到达 >= 21:00 时返回结果
    """
    try:
        h, m = [int(x) for x in arrival_time.split(":")]
        arr_min = h * 60 + m
    except Exception:
        return None

    city_type = _CITY_TYPE.get(city, _CITY_TYPE["default"])
    last_str = _METRO_LAST.get(city, _METRO_LAST["default"])
    last_min = _str_to_min(last_str)

    if arr_min < 21 * 60:
        return None  # 白天到不需要检查

    if arr_min <= last_min:
        level, icon, label = "caution", "", "偏晚"
        adv = f"{arrival_time}到{city}，地铁{last_str}末班，抓紧进站"
        suggest = f"出站后步行/打车至酒店，最后一班地铁前到站"
    elif arr_min <= last_min + 60:
        level, icon, label = "warning", "", "较晚"
        adv = f"{arrival_time}到{city}，地铁已停运（末班{last_str}），建议预约网约车"
        suggest = f"预约网约车/平台顺风车，预计¥20-60"
    else:
        level, icon, label = "danger", "", "深夜"
        adv = f"{arrival_time}深夜到{city}，建议提前订酒店接站或预约专车"
        suggest = f"提前在美团/滴滴预约接站；如需住宿可预订车站附近酒店"

    return {
        "city": city,
        "arrival_time": arrival_time,
        "level": level,
        "icon": icon,
        "label": label,
        "metro_last": last_str,
        "advice": adv,
        "suggest": suggest,
        "day_count": day_count,
    }


# ────────────────────────────────────────────
# 主入口：为联游路由计算完整风险
# ────────────────────────────────────────────

def assess_route_risks(route, transport_details, day_allocation):
    """
    对一条联游路线进行完整的交通风险评估

    参数:
        route: ["上海", "苏州", "乌镇"]
        transport_details: [{"from":"上海","to":"苏州","mode":"高铁","time_h":0.5,...}, ...]
        day_allocation: [2, 1, 2]

    返回:
        {segments: [...], last_mile: ..., summary: "...", ...}
    """
    # 路段评估
    segments = []
    for td in transport_details:
        from_city = td.get("from", "?")
        to_city = td.get("to", "?")
        mode = td.get("mode", "预估")
        time_h = td.get("time_h", 1)
        # 找到目标城市停留天数
        to_idx = route.index(to_city) if to_city in route else -1
        days_at_to = day_allocation[to_idx] if to_idx >= 0 else 1
        seg = assess_segment(mode, time_h, from_city, to_city, days_at_to)
        segments.append(seg)

    # ── 最后的深夜到达检查：基于最后一段交通的实际到达时间 ──
    last_mile = None
    if len(route) > 0:
        last_city = route[-1]
        last_days = day_allocation[-1] if len(day_allocation) >= len(route) else 1

        if last_days == 1:
            # 最后一天中途到达，活动到傍晚
            est_arrive = "16:00"
            ctype = _CITY_TYPE.get(last_city, _CITY_TYPE["default"])
            if ctype == "big":
                est_arrive = "18:00"
        else:
            # 多天：最后一天退房(12:00) + 半天活动
            # 如果是大城市会活动到晚上才离开
            ctype = _CITY_TYPE.get(last_city, _CITY_TYPE["default"])
            if ctype == "big":
                est_arrive = "21:00"
            elif ctype == "small":
                est_arrive = "16:00"
            else:
                est_arrive = "18:00"

        # 如果最后一段是当天到达，用实际到达时间替换估算
        if len(segments) > 0:
            last_seg = segments[-1]
            last_seg_arrival = last_seg.get("arrival", "")
            if last_seg_arrival:
                try:
                    arr_h = int(last_seg_arrival.split(":")[0])
                    # 实际到达时间晚于估算则用实际
                    if arr_h >= int(est_arrive.split(":")[0]):
                        est_arrive = last_seg_arrival
                except Exception:
                    pass

        last_mile = check_last_mile(last_city, est_arrive, last_days)

    # 综合评级
    levels = {"safe": 0, "caution": 1, "warning": 2, "danger": 3}
    max_level = "safe"
    for s in segments:
        if levels.get(s["level"], 0) > levels.get(max_level, 0):
            max_level = s["level"]
    if last_mile and levels.get(last_mile["level"], 0) > levels.get(max_level, 0):
        max_level = last_mile["level"]

    # 综合文案
    summaries = {
        "safe": "行程安排合理，时间充裕，放心出行",
        "caution": "个别路段注意时间，整体还行",
        "warning": "部分路段耗时较长或到达偏晚，建议留意",
        "danger": "有深夜到达或超长途路段，建议调整行程",
    }

    return {
        "segments": segments,
        "last_mile": last_mile,
        "overall": max_level,
        "overall_label": {"safe": "良好", "caution": "还行", "warning": "留意", "danger": "注意"}.get(max_level, ""),
        "overall_icon": {"safe": "", "caution": "", "warning": "", "danger": ""}.get(max_level, ""),
        "summary": summaries.get(max_level, ""),
    }
