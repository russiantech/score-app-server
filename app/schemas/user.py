# # ============================================================================
# # SCHEMAS - User
# # FILE: app/schemas/user.py
# # ============================================================================

# import re
# from datetime import datetime
# from typing import List, Optional
# from uuid import UUID

# from pydantic import BaseModel, EmailStr, Field, field_validator


# # ============================================================================
# # Constants & Regex
# # ============================================================================

# USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._-]+$")
# USERNAME_UPDATE_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")
# PHONE_LOCAL_REGEX = re.compile(r"^\d{7,11}$")
# PHONE_INTL_REGEX = re.compile(r"^\+?[0-9]{10,15}$")

# ALLOWED_ROLES = {"student", "tutor", "parent", "admin", "super_admin"}


# # ============================================================================
# # Shared Validators (DRY)
# # ============================================================================

# def normalize_username(value: str, regex: re.Pattern) -> str:
#     if not regex.match(value):
#         raise ValueError("Invalid username format")
#     return value.lower()


# def normalize_phone(value: Optional[str]) -> Optional[str]:
#     if not value:
#         return None

#     cleaned = re.sub(r"[^\d+]", "", value)

#     if PHONE_LOCAL_REGEX.match(cleaned):
#         return cleaned

#     if PHONE_INTL_REGEX.match(cleaned):
#         return cleaned

#     raise ValueError("Invalid phone number format")


# def validate_roles_list(roles: List[str]) -> List[str]:
#     for role in roles:
#         if role not in ALLOWED_ROLES:
#             raise ValueError(f"Invalid role: {role}")
#     return roles


# def validate_stripped_optional(value: Optional[str]) -> Optional[str]:
#     if not value:
#         return None
#     return value.strip()


# # ============================================================================
# # Base Schema
# # ============================================================================

# class UserBase(BaseModel):
#     username: str = Field(..., min_length=3, max_length=200)
#     names: str = Field(..., min_length=3, max_length=200)
#     email: EmailStr
#     phone: Optional[str] = Field(None, max_length=20)
#     roles: List[str] = Field(default_factory=lambda: ["student"])
#     parent_id: Optional[UUID] = None
#     is_active: Optional[bool] = None

#     @field_validator("username")
#     @classmethod
#     def validate_username(cls, v: str) -> str:
#         return normalize_username(v, USERNAME_REGEX)

#     @field_validator("phone")
#     @classmethod
#     def validate_phone(cls, v: Optional[str]) -> Optional[str]:
#         return normalize_phone(v)

#     @field_validator("roles")
#     @classmethod
#     def validate_roles(cls, v: List[str]) -> List[str]:
#         return validate_roles_list(v)


# # ============================================================================
# # Create Schema
# # ============================================================================

# class UserCreate(UserBase):
#     password: str = Field(..., min_length=5)

#     @field_validator("password")
#     @classmethod
#     def validate_password(cls, v: str) -> str:
#         if len(v) < 4:
#             raise ValueError("Password must be at least 4 characters long")
#         if not re.search(r"[A-Z]", v):
#             raise ValueError("Password must contain at least one uppercase letter")
#         if not re.search(r"[a-z]", v):
#             raise ValueError("Password must contain at least one lowercase letter")
#         if not re.search(r"\d", v):
#             raise ValueError("Password must contain at least one digit")
#         return v

#     @field_validator("parent_id", mode="before")
#     @classmethod
#     def empty_string_to_none(cls, v):
#         return None if v in ("", None) else v


# # ============================================================================
# # Update Schema
# # ============================================================================

# class UserUpdateSchema(BaseModel):
#     """
#     Partial update schema.
#     Only validates fields when provided.
#     """

#     username: Optional[str] = Field(None, min_length=3, max_length=30)
#     email: Optional[EmailStr] = None
#     names: Optional[str] = Field(None, min_length=2, max_length=100)
#     phone: Optional[str] = Field(None, max_length=20)
#     bio: Optional[str] = Field(None, max_length=500)
#     avatar_url: Optional[str] = Field(None, max_length=500)

#     password: Optional[str] = Field(None, min_length=6)
#     current_password: Optional[str] = None

