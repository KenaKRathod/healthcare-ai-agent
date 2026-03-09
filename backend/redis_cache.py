import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)


def cache_response(key, value):
    redis_client.set(key, value)


def get_cache(key):
    return redis_client.get(key)


def cache_data(key, value):
    cache_response(key, value)
