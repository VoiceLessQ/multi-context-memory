"""
Email sending utilities for the MCP Multi-Context Memory System.
"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from jinja2 import Environment, BaseLoader, Template
import os

logger = logging.getLogger(__name__)

# Email configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.example.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "your_email@example.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")  # No default - must be set in production
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "MCP Multi-Context Memory System")
EMAIL_FROM_EMAIL = os.getenv("EMAIL_FROM_EMAIL", EMAIL_HOST_USER)
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://yourapp.com")  # Base URL for email links

class InlineTemplateLoader(BaseLoader):
    """Custom Jinja2 loader for inline templates."""
    
    def __init__(self):
        self.templates = {
            "verification": """
            Hi {{ username }},
            
            Thank you for registering for the MCP Multi-Context Memory System.
            Please click the link below to activate your account:
            
            {{ activation_url }}
            
            If you did not register for this account, please ignore this email.
            
            Regards,
            The MCP Multi-Context Memory Team
            """,
            "password_reset": """
            Hi {{ username }},
            
            We received a request to reset your password for your MCP Multi-Context Memory System account.
            Please click the link below to reset your password:
            
            {{ reset_url }}
            
            If you did not request a password reset, please ignore this email.
            
            Regards,
            The MCP Multi-Context Memory Team
            """
        }
    
    def get_source(self, environment, template):
        if template not in self.templates:
            raise Exception(f"Template {template} not found")
        source = self.templates[template]
        return source, None, lambda: False

# Initialize Jinja2 environment with custom loader
try:
    env = Environment(loader=InlineTemplateLoader())
    logger.info("Email template system initialized successfully")
except Exception as e:
    logger.error(f"Error initializing email template system: {e}")
    env = None


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """
    Send an email using SMTP.

    Args:
        to_email: Recipient's email address
        subject: Email subject
        html_content: HTML body of the email
        text_content: Plain text alternative (optional)

    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Validate email configuration
        if not EMAIL_HOST_PASSWORD:
            logger.error("EMAIL_HOST_PASSWORD not configured. Cannot send email.")
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM_EMAIL}>"
        message["To"] = to_email

        if text_content:
            part_text = MIMEText(text_content, "plain")
            message.attach(part_text)

        part_html = MIMEText(html_content, "html")
        message.attach(part_html)

        context = ssl.create_default_context()
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            if EMAIL_USE_TLS:
                server.starttls(context=context)
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(EMAIL_FROM_EMAIL, to_email, message.as_string())

        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

async def send_verification_email(email: str, user_id: int, activation_token: str = None) -> bool:
    """Send a verification email to a user."""
    if not activation_token:
        logger.error("Activation token is required for verification email")
        return False

    activation_url = f"{APP_BASE_URL}/activate?user_id={user_id}&token={activation_token}"
    subject = "Verify Your Email Address - MCP Multi-Context Memory System"

    if env:
        template = env.get_template("verification")
        html_content = template.render(username="User", activation_url=activation_url)
    else:
        html_content = f"Please click here to activate your account: {activation_url}"

    text_content = f"Please click the link below to activate your account:\n{activation_url}"
    return send_email(to_email=email, subject=subject, html_content=html_content, text_content=text_content)

async def send_password_reset_email(email: str, user_id: int, reset_token: str = None) -> bool:
    """Send a password reset email to a user."""
    if not reset_token:
        logger.error("Reset token is required for password reset email")
        return False

    reset_url = f"{APP_BASE_URL}/reset-password?user_id={user_id}&token={reset_token}"
    subject = "Reset Your Password - MCP Multi-Context Memory System"

    if env:
        template = env.get_template("password_reset")
        html_content = template.render(username="User", reset_url=reset_url)
    else:
        html_content = f"Please click here to reset your password: {reset_url}"

    text_content = f"Please click the link below to reset your password:\n{reset_url}"
    return send_email(to_email=email, subject=subject, html_content=html_content, text_content=text_content)
