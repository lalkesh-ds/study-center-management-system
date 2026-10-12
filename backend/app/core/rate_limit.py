import time
from collections import defaultdict
from fastapi import Request, HTTPException, status

# In-memory token bucket/sliding window rate limiter
# Key: client_ip -> list of timestamps
_request_records = defaultdict(list)


def get_client_ip(request: Request) -> str:
    """
    Safely resolves client IP from request, taking the first X-Forwarded-For hop
    if present behind a reverse proxy, falling back to direct client host.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First entry is the client IP
        client = forwarded.split(",")[0].strip()
        if client:
            return client
    return request.client.host if request.client else "127.0.0.1"


def rate_limiter(max_requests: int = 10, window_seconds: int = 60):
    """
    FastAPI dependency factory enforcing rate limits per client IP.
    """
    def dependency(request: Request):
        client_ip = get_client_ip(request)
        now = time.time()
        timestamps = _request_records[client_ip]

        # Prune expired timestamps for current client
        valid_timestamps = [t for t in timestamps if now - t < window_seconds]
        _request_records[client_ip] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds."
            )

        _request_records[client_ip].append(now)

        # Opportunistic memory cleanup if map size exceeds 5000 entries
        if len(_request_records) > 5000:
            for ip in list(_request_records.keys()):
                _request_records[ip] = [t for t in _request_records[ip] if now - t < window_seconds]
                if not _request_records[ip]:
                    del _request_records[ip]

    return dependency


def reset_rate_limiter():
    """Clears rate limiter records (useful in test suites)."""
    _request_records.clear()
