from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, field_validator

from app.models import required_text

Texto = Annotated[str, BeforeValidator(lambda value: required_text(value, "El campo"))]


class ClienteCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: Texto
    documento: Texto
    telefono: Texto


class ClienteActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: Texto | None = None
    documento: Texto | None = None
    telefono: Texto | None = None

    @field_validator("*", mode="before")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Los campos enviados no pueden ser nulos.")
        return value


class ClienteRespuesta(ClienteCrear):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int


class ClientesPagina(BaseModel):
    items: list[ClienteRespuesta]
    total: int
    offset: int
    limit: int
