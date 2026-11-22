"""Mensualidades (RF-14): tarifa y periodo fijados por el servidor, pago en efectivo.

La fecha de la mensualidad no se corre por un pago extemporáneo: si han pasado hasta
DIAS_GRACIA_RENOVACION días desde que terminó el periodo anterior, el nuevo periodo
continúa justo donde quedó. Pasado ese margen (o si es el primer pago del vehículo),
se registra como una mensualidad nueva que empieza hoy.
"""

import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Operador, Pago, Vehiculo
from app.schemas.pago import PagoCrear

MONTO_POR_TIPO: dict[str, Decimal] = {
    "MOTO": Decimal("100000"),
    "AUTOMOVIL": Decimal("250000"),
    "CAMIONETA": Decimal("250000"),
}

# Margen de pago extemporáneo que aún cuenta como renovación (no mueve la mensualidad).
DIAS_GRACIA_RENOVACION = 5


class PagoError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail


def database_operation(operation):
    """Centraliza rollback y mensajes públicos sin detalles del driver."""
    @wraps(operation)
    def wrapped(session: Session, *args, **kwargs):
        try:
            return operation(session, *args, **kwargs)
        except IntegrityError as error:
            session.rollback()
            code = getattr(error.orig, "sqlstate", None)
            if code == "23503":
                raise PagoError(404, "El vehículo o el operador ya no existen.") from None
            if code in {"23502", "23514"}:
                raise PagoError(422, "Los datos incumplen las restricciones del pago.") from None
            raise PagoError(409, "La operación entra en conflicto con los datos existentes.") from None
        except SQLAlchemyError:
            session.rollback()
            raise PagoError(503, "No se pudo completar la operación con la base de datos.") from None
    return wrapped


def _hoy() -> date:
    return datetime.now(timezone.utc).date()


def _fin_de_periodo(inicio: date) -> date:
    """Un mes calendario completo a partir de 'inicio', ambos extremos incluidos.

    El día anterior a "el mismo día del mes siguiente"; si ese día no existe
    (p. ej. 31 de enero -> no hay 31 de febrero), el periodo llega hasta el
    último día de ese mes siguiente, sin restarle un día más.
    """
    siguiente_mes = inicio.month % 12 + 1
    siguiente_anio = inicio.year + (1 if inicio.month == 12 else 0)
    ultimo_dia = calendar.monthrange(siguiente_anio, siguiente_mes)[1]
    if inicio.day > ultimo_dia:
        return date(siguiente_anio, siguiente_mes, ultimo_dia)
    return date(siguiente_anio, siguiente_mes, inicio.day) - timedelta(days=1)


def _ultimo_pago(session: Session, vehiculo_id: int) -> Pago | None:
    return session.scalar(
        select(Pago).where(Pago.vehiculo_id == vehiculo_id).order_by(Pago.periodo_fin.desc())
    )


def _periodo_inicio_automatico(session: Session, vehiculo_id: int) -> date:
    """RF-14: continúa la mensualidad anterior si el pago llega a tiempo (hasta
    DIAS_GRACIA_RENOVACION días después de que terminó); si no, o si es el primer
    pago del vehículo, empieza una mensualidad nueva desde hoy."""
    anterior = _ultimo_pago(session, vehiculo_id)
    hoy = _hoy()
    if anterior is None:
        return hoy
    dias_desde_fin = (hoy - anterior.periodo_fin).days
    if dias_desde_fin <= DIAS_GRACIA_RENOVACION:
        return anterior.periodo_fin + timedelta(days=1)
    return hoy


@database_operation
def register_payment(session: Session, data: PagoCrear, operador: Operador) -> Pago:
    vehiculo = session.get(Vehiculo, data.vehiculo_id)
    if vehiculo is None:
        raise PagoError(404, "Vehículo no encontrado.")
    periodo_inicio = _periodo_inicio_automatico(session, vehiculo.id)
    pago = Pago(
        vehiculo_id=vehiculo.id,
        operador_id=operador.id,
        monto=MONTO_POR_TIPO[vehiculo.tipo],
        periodo_inicio=periodo_inicio,
        periodo_fin=_fin_de_periodo(periodo_inicio),
    )
    session.add(pago)
    session.commit()
    session.refresh(pago)
    return pago


@database_operation
def list_payments(session: Session, offset: int, limit: int, vehiculo_id: int | None = None) -> dict:
    query = select(Pago)
    count_query = select(func.count()).select_from(Pago)
    if vehiculo_id is not None:
        query = query.where(Pago.vehiculo_id == vehiculo_id)
        count_query = count_query.where(Pago.vehiculo_id == vehiculo_id)
    total = session.scalar(count_query)
    items = list(session.scalars(query.order_by(Pago.id).offset(offset).limit(limit)))
    return {"items": items, "total": total, "offset": offset, "limit": limit}


def vigente_para_vehiculo(session: Session, vehiculo_id: int, fecha: date | None = None) -> Pago | None:
    """Consulta simple, sin decorador propio: quien la llama ya corre dentro de su propia transacción."""
    fecha = fecha or _hoy()
    return session.scalar(
        select(Pago)
        .where(Pago.vehiculo_id == vehiculo_id, Pago.periodo_inicio <= fecha, Pago.periodo_fin >= fecha)
        .order_by(Pago.periodo_fin.desc())
    )


@database_operation
def estado_mensualidad(session: Session, vehiculo_id: int) -> dict:
    vehiculo = session.get(Vehiculo, vehiculo_id)
    if vehiculo is None:
        raise PagoError(404, "Vehículo no encontrado.")
    pago = vigente_para_vehiculo(session, vehiculo_id)
    return {"vehiculo_id": vehiculo_id, "vigente": pago is not None, "pago": pago}
