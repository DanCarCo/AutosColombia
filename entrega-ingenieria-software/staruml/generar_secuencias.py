"""Regenera los diagramas de secuencia de AutosColombia_con_diagramas.mdj (iteraciones 1 a 3).

Uso (solo biblioteca estándar):

    python generar_secuencias.py

Lee los bloques ``sequenceDiagram`` de docs/04-diagramas.md (secciones 4 a 10, la
fuente de verdad de la documentación), reemplaza en AutosColombia_con_diagramas.mdj
las secuencias dibujadas antes (importadas de Mermaid, desactualizadas) y escribe
el archivo en UTF-8. Los ids son deterministas.

Los bloques ``alt``/``else`` se aplanan: cada mensaje de una rama lleva su condición
entre corchetes, p. ej. «[Sin mensualidad vigente] 402 …». Los diagramas se dibujan
con líneas de vida, mensajes y activaciones; no necesitan ajuste manual.
"""

import hashlib
import json
import re
from pathlib import Path

CARPETA = Path(__file__).parent
DOCS = CARPETA.parents[1] / "docs" / "04-diagramas.md"
MDJ = CARPETA / "AutosColombia_con_diagramas.mdj"

# Orden de los bloques sequenceDiagram en docs/04-diagramas.md (secciones 4 a 10)
NOMBRES = [
    "SD Iniciar sesión (RF-16)",
    "SD Registrar entrada de vehículo (RF-03, RF-14)",
    "SD Registrar salida de vehículo (RF-04)",
    "SD Gestionar operadores - crear (RF-07)",
    "SD Gestionar operadores - editar y eliminar (RF-07, RF-17)",
    "SD Gestionar celdas - crear y consultar disponibles (RF-06, RF-10)",
    "SD Gestionar celdas - editar y eliminar (RF-06, RF-17)",
    "SD Registrar mensualidad (RF-14, RF-18, iteración 3)",
    "SD Gestionar clientes (RF-12, RF-13)",
]
ANCHO_MIN, SEPARACION, TOPE_Y, PASO_Y = 130, 60, 130, 40


def _id(clave: str) -> str:
    return "AAAAAA" + hashlib.sha1(clave.encode("utf-8")).hexdigest()[:14] + "="


def ref(n: dict) -> dict:
    return {"$ref": n["_id"]}


def parsear(codigo: str):
    """Devuelve (participantes[(alias, nombre)], mensajes[(origen, destino, texto, respuesta, guarda)])."""
    parts, msgs, guardas = [], [], []
    for linea in codigo.splitlines()[1:]:
        s = linea.strip()
        if not s or s == "autonumber":
            continue
        m = re.match(r"participant\s+(\w+)(?:\s+as\s+(.+))?$", s)
        if m:
            parts.append((m.group(1), (m.group(2) or m.group(1)).strip()))
            continue
        m = re.match(r"alt\s+(.+)$", s)
        if m:
            guardas = [m.group(1).strip()]
            continue
        m = re.match(r"else\s+(.+)$", s)
        if m:
            guardas[-1] = m.group(1).strip()
            continue
        if s == "end":
            guardas = []
            continue
        m = re.match(r"(\w+)(-->>|->>)(\w+):\s*(.+)$", s)
        if m:
            texto = m.group(4).strip()
            if guardas:
                texto = f"[{guardas[-1]}] {texto}"
            msgs.append((m.group(1), m.group(3), texto, m.group(2) == "-->>"))
    return parts, msgs


