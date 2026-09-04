import time
import httpx
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.config.settings import settings
from app.config.db import is_mysql_active, get_connection, get_memory_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

token_cache: Dict[str, Dict[str, Any]] = {}
NEW_USER_CREDITS = 2000
NEW_USER_PLAN = "Free"

class VerifyRequest(BaseModel):
    idToken: str

def bearer_token(request: Request) -> Optional[str]:
    header = request.headers.get("authorization") or ""
    if not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    return token or None

async def verify_google_token(id_token: str) -> Optional[Dict[str, Any]]:
    if not isinstance(id_token, str) or len(id_token) < 20:
        return None

    now = time.time()
    cached = token_cache.get(id_token)
    if cached and cached.get("exp", 0) > now - 60:
        return cached

    payload = None
    api_key = settings.FIREBASE_API_KEY

    # 1. Primary: Firebase identitytoolkit lookup
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}",
                    json={"idToken": id_token}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    users = data.get("users", [])
                    if users:
                        u = users[0]
                        provider_info = u.get("providerUserInfo", [])
                        google_info = next((p for p in provider_info if p.get("providerId") == "google.com"), {})
                        exp = int(u.get("expiresAt", 0)) // 1000 if u.get("expiresAt") else 0
                        payload = {
                            "sub": str(u.get("localId", ""))[:64],
                            "email": str(u.get("email", "")).lower(),
                            "name": (u.get("displayName") or "")[:80],
                            "picture": google_info.get("photoUrl") or u.get("photoUrl") or "",
                            "exp": exp
                        }
        except Exception as err:
            print("[Auth] identitytoolkit lookup warning:", err)

    # 2. Fallback: Google public tokeninfo endpoint
    if not payload:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
                if resp.status_code == 200:
                    info = resp.json()
                    if info.get("sub") and info.get("email"):
                        payload = {
                            "sub": str(info["sub"])[:64],
                            "email": str(info["email"]).lower(),
                            "name": (info.get("name") or "")[:80],
                            "picture": (info.get("picture") or "")[:512],
                            "exp": int(info.get("exp", 0))
                        }
        except Exception as err:
            print("[Auth] tokeninfo lookup warning:", err)

    if not payload:
        return None

    token_cache[id_token] = payload
    if len(token_cache) > 500:
        expired_keys = [k for k, v in token_cache.items() if v.get("exp", 0) < now]
        for k in expired_keys:
            token_cache.pop(k, None)

    return payload

def id_from_sub(sub: str) -> str:
    return f"usr-{sub}"

def derive_username(email: str) -> Optional[str]:
    base = str(email or "").split("@")[0] or ""
    import re
    cleaned = re.sub(r"[^a-z0-9_.]", "", base.lower())[:20]
    return cleaned or None

def upsert_user(google_user: Dict[str, Any]) -> Dict[str, Any]:
    uid = id_from_sub(google_user["sub"])
    email = google_user["email"]
    name = google_user.get("name") or "New User"
    avatar_url = google_user.get("picture") or ""
    username = derive_username(email)

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (id, email, name, avatar_url, username, credits_balance, plan_tier)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE email = VALUES(email)
                    """,
                    (uid, email, name, avatar_url, username, NEW_USER_CREDITS, NEW_USER_PLAN)
                )
                conn.commit()
                cursor.execute(
                    "SELECT id, email, name, avatar_url, username, credits_balance, plan_tier FROM users WHERE id = %s",
                    (uid,)
                )
                user = cursor.fetchone()
                conn.close()
                if user:
                    return user
        except Exception as err:
            print("[Auth] MySQL upsert failed, falling back to memory:", err)

    # In-memory fallback
    memory = get_memory_db()
    user = next((u for u in memory["users"] if u["id"] == uid or u["email"] == email), None)
    if not user:
        user = {
            "id": uid,
            "email": email,
            "name": name,
            "avatar_url": avatar_url,
            "username": username,
            "credits_balance": NEW_USER_CREDITS,
            "plan_tier": NEW_USER_PLAN
        }
        memory["users"].append(user)
    else:
        if user["id"] != uid:
            user["id"] = uid
        if not user.get("username"):
            user["username"] = username
        if not user.get("name"):
            user["name"] = name
        if not user.get("avatar_url") and avatar_url:
            user["avatar_url"] = avatar_url

    return dict(user)

async def require_user(request: Request) -> Optional[Dict[str, Any]]:
    token = bearer_token(request)
    if not token:
        return None
    google_user = await verify_google_token(token)
    if not google_user:
        return None
    return upsert_user(google_user)

@router.post("/verify")
async def verify(req: VerifyRequest):
    google_user = await verify_google_token(req.idToken)
    if not google_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired Google token.")
    profile = upsert_user(google_user)
    return {"ok": True, "profile": profile}

@router.get("/me")
async def me(request: Request):
    profile = await require_user(request)
    if not profile:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized. Sign in again.")
    return {"profile": profile}
