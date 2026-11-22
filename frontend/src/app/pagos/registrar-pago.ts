import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { Cliente } from '../models/cliente';
import { MensualidadEstado, Pago } from '../models/pago';
import { Vehiculo } from '../models/vehiculo';
import { ApiService } from '../services/api.service';
import { AuthService } from '../services/auth.service';
import { ClientesService } from '../services/clientes.service';
import { PagosService } from '../services/pagos.service';
import { formatoCop } from '../shared/formato';

// RF-14 y RF-19 (marco 26 de Figma, adaptado): registrar el pago en efectivo de una mensualidad.
// El valor y el periodo los calcula el servidor al confirmar; esta pantalla nunca los envía.
@Component({
  selector: 'app-registrar-pago',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './registrar-pago.html',
  styleUrls: ['../clientes/clientes.css', '../shared/gestion-tema.css', './pagos.css'],
})
export class RegistrarPago {
  private readonly pagosApi = inject(PagosService);
  private readonly vehiculosApi = inject(ApiService);
  private readonly clientesApi = inject(ClientesService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly fb = inject(FormBuilder);
  readonly auth = inject(AuthService);
  readonly formatoCop = formatoCop;

  readonly form = this.fb.group({
    vehiculo_id: this.fb.control<number | null>(null, Validators.required),
  });
  readonly vehiculos = signal<Vehiculo[]>([]);
  private readonly clientes = signal<Cliente[]>([]);
  readonly estado = signal<MensualidadEstado | null>(null);
  readonly pagado = signal<Pago | null>(null);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly busy = computed(() => this.loading() || this.saving());
  readonly error = signal('');
  private readonly vehiculoId = signal<number | null>(null);

  readonly vehiculo = computed(
    () => this.vehiculos().find((v) => v.id === this.vehiculoId()) ?? null,
  );
  readonly cliente = computed(() => {
    const v = this.vehiculo();
    return v ? (this.clientes().find((c) => c.id === v.cliente_id) ?? null) : null;
  });

  constructor() {
    this.cargar();
    this.form.controls.vehiculo_id.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((id) => {
        this.vehiculoId.set(id);
        this.estado.set(null);
        this.pagado.set(null);
        this.error.set('');
        if (id !== null) this.consultar(id);
      });
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set('');
    forkJoin({ vehiculos: this.vehiculosApi.todos(), clientes: this.clientesApi.todos() })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ vehiculos, clientes }) => {
          this.loading.set(false);
          this.vehiculos.set(vehiculos);
          this.clientes.set(clientes);
        },
        error: () => {
          this.loading.set(false);
          this.error.set('No se pudieron cargar los vehículos. Actualiza e intenta de nuevo.');
        },
      });
  }

  private consultar(id: number): void {
    this.pagosApi
      .estadoMensualidad(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (estado) => {
          if (this.vehiculoId() === id) this.estado.set(estado);
        },
        error: (error: HttpErrorResponse) => this.error.set(this.mensaje(error)),
      });
  }

  confirmar(): void {
    if (this.busy()) return;
    this.form.markAllAsTouched();
    const { vehiculo_id } = this.form.getRawValue();
    if (vehiculo_id === null) {
      this.error.set('Selecciona el vehículo al que corresponde el pago.');
      return;
    }
    this.saving.set(true);
    this.error.set('');
    this.pagado.set(null);
    this.pagosApi
      .registrar({ vehiculo_id })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (pago) => {
          this.saving.set(false);
          this.pagado.set(pago);
          this.estado.set({ vehiculo_id: pago.vehiculo_id, vigente: true, pago });
        },
        error: (error: HttpErrorResponse) => {
          this.saving.set(false);
          this.error.set(this.mensaje(error));
        },
      });
  }

  cancelar(): void {
    this.router.navigateByUrl('/gestion/pagos');
  }

  private mensaje(error: HttpErrorResponse): string {
    if (error.status === 401) return 'Inicia sesión para registrar pagos.';
    if (error.status === 404) return 'El vehículo ya no existe. Actualiza el listado.';
    if (error.status === 422) return 'Revisa los datos: el vehículo no es válido.';
    return 'No se pudo conectar con el servicio. Comprueba la conexión e intenta de nuevo.';
  }
}
