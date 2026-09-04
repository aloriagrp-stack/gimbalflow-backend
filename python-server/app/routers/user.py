import re
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.routers.auth import require_user
from app.config.db import is_mysql_active, get_connection, get_memory_db

router = APIRouter(prefix="/api/user", tags=["user"])

RESERVED_USERNAMES = [
    'admin', 'gimbalflow', 'gimbal', 'director', 'soul', 'soulid', 'support',
    'staff', 'official', 'moderator', 'system', 'guest', 'gimbalflowapp',
    'shriyanshaloria', 'shriyansh', 'loria', 'newuser', 'user', 'profile'
]

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None

class DeductCreditsRequest(BaseModel):
    amount: Optional[int] = 20

def validate_name(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if len(s) < 2 or len(s) > 80:
        return None
    return s

def validate_username(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    u = str(v).strip().lower()
    if not re.match(r"^[a-z0-9_.]{3,20}$", u):
        return None
    return u

@router.get("/profile")
async def get_user_profile(request: Request):
    user = await require_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized. Sign in first.")
    return user

@router.put("/profile")
async def update_user_profile(request: Request, body: ProfileUpdateRequest):
    user = await require_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized. Sign in first.")

    updates = {}
    if body.name is not None:
        valid_n = validate_name(body.name)
        if not valid_n:
            raise HTTPException(status_code=400, detail="Name must be 2-80 characters.")
        updates["name"] = valid_n

    if body.avatar_url is not None:
        v = str(body.avatar_url)
        if len(v) > 200000:
            raise HTTPException(status_code=400, detail="Avatar image is too large.")
        updates["avatar_url"] = v

    if body.username is not None:
        u = validate_username(body.username)
        if not u:
            raise HTTPException(status_code=400, detail="Username must be 3-20 characters. Letters, numbers, dots and underscores only.")
        if u in RESERVED_USERNAMES:
            raise HTTPException(status_code=400, detail="This username is reserved.")
        
        if is_mysql_active():
            try:
                conn = get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (u, user["id"]))
                    rows = cursor.fetchall()
                    if rows:
                        conn.close()
                        raise HTTPException(status_code=409, detail="This username is already taken.")
                conn.close()
            except HTTPException:
                raise
            except Exception as e:
                print("[User] MySQL username check failed:", e)
        else:
            clash = next((x for x in get_memory_db()["users"] if x.get("username") == u and x["id"] != user["id"]), None)
            if clash:
                raise HTTPException(status_code=409, detail="This username is already taken.")
        updates["username"] = u

    if not updates:
        return {"profile": user}

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
                cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s", list(updates.values()) + [user["id"]])
                conn.commit()
                cursor.execute(
                    "SELECT id, email, name, avatar_url, username, credits_balance, plan_tier FROM users WHERE id = %s",
                    (user["id"],)
                )
                updated_user = cursor.fetchone()
                conn.close()
                if updated_user:
                    return {"profile": updated_user}
        except Exception as e:
            print("[User] MySQL update failed:", e)

    # In-memory update
    memory_user = next((u for u in get_memory_db()["users"] if u["id"] == user["id"]), None)
    if memory_user:
        memory_user.update(updates)
        return {"profile": memory_user}

    user.update(updates)
    return {"profile": user}

@router.post("/deduct-credits")
async def deduct_credits(request: Request, body: DeductCreditsRequest):
    user = await require_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized. Sign in first.")

    cost = body.amount if body.amount is not None else 20

    if is_mysql_active():
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT credits_balance FROM users WHERE id = %s", (user["id"],))
                row = cursor.fetchone()
                if row:
                    current = row["credits_balance"]
                    if current < cost:
                        conn.close()
                        raise HTTPException(status_code=400, detail="Insufficient credits balance")
                    updated = current - cost
                    cursor.execute("UPDATE users SET credits_balance = %s WHERE id = %s", (updated, user["id"]))
                    conn.commit()
                    conn.close()
                    return {"credits_balance": updated}
            conn.close()
        except HTTPException:
            raise
        except Exception as e:
            print("[User] MySQL deduct credits failed:", e)

    memory_user = next((u for u in get_memory_db()["users"] if u["id"] == user["id"]), None)
    if not memory_user:
        raise HTTPException(status_code=401, detail="User not found")
    if memory_user.get("credits_balance", 0) < cost:
        raise HTTPException(status_code=400, detail="Insufficient credits balance")

    memory_user["credits_balance"] = memory_user.get("credits_balance", 0) - cost
    return {"credits_balance": memory_user["credits_balance"]}
