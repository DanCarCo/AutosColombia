import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { EMPTY, Observable, expand, reduce, throwError, timeout } from 'rxjs';
import { Cliente, ClienteActualizar, ClienteCrear, ClientesPagina } from '../models/cliente';

import { API_BASE_URL } from './api.service';

@Injectable({ providedIn: 'root' })
export class ClientesService {
  private readonly http = inject(HttpClient);
  private readonly base = inject(API_BASE_URL);
  private readonly clients = `${this.base}/clientes`;

  list(offset: number, limit: number) {
    return this.http
      .get<ClientesPagina>(this.clients, { params: { offset, limit } })
      .pipe(timeout(15000));
  }
  get(id: number) {
    return this.http.get<Cliente>(`${this.clients}/${id}`).pipe(timeout(15000));
  }
  create(data: ClienteCrear) {
    return this.http.post<Cliente>(this.clients, data).pipe(timeout(15000));
  }
  update(id: number, data: ClienteActualizar) {
    return this.http.patch<Cliente>(`${this.clients}/${id}`, data).pipe(timeout(15000));
  }
  delete(id: number) {
    return this.http.delete<void>(`${this.clients}/${id}`).pipe(timeout(15000));
  }

  // Catálogo completo para selectores (p. ej. el formulario de vehículos).
  todos(): Observable<Cliente[]> {
    const cargar = (offset: number) => this.list(offset, 100);
    return cargar(0).pipe(
      expand((page) => {
        const next = page.offset + page.items.length;
        if (next >= page.total) return EMPTY;
        if (!page.items.length)
          return throwError(() => new Error('Catálogo incompleto. Recarga las opciones.'));
        return cargar(next);
      }),
      reduce((items, page) => [...items, ...page.items], [] as Cliente[]),
    );
  }
}
