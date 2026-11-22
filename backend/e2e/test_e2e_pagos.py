"""Pruebas E2E de la gestión de pagos (iteración 3, RF-14 y RF-18) con Playwright.

Los pagos anteriores (vencidos hace 3, 5 o 10 días, o vigentes) se siembran directamente en la
base aislada para controlar las fechas; el pago nuevo siempre se registra por la interfaz o la API.
"""

import calendar
import re
from datetime import date, datetime, timedelta, timezone

import pytest
from playwright.sync_api import expect
from sqlalchemy import select
from sqlalchemy.orm import Session

from e2e.conftest import FRONT, evidencia, login_ui, token_api


def hoy() -> date:
    return datetime.now(timezone.utc).date()  # igual que app.services.pago._hoy


def fin_periodo(inicio: date) -> date:
    mes = inicio.month % 12 + 1
    anio = inicio.year + (1 if inicio.month == 12 else 0)
    ultimo = calendar.monthrange(anio, mes)[1]
    if inicio.day > ultimo:
        return date(anio, mes, ultimo)
    return date(anio, mes, inicio.day) - timedelta(days=1)


@pytest.fixture(scope="session")
def oper_pg(api, h_admin, claves):
    r = api.post("/operadores", headers=h_admin, json={
        "nombre": "Operador Pagos", "telefono": "3000000003", "usuario": "operador_pg",
        "password": claves["operador"], "turno": "DIA", "rol": "OPERADOR"})
    assert r.status_code == 201, r.text
    return {"usuario": "operador_pg", "password": claves["operador"], "id": r.json()["id"]}


@pytest.fixture(scope="session")
def h_oper_pg(api, oper_pg):
    return token_api(api, oper_pg["usuario"], oper_pg["password"])


