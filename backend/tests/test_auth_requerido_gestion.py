"""Las pantallas de gestión (operadores, celdas, clientes, vehículos) solo
permiten crear, editar o eliminar con sesión iniciada; con los roles (RF-17)
también las lecturas exigen sesión."""
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
def test_listados_de_gestion_tambien_requieren_sesion(ruta):
    """RF-16: con los roles, también las lecturas exigen sesión (401 sin token).
    Los permisos por rol (403) se verifican en test_roles.py."""
    with TestClient(app) as client:
        assert client.get(ruta).status_code == 401
