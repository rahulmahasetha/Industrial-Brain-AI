import os
import json
import redis
from typing import Any, Optional

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

class CacheService:
    def __init__(self):
        self.in_memory_metrics = []
        try:
            self.client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            self.enabled = True
        except Exception as e:
            print(f"[CacheService] Could not connect to Redis: {e}")
            self.enabled = False
            
    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        try:
            val = self.client.get(key)
            if val:
                self.record_hit()
                return json.loads(val)
            self.record_miss()
            return None
        except Exception as e:
            print(f"[CacheService] Redis GET error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 600) -> bool:
        if not self.enabled:
            return False
        try:
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            print(f"[CacheService] Redis SET error: {e}")
            return False
            
    def delete_prefix(self, prefix: str):
        if not self.enabled:
            return
        try:
            keys = self.client.keys(f"{prefix}*")
            if keys:
                self.client.delete(*keys)
        except Exception as e:
            print(f"[CacheService] Redis DELETE_PREFIX error: {e}")

    def record_hit(self):
        if self.enabled:
            try:
                self.client.incr("cache_stats:hits")
            except:
                pass
                
    def record_miss(self):
        if self.enabled:
            try:
                self.client.incr("cache_stats:misses")
            except:
                pass
                
    def get_stats(self):
        if not self.enabled:
            return {"hits": 0, "misses": 0}
        try:
            hits = int(self.client.get("cache_stats:hits") or 0)
            misses = int(self.client.get("cache_stats:misses") or 0)
            return {"hits": hits, "misses": misses}
        except:
            return {"hits": 0, "misses": 0}

    def record_query_metrics(self, metrics: dict):
        if self.enabled:
            try:
                self.client.lpush("observability:query_metrics", json.dumps(metrics))
                self.client.ltrim("observability:query_metrics", 0, 99)
                return
            except:
                pass
        self.in_memory_metrics.insert(0, metrics)
        self.in_memory_metrics = self.in_memory_metrics[:100]

    def get_query_metrics(self):
        if self.enabled:
            try:
                items = self.client.lrange("observability:query_metrics", 0, -1)
                return [json.loads(item) for item in items]
            except:
                pass
        return self.in_memory_metrics

cache_service = CacheService()
