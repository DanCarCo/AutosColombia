from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.auth import operador_actual
from app.database import get_session
from app.models import Operador
from app.schemas.pago import MensualidadEstadoRespuesta, PagoCrear, PagoRespuesta, PagosPagina
from app.services import pago as service

router = APIRouter(tags=["Mensualidades"])
DatabaseSession = Annotated[Session, Depends(get_session)]
OperadorAutenticado = Annotated[Operador, Depends(operador_actual)]
VehicleIdFiltro = Annotated[int, Query(ge=1, le=9223372036854775807)]
VehicleId = Annotated[int, Path(ge=1, le=9223372036854775807)]


@router.post("/pagos", response_model=PagoRespuesta, status_code=201)
def registrar(data: PagoCrear, session: DatabaseSession, operador: OperadorAutenticado) -> PagoRespuesta:
    """RF-14: registra el pago de la mensualidad; el monto lo calcula el servidor."""
    return service.register_payment(session, data, operador)


@router.get("/pagos", response_model=PagosPagina)
def list_all(
    session: DatabaseSession,
    offset: Annotated[int, Query(ge=0, le=9223372036854775807)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    vehiculo_id: VehicleIdFiltro | None = None,
) -> PagosPagina:
    return service.list_payments(session, offset, limit, vehiculo_id)


@router.get("/vehiculos/{id}/mensualidad", response_model=MensualidadEstadoRespuesta)
def estado(id: VehicleId, session: DatabaseSession) -> dict:
    """RF-14: indica si el vehículo tiene mensualidad vigente hoy."""
    return service.estado_mensualidad(session, id)
