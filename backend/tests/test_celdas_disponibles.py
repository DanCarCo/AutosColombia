"""RF-10: celdas sin estancia abierta en este momento. Sin depender de PostgreSQL."""
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.services.celda import list_available_cells


def test_list_available_cells_calls_session_and_paginates():
    session = MagicMock()
    session.scalar.return_value = 3
    session.scalars.return_value = []
    result = list_available_cells(session, offset=0, limit=20)
    assert result == {"items": [], "total": 3, "offset": 0, "limit": 20}


def test_disponibles_route_is_registered_before_the_id_route():
    """'/celdas/disponibles' no debe interpretarse como '/celdas/{id}' con id='disponibles'."""
    session = MagicMock()
    session.scalar.return_value = 0
    session.scalars.return_value = []

    def override():
        yield session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            response = client.get("/celdas/disponibles")
    finally:
        app.dependency_overrides.pop(get_session, None)
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "offset": 0, "limit": 20}
