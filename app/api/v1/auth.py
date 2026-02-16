"""
Authentication endpoints for user registration, login, password reset, and token management.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import (
    APIRouter, BackgroundTasks, Cookie, Depends, 
    Header, HTTPException, Request, Response, status
)
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.api.deps.storage import get_redis_instance, get_redis_service
from app.api.deps.users import get_current_user, get_db
from app.core.config import get_app_config
from app.core.security.auth import (
    create_access_token, create_refresh_token, decode_token
)
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordSchema, ResendVerificationSchema, ResetPasswordSchema,
    SignupSchema, VerifySignupSchema
)
from app.schemas.user import UserRead, UserSignin
from app.services.auth_service import authenticate_user
from app.services.notifications.email import (
    send_password_reset_email, send_verification_email, send_welcome_email
)
from app.services.notifications.sms import send_verification_sms
from app.services.redis_service import RedisService
from app.utils.helpers import generate_secure_code, get_client_ip
from app.utils.responses import api_response

logger = logging.getLogger(__name__)
router = APIRouter()
config = get_app_config()


@router.post("/signup")
async def signup(
    data: SignupSchema,
    request: Request,
    db: Session = Depends(get_db),
    redis: Optional[RedisService] = Depends(get_redis_service),  # Use dependency
) -> dict:
    """
    Step 1: Initiate signup process
    """
    try:
        client_ip = get_client_ip(request)
        
        # Rate limiting (skip if Redis unavailable)
        if redis:
            _, allowed = redis.increment_rate_limit(
                f"signup_initiate:{client_ip}",
                window=3600,
                limit=50
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many signup attempts. Please try again later."
                )
        else:
            logger.warning(f"⚠ Rate limiting skipped (Redis unavailable) for signup from {client_ip}")
        
        # Check for existing credentials
        existing_user = db.scalar(
            select(User).where(
                or_(
                    User.username == data.username,
                    User.email == data.email,
                    User.phone == data.phone
                )
            )
        )
        
        if existing_user:
            if existing_user.username == data.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This username is already taken."
                )
            elif existing_user.email == data.email:
                if (hasattr(existing_user, 'oauth_providers') and 
                    existing_user.oauth_providers and not existing_user.password):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="An account with this email exists via social login."
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An account with this email already exists."
                )
            elif existing_user.phone == data.phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This phone number is already registered."
                )
        
        # Generate verification codes and token
        email_code = generate_secure_code(6)
        phone_code = generate_secure_code(6)
        signup_token = secrets.token_urlsafe(32)
        
        # Store signup data in Redis (or fail gracefully)
        signup_data = {
            "username": data.username,
            "email": data.email,
            "phone": data.phone,
            "names": data.names,
            "password": data.password,
            "email_code": email_code,
            "phone_code": phone_code,
            "ip": client_ip,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Sign up: {signup_data}")
        
        # Check if Redis is available
        if not redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again in a moment."
            )
        
        redis_key = f"signup_pending:{signup_token}"
        if not redis.set(redis_key, signup_data, expiry=600):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again."
            )
        
        # Send verification codes
        email_sent = await send_verification_email(
            email=data.email,
            names=data.names,
            code=email_code
        )
        
        sms_sent = await send_verification_sms(
            phone=data.phone,
            code=phone_code
        )
        
        if not (email_sent or sms_sent):
            redis.delete(redis_key)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to send verification codes. Please try again."
            )
        
        logger.info(f"Signup initiated for {data.email} from IP {client_ip}")
        
        return api_response(
            success=True,
            message="Verification codes sent! Please check your email and phone.",
            data={
                "token": signup_token,
                "email": data.email,
                "phone": data.phone,
                "email_sent": email_sent,
                "sms_sent": sms_sent,
                "expires_in_seconds": 600
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup initiation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during signup"
        )
        
@router.post("/signup/verify")
async def verify_signup(
    data: VerifySignupSchema,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis: Optional[RedisService] = Depends(get_redis_service),  # Use dependency
) -> dict:
    """
    Step 2: Verify codes and create user account
    """
    try:
        client_ip = get_client_ip(request)
        
        # Check if Redis is available (required for verification)
        if not redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again."
            )
        
        # Rate limiting
        _, allowed = redis.increment_rate_limit(
            f"verify_signup:{client_ip}",
            window=300,
            limit=10
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many verification attempts. Please try again later."
            )
        
        if not data.email_code and not data.phone_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one verification code is required"
            )
        
        # Retrieve signup data from Redis
        redis_key = f"signup_pending:{data.token}"
        signup_data = redis.get(redis_key, as_json=True)
        
        if not signup_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification session expired. Please sign up again."
            )
        
        # Verify codes
        email_verified = False
        phone_verified = False
        
        if data.email_code:
            if signup_data.get('email_code') != data.email_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email verification code"
                )
            email_verified = True
        
        if data.phone_code:
            if signup_data.get('phone_code') != data.phone_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid phone verification code"
                )
            phone_verified = True
        
        # Final check for existing user (race condition protection)
        existing_user = db.scalar(
            select(User).where(
                or_(
                    User.username == signup_data['username'],
                    User.email == signup_data['email'],
                    User.phone == signup_data['phone']
                )
            )
        )
        
        if existing_user:
            redis.delete(redis_key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account information is already in use"
            )
        
        # Create user
        try:
            user = User(
                username=signup_data['username'],
                email=signup_data['email'],
                phone=signup_data['phone'],
                names=signup_data['names'],
                ip=signup_data['ip'],
                email_verified=email_verified,
                phone_verified=phone_verified,
                is_active=True
            )
            
            user.set_password(signup_data['password'])
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            redis.delete(redis_key)
            
            # Send welcome email
            if email_verified:
                # background_tasks.add_task(
                #     send_welcome_email,
                #     email=user.email,
                #     names=user.names or user.username
                # )
                await send_welcome_email(
                    email=user.email,
                    names=user.names or user.username,
                    background_tasks=background_tasks,
                )
            
            logger.info(f"User {user.username} created successfully")
            
            return api_response(
                success=True,
                message="Account created successfully! You can now sign in.",
                data={
                    "username": user.username,
                    "email": user.email,
                    "email_verified": email_verified,
                    "phone_verified": phone_verified
                }
            )
        
        except Exception as db_err:
            db.rollback()
            redis.delete(redis_key)
            logger.error(f"Database error during user creation: {db_err}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account. Please try again."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )

@router.post("/signup/resend")
async def resend_verification(
    data: ResendVerificationSchema,
    request: Request,
    redis: Optional[RedisService] = Depends(get_redis_service),  # Use dependency
) -> dict:
    """Resend verification code for email or phone"""
    try:
        client_ip = get_client_ip(request)
        
        # Check if Redis is available (required)
        if not redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again."
            )
        
        # Rate limiting
        _, allowed = redis.increment_rate_limit(
            f"resend_verification:{client_ip}",
            window=3600,
            limit=100
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many resend attempts. Please try again later."
            )
        
        redis_key = f"signup_pending:{data.token}"
        signup_data = redis.get(redis_key, as_json=True)
        
        if not signup_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification session expired. Please sign up again."
            )
        
        new_code = generate_secure_code(6)
        
        if data.type == "email":
            signup_data['email_code'] = new_code
            email_sent = await send_verification_email(
                email=signup_data['email'],
                names=signup_data['names'],
                code=new_code
            )
            
            if not email_sent:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send verification email"
                )
        
        elif data.type == "phone":
            signup_data['phone_code'] = new_code
            sms_sent = await send_verification_sms(
                phone=signup_data['phone'],
                code=new_code
            )
            
            if not sms_sent:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send verification SMS"
                )
        
        redis.set(redis_key, signup_data, expiry=600)
        
        logger.info(f"Verification code resent for {data.type}: {signup_data.get(data.type)}")
        
        return api_response(
            success=True,
            message=f"New {data.type} verification code sent successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend code"
        )

@router.post("/signin")
def signin(
    request: Request,
    response: Response,
    data: UserSignin,
    db: Session = Depends(get_db),
) -> dict:
    """Authenticate user and issue access/refresh tokens"""
    user = authenticate_user(db, data)

    access_token = create_access_token(
        subject={"username": user.username, "user_id": str(user.id)}
    )
    refresh_token = create_refresh_token(
        subject={"username": user.username, "user_id": str(user.id)}
    )

    cookie_params = {
        "httponly": True,
        "domain": config.hosting_config.cookie_config.domain,
        "samesite": "lax",
        "secure": not config.general_config.development_mode,
    }

    response.set_cookie(
        key="access_token_cookie",
        value=access_token,
        max_age=int(timedelta(
            minutes=config.security_config.access_token_expire_minutes
        ).total_seconds()),
        **cookie_params
    )

    response.set_cookie(
        key="refresh_token_cookie",
        value=refresh_token,
        max_age=int(timedelta(
            minutes=config.security_config.refresh_token_expire_minutes
        ).total_seconds()),
        **cookie_params
    )

    return api_response(
        success=True,
        message="Sign in successful",
        path=str(request.url.path),
        data={
            "user": user.get_summary(),
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
        }
    )


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordSchema,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis: Optional[RedisService] = Depends(get_redis_service),  # Use dependency
) -> dict:
    
    client_ip = get_client_ip(request)
    
    # Rate limiting (skip if Redis unavailable)
    if redis:
        redis.increment_rate_limit(
            f"forgot_password:{client_ip}",
            window=3600,
            limit=5
        )
    else:
        logger.warning(f"⚠ Rate limiting skipped for forgot-password from {client_ip}")

    user = db.scalar(select(User).where(User.email == data.email.lower()))

    # Always return success (security best practice)
    if not user or not user.is_active:
        return api_response(
            success=True,
            message="If an account exists, a reset code has been sent."
        )

    reset_code = generate_secure_code(6)
    
    # Store reset data in Redis if available
    if redis:
        reset_data = {
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        redis_key = f"password_reset_code:{reset_code}"
        redis.set(redis_key, reset_data, expiry=900)  # 15 minutes
        
        logger.info(f"Reset code stored: {reset_code}")
    else:
        logger.error("⚠ Cannot store reset code - Redis unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again."
        )

    background_tasks.add_task(
        send_password_reset_email,
        email=user.email,
        names=user.names or user.username,
        code=reset_code
    )

    return api_response(
        success=True,
        message="If an account exists, a reset code has been sent."
    )


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordSchema,
    request: Request,
    db: Session = Depends(get_db),
    redis: Optional[RedisService] = Depends(get_redis_service),  # Use dependency
) -> dict:
    logger.info(f"Reset password data: {data}")
    client_ip = get_client_ip(request)
    
    # Check if Redis is available (required)
    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again."
        )
    
    # Rate limiting
    redis.increment_rate_limit(
        f"reset_password:{client_ip}",
        window=300,
        limit=5
    )

    redis_key = f"password_reset_code:{data.reset_code.upper()}"
    reset_data = redis.get(redis_key, as_json=True)

    if not reset_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset code."
        )

    user = db.scalar(select(User).where(User.id == reset_data["user_id"]))

    if not user or not user.is_active:
        redis.delete(redis_key)
        raise HTTPException(status_code=400, detail="Account unavailable.")

    user.set_password(data.new_password)
    user.password_changed_at = datetime.now(timezone.utc)

    db.commit()
    redis.delete(redis_key)

    return api_response(
        success=True,
        message="Password reset successful. You can now sign in."
    )



# Removed: /reset-password/verify-token endpoint (no longer needed with code-based approach)


@router.post("/refresh-token")
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token_cookie: Optional[str] = Cookie(default=None),
    authorization: Optional[str] = Header(default=None),
) -> dict:
    """
    Refresh access token using refresh token from:
    - Cookie (refresh_token_cookie)
    - Authorization header (Bearer token)
    """
    token = refresh_token_cookie
    
    if not token and authorization:
        if authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    payload = decode_token(token, token_type="refresh")
    
    new_access_token = create_access_token(
        subject={
            "username": payload.get("username"),
            "user_id": payload.get("user_id")
        }
    )
    
    response.set_cookie(
        key="access_token_cookie",
        value=new_access_token,
        httponly=True,
        secure=not config.general_config.development_mode,
        samesite="lax",
        domain=config.hosting_config.cookie_config.domain,
        max_age=int(timedelta(
            minutes=config.security_config.access_token_expire_minutes
        ).total_seconds())
    )
    
    return api_response(
        success=True,
        message="Token refreshed successfully",
        path=str(request.url.path),
        data={
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    )


@router.get("/me")
def get_me(current_user=Depends(get_current_user)) -> dict:
    """Get current authenticated user"""
    return api_response(
        success=True,
        message="User retrieved successfully",
        data=UserRead.model_validate(current_user)
    )

@router.post("/signout")
def signout(response: Response) -> dict:
    """Sign out user by clearing authentication cookies"""
    cookie_params = {
        "domain": config.hosting_config.cookie_config.domain,
        "httponly": True,
        "secure": not config.general_config.development_mode,
        "samesite": "lax",
        "path": "/"
    }
    
    response.delete_cookie(key="access_token_cookie", **cookie_params)
    response.delete_cookie(key="refresh_token_cookie", **cookie_params)
    
    return api_response(
        success=True,
        message="Signed out successfully"
    )

