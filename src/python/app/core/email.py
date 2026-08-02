import resend
from src.python.app.core.config import settings

resend.api_key = settings.RESEND_API_KEY


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    """
    Sends a password reset email using Resend.
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 500px; margin: 0 auto; padding: 20px;">
          <h2>Reset Your Password</h2>
          <p>You requested a password reset. Click the button below to set a new password for your account.</p>
          <div style="margin: 30px 0;">
            <a href="{reset_link}" 
               style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
               Reset Password
            </a>
          </div>
          <p style="font-size: 14px; color: #666;">This link is valid for <strong>15 minutes</strong>. If you did not request this email, you can safely ignore it.</p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;" />
          <p style="font-size: 12px; color: #999;">Or copy and paste this URL into your browser: <br/><a href="{reset_link}" style="color: #2563eb;">{reset_link}</a></p>
        </div>
      </body>
    </html>
    """

    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [to_email],
        "subject": "Reset your password",
        "html": html_content,
    })