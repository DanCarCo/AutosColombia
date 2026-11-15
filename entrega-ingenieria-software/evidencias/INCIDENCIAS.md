# Incidencias del plan de pruebas PP-02

Estado al 15/11/2026: **las 4 incidencias están cerradas**; los 30 casos quedaron aprobados en la reejecución.

| Id | Descripción (primera ejecución, commit 0cfb344) | Casos | Solución | Verificación |
| --- | --- | --- | --- | --- |
| INC-01 | No existían roles; todas las cuentas veían el mismo menú y tenían los mismos permisos. | US-01, US-02, US-07, US-08, PE-02, PE-03, PE-04 | Columna `operador.rol` (migración 0005), `requiere_roles` en la API (403) y menú/guards por rol en el frontend | US-01, US-02, US-07, US-08, PE-02, PE-03, PE-04 aprobados; `tests/test_roles.py` cubre la matriz de permisos |
| INC-02 | Operadores y celdas no exigían sesión. | PE-01 | Todas las rutas de negocio exigen sesión (401) | PE-01 aprobado |
| INC-03 | El cierre de sesión no revocaba el token. | US-05, US-06 | `POST /auth/logout` guarda el `jti` en `token_revocado`; el frontend lo llama al cerrar sesión | US-05 y US-06 aprobados (el token reutilizado responde 401) |
| INC-04 | El formulario de entrada listaba las celdas ocupadas. | PE-05 | El selector usa `/celdas/disponibles` | PE-05 aprobado |

Resultado de la reejecución: **30 aprobados, 0 fallidos**. Los archivos `ID.txt` de esta carpeta son la evidencia de la reejecución
(la de la primera ejecución se sobrescribió; el Excel conserva en cada caso la nota de lo que había fallado). Credenciales y tokens ocultos.

Pendiente de la entrega: aplicar la migración 0005 en la base real (revisar antes con `alembic upgrade 0004:0005 --sql`) y crear el
primer administrador si hace falta.
