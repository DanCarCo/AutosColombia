# Plan de pruebas resumido — Gestión de usuarios y gestión de celdas

Formato resumido (entregable G). Cubre la **iteración 2** (usuarios y celdas) e
incluye las pruebas de las funciones que la hacen posible (sesión, mensualidad,
entrada). Cada caso indica si tiene prueba **automática** (archivo de `pytest`
o de Angular) y el paso **manual** para el video.

- **Entorno:** Windows, Python 3.13, Node.js 24, PostgreSQL local con migración `0004`.
- **Datos de demostración:** `backend/seed_demo.py` (solo demostración; ver `backend/README.md`).
- **Cómo ejecutar todo:** `entrega-ingenieria-software/verificar-entrega.ps1` (ver también `AGENTS.md`).

## Resultado de la última ejecución (14/11/2026)

| Suite | Comando | Resultado |
| --- | --- | --- |
| Backend | `.\.venv\Scripts\python.exe -m pytest -q` | **209 aprobadas**, 9 omitidas (necesitan `RUN_POSTGRES_TESTS=1`) |
| Frontend (compilación) | `npm.cmd run build` | Compilación correcta |
| Frontend (pruebas) | `npm.cmd test -- --watch=false` | **71 aprobadas** en 13 archivos |

Las 9 pruebas omitidas son de integración con PostgreSQL real; se activan con
`RUN_POSTGRES_TESTS=1` y requieren la base `autos_colombia` en la revisión `0004`
(ver `backend/README.md`). No se afirma su resultado aquí si no se ejecutaron.

## Casos de prueba

Convenciones: **A** = automática, **M** = manual. «Esperado» es lo que debe verse.

### Celdas (RF-06, RF-10 · HU-06, HU-09)

| Id | Caso | Pasos | Esperado | Tipo y evidencia |
| --- | --- | --- | --- | --- |
| CP-01 | Crear celda válida | `/gestion/celdas` → Nueva celda → código ` a-01 `, tipo «General» | Aparece `A-01` en mayúsculas y recortada | A: `test_celdas_postgres.py`, `celdas.spec.ts` · M |
| CP-02 | Código repetido | Crear de nuevo `A-01` | «Ya existe una celda con ese código» (409) | A: `celdas.spec.ts` · M |
| CP-03 | Campos vacíos | Guardar con código en blanco | No se envía; campo señalado (422 si llega a la API) | A: `celdas.spec.ts` |
| CP-04 | Eliminar celda sin uso | Eliminar `A-01` y confirmar | Desaparece del listado | A: `celdas.spec.ts` · M |
| CP-05 | Eliminar celda con estancias | Eliminar una celda usada | No se elimina (409) | A: restricción FK `RESTRICT` en `models.py` y `test_estancias_postgres.py` · M |
| CP-06 | Celdas iniciales | `python seed_data.py` dos veces | 80 celdas (10 MOTO, 70 CARRO), sin duplicados | M: contar en `/reportes` |
| CP-07 | Celdas disponibles | `GET /celdas/disponibles` | Solo celdas sin estancia abierta; cambia al entrar o salir un vehículo | A: `test_celdas_disponibles.py` · M |

### Operadores (RF-07 · HU-07)

| Id | Caso | Pasos | Esperado | Tipo y evidencia |
| --- | --- | --- | --- | --- |
| CP-08 | Crear operador | `/gestion/operadores` → datos + turno NOCHE | Registrado; la respuesta no trae contraseña | A: `test_operadores.py` (`test_response_never_includes_password_fields`), `operadores.spec.ts` |
| CP-09 | Contraseña protegida | Revisar la fila en BD o la respuesta | Solo `password_hash` con formato `pbkdf2_sha256$…` | A: `test_auth.py` (`test_hash_password_never_stores_plaintext…`) |
| CP-10 | Usuario repetido | Crear otro con el mismo usuario | «Ya existe un operador con ese usuario» (409) | A: `test_operadores.py` (`test_duplicate_usuario_conflict…`) |
| CP-11 | Turno inválido | `POST` con turno `TARDE` (Swagger) | 422 | A: `test_operadores.py` (`test_invalid_turno_is_422…`) |
| CP-12 | Editar sin contraseña | Editar nombre y dejar contraseña vacía | La contraseña anterior sigue funcionando en el login | A: `operadores.spec.ts` · M |

