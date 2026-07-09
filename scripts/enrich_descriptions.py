# -*- coding: utf-8 -*-
"""
enrich_descriptions.py — 批量生成 POI 景点描述
使用 Qwen-Plus API 分批生成描述文本

策略：
  - 按 (city, dest_type) 分组，每批最多 50 个 POI
  - API 一次生成一批的所有描述（OpenAI 兼容接口）
  - 增量保存，每批完成后写回 enriched_ai.json

用法：
    python scripts/enrich_descriptions.py               # 全量生成
    python scripts/enrich_descriptions.py --dry         # 预览
    python scripts/enrich_descriptions.py --city=北京   # 仅指定城市
"""
import json, os, sys, time, hashlib, urllib.request, urllib.error
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POI_FILE = os.path.join(BASE_DIR, "data", "enriched_ai.json")
CACHE_DIR = os.path.join(BASE_DIR, ".ai_cache_descriptions")
os.makedirs(CACHE_DIR, exist_ok=True)

# ─── API 配置 ───
# DashScope (阿里通义千问) — OpenAI 兼容接口
DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
Q_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
Q_MODEL = "qwen-turbo"
# 备选：如果 qwen-plus 不行，可以试试 qwen-turbo 或 qwen-max

BATCH_SIZE = 50
SLEEP = 0.5     # 批次间隔(秒)
TIMEOUT = 120

def log(m): print(m, flush=True)

# ─── 模板描述（备选方案） ───
def _template_desc(name, city, dest_type, rating):
    templates = {
        "自然风光": f"{name}位于{city}，是一处自然风光秀丽的景点，山川壮丽、空气清新，是亲近自然、放松身心的好去处。",
        "人文历史": f"{name}位于{city}，承载着深厚的历史文化底蕴，是了解{city}历史脉络和人文风貌的绝佳去处。",
        "古镇/乡村": f"{name}位于{city}，保留了古朴的建筑风貌和浓郁的乡村气息，漫步其中仿佛穿越时光。",
        "都市休闲": f"{name}位于{city}，是集休闲、娱乐、购物于一体的城市地标，适合周末放松和家庭出游。",
        "主题乐园": f"{name}位于{city}，拥有丰富多彩的游乐设施和互动体验项目，是亲子游玩和年轻人打卡的热门去处。",
        "度假休闲": f"{name}位于{city}，环境静谧舒适，配备了完善的休闲设施，是度假放松的理想之选。",
        "海岛/海滨": f"{name}位于{city}，坐拥碧海蓝天和细腻沙滩，是海滨度假和水上活动的绝佳目的地。",
    }
    tpl = templates.get(dest_type, f"{name}位于{city}，是一处值得游览的景点，兼具观光和休闲价值。")
    if rating >= 4.5:
        tpl += " 游客好评如潮，强烈推荐！"
    return tpl

