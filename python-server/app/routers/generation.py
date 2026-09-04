import time
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.ml.ml_pipeline import ml_engine
from app.config.redis_cache import enqueue_task
from app.config.db import is_mysql_active, get_connection, get_memory_db

router = APIRouter(prefix="/api/generate", tags=["generate"])

class EnhancePromptRequest(BaseModel):
    prompt: str

class GenerationJobRequest(BaseModel):
    type: Optional[str] = "video"
    prompt: str
    model: Optional[str] = "Seedance v2"
    aspectRatio: Optional[str] = "16:9"
    aspect_ratio: Optional[str] = None
    camera: Optional[str] = "FPV Drone Swoop 360°"
    resolution: Optional[str] = "8K Ultra"
    numImages: Optional[int] = 1
    guidance: Optional[float] = 7.5
    steps: Optional[int] = 30
    referenceImg: Optional[str] = None
    reference_img: Optional[str] = None

@router.post("/enhance-prompt")
async def enhance_prompt(body: EnhancePromptRequest):
    if not body.prompt or not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")
    enhanced = ml_engine.enhance_prompt(body.prompt)
    return enhanced

@router.post("/job", status_code=status.HTTP_201_CREATED)
async def create_generation_job(body: GenerationJobRequest):
    if not body.prompt or not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")

    aspect_ratio = body.aspectRatio or body.aspect_ratio or "16:9"
    ref_img = body.referenceImg or body.reference_img

    # 1. Enqueue task in Redis / internal queue
    task_payload = {
        "type": body.type or "video",
        "prompt": body.prompt,
        "model": body.model or "Seedance v2",
        "aspectRatio": aspect_ratio,
        "camera": body.camera or "FPV Drone Swoop 360°"
    }
    queue_item = enqueue_task("generation_tasks", task_payload)

    # 2. Execute via in-process ML Engine
    ml_result = ml_engine.execute_generation_pipeline({
        "type": body.type or "video",
        "prompt": body.prompt,
        "model": body.model or "Seedance v2",
        "aspectRatio": aspect_ratio,
        "camera": body.camera or "FPV Drone Swoop 360°",
        "referenceImg": ref_img
    })

    # 3. Create Generation Record
    generation_record = {
        "id": ml_result.get("job_id") or f"gen-{int(time.time() * 1000)}",
        "user_id": "usr-demo-01",
        "type": body.type or "video",
        "prompt": body.prompt,
        "model": body.model or "Seedance v2",
        "aspectRatio": aspect_ratio,
        "camera": body.camera or "FPV Drone Swoop 360°",
        "status": ml_result.get("status") or "completed",
        "mediaUrl": ml_result.get("media_url"),
        "cost": ml_result.get("cost") or 20,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO generations (id, user_id, type, prompt, model, aspect_ratio, camera, status, media_url, cost)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        generation_record["id"],
                        generation_record["user_id"],
                        generation_record["type"],
                        generation_record["prompt"],
                        generation_record["model"],
                        generation_record["aspectRatio"],
                        generation_record["camera"],
                        generation_record["status"],
                        generation_record["mediaUrl"],
                        generation_record["cost"]
                    )
                )
                conn.commit()
            conn.close()
        except Exception as err:
            print("[Generation] MySQL insert failed:", err)
            get_memory_db()["generations"].insert(0, generation_record)
    else:
        get_memory_db()["generations"].insert(0, generation_record)

    return {
        "success": True,
        "task": queue_item,
        "result": generation_record
    }
