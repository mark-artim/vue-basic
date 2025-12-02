"""
Log Service - Django equivalent of Node.js logService.js

Logs authentication events to MongoDB logs collection
for centralized audit trail across all backends.
"""

import logging
from datetime import datetime
from services.mongodb_service import mongodb_service

logger = logging.getLogger(__name__)


def log_event(user_id, user_email, company_id, company_code, event_type, source='django-backend', message='', meta=None):
    """
    Log an event to MongoDB logs collection

    Args:
        user_id: User MongoDB ID (string)
        user_email: User email address
        company_id: Company MongoDB ID (string)
        company_code: Company code (e.g., 'heritage', 'crescentpl')
        event_type: Event type (e.g., 'login', 'login-failure', 'logout')
        source: Source system (default: 'django-backend')
        message: Human-readable message
        meta: Additional metadata dictionary

    Mirrors Node.js logEvent function from auth-backend/services/logService.js
    """
    if meta is None:
        meta = {}

    try:
        db = mongodb_service.db
        logs_collection = db['logs']

        log_entry = {
            'timestamp': datetime.utcnow(),
            'userId': user_id,
            'userEmail': user_email,
            'companyId': company_id,
            'companyCode': company_code,
            'type': event_type,
            'source': source,
            'message': message,
            'meta': meta
        }

        logs_collection.insert_one(log_entry)
        logger.debug(f"[Log Service] Logged {event_type} event for {user_email}")

    except Exception as e:
        # Don't fail the request if logging fails - just log the error
        logger.error(f"[Log Service] Failed to log event: {e}", exc_info=True)
