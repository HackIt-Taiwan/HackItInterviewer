# app/utils/redis_client.py
from redis import Redis
import os

redis_uri = os.getenv('REDIS_URI')
redis_client = None

if redis_uri:
    try:
        redis_client = Redis.from_url(redis_uri)
    except Exception as e:
        print(f"Error initializing Redis: {e}")
else:
    print("REDIS_URI not set, skipping Redis initialization.")
