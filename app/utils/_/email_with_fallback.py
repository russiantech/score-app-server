from typing import Optional, List
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fastapi import BackgroundTasks
from pydantic import EmailStr

import aiosmtplib
import resend
import traceback
import logging

from app.core.config import get_app_config
# from app.core import config

app_config = get_app_config()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure DEBUG messages are shown


# --------------------------------------------------------------------
# Template Renderer
# --------------------------------------------------------------------
templates_env = Environment(
    loader=FileSystemLoader(app_config.general_config.templates_dir),
    autoescape=select_autoescape(["html", "xml"]),
)

def render_template(filename: str, **context) -> str:
    template = templates_env.get_template(f"email/{filename}")
    return template.render(**context)

from datetime import datetime

def render_template(filename: str, **context) -> str:
    base_context = {
        "company_name": app_config.mail_config.mail_sender_name,
        "logo_url": "	https://dunistech.ng/static/img/dun%20logo%20(1).png",
        "support_url": "https://dunistech.ng/support",
        "dashboard_url": "https://dunistech.ng/dashboard",
        "year": datetime.now().year,
    }

    full_context = base_context | context

    template = templates_env.get_template(f"email/{filename}")
    return template.render(**full_context)

# --------------------------------------------------------------------
# SMTP SENDER (REAL async)
# --------------------------------------------------------------------

# v2  - ssl compatible
async def _smtp_send_async(
    subject: str,
    recipients: List[str],
    html_body: str,
    text_body: str,
):
    msg = EmailMessage()
    
    msg["Subject"] = subject
    msg["From"] = f"Dunistech Academy <{app_config.mail_config.smtp_username}>"
    msg["To"] = ", ".join(recipients)
    
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    
    logger.info(f"Preparing SMTP email...")
    
    try:
        await aiosmtplib.send(
            msg,
            hostname=app_config.mail_config.smtp_host,
            port=app_config.mail_config.smtp_port,  # Should be 465
            username=app_config.mail_config.smtp_username,
            password=app_config.mail_config.smtp_password.strip(),  # Remove spaces
            use_tls=True,  # Use TLS for port 465
            start_tls=False,  # DISABLE STARTTLS for port 465
            timeout=30,
        )
        logger.info("✅ SMTP email sent successfully.")
    except Exception as e:
        logger.error(f"❌ SMTP send failed: {e}")
        raise


# --------------------------------------------------------------------
# API EMAIL SENDER (SYNC WRAPPER, ASYNC SAFE)
# --------------------------------------------------------------------
async def _api_send_async(
    subject: str,
    recipients: List[str],
    html_body: str,
    text_body: str,
):
    resend.api_key = app_config.mail_config.resend_api_key

    params = {
        "from": f"{app_config.mail_config.mail_sender_name} <{app_config.mail_config.mail_sender_email}>",
        "to": recipients,
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }

    resend.Emails.send(params)

    logger.info("✅ API email sent successfully.")

# --------------------------------------------------------------------
# REALTIME EMAIL SENDER (AWAITABLE)
# Used for OTP, verification, password reset
# --------------------------------------------------------------------
async def send_email(
    *,
    subject: str,
    to: EmailStr | List[EmailStr],
    html_body: str = "",
    text_body: str = "",
    via: str = "smtp"
):

    recipients = [to] if isinstance(to, str) else list(to)

    try:
        
        if via == "smtp":
            await _smtp_send_async(subject, recipients, html_body, text_body)

        elif via == "api":
            await _api_send_async(subject, recipients, html_body, text_body)

        else:
            raise ValueError(f"Invalid mail provider ->  {app_config.mail_config.provider}")

        return True

    except Exception:
        logger.error("❌ Real-time email send failed")
        traceback.print_exc()
        return False

# --------------------------------------------------------------------
# BACKGROUND EMAIL SENDER
# Used for welcome emails, alerts, broadcasts
# --------------------------------------------------------------------
def send_email_background(
    *,
    subject: str,
    to: EmailStr | List[EmailStr],
    html_body: str = "",
    text_body: str = "",
    background_tasks: BackgroundTasks,
    via: str = "smtp"
):
    recipients = [to] if isinstance(to, str) else list(to)

    if via == "smtp":
        background_tasks.add_task(
            _smtp_send_async,
            subject,
            recipients,
            html_body,
            text_body,
        )

    elif via == "api":
        background_tasks.add_task(
            _api_send_async,
            subject,
            recipients,
            html_body,
            text_body,
        )

    else:
        raise ValueError("Invalid mail provider")

    logger.info("📤 Background email queued.")

# ============================================================================
# EMAIL HELPERS
# ============================================================================

# ✅ Non-critical: use background
async def send_welcome_email(
    email: EmailStr,
    names: str,
    background_tasks: BackgroundTasks
):
    # html = render_template("welcome.html", names=names)
    html = render_template("welcome.html", names=names, subject="Welcome to Dunistech Academy")

    text = f"Welcome to DunisTech Academy, {names}!"

    send_email_background(
        subject="Welcome to DunisTech Academy",
        to=email,
        html_body=html,
        text_body=text,
        background_tasks=background_tasks,
        via=app_config.mail_config.provider,
    )


