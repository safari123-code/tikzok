# ---------------------------
# Redis Service (SAFE)
# ---------------------------

import redis
import os

try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )

    # test connection
    redis_client.ping()

except Exception as e:
    print("REDIS DISABLED:", e)
    redis_client = None