#     roles: Optional[List[str]] = None
#     is_active: Optional[bool] = None
#     is_verified: Optional[bool] = None

#     @field_validator("username")
#     @classmethod
#     def validate_username(cls, v: Optional[str]) -> Optional[str]:
#         if not v:
#             return None
#         return normalize_username(v, USERNAME_UPDATE_REGEX)

#     @field_validator("phone")
#     @classmethod
#     def validate_phone(cls, v: Optional[str]) -> Optional[str]:
#         return normalize_phone(v)

#     @field_validator("password")
#     @classmethod
#     def validate_password(cls, v: Optional[str]) -> Optional[str]:
#         if not v:
#             return None
#         if len(v) < 6:
#             raise ValueError("Password must be at least 6 characters")
#         return v

#     @field_validator("names", "bio", "avatar_url")
#     @classmethod
#     def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
#         return validate_stripped_optional(v)

#     @field_validator("roles")
#     @classmethod
#     def validate_roles(cls, v: Optional[List[str]]) -> Optional[List[str]]:
#         if v is None:
#             return None
#         return validate_roles_list(v)


# # ============================================================================
# # Read Schema
# # ============================================================================

# class UserRead(UserBase):
#     id: UUID
#     is_active: bool
#     is_verified: bool
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True


# # ============================================================================
# # Password Update
# # ============================================================================

# class PasswordUpdate(BaseModel):
#     current_password: str
#     new_password: str = Field(..., min_length=8, max_length=100)

#     @field_validator("new_password")
#     @classmethod
#     def validate_password(cls, v: str) -> str:
#         if len(v) < 5:
#             raise ValueError("Password must be at least 5 characters long")
#         if not re.search(r"[A-Z]", v):
#             raise ValueError("Password must contain at least one uppercase letter")
#         if not re.search(r"[a-z]", v):
#             raise ValueError("Password must contain at least one lowercase letter")
#         if not re.search(r"\d", v):
#             raise ValueError("Password must contain at least one digit")
#         return v


# # ============================================================================
# # Auth & List Schemas
# # ============================================================================

# class UserSignin(BaseModel):
#     username: str = Field(..., description="Email, username, or phone number")
#     password: str


# class UserListResponse(BaseModel):
#     users: List[UserRead]
#     total: int
#     page: int
#     page_size: int
#     total_pages: int


# class UserFilters(BaseModel):
#     role: Optional[str] = None
#     is_active: Optional[bool] = None
#     search: Optional[str] = None


# class ParentChildRead(BaseModel):
#     ...




# # v2
# # ============================================================================
# # SCHEMAS - User
# # FILE: app/schemas/user.py
# # ============================================================================

# import re
# from datetime import datetime
# from typing import List, Optional
# from uuid import UUID

# from pydantic import BaseModel, EmailStr, Field, field_validator


# # ============================================================================
# # Constants & Regex
# # ============================================================================

# USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._-]+$")
# USERNAME_UPDATE_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")
# PHONE_LOCAL_REGEX = re.compile(r"^\d{7,11}$")
# PHONE_INTL_REGEX = re.compile(r"^\+?[0-9]{10,15}$")

# ALLOWED_ROLES = {"student", "tutor", "parent", "admin", "super_admin"}


# # ============================================================================
# # Shared Validators (DRY)
# # ============================================================================

# def normalize_username(value: str, regex: re.Pattern) -> str:
#     if not regex.match(value):
#         raise ValueError("Invalid username format")
#     return value.lower()


# def normalize_phone(value: Optional[str]) -> Optional[str]:
#     if not value:
#         return None

#     cleaned = re.sub(r"[^\d+]", "", value)

#     if PHONE_LOCAL_REGEX.match(cleaned):
#         return cleaned

#     if PHONE_INTL_REGEX.match(cleaned):
#         return cleaned

#     raise ValueError("Invalid phone number format")


# def validate_roles_list(roles: List[str]) -> List[str]:
#     for role in roles:
#         if role not in ALLOWED_ROLES:
#             raise ValueError(f"Invalid role: {role}")
#     return roles


# def validate_stripped_optional(value: Optional[str]) -> Optional[str]:
#     if not value:
#         return None
#     return value.strip()


# # ============================================================================
# # Base Schema
# # ============================================================================

