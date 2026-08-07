"""Rate limiting middleware — simple in-memory sliding window."""

import time
from collections import defaultdict
from fastapi import Request, HTTPException


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        window = now - 60
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window]

        if len(self.requests[client_ip]) >= self.rpm:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")

        self.requests[client_ip].append(now)
        return await call_next(request)
