"""Dibuja en AutosColombia_con_diagramas.mdj los diagramas de la iteración 3 (pagos).

Uso (solo biblioteca estándar; repetible):

    python generar_diagramas.py

- «CU Gestión de pagos (iteración 3)»: Operador y Administrador con CU-11, CU-12, CU-19 (movimientos de pago,
  RF-19), CU-16 (decidir continuidad, incluido en CU-11) y CU-17 / CU-18 (extienden a CU-16).
- «Componentes frontend y backend (iteraciones 1 a 3)»: el diagrama de componentes anterior (1 y 2) ampliado con
  las pantallas FE Movimientos y FE RegistrarPago y sus dependencias.

Las vistas nuevas se clonan de las ya dibujadas en el mismo archivo (mismo estilo) con ids deterministas.
"""

import copy
import hashlib
import json
import math
from pathlib import Path

MDJ = Path(__file__).with_name("AutosColombia_con_diagramas.mdj")
NOMBRE_CU = "CU Gestión de pagos (iteración 3)"
NOMBRE_COMP_ANTIGUO = "Componentes frontend y backend (iteraciones 1 y 2)"
NOMBRE_COMP = "Componentes frontend y backend (iteraciones 1 a 3)"

NUEVOS_CU = [
    ("CU-16", "Decidir continuidad del periodo", "RF-18, HU-15. Incluido en CU-11 (iteración 3)."),
    ("CU-17", "Renovar sin mover la fecha", "RF-18, HU-15. Pago hasta 5 días tarde: periodo_fin anterior + 1 día. Extiende CU-16."),
    ("CU-18", "Iniciar mensualidad nueva", "RF-18, HU-15. Primer pago, o más de 5 días tarde: periodo desde hoy. Extiende CU-16."),
    ("CU-19", "Consultar movimientos de pago", "RF-19, HU-16. Historial con totales, filtros y exportación a CSV."),
]


def _id(clave: str) -> str:
    return "AAAAAA" + hashlib.sha1(clave.encode("utf-8")).hexdigest()[:14] + "="


def ref(e: dict) -> dict:
    return {"$ref": e["_id"]}


class Modelo:
    def __init__(self, raiz: dict) -> None:
        self.raiz = raiz
        self.idx: dict[str, dict] = {}
        self._reg(raiz)

    def _reg(self, n) -> None:
        if isinstance(n, dict):
            if "_id" in n:
                self.idx[n["_id"]] = n
            for v in n.values():
                self._reg(v)
        elif isinstance(n, list):
            for v in n:
                self._reg(v)

    def buscar(self, tipo: str, nombre: str | None = None, prefijo: str | None = None) -> dict | None:
        for e in self.idx.values():
            if e.get("_type") != tipo:
                continue
            if nombre is not None and e.get("name") != nombre:
                continue
            if prefijo is not None and not str(e.get("name", "")).startswith(prefijo):
                continue
            return e
        return None

    def nuevo(self, tipo: str, padre: dict, nombre: str, clave: str, campo: str = "ownedElements", **extra) -> dict:
        e = {"_type": tipo, "_id": _id(clave), "_parent": ref(padre)}
        if nombre:
            e["name"] = nombre
        e.update(extra)
        padre.setdefault(campo, []).append(e)
        self.idx[e["_id"]] = e
        return e

    def quitar(self, e: dict) -> None:
        padre = self.idx[e["_parent"]["$ref"]]
        for campo in ("ownedElements", "ownedViews"):
            if campo in padre and e in padre[campo]:
                padre[campo].remove(e)


def recortar(centro_a, tam_a, centro_b, tam_b):
    """Puntos de borde de dos rectángulos sobre la recta que une sus centros."""
    def borde(c, t, hacia):
        dx, dy = hacia[0] - c[0], hacia[1] - c[1]
        if dx == 0 and dy == 0:
            return c
        escala = min((t[0] / 2) / abs(dx) if dx else math.inf, (t[1] / 2) / abs(dy) if dy else math.inf)
        return (c[0] + dx * escala, c[1] + dy * escala)
    a, b = borde(centro_a, tam_a, centro_b), borde(centro_b, tam_b, centro_a)
    return f"{round(a[0])}:{round(a[1])};{round(b[0])}:{round(b[1])}"


