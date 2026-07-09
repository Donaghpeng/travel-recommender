# -*- coding: utf-8 -*-
"""
itinerary.py — Day-by-day travel itinerary generator
For each destination, provides a curated day-by-day plan
"""
import json, random

# Each destination has: list of day templates keyed by trip length
# Format: { day_num: { "morning": str, "afternoon": str, "evening": str, "meals": [str] } }

ITINERARIES = {
    "Sanya": {
        3: [
            {"morning": "Arrive & check in at beachfront hotel", "afternoon": "Relax on Dadonghai Beach, swim in crystal clear waters", "evening": "Seafood dinner at First Market, stroll along the bay", "meals": ["Seafood hotpot", "Coconut rice", "Fresh fruit"]},
            {"morning": "Visit Yalong Bay Tropical Paradise Forest Park", "afternoon": "Snorkeling at Wuzhizhou Island (clear waters, coral reefs)", "evening": "Enjoy Hai Chang Meng Show or night market snacks", "meals": ["Wenchang chicken", "Hainan noodles", "Coconut milk"]},
            {"morning": "Tianya Haijiao (End of the Earth) scenic area", "afternoon": "Shopping at duty-free mall, visit Luhuitou Park for sunset", "evening": "Farewell dinner at a seaside restaurant", "meals": ["Hainanese chicken rice", "Seafood BBQ"]},
        ],
        5: [{"morning": "Arrive & settle in", "afternoon": "Relax at Dadonghai Beach", "evening": "Dinner at Seafood Street", "meals": ["Coconut chicken", "Seafood platter"]},
            {"morning": "Yalong Bay Tropical Paradise Forest", "afternoon": "Snorkeling at Wuzhizhou Island", "evening": "Charming Hai Chang Meng Show", "meals": ["Wenchang chicken", "Hainan noodles"]},
            {"morning": "Nanshan Temple & Guanyin Statue", "afternoon": "Tianya Haijiao scenic area", "evening": "Duty-free shopping", "meals": ["Vegetarian temple food", "Seafood congee"]},
            {"morning": "Yanoda Rainforest (zip-lining, waterfall)", "afternoon": "Afternoon tea at beach club", "evening": "Sunset sailing cruise", "meals": ["BBQ dinner", "Coconut dessert"]},
            {"morning": "Morning beach walk, checkout", "afternoon": "Last souvenir shopping at Jie Fang Road", "evening": "Depart", "meals": ["Hainan rice noodles"]},
        ],
    },
    "Qingdao": {
        3: [
            {"morning": "Visit Zhanqiao Pier & Little Qingdao Island", "afternoon": "Walk along Badaguan (Eight Passes) European architecture", "evening": "Tsingtao Beer Museum + fresh beer tasting", "meals": ["Seafood dumplings", "Tsingtao beer", "Grilled squid"]},
            {"morning": "Laoshan Mountain hike (sea + mountain views)", "afternoon": "Rest at Qingdao No.1 Bathing Beach", "evening": "Seafood street at Yunxiao Road night market", "meals": ["Steamed sea bass", "Oysters", "Sweet potato porridge"]},
            {"morning": "Visit Catholic Cathedral & Signal Hill", "afternoon": "Shopping at Zhongshan Road, afternoon tea", "evening": "Depart", "meals": ["Qingdao-style pickled seafood"]},
        ],
        5: [
            {"morning": "Arrive, check in near the coast", "afternoon": "Zhanqiao Pier & Little Qingdao Island", "evening": "Stroll along the boardwalk", "meals": ["Seafood noodles"]},
            {"morning": "Badaguan architecture walk", "afternoon": "Tsingtao Beer Museum", "evening": "Beer street on Dengzhou Road", "meals": ["Dumplings", "Beer chicken"]},
            {"morning": "Laoshan Mountain full day", "afternoon": "Taiqing Temple, mountain springs", "evening": "Seafood hotpot dinner", "meals": ["Laoshan tea", "Seafood platter"]},
            {"morning": "Qingdao Underwater World", "afternoon": "Beach relaxation at Golden Sand Beach", "evening": "Shopping at Mixc Mall", "meals": ["Grilled seafood", "Cold noodles"]},
            {"morning": "Signal Hill sunrise view", "afternoon": "Departure preparations", "evening": "Depart", "meals": ["Pork trotter rice"]},
        ],
    },
    "Beijing": {
        3: [
            {"morning": "Tiananmen Square & Forbidden City (half day)", "afternoon": "Jingshan Park for panoramic view of Forbidden City", "evening": "Wangfujing Night Market for snacks", "meals": ["Peking duck", "Zha jiang mian", "Sugar-coated hawthorn"]},
            {"morning": "Great Wall at Mutianyu (less crowded)", "afternoon": "Return to city, rest", "evening": "Nanluoguxiang hutong walk + local dinner", "meals": ["Lamb hotpot", "Beijing dumplings"]},
            {"morning": "Temple of Heaven & morning tai chi", "afternoon": "Summer Palace boat ride", "evening": "Departure", "meals": ["Peking pulled noodle", "Douzhi fermented drink"]},
        ],
        5: [
            {"morning": "Arrive, settle in", "afternoon": "Tiananmen Square", "evening": "Wangfujing night market", "meals": ["Peking duck"]},
            {"morning": "Forbidden City (full day)", "afternoon": "Forbidden City continued", "evening": "Jingshan Park sunset", "meals": ["Noodles with soybean paste"]},
            {"morning": "Great Wall at Mutianyu", "afternoon": "Return from Great Wall", "evening": "Hutong rickshaw tour", "meals": ["Lamb hotpot"]},
            {"morning": "Temple of Heaven", "afternoon": "Summer Palace", "evening": "798 Art District", "meals": ["Beijing dumplings"]},
            {"morning": "National Museum or Lama Temple", "afternoon": "Final shopping at Dashilan", "evening": "Depart", "meals": ["Fried sauce noodles"]},
        ],
    },
    "Chengdu + Sichuan": {
        3: [
            {"morning": "Giant Panda Breeding Research Base (morning is best)", "afternoon": "Visit Jinli Ancient Street, taste local snacks", "evening": "Sichuan hotpot at a famous local restaurant", "meals": ["Sichuan hotpot", "Mapo tofu", "Kung Pao chicken"]},
            {"morning": "Wuhou Shrine (Three Kingdoms history)", "afternoon": "Kuanzhai Xiangzi (Wide & Narrow Alleys) + tea house", "evening": "Sichuan opera with face-changing performance", "meals": ["Dan dan noodles", "Fuqi feipian", "Tea"]},
            {"morning": "Mount Qingcheng (Taoist mountain, short hike)", "afternoon": "Dujiangyan Irrigation System (ancient engineering)", "evening": "Depart", "meals": ["Mao xue wang", "Sichuan pickles"]},
        ],
        5: [
            {"morning": "Panda Base", "afternoon": "Jinli Ancient Street", "evening": "Hotpot dinner", "meals": ["Sichuan hotpot"]},
            {"morning": "Wuhou Shrine", "afternoon": "Kuanzhai Xiangzi + tea", "evening": "Sichuan opera show", "meals": ["Dan dan noodles", "Tea"]},
            {"morning": "Qingcheng Mountain", "afternoon": "Dujiangyan", "evening": "Return to city", "meals": ["Mountain vegetarian"]},
            {"morning": "Leshan Giant Buddha (day trip)", "afternoon": "Leshan Giant Buddha continued", "evening": "Boat cruise on Qinhuai River", "meals": ["Leshan tofu pudding"]},
            {"morning": "Sichuan Museum or People's Park", "afternoon": "Last shopping, Chengdu snacks", "evening": "Depart", "meals": ["Chuanchuan xiang"]},
        ],
    },
    "Guilin/Yangshuo": {
        3: [
            {"morning": "Li River cruise Guilin to Yangshuo (4h, stunning karst scenery)", "afternoon": "Arrive Yangshuo, rent e-bike", "evening": "West Street night market + beer fish dinner", "meals": ["Beer fish", "Guilin rice noodles", "Stuffed li river snails"]},
            {"morning": "Xianggong Mountain sunrise + Yulong River bamboo raft", "afternoon": "Cycle through十里画廊 (Ten Mile Gallery)", "evening": "Impression Liu Sanjie light show", "meals": ["Yangshuo beer duck", "Fried taro cake"]},
            {"morning": "Xingping Ancient Town (20 RMB bill view)", "afternoon": "Return to Guilin, Elephant Trunk Hill", "evening": "Depart", "meals": ["Osmanthus cake", "Rice tofu"]},
        ],
    },
    "Xi'an": {
        3: [
            {"morning": "Terracotta Warriors (half-day, ~1h from city)", "afternoon": "Return to city, lunch at Muslim Quarter", "evening": "City Wall (rent bike + sunset cycle)", "meals": ["Yangrou paomo", "Biangbiang noodles", "Persimmon cake"]},
            {"morning": "Shaanxi History Museum (reserve ahead)", "afternoon": "Great Wild Goose Pagoda & Tang Paradise", "evening": "Muslim Quarter food street dinner", "meals": ["Lamb skewers", "Cold noodles", "Osmanthus wine"]},
            {"morning": "Bell Tower + Drum Tower area", "afternoon": "Huaqing Pool or Xi'an Museum", "evening": "Depart", "meals": ["Roujiamo", "Liangpi cold noodles"]},
        ],
    },
    "Hangzhou": {
        3: [
            {"morning": "West Lake boat ride + Broken Bridge", "afternoon": "Leifeng Pagoda (view of lake)", "evening": "He Fang Street night market + local snacks", "meals": ["Dongpo pork", "West Lake vinegar fish", "Longjing shrimp"]},
            {"morning": "Lingyin Temple + Feilai Feng grottoes", "afternoon": "Longjing tea village (tea tasting + fields)", "evening": "Impression West Lake show", "meals": ["Longjing tea", "Beggar's chicken", "Song sister fish soup"]},
            {"morning": "Xixi Wetlands (boat through water villages)", "afternoon": "Shopping at Hefang Street", "evening": "Depart", "meals": ["Hangzhou-style dim sum"]},
        ],
    },
    "Guizhou (Libo/Miao Village)": {
        3: [
            {"morning": "Xijiang Qianhu Miao Village (largest Miao village)", "afternoon": "Miao embroidery workshop + silver jewelry", "evening": "Miao family dinner + bonfire dance", "meals": ["Sour soup fish", "Miao-style bacon", "Sticky rice"]},
            {"morning": "Drive to Libo (3h)", "afternoon": "Libo Seven Small Arches (emerald water)", "evening": "Libo night market", "meals": ["Sour and spicy noodles", "Grilled fish"]},
            {"morning": "Libo Da Qikong (big seven arch bridge)", "afternoon": "Return to Guiyang", "evening": "Depart", "meals": ["Huaxi beef noodles"]},
        ],
    },
    "Chiang Mai (Thailand)": {
        3: [
            {"morning": "Doi Suthep Temple (mountain temple, city view)", "afternoon": "Old City temples: Wat Phra Singh, Wat Chedi Luang", "evening": "Sunday Night Market (if Sun) or Night Bazaar", "meals": ["Khao soi", "Pad thai", "Mango sticky rice"]},
            {"morning": "Elephant Nature Park (ethical sanctuary, half-day)", "afternoon": "Thai cooking class (learn 4 dishes)", "evening": "Massage + night market dinner", "meals": ["Tom yum soup", "Green curry", "Spring rolls"]},
            {"morning": "Doi Inthanon National Park (highest peak)", "afternoon": "Return to city, souvenir shopping at Warorot Market", "evening": "Depart", "meals": ["Khao kha mu", "Thai iced tea"]},
        ],
    },
    "Bangkok (Thailand)": {
        3: [
            {"morning": "Grand Palace + Wat Pho (Reclining Buddha)", "afternoon": "Wat Arun (Temple of Dawn) across river", "evening": "Yaowarat (Chinatown) street food feast", "meals": ["Tom yum goong", "Pad see ew", "Mango sticky rice"]},
            {"morning": "Floating market (Damnoen Saduak, weekend) or Chatuchak Market", "afternoon": "Jim Thompson House (Thai silk museum)", "evening": "Rooftop bar at sunset + Thai dinner", "meals": ["Green papaya salad", "Massaman curry", "Thai iced tea"]},
            {"morning": "Asiatique riverside market/boutique shopping", "afternoon": "ICONSIAM luxury mall + indoor floating market", "evening": "Depart", "meals": ["Boat noodles", "Coconut ice cream"]},
        ],
    },
}

