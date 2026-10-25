from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.schemas.vehiculo import VehiculoActualizar, VehiculoCrear
from app.services.vehiculo import VehiculoError, delete_vehicle


@pytest.mark.parametrize("field", ["placa", "color", "modelo", "marca", "tipo"])
def test_patch_rejects_explicit_null(field):
    with pytest.raises(ValidationError):
        VehiculoActualizar(**{field: None})


@pytest.mark.parametrize("field", ["placa", "color", "marca", "tipo"])
def test_patch_rejects_blank_text(field):
    with pytest.raises(ValidationError):
        VehiculoActualizar(**{field: " \t\n"})


def test_patch_only_supplied_fields_and_no_id():
    assert VehiculoActualizar(placa=" abc123 ").model_dump(exclude_unset=True) == {"placa": "ABC123"}
    assert VehiculoActualizar().model_dump(exclude_unset=True) == {}
    with pytest.raises(ValidationError):
        VehiculoActualizar(id=1)


@pytest.mark.parametrize("value", [1900, 2025, 2200])
def test_year_accepts_1900_to_2200(value):
    assert VehiculoActualizar(modelo=value).modelo == value


@pytest.mark.parametrize("value", [0, 1, 1899, 2201, 9999, True, "2025", 2025.5])
def test_year_rejects_values_outside_1900_to_2200(value):
    with pytest.raises(ValidationError):
        VehiculoActualizar(modelo=value)


def test_creation_requires_every_field():
    with pytest.raises(ValidationError):
        VehiculoCrear(placa="ABC123")


def test_creation_requires_cliente_id():
    """RF-12/RF-14: todo vehículo pertenece a un cliente, sin excepción."""
    base = dict(placa="ABC123", color="Azul", modelo=2025, marca="Marca", tipo="MOTO")
    with pytest.raises(ValidationError):
        VehiculoCrear(**base)
    assert VehiculoCrear(**base, cliente_id=1).cliente_id == 1


@pytest.mark.parametrize("value", [0, -1, True, "1", 1.5, None])
def test_cliente_id_rejects_invalid_values(value):
    with pytest.raises(ValidationError):
        VehiculoActualizar(cliente_id=value)


def test_patch_allows_reassigning_cliente():
    """RF-13: cambio de vehículo de un cliente, vía PATCH."""
    assert VehiculoActualizar(cliente_id=7).model_dump(exclude_unset=True) == {"cliente_id": 7}


def test_create_with_unknown_cliente_is_404_not_409():
    """fk_vehiculo_cliente es la misma sqlstate 23503 que un borrado bloqueado, pero significa otra cosa."""
    from app.services.vehiculo import create_vehicle

    session = MagicMock()
    driver_error = Exception("private database details")
    driver_error.sqlstate = "23503"
    driver_error.diag = SimpleNamespace(constraint_name="fk_vehiculo_cliente")
    session.commit.side_effect = IntegrityError("INSERT", {}, driver_error)
    data = VehiculoCrear(placa="ABC123", color="Azul", modelo=2025, marca="Marca", tipo="MOTO", cliente_id=999)
    with pytest.raises(VehiculoError) as result:
        create_vehicle(session, data)
    assert result.value.status_code == 404
    assert "private" not in result.value.detail
    session.rollback.assert_called_once()


def test_delete_foreign_key_conflict_rolls_back_without_related_deletes():
    session = MagicMock()
    vehicle = session.get.return_value
    driver_error = Exception("private database details")
    driver_error.sqlstate = "23503"
    driver_error.diag = SimpleNamespace(constraint_name="some_foreign_key")
    session.commit.side_effect = IntegrityError("DELETE", {}, driver_error)
    with pytest.raises(VehiculoError) as result:
        delete_vehicle(session, 1)
    assert result.value.status_code == 409
    assert "private" not in result.value.detail
    session.rollback.assert_called_once()
    session.delete.assert_called_once_with(vehicle)
