from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user_id: str
    organization_id: str
    role: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: str
    organization_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    status: str
    role_id: str
    roles: List[str] = []
    permissions: List[str] = []
    timezone: str
    language: str
    department: Optional[str] = None
    designation: Optional[str] = None
    profile_image: Optional[str] = None
    email_verified: bool = False
    mfa_enabled: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True
