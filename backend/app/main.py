from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routers.vehiculos import router as vehiculos_router
from app.services.vehiculo import VehiculoError
from app.routers.celdas import router as celdas_router
from app.services.celda import CeldaError
from app.routers.operadores import router as operadores_router
from app.services.operador import OperadorError
from app.routers.estancias import router as estancias_router
from app.services.estancia import EstanciaError
from app.routers.clientes import router as clientes_router
from app.services.cliente import ClienteError
from app.routers.pagos import router as pagos_router
from app.services.pago import PagoError
from app.routers.auth import router as auth_router
from app.auth import AuthError
from app.routers.reportes import router as reportes_router
from app.services.reporte import ReporteError

app = FastAPI(title="Autos Colombia API")
app.include_router(vehiculos_router)
app.include_router(celdas_router)
app.include_router(operadores_router)
app.include_router(estancias_router)
app.include_router(clientes_router)
app.include_router(pagos_router)
app.include_router(auth_router)
app.include_router(reportes_router)

EntityError = (
    VehiculoError | CeldaError | OperadorError | EstanciaError | ClienteError | PagoError | AuthError | ReporteError
)


@app.exception_handler(VehiculoError)
@app.exception_handler(CeldaError)
@app.exception_handler(OperadorError)
@app.exception_handler(EstanciaError)
@app.exception_handler(ClienteError)
@app.exception_handler(PagoError)
@app.exception_handler(AuthError)
@app.exception_handler(ReporteError)
async def entity_error_handler(request, error: EntityError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
