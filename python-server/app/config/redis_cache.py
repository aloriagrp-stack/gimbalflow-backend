import time
import json
from typing import Any, Optional, Dict
from app.config.settings import settings

redis_client = None
is_redis_connected: bool = False
in_memory_cache: Dict[str, Dict[str, Any]] = {}
in_memory_queue: list = []

def init_redis():
    global redis_client, is_redis_connected
    try:
        import redis
        host = settings.REDIS_HOST
        if host == "localhost":
            host = "127.0.0.1"
        client = redis.Redis(
            host=host,
            port=settings.REDIS_PORT,
            socket_connect_timeout=1,
            decode_responses=True
        )
        client.ping()
        redis_client = client
        is_redis_connected = True
        print(f"[Redis] Connected successfully to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except Exception as err:
        print(f"[Redis Notice] Redis connection failed ({err}). Using internal cache queue.")
        redis_client = None
        is_redis_connected = False

def set_cache(key: str, value: Any, ttl_seconds: int = 300):
    global in_memory_cache
    if is_redis_connected and redis_client:
        try:
            val_str = json.dumps(value) if value is not None else ""
            if value is None:
                redis_client.delete(key)
            else:
                redis_client.setex(key, ttl_seconds, val_str)
            return
        except Exception:
            pass

    if value is None:
        in_memory_cache.pop(key, None)
    else:
        in_memory_cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl_seconds
        }

def get_cache(key: str) -> Optional[Any]:
    global in_memory_cache
    if is_redis_connected and redis_client:
        try:
            data = redis_client.get(key)
            return json.loads(data) if data else None
        except Exception:
            pass

    item = in_memory_cache.get(key)
    if not item:
        return None
    if time.time() > item["expires_at"]:
        del in_memory_cache[key]
        return None
    return item["value"]

def enqueue_task(queue_name: str, task_data: Any) -> Dict[str, Any]:
    task_payload = {
        "id": f"task-{int(time.time() * 1000)}",
        "queueName": queue_name,
        "taskData": task_data,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    if is_redis_connected and redis_client:
        try:
            redis_client.lpush(queue_name, json.dumps(task_payload))
            return task_payload
        except Exception:
            pass

    in_memory_queue.append(task_payload)
    return task_payload

def get_redis_status() -> Dict[str, Any]:
    return {
        "connected": is_redis_connected,
        "cachedKeys": len(in_memory_cache),
        "queuedTasks": len(in_memory_queue)
    }
