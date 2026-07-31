"""
FlyoraGo Top MNC-Grade Premium Email Design System
Modeled directly after modern high-end technology company notifications.
Features custom transparent logo, 3D hero illustrations, status cards, and dark-teal brand footer.
"""

from django.conf import settings
from .sanitizer import sanitize_context, sanitize_value

LOGO_BASE64 = "{logo_b64}"

def get_master_layout(title: str, badge_text: str, badge_type: str, body_html: str, ref_id: str = "FG-ACCT-NOTICE-2026", hero_title: str = "Account Status Notice") -> str:
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    # Status Pill Styling
    badge_configs = {{
        'danger':  {{'bg': '#fde8e8', 'border': '#fca5a5', 'text': '#dc2626', 'icon': '🔒'}},
        'success': {{'bg': '#dcfce7', 'border': '#86efac', 'text': '#15803d', 'icon': '✓'}},
        'info':    {{'bg': '#e0f2fe', 'border': '#7dd3fc', 'text': '#0369a1', 'icon': '⚡'}},
        'warning': {{'bg': '#fef3c7', 'border': '#fde68a', 'text': '#b45309', 'icon': '🔑'}},
        'neutral': {{'bg': '#f1f5f9', 'border': '#e2e8f0', 'text': '#475569', 'icon': 'ℹ'}},
    }}
    cfg = badge_configs.get(badge_type, badge_configs['neutral'])

    badge_html = ""
    if badge_text:
        badge_html = f"""
        <div style="display: inline-block; padding: 6px 16px; background-color: {cfg['bg']}; border: 1px solid {cfg['border']}; border-radius: 8px; color: {cfg['text']}; font-size: 13px; font-weight: 800; letter-spacing: 0.05em; margin-bottom: 12px;">
            <span style="margin-right: 6px;">{cfg['icon']}</span> {badge_text}
        </div>
        """

    # Dynamic 3D Illustration SVG for Hero Section (Parcel Box with Cyan Airplane Trail)
    hero_illustration = """
    <svg width="140" height="110" viewBox="0 0 200 150" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 75 C 60 120, 140 120, 185 30" stroke="#0d9488" stroke-width="6" stroke-linecap="round" fill="none" opacity="0.8" />
        <path d="M175 25 L190 28 L182 42 Z" fill="#0d9488" />
        <rect x="75" y="35" width="65" height="65" rx="10" fill="#0d9488" transform="rotate(-10 107 67)" />
        <rect x="82" y="42" width="51" height="51" rx="6" fill="#14b8a6" transform="rotate(-10 107 67)" />
        <path d="M90 60 L125 54" stroke="#ffffff" stroke-width="4" stroke-linecap="round" />
        <path d="M105 45 L99 80" stroke="#ffffff" stroke-width="4" stroke-linecap="round" />
        <circle cx="45" cy="75" r="4" fill="#0d9488" opacity="0.6" />
        <circle cx="30" cy="68" r="3" fill="#14b8a6" opacity="0.4" />
    </svg>
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #0f172a;
            -webkit-font-smoothing: antialiased;
        }}
        table {{ border-collapse: collapse; }}
        a {{ color: #0d9488; text-decoration: none; }}
    </style>
</head>
<body style="margin: 0; padding: 36px 16px; background-color: #f1f5f9;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center">
                <!-- Main MNC Outer Container -->
                <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);" cellspacing="0" cellpadding="0" border="0">
                    
                    <!-- Top Header -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #ffffff;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <td valign="middle">
                                        <a href="{site_url}" target="_blank" style="text-decoration: none; display: inline-flex; align-items: center;">
                                            <img src="data:image/png;base64,{LOGO_BASE64}" alt="Flyorago" style="height: 38px; width: auto; vertical-align: middle; margin-right: 8px;" />
                                            <span style="font-size: 24px; font-weight: 800; color: #0d9488; letter-spacing: -0.03em; vertical-align: middle;">Flyorago</span>
                                        </a>
                                    </td>
                                    <td align="right" valign="middle">
                                        <span style="font-size: 13px; font-weight: 600; color: #475569;">
                                            Official Notice 
                                            <span style="display: inline-block; width: 16px; height: 16px; background-color: #0d9488; color: #ffffff; border-radius: 50%; text-align: center; line-height: 16px; font-size: 10px; font-weight: 800; margin-left: 4px;">✓</span>
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Hero Banner Card -->
                    <tr>
                        <td style="padding: 0 32px;">
                            <table role="presentation" width="100%" style="background: linear-gradient(135deg, #e6f7f5 0%, #f0fbf9 100%); border: 1px solid #ccfbf1; border-radius: 16px; padding: 24px 22px;" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <td valign="middle" style="width: 65%;">
                                        <h1 style="font-size: 24px; font-weight: 800; color: #0f172a; margin: 0 0 10px 0; line-height: 1.2; letter-spacing: -0.02em;">
                                            {hero_title}
                                        </h1>
                                        {badge_html}
                                        <div style="font-size: 12px; font-weight: 700; color: #0d9488; margin-top: 6px;">
                                            Reference ID: {ref_id}
                                        </div>
                                    </td>
                                    <td align="right" valign="middle" style="width: 35%;">
                                        {hero_illustration}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 28px 32px;">
                            {body_html}
                        </td>
                    </tr>

                    <!-- Footer Sign-off & Dark Teal Banner -->
                    <tr>
                        <td style="padding: 0 32px 32px 32px;">
                            <p style="margin: 0 0 4px 0; font-size: 14px; color: #475569;">Thank you,</p>
                            <p style="margin: 0 0 24px 0; font-size: 14px; font-weight: 700; color: #0f172a;">The <span style="color: #0d9488;">Flyorago</span> Team</p>

                            <!-- Dark Teal Banner -->
                            <table role="presentation" width="100%" style="background-color: #0d9488; border-radius: 14px; padding: 16px 20px; color: #ffffff;" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <td valign="middle">
                                        <div style="font-size: 13px; font-weight: 600;">
                                            <span style="display: inline-block; width: 22px; height: 22px; background: rgba(255,255,255,0.2); border-radius: 50%; text-align: center; line-height: 22px; margin-right: 4px;">f</span>
                                            <span style="display: inline-block; width: 22px; height: 22px; background: rgba(255,255,255,0.2); border-radius: 50%; text-align: center; line-height: 22px; margin-right: 4px;">📷</span>
                                            <span style="display: inline-block; width: 22px; height: 22px; background: rgba(255,255,255,0.2); border-radius: 50%; text-align: center; line-height: 22px; margin-right: 4px;">in</span>
                                            <span style="display: inline-block; width: 22px; height: 22px; background: rgba(255,255,255,0.2); border-radius: 50%; text-align: center; line-height: 22px;">𝕏</span>
                                        </div>
                                    </td>
                                    <td align="right" valign="middle" style="font-size: 12px; font-weight: 600; color: #ffffff;">
                                        <a href="{site_url}" style="color: #ffffff; text-decoration: none;">flyorago.me</a> &nbsp;|&nbsp; © 2026 Flyorago. All rights reserved.
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html


# ─── REUSABLE MNC COMPONENTS ──────────────────────────────────────────────

def component_alert_box(title: str, text: str, alert_type: str = "danger") -> str:
    """
    Renders the MNC callout box (e.g. Restriction Details with red left border).
    """
    styles = {
        'danger':  {'bg': '#fef2f2', 'border': '#ef4444', 'title': '#b91c1c', 'text': '#991b1b', 'icon': '!'},
        'success': {'bg': '#f0fdf4', 'border': '#22c55e', 'title': '#15803d', 'text': '#166534', 'icon': '✓'},
        'info':    {'bg': '#f0f9ff', 'border': '#0ea5e9', 'title': '#0369a1', 'text': '#075985', 'icon': 'ℹ'},
    }
    st = styles.get(alert_type, styles['danger'])

    return f"""
    <table role="presentation" width="100%" style="background-color: {st['bg']}; border-left: 4px solid {st['border']}; border-radius: 8px; margin: 20px 0;" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td style="padding: 16px 18px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td valign="top" style="width: 36px;">
                            <div style="width: 26px; height: 26px; border: 2px solid {st['border']}; border-radius: 50%; text-align: center; line-height: 24px; font-weight: 800; color: {st['border']}; font-size: 14px;">
                                {st['icon']}
                            </div>
                        </td>
                        <td valign="top">
                            <div style="font-size: 15px; font-weight: 700; color: {st['title']}; margin-bottom: 4px;">{title}</div>
                            <div style="font-size: 14px; color: {st['text']}; line-height: 1.5;">{text}</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """

def component_status_card(title: str, rows: list) -> str:
    """
    Renders the ACCOUNT STATUS card with cyan circular icons and dotted dividers.
    rows: list of tuples (icon_char, label, formatted_value_html)
    """
    rows_html = ""
    total = len(rows)
    for idx, row in enumerate(rows):
        icon_char, label, val_html = row[0], row[1], row[2]
        border_style = "border-bottom: 1px dotted #99f6e4;" if idx < total - 1 else ""
        
        rows_html += f"""
        <tr>
            <td style="padding: 12px 0; {border_style}">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td valign="middle" style="width: 40px;">
                            <div style="width: 30px; height: 30px; background-color: #ccfbf1; border-radius: 50%; text-align: center; line-height: 30px; font-size: 14px; color: #0d9488; font-weight: 700;">
                                {icon_char}
                            </div>
                        </td>
                        <td valign="middle" style="font-size: 14px; color: #475569; font-weight: 600;">
                            {label}
                        </td>
                        <td align="right" valign="middle" style="font-size: 14px;">
                            {val_html}
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """

    return f"""
    <div style="background-color: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 14px; padding: 18px 20px; margin: 20px 0;">
        <div style="font-size: 13px; font-weight: 800; color: #0d9488; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px;">
            {title}
        </div>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
            {rows_html}
        </table>
    </div>
    """

def component_support_box(text: str, button_text: str, button_url: str) -> str:
    """
    Renders the Support Card with headset icon and solid Teal button.
    """
    return f"""
    <table role="presentation" width="100%" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; margin: 20px 0;" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td style="padding: 16px 18px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td valign="middle" style="width: 42px;">
                            <div style="width: 32px; height: 32px; background-color: #e0f2fe; border-radius: 50%; text-align: center; line-height: 32px; font-size: 16px;">
                                🎧
                            </div>
                        </td>
                        <td valign="middle" style="font-size: 13px; color: #475569; line-height: 1.5; padding-right: 12px;">
                            {text}
                        </td>
                        <td align="right" valign="middle" style="width: 140px;">
                            <a href="{button_url}" target="_blank" style="display: inline-block; background-color: #0d9488; color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 700; padding: 10px 18px; border-radius: 8px;">
                                {button_text} &gt;
                            </a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """


# ─── SPECIFIC EMAIL BUILDERS ─────────────────────────────────────────────

def build_account_restricted_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    reason = ctx.get('blockReason', 'Account temporarily restricted by system administration.')
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    subject = "Important: Your Flyorago account has been restricted"
    
    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 20px 0;">
        Your Flyorago account has been temporarily restricted by an administrator.
    </p>

    {component_alert_box('Restriction Details', f'<strong>Reason:</strong> {reason}', 'danger')}

    {component_status_card('ACCOUNT STATUS', [
        ('👤', 'Current Status', '<span style="color: #dc2626; font-weight: 800;">RESTRICTED</span>'),
        ('⏸', 'Impact', '<span style="color: #0f172a; font-weight: 700;">Login and active features are paused</span>')
    ])}

    {component_support_box(
        'If you believe this restriction was made in error or would like to request a review, please contact our support team.',
        'Contact Support',
        'mailto:support@flyorago.tech'
    )}
    """

    html = get_master_layout(
        title=subject,
        badge_text="RESTRICTED",
        badge_type="danger",
        body_html=body,
        ref_id="FG-ACCT-RESTRICT-2026",
        hero_title="Account Status Notice"
    )
    text = f"Hi {email_or_name},
