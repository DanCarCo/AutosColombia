"""Hash de contraseñas con la librería estándar (sin dependencias nuevas)."""

import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 390_000


def hash_password(password: str) -> str:
    """Devuelve 'pbkdf2_sha256$iteraciones$salt$hash', todo en hexadecimal."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS)
    return f"{_ALGORITHM}${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Compara en tiempo constante; nunca lanza por un hash con formato inválido."""
    try:
        algorithm, iterations_text, salt, expected_hex = hashed.split("$")
        if algorithm != _ALGORITHM:
            return False
        iterations = int(iterations_text)
    except (ValueError, AttributeError):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations)
    return hmac.compare_digest(digest.hex(), expected_hex)
