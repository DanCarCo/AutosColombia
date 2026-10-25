"""RF-12: clientes y su asociación con varios vehículos. Sin depender de PostgreSQL."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.database import get_session
from app.main import app
from app.models import Cliente
from app.schemas.cliente import ClienteActualizar, ClienteCrear
from app.services.cliente import delete_client

VALIDO = {"nombre": "Juan Pérez", "documento": "123456", "telefono": "3000000000"}


@pytest.mark.parametrize("field", ["nombre", "documento", "telefono"])
@pytest.mark.parametrize("value", [None, "", " \t\n"])
def test_rejects_blank_text(field, value):
    with pytest.raises(ValidationError):
        ClienteCrear(**{**VALIDO, field: value})
    with pytest.raises(ValidationError):
        ClienteActualizar(**{field: value})


def test_creation_requires_every_field():
    with pytest.raises(ValidationError):
        ClienteCrear(nombre="Juan")


def test_patch_only_supplied_fields_and_no_id():
    assert ClienteActualizar(nombre=" Juan ").model_dump(exclude_unset=True) == {"nombre": "Juan"}
    assert ClienteActualizar().model_dump(exclude_unset=True) == {}
    with pytest.raises(ValidationError):
        ClienteActualizar(id=1)


def test_duplicate_documento_rolls_back_without_exposing_driver_details():
    session = MagicMock()
    driver_error = Exception("private database details")
    driver_error.sqlstate = "23505"
    driver_error.diag = SimpleNamespace(constraint_name="uq_cliente_documento")
    session.commit.side_effect = IntegrityError("INSERT", {}, driver_error)
    from app.services.cliente import ClienteError, create_client

    with pytest.raises(ClienteError) as result:
        create_client(session, ClienteCrear(**VALIDO))
    assert result.value.status_code == 409
    assert "private" not in result.value.detail
    session.rollback.assert_called_once()


def test_delete_with_vehicles_rolls_back_without_deleting_them():
    session = MagicMock()
    cliente = session.get.return_value
    driver_error = Exception("private database details")
    driver_error.sqlstate = "23503"
    session.commit.side_effect = IntegrityError("DELETE", {}, driver_error)
    from app.services.cliente import ClienteError

    with pytest.raises(ClienteError) as result:
        delete_client(session, 1)
    assert result.value.status_code == 409
    assert "private" not in result.value.detail
    session.rollback.assert_called_once()
    session.delete.assert_called_once_with(cliente)


@pytest.fixture
def api():
    session = MagicMock()
    session.get.return_value = Cliente(id=1, **VALIDO)

    def override():
        yield session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_patch_forbids_id_and_unknown_fields(api):
    client, session = api
    for payload in ({"id": 2}, {"vehiculos": []}):
        assert client.patch("/clientes/1", json=payload).status_code == 422
    session.commit.assert_not_called()


def test_get_returns_client_without_vehicle_list(api):
    client, _session = api
    body = client.get("/clientes/1").json()
    assert set(body) == {"id", "nombre", "documento", "telefono"}
