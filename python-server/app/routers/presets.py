from fastapi import APIRouter
from app.config.db import is_mysql_active, get_connection, get_memory_db
from app.config.redis_cache import get_cache, set_cache

router = APIRouter(prefix="/api/presets", tags=["presets"])

@router.get("")
async def get_presets():
    cache_key = "gimbalflow:presets:all"
    cached = get_cache(cache_key)
    if cached:
        return cached

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM presets ORDER BY created_at DESC")
                rows = cursor.fetchall()
            conn.close()
            set_cache(cache_key, rows, 300)
            return rows
        except Exception as err:
            print("[Presets] MySQL query failed:", err)

    memory = get_memory_db()
    set_cache(cache_key, memory["presets"], 300)
    return memory["presets"]