# class UserBase(BaseModel):
#     username: str = Field(..., min_length=3, max_length=200)
#     names: str = Field(..., min_length=3, max_length=200)
#     email: EmailStr
#     phone: Optional[str] = Field(None, max_length=20)
#     roles: List[str] = Field(default_factory=lambda: ["student"])
#     parent_id: Optional[UUID] = None
#     is_active: Optional[bool] = None

#     @field_validator("username")
#     @classmethod
#     def validate_username(cls, v: str) -> str:
#         return normalize_username(v, USERNAME_REGEX)

#     @field_validator("phone")
#     @classmethod
#     def validate_phone(cls, v: Optional[str]) -> Optional[str]:
#         return normalize_phone(v)

#     @field_validator("roles")
#     @classmethod
#     def validate_roles(cls, v: List[str]) -> List[str]:
#         return validate_roles_list(v)


# # ============================================================================
# # Create Schema
# # ============================================================================

# class UserCreate(UserBase):
#     password: str = Field(..., min_length=5)

#     @field_validator("password")
#     @classmethod
#     def validate_password(cls, v: str) -> str:
#         if len(v) < 4:
#             raise ValueError("Password must be at least 4 characters long")
#         if not re.search(r"[A-Z]", v):
#             raise ValueError("Password must contain at least one uppercase letter")
#         if not re.search(r"[a-z]", v):
#             raise ValueError("Password must contain at least one lowercase letter")
#         if not re.search(r"\d", v):
#             raise ValueError("Password must contain at least one digit")
#         return v

#     @field_validator("parent_id", mode="before")
#     @classmethod
#     def empty_string_to_none(cls, v):
#         return None if v in ("", None) else v


# # ============================================================================
# # Update Schema
# # ============================================================================

# class UserUpdateSchema(BaseModel):
#     """
#     Partial update schema.
#     Only validates fields when provided.
#     """

#     username: Optional[str] = Field(None, min_length=3, max_length=30)
#     email: Optional[EmailStr] = None
#     names: Optional[str] = Field(None, min_length=2, max_length=100)
#     phone: Optional[str] = Field(None, max_length=20)
#     bio: Optional[str] = Field(None, max_length=500)
#     address: Optional[str] = Field(None, max_length=500)
#     profile_picture: Optional[str] = Field(None, max_length=500)  # set by avatar upload, not by client directly

#     password: Optional[str] = Field(None, min_length=6)
#     current_password: Optional[str] = None

#     roles: Optional[List[str]] = None
#     is_active: Optional[bool] = None
#     is_verified: Optional[bool] = None

#     @field_validator("username")
#     @classmethod
#     def validate_username(cls, v: Optional[str]) -> Optional[str]:
#         if not v:
#             return None
#         return normalize_username(v, USERNAME_UPDATE_REGEX)

#     @field_validator("phone")
#     @classmethod
#     def validate_phone(cls, v: Optional[str]) -> Optional[str]:
#         return normalize_phone(v)

#     @field_validator("password")
#     @classmethod
#     def validate_password(cls, v: Optional[str]) -> Optional[str]:
#         if not v:
#             return None
#         if len(v) < 6:
#             raise ValueError("Password must be at least 6 characters")
#         return v

#     @field_validator("names", "bio", "address", "profile_picture")
#     @classmethod
#     def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
#         return validate_stripped_optional(v)

#     @field_validator("roles")
#     @classmethod
#     def validate_roles(cls, v: Optional[List[str]]) -> Optional[List[str]]:
#         if v is None:
#             return None
#         return validate_roles_list(v)


# # ============================================================================
# # Read / Response Schema
# # ============================================================================

# class UserRead(UserBase):
#     id: UUID
#     is_active: bool
#     is_verified: bool
#     profile_picture: Optional[str] = None
#     address: Optional[str] = None
#     bio: Optional[str] = None
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True


# # Alias used by the router — both names work
# UserResponse = UserRead


# # ============================================================================
# # Password Update
# # ============================================================================

# class PasswordUpdate(BaseModel):
#     current_password: str
#     new_password: str = Field(..., min_length=8, max_length=100)

