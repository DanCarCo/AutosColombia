"""Genera AutosColombia.mdj (modelo de StarUML) desde una descripción en Python.

Uso (solo biblioteca estándar; no necesita el entorno virtual del backend):

    python generar_mdj.py

Escribe ``AutosColombia.mdj`` en esta carpeta, en UTF-8. Los ids son
deterministas, así que volver a generarlo no produce cambios si la
descripción no cambia.

El archivo contiene el MODELO completo (clases, relaciones, actores, casos de
uso, componentes) más diagramas vacíos con nombre. Los diagramas se dibujan
arrastrando los elementos desde el Model Explorer: StarUML traza solas las
relaciones entre los elementos soltados. Ver docs/06-staruml.md.
"""

import hashlib
import json
from pathlib import Path

SALIDA = Path(__file__).with_name("AutosColombia.mdj")


def _id(clave: str) -> str:
    return "AAAAAA" + hashlib.sha1(clave.encode("utf-8")).hexdigest()[:14] + "="


def ref(elemento: dict) -> dict:
    return {"$ref": elemento["_id"]}


def nodo(tipo: str, padre: dict | None, nombre: str, **extra) -> dict:
    clave = f"{padre['_id'] if padre else ''}/{tipo}/{nombre}/{extra.get('_k', '')}"
    extra.pop("_k", None)
    d = {"_type": tipo, "_id": _id(clave)}
    if padre is not None:
        d["_parent"] = ref(padre)
    if nombre:
        d["name"] = nombre
    d.update(extra)
    return d


def agregar(padre: dict, hijo: dict, clave: str = "ownedElements") -> dict:
    padre.setdefault(clave, []).append(hijo)
    return hijo


def paquete(padre: dict, nombre: str, doc: str = "") -> dict:
    p = nodo("UMLPackage", padre, nombre, **({"documentation": doc} if doc else {}))
    return agregar(padre, p)


def diagrama(padre: dict, tipo: str, nombre: str, doc: str = "", defecto: bool = False) -> dict:
    d = nodo(tipo, padre, nombre, model=ref(padre))
    if doc:
        d["documentation"] = doc
    if defecto:
        d["defaultDiagram"] = True
    return agregar(padre, d)


def enumeracion(padre: dict, nombre: str, literales: list[str], doc: str) -> dict:
    e = agregar(padre, nodo("UMLEnumeration", padre, nombre, documentation=doc))
    for lit in literales:
        agregar(e, nodo("UMLEnumerationLiteral", e, lit))
    return e


def clase(padre: dict, nombre: str, atributos: list[tuple], doc: str, operaciones: list[str] | None = None) -> dict:
    c = agregar(padre, nodo("UMLClass", padre, nombre, documentation=doc))
    for a in atributos:
        nom, tipo = a[0], a[1]
        extra = {}
        if len(a) > 2 and a[2]:
            extra["documentation"] = a[2]
        if len(a) > 3 and a[3]:
            extra["multiplicity"] = a[3]
        agregar(c, nodo("UMLAttribute", c, nom, visibility="public", type=tipo, **extra), "attributes")
    for op in operaciones or []:
        agregar(c, nodo("UMLOperation", c, op, visibility="public"), "operations")
    return c


def asociacion(padre: dict, a: dict, rol_a: str, mult_a: str, b: dict, rol_b: str, mult_b: str, nombre: str = "") -> dict:
    s = agregar(padre, nodo("UMLAssociation", padre, nombre, _k=f"{a['name']}-{b['name']}-{rol_b}"))
    e1 = nodo("UMLAssociationEnd", s, rol_a, reference=ref(a), multiplicity=mult_a, navigable=False, _k="1")
    e2 = nodo("UMLAssociationEnd", s, rol_b, reference=ref(b), multiplicity=mult_b, navigable=True, _k="2")
    s["end1"], s["end2"] = e1, e2
    return s


