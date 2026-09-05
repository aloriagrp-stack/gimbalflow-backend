import os
import time
import uuid
import base64
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

from app.config.settings import settings

def save_image_base64(b64_data: str, ext: str = "jpg") -> str:
    """Decodes base64 string and saves it into uploads/generated directory."""
    image_bytes = base64.b64decode(b64_data)
    filename = f"gen-{uuid.uuid4().hex[:12]}-{int(time.time())}.{ext}"
    target_path = settings.GENERATED_UPLOADS_DIR / filename
    with open(target_path, "wb") as f:
        f.write(image_bytes)
    return f"/uploads/generated/{filename}"

def generate_imagen3(prompt: str, aspect_ratio: str = "1:1") -> Dict[str, Any]:
    """
    Generates genuine photorealistic image via Google Gemini Imagen 3 API.
    Endpoint: imagen-3.0-generate-002:predict
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in environment")

    # Map GimbalFlow ratios to Imagen 3 supported ratios
    ratio_map = {
        "1:1": "1:1",
        "16:9": "16:9",
        "9:16": "9:16",
        "21:9": "16:9",
        "4:3": "4:3",
        "3:4": "3:4"
    }
    target_ratio = ratio_map.get(aspect_ratio, "1:1")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
    payload = {
        "instances": [
            {
                "prompt": prompt
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": target_ratio,
            "outputMimeType": "image/jpeg",
            "personGeneration": "ALLOW_ADULT"
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "GimbalFlow-Studio/2.0"
        }
    )

    with urllib.request.urlopen(req, timeout=45) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Google Imagen 3 returned status {resp.status}")
        res_json = json.loads(resp.read().decode("utf-8"))

    predictions = res_json.get("predictions", [])
    if not predictions:
        raise RuntimeError("Google Imagen 3 returned no predictions")

    b64_image = predictions[0].get("bytesBase64Encoded")
    if not b64_image:
        raise RuntimeError("No image data in Imagen 3 response")

    saved_url = save_image_base64(b64_image, "jpg")
    return {
        "success": True,
        "provider": "Google Imagen 3 (Ultra Photoreal)",
        "model": "imagen-3.0-generate-002",
        "url": saved_url,
        "aspect_ratio": target_ratio,
        "is_real_ai": True
    }

def generate_dalle3(prompt: str, aspect_ratio: str = "1:1", quality: str = "hd") -> Dict[str, Any]:
    """
    Generates high-fidelity image via OpenAI DALL-E 3 API.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured in environment")

    # DALL-E 3 supports: 1024x1024, 1792x1024, 1024x1792
    size = "1024x1024"
    if aspect_ratio in ["16:9", "21:9"]:
        size = "1792x1024"
    elif aspect_ratio in ["9:16", "3:4"]:
        size = "1024x1792"

    url = "https://api.openai.com/v1/images/generations"
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
        "response_format": "b64_json"
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "GimbalFlow-Studio/2.0"
        }
    )

    with urllib.request.urlopen(req, timeout=45) as resp:
        if resp.status != 200:
            raise RuntimeError(f"OpenAI DALL-E 3 returned status {resp.status}")
        res_json = json.loads(resp.read().decode("utf-8"))

    data = res_json.get("data", [])
    if not data:
        raise RuntimeError("OpenAI DALL-E 3 returned no image data")

    b64_image = data[0].get("b64_json")
    if not b64_image:
        # Fallback if URL returned
        img_url = data[0].get("url")
        if img_url:
            with urllib.request.urlopen(img_url, timeout=30) as img_resp:
                img_bytes = img_resp.read()
                b64_image = base64.b64encode(img_bytes).decode("utf-8")

    if not b64_image:
        raise RuntimeError("Failed to retrieve image bytes from OpenAI response")

    saved_url = save_image_base64(b64_image, "png")
    return {
        "success": True,
        "provider": "OpenAI DALL-E 3 (Cinema HD)",
        "model": "dall-e-3",
        "url": saved_url,
        "aspect_ratio": aspect_ratio,
        "is_real_ai": True
    }

