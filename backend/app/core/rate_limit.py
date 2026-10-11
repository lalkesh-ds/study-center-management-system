import time
from collections import defaultdict
from fastapi import Request, HTTPException, status

# In-memory token bucket/sliding window rate limiter
# Key: client_ip -> list of timestamps
_request_records = defaultdict(list)


def rate_limiter(max_requests: int = 10, window_seconds: int = 60):
    """
    FastAPI dependency factory enforcing rate limits per client IP.
    """
    def dependency(request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        timestamps = _request_records[client_ip]

        # Prune expired timestamps
        _request_records[client_ip] = [t for t in timestamps if now - t < window_seconds]

        if len(_request_records[client_ip]) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds."
            )

        _request_records[client_ip].append(now)

    return dependency


def reset_rate_limiter():
    """Clears rate limiter records (useful in test suites)."""
    _request_records.clear()
