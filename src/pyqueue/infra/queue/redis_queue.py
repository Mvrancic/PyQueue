import json
import redis
from pyqueue.config import settings

class RedisQueue:
    def __init__(self, queue_name: str = "jobs:default"):
        self.queue_name = queue_name
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def enqueue(self, job_id: str):
        """Push job_id to the queue."""
        self.client.lpush(self.queue_name, json.dumps({"job_id": job_id}))

    def dequeue(self, timeout: int = 0):
        """Blocking pop from the queue."""
        # brpop returns a tuple (queue_name, data)
        item = self.client.brpop(self.queue_name, timeout=timeout)
        if item:
            return json.loads(item[1])
        return None

# Singleton instance for simple usage, or can be instantiated per request
queue_client = RedisQueue()
