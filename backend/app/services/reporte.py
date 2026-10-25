"""RF-15: resumen de celdas disponibles y clientes registrados."""

from functools import wraps

from sqlalchemy import exists, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Celda, Cliente, Estancia


class ReporteError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail


def database_operation(operation):
    @wraps(operation)
    def wrapped(session: Session, *args, **kwargs):
        try:
            return operation(session, *args, **kwargs)
        except SQLAlchemyError:
            session.rollback()
            raise ReporteError(503, "No se pudo completar la operación con la base de datos.") from None
    return wrapped


@database_operation
def resumen(session: Session) -> dict:
    ocupada = exists().where(Estancia.celda_id == Celda.id, Estancia.salida.is_(None))
    celdas_totales = session.scalar(select(func.count()).select_from(Celda))
    celdas_disponibles = session.scalar(select(func.count()).select_from(Celda).where(~ocupada))
    clientes_registrados = session.scalar(select(func.count()).select_from(Cliente))
    return {
        "celdas_totales": celdas_totales,
        "celdas_disponibles": celdas_disponibles,
        "clientes_registrados": clientes_registrados,
    }