Your Flyorago account has been restricted.
Reason: {reason}
Contact support@flyorago.tech"
    return subject, html, text

def build_account_reactivated_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    subject = "Your Flyorago account has been reactivated"

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 20px 0;">
        We are pleased to inform you that your Flyorago account has been successfully reactivated and restored to full active status.
    </p>

    {component_alert_box('Account Restored', 'Your account is in good standing. You can now use all Flyorago features.', 'success')}

    {component_status_card('ACCOUNT STATUS', [
        ('👤', 'Current Status', '<span style="color: #15803d; font-weight: 800;">ACTIVE</span>'),
        ('⚡', 'Access Level', '<span style="color: #0f172a; font-weight: 700;">Full Access Restored</span>')
    ])}

    {component_support_box(
        'Ready to continue? Sign in to access your trips, bookings, and wallet.',
        'Open Flyorago',
        f'{site_url}/login'
    )}
    """

    html = get_master_layout(
        title=subject,
        badge_text="ACTIVE",
        badge_type="success",
        body_html=body,
        ref_id="FG-ACCT-ACTIVE-2026",
        hero_title="Account Reactivated"
    )
    text = f"Hi {email_or_name},
Your Flyorago account has been reactivated.
Login: {site_url}/login"
    return subject, html, text

def build_welcome_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    subject = "Welcome to Flyorago"

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 20px 0;">
        Welcome to Flyorago — the premier global travel and luggage sharing marketplace. Your account is officially active.
    </p>

    {component_status_card('MARKETPLACE FEATURES', [
        ('✈️', 'For Travelers', '<span style="color: #0f172a; font-weight: 700;">Monetize unused flight luggage capacity</span>'),
        ('📦', 'For Senders', '<span style="color: #0f172a; font-weight: 700;">Ship parcels worldwide via verified travelers</span>')
    ])}

    {component_support_box(
        'Explore available flights or list your upcoming travel plans today.',
        'Explore Flyorago',
        site_url
    )}
    """

    html = get_master_layout(
        title=subject,
        badge_text="WELCOME",
        badge_type="info",
        body_html=body,
        ref_id="FG-USER-WELCOME-2026",
        hero_title="Welcome to Flyorago"
    )
    text = f"Welcome {email_or_name}!