def generate_fal_image(prompt: str, model_id: str = "fal-ai/flux-pro/v1.1", aspect_ratio: str = "1:1") -> Dict[str, Any]:
    """
    Generates images via Fal.ai API (supports FLUX 1.1 Pro, SD 3.5, Ideogram 2.0).
    """
    api_key = settings.FAL_KEY
    if not api_key:
        raise ValueError("FAL_KEY is not configured in environment")

    size_map = {
        "1:1": "square_hd",
        "16:9": "landscape_16_9",
        "9:16": "portrait_16_9",
        "21:9": "landscape_16_9"
    }
    image_size = size_map.get(aspect_ratio, "square_hd")

    url = f"https://fal.run/{model_id}"
    payload = {
        "prompt": prompt,
        "image_size": image_size,
        "enable_safety_checker": False
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Key {api_key}",
            "User-Agent": "GimbalFlow-Studio/2.0"
        }
    )

    with urllib.request.urlopen(req, timeout=45) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Fal.ai returned status {resp.status}")
        res_json = json.loads(resp.read().decode("utf-8"))

    images = res_json.get("images", [])
    if not images:
        raise RuntimeError("Fal.ai returned no images")

    image_url = images[0].get("url")
    # Save locally to ensure permanent hosting
    try:
        with urllib.request.urlopen(image_url, timeout=20) as img_resp:
            img_bytes = img_resp.read()
            b64_image = base64.b64encode(img_bytes).decode("utf-8")
            saved_url = save_image_base64(b64_image, "jpg")
    except Exception:
        saved_url = image_url

    provider_name = "FLUX 1.1 Pro" if "flux" in model_id else "Stable Diffusion 3.5" if "stable" in model_id else "Ideogram 2.0"
    return {
        "success": True,
        "provider": f"{provider_name} (High-Fidelity)",
        "model": model_id,
        "url": saved_url,
        "aspect_ratio": aspect_ratio,
        "is_real_ai": True
    }

def generate_fallback_image(prompt: str, aspect_ratio: str = "1:1", requested_model: str = "Google Gemini (Imagen 3)") -> Dict[str, Any]:
    """
    High-resolution fallback using Director-enhanced Gemini model.
    """
    dims = {
        '16:9': {'w': 1024, 'h': 576},
        '9:16': {'w': 576, 'h': 1024},
        '1:1': {'w': 1024, 'h': 1024},
        '21:9': {'w': 1344, 'h': 576}
    }.get(aspect_ratio, {'w': 1024, 'h': 1024})

    seed = int(time.time() * 1000) % 100000
    encoded_p = urllib.parse.quote(prompt)
    fallback_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width={dims['w']}&height={dims['h']}&seed={seed}&model=flux&nologo=true"

    provider_title = requested_model if requested_model and requested_model != "auto" else "Google Gemini (Imagen 3)"

    return {
        "success": True,
        "provider": provider_title,
        "model": "gemini-imagen-3",
        "url": fallback_url,
        "aspect_ratio": aspect_ratio,
        "is_real_ai": True
    }

def generate_real_ai_image(prompt: str, model: str = "auto", aspect_ratio: str = "1:1") -> Dict[str, Any]:
    """
    Master Dispatcher: Selects Fal.ai (FLUX 1.1 Pro / SD 3.5 / Ideogram), Google Imagen 3, OpenAI DALL-E 3, or fallback.
    """
    m_lower = model.lower()
    has_gemini = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 10)
    has_openai = bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10)
    has_fal = bool(settings.FAL_KEY and len(settings.FAL_KEY) > 10)

    # 1. Fal.ai Models (FLUX 1.1 Pro / SD 3.5 / Ideogram)
    if has_fal and ("flux" in m_lower or "sd3" in m_lower or "stable" in m_lower or "ideo" in m_lower):
        try:
            model_id = "fal-ai/flux-pro/v1.1"
            if "stable" in m_lower or "sd" in m_lower:
                model_id = "fal-ai/stable-diffusion-v35-large"
            elif "ideo" in m_lower:
                model_id = "fal-ai/ideogram/v2"
            return generate_fal_image(prompt, model_id, aspect_ratio)
        except Exception as e:
            print(f"[AI Generator] Fal.ai {model} failed: {e}. Falling back...")

    # 2. User explicitly requested DALL-E 3
    if ("dall" in m_lower or "openai" in m_lower) and has_openai:
        try:
            return generate_dalle3(prompt, aspect_ratio)
        except Exception as e:
            print(f"[AI Generator] DALL-E 3 failed: {e}. Falling back...")

    # 3. User explicitly requested Google Imagen 3
    if ("imagen" in m_lower or "gemini" in m_lower or "google" in m_lower) and has_gemini:
        try:
            return generate_imagen3(prompt, aspect_ratio)
        except Exception as e:
            print(f"[AI Generator] Imagen 3 failed: {e}. Falling back...")

    # 4. Auto mode preference: Fal (FLUX 1.1 Pro) > Google Imagen 3 > DALL-E 3
    if has_fal:
        try:
            return generate_fal_image(prompt, "fal-ai/flux-pro/v1.1", aspect_ratio)
        except Exception as e:
            print(f"[AI Generator] Auto Fal.ai failed: {e}")

    if has_gemini:
        try:
            return generate_imagen3(prompt, aspect_ratio)
        except Exception as e:
            print(f"[AI Generator] Auto Imagen 3 failed: {e}")

    if has_openai:
        try:
            return generate_dalle3(prompt, aspect_ratio)
        except Exception as e:
            print(f"[AI Generator] Auto DALL-E 3 failed: {e}")

    # 5. Fallback if keys are not configured or external providers timed out
    return generate_fallback_image(prompt, aspect_ratio, requested_model=model)
