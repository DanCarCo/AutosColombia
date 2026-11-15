# Incidencias del plan de pruebas PP-02 (ejecución del 15/11/2026)

| Id | Descripción | Casos afectados | Impacto | Propuesta |
| --- | --- | --- | --- | --- |
| INC-01 | El sistema no define roles (ADMINISTRADOR / OPERADOR). Todas las cuentas ven el mismo menú y tienen los mismos permisos. | US-01, US-02, US-07, US-08, PE-02, PE-03, PE-04, PE-05 | Alto: el plan acordado exige separación de roles | Agregar rol a `operador`, validarlo en el backend (403) y filtrar el menú por rol |
| INC-02 | Los endpoints de operadores y celdas no exigen sesión; solo estancias y pagos la exigen. | PE-01 | Crítico: cualquiera con acceso a la API crea o borra usuarios y celdas | Exigir `operador_actual` en `/operadores`, `/celdas`, `/clientes` y `/vehiculos` |
| INC-03 | El cierre de sesión no revoca el token (JWT sin lista de revocación): sigue válido hasta expirar (480 min). | US-05 (variante revocada), US-06 | Alto | Lista de revocación o tokens de corta duración con renovación |
| INC-04 | El formulario de entrada lista todas las celdas, incluidas las ocupadas, y rechaza la ocupación solo al registrar. | PE-05 | Medio: la API `/celdas/disponibles` ya filtra correctamente | Usar `/celdas/disponibles` en el selector de entrada |

Resultado: 19 casos aprobados y 11 fallidos de 30. Los fallos corresponden a funciones del plan que el sistema no implementa
(roles y revocación de sesión), no a errores en la gestión de celdas, que aprobó los 13 casos. Los datos de las ejecuciones están
en los archivos `ID.txt` de esta carpeta; las credenciales y tokens están ocultos.