@pytest.fixture(scope="session")
def cliente_pg(api, h_admin):
    r = api.post("/clientes", headers=h_admin, json={"nombre": "Cliente Pagos", "documento": "PG-DOC-1", "telefono": "3011112222"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture(scope="session")
def nuevo_vehiculo(api, h_admin, cliente_pg):
    def _crear(placa: str, tipo: str = "AUTOMOVIL") -> int:
        r = api.post("/vehiculos", headers=h_admin, json={"placa": placa, "color": "Negro", "modelo": 2023,
                                                          "marca": "Kia", "tipo": tipo, "cliente_id": cliente_pg})
        assert r.status_code == 201, r.text
        return r.json()["id"]
    return _crear


@pytest.fixture(scope="session")
def sembrar_pago(oper_pg):
    """Inserta un pago anterior con 'fin' dado (inicio = un mes calendario antes)."""
    from app.config import load_database_settings
    from app.database import create_database_engine
    from app.models import Pago

    engine = create_database_engine(load_database_settings())

    def _sembrar(vehiculo_id: int, fin: date, monto: str = "250000") -> None:
        inicio = fin - timedelta(days=29)
        with Session(engine) as s, s.begin():
            s.add(Pago(vehiculo_id=vehiculo_id, operador_id=oper_pg["id"], monto=monto,
                       periodo_inicio=inicio, periodo_fin=fin))
    return _sembrar


def pagos_de(api, headers, vehiculo_id: int) -> list[dict]:
    r = api.get("/pagos", headers=headers, params={"vehiculo_id": vehiculo_id, "limit": 100})
    assert r.status_code == 200, r.text
    return sorted(r.json()["items"], key=lambda p: p["periodo_fin"])


def abrir_mensualidades(page, oper):
    login_ui(page, oper["usuario"], oper["password"])
    page.get_by_role("link", name="Mensualidades").click()
    expect(page.get_by_role("heading", name="Mensualidades")).to_be_visible()


def registrar_en_ui(page, etiqueta: str):
    page.select_option("#vehiculo_id", label=etiqueta)
    page.get_by_role("button", name="Registrar mensualidad (efectivo)").click()
    expect(page.get_by_role("status").filter(has_text=re.compile("Mensualidad registrada")).first).to_be_visible()


def test_e2e_p01_primer_pago_empieza_hoy(page, oper_pg, h_oper_pg, api, nuevo_vehiculo):
    """Primer pago de un vehículo: la mensualidad empieza hoy y dura un mes calendario (monto $250.000)."""
    vid = nuevo_vehiculo("PGA001")
    abrir_mensualidades(page, oper_pg)
    page.select_option("#vehiculo_id", label="PGA001 · AUTOMOVIL")
    expect(page.get_by_text(re.compile("PGA001: sin mensualidad vigente"))).to_be_visible()
    registrar_en_ui(page, "PGA001 · AUTOMOVIL")
    pago = pagos_de(api, h_oper_pg, vid)[0]
    assert pago["periodo_inicio"] == hoy().isoformat()
    assert pago["periodo_fin"] == fin_periodo(hoy()).isoformat()
    assert pago["monto"] in ("250000.00", "250000")
    expect(page.get_by_text(f"{pago['periodo_inicio']} a {pago['periodo_fin']}").first).to_be_visible()
    evidencia(page, "E2E-P01")


def test_e2e_p02_monto_segun_tipo_de_vehiculo(page, oper_pg, h_oper_pg, api, nuevo_vehiculo):
    """El servidor calcula el monto por tipo: moto $100.000, camioneta y automóvil $250.000."""
    moto, camioneta = nuevo_vehiculo("PGM001", "MOTO"), nuevo_vehiculo("PGC001", "CAMIONETA")
    abrir_mensualidades(page, oper_pg)
    registrar_en_ui(page, "PGM001 · MOTO")
    registrar_en_ui(page, "PGC001 · CAMIONETA")
    assert pagos_de(api, h_oper_pg, moto)[0]["monto"] in ("100000.00", "100000")
    assert pagos_de(api, h_oper_pg, camioneta)[0]["monto"] in ("250000.00", "250000")
    evidencia(page, "E2E-P02")


def test_e2e_p03_renovacion_dentro_de_la_gracia(page, oper_pg, h_oper_pg, api, nuevo_vehiculo, sembrar_pago):
    """Pago 3 días después de vencida: la mensualidad continúa (inicio = fin anterior + 1 día), sin mover la fecha."""
    vid = nuevo_vehiculo("PGR003")
    fin_anterior = hoy() - timedelta(days=3)
    sembrar_pago(vid, fin_anterior)
    abrir_mensualidades(page, oper_pg)
    registrar_en_ui(page, "PGR003 · AUTOMOVIL")
    nuevo = pagos_de(api, h_oper_pg, vid)[-1]
    assert nuevo["periodo_inicio"] == (fin_anterior + timedelta(days=1)).isoformat()
    assert nuevo["periodo_fin"] == fin_periodo(fin_anterior + timedelta(days=1)).isoformat()
    evidencia(page, "E2E-P03")


def test_e2e_p04_pago_anticipado_continua_el_periodo(page, oper_pg, h_oper_pg, api, nuevo_vehiculo, sembrar_pago):
    """Pago con la mensualidad aún vigente (vence en 5 días): el nuevo periodo continúa al día siguiente del fin."""
    vid = nuevo_vehiculo("PGR004")
    fin_anterior = hoy() + timedelta(days=5)
    sembrar_pago(vid, fin_anterior)
    abrir_mensualidades(page, oper_pg)
    page.select_option("#vehiculo_id", label="PGR004 · AUTOMOVIL")
    expect(page.get_by_text(re.compile("PGR004: mensualidad vigente del"))).to_be_visible()
    registrar_en_ui(page, "PGR004 · AUTOMOVIL")
    nuevo = pagos_de(api, h_oper_pg, vid)[-1]
    assert nuevo["periodo_inicio"] == (fin_anterior + timedelta(days=1)).isoformat()
    evidencia(page, "E2E-P04")


def test_e2e_p05_pago_fuera_de_la_gracia_es_mensualidad_nueva(page, oper_pg, h_oper_pg, api, nuevo_vehiculo, sembrar_pago):
    """Pago 10 días después de vencida: es una mensualidad nueva que empieza hoy."""
    vid = nuevo_vehiculo("PGN005")
    sembrar_pago(vid, hoy() - timedelta(days=10))
    abrir_mensualidades(page, oper_pg)
    page.select_option("#vehiculo_id", label="PGN005 · AUTOMOVIL")
    expect(page.get_by_text(re.compile("PGN005: sin mensualidad vigente"))).to_be_visible()
    registrar_en_ui(page, "PGN005 · AUTOMOVIL")
    nuevo = pagos_de(api, h_oper_pg, vid)[-1]
    assert nuevo["periodo_inicio"] == hoy().isoformat()
    assert nuevo["periodo_fin"] == fin_periodo(hoy()).isoformat()
    evidencia(page, "E2E-P05")


def test_e2e_p06_limite_exacto_de_cinco_dias(api, h_oper_pg, nuevo_vehiculo, sembrar_pago):
    """Límite de la gracia: a 5 días continúa el periodo; a 6 días empieza una mensualidad nueva."""
    en_limite, pasado = nuevo_vehiculo("PGL005"), nuevo_vehiculo("PGL006")
    sembrar_pago(en_limite, hoy() - timedelta(days=5))
    sembrar_pago(pasado, hoy() - timedelta(days=6))
    a = api.post("/pagos", headers=h_oper_pg, json={"vehiculo_id": en_limite})
    b = api.post("/pagos", headers=h_oper_pg, json={"vehiculo_id": pasado})
    assert a.status_code == 201 and b.status_code == 201, (a.text, b.text)
    assert a.json()["periodo_inicio"] == (hoy() - timedelta(days=4)).isoformat()
    assert b.json()["periodo_inicio"] == hoy().isoformat()


def test_e2e_p07_periodo_y_monto_no_son_datos_de_entrada(page, oper_pg, api, h_oper_pg, nuevo_vehiculo):
    """La API rechaza (422) monto y periodo_inicio enviados por el cliente y la pantalla no tiene selector de fecha."""
    vid = nuevo_vehiculo("PGV007")
    for cuerpo in ({"vehiculo_id": vid, "monto": "1"}, {"vehiculo_id": vid, "periodo_inicio": "2026-01-01"},
                   {"vehiculo_id": vid, "periodo_fin": "2026-01-31"}):
        assert api.post("/pagos", headers=h_oper_pg, json=cuerpo).status_code == 422, cuerpo
    assert pagos_de(api, h_oper_pg, vid) == []
    abrir_mensualidades(page, oper_pg)
    assert page.locator("input[type=date]").count() == 0
    assert page.locator("input[type=number]").count() == 0
    evidencia(page, "E2E-P07")


def test_e2e_p08_consultar_vigencia(page, oper_pg, nuevo_vehiculo, sembrar_pago):
    """Consultar vigencia: avisa si falta el vehículo, muestra la mensualidad vigente y la ausencia de vigencia."""
    vigente, sin_pago = nuevo_vehiculo("PGQ008"), nuevo_vehiculo("PGQ009")
    sembrar_pago(vigente, hoy() + timedelta(days=10))
    abrir_mensualidades(page, oper_pg)
    page.get_by_role("button", name="Consultar vigencia").click()
    expect(page.get_by_role("alert").filter(has_text=re.compile("Selecciona un veh"))).to_be_visible()
    page.select_option("#vehiculo_id", label="PGQ008 · AUTOMOVIL")
    page.get_by_role("button", name="Consultar vigencia").click()
    expect(page.get_by_text(re.compile("PGQ008: mensualidad vigente del"))).to_be_visible()
    page.select_option("#vehiculo_id", label="PGQ009 · AUTOMOVIL")
    page.get_by_role("button", name="Consultar vigencia").click()
    expect(page.get_by_text(re.compile("PGQ009: sin mensualidad vigente"))).to_be_visible()
    evidencia(page, "E2E-P08")


def test_e2e_p09_la_entrada_exige_mensualidad_vigente(page, oper_pg, api, h_admin, h_oper_pg, nuevo_vehiculo):
    """Entrada: sin mensualidad se rechaza (402); tras registrar la mensualidad la entrada se confirma."""
    nuevo_vehiculo("PGE009")
    celda = api.post("/celdas", headers=h_admin, json={"codigo": "PG-E1", "tipo": "CARRO"})
    assert celda.status_code == 201, celda.text
    login_ui(page, oper_pg["usuario"], oper_pg["password"])
    page.get_by_role("link", name="Control de acceso").click()
    page.fill("#entry-plate", "pge009")
    page.select_option("#entry-cell", label="PG-E1 · CARRO")
    page.get_by_role("button", name="Registrar entrada").click()
    expect(page.get_by_role("alert").filter(has_text=re.compile("mensualidad", re.I))).to_be_visible()
    evidencia(page, "E2E-P09_rechazada")
    page.get_by_role("link", name="Mensualidades").click()
    registrar_en_ui(page, "PGE009 · AUTOMOVIL")
    page.get_by_role("link", name="Control de acceso").click()
    page.fill("#entry-plate", "pge009")
    page.select_option("#entry-cell", label="PG-E1 · CARRO")
    page.get_by_role("button", name="Registrar entrada").click()
    expect(page.get_by_role("status").filter(has_text=re.compile("PGE009")).first).to_be_visible()
    evidencia(page, "E2E-P09")


def test_e2e_p10_sesion_permisos_y_vehiculo_inexistente(api, h_admin, h_oper_pg, nuevo_vehiculo):
    """API de pagos: 401 sin sesión, 404 con vehículo inexistente y lectura permitida a ambos roles."""
    vid = nuevo_vehiculo("PGS010")
    assert api.get("/pagos").status_code == 401
    assert api.post("/pagos", json={"vehiculo_id": vid}).status_code == 401
    assert api.get(f"/vehiculos/{vid}/mensualidad").status_code == 401
    assert api.post("/pagos", headers=h_oper_pg, json={"vehiculo_id": 999999}).status_code == 404
    assert api.get("/vehiculos/999999/mensualidad", headers=h_oper_pg).status_code == 404
    for h in (h_admin, h_oper_pg):
        assert api.get("/pagos", headers=h).status_code == 200
        r = api.get(f"/vehiculos/{vid}/mensualidad", headers=h)
        assert r.status_code == 200 and r.json()["vigente"] is False


def test_e2e_p11_listado_de_pagos_coincide_con_la_api(page, oper_pg, api, h_oper_pg):
    """El listado «Pagos registrados» muestra el mismo total que la API."""
    total = api.get("/pagos", headers=h_oper_pg, params={"limit": 1}).json()["total"]
    assert total > 0
    abrir_mensualidades(page, oper_pg)
    expect(page.locator("section.list .count")).to_have_text(str(total))
    evidencia(page, "E2E-P11")


def texto_limpio(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace(" ", " ")).strip()


def pesos(valor: int) -> str:
    return "$ " + f"{valor:,}".replace(",", ".")


def test_e2e_p12_movimientos_totales_filtros_y_csv(page, oper_pg, api, h_oper_pg):
    """Movimientos: el total recaudado coincide con la API; filtra por placa y tipo, pagina y exporta el CSV filtrado."""
    todos = api.get("/pagos", headers=h_oper_pg, params={"limit": 100}).json()["items"]
    assert len(todos) > 10, "el escenario debe tener más de una página de pagos"
    suma = sum(int(float(p["monto"])) for p in todos)
    login_ui(page, oper_pg["usuario"], oper_pg["password"])
    page.get_by_role("link", name="Pagos", exact=True).click()
    expect(page.get_by_role("heading", name="Movimientos")).to_be_visible()
    expect(page.locator("#total-recaudado")).to_have_text(re.compile(re.escape(pesos(suma)).replace(r"\ ", r"\s")))
    assert texto_limpio(page.locator("#total-recaudado").inner_text()) == pesos(suma)
    expect(page.locator("section.list .count")).to_have_text(str(len(todos)))
    # paginación: 10 por página
    expect(page.get_by_text(re.compile(r"Página 1 de 2"))).to_be_visible()
    assert page.locator("tbody tr").count() == 10
    page.get_by_role("button", name="Siguiente").click()
    expect(page.get_by_text(re.compile(r"Página 2 de 2"))).to_be_visible()
    evidencia(page, "E2E-P12")
    # filtro por tipo de vehículo (moto)
    page.get_by_role("button", name="Anterior").click()
    page.select_option("#tipo", "MOTO")
    filas_moto = page.locator("tbody tr")
    assert filas_moto.count() >= 1
    for i in range(filas_moto.count()):
        assert "$ 100.000" in texto_limpio(filas_moto.nth(i).inner_text())
    # filtro por placa y exportación CSV de lo filtrado
    page.fill("#busqueda", "pgm001")
    expect(page.locator("tbody tr")).to_have_count(1)
    with page.expect_download() as descarga:
        page.get_by_role("button", name="Exportar CSV").click()
    contenido = open(descarga.value.path(), encoding="utf-8-sig").read().splitlines()
    assert len(contenido) == 2 and "PGM001" in contenido[1] and '"Efectivo"' in contenido[1], contenido
    page.get_by_role("button", name="Limpiar filtros").click()
    expect(page.locator("section.list .count")).to_have_text(str(len(todos)))


def test_e2e_p13_registrar_pago_desde_la_pantalla_de_pagos(page, oper_pg, api, h_oper_pg, nuevo_vehiculo):
    """Registrar pago: muestra cliente y vigencia, confirma sin pedir valor ni fecha y aparece en Movimientos."""
    vid = nuevo_vehiculo("PGX013")
    login_ui(page, oper_pg["usuario"], oper_pg["password"])
    page.get_by_role("link", name="Pagos", exact=True).click()
    page.get_by_role("link", name="+ Registrar pago").click()
    expect(page.get_by_role("heading", name="Registrar pago")).to_be_visible()
    assert page.locator("input[type=date], input[type=number]").count() == 0
    page.select_option("#vehiculo_id", label="PGX013 · AUTOMOVIL")
    expect(page.locator("#cliente-pago")).to_have_text("Cliente Pagos")
    expect(page.locator("#vigencia-pago")).to_contain_text("Sin mensualidad vigente")
    expect(page.get_by_text("Operador Pagos").first).to_be_visible()
    page.get_by_role("button", name="Confirmar pago").click()
    aviso = page.locator("p.success")
    expect(aviso).to_contain_text("registrado")
    pago = pagos_de(api, h_oper_pg, vid)[0]
    texto = texto_limpio(aviso.inner_text())
    assert f"PAG-{pago['id']}" in texto and pago["periodo_inicio"] in texto and pesos(250000) in texto, texto
    assert pago["periodo_inicio"] == hoy().isoformat() and pago["operador_id"] == oper_pg["id"]
    evidencia(page, "E2E-P13")
    page.get_by_role("link", name="Ver movimientos").click()
    primera = page.locator("tbody tr").first
    expect(primera).to_contain_text(f"PAG-{pago['id']}")
    expect(primera).to_contain_text("PGX013")
    expect(primera).to_contain_text("Vigente")
    # Cancelar vuelve al historial
    page.get_by_role("link", name="+ Registrar pago").click()
    page.get_by_role("button", name="Cancelar").click()
    expect(page.get_by_role("heading", name="Movimientos")).to_be_visible()


def test_e2e_p14_pagos_exige_sesion_y_lo_usan_ambos_roles(page, admin, oper_pg, api, h_admin, nuevo_vehiculo):
    """Pagos: sin sesión redirige al login; el administrador también registra pagos desde la pantalla."""
    page.goto(f"{FRONT}/gestion/pagos")
    page.wait_for_url(re.compile(r"/login"))
    page.goto(f"{FRONT}/gestion/pagos/nuevo")
    page.wait_for_url(re.compile(r"/login"))
    vid = nuevo_vehiculo("PGX014")
    login_ui(page, admin["usuario"], admin["password"])
    page.get_by_role("link", name="Pagos", exact=True).click()
    expect(page.get_by_role("heading", name="Movimientos")).to_be_visible()
    page.get_by_role("link", name="+ Registrar pago").click()
    page.select_option("#vehiculo_id", label="PGX014 · AUTOMOVIL")
    page.get_by_role("button", name="Confirmar pago").click()
    expect(page.locator("p.success")).to_contain_text("registrado")
    pago = pagos_de(api, h_admin, vid)[0]
    assert pago["operador_id"] != oper_pg["id"]  # queda a nombre del administrador de la sesión
    evidencia(page, "E2E-P14")