# ─── Qwen API 调用 ───
def _call_qwen(prompt):
    """调用 DashScope Qwen API（OpenAI 兼容模式）"""
    body = json.dumps({
        "model": Q_MODEL,
        "messages": [
            {"role": "system", "content": "你是旅游文案专家。根据景点信息，为每个景点生成简洁生动的中文描述（40-80字）。返回严格格式化的JSON数组：[{\"name\":\"景点名\",\"description\":\"描述\"}]。不要添加额外的说明文字。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 2048,
    }).encode()

    req = urllib.request.Request(
        Q_API_URL, data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DASHSCOPE_KEY}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())

        text = data["choices"][0]["message"]["content"].strip()
        # 清理 Markdown 代码块包装
        text = text.strip("```json").strip("```").strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 如果返回的是 Python 风格的 list 字符串
            import ast
            try:
                return ast.literal_eval(text)
            except:
                log(f"    [JSON-ERR] 解析失败，尝试重新提取 JSON")
                # 尝试从中提取 JSON 数组
                import re
                m = re.search(r'\[.*?\]', text, re.DOTALL)
                if m:
                    return json.loads(m.group())
                raise
    except Exception as e:
        raise

# ─── 系统环境检测 ───
def check_api():
    if not DASHSCOPE_KEY:
        log("[WARN] DASHSCOPE_API_KEY 未设置！仅使用模板生成")
        return False
    # 测试 API 连通性
    try:
        test_body = json.dumps({
            "model": Q_MODEL,
            "messages": [{"role": "user", "content": "回复 OK"}],
            "max_tokens": 10,
        }).encode()
        req = urllib.request.Request(
            Q_API_URL, data=test_body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {DASHSCOPE_KEY}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            log(f"[OK] Qwen API 连通性测试通过 ({Q_MODEL})")
            return True
    except Exception as e:
        log(f"[WARN] Qwen API 测试失败: {e}，将尝试使用模板")
        return False

# ─── 主处理函数 ───
def enrich():
    log("======== POI 描述批量生成器 ========")
    log(f"API: Qwen-Turbo ({Q_MODEL}) | Batch: {BATCH_SIZE}/批")

    use_ai = check_api()

    with open(POI_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    destinations = data["destinations"]
    total = len(destinations)

    # 找出需要生成的 POI
    need = [(i, d) for i, d in enumerate(destinations) if not d.get("description")]
    need_count = len(need)

    log(f"总计: {total} POI | 已有描述: {total - need_count} | 待生成: {need_count}")

    if is_dry:
        return

    # 按 (city, dest_type) 分组
    groups = defaultdict(list)
    for idx, poi in need:
        key = (poi["city"], poi["dest_type"])
        groups[key].append((idx, poi))

    log(f"分组数: {len(groups)}")

    # 如果指定了 --city，只处理该城市
    only_city = None
    for a in sys.argv:
        if a.startswith("--city="):
            only_city = a.split("=", 1)[1]
            log(f"仅处理城市: {only_city}")

    processed = 0
    updates = 0
    api_calls = 0

    for key, items in sorted(groups.items(), key=lambda x: sum(1 for _ in x[1]), reverse=True):
        city, dtype = key
        if only_city and city != only_city:
            continue

        # 分批次
        for batch_start in range(0, len(items), BATCH_SIZE):
            batch = items[batch_start:batch_start + BATCH_SIZE]

            if use_ai:
                # 构建提示词
                poi_items = "\n".join(
                    f"{j+1}. 名称: {poi['name']} | 类型: {poi['dest_type']} | 评分: {poi.get('rating', 0)} | 城市: {poi['city']}"
                    for j, (_, poi) in enumerate(batch)
                )
                prompt = (
                    f"为以下位于{city}的{len(batch)}个景点生成中文描述（每个40-80字）。\n"
                    f"要求：突出景点特色、历史或自然价值，语言生动。\n"
                    f"返回JSON数组：\n"
                    f"{poi_items}"
                )

                try:
                    results = _call_qwen(prompt)
                    desc_map = {r["name"]: r["description"] for r in results}
                    good = 0
                    for idx, poi in batch:
                        desc = desc_map.get(poi["name"], "")
                        if desc and len(desc) >= 8:
                            destinations[idx]["description"] = desc
                            good += 1
                        else:
                            destinations[idx]["description"] = _template_desc(poi["name"], city, dtype, poi.get("rating", 0))
                    updates += len(batch)
                    api_calls += 1
                    if good < len(batch):
                        log(f"  [PARTIAL] {city}/{dtype} batch{batch_start}: {good}/{len(batch)} AI描述")
                except Exception as e:
                    log(f"  [ERR] {city}/{dtype} batch{batch_start}: {e}")
                    for idx, poi in batch:
                        destinations[idx]["description"] = _template_desc(poi["name"], city, dtype, poi.get("rating", 0))
                    updates += len(batch)
            else:
                # 模板模式
                for idx, poi in batch:
                    destinations[idx]["description"] = _template_desc(poi["name"], city, dtype, poi.get("rating", 0))
                updates += len(batch)

            processed += len(batch)
            pct = processed / need_count * 100

            # 每 3 批、每 100 POI 或末尾保存一次
            if api_calls % 3 == 0 or processed >= need_count - BATCH_SIZE:
                data["meta"]["enriched"] = True
                data["meta"]["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                data["meta"]["description_source"] = "qwen-plus+template"
                with open(POI_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                log(f"  [SAVE] {processed}/{need_count} ({pct:.0f}%) | API: {api_calls}次")

            if use_ai:
                log(f"  [BATCH] {city}/{dtype}: {len(batch)} POI ({processed}/{need_count}, {pct:.0f}%)")
            time.sleep(SLEEP)

    # 最终保存
    data["meta"]["enriched"] = True
    data["meta"]["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    data["meta"]["description_source"] = "qwen-plus+template"
    with open(POI_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log(f"\n{'='*50}")
    log(f"完成！{updates}/{need_count} 条描述已生成 (API调用{api_calls}次)")
    log(f"源: {POI_FILE}")

    # 验证
    with open(POI_FILE, "r", encoding="utf-8") as f:
        final = json.load(f)
    still_empty = sum(1 for d in final["destinations"] if not d.get("description"))
    log(f"最终验证: {len(final['destinations'])} POI, {still_empty} 条空描述")

if __name__ == "__main__":
    is_dry = "--dry" in sys.argv
    enrich()
