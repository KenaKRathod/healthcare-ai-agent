import os
from datetime import datetime, timedelta
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = None
redis_available = False

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=1.0,  # Fast timeout for local dev
    )
    # Test connection
    redis_client.ping()
    redis_available = True
    print("Redis connected successfully. Caching is active.")
except Exception as e:
    redis_available = False
    print(f"Warning: Redis connection failed ({e}). Falling back to in-memory dictionary caching.")

# Fallback structures for in-memory cache
_in_memory_cache = {}
_in_memory_expirations = {}


def get_cache(key: str) -> str | None:
    """Retrieve key value from Redis or local in-memory fallback."""
    global redis_available
    if redis_available:
        try:
            return redis_client.get(key)
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            redis_available = False
            print("Redis server connection lost. Switched to in-memory fallback cache.")

    # In-memory fallback check
    if key in _in_memory_cache:
        expire_at = _in_memory_expirations.get(key)
        if expire_at and datetime.now() > expire_at:
            # Expired, clean up
            del _in_memory_cache[key]
            del _in_memory_expirations[key]
            return None
        return _in_memory_cache[key]
    return None


def cache_response(key: str, value: str, expire_seconds: int = 300):
    """Set value with expiration in Redis or local in-memory fallback."""
    global redis_available
    if redis_available:
        try:
            redis_client.set(key, value, ex=expire_seconds)
            return
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            redis_available = False
            print("Redis server connection lost during set. Switched to in-memory fallback cache.")

    # In-memory fallback storage
    _in_memory_cache[key] = value
    _in_memory_expirations[key] = datetime.now() + timedelta(seconds=expire_seconds)


def cache_data(key: str, value: str):
    """Alias for cache_response with default expiration."""
    cache_response(key, value)


def invalidate_cache(key: str):
    """Removes a cache key to force a fresh reload."""
    global redis_available
    if redis_available:
        try:
            redis_client.delete(key)
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            redis_available = False

    if key in _in_memory_cache:
        del _in_memory_cache[key]
    if key in _in_memory_expirations:
        del _in_memory_expirations[key]
