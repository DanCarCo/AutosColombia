"""RF-14: mensualidad vigente antes de la entrada y registro de pagos."""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.auth import operador_actual
from app.database import get_session
from app.main import app
from app.models import Operador, Pago, Vehiculo
from app.schemas.pago import PagoCrear
from app.services.pago import MONTO_POR_TIPO, PagoError, _fin_de_periodo, register_payment, vigente_para_vehiculo


@pytest.mark.parametrize("inicio, fin_esperado", [
    (date(2026, 1, 15), date(2026, 2, 14)),
    (date(2026, 1, 31), date(2026, 2, 28)),  # febrero no tiene 31: se ajusta al último día
    (date(2024, 1, 31), date(2024, 2, 29)),  # 2024 es bisiesto
    (date(2026, 12, 5), date(2027, 1, 4)),  # cruza de año
])
def test_fin_de_periodo_cubre_un_mes_calendario(inicio, fin_esperado):
    assert _fin_de_periodo(inicio) == fin_esperado


def test_vehiculo_no_encontrado_no_registra_pago():
    session = MagicMock()
    session.get.return_value = None
    operador = Operador(id=9)
    with pytest.raises(PagoError) as result:
        register_payment(session, PagoCrear(vehiculo_id=1), operador)
    assert result.value.status_code == 404
    session.add.assert_not_called()


@pytest.mark.parametrize("tipo, monto_esperado", [
    ("MOTO", MONTO_POR_TIPO["MOTO"]),
    ("AUTOMOVIL", MONTO_POR_TIPO["AUTOMOVIL"]),
    ("CAMIONETA", MONTO_POR_TIPO["CAMIONETA"]),
])
def test_monto_se_calcula_en_el_servidor_segun_el_tipo(tipo, monto_esperado):
    """El monto nunca lo decide quien llama: ni el esquema lo acepta ni el servicio lo usa."""
    session = MagicMock()
    session.get.return_value = Vehiculo(id=1, tipo=tipo, cliente_id=1)
    operador = Operador(id=9)
    register_payment(session, PagoCrear(vehiculo_id=1), operador)
    pago_creado = session.add.call_args.args[0]
    assert pago_creado.monto == monto_esperado
    assert pago_creado.operador_id == 9


def test_pago_crear_rechaza_monto_explicito():
    with pytest.raises(ValidationError):
        PagoCrear(vehiculo_id=1, monto=1)


def test_vigente_para_vehiculo_usa_la_fecha_dada_y_devuelve_lo_que_encuentra():
    """La condición de fecha en sí (periodo_inicio <= fecha <= periodo_fin) la prueba el
    filtro SQL; aquí solo se comprueba que la función consulta y propaga el resultado
    (una sesión simulada no evalúa el WHERE real). La prueba de integración con
    PostgreSQL es la que valida los límites del periodo contra datos reales."""
    pago = Pago(vehiculo_id=1, periodo_inicio=date(2026, 1, 1), periodo_fin=date(2026, 1, 31))
    session = MagicMock()
    session.scalar.return_value = pago
    assert vigente_para_vehiculo(session, 1, fecha=date(2026, 1, 1)) is pago
    session.scalar.assert_called_once()
    session.scalar.return_value = None
    assert vigente_para_vehiculo(session, 1, fecha=date(2026, 2, 1)) is None


@pytest.fixture
def api():
    session = MagicMock()

    def override_session():
        yield session

    def override_operador():
        return Operador(id=1, nombre="Prueba", telefono="001", usuario="prueba", turno="DIA")

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[operador_actual] = override_operador
    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(operador_actual, None)


@pytest.mark.parametrize("payload", [{}, {"vehiculo_id": 0}, {"vehiculo_id": True}, {"vehiculo_id": "1"},
                                     {"vehiculo_id": 1, "monto": 250000}])
def test_registrar_pago_invalido(api, payload):
    client, session = api
    assert client.post("/pagos", json=payload).status_code == 422
    session.commit.assert_not_called()


def test_registrar_pago_sin_sesion_iniciada_es_401():
    with TestClient(app) as client:
        assert client.post("/pagos", json={"vehiculo_id": 1}).status_code == 401


def test_estado_mensualidad_vehiculo_inexistente_es_404(api):
    client, session = api
    session.get.return_value = None
    assert client.get("/vehiculos/1/mensualidad").status_code == 404
