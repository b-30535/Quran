import os, json, base64, hashlib, hmac, secrets, time
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
import psycopg
from psycopg.rows import dict_row

app = FastAPI(title="Noor Al-Quran API", version="0.1.0")
allowed = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed, allow_credentials=False, allow_methods=["GET","POST","PUT","DELETE","OPTIONS"], allow_headers=["Authorization","Content-Type"])

def db():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise HTTPException(503, "Database is not configured. Set DATABASE_URL in the development environment.")
    return psycopg.connect(url, row_factory=dict_row, connect_timeout=5)

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS user_items (
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_type TEXT NOT NULL CHECK (item_type IN ('favorite','bookmark','progress')),
            item_key TEXT NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY(user_id,item_type,item_key)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS user_preferences (
            user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            reminder_time TEXT,
            reminder_enabled BOOLEAN NOT NULL DEFAULT false,
            timezone TEXT NOT NULL DEFAULT 'Asia/Karachi',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")

def password_hash(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or secrets.token_bytes(16)
    value = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(value).decode()

def password_ok(password: str, stored: str) -> bool:
    try:
        scheme, salt, expected = stored.split("$")
        if scheme != "scrypt": return False
        actual = password_hash(password, base64.urlsafe_b64decode(salt + "===")).split("$")[2]
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def token_for(user_id: str) -> str:
    secret = os.getenv("AUTH_SECRET")
    if not secret:
        raise HTTPException(503, "Authentication is not configured. Set AUTH_SECRET in the development environment.")
    head = b64(json.dumps({"alg":"HS256","typ":"JWT"},separators=(",",":")).encode())
    body = b64(json.dumps({"sub":user_id,"iat":int(time.time()),"exp":int(time.time())+60*60*24*7},separators=(",",":")).encode())
    sig = b64(hmac.new(secret.encode(),(head+"."+body).encode(),hashlib.sha256).digest())
    return head+"."+body+"."+sig

def current_user(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in required.")
    try:
        token = authorization[7:].split(".")
        secret = os.getenv("AUTH_SECRET")
        if not secret or len(token)!=3: raise ValueError()
        expected=b64(hmac.new(secret.encode(),(token[0]+"."+token[1]).encode(),hashlib.sha256).digest())
        if not hmac.compare_digest(expected,token[2]): raise ValueError()
        claims=json.loads(base64.urlsafe_b64decode(token[1]+"==="))
        if int(claims["exp"]) < int(time.time()): raise ValueError()
        return str(claims["sub"])
    except Exception:
        raise HTTPException(401, "Session expired or invalid. Please sign in again.")

class RegisterBody(BaseModel):
    name: str = Field(min_length=2,max_length=80)
    email: EmailStr
    password: str = Field(min_length=8,max_length=128)
class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8,max_length=128)
class ItemBody(BaseModel):
    item_type: str = Field(pattern="^(favorite|bookmark|progress)$")
    item_key: str = Field(min_length=1,max_length=40)
class PreferenceBody(BaseModel):
    reminder_time: Optional[str] = Field(default=None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    reminder_enabled: bool = False
    timezone: str = Field(default="Asia/Karachi",max_length=64)

@app.get("/api/health")
def health():
    return {"ok": True, "service": "noor-al-quran-api", "database_configured": bool(os.getenv("DATABASE_URL"))}

@app.post("/api/auth/register")
def register(body: RegisterBody):
    init_db()
    email = body.email.lower().strip()
    try:
        with db() as c:
            row = c.execute("INSERT INTO users(name,email,password_hash) VALUES(%s,%s,%s) RETURNING id,name,email", (body.name.strip(),email,password_hash(body.password))).fetchone()
            c.execute("INSERT INTO user_preferences(user_id) VALUES(%s) ON CONFLICT DO NOTHING",(row["id"],))
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "An account with this email already exists.")
    return {"token":token_for(str(row["id"])),"user":{"id":str(row["id"]),"name":row["name"],"email":row["email"]}}

@app.post("/api/auth/login")
def login(body: LoginBody):
    init_db()
    with db() as c:
        row=c.execute("SELECT id,name,email,password_hash FROM users WHERE email=%s",(body.email.lower().strip(),)).fetchone()
    if not row or not password_ok(body.password,row["password_hash"]):
        raise HTTPException(401,"Email or password is incorrect.")
    return {"token":token_for(str(row["id"])),"user":{"id":str(row["id"]),"name":row["name"],"email":row["email"]}}

@app.get("/api/me")
def me(authorization: Optional[str]=Header(default=None)):
    uid=current_user(authorization); init_db()
    with db() as c:
        row=c.execute("SELECT id,name,email,created_at FROM users WHERE id=%s",(uid,)).fetchone()
    if not row: raise HTTPException(401,"Account not found.")
    row["id"]=str(row["id"])
    return {"user":row}

@app.get("/api/me/items")
def get_items(authorization: Optional[str]=Header(default=None)):
    uid=current_user(authorization); init_db()
    with db() as c:
        rows=c.execute("SELECT item_type,item_key FROM user_items WHERE user_id=%s",(uid,)).fetchall()
    return {"items":[dict(r) for r in rows]}

@app.put("/api/me/items")
def put_item(body: ItemBody, authorization: Optional[str]=Header(default=None)):
    uid=current_user(authorization); init_db()
    if not __import__("re").fullmatch(r"\d{1,3}:\d{1,3}",body.item_key):
        raise HTTPException(422,"item_key must be a Surah:Ayah pair.")
    surah,ayah=map(int,body.item_key.split(":"))
    if not (1<=surah<=114 and 1<=ayah<=286): raise HTTPException(422,"Surah or ayah number is out of range.")
    with db() as c:
        c.execute("INSERT INTO user_items(user_id,item_type,item_key) VALUES(%s,%s,%s) ON CONFLICT(user_id,item_type,item_key) DO UPDATE SET updated_at=now()",(uid,body.item_type,body.item_key))
    return {"ok":True}

@app.delete("/api/me/items")
def delete_item(item_type: str, item_key: str, authorization: Optional[str]=Header(default=None)):
    uid=current_user(authorization); init_db()
    with db() as c: c.execute("DELETE FROM user_items WHERE user_id=%s AND item_type=%s AND item_key=%s",(uid,item_type,item_key))
    return {"ok":True}

@app.get("/api/me/preferences")
def get_preferences(authorization: Optional[str]=Header(default=None)):
    uid=current_user(authorization); init_db()
    with db() as c:
        row=c.execute("SELECT reminder_time,reminder_enabled,timezone FROM user_preferences WHERE user_id=%s",(uid,)).fetchone()
    return {"preferences":row or {"reminder_time":None,"reminder_enabled":False,"timezone":"Asia/Karachi"}}

@app.put("/api/me/preferences")
def set_preferences(body: PreferenceBody, authorization: Optional[str]=Header(default=None)):
    uid=current_user(authorization); init_db()
    with db() as c:
        c.execute("INSERT INTO user_preferences(user_id,reminder_time,reminder_enabled,timezone) VALUES(%s,%s,%s,%s) ON CONFLICT(user_id) DO UPDATE SET reminder_time=excluded.reminder_time,reminder_enabled=excluded.reminder_enabled,timezone=excluded.timezone,updated_at=now()",(uid,body.reminder_time,body.reminder_enabled,body.timezone))
    return {"ok":True,"preferences":body.model_dump()}
