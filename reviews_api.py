"""
reviews_api.py — 评价数据读写与统计
"""
import json, os
from models import Review, ReviewStats

DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DIR, "reviews_db.json")

# 内存缓存
_cache = {"reviews": [], "loaded": False}


def _load() -> list[Review]:
    """从 JSON 加载评价到内存"""
    if _cache["loaded"]:
        return _cache["reviews"]
    if not os.path.exists(DB_PATH):
        _cache["reviews"] = []
        _cache["loaded"] = True
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    _cache["reviews"] = [Review.from_dict(d) for d in data]
    _cache["loaded"] = True
    return _cache["reviews"]


def _save():
    """将内存评价写回 JSON"""
    data = [r.to_dict() for r in _cache["reviews"]]
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_reviews(destination: str, page: int = 1, limit: int = 5,
                sort: str = "newest", traveler_type: str = "") -> dict:
    """获取目的地评价列表"""
    reviews = _load()
    # 筛选
    filtered = [r for r in reviews if r.destination == destination]
    if traveler_type:
        filtered = [r for r in filtered if r.traveler_type == traveler_type]

    # 排序
    if sort == "newest":
        filtered.sort(key=lambda r: r.date, reverse=True)
    elif sort == "highest":
        filtered.sort(key=lambda r: r.rating, reverse=True)
    elif sort == "lowest":
        filtered.sort(key=lambda r: r.rating)

    total = len(filtered)
    start = (page - 1) * limit
    page_data = filtered[start:start + limit]

    return {
        "reviews": [r.to_dict() for r in page_data],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": max(1, (total + limit - 1) // limit),
    }


def get_review_stats(destination: str) -> ReviewStats:
    """获取目的地的评分统计"""
    reviews = _load()
    filtered = [r for r in reviews if r.destination == destination]
    if not filtered:
        return ReviewStats(destination=destination)

    total = len(filtered)
    avg = round(sum(r.rating for r in filtered) / total, 1)

    dist = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
    tag_counter = {}
    for r in filtered:
        star = str(int(r.rating))
        dist[star] = dist.get(star, 0) + 1
        for t in r.tags:
            tag_counter[t] = tag_counter.get(t, 0) + 1

    # 分布转百分比
    dist_pct = {k: round(v / total, 2) for k, v in dist.items()}

    # Top 10 标签
    top_tags = sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)[:10]
    keyword_tags = [{"tag": t, "count": c} for t, c in top_tags]

    return ReviewStats(
        destination=destination,
        avg_rating=avg,
        total_count=total,
        distribution=dist_pct,
        keyword_tags=keyword_tags,
    )


def add_review(review_data: dict) -> Review:
    """添加新评价"""
    reviews = _load()
    # 生成 ID
    ids = [int(r.id.split("_")[1]) for r in reviews if r.id.startswith("rev_")]
    next_id = max(ids) + 1 if ids else 1
    review_data["id"] = f"rev_{next_id:03d}"
    review = Review.from_dict(review_data)
    reviews.append(review)
    _cache["reviews"] = reviews
    _save()
    return review


def get_top_reviews(destination: str, limit: int = 3) -> list[dict]:
    """获取某目的地评分最高的前N条评价"""
    reviews = _load()
    filtered = [r for r in reviews if r.destination == destination]
    filtered.sort(key=lambda r: r.rating, reverse=True)
    return [r.to_dict() for r in filtered[:limit]]
