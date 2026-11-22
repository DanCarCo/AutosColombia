import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { EMPTY, Observable, expand, reduce, throwError, timeout } from 'rxjs';
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
  // Historial completo de pagos (todas las páginas) para la pantalla de movimientos (RF-19).
  todos(): Observable<Pago[]> {
    return this.listar(0, 100).pipe(
      expand((page) => {
        const next = page.offset + page.items.length;
        if (next >= page.total) return EMPTY;
        if (!page.items.length)
          return throwError(() => new Error('Historial incompleto. Vuelve a intentarlo.'));
        return this.listar(next, 100);
      }),
      reduce((items, page) => [...items, ...page.items], [] as Pago[]),
    );
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
