"""RF-16: matriz de permisos por rol. Sin sesión 401; con un rol no permitido 403; con el permitido se atiende la ruta."""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from conftest import sesion_como

ADMIN, OPER = "ADMINISTRADOR", "OPERADOR"
AMBOS = (ADMIN, OPER)
OPERADOR_NUEVO = {"nombre": "N", "telefono": "1", "usuario": "u", "password": "p", "turno": "DIA", "rol": "OPERADOR"}
CELDA = {"codigo": "A-1", "tipo": "CARRO"}
CLIENTE = {"nombre": "N", "documento": "1", "telefono": "1"}
VEHICULO = {"placa": "ABC123", "color": "x", "modelo": 2020, "marca": "m", "tipo": "MOTO", "cliente_id": 1}

MATRIZ = [
    ("GET", "/operadores", None, (ADMIN,)), ("POST", "/operadores", OPERADOR_NUEVO, (ADMIN,)),
    ("GET", "/operadores/1", None, (ADMIN,)), ("PATCH", "/operadores/1", {"turno": "NOCHE"}, (ADMIN,)),
    ("DELETE", "/operadores/1", None, (ADMIN,)),
    ("GET", "/celdas", None, (ADMIN,)), ("POST", "/celdas", CELDA, (ADMIN,)), ("GET", "/celdas/1", None, (ADMIN,)),
    ("PATCH", "/celdas/1", {"tipo": "MOTO"}, (ADMIN,)), ("DELETE", "/celdas/1", None, (ADMIN,)),
    ("GET", "/celdas/disponibles", None, AMBOS),
    ("GET", "/clientes", None, AMBOS), ("GET", "/clientes/1", None, AMBOS), ("POST", "/clientes", CLIENTE, (ADMIN,)),
    ("PATCH", "/clientes/1", {"telefono": "2"}, (ADMIN,)), ("DELETE", "/clientes/1", None, (ADMIN,)),
    ("GET", "/vehiculos", None, AMBOS), ("GET", "/vehiculos/1", None, AMBOS), ("POST", "/vehiculos", VEHICULO, (ADMIN,)),
    ("PATCH", "/vehiculos/1", {"color": "y"}, (ADMIN,)), ("DELETE", "/vehiculos/1", None, (ADMIN,)),
    ("POST", "/estancias/entrada", {"placa": "ABC123", "celda_id": 1}, (OPER,)),
    ("POST", "/estancias/salida", {"placa": "ABC123"}, (OPER,)),
    ("PATCH", "/estancias/celda", {"placa": "ABC123", "celda_id": 1}, (OPER,)),
    ("GET", "/estancias/vehiculo/ABC123", None, AMBOS),
    ("POST", "/pagos", {"vehiculo_id": 1}, AMBOS), ("GET", "/pagos", None, AMBOS), ("GET", "/vehiculos/1/mensualidad", None, AMBOS),
    ("GET", "/reportes/resumen", None, AMBOS),
]


@pytest.fixture
def client():
    def override():
        yield MagicMock()
    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.parametrize("metodo,ruta,cuerpo,permitidos", MATRIZ, ids=[f"{m} {r}" for m, r, _, _ in MATRIZ])
def test_permisos_por_rol(client, metodo, ruta, cuerpo, permitidos):
    assert client.request(metodo, ruta, json=cuerpo).status_code == 401  # sin sesión
    for rol in AMBOS:
        with sesion_como(rol):
            codigo = client.request(metodo, ruta, json=cuerpo).status_code
        if rol in permitidos:
            assert codigo not in (401, 403), f"{rol} debería poder usar {metodo} {ruta} (respondió {codigo})"
        else:
            assert codigo == 403, f"{rol} no debería poder usar {metodo} {ruta} (respondió {codigo})"


def test_rutas_publicas_no_exigen_sesion(client):
    assert client.get("/health").status_code == 200
    assert client.post("/auth/login", json={"usuario": "x", "password": "y"}).status_code != 403
