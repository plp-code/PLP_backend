import resend
from src.python.app.core.config import settings

resend.api_key = settings.RESEND_API_KEY


BRAND_NAME = "The Preloved Professional"

COLOR_PARCHMENT = "#f4f0e8"
COLOR_MAROON = "#3d0b19"
COLOR_MAROON_SOFT = "#624045"
COLOR_BLUSH = "#ffe8de"
COLOR_SECONDARY = "#cdc9c3"
COLOR_SECONDARY_DARK = "#9a958e"
COLOR_INK = "#1a1014"

FONT_STACK = "'Bodoni Moda', 'Prata', Georgia, 'Times New Roman', serif"


def _email_shell(preheader: str, title: str, body_html: str, footnote: str) -> str:
    """
    Shared retro 'beveled window' shell so every transactional email matches
    the site's PLP visual system. Inline styles throughout since most email
    clients strip <head><style> blocks.
    """
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta name="color-scheme" content="light">
        <meta name="supported-color-schemes" content="light">
      </head>
      <body style="margin:0; padding:0; background-color:{COLOR_PARCHMENT}; font-family:{FONT_STACK};">
        <!-- preheader, hidden -->
        <div style="display:none; max-height:0; overflow:hidden; opacity:0;">{preheader}</div>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{COLOR_PARCHMENT}; padding:32px 16px;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" style="max-width:480px; background-color:{COLOR_SECONDARY_DARK}20; border:1px solid {COLOR_INK}; box-shadow:3px 3px 0 0 rgba(0,0,0,0.18);" cellpadding="0" cellspacing="0">

                <!-- titlebar -->
                <tr>
                  <td style="background-color:{COLOR_MAROON}; padding:14px 24px; box-shadow: inset 0 -1px rgba(0,0,0,0.35);">
                    <span style="color:{COLOR_PARCHMENT}; font-family:{FONT_STACK}; font-size:14px; letter-spacing:0.08em; text-transform:uppercase;">
                      {BRAND_NAME}
                    </span>
                  </td>
                </tr>

                <!-- body -->
                <tr>
                  <td style="background-color:#ffffff; padding:32px 28px; color:{COLOR_INK};">
                    <h1 style="font-family:{FONT_STACK}; font-size:22px; color:{COLOR_MAROON}; margin:0 0 16px 0;">
                      {title}
                    </h1>
                    {body_html}
                  </td>
                </tr>

                <!-- footer -->
                <tr>
                  <td style="background-color:{COLOR_BLUSH}; padding:16px 28px; border-top:1px solid {COLOR_SECONDARY_DARK};">
                    <p style="font-family:{FONT_STACK}; font-size:12px; color:{COLOR_MAROON_SOFT}; margin:0; line-height:1.6;">
                      {footnote}
                    </p>
                  </td>
                </tr>

              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


def _plp_button(href: str, label: str) -> str:
    return f"""
    <div style="margin:28px 0;">
      <a href="{href}"
         style="background-color:{COLOR_MAROON}; color:{COLOR_PARCHMENT}; padding:12px 28px;
                text-decoration:none; font-family:{FONT_STACK}; font-weight:600; letter-spacing:0.02em;
                display:inline-block; border:1px solid {COLOR_INK}; box-shadow:2px 2px 0 0 rgba(0,0,0,0.18);">
        {label}
      </a>
    </div>
    """


def _plp_link_fallback(href: str) -> str:
    return f"""
    <hr style="border:none; border-top:1px solid {COLOR_SECONDARY}; margin:28px 0 16px 0;" />
    <p style="font-family:{FONT_STACK}; font-size:12px; color:{COLOR_MAROON_SOFT}; margin:0;">
      Or copy and paste this URL into your browser:<br/>
      <a href="{href}" style="color:{COLOR_MAROON};">{href}</a>
    </p>
    """


async def send_password_reset_email(to_email: str, reset_token: str, has_password: bool) -> None:
    """
    Sends a password set/reset email using Resend. Same mechanism whether
    the account has no password yet (post-purchase guest) or already has
    one and is resetting it.
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    if has_password:
        intro = "You requested a password reset. Click below to set a new password for your account."
        title = "Reset Your Password"
        subject = "Reset your password"
    else:
        intro = "Set a password so you can log back in anytime and see everything you've bought."
        title = "Set Your Password"
        subject = "Set your password"

    body_html = f"""
      <p style="font-family:{FONT_STACK}; font-size:15px; line-height:1.6; margin:0 0 8px 0;">
        {intro}
      </p>
      {_plp_button(reset_link, title)}
      <p style="font-family:{FONT_STACK}; font-size:13px; color:{COLOR_MAROON_SOFT}; margin:0;">
        This link is valid for <strong>15 minutes</strong>. If you did not request this, you can safely ignore it.
      </p>
      {_plp_link_fallback(reset_link)}
    """

    html_content = _email_shell(
        preheader=title,
        title=title,
        body_html=body_html,
        footnote=f"{BRAND_NAME} &middot; this link expires in 15 minutes",
    )

    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    })


async def send_magic_login_email(to_email: str, login_token: str) -> None:
    """
    Sends a one-time login link using Resend, for guest accounts logging
    back in without a password.
    """
    login_link = f"{settings.FRONTEND_URL}/magic-login?token={login_token}"

    body_html = f"""
      <p style="font-family:{FONT_STACK}; font-size:15px; line-height:1.6; margin:0 0 8px 0;">
        Click below to log in. No password needed.
      </p>
      {_plp_button(login_link, "Log In")}
      <p style="font-family:{FONT_STACK}; font-size:13px; color:{COLOR_MAROON_SOFT}; margin:0;">
        This link is valid for <strong>20 minutes</strong> and can only be used once.
        If you did not request this, you can safely ignore it.
      </p>
      {_plp_link_fallback(login_link)}
    """

    html_content = _email_shell(
        preheader="Your one-time login link",
        title="Log In",
        body_html=body_html,
        footnote=f"{BRAND_NAME} &middot; this link expires in 20 minutes and works once",
    )

    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [to_email],
        "subject": "Your login link",
        "html": html_content,
    })
    
    
async def send_email_verification(to_email: str, verification_token: str) -> None:
    """
    Sends an email verification link using Resend, for accounts that signed up
    with a password and need to confirm they own the inbox.
    """
    verify_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

    body_html = f"""
      <p style="font-family:{FONT_STACK}; font-size:15px; line-height:1.6; margin:0 0 8px 0;">
        Welcome! Confirm your email address to finish setting up your account.
      </p>
      {_plp_button(verify_link, "Verify Email")}
      <p style="font-family:{FONT_STACK}; font-size:13px; color:{COLOR_MAROON_SOFT}; margin:0 0 8px 0;">
        This link is valid for <strong>24 hours</strong>. You may be asked to log in
        first so we can confirm the link belongs to your account.
        If you did not create an account, you can safely ignore this email.
      </p>
      {_plp_link_fallback(verify_link)}
    """

    html_content = _email_shell(
        preheader="Confirm your email address",
        title="Verify Your Email",
        body_html=body_html,
        footnote=f"{BRAND_NAME} &middot; this link expires in 24 hours",
    )

    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [to_email],
        "subject": "Verify your email address",
        "html": html_content,
    })