Your Flyorago account is ready.
Visit: {site_url}"
    return subject, html, text

def build_verification_otp_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    otp = ctx.get('otp', '000000')

    subject = "Verify your Flyorago email address"

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 20px 0;">
        Please use the 6-digit verification code below to verify your email address:
    </p>

    <div style="background-color: #f0fdfa; border: 2px dashed #0d9488; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
        <div style="font-size: 12px; font-weight: 800; color: #0d9488; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;">VERIFICATION CODE</div>
        <div style="font-size: 34px; font-weight: 900; color: #0f172a; letter-spacing: 0.3em;">{otp}</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 8px;">Valid for 10 minutes. Do not share this code with anyone.</div>
    </div>

    {component_alert_box('Security Notice', 'If you did not request this code, you can safely ignore this email.', 'info')}
    """

    html = get_master_layout(
        title=subject,
        badge_text="SECURITY",
        badge_type="warning",
        body_html=body,
        ref_id="FG-AUTH-VERIFY-2026",
        hero_title="Email Verification"
    )
    text = f"Hi {email_or_name},
Your Flyorago verification code is: {otp}"
    return subject, html, text

def build_password_reset_otp_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    otp = ctx.get('otp', '000000')

    subject = "Reset your Flyorago password"

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 20px 0;">
        We received a request to reset your password. Use the code below:
    </p>

    <div style="background-color: #fffbeb; border: 2px dashed #f59e0b; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
        <div style="font-size: 12px; font-weight: 800; color: #b45309; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;">RESET CODE</div>
        <div style="font-size: 34px; font-weight: 900; color: #0f172a; letter-spacing: 0.3em;">{otp}</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 8px;">Valid for 10 minutes.</div>
    </div>

    {component_alert_box('Security Warning', 'If you did not request a password reset, please contact support immediately.', 'danger')}
    """

    html = get_master_layout(
        title=subject,
        badge_text="RESET PASSWORD",
        badge_type="warning",
        body_html=body,
        ref_id="FG-AUTH-RESET-2026",
        hero_title="Password Reset Request"
    )
    text = f"Hi {email_or_name},
