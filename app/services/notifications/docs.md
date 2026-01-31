what I have currently **works**, but it’s grown organically and now needs **professional service-layer refactoring** to stay DRY, clean, and scalable.

Below is a **clean, modern, production-grade organization** that:

* Eliminates repetition
* Separates **templates**, **transport**, and **usage**
* Clearly distinguishes **CRITICAL (realtime)** vs **NON-CRITICAL (background)**
* Keeps FastAPI-friendly patterns
* Makes future emails trivial to add

---

## ✅ Target Architecture (Clean & Scalable)

```
app/
├── services/
│   └── notifications/
│       ├── __init__.py
│       ├── email.py          # Public email API
│       ├── sms.py            # SMS API (future-ready)
│       ├── templates.py      # Template rendering helpers
│       └── dispatcher.py     # Low-level send logic
│
├── templates/
│   └── emails/
│       ├── welcome.html
│       ├── verify_email.html
│       ├── password_reset.html
│       └── password_changed.html
```

---

## 1️⃣ Core Dispatcher (Single Source of Truth)

### `dispatcher.py`

```python
from fastapi import BackgroundTasks
from typing import Optional
from app.core.config import app_config
from app.core.mail import send_email, send_email_background


async def dispatch_email(
    *,
    subject: str,
    to: str,
    html: str,
    text: str,
    background_tasks: Optional[BackgroundTasks] = None,
    critical: bool = False,
):
    """
    Unified email dispatcher.
    - critical=True  -> realtime (await)
    - critical=False -> background (fire & forget)
    """

    provider = app_config.mail_config.provider

    if critical or not background_tasks:
        return await send_email(
            subject=subject,
            to=to,
            html_body=html,
            text_body=text,
            via=provider,
        )

    send_email_background(
        subject=subject,
        to=to,
        html_body=html,
        text_body=text,
        background_tasks=background_tasks,
        via=provider,
    )
```

✅ **Why this matters**

* Zero duplication
* All provider logic in **one place**
* Easy to swap Mailgun / SES / SMTP later

---

## 2️⃣ Template Rendering (No Inline HTML Anymore)

### `templates.py`

```python
from datetime import datetime
from app.core.templating import render_template
from app.core.config import app_config


def render_email(template: str, **context) -> tuple[str, str]:
    """
    Returns (html, text)
    """
    context.setdefault("year", datetime.now().year)
    context.setdefault("app_name", app_config.general_config.site_name)

    html = render_template(f"emails/{template}", **context)

    # Minimal text fallback (can be improved later)
    text = f"{context.get('subject', '')}\n\n{context.get('names', '')}"

    return html, text
```

---

## 3️⃣ Email Service (Clean Public API)

### `email.py`

```python
from fastapi import BackgroundTasks
from pydantic import EmailStr
from typing import Optional

from .dispatcher import dispatch_email
from .templates import render_email
from app.core.config import app_config


# =========================
# NON-CRITICAL (BACKGROUND)
# =========================

async def send_welcome_email(
    *,
    email: EmailStr,
    names: str,
    background_tasks: BackgroundTasks,
):
    subject = "Welcome to Dunistech Academy"

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


async def send_password_reset_email(
    *,
    email: EmailStr,
    names: str,
    token: str,
    background_tasks: Optional[BackgroundTasks] = None,
):
    reset_link = (
        f"{app_config.frontend_url}/auth/reset-password?token={token}"
    )

    subject = "Reset Your Password"

    html, text = render_email(
        "password_reset.html",
        names=names,
        reset_link=reset_link,
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
```

---

## 4️⃣ SMS Service (Future-Safe, Clean)

### `sms.py`

```python
import logging

logger = logging.getLogger(__name__)


async def send_verification_sms(phone: str, code: str) -> bool:
    try:
        logger.info("📲 Sending SMS to %s", phone)

        # await sms_provider.send(phone, f"Your code: {code}")

        return False  # Placeholder
    except Exception:
        logger.exception("❌ SMS sending failed")
        return False
```

---

## 5️⃣ Usage (Controllers Stay Clean)

```python
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
```

No HTML.
No provider logic.
No duplication.

---

## 🔥 What You Gained

✔ DRY
✔ Clean separation of concerns
✔ Professional service-layer design
✔ Easy to add new emails
✔ Background vs realtime is explicit
✔ Production-ready

---

If you want, next we can:

* Convert templates to **Jinja macros**
* Add **retry + circuit breaker**
* Add **email event logging**
* Add **per-provider failover**
