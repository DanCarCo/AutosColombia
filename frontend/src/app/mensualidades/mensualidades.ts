import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { EMPTY, expand, reduce } from 'rxjs';
import { MensualidadEstado, Pago } from '../models/pago';
import { Vehiculo } from '../models/vehiculo';
import { ApiService } from '../services/api.service';
import { PagosService } from '../services/pagos.service';

// RF-14: registro de mensualidades y consulta de vigencia. El monto lo calcula
// el servidor según el tipo de vehículo; esta pantalla nunca lo envía.
@Component({
  selector: 'app-mensualidades',
  imports: [ReactiveFormsModule],
  templateUrl: './mensualidades.html',
  styleUrls: ['../clientes/clientes.css', '../shared/gestion-tema.css'],
})
export class Mensualidades {
  private readonly pagosApi = inject(PagosService);
  private readonly vehiculosApi = inject(ApiService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly fb = inject(FormBuilder);

  readonly form = this.fb.group({
    vehiculo_id: this.fb.control<number | null>(null, Validators.required),
  });
  readonly vehiculos = signal<Vehiculo[]>([]);
  readonly pagos = signal<Pago[]>([]);
  readonly total = signal(0);
  readonly estado = signal<MensualidadEstado | null>(null);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly busy = computed(() => this.loading() || this.saving());
  readonly error = signal('');
  readonly success = signal('');

  constructor() {
    this.cargar();
    this.form.controls.vehiculo_id.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((id) => {
        this.estado.set(null);
        this.success.set('');
        // Trae la fecha de la mensualidad vigente apenas se elige el vehículo.
        if (id !== null) this.consultar();
      });
  }

  placaDe(vehiculoId: number): string {
    return this.vehiculos().find((v) => v.id === vehiculoId)?.placa ?? `#${vehiculoId}`;
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set('');
    this.vehiculosApi
      .list(0, 100)
      .pipe(
        expand((page) => {
          const next = page.offset + page.items.length;
          return next >= page.total || !page.items.length
            ? EMPTY
            : this.vehiculosApi.list(next, 100);
        }),
        reduce((items, page) => [...items, ...page.items], [] as Vehiculo[]),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (items) => this.vehiculos.set(items),
        error: () => {
          this.loading.set(false);
          this.error.set('No se pudieron cargar los vehículos. Actualiza e intenta de nuevo.');
        },
        complete: () => this.cargarPagos(),
      });
  }

  private cargarPagos(): void {
    this.pagosApi
      .listar(0, 100)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (page) => {
          this.loading.set(false);
          this.pagos.set(page.items);
          this.total.set(page.total);
        },
        error: (error: HttpErrorResponse) => {
          this.loading.set(false);
          this.error.set(this.mensaje(error));
        },
      });
  }

  consultar(): void {
    const id = this.form.controls.vehiculo_id.value;
    if (id === null || this.busy()) {
      this.form.controls.vehiculo_id.markAsTouched();
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.pagosApi
      .estadoMensualidad(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (estado) => {
          this.loading.set(false);
          this.estado.set(estado);
        },
        error: (error: HttpErrorResponse) => {
          this.loading.set(false);
          this.error.set(this.mensaje(error));
        },
      });
  }

  registrar(): void {
    if (this.busy()) return;
    this.form.markAllAsTouched();
    const { vehiculo_id } = this.form.getRawValue();
    if (vehiculo_id === null) {
      this.error.set('Selecciona el vehículo al que corresponde la mensualidad.');
      return;
    }
    this.saving.set(true);
    this.error.set('');
    this.success.set('');
    this.pagosApi
      .registrar({ vehiculo_id })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (pago) => {
          this.saving.set(false);
          this.success.set(
            `Mensualidad registrada para ${this.placaDe(pago.vehiculo_id)}: ${pago.periodo_inicio} a ${pago.periodo_fin}.`,
          );
          this.estado.set({ vehiculo_id: pago.vehiculo_id, vigente: true, pago });
          this.cargarPagos();
        },
        error: (error: HttpErrorResponse) => {
          this.saving.set(false);
          this.error.set(this.mensaje(error));
        },
      });
  }

  private mensaje(error: HttpErrorResponse): string {
    if (error.status === 401) return 'Inicia sesión para registrar mensualidades.';
    if (error.status === 404) return 'El vehículo ya no existe. Actualiza el listado.';
    if (error.status === 422) return 'Revisa los datos: la fecha o el vehículo no son válidos.';
    return 'No se pudo conectar con el servicio. Comprueba la conexión e intenta de nuevo.';
  }
}
