from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, field_validator

from app.models import required_text

Texto = Annotated[str, BeforeValidator(lambda value: required_text(value, "El campo"))]
Turno = Literal["DIA", "NOCHE"]


class OperadorCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: Texto
    telefono: Texto
    usuario: Texto
    password: Texto
    turno: Turno


class OperadorActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: Texto | None = None
    telefono: Texto | None = None
    usuario: Texto | None = None
    password: Texto | None = None
    turno: Turno | None = None

    @field_validator("*", mode="before")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Los campos enviados no pueden ser nulos.")
        return value


class OperadorRespuesta(BaseModel):
    """Nunca incluye password ni password_hash."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int
    nombre: Texto
    telefono: Texto
    usuario: Texto
    turno: Turno


class OperadoresPagina(BaseModel):
    items: list[OperadorRespuesta]
    total: int
    offset: int
    limit: int
