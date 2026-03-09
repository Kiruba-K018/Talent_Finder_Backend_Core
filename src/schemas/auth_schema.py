from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role_id: int
    iat: int
    exp: int
    jti: str
    type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8)


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    role_id: int
    org_id: UUID | None = None


class UserResponse(BaseModel):
    user_id: UUID
    email: str
    name: str | None
    role_id: int
    org_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class RoleRequest(BaseModel):
    role: str


class RoleResponse(BaseModel):
    role_id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionRequest(BaseModel):
    entity_name: str
    action: str


class PermissionResponse(BaseModel):
    permission_id: int
    entity_name: str
    action: str

    class Config:
        from_attributes = True


class OrganizationRequest(BaseModel):
    org_name: str
    org_logo: str | None = None


class OrganizationResponse(BaseModel):
    org_id: UUID
    org_name: str
    org_logo: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: str | None = None
    org_id: UUID | None = None
