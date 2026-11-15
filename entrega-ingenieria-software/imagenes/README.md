# Imágenes de la entrega

| Carpeta | Contenido | Origen |
| --- | --- | --- |
| `figma/` | 12 marcos de los mockups (1440 × 900 px): inicio de sesión, operadores, celdas, clientes, corregir celda y entrada sin mensualidad | Exportados del archivo de Figma el 14/11/2026, ya con las correcciones |
| `staruml/` | 12 imágenes UML: 2 de casos de uso, 1 de clases, 7 de secuencia y 2 de componentes | Dibujadas y exportadas con StarUML 7 (modelo `../staruml/AutosColombia_con_diagramas.mdj`), con fondo blanco |
| `diagramas-mermaid/` | Los mismos 11 diagramas en versión limpia | Renderizados desde el código Mermaid de `docs/04-diagramas.md` |

## Notas

- Las imágenes de `staruml/` llevan la marca de agua **«UNREGISTERED»** porque StarUML se usó en versión de prueba
  (actividad educativa). Con una licencia se pueden volver a exportar sin ella: abrir
  `AutosColombia_con_diagramas.mdj` y usar *File ▸ Export All Diagrams As ▸ PNG*.
- En los diagramas de secuencia, las condiciones de las alternativas (`alt` / `else` del Mermaid) van entre corchetes al
  inicio del mensaje, por ejemplo «[Sin mensualidad vigente] 402 …».
- `diagramas-mermaid/` sirve de respaldo sin marca de agua. Sus diagramas de casos de uso y componentes son diagramas de
  flujo, no UML estricto.
