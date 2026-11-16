import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("recruitment", broker=REDIS_URL,
                    backend=REDIS_URL, include=["tasks"])

celery_app.conf.update(task_serializer="json", accept_content=[
                       "json"], result_serializer="json", timezone="Asia/Kolkata", enable_utc=True)