# Default itineraries for destinations without specific data
DEFAULT_DAYS = {
    3: [
        {"morning": "Explore the city center and main attractions", "afternoon": "Visit local markets and try regional cuisine", "evening": "Enjoy the local nightlife or night market", "meals": ["Local specialty cuisine", "Street food", "Regional dessert"]},
        {"morning": "Nature/outdoor excursion in surrounding area", "afternoon": "Cultural site or museum visit", "evening": "Fine dining at a renowned local restaurant", "meals": ["Authentic local dish", "Seafood/farm fresh", "Local craft beer or tea"]},
        {"morning": "Scenic viewpoint or morning hike", "afternoon": "Last-minute shopping and depart", "evening": "Depart", "meals": ["Breakfast specialty", "Farewell meal"]},
    ],
    5: [
        {"morning": "Arrive & acclimate", "afternoon": "Explore city center", "evening": "Welcome dinner", "meals": ["Local cuisine", "Street food"]},
        {"morning": "Main attraction #1", "afternoon": "Cultural site", "evening": "Night market", "meals": ["Regional specialty", "Dessert"]},
        {"morning": "Nature day trip", "afternoon": "Lunch at scenic spot", "evening": "Local performance", "meals": ["Picnic lunch", "Traditional dinner"]},
        {"morning": "Museum or historical site", "afternoon": "Shopping district", "evening": "Rooftop dinner", "meals": ["International cuisine", "Local wine/beer"]},
        {"morning": "Morning walk, photos", "afternoon": "Depart", "evening": "", "meals": ["Breakfast", "Snacks for road"]},
    ],
}


