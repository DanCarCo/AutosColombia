"""RF-16: inicio de sesión de operadores. Sin depender de PostgreSQL."""
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.auth import AuthError, crear_token, login, operador_actual
from app.config import AuthSettings
from app.database import get_session
from app.main import app
from app.models import Operador
from app.schemas.auth import LoginCrear
from app.security import hash_password, verify_password


def test_hash_password_never_stores_plaintext_and_verifies_correctly():
    hashed = hash_password("clave-secreta")
    assert "clave-secreta" not in hashed
    assert verify_password("clave-secreta", hashed) is True
    assert verify_password("otra-clave", hashed) is False


def test_verify_password_rejects_malformed_hash_without_raising():
    assert verify_password("cualquier-cosa", "no-es-un-hash-valido") is False
    assert verify_password("cualquier-cosa", "") is False


SETTINGS = AuthSettings(secret_key="una-clave-de-prueba-no-real-de-al-menos-32-bytes", expiration_minutes=60)


def test_crear_token_incluye_operador_y_expira_en_el_tiempo_configurado():
    operador = Operador(id=5, usuario="jperez", turno="NOCHE")
    token, minutos = crear_token(operador, SETTINGS)
    assert minutos == 60
    payload = jwt.decode(token, SETTINGS.secret_key, algorithms=["HS256"])
    assert payload["sub"] == "5"
    assert payload["usuario"] == "jperez"
    assert payload["turno"] == "NOCHE"


def test_login_usuario_inexistente_y_password_incorrecta_dan_el_mismo_mensaje():
    session = MagicMock()
    operador = Operador(id=1, usuario="jperez", password_hash=hash_password("correcta"))

    session.scalar.return_value = None
    with pytest.raises(AuthError) as sin_usuario:
        login(session, LoginCrear(usuario="nadie", password="x"), settings=SETTINGS)

    session.scalar.return_value = operador
    with pytest.raises(AuthError) as password_mala:
        login(session, LoginCrear(usuario="jperez", password="incorrecta"), settings=SETTINGS)

    assert sin_usuario.value.status_code == password_mala.value.status_code == 401
    assert sin_usuario.value.detail == password_mala.value.detail


def test_login_correcto_emite_token_valido():
    session = MagicMock()
    operador = Operador(id=3, usuario="jperez", password_hash=hash_password("correcta"), turno="DIA")
    session.scalar.return_value = operador
    operador_resultado, token, minutos = login(session, LoginCrear(usuario="jperez", password="correcta"),
                                               settings=SETTINGS)
    assert operador_resultado is operador
    assert minutos == 60
    payload = jwt.decode(token, SETTINGS.secret_key, algorithms=["HS256"])
    assert payload["sub"] == "3"


def test_operador_actual_sin_credenciales_es_401():
    with pytest.raises(AuthError) as result:
        operador_actual(credenciales=None, session=MagicMock())
    assert result.value.status_code == 401


def test_operador_actual_token_invalido_es_401(monkeypatch):
    from app import auth as auth_module
    monkeypatch.setattr(auth_module, "load_auth_settings", lambda: SETTINGS)
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials="esto-no-es-un-jwt")
    with pytest.raises(AuthError) as result:
        operador_actual(credenciales=credenciales, session=MagicMock())
    assert result.value.status_code == 401


def test_operador_actual_token_de_operador_eliminado_es_401(monkeypatch):
    from app import auth as auth_module
    monkeypatch.setattr(auth_module, "load_auth_settings", lambda: SETTINGS)
    token, _ = crear_token(Operador(id=99, usuario="x", turno="DIA"), SETTINGS)
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    session = MagicMock()
    session.get.return_value = None
    with pytest.raises(AuthError) as result:
        operador_actual(credenciales=credenciales, session=session)
    assert result.value.status_code == 401


def test_login_rejects_blank_fields():
    with pytest.raises(ValidationError):
        LoginCrear(usuario="", password="x")
    with pytest.raises(ValidationError):
        LoginCrear(usuario="x", password="")


@pytest.fixture
def api():
    session = MagicMock()

    def override():
        yield session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_login_endpoint_credenciales_invalidas_no_revela_cual_parte_fallo(api):
    client, session = api
    session.scalar.return_value = None
    response = client.post("/auth/login", json={"usuario": "nadie", "password": "x"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Usuario o contraseña incorrectos."


def test_login_endpoint_exitoso_devuelve_token_y_operador_sin_password(api):
    client, session = api
    operador = Operador(id=1, nombre="Prueba", telefono="001", usuario="jperez",
                        password_hash=hash_password("correcta"), turno="DIA")
    session.scalar.return_value = operador
    response = client.post("/auth/login", json={"usuario": "jperez", "password": "correcta"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "password" not in body["operador"]
    assert "password_hash" not in body["operador"]
    assert body["operador"]["usuario"] == "jperez"
