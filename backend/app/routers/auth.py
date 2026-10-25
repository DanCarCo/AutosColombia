from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import login as login_operator
from app.database import get_session
from app.schemas.auth import LoginCrear, TokenRespuesta

router = APIRouter(prefix="/auth", tags=["Autenticación"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.post("/login", response_model=TokenRespuesta)
def login(data: LoginCrear, session: DatabaseSession) -> TokenRespuesta:
    """RF-16: inicio de sesión de operadores; emite el token usado en entrada/salida/pagos."""
    operador, token, minutos = login_operator(session, data)
    return TokenRespuesta(access_token=token, expira_minutos=minutos, operador=operador)