def clonar(vista: dict, clave: str, modelo_nuevo: dict, nueva_pos: dict, extra_modelos: dict[str, str] | None = None) -> dict:
    """Copia una vista con ids nuevos y la apunta a otro elemento del modelo."""
    copia = copy.deepcopy(vista)
    antiguos: list[str] = []

    def recoger(n):
        if isinstance(n, dict):
            if "_id" in n:
                antiguos.append(n["_id"])
            for v in n.values():
                recoger(v)
        elif isinstance(n, list):
            for v in n:
                recoger(v)

    recoger(copia)
    mapa = {a: _id(f"{clave}/{a}") for a in antiguos}
    mapa[vista["model"]["$ref"]] = modelo_nuevo["_id"]
    mapa.update(extra_modelos or {})

    def reemplazar(n):
        if isinstance(n, dict):
            if "_id" in n and n["_id"] in mapa:
                n["_id"] = mapa[n["_id"]]
            if "$ref" in n and n["$ref"] in mapa:
                n["$ref"] = mapa[n["$ref"]]
            for v in n.values():
                reemplazar(v)
        elif isinstance(n, list):
            for v in n:
                reemplazar(v)

    reemplazar(copia)
    dx = nueva_pos.get("left", copia.get("left", 0)) - copia.get("left", 0) if "left" in copia else 0
    dy = nueva_pos.get("top", copia.get("top", 0)) - copia.get("top", 0) if "top" in copia else 0

    def mover(n, raiz=False):
        if isinstance(n, dict):
            if not raiz:
                if "left" in n:
                    n["left"] += dx
                if "top" in n:
                    n["top"] += dy
            for v in n.get("subViews", []):
                mover(v)
    mover(copia, raiz=True)
    for k in ("left", "top"):
        if k in copia:
            copia[k] += dx if k == "left" else dy
    return copia


def _etiqueta_nombre(vista: dict):
    for sv in vista.get("subViews", []):
        if sv["_type"] == "UMLNameCompartmentView":
            for lbl in sv["subViews"]:
                if lbl.get("font", "").endswith(";1"):
                    return sv, lbl
    raise ValueError("vista sin etiqueta de nombre")


def poner_texto(vista: dict, texto: str) -> None:
    _etiqueta_nombre(vista)[1]["text"] = texto


def ajustar_ancho(vista: dict, ancho: float) -> None:
    """Fija el ancho de una vista de nodo y recentra su compartimento y etiqueta de nombre."""
    vista["width"] = ancho
    comp, lbl = _etiqueta_nombre(vista)
    comp["width"], comp["left"] = ancho - 20, vista["left"] + 10
    lbl["width"], lbl["left"] = ancho - 30, vista["left"] + 15


def centro(v):
    return (v["left"] + v["width"] / 2, v["top"] + v["height"] / 2), (v["width"], v["height"])


