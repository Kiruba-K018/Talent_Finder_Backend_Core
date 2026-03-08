from fastapi import APIRouter, HTTPException, Depends, Response, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.data.clients.postgres_client import get_db
from src.data.clients.mongodb_client import get_db as get_mongo_db
from src.schemas.auth_schema import (
    LoginResponse,
    RegisterRequest,
    ForgotPasswordRequest,
    VerifyOTPRequest,
    ResetPasswordRequest,
)
from src.core.services.auth import auth_service
# import the new thin services
from src.core.services.auth.auth_service import (
    login_service,
    token_rotation_service,
    EmailValidationError,
)
from src.core.services.users import user_service
from src.core.services.role_permission import role_permission_service
from src.api.rest.dependencies import (
    get_current_user)
from datetime import timedelta
from src.config.settings import setting


auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@auth_router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    response: Response = None,
):
    """Login delegate to service layer."""
    try:
        result = await login_service(
            request=request,
            form_data=form_data,
            db=db,
            response=response,
        )
        return {
            "access_token": result.get("access_token"),
            "token_type": "bearer",
            "refresh_token": result.get("refresh_token")
        }

    except EmailValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@auth_router.post("/register", status_code=201)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    existing_user = await user_service.get_user_profile(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    default_role = await role_permission_service.get_role_by_name(db, "Recruiter")
    
    if not default_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default role not found. Please contact administrator."
        )
    
    try:
        user = await user_service.create_new_user(
            db,
            email=request.email,
            password=request.password,
            role_id=default_role.role_id,
            name=request.name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    
    return {"message": "User registered successfully", "user_id": str(user.user_id)}


@auth_router.post("/refresh")
async def token_rotation(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await token_rotation_service(request=request, response=response, db=db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@auth_router.post("/logout", status_code=200)
async def logout(
    response: Response,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="strict"
    )
    
    return {"message": "Successfully logged out"}


@auth_router.post("/forgot-password", status_code=200)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_user_profile(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    import random
    otp = str(random.randint(100000, 999999))
    
    return {"message": "OTP sent to your email", "otp": otp}


@auth_router.post("/verify-otp", status_code=200)
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_user_profile(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "OTP verified successfully", "valid": True}


@auth_router.post("/reset-password", status_code=200)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_user_profile(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    hashed_password = auth_service.hash_password(request.new_password)
    await user_service.update_user_profile(
        db,
        str(user.user_id),
        hashed_password=hashed_password
    )
    
    return {"message": "Password reset successfully"}
