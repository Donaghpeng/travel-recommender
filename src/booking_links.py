"""
booking_links.py — 预订跳转链接生成工具
接入去哪儿/携程/飞猪搜索链接
"""
import urllib.parse

# ─── 平台定义 ──────────────────────────────

PLATFORMS = {
    "qunar": {
        "name": "去哪儿",
        "color": "#00a65a",
        "flight": "https://flight.qunar.com/site/oneway_list.htm?searchDepartureAirport={departure}&searchArrivalAirport={destination}&searchDepartureTime={date}",
        "hotel": "https://hotel.qunar.com/city/{destination}/",
    },
    "ctrip": {
        "name": "携程",
        "color": "#287dfa",
        "hotel": "https://hotels.ctrip.com/hotel/{destination}",
        "flight": "https://flights.ctrip.com/itinerary/oneway/{departure}-{destination}?date={date}",
    },
    "fliggy": {
        "name": "飞猪",
        "color": "#ff6a00",
        "flight": "https://www.fliggy.com/search/{destination}?from={departure}&date={date}",
    },
}


def _encode(text):
    """URL encode Chinese text"""
    return urllib.parse.quote(text.strip())


def _clean_name(name):
    """Clean destination name for URL - return short form"""
    # English: "Water Towns (Xitang/Wuzhen)" -> "Water Towns"
    # Chinese: "水乡（西塘/乌镇）" -> "水乡"
    # "Chengdu + Sichuan" -> "成都"
    # "Guilin/Yangshuo" -> "桂林"
    import re
    # Handle both ASCII '(' and full-width '（'
    for sep in ["(", "（"]:
        if sep in name:
            name = name.split(sep)[0].strip()
    # Handle '/' and '+'
    for sep in ["/", "+", "＋", "／"]:
        if sep in name:
            name = name.split(sep)[0].strip()
    return name.strip()


def generate_links(departure, destination, travel_date=None):
    """Generate booking links for all platforms.

    Returns:
        list of dict: [{"name": "去哪儿", "color": "#...", "links": [...]}, ...]
    """
    dest_clean = _clean_name(destination)
    dep_clean = _clean_name(departure)

    # Use travel_date or default to next month
    date = travel_date if travel_date else "2026-07-01"
    if len(date) == 7:  # "2026-07" format
        date += "-01"

    results = []
    for key, platform in PLATFORMS.items():
        links = []
        for link_type in ["flight", "hotel"]:
            if link_type in platform:
                url = platform[link_type]
                # Apply translations for Ctrip airport codes
                dest_url = dest_clean
                dep_url = dep_clean

                url = url.replace("{departure}", _encode(dep_url))
                url = url.replace("{destination}", _encode(dest_url))
                url = url.replace("{date}", _encode(date))
                links.append({"type": link_type, "label": "机票" if link_type == "flight" else "酒店", "url": url})

        if links:
            results.append({"name": platform["name"], "color": platform["color"], "links": links})

    return results
