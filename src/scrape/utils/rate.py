import time
import random
from collections import deque
from loguru import logger

class RateLimiter:
    def __init__(self, max_per_minute: int, burst: int = 1, backoff_initial_s: float = 1.0, backoff_max_s: float = 30.0):
        self.max_per_minute = max_per_minute
        self.burst = burst
        self.backoff_initial_s = backoff_initial_s
        self.backoff_max_s = backoff_max_s
        self.calls = deque()
        self.consecutive_failures = 0

    def wait(self):
        """Wait if necessary to respect rate limits."""
        now = time.time()
        window = 60.0
        
        # Clean old calls outside the window
        while self.calls and (now - self.calls[0]) > window:
            self.calls.popleft()
        
        # Check if we need to wait
        if len(self.calls) >= self.max_per_minute:
            sleep_s = window - (now - self.calls[0]) + 0.1
            logger.debug(f"Rate limit reached, waiting {sleep_s:.2f}s")
            time.sleep(max(0.0, sleep_s))
        
        self.calls.append(time.time())

    def backoff(self):
        """Exponential backoff for consecutive failures."""
        self.consecutive_failures += 1
        backoff_s = min(
            self.backoff_initial_s * (2 ** (self.consecutive_failures - 1)),
            self.backoff_max_s
        )
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.1, 0.5) * backoff_s
        total_sleep = backoff_s + jitter
        
        logger.warning(f"Backing off for {total_sleep:.2f}s (failure #{self.consecutive_failures})")
        time.sleep(total_sleep)

    def reset_backoff(self):
        """Reset backoff counter on successful request."""
        self.consecutive_failures = 0