def generate_itinerary(dest_name: str, days: int) -> dict:
    """Generate day-by-day itinerary for a destination"""
    # Find the best matching itinerary
    dest_key = _find_key(dest_name, ITINERARIES)

    if not dest_key:
        return _generate_default(dest_name, days)

    # Find the best matching day plan
    plans = ITINERARIES[dest_key]
    plan_days = sorted([k for k in plans.keys() if k <= days], reverse=True)
    target_days = plan_days[0] if plan_days else 3

    days_data = plans[target_days]
    itinerary_days = []

    for i in range(min(days, len(days_data))):
        day = days_data[i]
        itinerary_days.append({
            "day": i + 1,
            "title": f"Day {i+1}: {_day_title(day)}",
            "morning": day["morning"],
            "afternoon": day["afternoon"],
            "evening": day["evening"],
            "meals": day.get("meals", []),
        })

    # Pad remaining days with default
    for i in range(len(days_data), days):
        itinerary_days.append({
            "day": i + 1,
            "title": f"Day {i+1}: Free exploration",
            "morning": "Free time to explore",
            "afternoon": "Continue exploring or relax",
            "evening": "Enjoy local dining",
            "meals": ["Local food", "Street snacks"],
        })

    return {
        "destination": dest_name,
        "total_days": days,
        "days": itinerary_days,
        "source": "curated" if dest_key else "template",
    }


