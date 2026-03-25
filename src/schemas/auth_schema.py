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
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    role_id: int
    iat: int
    exp: int
    jti: str
    type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class RefreshTokenResponse(BaseModel):
    access_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse (BaseModel):
    message: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)

class VerifyOTPResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8)

class ResetPasswordResponse(BaseModel):
    message: str
    
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

class UserProfileResponse(BaseModel):
    user_id: UUID
    email: str
    name: str | None
    role_id: int
    org_id: UUID | None


class LogoutResponse(BaseModel):
    message: str


class MessageResponse(BaseModel):
    message: str


class DeleteResponse(BaseModel):
    message: str


class UserCreateResponse(BaseModel):
    user_id: UUID
    email: str
    name: str | None
    role_id: int
    org_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserResponse]


class UserUpdateResponse(BaseModel):
    user_id: UUID
    email: str
    name: str | None
    role_id: int
    org_id: UUID | None

    class Config:
        from_attributes = True


class UserDeleteResponse(BaseModel):
    message: str


class RoleCreateResponse(BaseModel):
    role_id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    roles: list[RoleResponse]


class PermissionCreateResponse(BaseModel):
    permission_id: int
    entity_name: str
    action: str

    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    permissions: list[PermissionResponse]


class RefreshTokenResponse(BaseModel):
    jti: str
    session_id: str
    user_id: str
    expires_at: datetime

    class Config:
        from_attributes = True


class RevokedTokenResponse(BaseModel):
    message: str


class RotatedTokenResponse(BaseModel):
    jti: str
    session_id: str
    user_id: str
    expires_at: datetime

    class Config:
        from_attributes = True