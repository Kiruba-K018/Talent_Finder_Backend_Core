import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import _current_user, _db
from src.core.services.auth import auth_service
from src.core.services.users import user_service
from src.schemas.auth_schema import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginResponse,
    LogoutResponse,
    RefreshTokenResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserProfileResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

logger = logging.getLogger(__name__)

otp: str = ""


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = _db,
    response: Response = None,
) -> LoginResponse:
    """Authenticate user credentials and return access/refresh tokens.

    Validates user email and password against stored credentials. Issues
    new access and refresh tokens upon successful authentication.

    Args:
        request: HTTP request object containing client information.
        form_data: OAuth2 form containing email and password.
        db: Database session for user queries.
        response: HTTP response object to set secure cookies.

    Returns:
        LoginResponse: Contains access_token, token_type, and refresh_token.

    Raises:
        HTTPException: 400 if email validation fails.
        HTTPException: 401 if credentials are incorrect.
    """
    try:
        result = await auth_service.login_service(
            request=request,
            form_data=form_data,
            db=db,
            response=response,
        )
        return LoginResponse(
            access_token=result.get("access_token"),
            token_type="bearer",
            refresh_token=result.get("refresh_token"),
        )

    except auth_service.EmailValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e


@auth_router.post("/refresh", response_model=RefreshTokenResponse)
async def token_rotation(
    request: Request,
    response: Response,
    db: AsyncSession = _db,
) -> RefreshTokenResponse:
    """Rotate refresh token and issue new access token.

    Validates the current refresh token from cookies and issues a new
    access token. This implements token rotation for enhanced security.

    Args:
        request: HTTP request object containing refresh token cookie.
        response: HTTP response object to set new cookies.
        db: Database session for token validation.

    Returns:
        RefreshTokenResponse: Contains new access_token.

    Raises:
        HTTPException: 401 if refresh token is invalid or expired.
    """
    try:
        result = await auth_service.token_rotation_service(
            request=request, response=response, db=db
        )
        return RefreshTokenResponse(access_token=result["access_token"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e


@auth_router.post("/logout", status_code=200, response_model=LogoutResponse)
async def logout(
    response: Response,
    current_user=_current_user,
    db: AsyncSession = _db,
) -> LogoutResponse:
    """Revoke current user session and clear authentication tokens.

    Invalidates the user's current refresh token and clears authentication
    cookies, effectively logging out the user.

    Args:
        response: HTTP response object to clear cookies.
        current_user: Currently authenticated user from token.
        db: Database session for token revocation.

    Returns:
        LogoutResponse: Confirmation message of successful logout.
    """
    await auth_service.logout(current_user, db)
    return LogoutResponse(message="Logged out successfully")


@auth_router.post(
    "/forgot-password",
    status_code=200,
    response_model=ForgotPasswordResponse,
)
async def forgot_password(
    request: ForgotPasswordRequest, db: AsyncSession = _db
) -> ForgotPasswordResponse:
    """Initiate password reset by sending OTP to registered email.

    Validates user email existence and sends a one-time password (OTP)
    to the registered email address for password reset verification.

    Args:
        request: ForgotPasswordRequest containing user email.
        db: Database session for user lookup.

    Returns:
        ForgotPasswordResponse: Confirmation message that OTP was sent.

    Raises:
        HTTPException: 404 if email is not registered.
    """
    result = await auth_service.forgot_password(request, db)
    return ForgotPasswordResponse(message=result["message"])


@auth_router.post("/verify-otp", status_code=200, response_model=VerifyOTPResponse)
async def verify_otp(
    request: VerifyOTPRequest, db: AsyncSession = _db
) -> VerifyOTPResponse:
    """Validate one-time password sent to user email.

    Verifies that the OTP provided by the user matches the one sent
    to their email address. Confirms user identity before password reset.

    Args:
        request: VerifyOTPRequest containing email and OTP.
        db: Database session for OTP validation.

    Returns:
        VerifyOTPResponse: Confirmation message of OTP verification.

    Raises:
        HTTPException: 400 if OTP is invalid or expired.
    """
    result = await auth_service.verify_otp(request, db)
    return VerifyOTPResponse(message=result["message"])


@auth_router.post(
    "/reset-password",
    status_code=200,
    response_model=ResetPasswordResponse,
)
async def reset_password(
    request: ResetPasswordRequest, db: AsyncSession = _db
) -> ResetPasswordResponse:
    """Complete password reset with verified OTP and new password.

    Updates user password after OTP verification. Must be called after
    successful OTP verification from the verify-otp endpoint.

    Args:
        request: ResetPasswordRequest containing email, OTP, and new_password.
        db: Database session for password update.

    Returns:
        ResetPasswordResponse: Confirmation message of password reset.

    Raises:
        HTTPException: 404 if user not found.
        HTTPException: 400 if password does not meet requirements.
    """
    user = await user_service.get_user_profile(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    hashed_password = auth_service.hash_password(request.new_password)
    await user_service.update_user_profile(
        db, str(user.user_id), hashed_password=hashed_password
    )

    return ResetPasswordResponse(message="Password reset successfully")


@auth_router.get("/me", status_code=200, response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user=_current_user, db: AsyncSession = _db
) -> UserProfileResponse:
    """Retrieve authenticated user profile information.

    Returns detailed profile information for the currently authenticated user.
    Requires valid authentication token.

    Args:
        current_user: Currently authenticated user from token.
        db: Database session for profile retrieval.

    Returns:
        UserProfileResponse: User details including email, name, role, org.

    Raises:
        HTTPException: 401 if authentication token is invalid.
    """
    user = await user_service.get_current_user_profile_service(current_user, db)
    return UserProfileResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        role_id=user.role_id,
        org_id=user.org_id,
    )