#     @field_validator("new_password")
#     @classmethod
#     def validate_password(cls, v: str) -> str:
#         if len(v) < 5:
#             raise ValueError("Password must be at least 5 characters long")
#         if not re.search(r"[A-Z]", v):
#             raise ValueError("Password must contain at least one uppercase letter")
#         if not re.search(r"[a-z]", v):
#             raise ValueError("Password must contain at least one lowercase letter")
#         if not re.search(r"\d", v):
#             raise ValueError("Password must contain at least one digit")
#         return v


# # ============================================================================
# # Auth & List Schemas
# # ============================================================================

# class UserSignin(BaseModel):
#     username: str = Field(..., description="Email, username, or phone number")
#     password: str


# class UserListResponse(BaseModel):
#     users: List[UserRead]
#     total: int
#     page: int
#     page_size: int
#     total_pages: int


# class UserFilters(BaseModel):
#     role: Optional[str] = None
#     is_active: Optional[bool] = None
#     search: Optional[str] = None


# class ParentChildRead(BaseModel):
#     ...




# # v3
# # ============================================================================
# # SCHEMAS - User
# # FILE: app/schemas/user.py
# # ============================================================================

# import re
# from datetime import datetime
# from typing import List, Optional
# from uuid import UUID

# from pydantic import BaseModel, EmailStr, Field, field_validator


# # ============================================================================
# # Constants & Regex
# # ============================================================================

# USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._-]+$")
# USERNAME_UPDATE_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")
# PHONE_LOCAL_REGEX = re.compile(r"^\d{7,11}$")
# PHONE_INTL_REGEX = re.compile(r"^\+?[0-9]{10,15}$")

# ALLOWED_ROLES = {"student", "tutor", "parent", "admin", "super_admin"}


# # ============================================================================
# # Shared Validators (DRY)
# # ============================================================================

# def normalize_username(value: str, regex: re.Pattern) -> str:
#     if not regex.match(value):
#         raise ValueError("Invalid username format")
#     return value.lower()


# def normalize_phone(value: Optional[str]) -> Optional[str]:
#     if not value:
#         return None

#     cleaned = re.sub(r"[^\d+]", "", value)

#     if PHONE_LOCAL_REGEX.match(cleaned):
#         return cleaned

#     if PHONE_INTL_REGEX.match(cleaned):
#         return cleaned

#     raise ValueError("Invalid phone number format")


# def validate_roles_list(roles: List[str]) -> List[str]:
#     for role in roles:
#         if role not in ALLOWED_ROLES:
#             raise ValueError(f"Invalid role: {role}")
#     return roles


# def validate_stripped_optional(value: Optional[str]) -> Optional[str]:
#     if not value:
#         return None
#     return value.strip()


# # ============================================================================
# # Base Schema
# # ============================================================================

# class UserBase(BaseModel):
#     username: str = Field(..., min_length=3, max_length=200)
#     names: str = Field(..., min_length=3, max_length=200)
#     email: EmailStr
#     phone: Optional[str] = Field(None, max_length=20)
#     roles: List[str] = Field(default_factory=lambda: ["student"])
#     parent_id: Optional[UUID] = None
#     is_active: Optional[bool] = None

#     @field_validator("username")
#     @classmethod
#     def validate_username(cls, v: str) -> str:
#         return normalize_username(v, USERNAME_REGEX)

#     @field_validator("phone")
#     @classmethod
#     def validate_phone(cls, v: Optional[str]) -> Optional[str]:
#         return normalize_phone(v)

#     @field_validator("roles")
#     @classmethod
#     def validate_roles(cls, v: List[str]) -> List[str]:
#         return validate_roles_list(v)


# # ============================================================================
# # Create Schema
# # ============================================================================

# class UserCreate(UserBase):
#     password: str = Field(..., min_length=5)

#     @field_validator("password")
#     @classmethod
#     def validate_password(cls, v: str) -> str:
#         if len(v) < 4:
#             raise ValueError("Password must be at least 4 characters long")
#         if not re.search(r"[A-Z]", v):
#             raise ValueError("Password must contain at least one uppercase letter")
#         if not re.search(r"[a-z]", v):
#             raise ValueError("Password must contain at least one lowercase letter")
#         if not re.search(r"\d", v):
#             raise ValueError("Password must contain at least one digit")
#         return v

