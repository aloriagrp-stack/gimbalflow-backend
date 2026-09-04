from fastapi import APIRouter
from app.config.db import is_mysql_active, get_connection, get_memory_db
from app.config.redis_cache import get_cache, set_cache

router = APIRouter(prefix="/api/explore", tags=["explore"])

@router.get("")
async def get_explore_items():
    cache_key = "gimbalflow:explore:all"
    cached = get_cache(cache_key)
    if cached:
        return cached

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM explore_items ORDER BY likes DESC")
                rows = cursor.fetchall()
            conn.close()
            set_cache(cache_key, rows, 120)
            return rows
        except Exception as err:
            print("[Explore] MySQL query failed:", err)

    memory = get_memory_db()
    set_cache(cache_key, memory["explore"], 120)
    return memory["explore"]
