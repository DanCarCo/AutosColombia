import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ResumenReporte } from '../models/pago';
import { PagosService } from '../services/pagos.service';

// RF-15: resumen de celdas disponibles/totales y clientes registrados.
@Component({
  selector: 'app-reportes',
  templateUrl: './reportes.html',
  styleUrls: ['../clientes/clientes.css', '../shared/gestion-tema.css'],
})
export class Reportes {
  private readonly api = inject(PagosService);
  private readonly destroyRef = inject(DestroyRef);
  readonly resumen = signal<ResumenReporte | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set('');
    this.api
      .resumen()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          this.loading.set(false);
          this.resumen.set(data);
        },
        error: () => {
          this.loading.set(false);
          this.error.set('No se pudo cargar el resumen. Comprueba la conexión e intenta de nuevo.');
        },
      });
  }
}
