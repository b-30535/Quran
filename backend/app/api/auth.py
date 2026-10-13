from datetime import datetime, timedelta, timezone
import logging
import re

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pydantic import BaseModel, EmailStr, Field, field_validator
from pwdlib import PasswordHash
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.database import get_database

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer(auto_error=False)
password_hasher = PasswordHash.recommended()
logger = logging.getLogger(__name__)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=2, max_length=60)

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str) -> str:
        value = " ".join(value.split()).strip()
        if not value or not re.fullmatch(r"[\w .'-]+", value, flags=re.UNICODE):
            raise ValueError("Use letters, numbers, spaces, apostrophes, periods or hyphens.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


def _create_access_token(user_id: str, email: str) -> str:
    secret = settings.jwt_secret_key.strip()
    if len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Set a strong JWT_SECRET_KEY.",
        )
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "iss": settings.jwt_issuer,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _public_user(document: dict) -> UserResponse:
    return UserResponse(
        id=str(document["_id"]),
        email=document["email"],
        display_name=document["display_name"],
        created_at=document["created_at"],
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> AuthResponse:
    """Create an account. Passwords are hashed; plaintext passwords are never stored."""
    database = get_database()
    email = str(payload.email).lower().strip()
    existing = await database.users.find_one({"email": email}, {"_id": 1})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    document = {
        "email": email,
        "display_name": payload.display_name,
        "password_hash": password_hasher.hash(payload.password),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    try:
        result = await database.users.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    document["_id"] = result.inserted_id
    token = _create_access_token(str(result.inserted_id), email)
    return AuthResponse(access_token=token, user=_public_user(document))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    """Authenticate by email/password and return a short-lived bearer token."""
    database = get_database()
    email = str(payload.email).lower().strip()
    user = await database.users.find_one({"email": email})
    # Use the same public error for unknown emails and incorrect passwords.
    if not user or not password_hasher.verify(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")

    token = _create_access_token(str(user["_id"]), email)
    return AuthResponse(access_token=token, user=_public_user(user))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    secret = settings.jwt_secret_key.strip()
    if len(secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured.")
    try:
        payload = jwt.decode(
            credentials.credentials,
            secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            options={"require": ["sub", "exp", "iat", "iss"]},
        )
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Missing subject")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Session is invalid or expired.")

    from bson import ObjectId
    from bson.errors import InvalidId

    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=401, detail="Session is invalid or expired.")

    user = await get_database().users.find_one(
        {"_id": object_id},
        {"password_hash": 0},
    )
    if not user:
        raise HTTPException(status_code=401, detail="Account no longer exists.")
    return user


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)) -> UserResponse:
    """Return the signed-in user's safe public profile."""
    return _public_user(user)
