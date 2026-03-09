import redis
import os

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    decode_responses=True
)

def cache_data(key,value):

    redis_client.set(key,value)

def get_cache(key):

    return redis_client.get(key)