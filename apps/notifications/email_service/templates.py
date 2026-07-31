"""
FlyoraGo Ultra-Premium Google & Meta-Grade Transactional Email Templates
Features modern CSS keyframe animations (pulse, shimmer, glow), Google/Meta slate & teal card aesthetics,
bulletproof HTML table structure for 100% email client compatibility, and zero-overlap responsive layout.
"""

from django.conf import settings
from .sanitizer import sanitize_context, sanitize_value

def get_master_layout(title: str, badge_text: str, badge_type: str, body_html: str, ref_id: str = "FG-SEC-2026-X9", hero_title: str = "Account Status Notice") -> str:
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    # Badge Configuration (Meta/Google Color Palettes)
    badge_configs = {
        'danger':  {'bg': '#ffe4e6', 'border': '#f43f5e', 'text': '#e11d48', 'dot': '#f43f5e', 'label': 'RESTRICTED'},
        'success': {'bg': '#dcfce7', 'border': '#22c55e', 'text': '#15803d', 'dot': '#22c55e', 'label': 'ACTIVE'},
        'info':    {'bg': '#e0f2fe', 'border': '#38bdf8', 'text': '#0369a1', 'dot': '#0ea5e9', 'label': 'NOTICE'},
        'warning': {'bg': '#fef3c7', 'border': '#f59e0b', 'text': '#b45309', 'dot': '#f59e0b', 'label': 'SECURITY'},
        'neutral': {'bg': '#f1f5f9', 'border': '#94a3b8', 'text': '#475569', 'dot': '#64748b', 'label': 'NOTICE'},
    }
    cfg = badge_configs.get(badge_type, badge_configs['neutral'])
    actual_badge_text = badge_text or cfg['label']

    badge_html = f"""
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="display: inline-block;">
        <tr>
            <td style="background-color: {cfg['bg']}; border: 1px solid {cfg['border']}; border-radius: 20px; padding: 6px 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 12px; font-weight: 800; color: {cfg['text']}; letter-spacing: 0.5px;">
                <span class="pulse-dot" style="display: inline-block; width: 8px; height: 8px; background-color: {cfg['dot']}; border-radius: 50%; margin-right: 6px; vertical-align: middle;"></span>
                <span style="vertical-align: middle;">{actual_badge_text}</span>
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
    <style type="text/css">
        @keyframes pulseDot {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.2); opacity: 1; box-shadow: 0 0 8px rgba(13, 148, 136, 0.6); }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}
        .pulse-dot {{
            animation: pulseDot 2s infinite ease-in-out;
        }}
        .btn-action:hover {{
            background: linear-gradient(135deg, #0f766e 0%, #047857 100%) !important;
            box-shadow: 0 6px 20px rgba(13, 148, 136, 0.4) !important;
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; -webkit-font-smoothing: antialiased;">

    <!-- Outer Wrapper -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #0f172a; padding: 40px 12px;">
        <tr>
            <td align="center">

                <!-- Google / Meta Style White Container -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), 0 1px 3px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Top Branding Header -->
                    <tr>
                        <td style="padding: 28px 32px; background: #ffffff; border-bottom: 1px solid #f1f5f9;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <td valign="middle">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                            <tr>
                                                <td style="width: 42px; height: 42px; background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%); border-radius: 12px; text-align: center; vertical-align: middle; color: #ffffff; font-size: 22px; font-weight: 900; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);">
                                                    ✈
                                                </td>
                                                <td style="padding-left: 12px;">
                                                    <div style="font-size: 24px; font-weight: 900; color: #0f172a; letter-spacing: -0.8px; line-height: 1;">
                                                        Flyora<span style="color: #0d9488;">Go</span>
                                                    </div>
                                                    <div style="font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.5px; text-transform: uppercase; margin-top: 3px;">
                                                        Global Transport & Logistics
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                    <td align="right" valign="middle">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                            <tr>
                                                <td style="background-color: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 20px; padding: 6px 14px; font-size: 12px; font-weight: 700; color: #0d9488;">
                                                    Verified System Notice ✔
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Dark Luxury Hero Section (Google / Meta Dark Banner) -->
                    <tr>
                        <td style="padding: 0 32px 10px 32px; background-color: #ffffff;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top: 24px; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 18px; padding: 28px 28px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);">
                                <tr>
                                    <td>
                                        <div style="font-size: 26px; font-weight: 800; color: #ffffff; margin-bottom: 14px; letter-spacing: -0.5px; line-height: 1.2;">
                                            {hero_title}
                                        </div>
                                        <div style="margin-bottom: 12px;">
                                            {badge_html}
                                        </div>
                                        <div style="font-size: 12px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px; margin-top: 8px;">
                                            SYSTEM REF: <span style="color: #38bdf8;">{ref_id}</span>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Main Body Area -->
                    <tr>
                        <td style="padding: 24px 32px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
                            {body_html}
                        </td>
                    </tr>

                    <!-- Google / Meta Multi-Column Footer -->
                    <tr>
                        <td style="padding: 0 32px 36px 32px; background-color: #ffffff;">
                            <div style="border-top: 1px solid #e2e8f0; padding-top: 24px;">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td valign="top" style="font-size: 13px; color: #64748b; line-height: 1.6;">
                                            <strong style="color: #0f172a;">FlyoraGo Marketplace</strong><br />
                                            Official account & transaction notification service.
                                        </td>
                                        <td align="right" valign="top" style="font-size: 13px; color: #64748b; line-height: 1.6;">
                                            <a href="{site_url}" style="color: #0d9488; text-decoration: none; font-weight: 700;">flyorago.me</a><br />
                                            <a href="{site_url}/privacy" style="color: #64748b; text-decoration: underline;">Privacy</a> &bull; 
                                            <a href="{site_url}/terms" style="color: #64748b; text-decoration: underline;">Terms</a>
                                        </td>
                                    </tr>
                                </table>
                                <div style="margin-top: 18px; font-size: 11px; color: #94a3b8; text-align: center;">
                                    © 2026 FlyoraGo Technologies Inc. All rights reserved. Do not reply directly to this automated notification.
                                </div>
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


# ─── GOOGLE & META STYLE COMPONENTS ────────────────────────────────────────

def component_alert_box(title: str, text: str, alert_type: str = "danger") -> str:
    styles = {
        'danger':  {'bg': '#fff1f2', 'border': '#f43f5e', 'title': '#be123c', 'text': '#9f1239', 'icon': '🚨'},
        'success': {'bg': '#f0fdf4', 'border': '#22c55e', 'title': '#15803d', 'text': '#166534', 'icon': '✅'},
        'info':    {'bg': '#f0f9ff', 'border': '#0ea5e9', 'title': '#0369a1', 'text': '#075985', 'icon': '🛡️'},
    }
    st = styles.get(alert_type, styles['danger'])

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: {st['bg']}; border-left: 5px solid {st['border']}; border-radius: 10px; margin: 20px 0;">
        <tr>
            <td style="padding: 18px 20px;">
                <div style="font-size: 15px; font-weight: 800; color: {st['title']}; margin-bottom: 6px;">
                    <span style="margin-right: 6px;">{st['icon']}</span> {title}
                </div>
                <div style="font-size: 14px; color: {st['text']}; line-height: 1.6;">
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
            <td style="padding: 14px 0; font-size: 14px; color: #64748b; font-weight: 700; {border_style}">
                {label}
            </td>
            <td align="right" style="padding: 14px 0; font-size: 14px; {border_style}">
                {val_html}
            </td>
        </tr>
        """

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; margin: 20px 0;">
        <tr>
            <td style="padding: 20px 24px;">
                <div style="font-size: 12px; font-weight: 800; color: #0d9488; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;">
                    {title}
                </div>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    {rows_html}
                </table>
            </td>
        </tr>
    </table>
    """

def component_primary_button(text: str, url: str) -> str:
    return f"""
    <div style="margin: 28px 0; text-align: center;">
        <a href="{url}" class="btn-action" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #0d9488 0%, #059669 100%); color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 800; padding: 14px 34px; border-radius: 12px; box-shadow: 0 4px 14px rgba(13, 148, 136, 0.35); letter-spacing: 0.3px;">
            {text} &rarr;
        </a>
    </div>
    """


# ─── EMAIL BUILDERS ────────────────────────────────────────────────────────

def build_account_restricted_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    reason = ctx.get('blockReason', 'Account temporarily restricted by system administration.')
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    subject = "Important: Your FlyoraGo account has been restricted"
    
    body = f"""
    <div style="font-size: 16px; color: #0f172a; line-height: 1.6; margin-bottom: 16px;">
        Hi <strong style="color: #0d9488;">{email_or_name}</strong>,
    </div>
    <div style="font-size: 15px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
        Your FlyoraGo account has been temporarily restricted by an administrator as a security measure.
    </div>

    {component_alert_box('Security Notice: Restriction Details', f'<strong>Reason:</strong> {reason}', 'danger')}

    {component_status_card('ACCOUNT STATUS DETAILS', [
        ('Current Status', '<span style="background: #ffe4e6; color: #e11d48; padding: 4px 10px; border-radius: 6px; font-weight: 800;">RESTRICTED</span>'),
        ('Account Impact', '<span style="color: #0f172a; font-weight: 700;">Login & active marketplace features are paused</span>')
    ])}

    <div style="font-size: 14px; color: #64748b; line-height: 1.6; margin: 20px 0 10px 0;">
        If you believe this action was taken in error, you can submit a review request directly to our security & compliance department.
    </div>

    {component_primary_button('Contact Security Support', 'mailto:support@flyorago.tech')}
    """

    html = get_master_layout(
        title=subject,
        badge_text="RESTRICTED",
        badge_type="danger",
        body_html=body,
        ref_id="FG-SEC-RESTRICT-2026",
        hero_title="Account Status Notice"
    )
    text = f"Hi {email_or_name},\nYour FlyoraGo account has been restricted.\nReason: {reason}\nContact support@flyorago.tech"
    return subject, html, text

def build_account_reactivated_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    subject = "Your FlyoraGo account has been reactivated"

    body = f"""
    <div style="font-size: 16px; color: #0f172a; line-height: 1.6; margin-bottom: 16px;">
        Hi <strong style="color: #0d9488;">{email_or_name}</strong>,
    </div>
    <div style="font-size: 15px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
        Great news! Your FlyoraGo account has been successfully reactivated and restored to full active standing.
    </div>

    {component_alert_box('Account Verified & Restored', 'All restriction parameters have been cleared. You now have full access.', 'success')}

    {component_status_card('ACCOUNT STATUS DETAILS', [
        ('Current Status', '<span style="background: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 6px; font-weight: 800;">ACTIVE</span>'),
        ('Access Level', '<span style="color: #0f172a; font-weight: 700;">Full Unrestricted Access</span>')
    ])}

    {component_primary_button('Open FlyoraGo Marketplace', f'{site_url}/login')}
    """

    html = get_master_layout(
        title=subject,
        badge_text="ACTIVE",
        badge_type="success",
        body_html=body,
        ref_id="FG-SEC-ACTIVE-2026",
        hero_title="Account Reactivated"
    )
    text = f"Hi {email_or_name},\nYour FlyoraGo account has been reactivated.\nLogin: {site_url}/login"
    return subject, html, text

def build_welcome_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    site_url = getattr(settings, 'SITE_URL', 'https://flyorago.me')

    subject = "Welcome to FlyoraGo"

    body = f"""
    <div style="font-size: 16px; color: #0f172a; line-height: 1.6; margin-bottom: 16px;">
        Welcome <strong style="color: #0d9488;">{email_or_name}</strong>,
    </div>
    <div style="font-size: 15px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
        Thank you for creating an account with FlyoraGo — the world's most trusted peer-to-peer transport & luggage network.
    </div>

    {component_status_card('AVAILABLE CAPABILITIES', [
        ('For Air Travelers', '<span style="color: #0f172a; font-weight: 700;">Earn rewards sharing spare flight luggage capacity</span>'),
        ('For Parcel Senders', '<span style="color: #0f172a; font-weight: 700;">Ship parcels worldwide with verified travelers</span>')
    ])}

    {component_primary_button('Explore FlyoraGo Platform', site_url)}
    """

    html = get_master_layout(
        title=subject,
        badge_text="WELCOME",
        badge_type="info",
        body_html=body,
        ref_id="FG-USER-JOIN-2026",
        hero_title="Welcome to FlyoraGo"
    )
    text = f"Welcome {email_or_name}!\nYour FlyoraGo account is active."
    return subject, html, text

def build_verification_otp_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    otp = ctx.get('otp', '000000')

    subject = "Verify your FlyoraGo email address"

    body = f"""
    <div style="font-size: 16px; color: #0f172a; line-height: 1.6; margin-bottom: 16px;">
        Hi <strong style="color: #0d9488;">{email_or_name}</strong>,
    </div>
    <div style="font-size: 15px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
        Please enter the security verification code below to authorize your session:
    </div>

    <div style="background: linear-gradient(135deg, #f0fdfa 0%, #e0f2fe 100%); border: 2px dashed #0d9488; border-radius: 16px; padding: 28px; text-align: center; margin: 24px 0;">
        <div style="font-size: 12px; font-weight: 800; color: #0d9488; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px;">SECURITY OTP CODE</div>
        <div style="font-size: 38px; font-weight: 900; color: #0f172a; letter-spacing: 8px;">{otp}</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 10px;">Expires in 10 minutes. Do not share this code.</div>
    </div>

    {component_alert_box('Security Reminder', 'If you did not request this verification code, please ignore this message.', 'info')}
    """

    html = get_master_layout(
        title=subject,
        badge_text="SECURITY",
        badge_type="warning",
        body_html=body,
        ref_id="FG-AUTH-VERIFY-2026",
        hero_title="Email Verification"
    )
    text = f"Hi {email_or_name},\nYour verification code is: {otp}"
    return subject, html, text

def build_password_reset_otp_email(context: dict) -> tuple:
    ctx = sanitize_context(context)
    email_or_name = ctx.get('firstName') or ctx.get('email') or 'user'
    otp = ctx.get('otp', '000000')

    subject = "Reset your FlyoraGo password"

    body = f"""
    <div style="font-size: 16px; color: #0f172a; line-height: 1.6; margin-bottom: 16px;">
        Hi <strong style="color: #0d9488;">{email_or_name}</strong>,
    </div>
    <div style="font-size: 15px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
        A password reset authorization was requested for your FlyoraGo account. Use the code below:
    </div>

    <div style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 2px dashed #f59e0b; border-radius: 16px; padding: 28px; text-align: center; margin: 24px 0;">
        <div style="font-size: 12px; font-weight: 800; color: #b45309; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px;">AUTHORIZATION CODE</div>
        <div style="font-size: 38px; font-weight: 900; color: #0f172a; letter-spacing: 8px;">{otp}</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 10px;">Expires in 10 minutes.</div>
    </div>

    {component_alert_box('Account Protection', 'If you did not initiate this password reset, please change your password immediately.', 'danger')}
    """

    html = get_master_layout(
        title=subject,
        badge_text="PASSWORD RESET",
        badge_type="warning",
        body_html=body,
        ref_id="FG-AUTH-RESET-2026",
        hero_title="Password Reset Request"
    )
    text = f"Hi {email_or_name},\nYour password reset code is: {otp}"
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
        <div style="font-size: 16px; color: #0f172a;">Hi <strong style="color: #0d9488;">{email_or_name}</strong>,</div>
        <div style="font-size: 15px; color: #475569; margin-top: 8px;">Your identity verification submission has passed verification successfully.</div>
        {component_alert_box('Identity Verified', 'You now hold a Verified Traveler badge on FlyoraGo.', 'success')}
        {component_status_card('KYC STATUS DETAILS', [('Verification Status', '<span style="background: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 6px; font-weight: 800;">APPROVED</span>')])}
        {component_primary_button('View Profile & Badges', f'{site_url}/profile')}
        """
        b_type = 'success'
    elif status == 'REJECTED':
        subject = "FlyoraGo KYC Verification Update"
        body = f"""
        <div style="font-size: 16px; color: #0f172a;">Hi <strong style="color: #0d9488;">{email_or_name}</strong>,</div>
        <div style="font-size: 15px; color: #475569; margin-top: 8px;">Our compliance team requires additional information to approve your KYC.</div>
        {component_alert_box('Review Findings', f'<strong>Reason:</strong> {reason or "Document unreadable or invalid."}', 'danger')}
        {component_status_card('KYC STATUS DETAILS', [('Verification Status', '<span style="background: #ffe4e6; color: #e11d48; padding: 4px 10px; border-radius: 6px; font-weight: 800;">REJECTED</span>')])}
        {component_primary_button('Resubmit Documents', f'{site_url}/kyc')}
        """
        b_type = 'danger'
    else:
        subject = "Your FlyoraGo KYC Documents Received"
        body = f"""
        <div style="font-size: 16px; color: #0f172a;">Hi <strong style="color: #0d9488;">{email_or_name}</strong>,</div>
        <div style="font-size: 15px; color: #475569; margin-top: 8px;">We have safely received your verification documents and are processing them.</div>
        {component_status_card('KYC STATUS DETAILS', [('Verification Status', '<span style="background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 6px; font-weight: 800;">UNDER REVIEW</span>')])}
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
    text = f"Hi {email_or_name},\nYour KYC status is: {status}"
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

    card_html = component_status_card('EVENT DETAILS', status_rows) if status_rows else ''
    btn_html = component_primary_button(cta_text or 'Open FlyoraGo', cta_url or 'https://flyorago.me') if (cta_text and cta_url) else ''

    body = f"""
    <div style="font-size: 16px; color: #0f172a; line-height: 1.6; margin-bottom: 16px;">
        Hi <strong style="color: #0d9488;">{n_s}</strong>,
    </div>
    <div style="font-size: 15px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
        {m_s}
    </div>
    {card_html}
    {btn_html}
    """
    html = get_master_layout(
        title=t_s,
        badge_text=badge,
        badge_type=badge_type,
        body_html=body,
        ref_id="FG-EVENT-NOTICE-2026",
        hero_title=t_s
    )
    text = f"Hi {n_s},\n{m_s}"
    return t_s, html, text