def dibujar_cu(m: Modelo) -> str:
    pkg = m.buscar("UMLPackage", "CasosDeUso")
    operador = m.buscar("UMLActor", "Operador de parqueadero")
    admin = m.buscar("UMLActor", "Administrador de catálogos")
    ucs: dict[str, dict] = {}
    for e in m.idx.values():
        if e.get("_type") == "UMLUseCase" and str(e.get("name", "")).startswith("CU-"):
            ucs[e["name"][:5]] = e
    for codigo, nombre, doc in NUEVOS_CU:
        if codigo not in ucs:
            ucs[codigo] = m.nuevo("UMLUseCase", pkg, f"{codigo} {nombre}", f"cu/{codigo}", documentation=doc)

    def asociar(actor: dict, codigo: str) -> dict:
        for e in list(m.idx.values()):
            if e.get("_type") == "UMLAssociation" and e.get("end1", {}).get("reference", {}).get("$ref") == actor["_id"] \
                    and e.get("end2", {}).get("reference", {}).get("$ref") == ucs[codigo]["_id"]:
                return e
        a = m.nuevo("UMLAssociation", pkg, "", f"cu/as/{actor['name']}/{codigo}")
        a["end1"] = {"_type": "UMLAssociationEnd", "_id": _id(f"cu/as/{actor['name']}/{codigo}/1"), "_parent": ref(a),
                     "reference": ref(actor), "navigable": False}
        a["end2"] = {"_type": "UMLAssociationEnd", "_id": _id(f"cu/as/{actor['name']}/{codigo}/2"), "_parent": ref(a),
                     "reference": ref(ucs[codigo]), "navigable": True}
        m.idx[a["end1"]["_id"]], m.idx[a["end2"]["_id"]] = a["end1"], a["end2"]
        return a

    def relacion(tipo: str, origen: str, destino: str) -> dict:
        for e in m.idx.values():
            if e.get("_type") == tipo and e.get("source", {}).get("$ref") == ucs[origen]["_id"] \
                    and e.get("target", {}).get("$ref") == ucs[destino]["_id"]:
                return e
        return m.nuevo(tipo, pkg, "", f"cu/{tipo}/{origen}/{destino}", source=ref(ucs[origen]), target=ref(ucs[destino]))

    pares = [(operador, c) for c in ("CU-11", "CU-12", "CU-19")] + [(admin, c) for c in ("CU-11", "CU-12", "CU-19")]
    asocs = [(a, c, asociar(a, c)) for a, c in pares]
    inc = relacion("UMLInclude", "CU-11", "CU-16")
    ext = [relacion("UMLExtend", "CU-17", "CU-16"), relacion("UMLExtend", "CU-18", "CU-16")]

    # plantillas de vistas (diagrama «CU Operación y pagos», ya dibujado)
    base = m.buscar("UMLUseCaseDiagram", "CU Operación y pagos")
    plantilla = {}
    for v in base["ownedViews"]:
        plantilla.setdefault(v["_type"], v)
    for viejo in [e for e in m.idx.values() if e.get("_type") == "UMLUseCaseDiagram" and e.get("name") == NOMBRE_CU]:
        m.quitar(viejo)
    diag = m.nuevo("UMLUseCaseDiagram", pkg, NOMBRE_CU, "cu/diag", campo="ownedElements", model=ref(pkg),
                   documentation="Operador y Administrador + CU-11, CU-12, CU-19, CU-16 (incluido en CU-11), "
                                 "CU-17 y CU-18 (extienden a CU-16 según los días desde periodo_fin).",
                   ownedViews=[])
    vistas: dict[str, dict] = {}

    def nodo(clave: str, tipo_plantilla: str, modelo: dict, left: float, top: float, texto: str, ancho: float | None = None):
        v = clonar(plantilla[tipo_plantilla], f"cu/v/{clave}", modelo, {"left": left, "top": top})
        v["_parent"] = ref(diag)
        v["left"], v["top"] = left, top
        poner_texto(v, texto)
        if ancho:
            ajustar_ancho(v, ancho)
        diag["ownedViews"].append(v)
        vistas[clave] = v
        return v

    nodo("op", "UMLActorView", operador, 40, 90, "Operador de parqueadero")
    nodo("ad", "UMLActorView", admin, 40, 320, "Administrador de catálogos")
    pos = {"CU-11": (330, 40), "CU-12": (330, 150), "CU-19": (330, 260), "CU-16": (760, 40), "CU-17": (640, 190), "CU-18": (980, 190)}
    for codigo, (x, y) in pos.items():
        texto = ucs[codigo]["name"]
        nodo(codigo, "UMLUseCaseView", ucs[codigo], x, y, texto, ancho=max(190, len(texto) * 7.3 + 40))

    def arista(clave: str, tipo_plantilla: str, modelo: dict, origen: str, destino: str, texto: str | None = None,
               tipo_vista: str | None = None, extra: dict | None = None):
        a, b = vistas[origen], vistas[destino]
        v = clonar(plantilla[tipo_plantilla], f"cu/v/{clave}", modelo, {}, extra)
        v["_parent"] = ref(diag)
        if tipo_vista:
            v["_type"] = tipo_vista
        v["tail"], v["head"] = ref(a), ref(b)
        (ca, ta), (cb, tb) = centro(a), centro(b)
        v["points"] = recortar(ca, ta, cb, tb)
        medio = ((ca[0] + cb[0]) / 2, (ca[1] + cb[1]) / 2)
        for sv in v.get("subViews", []):
            if sv["_type"] == "EdgeLabelView":
                sv["left"], sv["top"] = round(medio[0]), round(medio[1] - 16)
                if texto and sv.get("visible") is not False:
                    sv["text"] = texto
        diag["ownedViews"].append(v)

    tpl_assoc = plantilla["UMLAssociationView"]
    assoc_old = m.idx[tpl_assoc["model"]["$ref"]]
    for actor, codigo, a in asocs:
        extra = {assoc_old["end1"]["_id"]: a["end1"]["_id"], assoc_old["end2"]["_id"]: a["end2"]["_id"]}
        arista(f"as/{actor['name']}/{codigo}", "UMLAssociationView", a, "op" if actor is operador else "ad", codigo, extra=extra)
    arista("inc", "UMLIncludeView", inc, "CU-11", "CU-16", "«include»")
    arista("ext17", "UMLIncludeView", ext[0], "CU-17", "CU-16", "«extend»", tipo_vista="UMLExtendView")
    arista("ext18", "UMLIncludeView", ext[1], "CU-18", "CU-16", "«extend»", tipo_vista="UMLExtendView")
    return f"{NOMBRE_CU}: {len(diag['ownedViews'])} vistas"


