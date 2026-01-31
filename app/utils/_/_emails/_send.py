
def _build_message(
    *,
    subject: str,
    recipients: list[str],
    html_body: str,
    text_body: str,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Dunistech Academy <{app_config.mail_config.smtp_username}>"
    msg["To"] = ", ".join(recipients)

    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    return msg

async def send_email(
    *,
    subject: str,
    to: EmailStr | list[EmailStr],
    html_body: str = "",
    text_body: str = "",
) -> bool:
    recipients = [to] if isinstance(to, str) else list(to)

    msg = _build_message(
        subject=subject,
        recipients=recipients,
        html_body=html_body,
        text_body=text_body,
    )

    try:
        return await _send_with_fallback(msg)
    except Exception:
        logger.exception("❌ Unexpected email failure")
        return False
