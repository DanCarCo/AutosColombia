"""Pruebas E2E con Playwright (navegador real contra frontend + API + PostgreSQL).

Se habilitan con ``RUN_E2E=1`` y requieren API y frontend en marcha y una base
PostgreSQL AISLADA con migraciones en ``head`` (nunca la base personal).
Las contraseñas de prueba se generan en cada ejecución y no se guardan.
"""

import json
import os
import secrets
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import sync_playwright
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

FRONT = os.environ.get("E2E_FRONT_URL", "http://127.0.0.1:4200")
API = os.environ.get("E2E_API_URL", "http://127.0.0.1:8000")
RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "entrega-ingenieria-software" / "evidencias" / "e2e"
RESULTADOS: dict[str, dict] = {}


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_E2E") != "1":
        saltar = pytest.mark.skip(reason="Pruebas E2E: defina RUN_E2E=1 con API, frontend y BD aislada")
        for item in items:
            if Path(str(item.fspath)).resolve().parent == Path(__file__).resolve().parent:
                item.add_marker(saltar)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    salida = yield
    informe = salida.get_result()
    if informe.when == "call" or (informe.when == "setup" and informe.failed):
        doc = (item.function.__doc__ or "").strip().splitlines()[0] if item.function.__doc__ else item.name
        ident = item.name.split("_")[2].upper() if item.name.startswith("test_e2e_") else item.name
        ident = f"E2E-{ident}"
        RESULTADOS[ident] = {
            "id": ident,
            "prueba": doc,
            "estado": "Aprobado" if informe.passed else "Fallido",
            "duracion_s": round(informe.duration, 2),
            "detalle": "" if informe.passed else str(informe.longrepr)[-1500:],
        }


def pytest_sessionfinish(session, exitstatus):
    if RESULTADOS:
        SALIDA.mkdir(parents=True, exist_ok=True)
        (SALIDA / "_resultados_e2e.json").write_text(
            json.dumps(
                {"ejecutado": time.strftime("%Y-%m-%d %H:%M:%S"), "resultados": dict(sorted(RESULTADOS.items()))},
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )


@pytest.fixture(scope="session")
def claves() -> dict[str, str]:
    return {"admin": secrets.token_urlsafe(12) + "Aa1", "operador": secrets.token_urlsafe(12) + "Bb2"}


@pytest.fixture(scope="session")
def admin(claves):
    """Primer administrador de la base aislada (equivale a crear_administrador.py)."""
    from app.database import create_database_engine
    from app.config import load_database_settings
    from app.models import Operador
    from app.security import hash_password

    engine = create_database_engine(load_database_settings())
    with Session(engine) as s, s.begin():
        s.execute(text("TRUNCATE token_revocado, pago, estancia, vehiculo, cliente, celda, operador RESTART IDENTITY CASCADE"))
        s.add(Operador(nombre="Admin E2E", telefono="3000000001", usuario="admin_e2e",
                       password_hash=hash_password(claves["admin"]), turno="DIA", rol="ADMINISTRADOR"))
    return {"usuario": "admin_e2e", "password": claves["admin"]}


@pytest.fixture(scope="session")
def pw():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def navegador(pw):
    b = pw.chromium.launch(headless=True)
    yield b
    b.close()


@pytest.fixture()
def page(navegador):
    ctx = navegador.new_context(viewport={"width": 1366, "height": 900}, locale="es-CO", timezone_id="America/Bogota")
    p = ctx.new_page()
    p.set_default_timeout(10000)
    yield p
    ctx.close()


@pytest.fixture(scope="session")
def api():
    with httpx.Client(base_url=API, timeout=15) as c:
        yield c


def token_api(api, usuario: str, password: str) -> dict:
    r = api.post("/auth/login", json={"usuario": usuario, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def h_admin(api, admin):
    return token_api(api, admin["usuario"], admin["password"])


def login_ui(page, usuario: str, password: str):
    page.goto(f"{FRONT}/login")
    page.fill("#usuario", usuario)
    page.fill("#password", password)
    page.click("button[type=submit]")


def evidencia(page, ident: str, nombre: str = ""):
    SALIDA.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SALIDA / f"{ident}{('_' + nombre) if nombre else ''}.png"))
