"""
cache_manager.py — 统一缓存管理
支持 TTL 过期、LRU 淘汰、自动清理
"""
import os
import time
import threading
from collections import OrderedDict

class CacheManager:
    """轻量级缓存管理器"""

    def __init__(self, name="default", max_size=500, default_ttl=600):
        self.name = name
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._times = {}  # key -> expiry timestamp
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key):
        """获取缓存值，过期则返回 None"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            if self._times.get(key, 0) < time.time():
                # 过期
                del self._cache[key]
                del self._times[key]
                self._misses += 1
                return None
            # LRU: 移到末尾
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def set(self, key, value, ttl=None):
        """设置缓存，ttl 秒后过期"""
        if ttl is None:
            ttl = self.default_ttl
        with self._lock:
            if len(self._cache) >= self.max_size and key not in self._cache:
                # LRU 淘汰：移除最久未使用的
                old_key, _ = self._cache.popitem(last=False)
                self._times.pop(old_key, None)
                self._evictions += 1
            self._cache[key] = value
            self._times[key] = time.time() + ttl
            self._cache.move_to_end(key)

    def delete(self, key):
        """删除指定缓存"""
        with self._lock:
            self._cache.pop(key, None)
            self._times.pop(key, None)

    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._times.clear()

    def save_to_file(self, filepath):
        """保存缓存到磁盘 JSON（保留数据和 TTL）"""
        import json
        with self._lock:
            now = time.time()
            data = []
            for k in list(self._cache.keys()):
                expiry = self._times.get(k, 0)
                if expiry > now:
                    data.append({
                        "key": k,
                        "value": self._cache[k],
                        "ttl_remaining": round(expiry - now, 0),
                    })
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return len(data)
        except Exception as e:
            print(f"[cache] save error: {e}")
            return 0

    def load_from_file(self, filepath):
        """从磁盘 JSON 加载缓存"""
        import json
        if not os.path.exists(filepath):
            return 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            count = 0
            now = time.time()
            for item in data:
                key = item.get("key")
                value = item.get("value")
                ttl_rem = item.get("ttl_remaining", 300)
                if key and value is not None and ttl_rem > 0:
                    self.set(key, value, ttl=ttl_rem)
                    count += 1
            print(f"[cache] loaded {count}/{len(data)} entries from {filepath}")
            return count
        except Exception as e:
            print(f"[cache] load error: {e}")
            return 0

    def cleanup(self):
        """清理所有过期条目"""
        with self._lock:
            now = time.time()
            expired = [k for k, t in self._times.items() if t < now]
            for k in expired:
                del self._cache[k]
                del self._times[k]
            return len(expired)

    def stats(self):
        """返回缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "name": self.name,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": round(hit_rate, 1),
                "default_ttl": self.default_ttl,
            }

    def __contains__(self, key):
        return self.get(key) is not None

    def __len__(self):
        return len(self._cache)


# ─── 全局缓存实例 ──

# 推荐结果缓存（短 TTL，因为 AI 文案会异步更新）
result_cache = CacheManager("results", max_size=200, default_ttl=300)

# 天气缓存（长 TTL，天气变化慢）
weather_cache = CacheManager("weather", max_size=200, default_ttl=1800)

# 高德地理编码缓存（非常长，坐标几乎不变）
geocode_cache = CacheManager("geocode", max_size=500, default_ttl=86400)


def run_periodic_cleanup(interval=300):
    """在后台线程定期清理所有缓存"""
    def _run():
        while True:
            time.sleep(interval)
            total = 0
            for cm in [result_cache, weather_cache, geocode_cache]:
                total += cm.cleanup()
            if total:
                print(f"[cache] cleaned {total} expired entries")
    t = threading.Thread(target=_run, daemon=True)
    t.start()
