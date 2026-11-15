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
| **2** | Gestión de usuarios (operadores, clientes, inicio de sesión) y gestión de celdas. Incluye pagos (mensualidades) y reportes, porque la entrada depende de la mensualidad. |

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
| RF-17 | 2 | **Roles y permisos.** ADMINISTRADOR: crea y gestiona operadores, celdas, clientes y vehículos; **no** registra accesos. OPERADOR: registra entradas, salidas y correcciones de celda, y consulta celdas disponibles; **no** administra usuarios ni celdas. Ambos registran mensualidades y ven el resumen. Un rol sin permiso recibe 403 y la interfaz oculta lo que no le corresponde. | `requiere_roles` en el backend · `rolGuard` y menú por rol en el frontend |

> La numeración RF-10 a RF-17 es la que ya usan el código y los comentarios del
> repositorio. RF-01 a RF-09 agrupan lo de la iteración 1 y las reglas
> transversales. Si tu documento de la Actividad 1 numera distinto, conserva la
> numeración de ese documento y usa la columna *Evidencia* para enlazar.

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
| RNF-10 | Evolución del esquema | Los cambios de base de datos se versionan. | Migraciones Alembic `0001` a `0004`; nunca se aplican sin autorización. |

## Alcance no cubierto

Declarado de forma explícita para no presentar como hecho lo que no lo está:

- No hay recibo imprimible ni cobro por pasarela de pago: la mensualidad se
  registra, no se procesa un pago real.
- No hay un editor de permisos: los dos roles (ADMINISTRADOR y OPERADOR) y sus
  permisos están fijos en el código; no hay más roles ni permisos configurables.
- Falta una revisión visual en móvil y una auditoría de accesibilidad completa.