### Clientes y vehículos (RF-12, RF-13 · HU-11)

| Id | Caso | Pasos | Esperado | Tipo y evidencia |
| --- | --- | --- | --- | --- |
| CP-13 | Crear cliente | `/gestion/clientes` → datos válidos | Aparece en el listado | A: `clientes.spec.ts` · M |
| CP-14 | Documento repetido | Repetir documento | «Ya existe un cliente con ese documento» (409) | A: `test_clientes.py` |
| CP-15 | Vehículo exige cliente | Crear vehículo sin cliente | No se guarda | A: `test_vehiculos.py` (`test_creation_requires_cliente_id`) |
| CP-16 | Reasignar vehículo | Editar vehículo → otro cliente | Queda asociado al nuevo cliente | A: `test_vehiculos.py` (`test_patch_allows_reassigning_cliente`) |
| CP-17 | Año válido | Modelo 1899 y 2201 | Rechazado; 1900 y 2200 aceptados | A: `test_vehiculos.py`, `test_models.py` |
| CP-18 | CHECK de año en BD | Revisar la migración `0004` | `ck_vehiculo_modelo_anio` = `modelo BETWEEN 1900 AND 2200` | A: `test_models.py` (`test_migration_matches_models_without_connecting`) · M: `alembic … upgrade head --sql` |
| CP-19 | Cliente con vehículos | Eliminar un cliente con vehículos | No se elimina (409) | A: `test_clientes.py` |

### Sesión, mensualidad y entrada (RF-14, RF-16 · HU-12, HU-14, HU-03)

| Id | Caso | Pasos | Esperado | Tipo y evidencia |
| --- | --- | --- | --- | --- |
| CP-20 | Login correcto | `/login` con usuario de demo | Entra; nombre visible y *Cerrar sesión* | A: `test_auth.py`, `login.spec.ts` · M |
| CP-21 | Login incorrecto | Contraseña errónea | «Usuario o contraseña incorrectos» (401), sin decir cuál falló | A: `test_auth.py` |
| CP-22 | Ruta protegida | Abrir `/control-acceso` sin sesión | Redirige a `/login` | A: `auth.guard.spec.ts` · M |
| CP-23 | Registrar mensualidad | `/gestion/mensualidades` → vehículo → Registrar | Pago con monto del servidor y periodo de un mes | A: `test_pagos.py`, `mensualidades.spec.ts` · M |
| CP-24 | Monto no aceptado | `POST /pagos` con `monto` (Swagger) | 422 | A: `test_pagos.py` (`test_pago_crear_rechaza_monto_explicito`) |
| CP-25 | Entrada sin mensualidad | Entrada de un vehículo sin pago vigente | 402 «El vehículo no tiene mensualidad vigente» | A: `test_estancia_servicio.py` |
| CP-26 | Pago exige sesión | `POST /pagos` sin token | 401 | A: `test_pagos.py` |

### Control de acceso y reportes (RF-03/04/05/11/15 · HU-03/04/05/10/13)

| Id | Caso | Pasos | Esperado | Tipo y evidencia |
| --- | --- | --- | --- | --- |
| CP-27 | Entrada y salida | Entrada, consulta *Dentro*, salida, consulta *Fuera* | Celda ocupada y luego libre | A: `control-acceso.spec.ts`, `test_estancias_postgres.py` · M |
| CP-28 | Corregir celda | `PATCH /estancias/celda` o pantalla | La estancia pasa a la nueva celda; si está ocupada, 409 | A: `test_estancia_servicio.py`, `control-acceso.spec.ts` · M |
| CP-29 | Resumen | `/reportes` | Celdas disponibles, totales y clientes registrados | A: `test_reportes.py`, `reportes.spec.ts` · M |
| CP-30 | Salud de la API | `GET /health` | `{"status":"ok"}` sin tocar la base de datos | A: `test_health.py` |

## Criterio de aceptación de la iteración

La iteración 2 se considera lista cuando: los 30 casos tienen resultado
«esperado»; ambas suites automáticas pasan; el recorrido manual del video no
muestra errores inesperados; y `git status` no contiene secretos.
