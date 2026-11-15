from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.auth import operador_actual, solo_administrador
from app.database import get_session
from app.schemas.cliente import ClienteActualizar, ClienteCrear, ClienteRespuesta, ClientesPagina
from app.services import cliente as service

router = APIRouter(prefix="/clientes", tags=["Clientes"])
DatabaseSession = Annotated[Session, Depends(get_session)]
ADMIN = [Depends(solo_administrador)]
SESION = [Depends(operador_actual)]
ClientId = Annotated[int, Path(ge=1, le=9223372036854775807)]


@router.post("", response_model=ClienteRespuesta, status_code=201, dependencies=ADMIN)
def create(data: ClienteCrear, session: DatabaseSession):
    return service.create_client(session, data)


@router.get("", response_model=ClientesPagina, dependencies=SESION)
def list_all(
    session: DatabaseSession,
    offset: Annotated[int, Query(ge=0, le=9223372036854775807)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.list_clients(session, offset, limit)


@router.get("/{id}", response_model=ClienteRespuesta, dependencies=SESION)
def get_one(id: ClientId, session: DatabaseSession):
    return service.get_client(session, id)


@router.patch("/{id}", response_model=ClienteRespuesta, dependencies=ADMIN)
def update(id: ClientId, data: ClienteActualizar, session: DatabaseSession):
    return service.update_client(session, id, data)


@router.delete("/{id}", status_code=204, dependencies=ADMIN)
def delete(id: ClientId, session: DatabaseSession) -> Response:
    service.delete_client(session, id)
    return Response(status_code=204)
