from collections import defaultdict, deque
import threading
import time

from fastapi import HTTPException, Request, status

_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_LOCK = threading.Lock()


def rate_limit(max_requests: int, window_seconds: int):
    async def dependency(request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with _LOCK:
            bucket = _BUCKETS[f"{request.url.path}:{ip}"]
            cutoff = now - window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= max_requests:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests. Please try again shortly.", headers={"Retry-After": str(retry_after)})
            bucket.append(now)
    return dependency
