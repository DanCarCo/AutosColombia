# Requerimientos — Autos Colombia

Parqueadero que presta el servicio **por mensualidad**. El sistema registra
entradas y salidas de vehículos, usuarios (operadores y clientes), celdas y pagos.

> **Estado de este documento:** todos los requerimientos listados están
> **implementados y verificados** en el código (ver columna *Evidencia* y
> [05-plan-de-pruebas.md](05-plan-de-pruebas.md)). Lo único pendiente se
> declara de forma explícita en la sección [Alcance no cubierto](#alcance-no-cubierto).

## Iteraciones

| Iteración | Alcance |
| --- | --- |
| **1** | Gestión de la entrada y salida de vehículos (vehículos, estancias, consulta de estado). |
| **2** | Gestión de usuarios (operadores, clientes, inicio de sesión) y gestión de celdas. Incluye el registro básico de pagos (mensualidades) y reportes, porque la entrada depende de la mensualidad. |
| **3** | Gestión de pagos: registro del pago en efectivo y continuidad del periodo de la mensualidad. Un pago hasta 5 días después de vencida la renueva sin mover la fecha; pasado ese margen (o en el primer pago) empieza una mensualidad nueva desde hoy. La fecha solo se mueve por cancelación y un nuevo contrato. |

## Requerimientos funcionales

| Id | Iteración | Requerimiento | Evidencia (API / pantalla) |
| --- | --- | --- | --- |
| RF-01 | 1 | Registrar un vehículo con placa única (normalizada a mayúsculas), color, marca, modelo (año **1900–2200**), tipo (MOTO, AUTOMOVIL, CAMIONETA) y cliente dueño. | `POST /vehiculos` · `/gestion/vehiculos` |
| RF-02 | 1 | Consultar (listado paginado y por id), editar y eliminar vehículos. No se elimina un vehículo con estancias o pagos. | `GET/PATCH/DELETE /vehiculos` · `/gestion/vehiculos` |
| RF-03 | 1 | Registrar la **entrada** de un vehículo a una celda. Rechaza vehículo ya dentro (409), celda ocupada (409) y vehículo sin mensualidad vigente (402). | `POST /estancias/entrada` · `/control-acceso` |
| RF-04 | 1 | Registrar la **salida** de un vehículo y liberar su celda. | `POST /estancias/salida` · `/control-acceso` |
| RF-05 | 1 | Consultar el estado de un vehículo por placa: *dentro* (con celda y fecha de entrada), *fuera* o *no registrado*. | `GET /estancias/vehiculo/{placa}` · `/control-acceso` |
| RF-06 | 2 | Gestionar **celdas** (crear, listar paginado, consultar, editar, eliminar). El código es único y se normaliza a mayúsculas; el tipo es obligatorio. | `/celdas` · `/gestion/celdas` |
| RF-07 | 2 | Gestionar **operadores**: nombre, teléfono, usuario único, contraseña (se guarda como hash, nunca en claro), turno DIA o NOCHE y **rol** ADMINISTRADOR u OPERADOR. Solo el administrador gestiona cuentas. | `/operadores` · `/gestion/operadores` |
| RF-08 | 1–2 | Validar los datos de entrada: textos no vacíos, año en rango, tipos permitidos, sin campos desconocidos. Respuestas 422 con mensaje. | Esquemas Pydantic y restricciones CHECK |
| RF-09 | 1–2 | Mantener la integridad referencial: no se borran celdas, vehículos, clientes u operadores con registros relacionados (409). | Claves foráneas `RESTRICT` |
| RF-10 | 2 | Cargar las **80 celdas iniciales** (10 MOTO + 70 CARRO) y consultar las **celdas disponibles** (sin estancia abierta). | `seed_data.py` · `GET /celdas/disponibles` |
| RF-11 | 2 | **Corregir la celda** de una estancia abierta (reasignación). Rechaza celda ocupada (409) y vehículo sin estancia abierta (409). | `PATCH /estancias/celda` · `/control-acceso` |
| RF-12 | 2 | Gestionar **clientes** (nombre, documento único, teléfono). Todo vehículo pertenece a un cliente. | `/clientes` · `/gestion/clientes` |
| RF-13 | 2 | **Reasignar** un vehículo a otro cliente. | `PATCH /vehiculos/{id}` con `cliente_id` · `/gestion/vehiculos` |
| RF-14 | 2 | Registrar **mensualidades**: el monto lo calcula el servidor según el tipo de vehículo (MOTO $100.000; AUTOMOVIL y CAMIONETA $250.000); el periodo cubre un mes calendario. Consultar la vigencia. La entrada exige mensualidad vigente. | `POST /pagos`, `GET /pagos`, `GET /vehiculos/{id}/mensualidad` · `/gestion/mensualidades` |
| RF-15 | 2 | **Reporte resumen**: celdas disponibles, celdas totales y clientes registrados. | `GET /reportes/resumen` · `/reportes` |
| RF-16 | 2 | **Inicio y cierre de sesión** de operadores con usuario y contraseña; token JWT con el rol. Todas las operaciones (salvo el login y `/health`) exigen sesión, y el operador que actúa se toma del token. **Cerrar sesión revoca el token** en el servidor. | `POST /auth/login`, `POST /auth/logout` · `/login` |
| RF-17 | 2 | **Roles y permisos.** Ver el detalle de qué puede hacer cada rol, por recurso, justo debajo de esta tabla. | `requiere_roles` en el backend · `rolGuard` y menú por rol en el frontend |
| RF-18 | 3 | **Continuidad del periodo de la mensualidad.** El periodo no es un dato de entrada: lo calcula siempre el servidor. Si el vehículo tiene un pago anterior y este se registra hasta **5 días** después de que venció (`DIAS_GRACIA_RENOVACION`), el nuevo periodo continúa justo donde quedó (`periodo_fin` anterior **+ 1 día**): un pago extemporáneo dentro del margen no mueve la mensualidad. Pasado ese margen, o si es el primer pago del vehículo, el periodo inicia **hoy** (mensualidad nueva). La fecha solo se mueve por una cancelación y el inicio de un contrato nuevo, que no se automatiza. | `app/services/pago.py::_periodo_inicio_automatico` · `POST /pagos` · `/gestion/mensualidades` |
| RF-19 | 3 | **Movimientos y registro de pagos (pantallas).** Listar el historial de pagos con referencia `PAG-n`, placa y cliente, periodo, valor, método (siempre efectivo), estado (Vigente, Vencida o Futura) y fecha de pago; filtrar por referencia, placa o cliente, fecha, tipo de vehículo y estado; mostrar el total recaudado y el recaudo por tipo de lo filtrado, y exportarlo a CSV. Registrar un pago eligiendo solo el vehículo: se muestran su cliente y su mensualidad actual, y el valor y el periodo los calcula el servidor (RF-14, RF-18). No hay medios de pago, referencias ni saldos. | `frontend/src/app/pagos/` · `/gestion/pagos` y `/gestion/pagos/nuevo` (usan `GET /pagos`, `POST /pagos`) |

> La numeración RF-10 a RF-19 es la que ya usan el código y los comentarios del
> repositorio. RF-01 a RF-09 agrupan lo de la iteración 1 y las reglas
> transversales. Si tu documento de la Actividad 1 numera distinto, conserva la
> numeración de ese documento y usa la columna *Evidencia* para enlazar.

### RF-17 en detalle: qué puede hacer cada rol

No alcanza con decir "ADMINISTRADOR gestiona, OPERADOR no administra": lectura
y escritura tienen reglas distintas por recurso, y así está implementado:

| Recurso | ADMINISTRADOR | OPERADOR | Cualquier sesión (sin importar el rol) |
| --- | --- | --- | --- |
| Operadores (`/operadores`) | Crear, editar, eliminar, listar y consultar | Sin acceso (403) | — |
| Celdas (`/celdas`) | Crear, editar, eliminar, listar y consultar | Sin acceso a `/celdas` (403) | `GET /celdas/disponibles` (RF-10) |
| Clientes (`/clientes`) | Crear, editar, eliminar | Sin escritura (403) | Listar y consultar |
| Vehículos (`/vehiculos`) | Crear, editar, eliminar | Sin escritura (403) | Listar y consultar |
| Estancias (`/estancias/entrada`, `/salida`, `/celda`) | Sin acceso (403): no registra accesos | Registrar entrada, salida y corregir celda | Consultar estado por placa (`GET /estancias/vehiculo/{placa}`) |
| Mensualidades (`/pagos`) | Registrar y consultar | Registrar y consultar | Consultar vigencia (`GET /vehiculos/{id}/mensualidad`) |
| Reportes (`/reportes/resumen`) | Consultar | Consultar | Consultar |

Reglas transversales: sin sesión, toda operación (salvo `/auth/login` y
`/health`) responde **401**. Con sesión pero sin el rol que exige el recurso,
responde **403** «No tienes permisos para esta operación.». El menú del
frontend (`app.html`) solo muestra las pantallas que el rol de la sesión puede
usar; intentar una ruta oculta por URL directa también recibe el 403 de la
API, porque el permiso se exige en el backend, no solo se oculta en pantalla.

## Requerimientos no funcionales

| Id | Categoría | Requerimiento | Cómo se cumple |
| --- | --- | --- | --- |
| RNF-01 | Seguridad | Las contraseñas no se almacenan en claro ni se devuelven en ninguna respuesta. | Hash PBKDF2-SHA256 (`app/security.py`); `OperadorRespuesta` no incluye contraseña. |
| RNF-02 | Seguridad | Toda operación de negocio exige sesión y respeta el rol (401 sin sesión, 403 sin permiso); el cierre de sesión revoca el token; los secretos no se versionan. | JWT firmado con `JWT_SECRET` (`backend/.env`, excluido de Git); `backend/.env.example` solo con valores ficticios. |
| RNF-03 | Integridad | La base de datos garantiza las reglas aunque falle la aplicación. | Restricciones únicas, CHECK, FK `RESTRICT` e índices únicos parciales (una estancia abierta por vehículo y por celda). |
| RNF-04 | Confiabilidad | Cada operación es atómica y no deja datos a medias. | Transacciones con commit/rollback en la capa de servicios; errores públicos sin detalles del controlador. |
| RNF-05 | Disponibilidad | Comprobar que la API vive sin depender de la base de datos. | `GET /health` responde `{"status":"ok"}` sin abrir conexión. |
| RNF-06 | Usabilidad | Interfaz en español, mensajes de error claros, formularios con validación visible y fechas en hora de Colombia. | Angular con formularios reactivos, `strictTemplates`, `America/Bogota`. |
| RNF-07 | Mantenibilidad | Separación en capas y cobertura de pruebas automáticas. | `routers` → `services` → `models`; `schemas` para contratos; 209 pruebas backend y 71 frontend. |
| RNF-08 | Portabilidad | Debe ejecutarse en Windows con herramientas verificadas. | Python 3.13, Node.js 24, npm 11, PostgreSQL; comandos PowerShell en `README.md`. |
| RNF-09 | Trazabilidad | Se registra quién actúa y cuándo. | `Estancia` guarda operador y fecha de entrada y salida; `Pago` guarda operador y `fecha_pago`. |
| RNF-10 | Evolución del esquema | Los cambios de base de datos se versionan. | Migraciones Alembic `0001` a `0005`; nunca se aplican sin autorización. |
| RNF-11 | Reglas de negocio | La continuidad de la mensualidad es una regla del servidor, no una opción de pantalla: el cliente nunca envía ni puede forzar el periodo. | `PagoCrear` solo acepta `vehiculo_id` (`extra="forbid"`); el periodo lo calcula siempre `services/pago.py`. |

## Alcance no cubierto

Declarado de forma explícita para no presentar como hecho lo que no lo está:

- No hay recibo imprimible ni cobro por pasarela de pago: la mensualidad se
  registra, no se procesa un pago real.
- No hay un editor de permisos: los dos roles (ADMINISTRADOR y OPERADOR) y sus
  permisos están fijos en el código; no hay más roles ni permisos configurables.
- La **cancelación de un contrato y el inicio de uno nuevo** (el único caso en
  que la fecha de la mensualidad se mueve fuera de la regla de los 5 días) no
  está automatizada: no hay una operación de "cancelar" que reinicie el
  periodo; hoy se logra únicamente dejando que pase el margen de gracia.
- Falta una revisión visual en móvil y una auditoría de accesibilidad completa.
