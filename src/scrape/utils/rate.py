import time
from collections import deque

class RateLimiter:
    def __init__(self, max_per_minute: int, burst: int = 1):
        self.max_per_minute = max_per_minute
        self.burst = burst
        self.calls = deque()

    def wait(self):
        now = time.time()
        window = 60.0
        # Clean old
        while self.calls and (now - self.calls[0]) > window:
            self.calls.popleft()
        # Enforce
        if len(self.calls) >= max(self.burst, self.max_per_minute):
            sleep_s = window - (now - self.calls[0]) + 0.05
            time.sleep(max(0.0, sleep_s))
        self.calls.append(time.time())
