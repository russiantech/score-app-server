from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, HTTPException
from app.models.user import User
from app.schemas.user import UserCreate, UserSignin
from app.core.security.password import hash_password, verify_password
from app.utils.email import render_template, send_email
from app.models.rbac import Role
from app.utils.helpers import get_client_ip

# v2
def create_user(db: Session, data: UserCreate, current_user: User | None = None) -> User:
    """Create a new user. Admins may assign roles."""
    
    # Check email
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")

    # Check username
    if db.scalar(select(User).where(User.username == data.username)):
        raise HTTPException(400, "This username is already taken.")

    # Check phone
    if db.scalar(select(User).where(User.phone == data.phone)):
        raise HTTPException(400, "Phone number already registered.")

    # Create user
    user = User(
        names=data.names,
        phone=data.phone,
        username=data.username,
        email=data.email,
        ip=get_client_ip(),
        password=hash_password(data.password),
    )

    db.add(user)
    db.flush()

    # Assign role only if admin provided a role
    if current_user and current_user.is_admin and getattr(data, 'role', None):
        role = db.query(Role).filter(Role.name == data.role).first()
        if role:
            user.roles.append(role)

    # Send welcome email (optional)
    try:
        html_body = render_template("welcome.html", user=user)
        text_body = render_template("welcome.txt", user=user)
        send_email(
            subject="Welcome to Dunistech Academy!",
            to=user.email,
            html_body=html_body,
            text_body=text_body,
            background_tasks=BackgroundTasks,
            via="smtp"
        )
    except Exception as mail_err:
        print(f" Email sending error: {mail_err}")

    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: UserSignin) -> User:
    user = db.query(User).filter(
        or_(
        User.email == data.username, 
        User.username == data.username,
        User.phone == data.username
        )).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(401, "Invalid credentials")
    return user