#     @field_validator("parent_id", mode="before")
#     @classmethod
#     def empty_string_to_none(cls, v):
#         return None if v in ("", None) else v


# # ============================================================================
# # Update Schema
# # ============================================================================

# class UserUpdateSchema(BaseModel):
#     """
#     Partial update schema.
#     Only validates fields when provided.
#     """

#     username: Optional[str] = Field(None, min_length=3, max_length=30)
#     email: Optional[EmailStr] = None
#     names: Optional[str] = Field(None, min_length=2, max_length=100)
#     phone: Optional[str] = Field(None, max_length=20)
#     bio: Optional[str] = Field(None, max_length=500)
#     address: Optional[str] = Field(None, max_length=500)
#     profile_picture: Optional[str] = Field(None, max_length=500)  # set by avatar upload, not by client directly

#     password: Optional[str] = Field(None, min_length=6)
#     current_password: Optional[str] = None

#     roles: Optional[List[str]] = None
#     is_active: Optional[bool] = None
#     is_verified: Optional[bool] = None

#     @field_validator("username")
#     @classmethod
#     def validate_username(cls, v: Optional[str]) -> Optional[str]:
#         if not v:
#             return None
#         return normalize_username(v, USERNAME_UPDATE_REGEX)

#     @field_validator("phone")
#     @classmethod
#     def validate_phone(cls, v: Optional[str]) -> Optional[str]:
#         return normalize_phone(v)

#     @field_validator("password")
#     @classmethod
#     def validate_password(cls, v: Optional[str]) -> Optional[str]:
#         if not v:
#             return None
#         if len(v) < 6:
#             raise ValueError("Password must be at least 6 characters")
#         return v

#     @field_validator("names", "bio", "address", "profile_picture")
#     @classmethod
#     def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
#         return validate_stripped_optional(v)

#     @field_validator("roles")
#     @classmethod
#     def validate_roles(cls, v: Optional[List[str]]) -> Optional[List[str]]:
#         if v is None:
#             return None
#         return validate_roles_list(v)


# # ============================================================================
# # Read / Response Schema
# # ============================================================================

# class UserRead(UserBase):
#     id: UUID
#     is_active: bool
#     is_verified: bool
#     profile_picture: Optional[str] = None
#     address: Optional[str] = None
#     bio: Optional[str] = None
#     created_at: datetime
#     updated_at: datetime

#     @field_validator("roles", mode="before")
#     @classmethod
#     def coerce_roles(cls, v):
#         """ORM returns Role objects; flatten to name strings before validation."""
#         if not v:
#             return []
#         return [r.name if hasattr(r, "name") else r for r in v]

#     class Config:
#         from_attributes = True


# # Alias used by the router — both names work
# UserResponse = UserRead


# # ============================================================================
# # Password Update
# # ============================================================================

# class PasswordUpdate(BaseModel):
#     current_password: str
#     new_password: str = Field(..., min_length=8, max_length=100)

#     @field_validator("new_password")
#     @classmethod
#     def validate_password(cls, v: str) -> str:
#         if len(v) < 5:
#             raise ValueError("Password must be at least 5 characters long")
#         if not re.search(r"[A-Z]", v):
#             raise ValueError("Password must contain at least one uppercase letter")
#         if not re.search(r"[a-z]", v):
#             raise ValueError("Password must contain at least one lowercase letter")
#         if not re.search(r"\d", v):
#             raise ValueError("Password must contain at least one digit")
#         return v


# # ============================================================================
# # Auth & List Schemas
# # ============================================================================

# class UserSignin(BaseModel):
#     username: str = Field(..., description="Email, username, or phone number")
#     password: str


# class UserListResponse(BaseModel):
#     users: List[UserRead]
#     total: int
#     page: int
#     page_size: int
#     total_pages: int


# class UserFilters(BaseModel):
#     role: Optional[str] = None
#     is_active: Optional[bool] = None
#     search: Optional[str] = None


# class ParentChildRead(BaseModel):
#     ...






# # v3
# # ============================================================================
# # SCHEMAS - User
# # FILE: app/schemas/user.py
# # ============================================================================

