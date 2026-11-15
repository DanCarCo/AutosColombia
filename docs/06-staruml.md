# Modelo de StarUML

Archivo: [`entrega-ingenieria-software/staruml/AutosColombia.mdj`](../entrega-ingenieria-software/staruml/AutosColombia.mdj)

## Qué contiene

El archivo se regenera con
[`generar_mdj.py`](../entrega-ingenieria-software/staruml/generar_mdj.py)
(solo biblioteca estándar de Python). Cambios frente a la versión anterior:

| Cambio | Motivo |
| --- | --- |
| Se añadieron las clases **Cliente** y **Pago** y sus asociaciones (Cliente–Vehiculo, Vehiculo–Pago, Operador–Pago). | Retroalimentación: el diagrama de clases debía incluirlos. |
| `Vehiculo` ahora tiene `cliente_id`; `Operador` tiene `usuario`, `password_hash` y `turno`; se añadió la enumeración **Turno**. | Coinciden con `backend/app/models.py` y la migración `0003`. |
| `Vehiculo.modelo` documenta el rango **1900–2200**. | Migración `0004`. |
| Casos de uso ampliados a **CU-01 a CU-15** (inicio de sesión, clientes, mensualidad, validación de mensualidad, celdas disponibles, corrección de celda, resumen) con `«include»`. | Retroalimentación: los casos de uso debían representar clientes, pago y validación de mensualidad. |
| Nuevo paquete **Componentes detallados** con las pantallas, los servicios y las capas del backend. | Entregable F. |
| Se corrigió la codificación del texto (tildes y eñes). | La versión anterior tenía caracteres dañados (`�`). |

Los diagramas que trae son **contenedores con nombre**; el contenido se dibuja
en un par de minutos arrastrando elementos (abajo). **Verificado el 14/11/2026 en
StarUML 7 (modo de prueba):** el archivo abre sin errores, las tildes se ven bien y
los diagramas aparecen en *Working Diagrams*. Además se comprobó que el JSON es válido,
que los ids son únicos y que todas las referencias existen.

## Abrir y dibujar

1. StarUML → **File ▸ Open** → `AutosColombia.mdj`.
2. En el **Model Explorer** (panel derecho) hay cinco paquetes. Abre el diagrama indicado (doble clic) y **arrastra** los elementos desde el árbol al lienzo. StarUML dibuja solo las relaciones entre elementos soltados.
3. Acomoda con **Format ▸ Auto Layout** (o a mano) y exporta.

| Entregable | Diagrama | Qué arrastrar |
| --- | --- | --- |
| Clases (retroalimentación) | `Dominio ▸ Diagrama de clases` | Las 6 clases y las 2 enumeraciones |
| B — casos de uso | `CasosDeUso ▸ CU Gestión de usuarios y celdas (iteración 2)` | Los 2 actores y CU-01, 06, 07, 08, 09, 10, 14 |
| B — casos de uso | `CasosDeUso ▸ CU Operación y pagos` | Actor Operador y CU-01 a CU-05, 11, 12, 13 |
| F — componentes | `Arquitectura ▸ Arquitectura del sistema` | Los 3 componentes |
| F — componentes | `Componentes detallados ▸ Componentes frontend y backend` | Todos los componentes del paquete |
| E — secuencia | Crear 7 diagramas en `Dominio` (o un paquete nuevo) | Ver [04-diagramas.md](04-diagramas.md), secciones 4 a 10 |

### Diagramas de secuencia (entregable E)

StarUML 7 genera el diagrama desde código Mermaid, sin dibujar mensaje por mensaje:

1. **Tools ▸ Generate Diagram by Mermaid…**
2. Pega el contenido de uno de los bloques `sequenceDiagram` de [04-diagramas.md](04-diagramas.md) (secciones 4 a 10), sin las líneas de las comillas invertidas.
3. Acepta: se crea un diagrama de secuencia con sus lifelines, mensajes y bloques `alt`.
4. Renómbralo (por ejemplo «SD Registrar entrada de vehículo») y acomoda si hace falta.

Esa importación no admite `actor`: el operador aparece como lifeline normal; si quieres el muñeco, cámbialo después a **Actor** en las propiedades.
Por el mismo camino puedes generar el diagrama de clases desde la sección 3, pero crearía clases duplicadas;
es mejor arrastrar las del modelo.

## Exportar las imágenes para el PDF

**File ▸ Export Diagram As ▸ PNG** (uno) o **File ▸ Export All Diagrams As ▸ PNG** (todos), en la carpeta
`entrega-ingenieria-software/diagramas/`. Usa nombres como `CU_GestionUsuariosCeldas.png`,
`CLASES_AutosColombia.png`, `SEC_RegistrarEntrada.png`, `COMP_Arquitectura.png`.

## Diagramas ya dibujados y exportados

`entrega-ingenieria-software/staruml/AutosColombia_con_diagramas.mdj` es el modelo anterior con **todos los diagramas
dibujados** (13: clases, 2 de casos de uso, 7 de secuencia, 2 de componentes y el de paquetes, que sigue vacío).
Las imágenes exportadas están en `entrega-ingenieria-software/imagenes/staruml/`. Se usó StarUML 7 en **versión de
prueba**, así que las imágenes llevan la marca «UNREGISTERED»; es aceptable para esta actividad educativa y con una
licencia se re-exportan sin ella.

Cómo se generaron (por si hay que repetirlo): StarUML 7 incluye una consola de scripts (QuickJS) que se ejecuta al
arrancar con la variable de entorno `STARUML_COMMANDS` (comandos separados por coma, por ejemplo
`script-console:run@codigo.json,project:save-as@ruta.json`). Con la API (`app.factory.createViewAndRelationships`,
`app.commands.execute('project:export-diagram-to-png', {path})`) se crean las vistas y se exporta cada diagrama.
Detalles que costó descubrir: las vistas nuevas miden 0 × 0 hasta que se dibujan, por lo que hay que asignar tamaños
aproximados para que la exportación no recorte; los diagramas de secuencia se importan con
`mermaid:generate-diagram` (`{code: ...}`), pero hay que recolocar líneas de vida y mensajes (`view.points = new
type.Points()`); y los archivos JSON de los comandos deben llevar los acentos escapados (`ó`).

## Regenerar el archivo

```powershell
Push-Location entrega-ingenieria-software\staruml
python generar_mdj.py
Pop-Location
```

Editar el modelo en StarUML y guardar sobrescribe el `.mdj`; si lo regeneras después,
perderás esos cambios. Elige una de las dos vías: o editas en StarUML, o cambias el script.

## Otros diagramas del repositorio

`entrega-ingenieria-software/diagramas/` conserva `MER_AutosColombia.png`,
`MR_AutosColombia.png` y `MF_AutosColombia.png` (modelos entidad-relación, relacional y físico).
El modelo físico ya incluye `cliente`, `pago` y el CHECK `modelo` 1900..2200 (revisado el 14/11/2026);
no necesita rehacerse. Inclúyelo en el PDF junto a los diagramas de StarUML.
