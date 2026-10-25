"""Configuración privada desde backend/.env y variables de entorno."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class ConfigurationError(ValueError):
    """Error que contiene únicamente nombres de variables, nunca sus valores."""


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str = field(repr=False)
    user: str = field(repr=False)
    password: str = field(repr=False)
    connect_timeout: int = 5


@dataclass(frozen=True)
class AuthSettings:
    secret_key: str = field(repr=False)
    expiration_minutes: int = 480


def _load_env_values() -> dict[str, str]:
    # No interpolar $ ni ${...} dentro de contraseñas o claves.
    return {**dotenv_values(ENV_FILE, encoding="utf-8-sig", interpolate=False), **os.environ}


def _require(values: dict[str, str], required: tuple[str, ...]) -> None:
    missing = [
        key for key in required
        if not (values.get(key) or "").strip()
        or (values.get(key) or "").startswith("CAMBIAR_")
    ]
    if missing:
        raise ConfigurationError("Completa en backend/.env: " + ", ".join(missing))


def _positive_integer(values: dict[str, str], key: str, maximum: int) -> int:
    try:
        number = int(values[key])
    except (ValueError, TypeError):
        raise ConfigurationError(f"{key} debe ser un entero válido.") from None
    if not 1 <= number <= maximum:
        raise ConfigurationError(f"{key} debe estar entre 1 y {maximum}.")
    return number


def load_database_settings() -> DatabaseSettings:
    values = _load_env_values()
    _require(values, ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_CONNECT_TIMEOUT"))
    return DatabaseSettings(
        host=values["DB_HOST"],
        port=_positive_integer(values, "DB_PORT", 65535),
        name=values["DB_NAME"],
        user=values["DB_USER"],
        password=values["DB_PASSWORD"],
        connect_timeout=_positive_integer(values, "DB_CONNECT_TIMEOUT", 60),
    )


def load_auth_settings() -> AuthSettings:
    """Clave de firma de tokens (RF-16). No depende de PostgreSQL."""
    values = _load_env_values()
    _require(values, ("JWT_SECRET",))
    expiration = values.get("JWT_EXPIRATION_MINUTES", "480") or "480"
    try:
        minutes = int(expiration)
    except ValueError:
        raise ConfigurationError("JWT_EXPIRATION_MINUTES debe ser un entero válido.") from None
    if not 1 <= minutes <= 10_080:
        raise ConfigurationError("JWT_EXPIRATION_MINUTES debe estar entre 1 y 10080 (una semana).")
    return AuthSettings(secret_key=values["JWT_SECRET"], expiration_minutes=minutes)
