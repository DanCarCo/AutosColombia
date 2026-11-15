import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { timeout } from 'rxjs';
import { MensualidadEstado, Pago, PagoCrear, PagosPagina, ResumenReporte } from '../models/pago';
import { API_BASE_URL } from './api.service';

// RF-14 (mensualidades) y RF-15 (reportes). El monto lo calcula el servidor.
@Injectable({ providedIn: 'root' })
export class PagosService {
  private readonly http = inject(HttpClient);
  private readonly base = inject(API_BASE_URL);

  registrar(data: PagoCrear) {
    return this.http.post<Pago>(`${this.base}/pagos`, data).pipe(timeout(15000));
  }
  listar(offset: number, limit: number) {
    return this.http
      .get<PagosPagina>(`${this.base}/pagos`, { params: { offset, limit } })
      .pipe(timeout(15000));
  }
  estadoMensualidad(vehiculoId: number) {
    return this.http
      .get<MensualidadEstado>(`${this.base}/vehiculos/${vehiculoId}/mensualidad`)
      .pipe(timeout(15000));
  }
  resumen() {
    return this.http.get<ResumenReporte>(`${this.base}/reportes/resumen`).pipe(timeout(15000));
  }
}