# import re
# from datetime import datetime
# from typing import List, Optional
# from uuid import UUID

# from pydantic import BaseModel, EmailStr, Field, field_validator


# # ============================================================================
# # Constants & Regex
# # ============================================================================

# USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._-]+$")
# USERNAME_UPDATE_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")
# PHONE_LOCAL_REGEX = re.compile(r"^\d{7,11}$")
# PHONE_INTL_REGEX = re.compile(r"^\+?[0-9]{10,15}$")

# ALLOWED_ROLES = {"student", "tutor", "parent", "admin", "super_admin"}


# # ============================================================================
# # Shared Validators (DRY)
# # ============================================================================

# def normalize_username(value: str, regex: re.Pattern) -> str:
#     if not regex.match(value):
#         raise ValueError("Invalid username format")
#     return value.lower()


# def normalize_phone(value: Optional[str]) -> Optional[str]:
#     if not value:
#         return None

#     cleaned = re.sub(r"[^\d+]", "", value)

#     if PHONE_LOCAL_REGEX.match(cleaned):
#         return cleaned

#     if PHONE_INTL_REGEX.match(cleaned):
#         return cleaned

#     raise ValueError("Invalid phone number format")


# def validate_roles_list(roles: List[str]) -> List[str]:
#     for role in roles:
#         if role not in ALLOWED_ROLES:
#             raise ValueError(f"Invalid role: {role}")
#     return roles


# def validate_stripped_optional(value: Optional[str]) -> Optional[str]:
#     if not value:
#         return None
#     return value.strip()


# # ============================================================================
# # Base Schema
# # ============================================================================

# class UserBase(BaseModel):
#     username: str = Field(..., min_length=3, max_length=200)
#     names: str = Field(..., min_length=3, max_length=200)
#     email: EmailStr
#     phone: Optional[str] = Field(None, max_length=20)
#     roles: List[str] = Field(default_factory=lambda: ["student"])
#     parent_id: Optional[UUID] = None
#     is_active: Optional[bool] = None

#     @field_validator("username")
#     @classmethod
#     def validate_username(cls, v: str) -> str:
#         return normalize_username(v, USERNAME_REGEX)

#     @field_validator("phone")
#     @classmethod
#     def validate_phone(cls, v: Optional[str]) -> Optional[str]:
#         return normalize_phone(v)

#     @field_validator("roles")
#     @classmethod
#     def validate_roles(cls, v: List[str]) -> List[str]:
#         return validate_roles_list(v)


# # ============================================================================
# # Create Schema
# # ============================================================================

# class UserCreate(UserBase):
#     password: str = Field(..., min_length=5)

#     @field_validator("password")
#     @classmethod
#     def validate_password(cls, v: str) -> str:
#         if len(v) < 4:
#             raise ValueError("Password must be at least 4 characters long")
#         if not re.search(r"[A-Z]", v):
#             raise ValueError("Password must contain at least one uppercase letter")
#         if not re.search(r"[a-z]", v):
#             raise ValueError("Password must contain at least one lowercase letter")
#         if not re.search(r"\d", v):
#             raise ValueError("Password must contain at least one digit")
#         return v

#     @field_validator("parent_id", mode="before")
#     @classmethod
#     def empty_string_to_none(cls, v):
#         return None if v in ("", None) else v


# # ============================================================================
# # Update Schema
# # ============================================================================

# class UserUpdateSchema(BaseModel):
#     """
#     Partial update schema.
#     Only validates fields when provided.
#     """

#     username: Optional[str] = Field(None, min_length=3, max_length=30)
#     email: Optional[EmailStr] = None
#     names: Optional[str] = Field(None, min_length=2, max_length=100)
#     phone: Optional[str] = Field(None, max_length=20)
#     bio: Optional[str] = Field(None, max_length=500)
#     address: Optional[str] = Field(None, max_length=500)
#     profile_picture: Optional[str] = Field(None, max_length=500)  # set by avatar upload, not by client directly

#     password: Optional[str] = Field(None, min_length=6)
#     current_password: Optional[str] = None

#     roles: Optional[List[str]] = None
#     is_active: Optional[bool] = None
#     is_verified: Optional[bool] = None

