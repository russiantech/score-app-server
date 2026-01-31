
# from fastapi import Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy import or_
# from sqlalchemy.orm import Session
# from jose import jwt, JWTError
# from app.db.session import SessionLocal
# from app.core.config import get_app_config
# from app.models.user import User
# from fastapi import Depends, HTTPException
# from app.models.user import User

# app_config = get_app_config()
# tokenUrl = f"{app_config.general_config.api_prefix}/auth/signin"
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl=tokenUrl)

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ) -> User:

#     try:
#         data = jwt.decode(
#             token,
#             app_config.security_config.auth_jwt_secret_key,
#             algorithms=[app_config.security_config.jwt_algorithm]
#         )
#         sub = data.get("sub")
#         if not sub:
#             raise HTTPException(401, "Invalid token payload")

#         # Auto-detect whether sub is numeric (id) or string (email/username/phone)
#         filters = [
#             User.username == sub,
#             User.email == sub,
#             User.phone == sub
#         ]

#         # If sub looks like an ID (digits)
#         if str(sub).isdigit():
#             filters.append(User.id == int(sub))

#         user = db.query(User).filter(or_(*filters)).first()

#     except JWTError:
#         raise HTTPException(401, "Invalid authentication token")

#     if not user:
#         raise HTTPException(401, "User not found")

#     return user



# v2

from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security.auth import decode_token
from app.models.user import User

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_optional(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None),
) -> Optional[User]:
    """
    Get current user from JWT token (optional authentication).
    Returns None if no valid token is provided.
    """
    token = None
    
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    # Then try cookie
    elif access_token:
        token = access_token
    
    # No token = no user
    if not token:
        return None
    
    try:
        # Decode token
        payload = decode_token(token, token_type="access")
        
        # Get user_id from token
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            return None
        
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        return user
        
    except Exception:
        return None


def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None),
) -> User:
    """
    Get current user from JWT token (REQUIRED authentication).
    Raises 401 if no valid token.
    """
    token = None
    
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    # Then try cookie
    elif access_token:
        token = access_token
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode token
        payload = decode_token(token, token_type="access")
        
        # Get user_id from token
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ===== ROLE CHECKERS =====
# def admin_required(user: User = Depends(get_current_user)):
#     if user.role != UserRole.admin:
#         raise HTTPException(403, "Admins only")
#     return user

# def instructor_required(user: User = Depends(get_current_user)):
#     if user.role not in [UserRole.instructor, UserRole.admin]:
#         raise HTTPException(403, "Instructors only")
#     return user

# def parent_required(user: User = Depends(get_current_user)):
#     if user.role != UserRole.parent:
#         raise HTTPException(403, "Parents only")
#     return user

# def student_required(user: User = Depends(get_current_user)):
#     if user.role != UserRole.student:
#         raise HTTPException(403, "Students only")
#     return user

# v2 - supports user's ability for multi role design.

def permission_required(permission: str):
    def wrapper(user: User = Depends(get_current_user)):
        if not user.has_permission(permission):
            raise HTTPException(403, f"Missing permission: {permission}")
        return user
    return wrapper

# - - ADMIN - -
def admin_required(user: User = Depends(get_current_user)):
    if not user.has_role("admin", "dev"):
        raise HTTPException(403, "Admins only")
    return user

# def admin_required(user = Depends(get_current_user)):
#     if not user.has_role("admin", "dev"):
#         raise HTTPException(status_code=403, detail="Admins only")
#     return user

# - - INSTRUCTOR / TUTOR- -
def tutor_required(user: User = Depends(get_current_user)):
    if not user.has_role("tutor", "admin", "dev"):
        raise HTTPException(403, "Instructors / Tutor only required")
    return user


# - - PARENT - -
def parent_required(user: User = Depends(get_current_user)):
    if not user.has_role("parent", "admin", "dev"):
        raise HTTPException(403, "Parents only required")
    return user


# - - STUDENT - -
def student_required(user: User = Depends(get_current_user)):
    if not user.has_role("student", "admin", "dev"):
        raise HTTPException(403, "Students only required")
    return user

