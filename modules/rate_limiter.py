from functools import wraps
from flask import request, abort, jsonify
import time

# Simple in-memory rate limiter to avoid package installation overhead or failures
# Stores: key (route:ip) -> list of timestamps
_IP_LIMITS = {}

def rate_limit(limit=5, period=60):
    """
    Simple IP-based rate limiter decorator.
    limit: max requests allowed
    period: time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # In local dev request.remote_addr is fine. Behind proxies (like Render),
            # ProxyFix is already configured on app, so request.remote_addr is resolved correctly.
            ip = request.remote_addr or "unknown"
            now = time.time()
            
            # Use route path and IP to isolate rate limits per route
            key = f"{request.path}:{ip}"
            
            if key not in _IP_LIMITS:
                _IP_LIMITS[key] = []
                
            # Filter out timestamps outside the time window
            _IP_LIMITS[key] = [t for t in _IP_LIMITS[key] if now - t < period]
            
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