Your Flyorago password reset code is: {otp}"
    return subject, html, text

def build_kyc_status_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    status = ctx.get('status', 'PENDING').upper()
    reason = ctx.get('rejectionReason', '')
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    if status == 'APPROVED':
        subject = "Your Flyorago KYC Verification is Approved"
        body = f"""
        <p style="font-size: 15px; color: #334155;">Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,</p>
        <p style="font-size: 15px; color: #334155;">Your identity verification documents have been reviewed and approved.</p>
        {component_alert_box('Verification Complete', 'You now have full verified status on Flyorago.', 'success')}
        {component_status_card('KYC STATUS', [('✓', 'Status', '<span style="color: #15803d; font-weight: 800;">APPROVED</span>')])}
        {component_support_box('Check your profile status anytime on Flyorago.', 'View Profile', f'{site_url}/profile')}
        """
        b_type = 'success'
    elif status == 'REJECTED':
        subject = "Flyorago KYC Verification Update"
        body = f"""
        <p style="font-size: 15px; color: #334155;">Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,</p>
        <p style="font-size: 15px; color: #334155;">Our team reviewed your KYC submission and requires resubmission.</p>
        {component_alert_box('Review Details', f'<strong>Reason:</strong> {reason or "Document unreadable or invalid."}', 'danger')}
        {component_status_card('KYC STATUS', [('!', 'Status', '<span style="color: #dc2626; font-weight: 800;">REJECTED</span>')])}
        {component_support_box('Please upload valid documents to complete verification.', 'Resubmit KYC', f'{site_url}/kyc')}
        """
        b_type = 'danger'
    else:
        subject = "Your Flyorago KYC Verification Documents Received"
        body = f"""
        <p style="font-size: 15px; color: #334155;">Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,</p>
        <p style="font-size: 15px; color: #334155;">We received your KYC documents and are reviewing them.</p>
        {component_status_card('KYC STATUS', [('⏳', 'Status', '<span style="color: #0369a1; font-weight: 800;">UNDER REVIEW</span>')])}
        """
        b_type = 'info'

    html = get_master_layout(
        title=subject,
        badge_text=f"KYC {status}",
        badge_type=b_type,
        body_html=body,
        ref_id="FG-KYC-STATUS-2026",
        hero_title="KYC Verification Notice"
    )
    text = f"Hi {email_or_name},
