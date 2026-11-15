"""Las pantallas de gestión (operadores, celdas, clientes, vehículos) solo
permiten crear, editar o eliminar con sesión iniciada; las lecturas quedan
abiertas, igual que en /estancias y /pagos."""
from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.mark.parametrize("metodo,ruta,cuerpo", [
    ("post", "/operadores", {}),
    ("patch", "/operadores/1", {}),
    ("delete", "/operadores/1", None),
    ("post", "/celdas", {}),
    ("patch", "/celdas/1", {}),
    ("delete", "/celdas/1", None),
    ("post", "/clientes", {}),
    ("patch", "/clientes/1", {}),
    ("delete", "/clientes/1", None),
    ("post", "/vehiculos", {}),
    ("patch", "/vehiculos/1", {}),
    ("delete", "/vehiculos/1", None),
])
def test_mutaciones_de_gestion_requieren_sesion(metodo, ruta, cuerpo):
    with TestClient(app) as client:
        llamada = getattr(client, metodo)
        resultado = llamada(ruta, json=cuerpo) if cuerpo is not None else llamada(ruta)
        assert resultado.status_code == 401


@pytest.mark.parametrize("ruta", ["/operadores", "/celdas", "/clientes", "/vehiculos"])
def test_listados_de_gestion_no_requieren_sesion(ruta):
    """Las lecturas siguen abiertas; solo las escrituras exigen sesión."""
    with TestClient(app) as client:
        assert client.get(ruta).status_code == 200
