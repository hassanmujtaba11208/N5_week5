from collections import defaultdict, deque
from threading import Lock
from time import monotonic

class RateLimiter:
    """In-memory sliding-window limiter with independent counters per API key."""
    def __init__(self, limit: int, window_seconds: int):
        if limit < 1 or window_seconds < 1:
            raise ValueError("Rate limit and window must be positive.")
        self.limit = limit
        self.window_seconds = window_seconds
        self._events = defaultdict(deque)
        self._lock = Lock()

    def check(self, key_fingerprint: str):
        now = monotonic()
        with self._lock:
            events = self._events[key_fingerprint]
            while events and now - events[0] >= self.window_seconds:
                events.popleft()
            if len(events) >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - events[0])))
                return False, retry_after, len(events)
            events.append(now)
            return True, 0, len(events)