def construir_secuencia(nombre: str, codigo: str, padre: dict, k: str) -> list[dict]:
    parts, msgs = parsear(codigo)
    colab = {"_type": "UMLCollaboration", "_id": _id(f"{k}/colab"), "_parent": ref(padre),
             "name": f"Colaboración {nombre}", "ownedElements": [], "attributes": []}
    inter = {"_type": "UMLInteraction", "_id": _id(f"{k}/inter"), "_parent": ref(colab),
             "name": f"Interacción {nombre}", "ownedElements": [], "messages": [], "participants": []}
    colab["ownedElements"].append(inter)
    diag = {"_type": "UMLSequenceDiagram", "_id": _id(f"{k}/diag"), "_parent": ref(inter), "name": nombre,
            "ownedViews": [], "showSequenceNumber": True, "showActivation": False}
    inter["ownedElements"].append(diag)

    vidas, linea_x = {}, {}
    x = 30
    propios = sum(1 for m in msgs if m[0] == m[1])
    alto_linea = len(msgs) * PASO_Y + propios * 20 + 90
    for alias, titulo in parts:
        ancho = max(ANCHO_MIN, int(len(titulo) * 7.4) + 30)
        attr = {"_type": "UMLAttribute", "_id": _id(f"{k}/attr/{alias}"), "_parent": ref(colab),
                "name": f"{alias}Role", "type": ""}
        colab["attributes"].append(attr)
        vida = {"_type": "UMLLifeline", "_id": _id(f"{k}/vida/{alias}"), "_parent": ref(inter),
                "name": titulo, "represent": ref(attr), "isMultiInstance": False}
        inter["participants"].append(vida)
        vidas[alias] = vida
        centro = x + ancho // 2
        linea_x[alias] = centro
        vid = _id(f"{k}/vistavida/{alias}")
        cab = _id(f"{k}/cab/{alias}")
        etiqueta = _id(f"{k}/etq/{alias}")
        linea = _id(f"{k}/linea/{alias}")
        oculto = lambda suf, **kw: {"_type": "LabelView", "_id": _id(f"{k}/lbl/{alias}/{suf}"), "_parent": {"$ref": cab},
                                    "visible": False, "font": "Arial;13;0", "parentStyle": True, **kw}
        est, ns, prop = oculto("e", height=13), oculto("n", height=13), oculto("p", height=13, horizontalAlignment=1)
        nombre_lbl = {"_type": "LabelView", "_id": etiqueta, "_parent": {"$ref": cab}, "font": "Arial;13;1",
                      "parentStyle": True, "left": x + 5, "top": 47, "width": ancho - 10, "height": 13, "text": titulo}
        diag["ownedViews"].append({
            "_type": "UMLSeqLifelineView", "_id": vid, "_parent": ref(diag), "model": ref(vida),
            "subViews": [
                {"_type": "UMLNameCompartmentView", "_id": cab, "_parent": {"$ref": vid}, "model": ref(vida),
                 "subViews": [est, nombre_lbl, ns, prop], "font": "Arial;13;0", "parentStyle": True,
                 "left": x, "top": 40, "width": ancho, "height": 40,
                 "stereotypeLabel": {"$ref": est["_id"]}, "nameLabel": {"$ref": etiqueta},
                 "namespaceLabel": {"$ref": ns["_id"]}, "propertyLabel": {"$ref": prop["_id"]}},
                {"_type": "UMLLinePartView", "_id": linea, "_parent": {"$ref": vid}, "model": ref(vida),
                 "font": "Arial;13;0", "parentStyle": False, "left": centro, "top": 81, "width": 1, "height": alto_linea},
            ],
            "font": "Arial;13;0", "parentStyle": False, "left": x, "top": 40, "width": ancho,
            "height": alto_linea + 41, "nameCompartment": {"$ref": cab}, "linePart": {"$ref": linea},
        })
        x += ancho + SEPARACION

    y = TOPE_Y
    for i, (origen, destino, texto, respuesta) in enumerate(msgs):
        if origen not in vidas or destino not in vidas:
            raise ValueError(f"{nombre}: participante desconocido en «{texto}»")
        modelo = {"_type": "UMLMessage", "_id": _id(f"{k}/msg/{i}"), "_parent": ref(inter), "name": texto,
                  "source": ref(vidas[origen]), "target": ref(vidas[destino])}
        if respuesta:
            modelo["messageSort"] = "reply"
        inter["messages"].append(modelo)
        mid = _id(f"{k}/vmsg/{i}")
        lbl = _id(f"{k}/vlbl/{i}")
        xo, xd = linea_x[origen], linea_x[destino]
        if origen == destino:
            puntos = f"{xo + 1}:{y};{xo + 31}:{y};{xo + 31}:{y + 20};{xo + 1}:{y + 20}"
            ancho_lbl, izq = 220, xo + 36
        else:
            puntos = f"{xo + 1}:{y};{xd}:{y}" if xo < xd else f"{xo}:{y};{xd + 1}:{y}"
            ancho_lbl, izq = abs(xd - xo) - 10, min(xo, xd) + 5
        def etiqueta_borde(suf, visible, texto_lbl=None):
            d = {"_type": "EdgeLabelView", "_id": _id(f"{k}/vlbl/{i}/{suf}"), "_parent": {"$ref": mid},
                 "model": ref(modelo), "font": "Arial;13;0", "parentStyle": False, "left": izq, "top": y - 16,
                 "height": 13, "alpha": 1.5707963267948966, "distance": 10, "hostEdge": {"$ref": mid},
                 "edgePosition": 1}
            if not visible:
                d["visible"] = False
            if texto_lbl:
                d["width"], d["text"] = ancho_lbl, texto_lbl
            return d
        nom, est, prop = etiqueta_borde("n", True, texto), etiqueta_borde("e", False), etiqueta_borde("p", False)
        act = {"_type": "UMLActivationView", "_id": _id(f"{k}/vact/{i}"), "_parent": {"$ref": mid},
               "model": ref(modelo), "visible": False, "font": "Arial;13;0", "parentStyle": False,
               "left": xd, "top": y, "width": 14, "height": 40}
        diag["ownedViews"].append({
            "_type": "UMLSeqMessageView", "_id": mid, "_parent": ref(diag), "model": ref(modelo),
            "subViews": [nom, est, prop, act], "font": "Arial;13;0", "parentStyle": False,
            "head": {"$ref": _id(f"{k}/linea/{destino}")}, "tail": {"$ref": _id(f"{k}/linea/{origen}")},
            "points": puntos, "nameLabel": {"$ref": nom["_id"]}, "stereotypeLabel": {"$ref": est["_id"]},
            "propertyLabel": {"$ref": prop["_id"]}, "activation": {"$ref": act["_id"]},
        })
        y += PASO_Y + (20 if origen == destino else 0)
    return [colab]


