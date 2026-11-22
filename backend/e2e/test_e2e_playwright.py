"""Pruebas E2E del sistema Autos Colombia con Playwright (Chromium)."""

import re

import pytest
from playwright.sync_api import expect

from e2e.conftest import FRONT, evidencia, login_ui, token_api

JS_TOKEN = """() => {
  for (const k of Object.keys(localStorage)) {
    const v = localStorage.getItem(k);
    const m = v && v.match(/eyJ[\\w-]+\\.[\\w-]+\\.[\\w-]+/);
    if (m) return m[0];
  }
  return null;
}"""


@pytest.fixture(scope="session")
def operador(api, h_admin, claves):
    r = api.post("/operadores", headers=h_admin, json={
        "nombre": "Operador E2E", "telefono": "3000000002", "usuario": "operador_e2e",
        "password": claves["operador"], "turno": "DIA", "rol": "OPERADOR"})
    assert r.status_code == 201, r.text
    return {"usuario": "operador_e2e", "password": claves["operador"]}


@pytest.fixture(scope="session")
def h_oper(api, operador):
    return token_api(api, operador["usuario"], operador["password"])


@pytest.fixture(scope="session")
def datos(api, h_admin, h_oper):
    """Celdas, cliente y tres vehículos (uno sin mensualidad) para el flujo de acceso."""
    d = {}
    for cod in ("E2E-A1", "E2E-A2", "E2E-A3"):
        r = api.post("/celdas", headers=h_admin, json={"codigo": cod, "tipo": "CARRO"})
        assert r.status_code == 201, r.text
        d[cod] = r.json()["id"]
    c = api.post("/clientes", headers=h_admin, json={"nombre": "Cliente E2E", "documento": "E2E-DOC-1", "telefono": "3001234567"})
    assert c.status_code == 201, c.text
    d["cliente"] = c.json()["id"]
    for placa in ("E2E001", "E2E002", "E2E003"):
        v = api.post("/vehiculos", headers=h_admin, json={"placa": placa, "color": "Rojo", "modelo": 2022,
                                                          "marca": "Mazda", "tipo": "AUTOMOVIL", "cliente_id": d["cliente"]})
        assert v.status_code == 201, v.text
        d[placa] = v.json()["id"]
    for placa in ("E2E001", "E2E002"):
        p = api.post("/pagos", headers=h_oper, json={"vehiculo_id": d[placa]})
        assert p.status_code == 201, p.text
    return d


def menu(page) -> list[str]:
    return [t.strip() for t in page.locator("nav[aria-label='Navegación principal'] a").all_inner_texts()]


def test_e2e_01_login_administrador_y_menu(page, admin):
    """Login del administrador: menú de gestión sin Control de acceso."""
    login_ui(page, admin["usuario"], admin["password"])
    expect(page.get_by_role("button", name="Cerrar sesión")).to_be_visible()
    m = menu(page)
    assert {"Vehículos", "Celdas", "Operadores", "Clientes", "Mensualidades", "Reportes"} <= set(m), m
    assert "Control de acceso" not in m
    evidencia(page, "E2E-01")


def test_e2e_02_login_operador_y_menu(page, operador):
    """Login del operador: menú con Control de acceso y sin gestión."""
    login_ui(page, operador["usuario"], operador["password"])
    expect(page.get_by_role("link", name="Control de acceso")).to_be_visible()
    m = menu(page)
    assert "Control de acceso" in m and not ({"Operadores", "Celdas", "Clientes", "Vehículos"} & set(m)), m
    evidencia(page, "E2E-02")


def test_e2e_03_credenciales_incorrectas(page, admin, operador):
    """Credenciales incorrectas: mensaje genérico idéntico para usuario inexistente y clave errónea."""
    mensajes = []
    for usuario, clave in ((admin["usuario"], "ClaveIncorrecta-1"), ("no_existe_e2e", "ClaveIncorrecta-1")):
        login_ui(page, usuario, clave)
        alerta = page.get_by_role("alert")
        expect(alerta).to_be_visible()
        mensajes.append(alerta.inner_text().strip())
    assert mensajes[0] == mensajes[1] and mensajes[0], mensajes
    assert re.search(r"incorrect", mensajes[0], re.I)
    assert "/login" in page.url
    evidencia(page, "E2E-03")


