from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Identificador = Annotated[int, Field(strict=True, ge=1, le=9223372036854775807)]


class PagoCrear(BaseModel):
    """El monto y el periodo se calculan en el servidor (RF-14); el cliente nunca los envía.

    El inicio del periodo no es un dato de entrada: si hay un pago anterior y el pago se
    registra hasta 5 días después de que terminó, el nuevo periodo continúa justo donde
    quedó (un pago extemporáneo no corre la mensualidad). Pasados esos 5 días, o si es el
    primer pago del vehículo, el periodo inicia hoy (nueva mensualidad).
    """

    model_config = ConfigDict(extra="forbid")
    vehiculo_id: Identificador


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
