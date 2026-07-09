#!/usr/bin/env python
"""
apply_new_destinations.py — 将 POI 聚合的新目的地直接写入系统文件

用法：
  python scripts/apply_new_destinations.py
"""

import json, os, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POI_PATH = os.path.join(ROOT, "data", "enriched_ai.json")

# ── Same filtering logic ──
EXISTING_CITIES = {"三亚","北京","南京","厦门","广州","杭州","武汉","深圳",
    "珠海","重庆","长沙","青岛","成都","西安","香港","黄山","桂林","张家界",
    "昆明","拉萨","大理","丽江","西双版纳","呼伦贝尔","喀纳斯","张掖","九寨沟",
    "平遥","北海","峨眉山","乐山","西塘","乌镇","贵阳","荔波","稻城","顺德"}
TOURIST_CITIES = {"苏州","扬州","绍兴","洛阳","泉州","大连","海口","烟台","威海",
    "秦皇岛","哈尔滨","长春","沈阳","大同","开封","敦煌","兰州","南宁","景德镇",
    "承德","泰安","宜昌","襄阳","岳阳","福州","宁波","温州","嘉兴","湖州","金华",
    "台州","丽水","漳州","南昌","九江","合肥","芜湖","济南","太原","郑州","徐州",
    "镇江","常州","南通","延边","牡丹江","丹东","恩施","湘西","红河","黔东南","迪庆",
    "汉中","宝鸡","上饶","保定"}
EXCLUDED_CITIES = {"东莞","佛山","惠州","中山","湛江","汕头","南充","自贡","泸州",
    "绵阳","德阳","宜宾","广元","淮安","盐城","沧州","廊坊","鞍山","抚顺","本溪",
    "潍坊","济宁","临沂","枣庄","南阳","商丘","周口","驻马店","淮南","淮北","大庆","齐齐哈尔"}
POI_TYPE_MAP = {"古镇/乡村":"AncientTown","自然风光":"Nature","人文历史":"Culture",
    "都市休闲":"City","主题乐园":"Adventure","度假休闲":"Beach","海岛/海滨":"Beach"}
PROVINCE_TO_REGION = {"北京":"North","天津":"North","河北":"North","山西":"North","内蒙古":"North",
    "上海":"East","江苏":"East","浙江":"East","安徽":"East","福建":"East","江西":"East","山东":"East",
    "广东":"South","广西":"South","海南":"South","湖北":"Central","湖南":"Central","河南":"Central",
    "重庆":"Southwest","四川":"Southwest","贵州":"Southwest","云南":"Southwest","西藏":"Southwest",
    "陕西":"Northwest","甘肃":"Northwest","青海":"Northwest","宁夏":"Northwest","新疆":"Northwest",
    "辽宁":"Northeast","吉林":"Northeast","黑龙江":"Northeast"}
COST_TMPL = {"South":(400,600,1000,100,180,350,60,90,140),"East":(300,500,800,120,200,350,60,100,150),
    "North":(300,500,800,100,180,300,50,80,130),"Central":(300,500,800,80,150,280,50,80,120),
    "Southwest":(400,600,1000,80,150,280,50,80,120),"Northwest":(500,700,1200,80,130,250,45,75,110),
    "Northeast":(400,600,1000,80,140,250,50,80,120)}

def gen_desc(city, pois):
    top = sorted(pois, key=lambda p: p.get("rating",0), reverse=True)[:3]
    for p in top:
        d = p.get("description","")
        if len(d) > 20: return d[:80].rstrip("，。") + "。"
    return f"{city}，值得一去的旅游目的地。"

with open(POI_PATH,"r",encoding="utf-8") as f:
    data = json.load(f)
dests = data["destinations"]

city_groups = defaultdict(list)
for d in dests:
    city = d.get("city","未知").strip()
    city_groups[city].append(d)

