# Mockups — Figma

Archivo: <https://www.figma.com/design/Vc0HYpxToLRUKwBl8FLhTl/Historias-de-usuario-asociadas-AutosColombia?node-id=0-1>

Revisado y corregido el 14/11/2026 (todos los marcos, con el conector de Figma). Los mockups
ya describen el sistema que se implementó: parqueadero **por mensualidad**, sin cobro por minuto,
con los campos reales de cada formulario.

> **Antes de entregar:** la página **«Respaldo antes de correcciones»** es una copia de seguridad
> de cómo estaba el archivo antes de editar. Bórrala cuando confirmes que los marcos nuevos te
> convencen (clic derecho sobre la página ▸ *Delete page*), para que el docente solo vea la versión final.

## Marcos y su historia

| Marcos | Pantalla | Historia | En la aplicación |
| --- | --- | --- | --- |
| 41 | **Inicio de sesión** (nuevo) | HU-14 | `/login` |
| 01 | Inicio / Resumen operativo | — | `/` |
| 02–06 | Vehículos: listado, nuevo, editar, detalle, confirmar eliminación | HU-01, HU-02, HU-11 | `/gestion/vehiculos` |
| 07–09 | Celdas: listado, nueva, editar | HU-06, HU-09 | `/gestion/celdas` |
| 10–12 | Operadores: listado, nuevo, editar | HU-07 | `/gestion/operadores` |
| 14–16, 17 | Control de acceso: entrada, consulta, salida, salida confirmada | HU-03, HU-04, HU-05 | `/control-acceso` |
| 18 | Entrada rechazada: vehículo ya dentro | HU-03 | `/control-acceso` (409) |
| 43 | **Entrada rechazada: sin mensualidad** (nuevo) | HU-03, HU-12 | `/control-acceso` (402) |
| 42 | **Corregir celda** (nuevo) | HU-10 | `/control-acceso` |
| 21–24 | Clientes: listado, nuevo, editar, detalle | HU-11 | `/gestion/clientes` |
| 27–29 | Mensualidades: listado, nueva, renovar | HU-12, HU-15 | `/gestion/mensualidades` |
| 30 | Reportes / Resumen | HU-13 | `/reportes` |
| 36–37 | Estados: sin resultados, validación y guardado | HU-01 a HU-12 | Mensajes de error y estados vacíos |
| 38–40 | Sistema visual (colores, botones, campos, tablas) | — | Tema de la aplicación |

## Qué se corrigió

| Tema | Antes | Ahora |
| --- | --- | --- |
| Modelo de cobro | Tarifa por minuto ($100), tolerancia de 5 min, cobro y comprobante de pago al salir | Mensualidad: la entrada exige mensualidad vigente; la salida solo cierra la estancia y libera la celda, sin cobro |
| Precios | Planes de $280.000 / $140.000 / $180.000 | Tarifa fija por tipo: Moto $100.000; Automóvil y Camioneta $250.000; el servidor calcula el monto |
| Mensualidades | Planes, celda fija, pago inicial, medio de pago, referencia, saldos | Pago en efectivo por vehículo; el servidor calcula monto y periodo (RF-18, iteración 3; sin selector de fecha); un pago hasta 5 días después de vencida la mensualidad la renueva sin mover la fecha; sin saldos. «Editar o renovar» pasó a **Renovar**. Actualizado el 22/11/2026 (marcos 28 y 29) |
| Operadores | Documento, correo, rol, estado, turnos por horario | Nombre, teléfono, usuario, contraseña (opcional al editar), turno **DIA / NOCHE** y rol **ADMINISTRADOR / OPERADOR** (RF-17) |
| Clientes | Tipo de cliente, tipo de documento, email, dirección, vehículos vinculados, observaciones | Nombre, documento y teléfono |
| Vehículos | Modelo / línea libre, notas, tipo «Carro» | Modelo = **año 1900–2200**, sin notas, tipos Automóvil / Moto / Camioneta |
| Celdas | Zona, tarifa, mantenimiento, estado inicial, observaciones; 24 celdas | Código y tipo; 80 celdas (10 MOTO y 70 CARRO) |
| Reporte | Ocupación, ingresos, operadores, filtros y exportaciones | Resumen: celdas disponibles, celdas totales y clientes registrados |
| Cabecera y menú lateral | Selector de sede «Parqueadero Centro», «Medellín», rol «Administrador» fijo | «Autos Colombia», turno y rol real de la sesión (ADMINISTRADOR / OPERADOR, RF-17); sin selector de sede ni de rol — el rol lo asigna quien crea la cuenta, no se elige al navegar |
| Estado del vehículo | «En parqueadero» / «Finalizado» | «Dentro» / «Fuera» |
| Faltaban | Inicio de sesión, corregir celda, rechazo por falta de mensualidad | Marcos 41, 42 y 43 |

## Marcos que son propuesta futura

El sistema **no** implementa estas pantallas. Siguen en el archivo con la etiqueta
**«PROPUESTA FUTURA · no implementada»** y el sufijo en el nombre del marco, para que se lean
como diseño de siguientes iteraciones y no como funcionalidad hecha:

| Marco | Contenido |
| --- | --- |
| 13 | Roles y permisos (editor de permisos; los dos roles fijos ya existen, el editor no) |
| 19–20 | Mapa de celdas |
| 25–26 | Pagos: movimientos y registrar pago (cobro con medios de pago) |
| 31–32 | Reportes de ocupación e ingresos |
| 33–35 | Configuración: general, tarifas por minuto y reglas operativas |

El marco **«01 - Inicio (versión anterior)»** es un borrador previo; conviene eliminarlo o dejarlo fuera del PDF.

## Pendiente: campo Rol en los formularios de Operadores

Los marcos 11 y 12 (Nuevo operador / Editar operador) no incluían el campo **Rol**
(ADMINISTRADOR / OPERADOR) cuando se implementó RF-17 — el mockup quedó
desactualizado respecto al formulario real, que sí lo exige.

- **Marco 11 (Nuevo operador): corregido.** Ya incluye el campo «Rol *» junto a
  Usuario, coherente con el resto del formulario.
- **Marco 12 (Editar operador): pendiente.** Todavía no muestra el campo Rol;
  hay que agregarlo en Figma (junto a Usuario, igual que en el marco 11) y
  volver a exportarlo.

## Diferencias que se mantienen (decisión consciente)

- El **menú lateral** conserva las entradas «Mapa de celdas», «Pagos» y «Configuración», porque corresponden a los marcos de propuesta futura. La aplicación no las tiene.
- El marco 01 conserva el gráfico «Ocupación por hora», la tarjeta «Movimientos del turno» y el acceso «Ver mapa de celdas»: son ilustrativos y no existen en la aplicación.
- Los códigos de celda `A-12`, `B-03`… son válidos (el código es texto libre); el sistema inicia con `MOTO-01…` y `CARRO-001…`.
- Los datos de ejemplo (placas, nombres, fechas del 24 oct 2026) son ficticios.

## Para el PDF

1. Exporta cada marco usado como PNG (clic derecho ▸ *Copy/Export as ▸ PNG*) y rotúlalo con su historia.
2. Mínimo recomendado para el entregable D: 41, 10–12 (operadores), 07–09 (celdas), 21–23 (clientes), 42 y 43.
3. Confirma que el enlace tenga permiso «Cualquiera con el enlace puede ver».
