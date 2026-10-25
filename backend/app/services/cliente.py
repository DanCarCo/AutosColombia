from functools import wraps

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Cliente
from app.schemas.cliente import ClienteActualizar, ClienteCrear


class ClienteError(Exception):
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
            constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            if code == "23505" and constraint == "uq_cliente_documento":
                raise ClienteError(409, "Ya existe un cliente con ese documento.") from None
            if code == "23503":
                raise ClienteError(409, "El cliente tiene registros relacionados y no se puede eliminar.") from None
            if code in {"23502", "23514"}:
                raise ClienteError(422, "Los datos incumplen las restricciones del cliente.") from None
            raise ClienteError(409, "La operación entra en conflicto con los datos existentes.") from None
        except SQLAlchemyError:
            session.rollback()
            raise ClienteError(503, "No se pudo completar la operación con la base de datos.") from None
    return wrapped


def find_client(session: Session, client_id: int) -> Cliente:
    client = session.get(Cliente, client_id)
    if client is None:
        raise ClienteError(404, "Cliente no encontrado.")
    return client


@database_operation
def create_client(session: Session, data: ClienteCrear) -> Cliente:
    client = Cliente(**data.model_dump())
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@database_operation
def list_clients(session: Session, offset: int, limit: int) -> dict:
    total = session.scalar(select(func.count()).select_from(Cliente))
    items = list(session.scalars(select(Cliente).order_by(Cliente.id).offset(offset).limit(limit)))
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@database_operation
def get_client(session: Session, client_id: int) -> Cliente:
    return find_client(session, client_id)


@database_operation
def update_client(session: Session, client_id: int, data: ClienteActualizar) -> Cliente:
    client = find_client(session, client_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    session.commit()
    session.refresh(client)
    return client


@database_operation
def delete_client(session: Session, client_id: int) -> None:
    client = find_client(session, client_id)
    session.delete(client)
    session.commit()
