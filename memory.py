"""
memory.py — 三层记忆系统
短期记忆（会话缓存） + 中期记忆（用户偏好） + 长期记忆（向量检索）
"""
import time, json, re, math
from collections import Counter
from threading import Lock

# ══════════════════════════════════════════════
# Layer 1: 短期记忆 — 会话缓存
# ══════════════════════════════════════════════

class ShortTermMemory:
    """保留最近 N 轮对话，TTL=5min"""
    def __init__(self, max_rounds=10, ttl=300):
        self.max_rounds = max_rounds
        self.ttl = ttl
        self._rounds = []
        self._lock = Lock()

    def add(self, query, results_preview=""):
        with self._lock:
            self._cleanup()
            self._rounds.append((time.time(), query, str(results_preview)[:200]))
            if len(self._rounds) > self.max_rounds:
                self._rounds.pop(0)

    def get_recent(self, n=3):
        with self._lock:
            self._cleanup()
            return [{"query": q, "results": r[:60]} for _, q, r in self._rounds[-n:]]

    def find_similar(self, query, threshold=0.3):
        with self._lock:
            self._cleanup()
            for ts, q, r in reversed(self._rounds):
                sim = self._jaccard(query, q)
                if sim >= threshold:
                    return {"query": q, "results": r[:60], "similarity": round(sim, 2)}
        return None

    def _cleanup(self):
        now = time.time()
        self._rounds = [(ts, q, r) for ts, q, r in self._rounds if now - ts < self.ttl]

    def _jaccard(self, a, b):
        sa, sb = set(a.lower().split()), set(b.lower().split())
        if not sa or not sb:
            return 0
        return len(sa & sb) / len(sa | sb)

    @property
    def size(self):
        return len(self._rounds)


# ══════════════════════════════════════════════
# Layer 2: 中期记忆 — 用户偏好
# ══════════════════════════════════════════════

class MediumTermMemory:
    """用户偏好缓存，TTL=1h"""
    DEFAULTS = {
        "budget": 4000, "days": 5, "departure": "\u4e0a\u6d77",
        "preferences": [], "travelers": "\u60c5\u4fa3", "region": "all",
        "last_searched": [], "preferred_types": [],
    }

    def __init__(self, ttl=3600):
        self.ttl = ttl
        self._data = dict(self.DEFAULTS)
        self._updated = time.time()
        self._lock = Lock()

    def update(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                if k in self._data:
                    if k == "preferences" and isinstance(v, list):
                        self._data["preferences"] = list(set(self._data["preferences"] + v))[:5]
                    elif k == "preferred_types" and isinstance(v, str):
                        self._data["preferred_types"] = (self._data.get("preferred_types", []) + [v])[-20:]
                    else:
                        self._data[k] = v
                if k == "last_searched" and isinstance(v, str):
                    searched = self._data.get("last_searched", [])
                    searched = ([v] + searched)[:10]
                    self._data["last_searched"] = searched
            self._updated = time.time()

    def get(self, key=None):
        with self._lock:
            self._check_expiry()
            if key:
                return self._data.get(key, self.DEFAULTS.get(key))
            return dict(self._data)

    def get_preferred_type(self):
        types = self._data.get("preferred_types", [])
        if not types:
            return None
        return Counter(types).most_common(1)[0][0]

    def _check_expiry(self):
        if time.time() - self._updated > self.ttl:
            self._data = dict(self.DEFAULTS)

    def suggest(self, current_input):
        suggestion = {}
        self._check_expiry()
        for k, default in self.DEFAULTS.items():
            if k not in current_input or not current_input.get(k):
                val = self._data.get(k)
                if val is not None and val != default:
                    suggestion[k] = val
        return suggestion


# ══════════════════════════════════════════════
# Layer 3: 长期记忆 — 向量检索 (RAG)
# ══════════════════════════════════════════════

_CHAR_STOP = set("\u7684\u4e86\u662f\u5728\u6709\u548c\u4e0e\u6211\u4eba\u8fd9\u90a3\u4e3a\u5230\u5bf9\u8981\u90fd\u53bb\u4e5f\u5f88")


def _extract_features(text):
    """提取文本特征词（双字词 + 单字过滤）"""
    text = text.lower()
    words = set()
    for i in range(len(text) - 1):
        bg = text[i:i+2]
        if all('\u4e00' <= c <= '\u9fff' for c in bg):
            if bg not in _CHAR_STOP:
                words.add(bg)
    for c in text:
        if '\u4e00' <= c <= '\u9fff' and c not in _CHAR_STOP:
            words.add(c)
    return words


class LongTermMemory:
    """基于特征词的目的地向量检索"""

    def __init__(self):
        self._index = []  # [{name, name_cn, type, features, name_en}, ...]
        self._ready = False
        self._lock = Lock()

    def build_index(self, destinations):
        """从目的地列表构建索引"""
        with self._lock:
            self._index = []
            for d in destinations:
                name = d.get("name")
                text_parts = [
                    d.get("name_cn", d.get("name", "")),
                    d.get("description", ""),
                    " ".join(d.get("keywords", [])),
                    d.get("type", ""),
                ]
                text = " ".join(text_parts)
                features = _extract_features(text)
                if features:
                    self._index.append({
                        "name": d.get("name_cn", name),
                        "name_en": name,
                        "type": d.get("type", ""),
                        "features": features,
                        "keywords": d.get("keywords", []),
                    })
            self._ready = True

    def search(self, query, top_k=5):
        """语义搜索（Jaccard + 关键词加分）"""
        if not self._ready:
            return []
        q_feat = _extract_features(query)
        if not q_feat:
            return []

        scores = []
        q_lower = query.lower()
        for d in self._index:
            df = d["features"]
            inter = len(q_feat & df)
            union = len(q_feat | df)
            sim = inter / union if union > 0 else 0
            kw_bonus = sum(0.1 for kw in d.get("keywords", []) if kw in q_lower)
            scores.append({
                "name": d["name"],
                "name_en": d["name_en"],
                "type": d["type"],
                "similarity": round(sim + kw_bonus, 3),
            })

        scores.sort(key=lambda x: x["similarity"], reverse=True)
        return scores[:top_k]

    def search_by_type(self, dest_type, top_k=10):
        if not self._ready:
            return []
        results = [d for d in self._index if d["type"].lower() == dest_type.lower()]
        return results[:top_k]


# ══════════════════════════════════════════════
# 全局实例
# ══════════════════════════════════════════════

short_term = ShortTermMemory()
medium_term = MediumTermMemory()
long_term = LongTermMemory()
