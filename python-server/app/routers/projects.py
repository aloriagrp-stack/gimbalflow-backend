import time
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.config.db import is_mysql_active, get_connection, get_memory_db
from app.config.redis_cache import get_cache, set_cache

router = APIRouter(prefix="/api/projects", tags=["projects"])

class ProjectCreateRequest(BaseModel):
    title: Optional[str] = "Untitled Project"
    type: Optional[str] = "video"
    scenesCount: Optional[int] = 1
    itemsCount: Optional[int] = 1
    tag: Optional[str] = None

@router.get("")
async def get_projects():
    cache_key = "gimbalflow:projects:all"
    cached = get_cache(cache_key)
    if cached:
        return cached

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
                rows = cursor.fetchall()
            conn.close()
            set_cache(cache_key, rows, 60)
            return rows
        except Exception as err:
            print("[Projects] MySQL query failed:", err)

    memory = get_memory_db()
    set_cache(cache_key, memory["projects"], 60)
    return memory["projects"]

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreateRequest):
    new_proj = {
        "id": f"proj-{int(time.time() * 1000)}",
        "user_id": "usr-demo-01",
        "title": body.title or "Untitled Project",
        "type": body.type or "video",
        "scenesCount": body.scenesCount or 1,
        "itemsCount": body.itemsCount or 1,
        "tag": body.tag or ("8K Textures" if body.type == "image" else "60FPS Video"),
        "updatedAt": "Just now"
    }

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO projects (id, user_id, title, type, scenes_count, items_count, tag)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        new_proj["id"],
                        new_proj["user_id"],
                        new_proj["title"],
                        new_proj["type"],
                        new_proj["scenesCount"],
                        new_proj["itemsCount"],
                        new_proj["tag"]
                    )
                )
                conn.commit()
            conn.close()
        except Exception as err:
            print("[Projects] MySQL insert failed:", err)
            get_memory_db()["projects"].insert(0, new_proj)
    else:
        get_memory_db()["projects"].insert(0, new_proj)

    # Invalidate cache
    set_cache("gimbalflow:projects:all", None, 0)
    return new_proj
