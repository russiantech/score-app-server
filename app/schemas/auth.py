"""
Authentication schemas for request/response validation.
"""

import re
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# Constants for validation
MIN_PASSWORD_LENGTH = 5
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 30
MIN_NAMES_LENGTH = 2
MAX_NAMES_LENGTH = 50

PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$')
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')
NAMES_PATTERN = re.compile(r'^[a-zA-Z\s]+$')
PHONE_PATTERN = re.compile(r'^\+?[0-9]{7,15}$')


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"


class UserSignin(BaseModel):
    """User sign-in request schema"""
    username: str = Field(..., min_length=MIN_USERNAME_LENGTH)
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)


class BaseUserSchema(BaseModel):
    """Base schema for user data with common validations"""
    
    names: Optional[str] = Field(
        None,
        min_length=MIN_NAMES_LENGTH,
        max_length=MAX_NAMES_LENGTH,
        description="Full name (2-50 letters and spaces)",
        examples=["Chris James"]
    )
    
    username: str = Field(
        ...,
        min_length=MIN_USERNAME_LENGTH,
        max_length=MAX_USERNAME_LENGTH,
        description="Username (3-30 letters, numbers, underscores)",
        examples=["chrisjsm"]
    )
    
    email: EmailStr = Field(
        ...,
        description="Valid email address",
        examples=["chris@coding.com"]
    )
    
    phone: str = Field(
        ...,
        description="Phone number with country code",
        examples=["+2348012345678"]
    )
    
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=100,
        description="Password (5+ chars, uppercase, lowercase, number)",
        examples=["P@ssw0rd!"]
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not USERNAME_PATTERN.match(v):
            raise ValueError(
                'Username can only contain letters, numbers, and underscores'
            )
        return v.lower()
    
    @field_validator('names')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate names format"""
        if v and not NAMES_PATTERN.match(v):
            raise ValueError('Names can only contain letters and spaces')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f'Password must be at least {MIN_PASSWORD_LENGTH} characters'
            )
        
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                'Password must contain uppercase, lowercase, and number'
            )
        
        return v
    
    # @field_validator('phone')
    # @classmethod
    # def validate_phone(cls, v: str) -> str:
    #     """Validate phone format"""
    #     if not PHONE_PATTERN.match(v):
    #         raise ValueError('Invalid phone number format')
        
    #     if not v.startswith('+'):
    #         raise ValueError(
    #             'Phone number must include country code (e.g., +234...)'
    #         )
        
    #     return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """
        Validate phone numbers in either:
        - International format: +14155552671
        - Local numeric format: 08012345678
        """

        if not v:
            raise ValueError("Phone number is required.")

        v = v.strip().replace(" ", "")

        # Allow purely local numbers starting with 0
        if v.startswith("0") and v.isdigit():
            if len(v) < 7 or len(v) > 15:
                raise ValueError(
                    "Phone number must contain between 7 and 15 digits."
                )
            return v

        # Allow international numbers with +
        if PHONE_PATTERN.match(v):
            return v

        raise ValueError(
            "Invalid phone number format. Use a valid local number "
            "(e.g., 08012345678) or international format (e.g., +14155552671)."
        )
        
    class Config:
        extra = "forbid"


class SignupSchema(BaseUserSchema):
    """Schema for user signup"""
    pass


class UpdateUserSchema(BaseModel):
    """Schema for updating user information"""
    
    user_id: Optional[int] = None
    names: Optional[str] = Field(None, min_length=2, max_length=50)
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    image: Optional[str] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    about_me: Optional[str] = Field(None, max_length=500)
    membership: Optional[Literal["free", "premium", "vip"]] = "free"
    balance: Optional[float] = 0.0
    withdrawal_password: Optional[str] = None
    valid_email: Optional[bool] = False
    ip: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v and not USERNAME_PATTERN.match(v):
            raise ValueError(
                'Username can only contain letters, numbers, and underscores'
            )
        return v.lower() if v else None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not PHONE_PATTERN.match(v):
            raise ValueError('Invalid phone number format')
        return v


class VerifySignupSchema(BaseModel):
    """Schema for verifying signup codes"""
    
    token: str = Field(..., min_length=32, description="Signup token")
    email_code: Optional[str] = Field(
        None,
        min_length=5,
        max_length=6,
        description="Email verification code"
    )
    phone_code: Optional[str] = Field(
        None,
        min_length=5,
        max_length=6,
        description="Phone verification code"
    )
    
    @field_validator('email_code', 'phone_code')
    @classmethod
    def validate_codes(cls, v: Optional[str]) -> Optional[str]:
        """Normalize verification codes to uppercase"""
        return v.strip().upper() if v else None


class ResendVerificationSchema(BaseModel):
    """Schema for resending verification codes"""
    
    token: str = Field(..., min_length=32, description="Signup token")
    type: Literal["email", "phone"] = Field(
        ...,
        description="Type of verification to resend"
    )


class ForgotPasswordSchema(BaseModel):
    """Schema for forgot password request"""
    
    email: EmailStr = Field(..., description="Valid email address")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: EmailStr) -> str:
        """Normalize email"""
        if not v:
            raise ValueError('Email is required')
        return str(v).lower().strip()


class ResetPasswordSchema(BaseModel):
    """Schema for password reset with code"""
    
    # email: EmailStr = Field(..., description="Email address") // no longer required.
    reset_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit reset code from email"
    )
    new_password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=100,
        description="New password"
    )
    
    # @field_validator('email')
    # @classmethod
    # def validate_email(cls, v: EmailStr) -> str:
    #     """Normalize email"""
    #     return str(v).lower().strip()
    
    @field_validator('reset_code')
    @classmethod
    def validate_reset_code(cls, v: str) -> str:
        """Normalize reset code"""
        code = v.strip().upper()
        if not code.isalnum():
            raise ValueError('Reset code must contain only letters and numbers')
        return code
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f'Password must be at least {MIN_PASSWORD_LENGTH} characters'
            )
        
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                'Password must contain uppercase, lowercase, and number'
            )
        
        return v


# Removed: VerifyResetTokenSchema (no longer needed with code-based approach)
