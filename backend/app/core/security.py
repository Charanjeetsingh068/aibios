from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain password matches its hashed equivalent."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates a secure hash from a plain text password."""
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token containing a subject claims payload."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# ==============================================================================
# Role-Based Access Control (RBAC) Framework Skeletons
# ==============================================================================

class RoleChecker:
    """
    FastAPI dependency that enforces RBAC authorization requirements.
    
    Example usage in routes:
        @router.get("/admin-only", dependencies=[Depends(RoleChecker(["administrator"]))])
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token is missing.",
            )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            # In Phase 0 initialization, we simulate decoding and checking roles
            user_roles = payload.get("roles", [])
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload.",
                )
                
            # If the user has any of the allowed roles, proceed
            if any(role in self.allowed_roles for role in user_roles) or "administrator" in user_roles:
                return {"user_id": user_id, "roles": user_roles}
                
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this resource.",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
            )


def get_security_headers(environment: str) -> dict[str, str]:
    """
    Returns security headers based on the active environment (development or production).
    """
    # Enterprise-grade base headers
    headers = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "X-Permitted-Cross-Domain-Policies": "none",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin"
    }
    
    if environment.lower() == "development":
        # Relaxed CSP for local development to allow Swagger UI, ReDoc, and OpenAPI assets (from CDN / localhost)
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "img-src 'self' data: fastapi.tiangolo.com cdn.jsdelivr.net; "
            "connect-src 'self' http://localhost:8000 http://localhost:3000 http://127.0.0.1:8000 http://127.0.0.1:3000 ws://localhost:3000 ws://127.0.0.1:3000; "
            "frame-ancestors 'none';"
        )
    else:
        # Strict security headers for production environment
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "frame-ancestors 'none';"
        )
        
    return headers
