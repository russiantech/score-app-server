# from datetime import datetime, timedelta
# from jose import jwt
# from app.core.config import get_app_config

# app_config = get_app_config()

# def create_access_token(subject: str):
#     expire = datetime.now() + timedelta(minutes=app_config.security_config.access_token_expire_minutes)
#     return jwt.encode(
#         {"sub": subject, "exp": expire}, 
#         app_config.security_config.auth_jwt_secret_key, 
#         algorithm=app_config.security_config.jwt_algorithm
#         )


# v2

# # app/core/security.py
# from datetime import datetime, timedelta
# from jose import jwt
# from fastapi_jwt import JwtAccessBearer, JwtRefreshBearer
# from app.core.config import get_app_config

# config = get_app_config()

# # JWT Access Token
# jwt_access_security = JwtAccessBearer(
#     secret_key=config.security_config.auth_jwt_secret_key,
#     auto_error=True
# )

# # JWT Refresh Token
# jwt_refresh_security = JwtRefreshBearer(
#     secret_key=config.security_config.auth_jwt_secret_key,
#     auto_error=True
# )


# def create_access_token(subject: str) -> str:
#     """Create JWT access token."""
#     expire = datetime.utcnow() + timedelta(
#         minutes=config.security_config.access_token_expire_minutes
#     )
    
#     to_encode = {
#         "sub": subject,
#         "exp": expire,
#         "type": "access"
#     }
    
#     encoded_jwt = jwt.encode(
#         to_encode,
#         config.security_config.auth_jwt_secret_key,
#         algorithm=config.security_config.jwt_algorithm
#     )
    
#     return encoded_jwt

# v3
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import get_app_config

# Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get config
config = get_app_config()
SECRET_KEY = config.security_config.auth_jwt_secret_key
ALGORITHM = config.security_config.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = config.security_config.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_MINUTES = config.security_config.refresh_token_expire_minutes


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify a password against a hash."""
#     return pwd_context.verify(plain_password, hashed_password)


# def get_password_hash(password: str) -> str:
#     """Hash a password."""
#     return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, dict], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        subject: User identifier (user_id, username, email, or dict with user data)
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # If subject is a dict, use it as-is; otherwise wrap in dict
    if isinstance(subject, dict):
        to_encode = subject.copy()
    else:
        to_encode = {"sub": str(subject)}
    
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, dict],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token.
    
    Args:
        subject: User identifier
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    if isinstance(subject, dict):
        to_encode = subject.copy()
    else:
        to_encode = {"sub": str(subject)}
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str, token_type: str = "access") -> dict:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type (access or refresh)
    
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise credentials_exception
        
        return payload
        
    except JWTError:
        raise credentials_exception