def construir() -> dict:
    proyecto = {"_type": "Project", "_id": _id("proyecto"), "name": "AutosColombia"}
    modelo = agregar(proyecto, nodo("UMLModel", proyecto, "AutosColombia"))

    # ------------------------------------------------------------------ Dominio
    dom = paquete(modelo, "Dominio", "Modelo de dominio; coincide con backend/app/models.py (migraciones 0001 a 0004).")
    tipo_veh = enumeracion(dom, "TipoVehiculo", ["MOTO", "AUTOMOVIL", "CAMIONETA"], "Valores permitidos por el CHECK ck_vehiculo_tipo.")
    turno = enumeracion(dom, "Turno", ["DIA", "NOCHE"], "Valores permitidos por el CHECK ck_operador_turno.")
    rol = enumeracion(dom, "Rol", ["ADMINISTRADOR", "OPERADOR"], "Valores permitidos por el CHECK ck_operador_rol (migración 0005).")
    cliente = clase(dom, "Cliente", [
        ("id", "Long", "Identidad generada."), ("nombre", "String"),
        ("documento", "String", "Único (uq_cliente_documento)."), ("telefono", "String")],
        "Tabla cliente (RF-12). Dueño de uno o más vehículos.")
    vehiculo = clase(dom, "Vehiculo", [
        ("id", "Long"), ("placa", "String", "Única; normalizada a mayúsculas."), ("color", "String"),
        ("modelo", "Integer", "Año entre 1900 y 2200 (CHECK ck_vehiculo_modelo_anio, migración 0004)."),
        ("marca", "String"), ("tipo", "TipoVehiculo"), ("cliente_id", "Long", "FK a cliente; obligatoria.")],
        "Tabla vehiculo. Todo vehículo pertenece a un cliente (RF-12, RF-13).")
    celda = clase(dom, "Celda", [
        ("id", "Long"), ("codigo", "String", "Único y normalizado a mayúsculas."), ("tipo", "String", "Texto libre obligatorio.")],
        "Tabla celda (RF-06, RF-10). El parqueadero inicia con 80: 10 MOTO y 70 CARRO.")
    operador = clase(dom, "Operador", [
        ("id", "Long"), ("nombre", "String"), ("telefono", "String"), ("usuario", "String", "Único."),
        ("password_hash", "String", "PBKDF2-SHA256; nunca la contraseña en claro."), ("turno", "Turno"),
        ("rol", "Rol", "ADMINISTRADOR gestiona usuarios y celdas; OPERADOR registra accesos (RF-17).")],
        "Tabla operador (RF-07, RF-16). Inicia sesión con usuario y contraseña.")
    estancia = clase(dom, "Estancia", [
        ("id", "Long"), ("entrada", "DateTime"), ("salida", "DateTime", "Nula mientras la estancia está abierta.", "0..1"),
        ("vehiculo_id", "Long"), ("celda_id", "Long"), ("operador_entrada_id", "Long"),
        ("operador_salida_id", "Long", "Obligatoria si y solo si hay salida.", "0..1")],
        "Tabla estancia. Como máximo una estancia abierta por vehículo y por celda (índices únicos parciales).",
        ["esta_abierta()", "cerrar(fecha_salida, operador)"])
    pago = clase(dom, "Pago", [
        ("id", "Long"), ("vehiculo_id", "Long"), ("operador_id", "Long"),
        ("monto", "Decimal", "Lo calcula el servidor según el tipo de vehículo; nunca lo envía el cliente."),
        ("periodo_inicio", "Date", "Lo calcula el servidor (RF-18): continúa el anterior + 1 día si el pago llega hasta 5 días tarde, o empieza hoy."),
        ("periodo_fin", "Date", "Mayor o igual que periodo_inicio."), ("fecha_pago", "DateTime")],
        "Tabla pago (RF-14, RF-18). Mensualidad de un vehículo: un mes calendario; el periodo nunca es un dato de entrada.")
    asociacion(dom, cliente, "cliente", "1", vehiculo, "vehiculos", "0..*", "posee")
    asociacion(dom, vehiculo, "vehiculo", "1", estancia, "estancias", "0..*", "tiene")
    asociacion(dom, celda, "celda", "1", estancia, "estancias", "0..*", "aloja")
    asociacion(dom, operador, "operadorEntrada", "1", estancia, "estanciasAbiertas", "0..*", "registra entrada")
    asociacion(dom, operador, "operadorSalida", "0..1", estancia, "estanciasCerradas", "0..*", "registra salida")
    asociacion(dom, vehiculo, "vehiculo", "1", pago, "pagos", "0..*", "cubre")
    asociacion(dom, operador, "operador", "1", pago, "pagosRegistrados", "0..*", "registra")
    for origen, destino, nombre in [(vehiculo, tipo_veh, "tipo"), (operador, turno, "turno"), (operador, rol, "rol")]:
        agregar(dom, nodo("UMLDependency", dom, "", source=ref(origen), target=ref(destino), _k=nombre))
    diagrama(dom, "UMLClassDiagram", "Diagrama de clases",
             "Arrastra aquí las 6 clases y las 3 enumeraciones: Cliente, Vehiculo, Celda, Operador, Estancia, Pago; TipoVehiculo, Turno, Rol.", True)

    # -------------------------------------------------------------- Casos de uso
    cu = paquete(modelo, "CasosDeUso", "Actores y casos de uso. CU-nn corresponde a docs/02-historias-de-usuario.md.")
    operador_a = agregar(cu, nodo("UMLActor", cu, "Operador de parqueadero",
                                  documentation="Atiende el acceso. Inicia sesión como operador."))
    admin_a = agregar(cu, nodo("UMLActor", cu, "Administrador de catálogos",
                               documentation="Mantiene operadores, clientes, vehículos y celdas. También inicia sesión como operador."))
    casos = {}
    definiciones = [
        ("CU-01", "Iniciar sesión", "RF-16, HU-14"),
        ("CU-02", "Registrar entrada de vehículo", "RF-03, HU-03. Exige mensualidad vigente."),
        ("CU-03", "Registrar salida de vehículo", "RF-04, HU-04"),
        ("CU-04", "Consultar estado de vehículo", "RF-05, HU-05"),
        ("CU-05", "Corregir celda de la estancia", "RF-11, HU-10"),
        ("CU-06", "Gestionar vehículos", "RF-01, RF-02, RF-13, HU-01, HU-02, HU-11"),
        ("CU-07", "Gestionar celdas", "RF-06, HU-06"),
        ("CU-08", "Consultar celdas disponibles", "RF-10, HU-09"),
        ("CU-09", "Gestionar operadores", "RF-07, HU-07"),
        ("CU-10", "Gestionar clientes", "RF-12, HU-11"),
        ("CU-11", "Registrar mensualidad", "RF-14, RF-18, HU-12, HU-15"),
        ("CU-12", "Consultar vigencia de mensualidad", "RF-14, HU-12"),
        ("CU-13", "Validar mensualidad vigente", "RF-14. Incluido en CU-02."),
        ("CU-14", "Consultar resumen del parqueadero", "RF-15, HU-13"),
        ("CU-15", "Verificar estado de la API", "GET /health"),
        ("CU-16", "Decidir continuidad del periodo", "RF-18, HU-15. Incluido en CU-11 (iteración 3)."),
        ("CU-17", "Renovar sin mover la fecha", "RF-18, HU-15. Pago hasta 5 días tarde: periodo_fin anterior + 1 día."),
        ("CU-18", "Iniciar mensualidad nueva", "RF-18, HU-15. Primer pago, o más de 5 días tarde: periodo desde hoy."),
    ]
    for codigo, nombre, doc in definiciones:
        casos[codigo] = agregar(cu, nodo("UMLUseCase", cu, f"{codigo} {nombre}", documentation=doc))

    def usa(actor: dict, codigos: list[str]) -> None:
        for c in codigos:
            s = agregar(cu, nodo("UMLAssociation", cu, "", _k=f"{actor['name']}-{c}"))
            s["end1"] = nodo("UMLAssociationEnd", s, "", reference=ref(actor), navigable=False, _k="1")
            s["end2"] = nodo("UMLAssociationEnd", s, "", reference=ref(casos[c]), navigable=True, _k="2")

    usa(operador_a, ["CU-01", "CU-02", "CU-03", "CU-04", "CU-05", "CU-08", "CU-11", "CU-12", "CU-14"])
    usa(admin_a, ["CU-01", "CU-06", "CU-07", "CU-08", "CU-09", "CU-10", "CU-14", "CU-15"])
    for origen, destino in [("CU-02", "CU-13"), ("CU-02", "CU-01"), ("CU-03", "CU-01"),
                            ("CU-05", "CU-01"), ("CU-11", "CU-01"), ("CU-11", "CU-16")]:
        agregar(cu, nodo("UMLInclude", cu, "", source=ref(casos[origen]), target=ref(casos[destino]),
                         _k=f"{origen}-{destino}"))
    for origen, destino in [("CU-16", "CU-17"), ("CU-16", "CU-18")]:
        agregar(cu, nodo("UMLExtend", cu, "", source=ref(casos[origen]), target=ref(casos[destino]),
                         _k=f"{origen}-{destino}"))
    diagrama(cu, "UMLUseCaseDiagram", "CU Gestión de usuarios y celdas (iteración 2)",
             "Actores + CU-01, CU-06, CU-07, CU-08, CU-09, CU-10, CU-14.", True)
    diagrama(cu, "UMLUseCaseDiagram", "CU Operación y pagos",
             "Operador + CU-01 a CU-05, CU-11, CU-12, CU-13 (con los include).")
    diagrama(cu, "UMLUseCaseDiagram", "CU Gestión de pagos (iteración 3)",
             "Operador + CU-11, CU-12, CU-16 (incluido en CU-11), CU-17 y CU-18 (extienden a CU-16 según los días desde periodo_fin).")

    # --------------------------------------------------------------- Arquitectura
    arq = paquete(modelo, "Arquitectura", "Componentes principales y su comunicación.")
    c_fe = agregar(arq, nodo("UMLComponent", arq, "Frontend (Angular 22)",
                             documentation="Pantallas standalone; servicios HTTP con ApiService; authGuard e interceptor."))
    c_api = agregar(arq, nodo("UMLComponent", arq, "API (FastAPI)",
                              documentation="routers, services, schemas, models, auth y security."))
    c_db = agregar(arq, nodo("UMLComponent", arq, "Base de datos (PostgreSQL)",
                             documentation="autos_colombia; migraciones Alembic 0001 a 0005."))
    agregar(arq, nodo("UMLDependency", arq, "HTTP JSON", source=ref(c_fe), target=ref(c_api), _k="fe-api"))
    agregar(arq, nodo("UMLDependency", arq, "SQLAlchemy y psycopg", source=ref(c_api), target=ref(c_db), _k="api-db"))
    diagrama(arq, "UMLComponentDiagram", "Arquitectura del sistema", "Tres componentes y dos dependencias.", True)

    comp = paquete(modelo, "Componentes detallados", "Componentes internos del frontend y del backend (iteraciones 1 a 3).")
    pantallas = ["Home", "Login", "ControlAcceso", "Vehiculos", "Celdas", "Operadores", "Clientes", "Mensualidades", "Reportes"]
    fe = {n: agregar(comp, nodo("UMLComponent", comp, f"FE {n}")) for n in pantallas}
    fe_serv = {n: agregar(comp, nodo("UMLComponent", comp, n)) for n in
               ["ApiService", "CeldasService", "OperadoresService", "ClientesService", "EstanciasService", "PagosService", "AuthService"]}
    fe_seg = agregar(comp, nodo("UMLComponent", comp, "authGuard e interceptor"))
    be = {n: agregar(comp, nodo("UMLComponent", comp, f"BE {n}")) for n in
          ["routers", "services", "schemas", "models", "auth y security"]}
    bd = agregar(comp, nodo("UMLComponent", comp, "PostgreSQL"))
    usos = {
        "Vehiculos": ["ApiService", "ClientesService"], "Celdas": ["CeldasService"], "Operadores": ["OperadoresService"],
        "Clientes": ["ClientesService"], "ControlAcceso": ["EstanciasService", "AuthService"],
        "Mensualidades": ["PagosService", "ApiService"], "Reportes": ["PagosService"], "Login": ["AuthService"],
        "Home": ["ApiService"],
    }
    for pantalla, servicios in usos.items():
        for s in servicios:
            agregar(comp, nodo("UMLDependency", comp, "", source=ref(fe[pantalla]), target=ref(fe_serv[s]), _k=f"{pantalla}-{s}"))
    agregar(comp, nodo("UMLDependency", comp, "", source=ref(fe["ControlAcceso"]), target=ref(fe_seg), _k="ca-seg"))
    agregar(comp, nodo("UMLDependency", comp, "", source=ref(fe["Mensualidades"]), target=ref(fe_seg), _k="m-seg"))
    agregar(comp, nodo("UMLDependency", comp, "HTTP JSON", source=ref(fe_serv["ApiService"]), target=ref(be["routers"]), _k="http"))
    for origen, destino in [("routers", "schemas"), ("routers", "services"), ("routers", "auth y security"),
                            ("services", "models"), ("auth y security", "models")]:
        agregar(comp, nodo("UMLDependency", comp, "", source=ref(be[origen]), target=ref(be[destino]), _k=f"{origen}-{destino}"))
    agregar(comp, nodo("UMLDependency", comp, "psycopg", source=ref(be["models"]), target=ref(bd), _k="models-bd"))
    diagrama(comp, "UMLComponentDiagram", "Componentes frontend y backend (iteraciones 1 a 3)",
             "Arrastra todos los componentes de este paquete: las dependencias aparecen solas.")

    # Paquetes de código (referencia de estructura)
    be_pkg = paquete(modelo, "Backend (backend/app)")
    for n in ["routers", "services", "schemas", "models", "database y config", "auth y security"]:
        paquete(be_pkg, n)
    fe_pkg = paquete(modelo, "Frontend (frontend/src/app)")
    for n in ["home", "login", "control-acceso", "vehiculos", "celdas", "operadores", "clientes", "mensualidades",
              "reportes", "services", "models", "guards", "interceptors"]:
        paquete(fe_pkg, n)
    diagrama(modelo, "UMLPackageDiagram", "Paquetes", "Estructura de carpetas del backend y del frontend.")
    return proyecto


def main() -> None:
    texto = json.dumps(construir(), ensure_ascii=False, indent=2)
    SALIDA.write_text(texto + "\n", encoding="utf-8", newline="\n")
    print(f"Escrito {SALIDA} ({len(texto.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