def test_e2e_04_campos_obligatorios_login(page):
    """Login con campos vacíos: la interfaz indica los campos obligatorios y no envía la solicitud."""
    enviadas = []
    page.on("request", lambda r: enviadas.append(r.url) if r.url.endswith("/auth/login") else None)
    page.goto(f"{FRONT}/login")
    page.click("button[type=submit]")
    expect(page.get_by_text("El usuario es obligatorio.")).to_be_visible()
    expect(page.get_by_text("La contraseña es obligatoria.")).to_be_visible()
    assert enviadas == []
    evidencia(page, "E2E-04")


def test_e2e_05_admin_crea_operador_en_interfaz(page, admin, api, claves):
    """El administrador crea un operador desde la pantalla Operadores y puede iniciar sesión."""
    login_ui(page, admin["usuario"], admin["password"])
    page.get_by_role("link", name="Operadores").click()
    page.get_by_role("button", name="+ Nuevo operador").click()
    page.fill("#nombre", "Operador UI")
    page.fill("#telefono", "0031234567")
    page.fill("#usuario", "operador_ui")
    page.fill("#password", claves["operador"])
    page.select_option("#turno", "NOCHE")
    page.select_option("#rol", "OPERADOR")
    page.get_by_role("button", name="Guardar operador").click()
    expect(page.locator("p.notice.success")).to_contain_text(re.compile("registrado", re.I))
    expect(page.get_by_role("cell", name="operador_ui")).to_be_visible()
    expect(page.get_by_role("cell", name="0031234567")).to_be_visible()  # conserva ceros iniciales
    evidencia(page, "E2E-05")
    assert api.post("/auth/login", json={"usuario": "operador_ui", "password": claves["operador"]}).status_code == 200


def test_e2e_06_operador_duplicado_y_validaciones(page, admin, claves):
    """Operador: campos obligatorios validados en el formulario y usuario duplicado rechazado."""
    login_ui(page, admin["usuario"], admin["password"])
    page.get_by_role("link", name="Operadores").click()
    page.get_by_role("button", name="+ Nuevo operador").click()
    page.get_by_role("button", name="Guardar operador").click()
    errores = page.locator(".field-error").all_inner_texts()
    assert sum(1 for e in errores if e.strip()) >= 5, errores
    evidencia(page, "E2E-06_validacion")
    page.fill("#nombre", "Duplicado")
    page.fill("#telefono", "3000000009")
    page.fill("#usuario", "operador_ui")
    page.fill("#password", claves["operador"])
    page.select_option("#turno", "DIA")
    page.select_option("#rol", "OPERADOR")
    page.get_by_role("button", name="Guardar operador").click()
    expect(page.get_by_role("alert").filter(has_text=re.compile("ya existe", re.I))).to_be_visible()
    evidencia(page, "E2E-06")


def test_e2e_07_crud_celdas_en_interfaz(page, admin):
    """Celdas: crear, rechazar duplicada, validar obligatorios, editar y eliminar desde la interfaz."""
    login_ui(page, admin["usuario"], admin["password"])
    page.get_by_role("link", name="Celdas").click()
    page.get_by_role("button", name="+ Nueva celda").click()
    page.get_by_role("button", name="Guardar celda").click()
    assert sum(1 for e in page.locator(".field-error").all_inner_texts() if e.strip()) >= 2
    page.fill("#codigo", "e2e-ui-01")
    page.fill("#tipo", "MOTO")
    page.get_by_role("button", name="Guardar celda").click()
    expect(page.get_by_role("cell", name="E2E-UI-01")).to_be_visible()  # código normalizado
    page.get_by_role("button", name="+ Nueva celda").click()
    page.fill("#codigo", "E2E-UI-01")
    page.fill("#tipo", "MOTO")
    page.get_by_role("button", name="Guardar celda").click()
    expect(page.get_by_role("alert").filter(has_text=re.compile("ya existe", re.I)).first).to_be_visible()
    page.get_by_role("button", name="Cancelar", exact=True).click()
    page.get_by_role("button", name="Editar E2E-UI-01").click()
    page.fill("#tipo", "ESPECIAL")
    page.get_by_role("button", name="Guardar celda").click()
    expect(page.get_by_role("cell", name="ESPECIAL")).to_be_visible()
    evidencia(page, "E2E-07")
    page.get_by_role("button", name="Eliminar E2E-UI-01").click()
    page.get_by_role("button", name="Confirmar eliminación").click()
    expect(page.get_by_role("cell", name="E2E-UI-01")).to_have_count(0)


