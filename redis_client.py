
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


def clear_dashboard_cache(user_id: int):
    pattern = f"dashboard:{user_id}:*"

    keys = redis_client.scan_iter(match=pattern)

    for key in keys:
        redis_client.delete(key)