candidates = []
for city in sorted(city_groups.keys()):
    if any(e in city or city in e for e in EXISTING_CITIES): continue
    if any(e in city or city in e for e in EXCLUDED_CITIES): continue
    pois = city_groups[city]
    has_r = [p for p in pois if p.get("rating",0) > 0]
    avg_r = sum(p["rating"] for p in has_r)/len(has_r) if has_r else 0
    if city in TOURIST_CITIES:
        if len(pois)>=20: candidates.append((city,avg_r,len(pois)))
    else:
        if len(has_r)>=50 and avg_r>=3.8: candidates.append((city,avg_r,len(pois)))
candidates.sort(key=lambda x:-x[1])

# Build new destination strings
new_dest_lines = []
new_zh_lines = []
for i,(city,_,_) in enumerate(candidates):
    new_id = 62+i
    pois = city_groups[city]
    province = pois[0].get("province","")
    region = PROVINCE_TO_REGION.get(province,"Central")
    tc = Counter(p.get("dest_type","") for p in pois)
    dt = POI_TYPE_MAP.get(tc.most_common(1)[0][0],"City")
    ratings = [p.get("rating",0) for p in pois if p.get("rating",0) > 0]
    avg_r = round(sum(ratings)/len(ratings),2) if ratings else 3.5
    r_cnt = len(ratings)
    all_kw = []
    for p in pois: all_kw.extend(p.get("keywords",[]))
    top_kw = [kw for kw,_ in Counter(all_kw).most_common(6)]
    coords = [(p.get("coords",{}).get("lat",0),p.get("coords",{}).get("lng",0))
              for p in pois if p.get("coords")]
    avg_lat = round(sum(c[0] for c in coords)/len(coords),4) if coords else 0
    avg_lng = round(sum(c[1] for c in coords)/len(coords),4) if coords else 0
    desc = gen_desc(city,pois)
    ct = COST_TMPL.get(region,COST_TMPL["Central"])
    kw_s = ", ".join(f'"{k}"' for k in top_kw)
    new_dest_lines.append(
        f'        Destination({new_id}, "{city}", "China", "{region}", "{dt}",\n'
        f'            {avg_lat}, {avg_lng}, "{desc}",\n'
        f'            [{kw_s}],\n'
        f'            cost_flight=({ct[0]}, {ct[1]}, {ct[2]}), cost_hotel_per_night=({ct[3]}, {ct[4]}, {ct[5]}),\n'
        f'            cost_food_per_day=({ct[6]}, {ct[7]}, {ct[8]}), cost_ticket=100, cost_local_transport=(30, 50, 80),\n'
        f'            rating_overall={avg_r}, rating_count={r_cnt}),'
    )
    new_zh_lines.append(f'    "{city}": "{city}",')

# ── Write to destinations_data.py ──
dest_path = os.path.join(ROOT, "destinations_data.py")
with open(dest_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the last ] and insert before it
last_bracket = content.rfind("]")
if last_bracket == -1:
    print("ERROR: Could not find closing bracket in destinations_data.py")
    sys.exit(1)

new_section = "\n        # ════════════════════════════════════════════\n"
new_section += "        # 🏙️ NEW: POI-aggregated domestic cities (68)\n"
new_section += "        # ════════════════════════════════════════════\n"
for line in new_dest_lines:
    new_section += line + "\n"

new_content = content[:last_bracket] + new_section + content[last_bracket:]
with open(dest_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print(f"✅ Added {len(new_dest_lines)} destinations to {dest_path}")

# ── Write to zh_names.py ──
zh_path = os.path.join(ROOT, "zh_names.py")
with open(zh_path, "r", encoding="utf-8") as f:
    content = f.read()

last_brace = content.rfind("}")
if last_brace == -1:
    print("ERROR: Could not find closing brace in zh_names.py")
    sys.exit(1)

new_zh_section = "\n" + "\n".join(new_zh_lines) + "\n"
new_content = content[:last_brace] + new_zh_section + content[last_brace:]
with open(zh_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print(f"✅ Added {len(new_zh_lines)} names to {zh_path}")

print(f"\n🎉 Total: 58 original + {len(new_dest_lines)} new = {58+len(new_dest_lines)} destinations")
