
import redis

from config import settings

redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)


def get_redis():
    return redis_client


def clear_job_cache():
    keys = redis_client.keys("jobs:list:*")
    if keys:
        redis_client.delete(*keys)