Your Flyorago KYC status is: {status}"
    return subject, html, text

def build_generic_event_email(title: str, recipient_name: str, message: str, details: list = None, cta_text: str = None, cta_url: str = None, badge: str = "NOTICE", badge_type: str = "info") -> tuple:
    t_s = sanitize_value(title)
    n_s = sanitize_value(recipient_name)
    m_s = sanitize_value(message)

    status_rows = []
    if details:
        for d in details:
            if isinstance(d, (list, tuple)):
                status_rows.append(('•', d[0], f'<span style="color: #0f172a; font-weight: 700;">{d[1]}</span>'))
            elif isinstance(d, dict):
                status_rows.append(('•', d.get('label', ''), f'<span style="color: #0f172a; font-weight: 700;">{d.get("value", "")}</span>'))

    card_html = component_status_card('DETAILS', status_rows) if status_rows else ''
    sup_html = component_support_box('Need help? Contact Flyorago support.', cta_text or 'Open Flyorago', cta_url or 'https://flyorago.me') if (cta_text and cta_url) else ''

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{n_s}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 20px 0;">
        {m_s}
    </p>
    {card_html}
    {sup_html}
    """
    html = get_master_layout(
        title=t_s,
        badge_text=badge,
        badge_type=badge_type,
        body_html=body,
        ref_id="FG-EVENT-NOTICE-2026",
        hero_title=t_s
    )
    text = f"Hi {n_s},
{m_s}"
    return t_s, html, text
