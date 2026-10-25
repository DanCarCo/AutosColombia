r"""Datos de demostración para probar control de acceso de punta a punta.

NO pensado para producción: crea operadores, clientes, vehículos,
mensualidades vigentes y un par de estancias abiertas con credenciales
de ejemplo bien conocidas, para verificar manualmente entrada/salida,
corrección de celda y reportes. Es idempotente por campos únicos
(usuario, documento, placa): si el dato ya existe, lo deja igual.

Uso (con backend/.env ya completo y tras aplicar migraciones):
    .venv/bin/python seed_demo.py
"""

import sys
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ConfigurationError, load_database_settings
from app.database import create_database_engine
from app.models import Celda, Cliente, Operador, Pago, Vehiculo
from app.security import hash_password
from app.services.pago import MONTO_POR_TIPO, _fin_de_periodo

OPERADORES = [
    {"nombre": "Laura Gómez", "telefono": "3001112222", "usuario": "operador.dia", "password": "Operador123", "turno": "DIA"},
    {"nombre": "Carlos Ruiz", "telefono": "3003334444", "usuario": "admin", "password": "Admin1234", "turno": "NOCHE"},
]

CLIENTES = [
    {"nombre": "Juan Pérez", "documento": "1000100010", "telefono": "3101112222"},
    {"nombre": "María Torres", "documento": "1000200020", "telefono": "3102223333"},
    {"nombre": "Andrés López", "documento": "1000300030", "telefono": "3103334444"},
]

VEHICULOS = [
    {"placa": "ABC123", "color": "Rojo", "modelo": 2021, "marca": "Mazda", "tipo": "AUTOMOVIL", "cliente_documento": "1000100010"},
    {"placa": "XYZ789", "color": "Azul", "modelo": 2019, "marca": "Chevrolet", "tipo": "CAMIONETA", "cliente_documento": "1000100010"},
    {"placa": "MOT001", "color": "Negro", "modelo": 2022, "marca": "Yamaha", "tipo": "MOTO", "cliente_documento": "1000200020"},
    {"placa": "DEF456", "color": "Blanco", "modelo": 2020, "marca": "Renault", "tipo": "AUTOMOVIL", "cliente_documento": "1000300030"},
]

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
            existentes_celdas = set(session.scalars(select(Celda.codigo)))
            nuevas_celdas = [c for c in celdas_iniciales() if c.codigo not in existentes_celdas]
            session.add_all(nuevas_celdas)
            session.flush()

            operadores_por_usuario: dict[str, Operador] = {}
            for datos in OPERADORES:
                operador = session.scalar(select(Operador).where(Operador.usuario == datos["usuario"]))
                if operador is None:
                    operador = Operador(
                        nombre=datos["nombre"],
                        telefono=datos["telefono"],
                        usuario=datos["usuario"],
                        password_hash=hash_password(datos["password"]),
                        turno=datos["turno"],
                    )
                    session.add(operador)
                    session.flush()
                operadores_por_usuario[datos["usuario"]] = operador

            clientes_por_documento: dict[str, Cliente] = {}
            for datos in CLIENTES:
                cliente = session.scalar(select(Cliente).where(Cliente.documento == datos["documento"]))
                if cliente is None:
                    cliente = Cliente(nombre=datos["nombre"], documento=datos["documento"], telefono=datos["telefono"])
                    session.add(cliente)
                    session.flush()
                clientes_por_documento[datos["documento"]] = cliente

            vehiculos_por_placa: dict[str, Vehiculo] = {}
            for datos in VEHICULOS:
                vehiculo = session.scalar(select(Vehiculo).where(Vehiculo.placa == datos["placa"]))
                if vehiculo is None:
                    vehiculo = Vehiculo(
                        placa=datos["placa"],
                        color=datos["color"],
                        modelo=datos["modelo"],
                        marca=datos["marca"],
                        tipo=datos["tipo"],
                        cliente_id=clientes_por_documento[datos["cliente_documento"]].id,
                    )
                    session.add(vehiculo)
                    session.flush()
                vehiculos_por_placa[datos["placa"]] = vehiculo

            operador_dia = operadores_por_usuario["operador.dia"]
            hoy = date.today()
            for vehiculo in vehiculos_por_placa.values():
                tiene_pago_vigente = session.scalar(
                    select(Pago).where(
                        Pago.vehiculo_id == vehiculo.id,
                        Pago.periodo_inicio <= hoy,
                        Pago.periodo_fin >= hoy,
                    )
                )
                if tiene_pago_vigente is None:
                    session.add(
                        Pago(
                            vehiculo_id=vehiculo.id,
                            operador_id=operador_dia.id,
                            monto=MONTO_POR_TIPO[vehiculo.tipo],
                            periodo_inicio=hoy,
                            periodo_fin=_fin_de_periodo(hoy),
                        )
                    )

        print("Listo. Credenciales de prueba:")
        for datos in OPERADORES:
            print(f"  usuario={datos['usuario']!r} password={datos['password']!r} turno={datos['turno']}")
        print(f"Clientes: {len(CLIENTES)}. Vehículos: {len(VEHICULOS)} (todos con mensualidad vigente).")
        print(f"Celdas nuevas creadas: {len(nuevas_celdas)}.")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
