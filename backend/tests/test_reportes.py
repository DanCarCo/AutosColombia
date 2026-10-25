"""RF-15: resumen de celdas disponibles/totales y clientes registrados."""
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.services.reporte import resumen


def test_resumen_devuelve_los_tres_conteos():
    session = MagicMock()
    session.scalar.side_effect = [80, 23, 15]  # celdas_totales, celdas_disponibles, clientes_registrados
    assert resumen(session) == {
        "celdas_totales": 80,
        "celdas_disponibles": 23,
        "clientes_registrados": 15,
    }


def test_resumen_endpoint_no_requiere_sesion_iniciada():
    session = MagicMock()
    session.scalar.side_effect = [80, 23, 15]

    def override():
        yield session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            response = client.get("/reportes/resumen")
    finally:
        app.dependency_overrides.pop(get_session, None)
    assert response.status_code == 200
    assert response.json()["celdas_disponibles"] == 23
