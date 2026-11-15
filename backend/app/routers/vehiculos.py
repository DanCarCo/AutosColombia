from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.auth import operador_actual
from app.database import get_session
from app.models import Operador
from app.schemas.vehiculo import VehiculoActualizar, VehiculoCrear, VehiculoRespuesta, VehiculosPagina
from app.services import vehiculo as service

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])
DatabaseSession = Annotated[Session, Depends(get_session)]
OperadorAutenticado = Annotated[Operador, Depends(operador_actual)]
VehicleId = Annotated[int, Path(ge=1, le=9223372036854775807)]


@router.post("", response_model=VehiculoRespuesta, status_code=201)
def create(data: VehiculoCrear, session: DatabaseSession, operador: OperadorAutenticado):
    return service.create_vehicle(session, data)


@router.get("", response_model=VehiculosPagina)
def list_all(
    session: DatabaseSession,
    offset: Annotated[int, Query(ge=0, le=9223372036854775807)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.list_vehicles(session, offset, limit)


@router.get("/{id}", response_model=VehiculoRespuesta)
def get_one(id: VehicleId, session: DatabaseSession):
    return service.get_vehicle(session, id)


@router.patch("/{id}", response_model=VehiculoRespuesta)
def update(id: VehicleId, data: VehiculoActualizar, session: DatabaseSession, operador: OperadorAutenticado):
    return service.update_vehicle(session, id, data)


@router.delete("/{id}", status_code=204)
def delete(id: VehicleId, session: DatabaseSession, operador: OperadorAutenticado) -> Response:
    service.delete_vehicle(session, id)
    return Response(status_code=204)
