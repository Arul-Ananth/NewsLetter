import logging
from typing import Optional

import keyring

SERVICE_NAME = "AeroBrief"

logger = logging.getLogger(__name__)


def get_secret(key: str) -> Optional[str]:
    """Retrieve a secret from the OS keyring."""
    try:
        return keyring.get_password(SERVICE_NAME, key)
    except Exception as exc:
        logger.exception("Error accessing keyring for %s: %s", key, exc)
        return None


def set_secret(key: str, value: str) -> bool:
    """Save a secret to the OS keyring."""
    try:
        keyring.set_password(SERVICE_NAME, key, value)
        return True
    except Exception as exc:
        logger.exception("Error setting keyring for %s: %s", key, exc)
        return False


def delete_secret(key: str) -> bool:
    """Delete a secret from the OS keyring."""
    try:
        keyring.delete_password(SERVICE_NAME, key)
        return True
    except Exception as exc:
        logger.exception("Error deleting keyring for %s: %s", key, exc)
        return False