def test_e2e_08_clientes_y_vehiculos_en_interfaz(page, admin):
    """Clientes y vehículos: el administrador registra un cliente y un vehículo asociado desde la interfaz."""
    login_ui(page, admin["usuario"], admin["password"])
    page.get_by_role("link", name="Clientes").click()
    page.get_by_role("button", name="Nuevo cliente").click()
    page.fill("#nombre", "Cliente UI")
    page.fill("#documento", "E2E-UI-DOC")
    page.fill("#telefono", "3109998877")
    page.get_by_role("button", name="Guardar cliente").click()
    expect(page.get_by_role("cell", name="E2E-UI-DOC")).to_be_visible()
    page.get_by_role("link", name="Vehículos").click()
    page.get_by_role("button", name=re.compile("Nuevo veh", re.I)).click()
    page.fill("#placa", "uie2e1")
    page.fill("#marca", "Renault")
    page.fill("#modelo", "2021")
    page.fill("#color", "Azul")
    page.select_option("#tipo", index=1)
    page.select_option("#cliente_id", index=page.locator("#cliente_id option").count() - 1)
    page.get_by_role("button", name="Guardar vehículo").click()
    expect(page.get_by_text("Cargando vehículos")).to_have_count(0)
    paginacion = page.get_by_role("navigation", name="Paginación de vehículos")
    for _ in range(10):  # el listado es paginado: avanza a la última página, donde queda el vehículo nuevo
        expect(page.get_by_role("button", name="Actualizar listado")).to_be_enabled()  # termina de cargar
        m = re.search(r"Página (\d+) de (\d+)", paginacion.inner_text())
        if m is None or m.group(1) == m.group(2):
            break
        paginacion.get_by_role("button", name="Siguiente").click()
        expect(page.get_by_text("Cargando vehículos")).to_have_count(0)
    expect(page.get_by_role("cell", name="UIE2E1")).to_be_visible()
    evidencia(page, "E2E-08")


def test_e2e_09_entrada_rechazada_sin_mensualidad(page, operador, datos):
    """Control de acceso: la entrada de un vehículo sin mensualidad vigente es rechazada."""
    login_ui(page, operador["usuario"], operador["password"])
    page.get_by_role("link", name="Control de acceso").click()
    page.fill("#entry-plate", "e2e003")
    page.select_option("#entry-cell", label="E2E-A1 · CARRO")
    page.get_by_role("button", name="Registrar entrada").click()
    expect(page.get_by_role("alert").filter(has_text=re.compile("mensualidad", re.I))).to_be_visible()
    evidencia(page, "E2E-09")


def test_e2e_10_mensualidad_desde_interfaz(page, operador, datos, api, h_oper):
    """Mensualidades: registrar y consultar vigencia desde la interfaz (monto calculado por el servidor)."""
    login_ui(page, operador["usuario"], operador["password"])
    page.get_by_role("link", name="Mensualidades").click()
    page.select_option("#vehiculo_id", label="E2E003 · AUTOMOVIL")
    page.get_by_role("button", name="Registrar mensualidad").click()
    expect(page.get_by_role("status").filter(has_text=re.compile("registrad", re.I)).first).to_be_visible()
    page.select_option("#vehiculo_id", label="E2E003 · AUTOMOVIL")
    page.get_by_role("button", name="Consultar vigencia").click()
    expect(page.get_by_text(re.compile("mensualidad vigente del"))).to_be_visible()
    evidencia(page, "E2E-10")
    r = api.post("/pagos", headers=h_oper, json={"vehiculo_id": datos["E2E001"], "monto": "1"})
    assert r.status_code == 422, r.text


def test_e2e_11_ciclo_entrada_consulta_correccion_salida(page, operador, datos):
    """Control de acceso: entrada, duplicada, consulta, corrección de celda y salida."""
    login_ui(page, operador["usuario"], operador["password"])
    page.get_by_role("link", name="Control de acceso").click()
    page.fill("#entry-plate", " e2e001 ")
    page.select_option("#entry-cell", label="E2E-A1 · CARRO")
    page.get_by_role("button", name="Registrar entrada").click()
    expect(page.get_by_role("status").filter(has_text=re.compile("E2E001")).first).to_be_visible()
    page.fill("#entry-plate", "E2E001")
    page.select_option("#entry-cell", label="E2E-A2 · CARRO")
    page.get_by_role("button", name="Registrar entrada").click()
    expect(page.get_by_role("alert").filter(has_text=re.compile("ya está dentro", re.I))).to_be_visible()
    page.fill("#query-plate", "E2E001")
    page.get_by_role("button", name="Consultar vehículo").click()
    expect(page.get_by_text(re.compile("E2E001 · Dentro"))).to_be_visible()
    evidencia(page, "E2E-11_dentro")
    page.fill("#move-plate", "E2E001")
    page.select_option("#move-cell", label="E2E-A3 · CARRO")
    page.get_by_role("button", name="Mover vehículo de celda").click()
    expect(page.get_by_role("status").filter(has_text=re.compile("E2E-A3")).first).to_be_visible()
    page.get_by_role("button", name="Consultar vehículo").click()
    expect(page.get_by_text(re.compile("Celda E2E-A3"))).to_be_visible()
    page.get_by_role("button", name="Confirmar salida").click()
    expect(page.get_by_text(re.compile("E2E001 · Fuera"))).to_be_visible()
    evidencia(page, "E2E-11")


