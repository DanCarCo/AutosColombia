"""Autenticación de operadores (RF-16): login con usuario/contraseña y token JWT.

No se valida contra PostgreSQL al importar este módulo; la conexión solo
ocurre al resolver las dependencias de FastAPI en una solicitud real.
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import AuthSettings, ConfigurationError, load_auth_settings
from app.database import get_session
from app.models import Operador
from app.schemas.auth import LoginCrear
from app.security import verify_password

ALGORITMO = "HS256"
_bearer_scheme = HTTPBearer(auto_error=False)


class AuthError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail


def crear_token(operador: Operador, settings: AuthSettings) -> tuple[str, int]:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(operador.id),
        "usuario": operador.usuario,
        "turno": operador.turno,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.expiration_minutes),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITMO)
    return token, settings.expiration_minutes


def login(session: Session, data: LoginCrear, settings: AuthSettings | None = None) -> tuple[Operador, str, int]:
    try:
        settings = settings or load_auth_settings()
    except ConfigurationError:
        raise AuthError(503, "La autenticación no está configurada en el servidor.") from None
    try:
        operador = session.scalar(select(Operador).where(Operador.usuario == data.usuario))
    except SQLAlchemyError:
        raise AuthError(503, "No se pudo completar la operación con la base de datos.") from None
    if operador is None or not verify_password(data.password, operador.password_hash):
        # Mismo mensaje exista o no el usuario: no revela qué parte falló.
        raise AuthError(401, "Usuario o contraseña incorrectos.")
    token, minutos = crear_token(operador, settings)
    return operador, token, minutos


def operador_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: Session = Depends(get_session),
) -> Operador:
    """Dependencia de FastAPI: exige 'Authorization: Bearer <token>' y resuelve el operador."""
    if credenciales is None:
        raise AuthError(401, "Se requiere iniciar sesión.")
    try:
        settings = load_auth_settings()
    except ConfigurationError:
        raise AuthError(503, "La autenticación no está configurada en el servidor.") from None
    try:
        payload = jwt.decode(credenciales.credentials, settings.secret_key, algorithms=[ALGORITMO])
    except jwt.ExpiredSignatureError:
        raise AuthError(401, "La sesión expiró; inicia sesión de nuevo.") from None
    except jwt.InvalidTokenError:
        raise AuthError(401, "Token inválido.") from None
    try:
        operador_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise AuthError(401, "Token inválido.") from None
    try:
        operador = session.get(Operador, operador_id)
    except SQLAlchemyError:
        raise AuthError(503, "No se pudo completar la operación con la base de datos.") from None
    if operador is None:
        raise AuthError(401, "El operador del token ya no existe.")
    return operador
