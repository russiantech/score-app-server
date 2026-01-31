from fastapi import BackgroundTasks
from pydantic import EmailStr
from typing import Optional

from .dispatcher import dispatch_email
from .templates import render_email
# from app.core.config import app_config


# =========================
# NON-CRITICAL (BACKGROUND)
# =========================

async def send_welcome_email_0(
    *,
    email: EmailStr,
    names: str,
    background_tasks: BackgroundTasks,
):
    subject = "Welcome to Our Scoring System. Dunistech Academy"

    html, text = render_email(
        "welcome.html",
        names=names,
        subject=subject,
    )

    await dispatch_email(
        subject=subject,
        to=email,
        html=html,
        text=text,
        background_tasks=background_tasks,
        critical=False,
    )


# from fastapi import BackgroundTasks
# from pydantic import EmailStr

# from app.core.config import get_app_config
# from app.services.mail.dispatcher import dispatch_email
# from app.services.mail.templates import render_email

from app.core.config import get_app_config
app_config = get_app_config()

# v2 - also informs admin about new successful signups
async def send_welcome_email(
    *,
    email: EmailStr,
    names: str,
    background_tasks: BackgroundTasks,
):
    """
    Sends welcome email to:
    - the user
    - system admin email (CC-style, same content)
    """

    subject = "Welcome to Our Scoring System – Dunistech Academy"

    html, text = render_email(
        "welcome.html",
        names=names,
        subject=subject,
    )

    # Build recipient list
    recipients: list[EmailStr] = [email]

    contact_email = app_config.general_config.contact_email
    if contact_email:
        recipients.append(contact_email)

    await dispatch_email(
        subject=subject,
        to=recipients,  # 👈 multiple recipients
        html=html,
        text=text,
        background_tasks=background_tasks,
        critical=False,
    )


# =========================
# CRITICAL (REALTIME)
# =========================

async def send_verification_email(
    *,
    email: EmailStr,
    code: str,
    names: Optional[str] = None,
):
    subject = "Verify Your Email"

    html, text = render_email(
        "verify_email.html",
        names=names,
        code=code,
        subject=subject,
    )

    return await dispatch_email(
        subject=subject,
        to=email,
        html=html,
        text=text,
        critical=True,
    )


# async def send_password_reset_email(
#     *,
#     email: EmailStr,
#     names: str,
#     token: str,
#     background_tasks: Optional[BackgroundTasks] = None,
# ):
#     reset_link = (
#         f"{app_config.general_config.frontend_url}/auth/reset-password?token={token}"
#     )

#     subject = "Reset Your Password"

#     html, text = render_email(
#         "password_reset.html",
#         names=names,
#         reset_link=reset_link,
#         subject=subject,
#     )

#     await dispatch_email(
#         subject=subject,
#         to=email,
#         html=html,
#         text=text,
#         background_tasks=background_tasks,
#         critical=background_tasks is None,
#     )


# async def send_password_reset_email(
#     *,
#     email: EmailStr,
#     names: str,
#     code: str,  # ✅ NEW - 6-digit code
#     background_tasks: Optional[BackgroundTasks] = None,
# ):
#     """Send password reset code via email"""
#     subject = "Reset Your Password"

#     html, text = render_email(
#         "password_reset.html",
#         names=names,
#         code=code,  # ✅ NEW - pass code to template
#         subject=subject,
#     )

#     await dispatch_email(
#         subject=subject,
#         to=email,
#         html=html,
#         text=text,
#         background_tasks=background_tasks,
#         critical=background_tasks is None,
#     )


# NEW VERSION (code-based)
async def send_password_reset_email(
    *,
    email: EmailStr,
    names: str,
    code: str,  # ✅ NEW - 6-digit code
    background_tasks: Optional[BackgroundTasks] = None,
):
    """Send password reset code via email"""
    subject = "Reset Your Password"

    html, text = render_email(
        "password_reset.html",
        names=names,
        code=code,  # ✅ NEW - pass code to template
        subject=subject,
    )

    await dispatch_email(
        subject=subject,
        to=email,
        html=html,
        text=text,
        background_tasks=background_tasks,
        critical=background_tasks is None,
    )


# async def send_password_reset_email(
#     *,
#     email: str,
#     names: str,
#     token: str,
# ):
#     html, text = render_email(
#         "password_reset.html",
#         name=names,
#         reset_link=f"{FRONTEND_URL}/reset-password?token={token}",
#     )

#     dispatch_email(
#         subject="Reset your password",
#         recipients=[email],
#         html=html,
#         text=text,
#     )
#     return True


async def send_password_changed_email(
    *,
    email: EmailStr,
    names: str,
    background_tasks: Optional[BackgroundTasks] = None,
):
    subject = "Password Changed Successfully"

    html, text = render_email(
        "password_changed.html",
        names=names,
        subject=subject,
    )

    await dispatch_email(
        subject=subject,
        to=email,
        html=html,
        text=text,
        background_tasks=background_tasks,
        critical=background_tasks is None,
    )

""" 
SEE USAGE
await send_verification_email(
    email=user.email,
    code=otp,
    names=user.first_name,
)

await send_welcome_email(
    email=user.email,
    names=user.first_name,
    background_tasks=background_tasks,
)

"""