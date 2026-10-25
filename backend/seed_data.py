r"""Datos iniciales para RF-10 (80 celdas: 10 motos y 70 carros).

No se ejecuta automáticamente ni se importa desde la aplicación: es un
script opcional para cargar la configuración inicial del parqueadero en
``autos_colombia``, una sola vez. Es idempotente por código de celda: si
una celda con ese código ya existe, se omite en vez de duplicarla.

No crea operadores (RF-16): usuario, contraseña y turno son datos
sensibles/propios de cada persona y deben crearse desde ``POST /operadores``
(o la pantalla de gestión), nunca con valores de ejemplo en un script.

Uso (PowerShell, con backend/.env ya completo):
    .\.venv\Scripts\python.exe seed_data.py
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ConfigurationError, load_database_settings
from app.database import create_database_engine
from app.models import Celda

MOTOS = 10
CARROS = 70


def celdas_iniciales() -> list[Celda]:
    celdas = [Celda(codigo=f"MOTO-{n:02d}", tipo="MOTO") for n in range(1, MOTOS + 1)]
    celdas += [Celda(codigo=f"CARRO-{n:03d}", tipo="CARRO") for n in range(1, CARROS + 1)]
    return celdas


def main() -> int:
    try:
        engine = create_database_engine(load_database_settings())
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 2
    try:
        with Session(engine) as session, session.begin():
            existentes = set(session.scalars(select(Celda.codigo)))
            todas = celdas_iniciales()
            nuevas = [c for c in todas if c.codigo not in existentes]
            session.add_all(nuevas)
        print(f"Celdas creadas: {len(nuevas)}. Ya existían: {len(todas) - len(nuevas)}.")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
