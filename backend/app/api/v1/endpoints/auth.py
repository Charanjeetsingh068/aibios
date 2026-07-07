import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    oauth2_scheme
)
from app.models.auth import (
    User,
    Organization,
    Session as UserSession,
    RefreshToken,
    LoginHistory,
    AuditLog,
    PasswordResetToken
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    UserResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Authentication dependency to retrieve the current active user
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Query user details eager loading their organization and role with permissions
    query = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.organization), selectinload(User.role))
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    if user.organization.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is suspended"
        )
    return user

# Helper dependency to check permissions
class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        # Super admins bypass all permission gates
        if current_user.role_id == "super_admin":
            return current_user
            
        # Parse permission strings from user role
        permissions = [p.id for p in current_user.role.permissions]
        if self.required_permission in permissions or "admin:all" in permissions:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this resource"
        )

# Helper dependency to check roles
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role_id in self.allowed_roles or current_user.role_id == "super_admin":
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not permitted to access this resource"
        )

# ------------------------------------------------------------------------------
# AUTH ROUTES
# ------------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    ip_address = request.client.host if request.client else None
    device_info = request.headers.get("user-agent", "Unknown Device")

    # 1. Fetch user by email
    query = (
        select(User)
        .where(User.email == login_data.email)
        .options(selectinload(User.organization), selectinload(User.role))
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # Log failed attempt if user not found
    if not user:
        history = LoginHistory(
            email=login_data.email,
            status="failed",
            failure_reason="User not found",
            ip_address=ip_address,
            device_info=device_info
        )
        db.add(history)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # 2. Check password and active statuses
    if not verify_password(login_data.password, user.password_hash):
        history = LoginHistory(
            user_id=user.id,
            organization_id=user.organization_id,
            email=login_data.email,
            status="failed",
            failure_reason="Incorrect password",
            ip_address=ip_address,
            device_info=device_info
        )
        db.add(history)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your user account is deactivated"
        )

    if user.organization.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your tenant organization is deactivated"
        )

    # 3. Create Session
    session_expiry = datetime.utcnow() + timedelta(days=30 if login_data.remember_me else 1)
    access_token_id = str(uuid.uuid4())
    
    session = UserSession(
        user_id=user.id,
        organization_id=user.organization_id,
        access_token_id=access_token_id,
        device_info=device_info,
        ip_address=ip_address,
        is_active=True,
        expires_at=session_expiry
    )
    db.add(session)
    await db.flush()  # populate session ID

    # 4. Generate Tokens
    access_token_payload = {
        "sub": user.id,
        "org_id": user.organization_id,
        "roles": [user.role_id],
        "sid": session.id,
        "token_id": access_token_id
    }
    
    # Expires in 1 hour
    access_token_expiry = timedelta(minutes=60)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expiry
    )
    # Re-encode JWT containing full roles claims to assist client routing gates
    access_token = jwt.encode(
        {**access_token_payload, "exp": datetime.utcnow() + access_token_expiry},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    # Refresh token rotation hash
    raw_refresh_token = secrets.token_hex(32)
    refresh_token_hash = get_password_hash(raw_refresh_token)
    
    refresh_token_obj = RefreshToken(
        session_id=session.id,
        token_hash=refresh_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=30),
        is_revoked=False
    )
    db.add(refresh_token_obj)

    # Log successful login
    history = LoginHistory(
        user_id=user.id,
        organization_id=user.organization_id,
        email=login_data.email,
        status="success",
        ip_address=ip_address,
        device_info=device_info
    )
    db.add(history)

    # Update last login time
    user.last_login = datetime.utcnow()
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        expires_in=3600,
        refresh_token=raw_refresh_token,
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role_id
    )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        session_id = payload.get("sid")
        if session_id:
            # Query session and deactivate it
            query = select(UserSession).where(UserSession.id == session_id)
            result = await db.execute(query)
            session = result.scalar_one_or_none()
            if session:
                session.is_active = False
                
                # Revoke refresh tokens
                rt_query = select(RefreshToken).where(RefreshToken.session_id == session.id)
                rt_result = await db.execute(rt_query)
                for rt in rt_result.scalars():
                    rt.is_revoked = True
            await db.commit()
    except JWTError:
        pass
        
    return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    # Query refresh tokens to verify match (we query and verify using bcrypt hashes)
    query = (
        select(RefreshToken)
        .where(RefreshToken.is_revoked == False)
        .options(selectinload(RefreshToken.session).selectinload(UserSession.user).selectinload(User.organization))
    )
    result = await db.execute(query)
    all_active_tokens = result.scalars().all()

    target_token = None
    for token_obj in all_active_tokens:
        if verify_password(refresh_data.refresh_token, token_obj.token_hash):
            target_token = token_obj
            break

    if not target_token or target_token.expires_at < datetime.utcnow() or not target_token.session.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    session = target_token.session
    user = session.user

    # Revoke old refresh token (rotation enforcement)
    target_token.is_revoked = True

    # Generate new tokens
    access_token_id = str(uuid.uuid4())
    session.access_token_id = access_token_id

    access_token_payload = {
        "sub": user.id,
        "org_id": user.organization_id,
        "roles": [user.role_id],
        "sid": session.id,
        "token_id": access_token_id
    }
    
    access_token_expiry = timedelta(minutes=60)
    access_token = jwt.encode(
        {**access_token_payload, "exp": datetime.utcnow() + access_token_expiry},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    new_raw_refresh = secrets.token_hex(32)
    new_refresh_hash = get_password_hash(new_raw_refresh)

    new_refresh_token_obj = RefreshToken(
        session_id=session.id,
        token_hash=new_refresh_hash,
        expires_at=datetime.utcnow() + timedelta(days=30),
        is_revoked=False
    )
    db.add(new_refresh_token_obj)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        expires_in=3600,
        refresh_token=new_raw_refresh,
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role_id
    )

