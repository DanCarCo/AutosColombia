import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { EMPTY, Observable, expand, reduce, throwError, timeout } from 'rxjs';
import { Celda } from '../models/celda';
import { CambiarCeldaCrear, EntradaCrear, SalidaCrear, Estancia, EstadoVehiculo } from '../models/estancia';
import { API_BASE_URL } from './api.service';
import { CeldasService } from './celdas.service';

interface Pagina<T> {
  items: T[];
  offset: number;
  limit: number;
  total: number;
}

@Injectable({ providedIn: 'root' })
export class EstanciasService {
  private readonly http = inject(HttpClient);
  private readonly base = `${inject(API_BASE_URL)}/estancias`;
  private readonly cells = inject(CeldasService);

  // El operador que actúa se identifica por el token de sesión (RF-16), no por el cuerpo.
  entrada(data: EntradaCrear) {
    return this.http.post<Estancia>(`${this.base}/entrada`, data).pipe(timeout(15000));
  }
  salida(data: SalidaCrear) {
    return this.http.post<Estancia>(`${this.base}/salida`, data).pipe(timeout(15000));
  }
  cambiarCelda(data: CambiarCeldaCrear) {
    return this.http.patch<Estancia>(`${this.base}/celda`, data).pipe(timeout(15000));
  }
  consultar(placa: string) {
    return this.http
      .get<EstadoVehiculo>(`${this.base}/vehiculo/${encodeURIComponent(placa)}`)
      .pipe(timeout(15000));
  }
  celdas(): Observable<Celda[]> {
    return this.todas((offset) => this.cells.list(offset, 100));
  }

  private todas<T>(load: (offset: number) => Observable<Pagina<T>>): Observable<T[]> {
    return load(0).pipe(
      expand((page) => {
        const next = page.offset + page.items.length;
        if (next >= page.total) return EMPTY;
        if (!page.items.length)
          return throwError(() => new Error('Catálogo incompleto. Recarga las opciones.'));
        return load(next);
      }),
      reduce((items, page) => [...items, ...page.items], [] as T[]),
    );
  }
}
