import logging
import json
import time
import urllib.request
import urllib.error
from django.conf import settings

logger = logging.getLogger(__name__)

class ResendEmailClient:
    """
    Production Resend HTTP API Client for FlyoraGo.
    Uses Resend HTTP endpoint directly with Bearer authentication and exponential backoff retry.
    """
    API_URL = "https://api.resend.com/emails"

    @classmethod
    def send_email(cls, recipient: str, subject: str, html_content: str, text_content: str = None, reply_to: str = None):
        api_key = getattr(settings, 'RESEND_API_KEY', '')
        from_email = getattr(settings, 'EMAIL_FROM', 'FlyoraGo <no-reply@flyorago.tech>')
        reply_email = reply_to or getattr(settings, 'EMAIL_REPLY_TO', 'support@flyorago.tech')
        test_mode = getattr(settings, 'EMAIL_TEST_MODE', False)

        if not api_key:
            logger.warning("RESEND_API_KEY is not configured in settings. Email send skipped.")
            return False, None, "RESEND_API_KEY missing"

        if test_mode:
            logger.info(f"[TEST_MODE] Email to {recipient} with subject '{subject}' simulated.")
            return True, "test_msg_id_simulated", None

        payload = {
            "from": from_email,
            "to": [recipient],
            "subject": subject,
            "html": html_content,
            "reply_to": reply_email
        }
        if text_content:
            payload["text"] = text_content

        payload_bytes = json.dumps(payload).encode('utf-8')
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "FlyoraGo-EmailEngine/1.0"
        }

        max_attempts = 3
        backoff_seconds = 1.0

        for attempt in range(1, max_attempts + 1):
            try:
                req = urllib.request.Request(cls.API_URL, data=payload_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=15) as response:
                    response_body = response.read().decode('utf-8')
                    if response.status in (200, 201):
                        resp_json = json.loads(response_body)
                        msg_id = resp_json.get("id")
                        logger.info(f"Resend email delivered to {recipient}, Message ID: {msg_id}")
                        return True, msg_id, None
                    else:
                        error_msg = f"HTTP {response.status}: {response_body}"
            except urllib.error.HTTPError as http_err:
                try:
                    err_body = http_err.read().decode('utf-8')
                except Exception:
                    err_body = str(http_err)
                error_msg = f"HTTPError {http_err.code}: {err_body}"
                # If 4xx client error (e.g. invalid recipient or bad request), do not retry
                if 400 <= http_err.code < 500:
                    logger.error(f"Resend permanent error ({http_err.code}): {err_body}")
                    return False, None, error_msg
            except Exception as exc:
                error_msg = f"Network exception: {str(exc)}"

            logger.warning(f"Resend send attempt {attempt}/{max_attempts} failed: {error_msg}")
            if attempt < max_attempts:
                time.sleep(backoff_seconds)
                backoff_seconds *= 2.0

        return False, None, f"Failed after {max_attempts} attempts. Last error: {error_msg}"