def test_e2e_12_consulta_vehiculo_no_registrado(page, operador, datos):
    """Control de acceso: consultar una placa inexistente informa que no está registrada."""
    login_ui(page, operador["usuario"], operador["password"])
    page.get_by_role("link", name="Control de acceso").click()
    page.fill("#query-plate", "NOEXISTE9")
    page.get_by_role("button", name="Consultar vehículo").click()
    expect(page.get_by_role("alert").filter(has_text=re.compile("no registrad|no existe|no encontr", re.I))).to_be_visible()
    evidencia(page, "E2E-12")


def test_e2e_13_reportes_resumen(page, admin, api, h_admin, datos):
    """Reportes: la pantalla muestra celdas disponibles/totales y clientes iguales a los de la API."""
    esperado = api.get("/reportes/resumen", headers=h_admin).json()
    login_ui(page, admin["usuario"], admin["password"])
    page.get_by_role("link", name="Reportes").click()
    expect(page.locator("#celdas-totales")).to_have_text(str(esperado["celdas_totales"]))
    expect(page.locator("#celdas-disponibles")).to_have_text(str(esperado["celdas_disponibles"]))
    expect(page.locator("#clientes-registrados")).to_have_text(str(esperado["clientes_registrados"]))
    evidencia(page, "E2E-13")


def test_e2e_14_guardas_de_ruta_por_rol(page, operador, admin):
    """Rutas protegidas: sin sesión → login; operador no entra a gestión; administrador no entra a Control de acceso."""
    page.goto(f"{FRONT}/control-acceso")
    page.wait_for_url(re.compile(r"/login"))
    login_ui(page, operador["usuario"], operador["password"])
    expect(page.get_by_role("button", name="Cerrar sesión")).to_be_visible()
    page.goto(f"{FRONT}/gestion/celdas")
    page.wait_for_url(f"{FRONT}/")
    evidencia(page, "E2E-14_operador")
    page.get_by_role("button", name="Cerrar sesión").click()
    login_ui(page, admin["usuario"], admin["password"])
    expect(page.get_by_role("button", name="Cerrar sesión")).to_be_visible()
    page.goto(f"{FRONT}/control-acceso")
    page.wait_for_url(f"{FRONT}/")
    evidencia(page, "E2E-14")


def test_e2e_15_cierre_de_sesion_revoca_token(page, operador, api):
    """Cierre de sesión: vuelve al login y el token anterior responde 401."""
    login_ui(page, operador["usuario"], operador["password"])
    page.get_by_role("link", name="Control de acceso").wait_for()
    token = page.evaluate(JS_TOKEN)
    assert token, "No se encontró el token en localStorage"
    assert api.get("/celdas/disponibles", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    page.get_by_role("button", name="Cerrar sesión").click()
    expect(page.get_by_role("link", name="Iniciar sesión")).to_be_visible()
    codigo = None
    for _ in range(20):  # la revocación viaja en segundo plano: espera a que el servidor la registre
        codigo = api.get("/celdas/disponibles", headers={"Authorization": f"Bearer {token}"}).status_code
        if codigo == 401:
            break
        page.wait_for_timeout(250)
    assert codigo == 401
    evidencia(page, "E2E-15")


def test_e2e_16_api_sin_sesion_y_permisos(api, h_oper, h_admin):
    """API: sin sesión 401 en módulos de negocio; operador 403 en gestión; administrador 403 en entradas."""
    for ruta in ("/celdas", "/operadores", "/clientes", "/vehiculos", "/pagos", "/reportes/resumen"):
        assert api.get(ruta).status_code == 401, ruta
    assert api.get("/health").json() == {"status": "ok"}
    assert api.get("/operadores", headers=h_oper).status_code == 403
    assert api.post("/celdas", headers=h_oper, json={"codigo": "X", "tipo": "Y"}).status_code == 403
    assert api.post("/estancias/entrada", headers=h_admin, json={"placa": "E2E001", "celda_id": 1}).status_code == 403
