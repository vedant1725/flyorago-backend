from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from notifications.models import EmailLog
from notifications.email_service import EmailService
from notifications.email_service.client import ResendEmailClient
from notifications.email_service.sanitizer import sanitize_value, sanitize_context

from unittest.mock import patch

User = get_user_model()

class EmailSystemTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@flyorago.tech",
            password="Password123!",
            first_name="John",
            last_name="Doe"
        )

    def test_sanitizer_escapes_html(self):
        malicious = "<script>alert('xss')</script>"
        sanitized = sanitize_value(malicious)
        self.assertNotIn("<script>", sanitized)
        self.assertIn("&lt;script&gt;", sanitized)

    def test_sanitizer_context_dict(self):
        ctx = {"firstName": "<b>John</b>", "blockReason": "Violated terms <bad>"}
        clean_ctx = sanitize_context(ctx)
        self.assertEqual(clean_ctx["firstName"], "&lt;b&gt;John&lt;/b&gt;")
        self.assertNotIn("<bad>", clean_ctx["blockReason"])

    def test_email_service_idempotency(self):
        key = "test-idempotency-key-123"
        # First send
        res1 = EmailService._dispatch_email(
            recipient="testuser@flyorago.tech",
            subject="Test Subject",
            html_content="<p>Test</p>",
            text_content="Test",
            event_name="TEST_EVENT",
            template_name="test_template",
            idempotency_key=key
        )
        self.assertTrue(res1)
        log1 = EmailLog.objects.get(idempotency_key=key)
        self.assertEqual(log1.status, 'SENT')

        # Second send with same idempotency key
        res2 = EmailService._dispatch_email(
            recipient="testuser@flyorago.tech",
            subject="Test Subject Duplicate",
            html_content="<p>Test</p>",
            text_content="Test",
            event_name="TEST_EVENT",
            template_name="test_template",
            idempotency_key=key
        )
        self.assertTrue(res2)
        count = EmailLog.objects.filter(idempotency_key=key).count()
        self.assertEqual(count, 1)

    def test_failure_safety_isolated(self):
        with patch.object(ResendEmailClient, 'send_email', return_value=(False, None, "Simulated network timeout")):
            res = EmailService.send_account_restricted(self.user, reason="Test block reason")
            self.assertFalse(res)
            # Verify EmailLog recorded failure
            failed_log = EmailLog.objects.filter(recipient="testuser@flyorago.tech", status='FAILED').first()
            self.assertIsNotNone(failed_log)
            self.assertIn("Simulated network timeout", failed_log.error)
            # User DB status remains intact
            self.assertEqual(self.user.email, "testuser@flyorago.tech")

    def test_admin_block_and_activate_triggers(self):
        # Test Admin Block Email
        res_block = EmailService.send_account_restricted(self.user, reason="Safety policy violation")
        self.assertTrue(res_block)
        block_log = EmailLog.objects.filter(event='ACCOUNT_RESTRICTED').first()
        self.assertIsNotNone(block_log)
        self.assertEqual(block_log.status, 'SENT')
        self.assertIsNotNone(block_log.message_id)

        # Test Admin Activate Email
        res_activate = EmailService.send_account_reactivated(self.user)
        self.assertTrue(res_activate)
        activate_log = EmailLog.objects.filter(event='ACCOUNT_REACTIVATED').first()
        self.assertIsNotNone(activate_log)
        self.assertEqual(activate_log.status, 'SENT')
        self.assertIsNotNone(activate_log.message_id)

    def test_real_resend_email_dispatch(self):
        """
        Tests actual delivery to Resend HTTP API using configured RESEND_API_KEY.
        """
        api_key = getattr(settings, 'RESEND_API_KEY', '')
        self.assertTrue(bool(api_key), "RESEND_API_KEY must be set in environment settings")

        success, msg_id, err = ResendEmailClient.send_email(
            recipient="support@flyorago.tech",
            subject="FlyoraGo Automated Test Delivery",
            html_content="<h1>FlyoraGo Email System Operational</h1><p>Test delivery verified via Resend API.</p>"
        )
        self.assertTrue(success, f"Resend API call failed: {err}")
        self.assertIsNotNone(msg_id, "Resend API must return a valid Message ID")
        self.assertTrue(msg_id.startswith("msg_") or len(msg_id) > 5)
