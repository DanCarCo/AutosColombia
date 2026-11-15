"""Autenticación de operadores (RF-16): login con usuario/contraseña y token JWT.

No se valida contra PostgreSQL al importar este módulo; la conexión solo
ocurre al resolver las dependencias de FastAPI en una solicitud real.
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import AuthSettings, ConfigurationError, load_auth_settings
from app.database import get_session
from app.models import Operador, TokenRevocado
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
        "rol": operador.rol,
        "jti": uuid.uuid4().hex,
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


def _decodificar(credenciales: HTTPAuthorizationCredentials | None) -> dict:
    """Valida firma y vigencia del token; devuelve su contenido."""
    if credenciales is None:
        raise AuthError(401, "Se requiere iniciar sesión.")
    try:
        settings = load_auth_settings()
    except ConfigurationError:
        raise AuthError(503, "La autenticación no está configurada en el servidor.") from None
    try:
        return jwt.decode(credenciales.credentials, settings.secret_key, algorithms=[ALGORITMO])
    except jwt.ExpiredSignatureError:
        raise AuthError(401, "La sesión expiró; inicia sesión de nuevo.") from None
    except jwt.InvalidTokenError:
        raise AuthError(401, "Token inválido.") from None


def operador_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: Session = Depends(get_session),
) -> Operador:
    """Dependencia de FastAPI: exige 'Authorization: Bearer <token>' y resuelve el operador."""
    payload = _decodificar(credenciales)
    try:
        operador_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise AuthError(401, "Token inválido.") from None
    try:
        jti = payload.get("jti")
        if jti and session.get(TokenRevocado, jti) is not None:
            raise AuthError(401, "La sesión fue cerrada; inicia sesión de nuevo.")
        operador = session.get(Operador, operador_id)
    except SQLAlchemyError:
        raise AuthError(503, "No se pudo completar la operación con la base de datos.") from None
    if operador is None:
        raise AuthError(401, "El operador del token ya no existe.")
    return operador


def requiere_roles(*roles: str):
    """Dependencia de FastAPI: exige sesión válida y que el rol del operador esté en `roles` (403 si no)."""
    def dependencia(operador: Operador = Depends(operador_actual)) -> Operador:
        if operador.rol not in roles:
            raise AuthError(403, "No tienes permisos para esta operación.")
        return operador
    return dependencia


solo_administrador = requiere_roles("ADMINISTRADOR")
solo_operador = requiere_roles("OPERADOR")


def cerrar_sesion(session: Session, credenciales: HTTPAuthorizationCredentials | None) -> None:
    """Revoca el token actual: su jti queda registrado y deja de autorizar solicitudes."""
    payload = _decodificar(credenciales)
    jti = payload.get("jti")
    if not jti:
        raise AuthError(400, "El token no es revocable; inicia sesión de nuevo.")
    try:
        ahora = datetime.now(timezone.utc)
        session.query(TokenRevocado).filter(TokenRevocado.expira < ahora).delete()
        if session.get(TokenRevocado, jti) is None:
            session.add(TokenRevocado(jti=jti, expira=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)))
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise AuthError(503, "No se pudo completar la operación con la base de datos.") from None
