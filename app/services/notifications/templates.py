""" Template Rendering (No Inline HTML Anymore) """

from datetime import datetime
# from app.core.templating import render_template
from app.services.mail.templates import render_email as render_email_template
from app.core.config import app_config


def render_email(template: str, **context) -> tuple[str, str]:
    """
    Returns (html, text)
    """
    context.setdefault("year", datetime.now().year)
    context.setdefault("app_name", app_config.general_config.site_name)

    # html = render_template(f"emails/{template}", **context)
    html = render_email_template(f"{template}", **context)

    # Minimal text fallback (can be improved later)
    text = f"{context.get('subject', '')}\n\n{context.get('names', '')}"

    return html, text