@router.post("/forgot-password")
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(User.email == forgot_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # Safe return to avoid email harvesting
    if not user:
        return {"message": "If the email is registered, a password reset link has been dispatched"}

    # Generate recovery token
    raw_token = secrets.token_urlsafe(32)
    token_hash = get_password_hash(raw_token)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(reset_token)

    # Log audit trail
    audit = AuditLog(
        user_id=user.id,
        organization_id=user.organization_id,
        action="forgot_password_request",
        description="Password reset token generated",
        resource="users",
        resource_id=user.id
    )
    db.add(audit)
    await db.commit()

    # Note: In production we dispatch via SMTP; for local E2E verification we log it to standard stdout.
    logger.info(f"== LOCAL RESET PASSWORD URL (DEVELOPMENT ONLY): http://localhost:3000/auth/reset-password?token={raw_token} ==")

    return {"message": "If the email is registered, a password reset link has been dispatched", "token_dev_only": raw_token}

@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    # Query reset tokens
    query = (
        select(PasswordResetToken)
        .where(PasswordResetToken.is_used == False)
        .options(selectinload(PasswordResetToken.user))
    )
    result = await db.execute(query)
    all_tokens = result.scalars().all()

    target_token = None
    for tok in all_tokens:
        if verify_password(reset_data.token, tok.token_hash):
            target_token = tok
            break

    if not target_token or target_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user = target_token.user
    user.password_hash = get_password_hash(reset_data.new_password)
    target_token.is_used = True

    # Audit logging
    audit = AuditLog(
        user_id=user.id,
        organization_id=user.organization_id,
        action="password_reset_success",
        description="Password reset successfully completed using token recovery",
        resource="users",
        resource_id=user.id
    )
    db.add(audit)
    await db.commit()

    return {"message": "Password updated successfully"}

@router.post("/change-password")
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not verify_password(change_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    current_user.password_hash = get_password_hash(change_data.new_password)

    # Invalidate all active user sessions for security enforcement
    q_session = select(UserSession).where(UserSession.user_id == current_user.id)
    s_result = await db.execute(q_session)
    for sess in s_result.scalars():
        sess.is_active = False

    audit = AuditLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action="change_password",
        description="User manually changed password",
        resource="users",
        resource_id=current_user.id
    )
    db.add(audit)
    await db.commit()

    return {"message": "Password changed successfully. Please log in again."}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
