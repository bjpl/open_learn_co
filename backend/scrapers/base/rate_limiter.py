"""
Rate limiter for web scraping operations
"""

import asyncio
import time
from typing import Dict, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for async operations"""

    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        async with self._lock:
            now = time.time()

            # Remove old requests outside the time window
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()

            # If we're at the limit, wait
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                    await asyncio.sleep(sleep_time)
                    # After sleeping, clean up old requests again
                    now = time.time()
                    while self.requests and self.requests[0] <= now - self.time_window:
                        self.requests.popleft()

            # Record this request
            self.requests.append(now)

    def get_current_rate(self) -> float:
        """Get current request rate"""
        now = time.time()
        # Clean old requests
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()

        if not self.requests:
            return 0.0

        time_span = now - self.requests[0]
        if time_span == 0:
            return 0.0

        return len(self.requests) / time_span


class DomainRateLimiter:
    """Rate limiter that manages limits per domain"""

    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.default_max_requests = 10
        self.default_time_window = 60

    def get_limiter(self, domain: str) -> RateLimiter:
        """Get or create a rate limiter for a domain"""
        if domain not in self.limiters:
            # Custom limits for specific domains
            if "eltiempo.com" in domain:
                self.limiters[domain] = RateLimiter(max_requests=5, time_window=60)
            elif "elespectador.com" in domain:
                self.limiters[domain] = RateLimiter(max_requests=5, time_window=60)
            elif "gov.co" in domain:
                self.limiters[domain] = RateLimiter(max_requests=3, time_window=60)
            else:
                self.limiters[domain] = RateLimiter(
                    self.default_max_requests,
                    self.default_time_window
                )

        return self.limiters[domain]

    async def acquire(self, url: str):
        """Acquire permission to make a request to a URL"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        limiter = self.get_limiter(domain)
        await limiter.acquire()


# Global rate limiter instance
global_rate_limiter = DomainRateLimiter()