from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Response, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from src.config.settings import setting
from src.data.repositories.postgres import user_crud, token_crud


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



def create_access_token(user_id: str, role_id: int) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=setting.access_expire_min)
    jti = str(uuid4())
    
    payload = {
        "sub": user_id,
        "role_id": role_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
        "type": "access"
    }
    
    token = jwt.encode(
        payload,
        setting.access_secret,
        algorithm=setting.algorithm
    )
    return token


async def create_refresh_token(
    session: AsyncSession,
    user_id: str,
    role_id: int
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=setting.refresh_expire_min)
    
    token_record = await token_crud.create_refresh_token(
        session,
        user_id,
        exp
    )
    
    jti = str(token_record.jti)
    
    payload = {
        "sub": user_id,
        "role_id": role_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
        "type": "refresh"
    }
    
    token = jwt.encode(
        payload,
        setting.refresh_secret,
        algorithm=setting.algorithm
    )
    return token


def encode_refresh_token(user_id: str, role_id: int, jti: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=setting.refresh_expire_min)
    
    payload = {
        "sub": user_id,
        "role_id": role_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
        "type": "refresh"
    }
    
    token = jwt.encode(
        payload,
        setting.refresh_secret,
        algorithm=setting.algorithm
    )
    return token


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            setting.access_secret,
            algorithms=[setting.algorithm]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            setting.refresh_secret,
            algorithms=[setting.algorithm]
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


async def verify_refresh_token(
    session: AsyncSession,
    token: str
) -> dict:
    payload = decode_refresh_token(token)
    if not payload:
        return None
    
    jti = payload.get("jti")
    is_revoked = await token_crud.is_token_revoked(session, jti)
    if is_revoked:
        return None
    
    token_record = await token_crud.get_refresh_token(session, jti)
    if not token_record:
        return None
    
    if token_record.expires_at < datetime.now(timezone.utc):
        return None
    
    return payload


async def verify_access_token(
    session: AsyncSession,
    token: str
) -> dict:
        payload = decode_access_token(token)
        if not payload:
            raise ValueError("Invalid or expired access token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload: missing user_id")
        
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise ValueError("Invalid token payload: invalid user_id format")
        
        user = await user_crud.get_user_by_id(session, user_uuid)
        if not user:
            raise ValueError(f"User not found for token user_id: {user_id}")
        
        return payload



async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str
):
    user = await user_crud.get_user_by_email(session, email)
    if not user:
        # caller will translate into unauthorized
        raise ValueError("authentication failed: user not found")
    
    if not verify_password(password, user.hashed_password):
        raise ValueError("authentication failed: incorrect password")
    
    return user


async def logout_user(session: AsyncSession, jti: str):
    success = await token_crud.revoke_refresh_token(session, jti)
    if not success:
        raise ValueError(f"logout failed: token {jti} not found or already revoked")
    return success


# ---------------------------------------------------------------------------
# higher‑level helpers used by route handlers (thin service layer)
# ---------------------------------------------------------------------------

class EmailValidationError(ValueError):
    """Raised when an email address fails basic validation checks."""


async def login_service(
    request,
    form_data: OAuth2PasswordRequestForm,
    db: AsyncSession,
    response: Response = None,
):
    

    email = form_data.username
    password = form_data.password

    # simple sanity check – callers expect ``EmailValidationError``
    if "@" not in email or email.strip().startswith("@"):
        raise EmailValidationError("Invalid email address")

    user = await authenticate_user(db, email, password)

    access_token = create_access_token(str(user.user_id), user.role_id)
    refresh_token = await create_refresh_token(db, str(user.user_id), user.role_id)

    if response is not None:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=setting.refresh_expire_min * 60,
            httponly=True,
            secure=True,
            samesite="strict",
        )

    return {"access_token": access_token, "refresh_token": refresh_token}


async def token_rotation_service(request, response: Response, db: AsyncSession):
    """Rotate a refresh token stored in a cookie and return a fresh access
    token.  This duplicates the logic that used to live in the router but
    keeps it out of the endpoint so tests can call it directly.

    The implementation mirrors the original ``/refresh`` handler.

    ``db`` is passed in from the caller so that dependency injection can be
    used; the original snippet omitted it, but adding the session makes the
    service easier to test and avoids complicated session management inside
    the service itself.
    """

    # extract token from cookie
    token = request.cookies.get("refresh_token")
    if not token:
        raise ValueError("refresh token missing")

    payload = decode_refresh_token(token)
    if not payload:
        raise ValueError("invalid refresh token")

    user_id = payload.get("sub")
    role_id = payload.get("role_id")
    old_jti = payload.get("jti")

    # make sure user exists
    user = await user_crud.get_user_by_id(db, user_id)
    if not user:
        raise ValueError("user not found during token rotation")

    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=setting.refresh_expire_min)

    new_token_record = await token_crud.rotate_refresh_token(db, old_jti, user_id, exp)
    if not new_token_record:
        raise ValueError("failed to refresh token")

    new_refresh_token = encode_refresh_token(user_id, role_id, str(new_token_record.jti))

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=setting.refresh_expire_min * 60,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    access_token = create_access_token(user_id, role_id)
    return {"access_token": access_token}

