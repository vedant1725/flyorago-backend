import os
import logging
from django.utils import timezone
from django.conf import settings

# Create a custom logger for security audits
logger = logging.getLogger('security_audit')
logger.setLevel(logging.INFO)

# Formatter for structured logs
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        import json
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
        }
        if hasattr(record, 'audit_data'):
            log_data.update(record.audit_data)
        return json.dumps(log_data)

# Set up file handler inside BASE_DIR
logs_dir = os.path.join(settings.BASE_DIR, 'logs')
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, 'security.log')

# Avoid duplicate handlers in reloading environments
if not logger.handlers:
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)

    # Output to console if in DEBUG mode
    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        logger.addHandler(console_handler)


class SecurityLogger:
    @staticmethod
    def _sanitize(data):
        if not isinstance(data, dict):
            return data
        sanitized = data.copy()
        sensitive_keys = [
            'password', 'otp', 'new_password', 'current_password', 
            'token', 'access', 'refresh', 'signing_key', 'api_key', 'secret'
        ]
        for key in sensitive_keys:
            for k in list(sanitized.keys()):
                if key in k.lower():
                    sanitized[k] = '[REDACTED]'
        return sanitized

    @classmethod
    def log_event(cls, action, user=None, status='SUCCESS', description='', ip_address=None, user_agent=None, target_object=None, additional_data=None):
        audit_data = {
            'action': action,
            'status': status,
            'description': description,
            'ip_address': ip_address or 'unknown',
            'user_agent': user_agent or 'unknown',
        }
        if user:
            if hasattr(user, 'is_authenticated') and user.is_authenticated:
                audit_data['user_id'] = str(user.id)
                audit_data['user_email'] = user.email
                audit_data['user_role'] = getattr(user, 'role', 'user')
            else:
                audit_data['user_id'] = 'anonymous'
        else:
            audit_data['user_id'] = 'system'
            
        if target_object:
            audit_data['target_object'] = str(target_object)
            
        if additional_data:
            audit_data['details'] = cls._sanitize(additional_data)
            
        logger.info(f"Security event: {action} - {status}", extra={'audit_data': audit_data})
