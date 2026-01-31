 # Jinja email rendering
 
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.config import get_app_config

app_config = get_app_config()

env = Environment(
    loader=FileSystemLoader(app_config.general_config.templates_dir),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_email(template: str, **context) -> str:
    base_context = {
        "company_name": app_config.mail_config.mail_sender_name,
        "year": datetime.now().year,
        "dashboard_url": app_config.general_config.frontend_url,
    }

    return env.get_template(f"emails/{template}").render(
        base_context | context
    )
