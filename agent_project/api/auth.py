import sqlite3
import os
import hashlib
import hmac
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, HTTPException, status, Header

router = APIRouter(prefix="/auth", tags=["Authentication"])

DB_PATH = "/tmp/users.db" if os.getenv("VERCEL") else "users.db"
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_agent_project_key_2026")

class UserAuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        stripped = v.strip()
        # Allow alphanumeric, '@', '.', '_', '-' to support email usernames
        if not all(c.isalnum() or c in "@._-" for c in stripped):
            raise ValueError("Username must be alphanumeric or a valid email address.")
        return stripped

# Database Initializer
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        conn.commit()

# Cryptographic password hashing
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + key.hex()

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, key_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return new_key == key
    except Exception:
        return False

# Cryptographic signed tokens
def generate_token(username: str) -> str:
    signature = hmac.new(SECRET_KEY.encode(), username.encode(), hashlib.sha256).hexdigest()
    return f"{username}:{signature}"

def verify_token(token: str) -> bool:
    try:
        if not token:
            return False
        # Handle Bearer token prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        username, signature = token.split(":", 1)
        expected = hmac.new(SECRET_KEY.encode(), username.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False

def get_username_from_token(token: str) -> str:
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        if verify_token(token):
            return token.split(":", 1)[0]
    except Exception:
        pass
    return None

# Initialize Database on module load
init_db()

@router.post("/register")
async def register(payload: UserAuthRequest):
    username = payload.username
    password = payload.password
    
    password_hash = hash_password(password)
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
        return {"status": "success", "message": "User registered successfully."}
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists."
        )

@router.post("/login")
async def login(payload: UserAuthRequest):
    username = payload.username
    password = payload.password
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
    
    if not row or not verify_password(password, row[0]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )
        
    token = generate_token(username)
    return {
        "status": "success",
        "username": username,
        "token": token
    }

@router.get("/me")
async def get_me(authorization: str = Header(None)):
    if not authorization or not verify_token(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing session token."
        )
    username = get_username_from_token(authorization)
    return {"status": "success", "username": username}
