from fastapi.testclient import TestClient
import pytest

from app.auth import operador_actual
from app.main import app
from app.models import Operador


def _operador_falso() -> Operador:
    return Operador(id=1, nombre="Prueba", telefono="001", usuario="prueba", turno="DIA")


@pytest.fixture
def autenticado():
    """RF-16: simula una sesión ya iniciada, sin depender de un token real ni de PostgreSQL."""
    app.dependency_overrides[operador_actual] = _operador_falso
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(operador_actual, None)


def test_openapi_y_salud():
    with TestClient(app) as client:
        schema = client.get('/openapi.json').json()
        for path, method in [('/estancias/entrada', 'post'), ('/estancias/salida', 'post'),
                             ('/estancias/celda', 'patch'), ('/estancias/vehiculo/{placa}', 'get')]:
            assert method in schema['paths'][path]
        assert client.get('/health').json() == {'status': 'ok'}


@pytest.mark.parametrize('metodo,ruta,cuerpo', [
    ('post', '/estancias/entrada', {'placa': 'TEST', 'celda_id': 1}),
    ('post', '/estancias/salida', {'placa': 'TEST'}),
    ('patch', '/estancias/celda', {'placa': 'TEST', 'celda_id': 1}),
])
def test_requiere_sesion_iniciada(metodo, ruta, cuerpo):
    """RF-16: sin token (Authorization: Bearer ...), estos endpoints no se pueden usar."""
    with TestClient(app) as client:
        assert getattr(client, metodo)(ruta, json=cuerpo).status_code == 401


@pytest.mark.parametrize('payload', [
    {}, {'placa': ' ', 'celda_id': 1},
    {'placa': None, 'celda_id': 1},
    {'placa': 'TEST', 'celda_id': 0},
    {'placa': 'TEST', 'celda_id': True},
    {'placa': 'TEST', 'celda_id': '1'},
    {'placa': 'TEST', 'celda_id': 9223372036854775808},
    {'placa': 'TEST', 'celda_id': 1, 'entrada': '2026-01-01'},
    # El operador ya no viaja en el cuerpo (se toma del token): enviarlo se rechaza.
    {'placa': 'TEST', 'celda_id': 1, 'operador_id': 1},
])
def test_entrada_invalida(autenticado, payload):
    assert autenticado.post('/estancias/entrada', json=payload).status_code == 422


def test_salida_no_admite_celda_ni_operador_ni_fecha(autenticado):
    for extra in ({'celda_id': 1}, {'salida': '2026-01-01'}, {'id': 1}, {'operador_id': 1}):
        assert autenticado.post('/estancias/salida', json={'placa': 'TEST', **extra}).status_code == 422
    assert autenticado.get('/estancias/vehiculo/%20%20').status_code == 422


@pytest.mark.parametrize('payload', [
    {}, {'placa': 'TEST'}, {'placa': 'TEST', 'celda_id': 0}, {'placa': ' ', 'celda_id': 1},
])
def test_cambiar_celda_invalida(autenticado, payload):
    assert autenticado.patch('/estancias/celda', json=payload).status_code == 422
