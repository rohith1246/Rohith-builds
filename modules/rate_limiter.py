from functools import wraps
from flask import request, abort, jsonify
import time
import threading

# Simple in-memory rate limiter to avoid package installation overhead or failures
# Stores: key (route:ip) -> list of timestamps
_IP_LIMITS = {}
_LIMITS_LOCK = threading.Lock()
_LAST_CLEANUP = 0
_CLEANUP_INTERVAL = 300 # 5 minutes

def rate_limit(limit=5, period=60):
    """
    Simple IP-based rate limiter decorator.
    limit: max requests allowed
    period: time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            global _LAST_CLEANUP
            # In local dev request.remote_addr is fine. Behind proxies (like Render),
            # ProxyFix is already configured on app, so request.remote_addr is resolved correctly.
            ip = request.remote_addr or "unknown"
            now = time.time()
            
            # Use route path and IP to isolate rate limits per route
            key = f"{request.path}:{ip}"
            
            with _LIMITS_LOCK:
                # Periodic cleanup of all expired keys in _IP_LIMITS to prevent memory leak
                if now - _LAST_CLEANUP > _CLEANUP_INTERVAL:
                    for k in list(_IP_LIMITS.keys()):
                        _IP_LIMITS[k] = [t for t in _IP_LIMITS[k] if now - t < period]
                        if not _IP_LIMITS[k]:
                            _IP_LIMITS.pop(k, None)
                    _LAST_CLEANUP = now

                # Initialize key list if not present
                if key not in _IP_LIMITS:
                    _IP_LIMITS[key] = []
                    
                # Filter out timestamps outside the time window for the current key
                _IP_LIMITS[key] = [t for t in _IP_LIMITS[key] if now - t < period]
                
                # Check limit
                if len(_IP_LIMITS[key]) >= limit:
                    # Return JSON response for API endpoints, abort 429 for page requests
                    is_json = (
                        request.path.startswith("/api/") 
                        or request.headers.get("Content-Type") == "application/json" 
                        or request.accept_mimetypes.accept_json
                    )
                    if is_json:
                        return jsonify({"success": False, "message": "Too many requests. Please try again later."}), 429
                    abort(429, description="Too many requests. Please try again later.")
                    
                _IP_LIMITS[key].append(now)

            return f(*args, **kwargs)
        return wrapped
    return decorator
