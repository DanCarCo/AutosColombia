r"""Crea (o promueve) una cuenta ADMINISTRADOR. Necesario en una base nueva, porque POST /operadores exige ese rol.

Uso (con backend/.env completo y las migraciones aplicadas):
    .venv\Scripts\python.exe crear_administrador.py USUARIO
La contraseña se pide por teclado (no queda en el historial ni en argumentos).
Si el usuario ya existe, solo se le asigna el rol ADMINISTRADOR (no se cambia su contraseña).
"""

import getpass
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ConfigurationError, load_database_settings
from app.database import create_database_engine
from app.models import Operador
from app.security import hash_password


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].strip():
        print("Uso: crear_administrador.py USUARIO", file=sys.stderr)
        return 2
    usuario = argv[1].strip()
    try:
        engine = create_database_engine(load_database_settings())
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 2
    try:
        with Session(engine) as session, session.begin():
            operador = session.scalar(select(Operador).where(Operador.usuario == usuario))
            if operador is not None:
                operador.rol = "ADMINISTRADOR"
                print(f"El usuario {usuario!r} ya existía: ahora es ADMINISTRADOR (contraseña sin cambios).")
                return 0
            clave = getpass.getpass("Contraseña del nuevo administrador: ")
            if clave != getpass.getpass("Repite la contraseña: ") or not clave.strip():
                print("Las contraseñas no coinciden o están vacías.", file=sys.stderr)
                return 1
            session.add(Operador(nombre=usuario, telefono="sin registrar", usuario=usuario,
                                 password_hash=hash_password(clave), turno="DIA", rol="ADMINISTRADOR"))
            print(f"Administrador {usuario!r} creado. Edita sus datos desde la pantalla de operadores.")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
