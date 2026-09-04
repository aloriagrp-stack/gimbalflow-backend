import time
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Optional
from app.config.db import is_mysql_active, get_connection, get_memory_db
from app.config.redis_cache import get_cache, set_cache

router = APIRouter(prefix="/api/assets", tags=["assets"])

class AssetCreateRequest(BaseModel):
    name: Optional[str] = "New Asset Reference"
    type: Optional[str] = "image"
    tag: Optional[str] = "Custom Reference"
    tagClass: Optional[str] = "soul"
    meta: Optional[str] = "Used in 1 Project"
    url: Optional[str] = None

@router.get("")
async def get_assets():
    cache_key = "gimbalflow:assets:all"
    cached = get_cache(cache_key)
    if cached:
        return cached

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM assets ORDER BY created_at DESC")
                rows = cursor.fetchall()
            conn.close()
            set_cache(cache_key, rows, 60)
            return rows
        except Exception as err:
            print("[Assets] MySQL query failed:", err)

    memory = get_memory_db()
    set_cache(cache_key, memory["assets"], 60)
    return memory["assets"]

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_asset(body: AssetCreateRequest):
    new_asset = {
        "id": f"ast-{int(time.time() * 1000)}",
        "user_id": "usr-demo-01",
        "name": body.name or "New Asset Reference",
        "type": body.type or "image",
        "tag": body.tag or "Custom Reference",
        "tagClass": body.tagClass or "soul",
        "meta": body.meta or "Used in 1 Project",
        "url": body.url or "https://image.pollinations.ai/prompt/cinematic%20portrait%20of%20a%20woman%20neon%20cyan%20rim%20light%20dark%20studio?width=500&height=500&seed=501&model=flux&nologo=true"
    }

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO assets (id, user_id, name, type, tag, tag_class, meta, url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        new_asset["id"],
                        new_asset["user_id"],
                        new_asset["name"],
                        new_asset["type"],
                        new_asset["tag"],
                        new_asset["tagClass"],
                        new_asset["meta"],
                        new_asset["url"]
                    )
                )
                conn.commit()
            conn.close()
        except Exception as err:
            print("[Assets] MySQL insert failed:", err)
            get_memory_db()["assets"].insert(0, new_asset)
    else:
        get_memory_db()["assets"].insert(0, new_asset)

    set_cache("gimbalflow:assets:all", None, 0)
    return new_asset
