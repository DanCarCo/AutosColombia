from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Identificador = Annotated[int, Field(strict=True, ge=1, le=9223372036854775807)]


class PagoCrear(BaseModel):
    """El monto se calcula en el servidor según el tipo de vehículo (RF-14); nunca lo envía el cliente."""

    model_config = ConfigDict(extra="forbid")
    vehiculo_id: Identificador
    # Si se omite, el servicio usa la fecha del servidor como inicio del periodo.
    periodo_inicio: date | None = None


class PagoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int
    vehiculo_id: int
    operador_id: int
    monto: Decimal
    periodo_inicio: date
    periodo_fin: date
    fecha_pago: datetime


class PagosPagina(BaseModel):
    items: list[PagoRespuesta]
    total: int
    offset: int
    limit: int


class MensualidadEstadoRespuesta(BaseModel):
    vehiculo_id: int
    vigente: bool
    pago: PagoRespuesta | None
