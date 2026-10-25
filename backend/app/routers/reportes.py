from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.services import reporte as service

router = APIRouter(prefix="/reportes", tags=["Reportes"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get("/resumen")
def resumen(session: DatabaseSession) -> dict:
    """RF-15: celdas disponibles/totales y clientes registrados, en cualquier momento."""
    return service.resumen(session)
