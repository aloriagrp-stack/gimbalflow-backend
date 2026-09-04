import json
import time
import base64
import secrets
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel
from app.config.settings import settings
from app.config.admin_auth import (
    check_credentials,
    create_session,
    verify_token,
    revoke_token,
    session_count
)

router = APIRouter(tags=["admin"])

DATA_DIR = settings.DATA_DIR
UPLOAD_DIR = settings.HERO_UPLOADS_DIR
HERO_FILE = DATA_DIR / "hero-cards.json"
GALLERY_FILE = DATA_DIR / "gallery.json"

EXT_BY_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov"
}

def load_cards() -> List[Dict[str, Any]]:
    if HERO_FILE.exists():
        try:
            with open(HERO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print("[Admin] Could not read hero-cards.json:", e)
    return []

hero_cards: List[Dict[str, Any]] = load_cards()

def save_cards():
    try:
        with open(HERO_FILE, "w", encoding="utf-8") as f:
            json.dump(hero_cards, f, indent=2)
    except Exception as e:
        print("[Admin] Failed to persist hero cards:", e)

def load_gallery() -> List[Dict[str, Any]]:
    if GALLERY_FILE.exists():
        try:
            with open(GALLERY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print("[Admin] Could not read gallery.json:", e)
    return []

gallery: List[Dict[str, Any]] = load_gallery()

def save_gallery_file():
    try:
        with open(GALLERY_FILE, "w", encoding="utf-8") as f:
            json.dump(gallery, f, indent=2)
    except Exception as e:
        print("[Admin] Failed to persist gallery:", e)

def save_media(data_url: Optional[str]) -> Optional[str]:
    if not isinstance(data_url, str) or not data_url:
        return None

    if data_url.startswith("/uploads/") or data_url.startswith("http://") or data_url.startswith("https://"):
        return data_url

    if not data_url.startswith("data:") or ";base64," not in data_url:
        return None

    try:
        header, base64_data = data_url.split(";base64,", 1)
        raw_mime = header[5:].split(";")[0].lower().strip()

        ext = EXT_BY_MIME.get(raw_mime)
        if not ext:
            if raw_mime.startswith("video/"):
                ext = "mp4"
            elif raw_mime.startswith("image/"):
                ext = "jpg"
            else:
                ext = "bin"

        file_bytes = base64.b64decode(base64_data)
        if not file_bytes:
            return None

        filename = f"{int(time.time() * 1000)}-{secrets.token_hex(6)}.{ext}"
        target_path = UPLOAD_DIR / filename
        with open(target_path, "wb") as f:
            f.write(file_bytes)

        return f"/uploads/hero/{filename}"
    except Exception as e:
        print("[Admin] save_media write failed:", e)
        return None

def delete_media(url_path: Optional[str]):
    if not isinstance(url_path, str) or not url_path.startswith("/uploads/"):
        return
    try:
        name = Path(url_path).name
        target = UPLOAD_DIR / name
        if target.exists():
            target.unlink()
    except Exception as e:
        print("[Admin] Could not delete media file:", e)

def require_admin_auth(request: Request):
    header = request.headers.get("authorization") or ""
    token = header[7:].strip() if header.startswith("Bearer ") else ""
    if not token or not verify_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized. Valid admin session required."
        )
    return True

# ─── Pydantic Request Models ───
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class HeroCardsSaveRequest(BaseModel):
    cards: List[Dict[str, Any]]

class GallerySaveRequest(BaseModel):
    items: List[Dict[str, Any]]

class UploadMediaRequest(BaseModel):
    fileData: str

# ─── Public Endpoints ───
@router.get("/api/hero")
def get_hero_cards():
    return hero_cards

@router.get("/api/gallery")
def get_gallery():
    return gallery

# ─── Admin Endpoints ───
@router.post("/api/admin/login")
def admin_login(body: AdminLoginRequest):
    if not check_credentials(body.username, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    token = create_session()
    return {
        "token": token,
        "expiresInHours": settings.ADMIN_TOKEN_TTL_HOURS or 12
    }

@router.post("/api/admin/logout")
def admin_logout(request: Request):
    header = request.headers.get("authorization") or ""
    token = header[7:].strip() if header.startswith("Bearer ") else ""
    revoke_token(token)
    return {"ok": True}

@router.get("/api/admin/info")
def admin_info(auth: bool = Depends(require_admin_auth)):
    return {
        "sessions": session_count(),
        "heroCards": len(hero_cards)
    }

@router.post("/api/admin/hero")
def save_hero_cards(body: HeroCardsSaveRequest, auth: bool = Depends(require_admin_auth)):
    global hero_cards
    refreshed = []
    valid_links = ["/cinema", "/image", "/explore", "/profile"]

    for c in body.cards:
        prev = next((h for h in hero_cards if h.get("id") == c.get("id")), None)
        title = (c.get("title") or "").strip()[:80]
        desc = (c.get("desc") or "").strip()[:160] if c.get("desc") is not None else (prev.get("desc") if prev else "")
        media = "video" if c.get("media") == "video" else "img"
        
        link = c.get("link")
        if link not in valid_links:
            link = prev.get("link") if prev and prev.get("link") in valid_links else None

        src = c.get("src") or (prev.get("src") if prev else "")
        poster = c.get("poster") or (prev.get("poster") if prev else "")

        new_src = save_media(c.get("srcData"))
        if new_src:
            delete_media(src)
            src = new_src
        elif not src and c.get("srcData"):
            src = c.get("srcData")

        new_poster = save_media(c.get("posterData"))
        if new_poster:
            delete_media(poster)
            poster = new_poster
        elif not poster and c.get("posterData"):
            poster = c.get("posterData")

        if not title and not src:
            continue

        refreshed.append({
            "id": c.get("id") or f"hero-{int(time.time() * 1000)}-{secrets.token_hex(3)}",
            "media": media,
            "src": src or "",
            "poster": poster or "",
            "title": title or (prev.get("title") if prev else "Untitled Card"),
            "desc": desc,
            "link": link
        })

    hero_cards = refreshed
    save_cards()
    return {"ok": True, "cards": hero_cards}

@router.post("/api/admin/gallery")
def save_gallery_endpoint(body: GallerySaveRequest, auth: bool = Depends(require_admin_auth)):
    global gallery
    refreshed = []
    for it in body.items:
        prev = next((g for g in gallery if g.get("id") == it.get("id")), None)
        media = "video" if it.get("media") == "video" else "img"
        ratio = "square" if it.get("ratio") == "square" else "tall"

        src = it.get("src") or (prev.get("src") if prev else "")
        poster = it.get("poster") or (prev.get("poster") if prev else "")

        new_src = save_media(it.get("srcData"))
        if new_src:
            delete_media(src)
            src = new_src
        elif not src and it.get("srcData"):
            src = it.get("srcData")

        new_poster = save_media(it.get("posterData"))
        if new_poster:
            delete_media(poster)
            poster = new_poster
        elif not poster and it.get("posterData"):
            poster = it.get("posterData")

        if not src:
            continue

        refreshed.append({
            "id": it.get("id") or f"gal-{int(time.time() * 1000)}-{secrets.token_hex(3)}",
            "media": media,
            "ratio": ratio,
            "src": src or "",
            "poster": poster or ""
        })

    gallery = refreshed
    save_gallery_file()
    return {"ok": True, "items": gallery}

@router.post("/api/admin/upload")
def upload_media_endpoint(body: UploadMediaRequest, auth: bool = Depends(require_admin_auth)):
    url = save_media(body.fileData)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to save media file on server.")
    return {"ok": True, "url": url}
