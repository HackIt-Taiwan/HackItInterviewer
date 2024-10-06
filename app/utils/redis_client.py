# app/utils/redis_client.py
from redis import Redis
import os

redis_client = Redis.from_url(os.getenv('REDIS_URI'))