# -*- coding: utf-8 -*-
"""
ai_writer.py — DeepSeek-powered recommendation description generator
Generates personalized travel recommendation blurbs using AI
"""
import json, urllib.request, urllib.error, os, time

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".ai_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

CACHE_TTL = 86400 * 7  # 7 days

if not API_KEY:
    import warnings
    print("  [ai_writer] \u8b66\u544a: DEEPSEEK_API_KEY \u73af\u5883\u53d8\u91cf\u672a\u8bbe\u7f6e\uff0cAI \u6587\u6848\u5c06\u4f7f\u7528\u6a21\u677f")
    API_KEY = "__missing__"


def _cache_key(dest_name: str, budget: int, days: int, prefs: list) -> str:
    import hashlib
    raw = f"{dest_name}|{budget}|{days}|{','.join(sorted(prefs))}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _cache_get(key: str) -> str:
    path = os.path.join(CACHE_DIR, f"{key}.txt")
    if os.path.exists(path) and (time.time() - os.path.getmtime(path)) < CACHE_TTL:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def _cache_set(key: str, text: str):
    path = os.path.join(CACHE_DIR, f"{key}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def generate_blurb(dest_name: str, desc: str, budget: int, days: int,
                    estimate: int, prefs: list, scores: dict) -> str:
    """
    Generate a short personalized recommendation blurb using DeepSeek.
    Falls back to template if API fails.
    """
    key = _cache_key(dest_name, budget, days, prefs)
    cached = _cache_get(key)
    if cached:
        return cached

    # Build prompt
    pref_str = ", ".join(prefs) if prefs else "travel"
    prompt = (
        f"You are a travel advisor. Write a short recommendation blurb for {dest_name}. "
        f"Description: {desc}. "
        f"Budget: RMB {budget} for {days} days. "
        f"Estimated cost: RMB {estimate}. "
        f"Traveler preferences: {pref_str}. "
        f"Cost score: {scores['cost']}/5, Weather score: {scores['weather']}/5, "
        f"Review score: {scores['review']}/5. "
        f"Write 2-3 sentences in Chinese. Be specific and convincing. "
        f"Mention why it fits the budget and preferences."
    )

    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 200,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        text = data["choices"][0]["message"]["content"].strip()
        # Remove quotes if the model wraps it
        text = text.strip('"').strip("'").strip()
        _cache_set(key, text)
        return text
    except Exception as e:
        print(f"  [ai_writer] API error for {dest_name}: {e}")
        return _template_blurb(dest_name, estimate, budget, scores)


def _template_blurb(dest_name: str, estimate: int, budget: int, scores: dict) -> str:
    """Fallback template when API is unavailable"""
    over = estimate <= budget
    money = f"在预算内" if over else f"略超预算RMB{estimate - budget}"
    highlights = []
    if scores["cost"] >= 4:
        highlights.append("性价比高")
    if scores["weather"] >= 4:
        highlights.append("天气舒适")
    if scores["review"] >= 4.5:
        highlights.append("口碑极佳")
    if scores["preference"] >= 4:
        highlights.append("匹配偏好")
    highlight = "、".join(highlights) if highlights else "综合表现不错"
    return f"推荐{dest_name}！{money}，{highlight}。适合安排{budget}元预算的行程。"


def batch_generate(results: list, budget: int, days: int, prefs: list) -> list:
    """Generate blurbs for all results in batch"""
    for r in results:
        blurb = generate_blurb(
            r["name"], r["description"], budget, days,
            r["estimate"], prefs, r["scores"],
        )
        r["ai_blurb"] = blurb
        print(f"  [{r['name']:30s}] blurb generated ({len(blurb)} chars)")
    return results


# ─── Test ──────────────────────────────────────────────────

if __name__ == "__main__":
    from travel_recommender import TravelRecommender

    rec = TravelRecommender()
    results = rec.recommend({
        "budget": 4000, "days": 5, "travel_date": "2026-07",
        "departure": "Shanghai", "preferences": ["beach", "food"],
        "travelers": "couple", "region": "all",
    })

    # Add estimate if not present
    for r in results:
        r.setdefault("estimate", 3000)
        r.setdefault("scores", {"cost": 3.5, "weather": 4.0, "review": 4.0, "preference": 3.5, "route": 3.5})

    print("Generating AI blurbs...")
    enriched = batch_generate(results, 4000, 5, ["beach", "food"])
    print("\nResults with AI blurbs:")
    for r in enriched:
        print(f'\n  {r["name"]}:')
        print(f'    {r.get("ai_blurb", "(none)")}')
