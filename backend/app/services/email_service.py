import smtplib
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from email.mime.text import MIMEText

import jwt
from fastapi import HTTPException

from app.config import get_settings

settings = get_settings()


class EmailService:
    def generate_verify_token(self, user_id: str, email: str) -> str:
        expire_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire_at,
            "type": "email_verify",
        }
        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    def decode_verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "email_verify":
                raise HTTPException(
                    status_code=400, detail="Invalid verification token"
                )
            return payload
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=400, detail="Verification token expired"
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=400, detail="Invalid verification token"
            ) from exc

    def send_verification_email(self, to_email: str, token: str) -> None:
        verify_url = f"{settings.FRONTEND_BASE_URL}/verify-email?token={token}"
        body = f"""Welcome to Campus BBS!

Please verify your email address by visiting the link below:

    {verify_url}

This link will expire in {settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES // 60} hours.

If you did not create this account, please ignore this email.
"""
        msg = MIMEText(body)
        msg["Subject"] = "Verify your email - Campus BBS"
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email

        try:
            if settings.SMTP_USE_TLS:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.starttls()
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
            server.quit()
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"Failed to send email: {exc}"
            ) from exc
