"""Configuración compartida de pruebas.

Varias pruebas de la API resuelven la configuración (JWT y PostgreSQL) a
través de las dependencias de FastAPI. Antes dependían de que existiera
``backend/.env``, por lo que fallaban en un clon limpio. Si NO existe
``backend/.env``, aquí se fijan valores ficticios solo para este proceso de
pruebas (el entorno tiene prioridad sobre ``.env``). Nunca se abre una
conexión real con ellos y no son secretos. Si existe un ``.env`` real, no se
toca (así las pruebas con ``RUN_POSTGRES_TESTS=1`` usan la base verdadera).
"""

import os

from app.config import ENV_FILE

if not ENV_FILE.exists():
    for clave, valor in {
        "JWT_SECRET": "secreto-ficticio-solo-para-pruebas-automatizadas",
        "JWT_EXPIRATION_MINUTES": "480",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "5432",
        "DB_NAME": "base_ficticia_pruebas",
        "DB_USER": "usuario_ficticio",
        "DB_PASSWORD": "clave-ficticia-pruebas",
        "DB_CONNECT_TIMEOUT": "1",
    }.items():
        os.environ.setdefault(clave, valor)