#     @field_validator("username")
#     @classmethod
#     def validate_username(cls, v: Optional[str]) -> Optional[str]:
#         if not v:
#             return None
#         return normalize_username(v, USERNAME_UPDATE_REGEX)

#     @field_validator("phone")
#     @classmethod
#     def validate_phone(cls, v: Optional[str]) -> Optional[str]:
#         return normalize_phone(v)

#     @field_validator("password")
#     @classmethod
#     def validate_password(cls, v: Optional[str]) -> Optional[str]:
#         if not v:
#             return None
#         if len(v) < 6:
#             raise ValueError("Password must be at least 6 characters")
#         return v

#     @field_validator("names", "bio", "address", "profile_picture")
#     @classmethod
#     def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
#         return validate_stripped_optional(v)

#     @field_validator("roles")
#     @classmethod
#     def validate_roles(cls, v: Optional[List[str]]) -> Optional[List[str]]:
#         if v is None:
#             return None
#         return validate_roles_list(v)


# # ============================================================================
# # Read / Response Schema
# # ============================================================================

# class UserRead(UserBase):
#     id: UUID
#     is_active: bool
#     is_verified: bool
#     profile_picture: Optional[str] = None  # resolved from avatar relationship
#     address: Optional[str] = None
#     bio: Optional[str] = None
#     created_at: datetime
#     updated_at: datetime

#     @field_validator("roles", mode="before")
#     @classmethod
#     def coerce_roles(cls, v):
#         """ORM returns Role objects; flatten to name strings before validation."""
#         if not v:
#             return []
#         return [r.name if hasattr(r, "name") else r for r in v]

#     @field_validator("profile_picture", mode="before")
#     @classmethod
#     def resolve_avatar(cls, v, info):
#         """
#         profile_picture can arrive as:
#           - a string (direct column or already resolved)
#           - a UserAvatar ORM object  (via user.avatar relationship)
#           - None
#         Flatten to the URL string in all cases.
#         """
#         if v is None:
#             return None
#         if isinstance(v, str):
#             return v
#         # ORM object — pull file_path (the stored URL)
#         return getattr(v, "file_path", None)

#     class Config:
#         from_attributes = True


# # Alias used by the router — both names work
# UserResponse = UserRead


# # ============================================================================
# # Password Update
# # ============================================================================

# class PasswordUpdate(BaseModel):
#     current_password: str
#     new_password: str = Field(..., min_length=8, max_length=100)

#     @field_validator("new_password")
#     @classmethod
#     def validate_password(cls, v: str) -> str:
#         if len(v) < 5:
#             raise ValueError("Password must be at least 5 characters long")
#         if not re.search(r"[A-Z]", v):
#             raise ValueError("Password must contain at least one uppercase letter")
#         if not re.search(r"[a-z]", v):
#             raise ValueError("Password must contain at least one lowercase letter")
#         if not re.search(r"\d", v):
#             raise ValueError("Password must contain at least one digit")
#         return v


# # ============================================================================
# # Auth & List Schemas
# # ============================================================================

# class UserSignin(BaseModel):
#     username: str = Field(..., description="Email, username, or phone number")
#     password: str


# class UserListResponse(BaseModel):
#     users: List[UserRead]
#     total: int
#     page: int
#     page_size: int
#     total_pages: int


# class UserFilters(BaseModel):
#     role: Optional[str] = None
#     is_active: Optional[bool] = None
#     search: Optional[str] = None


# class ParentChildRead(BaseModel):
#     ...




# v4
# ============================================================================
# SCHEMAS - User
# FILE: app/schemas/user.py
# ============================================================================

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# Constants & Regex
# ============================================================================

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._-]+$")
USERNAME_UPDATE_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")
PHONE_LOCAL_REGEX = re.compile(r"^\d{7,11}$")
PHONE_INTL_REGEX = re.compile(r"^\+?[0-9]{10,15}$")

ALLOWED_ROLES = {"student", "tutor", "parent", "admin", "super_admin"}


# ============================================================================
# Shared Validators (DRY)
# ============================================================================

def normalize_username(value: str, regex: re.Pattern) -> str:
    if not regex.match(value):
        raise ValueError("Invalid username format")
    return value.lower()


