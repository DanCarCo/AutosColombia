# Base de datos (volcado)

`autos_colombia.sql` es un volcado de PostgreSQL 16 (esquema, restricciones y datos
de demostración generados con `backend/seed_demo.py`). Las contraseñas están como hash
PBKDF2; las credenciales de ejemplo de `seed_demo.py` son solo para pruebas.

Restaurar en una base vacía (por ejemplo, un contenedor `postgres:16` en el puerto 5433):

```powershell
docker exec -i autos_postgres psql -U autos -d autos_colombia < backend/database/autos_colombia.sql
```
