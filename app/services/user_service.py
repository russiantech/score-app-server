
# v3
# ============================================================================
# SERVICE: User Service (Functional Style)
# FILE: app/services/user_service.py
# ============================================================================

"""
User service layer providing user management operations.
Uses functional programming style instead of class-based approach.
"""

from typing import Optional, List
from uuid import UUID
import logging

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.models.rbac import Role
# from app.models.association_tables import parent_students
from app.models.parents import ParentChildren, RelationshipType, LinkStatus


from app.schemas.user import (
    UserCreate,
    UserUpdateSchema,
    PasswordUpdate,
    UserFilters,
)

from app.core.security.password import hash_password, verify_password
from app.services.notifications.email import send_welcome_email


logger = logging.getLogger(__name__)


# ============================================================================
# FETCH OPERATIONS
# ============================================================================

def get_user(db: Session, identifier: str | UUID) -> User:
    """
    Fetch user by ID, email, username, or phone.
    
    Args:
        db: Database session
        identifier: User ID, email, username, or phone
    
    Returns:
        User object
    
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(
        or_(
            User.id == identifier,
            User.email == identifier,
            User.username == identifier,
            User.phone == identifier,
        )
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """Get user by ID only."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    """Get user by phone number."""
    return db.query(User).filter(User.phone == phone).first()


# ============================================================================
# LIST & FILTER OPERATIONS
# ============================================================================

def list_users(
    db: Session,
    filters: Optional[UserFilters] = None,
    page: int = 1,
    page_size: int = 20
) -> List[User]:
    """
    Get paginated list of users with optional filtering.
    
    Args:
        db: Database session
        filters: Optional filtering criteria
        page: Page number (1-indexed)
        page_size: Number of users per page
    
    Returns:
        List of User objects
    """
    query = db.query(User)

    if filters:
        # Search by username, email, name, or phone
        if filters.search:
            term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    User.names.ilike(term),
                    User.email.ilike(term),
                    User.username.ilike(term),
                    User.phone.ilike(term),
                )
            )

        # Filter by active status
        if filters.is_active is not None:
            query = query.filter(User.is_active == filters.is_active)

        # Filter by role
        if filters.role:
            query = query.join(User.roles).filter(Role.name == filters.role)

    # Pagination
    users = (
        query
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return users


# ============================================================================
# CREATE OPERATIONS
# ============================================================================

async def create_user(
    db: Session,
    data: UserCreate,
    background_tasks: BackgroundTasks,
) -> User:
    """
    Create a new user with role assignment and optional parent linking.
    
    Args:
        db: Database session
        data: User creation data
        background_tasks: FastAPI background tasks for async operations
    
    Returns:
        Created User object
    
    Raises:
        HTTPException: If email, username, or phone already exists
    """
    # Validate uniqueness
    if get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    if get_user_by_username(db, data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    if data.phone and get_user_by_phone(db, data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone already registered"
        )

    # Create user
    user = User(
        email=data.email,
        username=data.username,
        names=data.names,
        phone=data.phone,
        password=hash_password(data.password),
        is_active=True,
        is_verified=False,
    )

    db.add(user)
    db.flush()  # Get user.id without committing

    # Assign roles
    if data.roles:
        roles = db.query(Role).filter(Role.name.in_(data.roles)).all()
        if not roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid roles: {data.roles}"
            )
        user.roles.extend(roles)

    # Commit to save user and roles
    db.commit()
    db.refresh(user)

    # Send welcome email in background
    # background_tasks.add_task(
    #     send_welcome_email,
    #     email=user.email,
    #     names=user.names or user.username,
    # )
    await send_welcome_email(
        email=user.email,
        names=user.names or user.username,
        background_tasks=background_tasks,
    )

    # Link to parent if student
    if data.parent_id and "student" in (data.roles or []):
        try:
            # link_parent_to_student(
            #     db=db,
            #     parent_id=data.parent_id,
            #     student_id=user.id,
            # )
            link_parent_to_student(
                db=db,
                parent_id=data.parent_id,
                student_id=user.id,
                relationship_type="guardian",
                is_primary=True,
                linked_by=user.id,
            )

        except Exception as e:
            logger.warning(f"Could not link parent to student: {e}")

    return user


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================

def update_user(
    db: Session,
    user_id: UUID,
    data: UserUpdateSchema,
    current_user: User,
) -> User:
    """
    Update user information including password.
    
    Password update rules:
    - Regular users: Must provide current_password
    - Admins updating others: No current_password required
    - Admins updating self: Must provide current_password
    
    Args:
        db: Database session
        user_id: ID of user to update
        data: Update data (only provided fields will be updated)
        current_user: User making the request
    
    Returns:
        Updated User object
    
    Raises:
        HTTPException: If user not found, unauthorized, or validation fails
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Permission check: users can only update themselves unless admin
    is_self_update = user.id == current_user.id
    
    if not is_self_update and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    # Get only fields that were explicitly provided
    update_data = data.model_dump(exclude_unset=True)
    
    # System fields that cannot be updated
    SYSTEM_FIELDS = {"id", "created_at", "updated_at"}
    RELATIONSHIP_FIELDS = {"roles", "parent_id"}
    
    # Remove system fields
    for field in SYSTEM_FIELDS:
        update_data.pop(field, None)

    # Handle password update if provided
    password_updated = False
    if "password" in update_data and update_data["password"]:
        # Admin updating another user's password - no current_password required
        if not is_self_update and current_user.is_admin:
            user.password = hash_password(update_data["password"])
            password_updated = True
        else:
            # Self-update OR non-admin - current_password required
            if not hasattr(data, 'current_password') or not data.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required to update password"
                )
            
            # Verify current password
            if not verify_password(data.current_password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            user.password = hash_password(update_data["password"])
            password_updated = True
        
        # Remove password fields from update_data
        update_data.pop("password", None)
        update_data.pop("current_password", None)

    # Validate unique constraints
    if "email" in update_data and update_data["email"] != user.email:
        if update_data["email"] and get_user_by_email(db, update_data["email"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    if "username" in update_data and update_data["username"] != user.username:
        if update_data["username"] and get_user_by_username(db, update_data["username"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    if "phone" in update_data and update_data["phone"] != user.phone:
        if update_data["phone"] and get_user_by_phone(db, update_data["phone"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone already in use"
            )

    # Update scalar fields
    for field, value in update_data.items():
        if field in RELATIONSHIP_FIELDS:
            continue
        
        current_value = getattr(user, field, None)
        
        if value != current_value:
            if value is None or (isinstance(value, str) and value == ""):
                setattr(user, field, None)
            else:
                setattr(user, field, value)

    # Update roles (admin-only)
    if "roles" in update_data:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update user roles"
            )
        
        new_roles = update_data["roles"]
        if new_roles:
            roles = db.query(Role).filter(Role.name.in_(new_roles)).all()
            
            if len(roles) != len(new_roles):
                found_role_names = [r.name for r in roles]
                invalid_roles = [r for r in new_roles if r not in found_role_names]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid roles: {invalid_roles}"
                )
            
            current_role_names = {r.name for r in user.roles}
            new_role_names = set(new_roles)
            
            if current_role_names != new_role_names:
                user.roles.clear()
                user.roles.extend(roles)

    db.commit()
    db.refresh(user)
    
    # Log the update
    action = "password updated" if password_updated else "updated"
    logger.info(f"User {user.id} {action} by {current_user.id} (admin={current_user.is_admin})")
    
    return user


# ============================================================================
# PASSWORD OPERATIONS
# ============================================================================

def update_password(
    db: Session,
    user_id: UUID,
    data: PasswordUpdate,
    current_user: User,
) -> User:
    """
    Update user password.
    
    Requires current password for verification.
    Users can only change their own password.
    
    Args:
        db: Database session
        user_id: ID of user whose password to update
        data: Password update data (current and new password)
        current_user: User making the request
    
    Returns:
        Updated User object
    
    Raises:
        HTTPException: If unauthorized or current password incorrect
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Users can only change their own password
    if user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to change this password"
        )

    # Verify current password
    if not verify_password(data.current_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    user.password = hash_password(data.new_password)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Password updated for user {user.id}")
    
    return user


# ============================================================================
# DELETE & STATUS OPERATIONS
# ============================================================================

def toggle_user_status(db: Session, user_id: UUID, current_user: User) -> User:
    """
    Toggle user active/inactive status.
    
    Args:
        db: Database session
        user_id: ID of user to toggle
        current_user: User making the request
    
    Returns:
        Updated User object
    
    Raises:
        HTTPException: If user not found or unauthorized
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can toggle user status"
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent deactivating self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot toggle your own status"
        )

    user.is_active = not user.is_active
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User {user.id} status toggled to {user.is_active} by {current_user.id}")
    
    return user


def delete_user(
    db: Session,
    user_id: UUID,
    current_user: User,
    hard_delete: bool = False
) -> None:
    """
    Delete user (soft delete by default).
    
    Args:
        db: Database session
        user_id: ID of user to delete
        current_user: User making the request
        hard_delete: If True, permanently delete; if False, soft delete
    
    Raises:
        HTTPException: If user not found, unauthorized, or trying to delete self
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users"
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    if hard_delete:
        db.delete(user)
        logger.warning(f"User {user.id} permanently deleted by {current_user.id}")
    else:
        user.is_active = False
        logger.info(f"User {user.id} soft deleted by {current_user.id}")
    
    db.commit()


# ============================================================================
# ROLE MANAGEMENT
# ============================================================================

def is_admin(user: User) -> bool:
    """
    Check if user has admin role.
    
    Args:
        user: User to check
    
    Returns:
        True if user is admin, False otherwise
    """
    if not user.roles:
        return False
    return any(role.name.lower() == "admin" for role in user.roles)


def assign_role(
    db: Session,
    user_id: UUID,
    role_name: str,
    current_user: User,
) -> User:
    """
    Assign a role to a user.
    
    Args:
        db: Database session
        user_id: ID of user to assign role to
        role_name: Name of role to assign
        current_user: User making the request
    
    Returns:
        Updated User object
    
    Raises:
        HTTPException: If unauthorized, user not found, or role not found
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign roles"
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )

    # Check if user already has this role
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)
        logger.info(f"Role '{role_name}' assigned to user {user.id} by {current_user.id}")

    return user


def remove_role(
    db: Session,
    user_id: UUID,
    role_name: str,
    current_user: User,
) -> User:
    """
    Remove a role from a user.
    
    Args:
        db: Database session
        user_id: ID of user to remove role from
        role_name: Name of role to remove
        current_user: User making the request
    
    Returns:
        Updated User object
    
    Raises:
        HTTPException: If unauthorized, user not found, or role not found
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can remove roles"
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )

    # Remove role if user has it
    if role in user.roles:
        user.roles.remove(role)
        db.commit()
        db.refresh(user)
        logger.info(f"Role '{role_name}' removed from user {user.id} by {current_user.id}")

    return user


def link_parent_to_student(
    db: Session,
    parent_id: UUID,
    student_id: UUID,
    relationship_type: str = "guardian",
    is_primary: bool = False,
    linked_by: UUID | None = None,
) -> ParentChildren:
    """
    Link a parent/guardian to a student using ParentChildren entity.
    """

    parent = get_user_by_id(db, parent_id)
    student = get_user_by_id(db, student_id)

    if not parent or not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent or student not found",
        )

    if not parent.is_parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a parent",
        )

    if not student.is_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a student",
        )

    # Prevent duplicate link
    existing = (
        db.query(ParentChildren)
        .filter(
            ParentChildren.parent_id == parent_id,
            ParentChildren.student_id == student_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent-student relationship already exists",
        )

    # Validate enum
    try:
        relationship_enum = RelationshipType(relationship_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid relationship type: {relationship_type}",
        )

    # Ensure only one primary guardian
    if is_primary:
        db.query(ParentChildren).filter(
            ParentChildren.student_id == student_id,
            ParentChildren.is_primary.is_(True),
        ).update({"is_primary": False})

    link = ParentChildren(
        parent_id=parent_id,
        student_id=student_id,
        relationship_type=relationship_enum,
        status=LinkStatus.ACTIVE,
        is_primary=is_primary,
        linked_by=linked_by,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    logger.info(
        f"Parent {parent_id} linked to student {student_id} "
        f"(relationship={relationship_enum.value}, primary={is_primary})"
    )

    return link


def unlink_parent_from_student(
    db: Session,
    parent_id: UUID,
    student_id: UUID,
    reason: str | None = None,
) -> None:
    """
    Soft-remove parent-student relationship (sets status to INACTIVE).
    """

    link = (
        db.query(ParentChildren)
        .filter(
            ParentChildren.parent_id == parent_id,
            ParentChildren.student_id == student_id,
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent-student relationship not found",
        )

    link.status = LinkStatus.INACTIVE
    link.suspended_at = None
    link.suspended_reason = reason

    db.commit()

    logger.info(f"Parent {parent_id} unlinked from student {student_id}")