def normalize_phone(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    cleaned = re.sub(r"[^\d+]", "", value)

    if PHONE_LOCAL_REGEX.match(cleaned):
        return cleaned

    if PHONE_INTL_REGEX.match(cleaned):
        return cleaned

    raise ValueError("Invalid phone number format")


def validate_roles_list(roles: List[str]) -> List[str]:
    for role in roles:
        if role not in ALLOWED_ROLES:
            raise ValueError(f"Invalid role: {role}")
    return roles


def validate_stripped_optional(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return value.strip()


# ============================================================================
# Base Schema
# ============================================================================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=200)
    names: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    roles: List[str] = Field(default_factory=lambda: ["student"])
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return normalize_username(v, USERNAME_REGEX)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        return normalize_phone(v)

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: List[str]) -> List[str]:
        return validate_roles_list(v)


# ============================================================================
# Create Schema
# ============================================================================

class UserCreate(UserBase):
    password: str = Field(..., min_length=5)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 4:
            raise ValueError("Password must be at least 4 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        return None if v in ("", None) else v


# ============================================================================
# Update Schema
# ============================================================================

class UserUpdateSchema(BaseModel):
    """
    Partial update schema.
    Only validates fields when provided.
    """

    username: Optional[str] = Field(None, min_length=3, max_length=30)
    email: Optional[EmailStr] = None
    names: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = Field(None, max_length=500)
    profile_picture: Optional[str] = Field(None, max_length=500)  # set by avatar upload, not by client directly

    password: Optional[str] = Field(None, min_length=6)
    current_password: Optional[str] = None

    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        return normalize_username(v, USERNAME_UPDATE_REGEX)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        return normalize_phone(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("names", "bio", "address", "profile_picture")
    @classmethod
    def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        return validate_stripped_optional(v)

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        return validate_roles_list(v)


# ============================================================================
# Read / Response Schema
# ============================================================================

class UserRead(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    profile_picture: Optional[str] = None  # resolved from avatar relationship
    address: Optional[str] = None   # resolved from addresses relationship (first entry)
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("roles", mode="before")
    @classmethod
    def coerce_roles(cls, v):
        """ORM returns Role objects; flatten to name strings before validation."""
        if not v:
            return []
        return [r.name if hasattr(r, "name") else r for r in v]

    @field_validator("address", mode="before")
    @classmethod
    def resolve_address(cls, v):
        """
        User has no address column — the ORM gives us the addresses list.
        Flatten to a single display string from the first active entry.
        """
        if v is None:
            return None
        if isinstance(v, str):
            return v
        # List of Address ORM objects
        if isinstance(v, list):
            if not v:
                return None
            first = v[0]
            # Try common address fields; adjust to your Address model
            parts = [
                getattr(first, "street", None),
                getattr(first, "city", None),
                getattr(first, "state", None),
            ]
            return ", ".join(p for p in parts if p) or None
        return None

    @field_validator("profile_picture", mode="before")
    @classmethod
    def resolve_avatar(cls, v, info):
        """
        profile_picture arrives as the result of the User.profile_picture property,
        which is already a string URL or None — just pass it through.
        If somehow a list of UserAvatar objects arrives, pick the latest active one.
        """
        if v is None:
            return None
        if isinstance(v, str):
            return v
        # List of UserAvatar ORM objects — pick latest non-deleted
        if isinstance(v, list):
            active = [a for a in v if not getattr(a, "is_deleted", False)]
            if not active:
                return None
            latest = sorted(active, key=lambda a: a.created_at, reverse=True)[0]
            return getattr(latest, "file_path", None)
        # Single ORM object fallback
        return getattr(v, "file_path", None)

    class Config:
        from_attributes = True


# Alias used by the router — both names work
UserResponse = UserRead


# ============================================================================
# Password Update
# ============================================================================

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 5:
            raise ValueError("Password must be at least 5 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


# ============================================================================
# Auth & List Schemas
# ============================================================================

class UserSignin(BaseModel):
    username: str = Field(..., description="Email, username, or phone number")
    password: str


class UserListResponse(BaseModel):
    users: List[UserRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserFilters(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None


class ParentChildRead(BaseModel):
    ...

