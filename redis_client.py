import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_redis():
    return redis_client


def clear_job_cache():
    keys = redis_client.keys("jobs:list:*")

    if keys:
        redis_client.delete(*keys)