def _day_title(day_data: dict) -> str:
    """Generate a short title from morning activity"""
    m = day_data["morning"]
    if len(m) > 30:
        m = m[:30]
    return m


def _find_key(name: str, data: dict) -> str:
    """Find best matching key in data dict"""
    if name in data:
        return name
    for key in data:
        if key.lower() in name.lower() or name.lower() in key.lower():
            return key
        # Check word matches
        name_words = set(name.lower().split())
        key_words = set(key.lower().split())
        if name_words & key_words:
            return key
    return None


def _generate_default(dest_name: str, days: int) -> dict:
    """Generate a generic itinerary for unknown destinations"""
    plan = DEFAULT_DAYS.get(3, DEFAULT_DAYS[3])
    itinerary_days = []

    for i in range(min(days, 3)):
        day = plan[i]
        itinerary_days.append({
            "day": i + 1,
            "title": f"Day {i+1}: Exploring {dest_name}",
            "morning": day["morning"],
            "afternoon": day["afternoon"],
            "evening": day["evening"],
            "meals": day.get("meals", []),
        })

    for i in range(3, days):
        itinerary_days.append({
            "day": i + 1,
            "title": f"Day {i+1}: Free day",
            "morning": "Free exploration",
            "afternoon": "Local discoveries",
            "evening": "Evening relaxation",
            "meals": ["Local cuisine"],
        })

    return {
        "destination": dest_name,
        "total_days": days,
        "days": itinerary_days,
        "source": "template",
    }


def add_itinerary_to_results(results: list, days: int) -> list:
    """Add itinerary data to recommendation results"""
    for r in results:
        days_val = days or r.get("days", 5)
        itinerary = generate_itinerary(r["name"], days_val)
        r["itinerary"] = itinerary
    return results


if __name__ == "__main__":
    # Test
    for name in ["Sanya", "Beijing", "Guilin/Yangshuo", "UnknownPlace"]:
        it = generate_itinerary(name, 3)
        print(f"\n{name} (3 days):")
        for d in it["days"]:
            print(f"  Day {d['day']}: {d['morning'][:40]}... -> {d['evening'][:30]}...")