# ✅ CRITICAL: MUST be realtime
async def send_verification_email(
    email: EmailStr,
    code: str,
    names: Optional[str] = None,
):
    html = render_template(
        "email_verification_code.html",
        names=names,
        code=code,
        
    )

    text = f"""
    Hi {names or ''},

    Your email verification code is: {code}

    Please do not share this code with anyone.

    {app_config.mail_config.mail_sender_name}
    """
    # logger.debug(f"Email provider: {app_config.mail_config.provider}")
    return await send_email(
        subject="Verify Your Email",
        to=email,
        html_body=html,
        text_body=text,
        via=app_config.mail_config.provider,
    )


# ✅ CRITICAL (SMS OTP → realtime)
async def send_verification_sms(phone: str, code: str) -> bool:
    try:
        logger.info(f"📲 Sending SMS code {code} to {phone}")

        # await sms_provider.send(phone, f"Your verification code: {code}")

        # return True
        return False # Placeholder until SMS service is implemented

    except Exception:
        logger.error("❌ SMS sending error")
        traceback.print_exc()
        return False




# =====================Thursday 18 2025 ========================================
# NEW
# Add these functions to your email service

async def send_password_reset_email(
    email: str,
    names: str,
    token: str,
    background_tasks: BackgroundTasks = None,
) -> bool:
    """
    Send password reset email with reset link
    """
    try:
        # Generate reset link
        reset_link = f"{app_config.general_config.frontend_url}/auth/reset-password?token={token}"
        
        subject = "Reset Your Password - Dunistech Academy"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4a6fa5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; background-color: #4a6fa5; color: white; 
                         padding: 12px 30px; text-decoration: none; border-radius: 5px; 
                         font-weight: bold; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; 
                         color: #666; font-size: 12px; text-align: center; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; 
                         padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {names},</h2>
                    <p>You recently requested to reset your password for your Dunistech Academy account.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </div>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; background-color: #eee; padding: 10px; border-radius: 5px;">
                        {reset_link}
                    </p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong>
                        <ul>
                            <li>This link will expire in 15 minutes</li>
                            <li>If you didn't request this, please ignore this email</li>
                            <li>Your password will remain unchanged until you click the link above</li>
                        </ul>
                    </div>
                    
                    <p>For security reasons, this link can only be used once.</p>
                    <p>If you're having trouble clicking the button, copy and paste the URL above into your web browser.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply to this email.</p>
                    <p>© {datetime.now().year} Dunistech Academy. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Hi {names},
        
        You requested to reset your password for Dunistech Academy.
        
        Reset Link: {reset_link}
        
        This link expires in 15 minutes.
        
        If you didn't request this, please ignore this email.
        
        © {datetime.now().year} Dunistech Academy
        """
        
        # Send email (using your existing email sending infrastructure)
        if background_tasks:
            # Queue email sending
            background_tasks.add_task(
                send_email,
                subject=subject,
                recipients=[email],
                html_body=html_body,
                text_body=text_body
            )
            return True
        else:
            # Send immediately
            await send_email(
                subject=subject,
                recipients=[email],
                html_body=html_body,
                text_body=text_body
            )
            return True
            
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {e}")
        return False


async def send_password_changed_email(
    email: str,
    names: str,
    background_tasks: BackgroundTasks = None,
) -> bool:
    """
    Send notification email when password is changed
    """
    try:
        subject = "Password Changed Successfully - Dunistech Academy"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9f9f9; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; 
                         padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; 
                         color: #666; font-size: 12px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Updated</h1>
                </div>
                <div class="content">
                    <h2>Hi {names},</h2>
                    <p>Your password has been successfully changed.</p>
                    
                    <div class="warning">
                        <strong>🔒 Security Alert:</strong>
                        <ul>
                            <li>If you made this change, no further action is required</li>
                            <li>If you did NOT change your password, please contact support immediately</li>
                            <li>We recommend using a unique password for each service</li>
                        </ul>
                    </div>
                    
                    <p>For security, we recommend:</p>
                    <ul>
                        <li>Using a strong, unique password</li>
                        <li>Enabling two-factor authentication if available</li>
                        <li>Regularly updating your password</li>
                    </ul>
                    
                    <p>If you have any questions or concerns, please contact our support team.</p>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} Dunistech Academy. All rights reserved.</p>
                    <p><small>This is an automated security notification.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Hi {names},
        
        Your Dunistech Academy password has been changed successfully.
        
        If you made this change, no further action is needed.
        
        If you did NOT change your password, please contact support immediately.
        
        Security Tips:
        - Use a strong, unique password
        - Enable two-factor authentication
        - Regularly update your password
        
        © {datetime.now().year} Dunistech Academy
        """
        
        # Send email
        if background_tasks:
            background_tasks.add_task(
                send_email,
                subject=subject,
                recipients=[email],
                html_body=html_body,
                text_body=text_body
            )
            return True
        else:
            await send_email(
                subject=subject,
                recipients=[email],
                html_body=html_body,
                text_body=text_body
            )
            return True
            
    except Exception as e:
        logger.error(f"Failed to send password changed email to {email}: {e}")
        return False