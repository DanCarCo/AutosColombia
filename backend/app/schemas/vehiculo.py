from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.models import required_text


Texto = Annotated[str, BeforeValidator(lambda value: required_text(value, "El campo"))]
Placa = Annotated[Texto, AfterValidator(str.upper)]
Anio = Annotated[int, Field(strict=True, ge=1900, le=2200)]
TipoVehiculo = Annotated[
    Literal["MOTO", "AUTOMOVIL", "CAMIONETA"],
    BeforeValidator(lambda value: required_text(value, "tipo")),
]
Identificador = Annotated[int, Field(strict=True, ge=1, le=9223372036854775807)]


class VehiculoCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    placa: Placa
    color: Texto
    modelo: Anio
    marca: Texto
    tipo: TipoVehiculo
    # RF-12: todo vehículo pertenece a un cliente (obligatorio, sin excepción: RF-14).
    cliente_id: Identificador


class VehiculoActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    placa: Placa | None = None
    color: Texto | None = None
    modelo: Anio | None = None
    marca: Texto | None = None
    tipo: TipoVehiculo | None = None
    # RF-13: reasigna el vehículo a otro cliente.
    cliente_id: Identificador | None = None

    @field_validator("*", mode="before")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Los campos enviados no pueden ser nulos.")
        return value


class VehiculoRespuesta(VehiculoCrear):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int


class VehiculosPagina(BaseModel):
    items: list[VehiculoRespuesta]
    total: int
    offset: int
    limit: int
