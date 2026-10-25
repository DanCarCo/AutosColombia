"""ServicioEstancia: reglas nuevas (RF-11, RF-14) con una sesión simulada."""
from unittest.mock import MagicMock

import pytest

from app.models import Celda, Operador, Vehiculo
from app.schemas.estancia import CambiarCeldaCrear, EntradaCrear
from app.services.estancia import EstanciaError, ServicioEstancia


def test_entrada_rechaza_sin_mensualidad_vigente():
    """RF-14: ningún vehículo entra sin mensualidad vigente, sin excepción."""
    session = MagicMock()
    vehiculo = Vehiculo(id=1, placa="ABC123", tipo="MOTO", cliente_id=1)
    # 1) _vehiculo() lo encuentra; 2) vigente_para_vehiculo no encuentra pago vigente.
    session.scalar.side_effect = [vehiculo, None]
    session.get.return_value = Celda(id=2, codigo="A-01")
    servicio = ServicioEstancia(session)

    with pytest.raises(EstanciaError) as result:
        servicio.entrada(EntradaCrear(placa="ABC123", celda_id=2), Operador(id=9))

    assert result.value.status_code == 402
    assert "mensualidad" in result.value.detail
    session.add.assert_not_called()


def test_cambiar_celda_rechaza_sin_estancia_abierta():
    """RF-11: solo se puede mover la celda de un vehículo que está dentro."""
    session = MagicMock()
    vehiculo = Vehiculo(id=1, placa="ABC123")
    session.scalar.side_effect = [vehiculo, None]  # _vehiculo(), estancia abierta -> ninguna
    servicio = ServicioEstancia(session)

    with pytest.raises(EstanciaError) as result:
        servicio.cambiar_celda(CambiarCeldaCrear(placa="ABC123", celda_id=2))

    assert result.value.status_code == 409
    assert "estancia abierta" in result.value.detail


def test_cambiar_celda_rechaza_celda_inexistente():
    session = MagicMock()
    vehiculo = Vehiculo(id=1, placa="ABC123")
    estancia_abierta = MagicMock(celda_id=5)
    session.scalar.side_effect = [vehiculo, estancia_abierta]
    session.get.return_value = None  # la celda destino no existe
    servicio = ServicioEstancia(session)

    with pytest.raises(EstanciaError) as result:
        servicio.cambiar_celda(CambiarCeldaCrear(placa="ABC123", celda_id=99))

    assert result.value.status_code == 404