def dibujar_componentes(m: Modelo) -> str:
    diag = m.buscar("UMLComponentDiagram", NOMBRE_COMP_ANTIGUO) or m.buscar("UMLComponentDiagram", NOMBRE_COMP)
    pkg = m.idx[diag["_parent"]["$ref"]]
    diag["name"] = NOMBRE_COMP
    diag["documentation"] = "Componentes internos del frontend y del backend (iteraciones 1 a 3), con las pantallas de pagos."
    comp = {e["name"]: e for e in m.idx.values() if e.get("_type") == "UMLComponent" and e.get("_parent", {}).get("$ref") == pkg["_id"]}
    por_modelo = {v["model"]["$ref"]: v for v in diag["ownedViews"] if v["_type"] == "UMLComponentView"}
    vista_de = lambda nombre: por_modelo[comp[nombre]["_id"]]
    plantilla_comp = vista_de("FE Mensualidades")
    plantilla_dep = next(v for v in diag["ownedViews"] if v["_type"] == "UMLDependencyView")

    nuevos = {"FE Movimientos": (30, 786, 190), "FE RegistrarPago": (30, 870, 200)}
    dependencias = {
        "FE Movimientos": ["PagosService", "ApiService", "ClientesService", "authGuard e interceptor"],
        "FE RegistrarPago": ["PagosService", "ApiService", "ClientesService", "AuthService", "authGuard e interceptor"],
    }
    creadas = 0
    for nombre, (x, y, ancho) in nuevos.items():
        if nombre not in comp:
            comp[nombre] = m.nuevo("UMLComponent", pkg, nombre, f"comp/{nombre}")
        if comp[nombre]["_id"] not in por_modelo:
            v = clonar(plantilla_comp, f"comp/v/{nombre}", comp[nombre], {"left": x, "top": y})
            v["_parent"] = ref(diag)
            v["left"], v["top"] = x, y
            poner_texto(v, nombre)
            ajustar_ancho(v, ancho)
            diag["ownedViews"].append(v)
            por_modelo[comp[nombre]["_id"]] = v
            creadas += 1
        for destino in dependencias[nombre]:
            existe = any(e.get("_type") == "UMLDependency" and e.get("source", {}).get("$ref") == comp[nombre]["_id"]
                         and e.get("target", {}).get("$ref") == comp[destino]["_id"] for e in m.idx.values())
            if existe:
                continue
            dep = m.nuevo("UMLDependency", pkg, "", f"comp/dep/{nombre}/{destino}",
                          source=ref(comp[nombre]), target=ref(comp[destino]))
            o, d = vista_de(nombre), vista_de(destino)
            v = clonar(plantilla_dep, f"comp/vdep/{nombre}/{destino}", dep, {})
            v["_parent"] = ref(diag)
            v["tail"], v["head"] = ref(o), ref(d)
            (ca, ta), (cb, tb) = centro(o), centro(d)
            v["points"] = recortar(ca, ta, cb, tb)
            diag["ownedViews"].append(v)
    return f"{NOMBRE_COMP}: {len(diag['ownedViews'])} vistas ({creadas} componentes nuevos)"


def main() -> None:
    raiz = json.loads(MDJ.read_text(encoding="utf-8"))
    m = Modelo(raiz)
    print(dibujar_cu(m))
    print(dibujar_componentes(m))
    MDJ.write_text(json.dumps(raiz, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
