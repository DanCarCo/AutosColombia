from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import operador_actual
from app.database import get_session
from app.models import Operador
from app.schemas.estancia import (
    CambiarCeldaCrear, EntradaCrear, SalidaCrear, EstanciaRespuesta, EstadoVehiculoRespuesta,
)
from app.schemas.vehiculo import Placa
from app.services.estancia import ServicioEstancia

router = APIRouter(prefix="/estancias", tags=["Estancias"])
DatabaseSession = Annotated[Session, Depends(get_session)]
OperadorAutenticado = Annotated[Operador, Depends(operador_actual)]


@router.post("/entrada", response_model=EstanciaRespuesta, status_code=201)
def entrada(data: EntradaCrear, session: DatabaseSession, operador: OperadorAutenticado) -> EstanciaRespuesta:
    return ServicioEstancia(session).entrada(data, operador)


@router.post("/salida", response_model=EstanciaRespuesta)
def salida(data: SalidaCrear, session: DatabaseSession, operador: OperadorAutenticado) -> EstanciaRespuesta:
    return ServicioEstancia(session).salida(data, operador)


@router.patch("/celda", response_model=EstanciaRespuesta)
def cambiar_celda(
    data: CambiarCeldaCrear, session: DatabaseSession, operador: OperadorAutenticado
) -> EstanciaRespuesta:
    """RF-11: mueve la estancia abierta de un vehículo a otra celda."""
    return ServicioEstancia(session).cambiar_celda(data)


@router.get("/vehiculo/{placa}", response_model=EstadoVehiculoRespuesta)
def consultar(placa: Placa, session: DatabaseSession) -> EstadoVehiculoRespuesta:
    return ServicioEstancia(session).consultar(placa)
