import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, ValidatorFn, Validators } from '@angular/forms';
import { Celda } from '../models/celda';
import { EstadoVehiculo } from '../models/estancia';
import { AuthService } from '../services/auth.service';
import { EstanciasService } from '../services/estancias.service';

const nonBlank: ValidatorFn = (c) =>
  typeof c.value === 'string' && c.value.trim() ? null : { required: true };
const placa = (value: string) => value.trim().toUpperCase();

@Component({
  selector: 'app-control-acceso',
  imports: [ReactiveFormsModule],
  templateUrl: './control-acceso.html',
  styleUrls: ['./control-acceso.css', '../shared/gestion-tema.css'],
})
export class ControlAcceso {
  private readonly api = inject(EstanciasService);
  private readonly fb = inject(FormBuilder);
  private readonly destroy = inject(DestroyRef);
  readonly auth = inject(AuthService);
  private version = 0;
  readonly entrada = this.fb.group({
    placa: this.fb.nonNullable.control('', nonBlank),
    celda_id: this.fb.control<number | null>(null, Validators.required),
  });
  readonly consulta = this.fb.group({
    placa: this.fb.nonNullable.control('', nonBlank),
  });
  readonly cambioCelda = this.fb.group({
    placa: this.fb.nonNullable.control('', nonBlank),
    celda_id: this.fb.control<number | null>(null, Validators.required),
  });
  readonly celdas = signal<Celda[]>([]);
  readonly catalogLoading = signal(false);
  readonly catalogError = signal('');
  readonly saving = signal(false);
  readonly querying = signal(false);
  readonly movingCell = signal(false);
  readonly busy = computed(() => this.saving() || this.querying() || this.movingCell());
  readonly estado = signal<EstadoVehiculo | null>(null);
  readonly errorEntrada = signal('');
  readonly errorConsulta = signal('');
  readonly exitoEntrada = signal('');
  readonly exitoSalida = signal('');
  readonly errorCambioCelda = signal('');
  readonly exitoCambioCelda = signal('');

  constructor() {
    this.consulta.controls.placa.valueChanges
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe(() => {
        this.version++;
        this.estado.set(null);
        this.errorConsulta.set('');
        this.exitoSalida.set('');
      });
    this.cargarCatalogos();
  }

  cargarCatalogos(): void {
    if (this.catalogLoading() || this.saving()) return;
    this.catalogLoading.set(true);
    this.catalogError.set('');
    this.entrada.controls.celda_id.reset();
    this.cambioCelda.controls.celda_id.reset();
    this.api
      .celdas()
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({
        next: (data) => {
          this.celdas.set(data);
          this.catalogLoading.set(false);
        },
        error: () => {
          this.catalogLoading.set(false);
          this.celdas.set([]);
          this.catalogError.set(
            'No se pudieron cargar todas las celdas. Reintenta actualizar catálogos.',
          );
        },
      });
  }

  registrarEntrada(): void {
    if (this.busy() || this.catalogLoading() || this.catalogError()) return;
    this.entrada.markAllAsTouched();
    if (this.entrada.invalid) return;
    const raw = this.entrada.getRawValue();
    const data = { placa: placa(raw.placa), celda_id: raw.celda_id! };
    const codigo =
      this.celdas().find((c) => c.id === data.celda_id)?.codigo ?? String(data.celda_id);
    this.entrada.controls.placa.setValue(data.placa);
    this.saving.set(true);
    this.errorEntrada.set('');
    this.exitoEntrada.set('');
    this.version++;
    this.estado.set(null);
    this.api
      .entrada(data)
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({
        next: (result) => {
          this.saving.set(false);
          this.exitoEntrada.set(
            `Entrada registrada: ${data.placa}, celda ${codigo}, ${this.fecha(result.entrada)}.`,
          );
        },
        error: (error) => {
          this.saving.set(false);
          this.errorEntrada.set(this.mensaje(error));
        },
      });
  }

  buscar(): void {
    if (this.busy()) return;
    this.consulta.controls.placa.markAsTouched();
    if (this.consulta.controls.placa.invalid) return;
    const value = placa(this.consulta.controls.placa.value);
    this.consulta.controls.placa.setValue(value, { emitEvent: false });
    const version = ++this.version;
    this.estado.set(null);
    this.errorConsulta.set('');
    this.querying.set(true);
    this.api
      .consultar(value)
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({
        next: (result) => {
          this.querying.set(false);
          if (version === this.version) this.estado.set(result);
        },
        error: (error) => {
          this.querying.set(false);
          if (version === this.version)
            this.errorConsulta.set(
              error.status === 404 ? 'Vehículo no registrado.' : this.mensaje(error),
            );
        },
      });
  }

  registrarSalida(): void {
    if (this.busy()) return;
    const state = this.estado();
    const value = placa(this.consulta.controls.placa.value);
    if (!state?.estancia || !state.esta_dentro || state.vehiculo.placa !== value) return;
    const version = this.version;
    this.saving.set(true);
    this.errorConsulta.set('');
    this.exitoSalida.set('');
    this.api
      .salida({ placa: value })
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({
        next: (result) => {
          this.saving.set(false);
          this.estado.set(null);
          if (version !== this.version) return;
          this.exitoSalida.set(
            `Salida registrada: ${value}, celda ${state.estancia!.celda.codigo}, ${this.fecha(result.salida!)}.`,
          );
          this.buscar();
        },
        error: (error) => {
          this.saving.set(false);
          this.estado.set(null);
          if (version === this.version)
            this.errorConsulta.set(
              this.mensaje(error) + ' Consulta nuevamente antes de confirmar otra salida.',
            );
        },
      });
  }

  // RF-11: corrige la celda de un vehículo que quedó en una celda equivocada.
  cambiarCelda(): void {
    if (this.busy() || this.catalogLoading() || this.catalogError()) return;
    this.cambioCelda.markAllAsTouched();
    if (this.cambioCelda.invalid) return;
    const raw = this.cambioCelda.getRawValue();
    const data = { placa: placa(raw.placa), celda_id: raw.celda_id! };
    const codigo =
      this.celdas().find((c) => c.id === data.celda_id)?.codigo ?? String(data.celda_id);
    this.cambioCelda.controls.placa.setValue(data.placa);
    this.movingCell.set(true);
    this.errorCambioCelda.set('');
    this.exitoCambioCelda.set('');
    this.api
      .cambiarCelda(data)
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({
        next: () => {
          this.movingCell.set(false);
          this.exitoCambioCelda.set(`Vehículo ${data.placa} movido a la celda ${codigo}.`);
          if (placa(this.consulta.controls.placa.value) === data.placa) this.buscar();
        },
        error: (error) => {
          this.movingCell.set(false);
          this.errorCambioCelda.set(this.mensaje(error));
        },
      });
  }

  fecha(value: string): string {
    return (
      new Intl.DateTimeFormat('es-CO', {
        timeZone: 'America/Bogota',
        dateStyle: 'medium',
        timeStyle: 'medium',
      }).format(new Date(value)) + ' (Bogotá)'
    );
  }

  private mensaje(error: HttpErrorResponse): string {
    if (error.status === 401) return 'Tu sesión expiró o no es válida. Inicia sesión de nuevo.';
    if ([402, 404, 409].includes(error.status) && typeof error.error?.detail === 'string')
      return error.error.detail;
    if (error.status === 422)
      return 'Datos inválidos. Revisa la placa y selecciona una celda válida.';
    return 'No se pudo conectar con el servicio. Consulta el vehículo antes de reintentar: la operación podría haberse completado.';
  }
}
