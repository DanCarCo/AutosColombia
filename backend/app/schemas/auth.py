from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict

from app.models import required_text
from app.schemas.operador import OperadorRespuesta

Texto = Annotated[str, BeforeValidator(lambda value: required_text(value, "El campo"))]


class LoginCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario: Texto
    password: Texto


class TokenRespuesta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str
    token_type: str = "bearer"
    expira_minutos: int
    operador: OperadorRespuesta
