"""Supabase JWT validation dependency for FastAPI."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from config import get_settings

security = HTTPBearer()


class CurrentUser(BaseModel):
    """Extracted user context from the Supabase JWT."""
    user_id: str
    email: str
    role: str | None = None
    institution_id: str | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """Validate Supabase JWT and extract user claims.

    The JWT is signed by Supabase using the project's JWT secret.
    We decode it locally (no network call) for speed.
    """
    settings = get_settings()
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    email = payload.get("email", "")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
        )

    # Role and institution_id come from user_metadata (set during registration)
    # or from app_metadata (set by the backend after profile creation)
    metadata = payload.get("user_metadata", {})
    app_metadata = payload.get("app_metadata", {})

    return CurrentUser(
        user_id=user_id,
        email=email,
        role=app_metadata.get("role") or metadata.get("role"),
        institution_id=app_metadata.get("institution_id") or metadata.get("institution_id"),
    )
