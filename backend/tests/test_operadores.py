"""Errores HTTP y rollback sin depender de PostgreSQL."""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database import get_session
from app.main import app
from app.models import Operador

VALIDO = {"nombre": "Prueba", "telefono": "001", "usuario": "prueba", "password": "secreta123", "turno": "DIA"}


@pytest.fixture
def api():
    session = MagicMock()
    session.get.return_value = Operador(
        id=1, nombre="Prueba", telefono="001", usuario="prueba", password_hash="x", turno="DIA"
    )

    def override():
        yield session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.parametrize("field", ["nombre", "telefono", "usuario", "password"])
@pytest.mark.parametrize("value", [None, "", " \t\n", 123, True, []])
def test_invalid_text_fields_are_422_without_writes(api, field, value):
    client, session = api
    assert client.post("/operadores", json={**VALIDO, field: value}).status_code == 422
    assert client.patch("/operadores/1", json={field: value}).status_code == 422
    session.commit.assert_not_called()


@pytest.mark.parametrize("value", [None, "", "dia", "NOCHE ", "MADRUGADA", 1])
def test_invalid_turno_is_422_without_writes(api, value):
    client, session = api
    assert client.post("/operadores", json={**VALIDO, "turno": value}).status_code == 422
    assert client.patch("/operadores/1", json={"turno": value}).status_code == 422
    session.commit.assert_not_called()


@pytest.mark.parametrize("campo_faltante", ["nombre", "telefono", "usuario", "password", "turno"])
def test_creation_requires_every_field(api, campo_faltante):
    client, session = api
    payload = {k: v for k, v in VALIDO.items() if k != campo_faltante}
    assert client.post("/operadores", json=payload).status_code == 422
    session.commit.assert_not_called()


def test_creation_forbids_id_and_password_hash(api):
    client, session = api
    for extra in ({"id": 1}, {"password_hash": "y"}):
        assert client.post("/operadores", json={**VALIDO, **extra}).status_code == 422
    session.commit.assert_not_called()


def test_patch_forbids_id_and_unknown_fields(api):
    client, session = api
    for payload in ({"id": 2}, {"rol": "admin"}, {"password_hash": "y"}):
        assert client.patch("/operadores/1", json=payload).status_code == 422
    session.commit.assert_not_called()


def test_creation_never_sends_plaintext_password_to_the_model():
    """El servicio reemplaza password por password_hash antes de construir el modelo."""
    from app.schemas.operador import OperadorCrear
    from app.services.operador import create_operator

    session = MagicMock()
    create_operator(session, OperadorCrear(**VALIDO))
    operador_creado = session.add.call_args.args[0]
    assert operador_creado.password_hash != VALIDO["password"]
    assert operador_creado.password_hash.startswith("pbkdf2_sha256$")
    assert not hasattr(operador_creado, "password")


def test_response_never_includes_password_fields(api):
    client, _session = api
    body = client.get("/operadores/1").json()
    assert set(body) == {"id", "nombre", "telefono", "usuario", "turno"}


@pytest.mark.parametrize("sqlstate, status", [("23503", 409), ("23502", 422), ("23514", 422)])
def test_database_conflicts_roll_back_and_hide_details(api, sqlstate, status):
    client, session = api
    driver_error = Exception("PRIVATE DRIVER DETAILS")
    driver_error.sqlstate = sqlstate
    session.commit.side_effect = IntegrityError("DELETE", {}, driver_error)
    result = client.delete("/operadores/1")
    assert result.status_code == status
    assert "PRIVATE" not in result.text
    assert isinstance(result.json()["detail"], str)
    session.rollback.assert_called_once()
    session.delete.assert_called_once_with(session.get.return_value)


def test_duplicate_usuario_conflict_hides_driver_details(api):
    from types import SimpleNamespace

    client, session = api
    driver_error = Exception("PRIVATE DRIVER DETAILS")
    driver_error.sqlstate = "23505"
    driver_error.diag = SimpleNamespace(constraint_name="uq_operador_usuario")
    session.commit.side_effect = IntegrityError("INSERT", {}, driver_error)
    result = client.post("/operadores", json=VALIDO)
    assert result.status_code == 409
    assert "PRIVATE" not in result.text
    assert "usuario" in result.json()["detail"]
    session.rollback.assert_called_once()


def test_database_failure_rolls_back_and_is_generic(api):
    client, session = api
    session.get.side_effect = SQLAlchemyError("PRIVATE DRIVER DETAILS")
    result = client.get("/operadores/1")
    assert result.status_code == 503
    assert "PRIVATE" not in result.text
    session.rollback.assert_called_once()