def main() -> None:
    texto = DOCS.read_text(encoding="utf-8")
    bloques = re.findall(r"```mermaid\n(sequenceDiagram.*?)```", texto, re.S)
    if len(bloques) != len(NOMBRES):
        raise SystemExit(f"Se esperaban {len(NOMBRES)} diagramas de secuencia y hay {len(bloques)} en {DOCS.name}.")
    proyecto = json.loads(MDJ.read_text(encoding="utf-8"))
    # Quita las secuencias antiguas (importadas de Mermaid) y recuerda su paquete padre
    padre = None

    def limpiar(n):
        nonlocal padre
        if isinstance(n, dict):
            for clave in ("ownedElements",):
                if clave in n:
                    quedan = []
                    for e in n[clave]:
                        if isinstance(e, dict) and e.get("_type") == "UMLCollaboration" and (
                                "Mermaid" in e.get("name", "") or e.get("name", "").startswith("Colaboración SD ")):
                            padre = padre or n
                            continue
                        quedan.append(e)
                    n[clave] = quedan
            for v in list(n.values()):
                limpiar(v)
        elif isinstance(n, list):
            for v in n:
                limpiar(v)

    limpiar(proyecto)
    if padre is None:
        raise SystemExit("No se encontró el paquete que contenía las secuencias anteriores.")
    for i, (nombre, codigo) in enumerate(zip(NOMBRES, bloques)):
        padre["ownedElements"].extend(construir_secuencia(nombre, codigo, padre, f"sec{i}"))
    MDJ.write_text(json.dumps(proyecto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Escrito {MDJ.name}: {len(NOMBRES)} diagramas de secuencia en «{padre.get('name')}».")


if __name__ == "__main__":
    main()
