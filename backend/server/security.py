import keyring
from typing import Optional

SERVICE_NAME = "AeroBrief"

def get_secret(key: str) -> Optional[str]:
    """Retrieve a secret from the OS keyring."""
    try:
        return keyring.get_password(SERVICE_NAME, key)
    except Exception as e:
        print(f"Error accessing keyring for {key}: {e}")
        return None

def set_secret(key: str, value: str) -> bool:
    """Save a secret to the OS keyring."""
    try:
        keyring.set_password(SERVICE_NAME, key, value)
        return True
    except Exception as e:
        print(f"Error setting keyring for {key}: {e}")
        return False

def delete_secret(key: str) -> bool:
    """Delete a secret from the OS keyring."""
    try:
        keyring.delete_password(SERVICE_NAME, key)
        return True
    except Exception as e:
        print(f"Error deleting keyring for {key}: {e}")
        return False
