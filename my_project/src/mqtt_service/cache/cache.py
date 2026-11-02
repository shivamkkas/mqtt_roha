# from collections import defaultdict, deque
# import threading
# from datetime import datetime


# class StatusCache:
#     def __init__(self):
#         self._lock = threading.Lock()
#         self._store = defaultdict(dict)
#         self._latest_operated_key = deque(maxlen=10)

#     def update_status(self, name: str, value):
#         with self._lock:
#             self._store[name]["current_status"] = value
#             self._store[name]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#             self._latest_operated_key.append(name)

#     def get_status(self, name: str):
#         with self._lock:
#             return self._store.get(name)

#     def get_latest_operated_key(self):
#         with self._lock:
#             if not self._latest_operated_key:
#                 return None

#             key = self._latest_operated_key.popleft()

#             # Delete from store also
#             self._store.pop(key, None)

#             return key

#     def get_all(self):
#         with self._lock:
#             return dict(sorted(self._store.items()))

from collections import defaultdict, deque
import threading
from datetime import datetime, timedelta


class StatusCache:
    def __init__(self, ttl_seconds: int = 15):
        self._lock = threading.Lock()
        self._store = defaultdict(dict)
        self._latest_operated_key = deque()  # removed maxlen (important!)
        self._ttl = ttl_seconds

    def update_status(self, name: str, value):
        with self._lock:
            now = datetime.now()

            self._store[name] = {
                "current_status": value,
                "last_updated": now,
                "expiry": now + timedelta(seconds=self._ttl),
            }

            self._latest_operated_key.append(name)

    def get_latest_operated_key(self):
        with self._lock:
            now = datetime.now()

            while self._latest_operated_key:
                key = self._latest_operated_key.popleft()
                item = self._store.get(key)

                if not item:
                    continue
                if now > item["expiry"]:
                    self._store.pop(key, None)
                    continue
                self._store.pop(key, None)
                return key

            return None

    def get_status(self, name: str):
        with self._lock:
            item = self._store.get(name)
            if not item:
                return None

            if datetime.now() > item["expiry"]:
                self._store.pop(name, None)
                return None

            return {
                "current_status": item["current_status"],
                "last_updated": item["last_updated"].strftime("%Y-%m-%d %H:%M:%S"),
            }

    def get_all(self):
        with self._lock:
            now = datetime.now()
            expired_keys = [
                k for k, v in self._store.items()
                if now > v["expiry"]
            ]
            for k in expired_keys:
                self._store.pop(k, None)

            return {
                k: {
                    "current_status": v["current_status"],
                    "last_updated": v["last_updated"].strftime("%Y-%m-%d %H:%M:%S"),
                }
                for k, v in sorted(self._store.items())
            }