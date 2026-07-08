import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)


class CryptoNotConfiguredError(Exception):
    """Raised when ENCRYPTION_KEY isn't set — callers that would persist a real secret
    (OAuth tokens, API keys) must fail closed with this rather than ever storing plaintext."""


_fernet: Optional[Fernet] = None
_fernet_checked = False


def _get_fernet() -> Fernet:
    global _fernet, _fernet_checked
    if not _fernet_checked:
        _fernet_checked = True
        if settings.ENCRYPTION_KEY:
            try:
                _fernet = Fernet(settings.ENCRYPTION_KEY.encode("utf-8"))
            except Exception as e:
                logger.error(f"ENCRYPTION_KEY is set but invalid (must be a Fernet.generate_key() value): {e}")
                _fernet = None
    if _fernet is None:
        raise CryptoNotConfiguredError(
            "ENCRYPTION_KEY is not set or invalid. Generate one with "
            "`python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"` "
            "and set it in the environment before storing integration credentials."
        )
    return _fernet


def encrypt_value(plaintext: str) -> str:
    """Encrypts a secret (OAuth token, API key) for storage at rest. Raises
    CryptoNotConfiguredError if ENCRYPTION_KEY isn't set — never falls back to storing
    plaintext."""
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """Decrypts a value previously produced by encrypt_value(). Raises CryptoNotConfiguredError
    if ENCRYPTION_KEY isn't set, or ValueError if the ciphertext is invalid/was encrypted with a
    different key (e.g. ENCRYPTION_KEY was rotated without re-encrypting existing rows)."""
    fernet = _get_fernet()
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise ValueError("Could not decrypt value — it may have been encrypted with a different ENCRYPTION_KEY.")
