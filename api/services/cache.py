import time
from datetime import datetime, timezone

class RiskCache:
    def __init__(self):
        self._store = {}

    def set(self, key: str, value, ttl_seconds: int = 1800):
        expires_at = time.time() + ttl_seconds
        set_at = time.time()
        self._store[key] = {
            "value": value,
            "expires_at": expires_at,
            "set_at": set_at
        }

    def get(self, key: str):
        item = self._store.get(key)
        if not item:
            return None
        
        if time.time() > item["expires_at"]:
            self.invalidate(key)
            return None
        
        return item["value"]

    def invalidate(self, key: str):
        if key in self._store:
            del self._store[key]

    def age_seconds(self, key: str) -> float | None:
        item = self._store.get(key)
        if not item or time.time() > item["expires_at"]:
            return None
        
        return time.time() - item["set_at"]

    def last_set(self, key: str) -> str | None:
        item = self._store.get(key)
        if not item or time.time() > item["expires_at"]:
            return None
        
        dt = datetime.fromtimestamp(item["set_at"], tz=timezone.utc)
        return dt.isoformat()

risk_cache = RiskCache()
