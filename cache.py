import time
import threading
from collections import defaultdict


class StatusCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._store = defaultdict(dict)
        self._latest_operated_key = None

    def update_status(self, name: str, value):
        """Update current and last status"""
        with self._lock:
            prev = self._store[name].get("current_status")
            self._store[name]["last_status"] = prev
            self._store[name]["current_status"] = value
            self._store[name]["last_updated"] = int(time.time() * 1000)

            # Track latest operated key
            self._latest_operated_key = name

    def get_status(self, name: str):
        """Return full status object"""
        with self._lock:
            return self._store.get(name)

    def get_latest_operated_key(self):
        """Return most recently updated key"""
        with self._lock:
            return self._latest_operated_key

    def get_all(self):
        """Optional: debug purpose"""
        with self._lock:
            return dict(self._store)