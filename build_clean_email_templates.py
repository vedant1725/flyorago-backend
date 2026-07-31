import os

template_code = '''"""
FlyoraGo Google/Stripe-Grade Clean & Bulletproof Email Templates
Designed specifically for 100% pixel-perfect rendering in Gmail, Outlook, Apple Mail, and mobile screens.
Zero flexbox, Zero SVG tags, Zero Base64 imagery. Uses pure web-safe HTML table structure.
"""

from django.conf import settings
from .sanitizer import sanitize_context, sanitize_value

def get_master_layout(title: str, badge_text: str, badge_type: str, body_html: str, ref_id: str = "FG-ACCT-NOTICE-2026", hero_title: str = "Account Status Notice") -> str:
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    # Badge Colors (Pure HTML inline styles)
    badge_configs = {
        'danger':  {'bg': '#fef2f2', 'border': '#fecaca', 'text': '#dc2626', 'label': 'RESTRICTED'},
        'success': {'bg': '#f0fdf4', 'border': '#bbf7d0', 'text': '#166534', 'label': 'ACTIVE'},
        'info':    {'bg': '#f0f9ff', 'border': '#bae6fd', 'text': '#0369a1', 'label': 'NOTICE'},
        'warning': {'bg': '#fffbeb', 'border': '#fde68a', 'text': '#b45309', 'label': 'SECURITY'},
        'neutral': {'bg': '#f8fafc', 'border': '#e2e8f0', 'text': '#475569', 'label': 'NOTICE'},
    }
    cfg = badge_configs.get(badge_type, badge_configs['neutral'])
    actual_badge_text = badge_text or cfg['label']

    badge_html = f"""
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="display: inline-block;">
        <tr>
            <td style="background-color: {cfg['bg']}; border: 1px solid {cfg['border']}; border-radius: 6px; padding: 4px 12px; font-family: Arial, Helvetica, sans-serif; font-size: 12px; font-weight: 800; color: {cfg['text']}; letter-spacing: 0.5px;">
                {actual_badge_text}
            </td>
        </tr>
    </table>
    """

    html = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: Arial, Helvetica, sans-serif; -webkit-font-smoothing: antialiased;">

    <!-- Outer Envelope Table -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f8fafc; padding: 30px 10px;">
        <tr>
            <td align="center">

                <!-- Main White Container -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 580px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding: 24px 28px; border-bottom: 1px solid #f1f5f9;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <!-- Logo Mark & Text -->
                                    <td valign="middle">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                            <tr>
                                                <td style="width: 36px; height: 36px; background-color: #0d9488; border-radius: 8px; text-align: center; vertical-align: middle; color: #ffffff; font-size: 20px; font-weight: 900; font-family: Arial, sans-serif;">
                                                    ✈
                                                </td>
                                                <td style="padding-left: 10px; font-size: 22px; font-weight: 800; color: #0d9488; font-family: Arial, sans-serif; letter-spacing: -0.5px;">
                                                    Flyora<span style="color: #0f172a;">Go</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                    <!-- Official Badge -->
                                    <td align="right" valign="middle" style="font-size: 12px; font-weight: 700; color: #64748b; font-family: Arial, sans-serif;">
                                        Official Notice <span style="color: #0d9488; font-size: 14px;">✔</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Hero Banner Card -->
                    <tr>
                        <td style="padding: 24px 28px 10px 28px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 12px; padding: 20px 24px;">
                                <tr>
                                    <td>
                                        <div style="font-size: 22px; font-weight: 800; color: #0f172a; margin-bottom: 10px; font-family: Arial, sans-serif;">
                                            {hero_title}
                                        </div>
                                        <div style="margin-bottom: 8px;">
                                            {badge_html}
                                        </div>
                                        <div style="font-size: 12px; font-weight: 700; color: #0d9488; font-family: Arial, sans-serif;">
                                            Reference ID: {ref_id}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 20px 28px 24px 28px; font-family: Arial, sans-serif;">
                            {body_html}
                        </td>
                    </tr>

                    <!-- Footer Sign-Off & Legal Links -->
                    <tr>
                        <td style="padding: 0 28px 28px 28px; font-family: Arial, sans-serif;">
                            <div style="font-size: 14px; color: #475569; margin-bottom: 4px;">Thank you,</div>
                            <div style="font-size: 14px; font-weight: 800; color: #0f172a; margin-bottom: 24px;">
                                The <span style="color: #0d9488;">FlyoraGo</span> Team
                            </div>

                            <!-- Footer Divider & Copyright -->
                            <div style="border-top: 1px solid #e2e8f0; padding-top: 16px;">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td style="font-size: 12px; color: #64748b; font-family: Arial, sans-serif;">
                                            <strong>FlyoraGo</strong> — Safe. Simple. Trusted Global Network.
                                        </td>
                                        <td align="right" style="font-size: 12px; color: #64748b; font-family: Arial, sans-serif;">
                                            <a href="{site_url}" style="color: #0d9488; text-decoration: none; font-weight: 700;">flyorago.me</a> &nbsp;|&nbsp; © 2026
                                        </td>
                                    </tr>
                                </table>
                            </div>
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


# ─── BULLETPROOF COMPONENT BUILDERS ──────────────────────────────────────────

def component_alert_box(title: str, text: str, alert_type: str = "danger") -> str:
    styles = {
        'danger':  {'bg': '#fef2f2', 'border': '#ef4444', 'title': '#b91c1c', 'text': '#991b1b', 'icon': '⚠'},
        'success': {'bg': '#f0fdf4', 'border': '#22c55e', 'title': '#15803d', 'text': '#166534', 'icon': '✓'},
        'info':    {'bg': '#f0f9ff', 'border': '#0ea5e9', 'title': '#0369a1', 'text': '#075985', 'icon': 'ℹ'},
    }
    st = styles.get(alert_type, styles['danger'])

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: {st['bg']}; border-left: 4px solid {st['border']}; border-radius: 6px; margin: 18px 0;">
        <tr>
            <td style="padding: 14px 16px; font-family: Arial, sans-serif;">
                <div style="font-size: 14px; font-weight: 800; color: {st['title']}; margin-bottom: 4px;">
                    <span style="margin-right: 6px;">{st['icon']}</span> {title}
                </div>
                <div style="font-size: 13px; color: {st['text']}; line-height: 1.5;">
                    {text}
                </div>
            </td>
        </tr>
    </table>
    """

def component_status_card(title: str, rows: list) -> str:
    rows_html = ""
    total = len(rows)
    for idx, row in enumerate(rows):
        label, val_html = row[0], row[1]
        border_style = "border-bottom: 1px solid #e2e8f0;" if idx < total - 1 else ""
        
        rows_html += f"""
        <tr>
            <td style="padding: 10px 0; font-size: 13px; color: #64748b; font-weight: 700; font-family: Arial, sans-serif; {border_style}">
                {label}
            </td>
            <td align="right" style="padding: 10px 0; font-size: 14px; font-family: Arial, sans-serif; {border_style}">
                {val_html}
            </td>
        </tr>
        """

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; margin: 18px 0;">
        <tr>
            <td style="padding: 16px 18px; font-family: Arial, sans-serif;">
                <div style="font-size: 11px; font-weight: 800; color: #0d9488; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                    {title}
                </div>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    {rows_html}
                </table>
            </td>
        </tr>
    </table>
    """

def component_support_box(text: str, button_text: str, button_url: str) -> str:
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; margin: 20px 0;">
        <tr>
            <td style="padding: 16px 18px; font-family: Arial, sans-serif;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td valign="middle" style="font-size: 13px; color: #475569; line-height: 1.5; padding-right: 12px;">
                            {text}
                        </td>
                        <td align="right" valign="middle" style="width: 140px;">
                            <a href="{button_url}" target="_blank" style="display: inline-block; background-color: #0d9488; color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 800; padding: 10px 16px; border-radius: 6px; font-family: Arial, sans-serif; text-align: center;">
                                {button_text} &rarr;
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

    subject = "Important: Your FlyoraGo account has been restricted"
    
    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 12px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        Your FlyoraGo account has been temporarily restricted by an administrator.
    </p>

    {component_alert_box('Restriction Details', f'<strong>Reason:</strong> {reason}', 'danger')}

    {component_status_card('ACCOUNT STATUS', [
        ('Current Status', '<span style="color: #dc2626; font-weight: 800;">RESTRICTED</span>'),
        ('Impact', '<span style="color: #0f172a; font-weight: 700;">Login and active features are paused</span>')
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
    text = f"Hi {email_or_name},\\nYour FlyoraGo account has been restricted.\\nReason: {reason}\\nContact support@flyorago.tech"
    return subject, html, text

def build_account_reactivated_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    subject = "Your FlyoraGo account has been reactivated"

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 12px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        We are pleased to inform you that your FlyoraGo account has been successfully reactivated and restored to full active status.
    </p>

    {component_alert_box('Account Restored', 'Your account is in good standing. You can now use all FlyoraGo features.', 'success')}

    {component_status_card('ACCOUNT STATUS', [
        ('Current Status', '<span style="color: #166534; font-weight: 800;">ACTIVE</span>'),
        ('Access Level', '<span style="color: #0f172a; font-weight: 700;">Full Access Restored</span>')
    ])}

    {component_support_box(
        'Ready to continue? Sign in to access your trips, bookings, and wallet.',
        'Open FlyoraGo',
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
    text = f"Hi {email_or_name},\\nYour FlyoraGo account has been reactivated.\\nLogin: {site_url}/login"
    return subject, html, text

def build_welcome_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    subject = "Welcome to FlyoraGo"

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 12px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        Welcome to FlyoraGo — the premier global travel and luggage sharing marketplace. Your account is ready.
    </p>

    {component_status_card('MARKETPLACE FEATURES', [
        ('For Travelers', '<span style="color: #0f172a; font-weight: 700;">Monetize unused flight luggage capacity</span>'),
        ('For Senders', '<span style="color: #0f172a; font-weight: 700;">Ship parcels worldwide via verified travelers</span>')
    ])}

    {component_support_box(
        'Explore available flights or list your upcoming travel plans today.',
        'Explore FlyoraGo',
        site_url
    )}
    """

    html = get_master_layout(
        title=subject,
        badge_text="WELCOME",
        badge_type="info",
        body_html=body,
        ref_id="FG-USER-WELCOME-2026",
        hero_title="Welcome to FlyoraGo"
    )
    text = f"Welcome {email_or_name}!\\nYour FlyoraGo account is ready.\\nVisit: {site_url}"
    return subject, html, text

def build_verification_otp_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    otp = ctx.get('otp', '000000')

    subject = "Verify your FlyoraGo email address"

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 12px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        Please use the 6-digit verification code below to confirm your email address:
    </p>

    <div style="background-color: #f0fdfa; border: 2px dashed #0d9488; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0; font-family: Arial, sans-serif;">
        <div style="font-size: 11px; font-weight: 800; color: #0d9488; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">VERIFICATION CODE</div>
        <div style="font-size: 32px; font-weight: 900; color: #0f172a; letter-spacing: 6px;">{otp}</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 6px;">Valid for 10 minutes. Do not share this code with anyone.</div>
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
    text = f"Hi {email_or_name},\\nYour FlyoraGo verification code is: {otp}"
    return subject, html, text

def build_password_reset_otp_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    otp = ctx.get('otp', '000000')

    subject = "Reset your FlyoraGo password"

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 12px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
        We received a request to reset your password. Use the code below:
    </p>

    <div style="background-color: #fffbeb; border: 2px dashed #f59e0b; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0; font-family: Arial, sans-serif;">
        <div style="font-size: 11px; font-weight: 800; color: #b45309; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">RESET CODE</div>
        <div style="font-size: 32px; font-weight: 900; color: #0f172a; letter-spacing: 6px;">{otp}</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 6px;">Valid for 10 minutes.</div>
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
    text = f"Hi {email_or_name},\\nYour FlyoraGo password reset code is: {otp}"
    return subject, html, text

def build_kyc_status_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    status = ctx.get('status', 'PENDING').upper()
    reason = ctx.get('rejectionReason', '')
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    if status == 'APPROVED':
        subject = "Your FlyoraGo KYC Verification is Approved"
        body = f"""
        <p style="font-size: 15px; color: #334155;">Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,</p>
        <p style="font-size: 15px; color: #334155;">Your identity verification documents have been reviewed and approved.</p>
        {component_alert_box('Verification Complete', 'You now have full verified status on FlyoraGo.', 'success')}
        {component_status_card('KYC STATUS', [('Status', '<span style="color: #166534; font-weight: 800;">APPROVED</span>')])}
        {component_support_box('Check your profile status anytime on FlyoraGo.', 'View Profile', f'{site_url}/profile')}
        """
        b_type = 'success'
    elif status == 'REJECTED':
        subject = "FlyoraGo KYC Verification Update"
        body = f"""
        <p style="font-size: 15px; color: #334155;">Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,</p>
        <p style="font-size: 15px; color: #334155;">Our team reviewed your KYC submission and requires resubmission.</p>
        {component_alert_box('Review Details', f'<strong>Reason:</strong> {reason or "Document unreadable or invalid."}', 'danger')}
        {component_status_card('KYC STATUS', [('Status', '<span style="color: #dc2626; font-weight: 800;">REJECTED</span>')])}
        {component_support_box('Please upload valid documents to complete verification.', 'Resubmit KYC', f'{site_url}/kyc')}
        """
        b_type = 'danger'
    else:
        subject = "Your FlyoraGo KYC Verification Documents Received"
        body = f"""
        <p style="font-size: 15px; color: #334155;">Hi <span style="color: #0d9488; font-weight: 700;">{email_or_name}</span>,</p>
        <p style="font-size: 15px; color: #334155;">We received your KYC documents and are reviewing them.</p>
        {component_status_card('KYC STATUS', [('Status', '<span style="color: #0369a1; font-weight: 800;">UNDER REVIEW</span>')])}
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
    text = f"Hi {email_or_name},\\nYour FlyoraGo KYC status is: {status}"
    return subject, html, text

def build_generic_event_email(title: str, recipient_name: str, message: str, details: list = None, cta_text: str = None, cta_url: str = None, badge: str = "NOTICE", badge_type: str = "info") -> tuple:
    t_s = sanitize_value(title)
    n_s = sanitize_value(recipient_name)
    m_s = sanitize_value(message)

    status_rows = []
    if details:
        for d in details:
            if isinstance(d, (list, tuple)):
                status_rows.append((d[0], f'<span style="color: #0f172a; font-weight: 700;">{d[1]}</span>'))
            elif isinstance(d, dict):
                status_rows.append((d.get('label', ''), f'<span style="color: #0f172a; font-weight: 700;">{d.get("value", "")}</span>'))

    card_html = component_status_card('DETAILS', status_rows) if status_rows else ''
    sup_html = component_support_box('Need help? Contact FlyoraGo support.', cta_text or 'Open FlyoraGo', cta_url or 'https://flyorago.me') if (cta_text and cta_url) else ''

    body = f"""
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 12px 0;">
        Hi <span style="color: #0d9488; font-weight: 700;">{n_s}</span>,
    </p>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 16px 0;">
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
    text = f"Hi {n_s},\\n{m_s}"
    return t_s, html, text
'''

out_path = r'c:\Users\Akash\OneDrive\Documents\flyorago-backend\apps\notifications\email_service\templates.py'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(template_code)

print("Successfully written bulletproof clean templates.py! File size:", os.path.getsize(out_path))
