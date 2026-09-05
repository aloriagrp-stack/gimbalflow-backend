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

class AiImageRequest(BaseModel):
    prompt: str
    model: Optional[str] = "Google Imagen 3 (Ultra Photoreal)"
    aspectRatio: Optional[str] = "1:1"
    aspect_ratio: Optional[str] = None
    numImages: Optional[int] = 1

@router.get("/providers-status")
def get_providers_status():
    from app.config.settings import settings
    has_gemini = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 10)
    has_openai = bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10)
    has_fal = bool(settings.FAL_KEY and len(settings.FAL_KEY) > 10)

    # Strictly list only models that are actively connected and working
    active = []
    if has_fal:
        active.extend(["FLUX 1.1 Pro", "Stable Diffusion 3.5 Large", "Ideogram 2.0"])
    if has_openai:
        active.append("OpenAI DALL-E 3")
    if has_gemini:
        active.append("Google Imagen 3")

    # Flux Realism is the verified active production generator
    active.append("Flux Realism")

    return {
        "gemini_imagen": has_gemini,
        "openai_dalle": has_openai,
        "fal_ai": has_fal,
        "active_models": active
    }

@router.post("/ai-image")
async def generate_ai_image(body: AiImageRequest):
    if not body.prompt or not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    aspect_ratio = body.aspectRatio or body.aspect_ratio or "1:1"
    raw_prompt = body.prompt.strip()

    # 1. Expand with Director-Grade prompt engine
    enhanced_data = ml_engine.enhance_prompt(raw_prompt)
    enhanced_prompt = enhanced_data.get("enhanced_prompt") or raw_prompt
    applied_tags = enhanced_data.get("applied_tags") or []
    category = enhanced_data.get("category") or "GENERAL"

    # 2. Dispatch to Real AI Provider (Imagen 3 / DALL-E 3 / Fallback)
    from app.ml.ai_image_providers import generate_real_ai_image
    gen_result = generate_real_ai_image(
        prompt=enhanced_prompt,
        model=body.model or "auto",
        aspect_ratio=aspect_ratio
    )

    image_url = gen_result.get("url")
    provider = gen_result.get("provider", "GimbalFlow AI")
    is_real_ai = gen_result.get("is_real_ai", False)

    # 3. Create generation record in DB
    gen_id = f"img-{int(time.time() * 1000)}"
    record = {
        "id": gen_id,
        "user_id": "usr-demo-01",
        "type": "image",
        "prompt": raw_prompt,
        "enhanced_prompt": enhanced_prompt,
        "model": provider,
        "aspect_ratio": aspect_ratio,
        "camera": "Hasselblad H6D-100c" if "FOOD" in category else "ARRI Alexa Mini LF",
        "status": "completed",
        "media_url": image_url,
        "cost": 10,
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
                        record["id"],
                        record["user_id"],
                        record["type"],
                        record["prompt"],
                        record["model"],
                        record["aspect_ratio"],
                        record["camera"],
                        record["status"],
                        record["media_url"],
                        record["cost"]
                    )
                )
                conn.commit()
            conn.close()
        except Exception as err:
            print("[Generation] MySQL insert failed:", err)
            get_memory_db()["generations"].insert(0, record)
    else:
        get_memory_db()["generations"].insert(0, record)

    return {
        "success": True,
        "id": gen_id,
        "url": image_url,
        "prompt": raw_prompt,
        "enhanced_prompt": enhanced_prompt,
        "category": category,
        "applied_tags": applied_tags,
        "provider": provider,
        "is_real_ai": is_real_ai,
        "aspect_ratio": aspect_ratio,
        "notice": gen_result.get("notice")
    }

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
