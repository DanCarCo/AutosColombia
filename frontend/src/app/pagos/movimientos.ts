import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { Cliente } from '../models/cliente';
import { Pago } from '../models/pago';
import { TIPOS_VEHICULO, TipoVehiculo, Vehiculo } from '../models/vehiculo';
import { diaBogota, fechaHoraBogota, formatoCop } from '../shared/formato';
import { ApiService } from '../services/api.service';
import { ClientesService } from '../services/clientes.service';
import { PagosService } from '../services/pagos.service';

export type EstadoPago = 'Vigente' | 'Vencida' | 'Futura';

export interface Movimiento {
  pago: Pago;
  referencia: string;
  placa: string;
  tipo: TipoVehiculo | '';
  cliente: string;
  estado: EstadoPago;
  valor: number;
}

// RF-19 (marco 25 de Figma, adaptado): historial de pagos con totales, filtros y exportación.
// El sistema solo cobra mensualidades en efectivo, por lo que no hay medios de pago ni saldos.
@Component({
  selector: 'app-movimientos',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './movimientos.html',
  styleUrls: ['../clientes/clientes.css', '../shared/gestion-tema.css', './pagos.css'],
})
export class Movimientos {
  private readonly pagosApi = inject(PagosService);
  private readonly vehiculosApi = inject(ApiService);
  private readonly clientesApi = inject(ClientesService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly fb = inject(FormBuilder);

  readonly tipos = TIPOS_VEHICULO;
  readonly porPagina = 10;
  readonly formatoCop = formatoCop;
  readonly fechaHora = fechaHoraBogota;

  readonly filtros = this.fb.nonNullable.group({
    busqueda: '',
    fecha: '',
    tipo: '',
    estado: '',
  });
  private readonly valoresFiltro = toSignal(this.filtros.valueChanges, {
    initialValue: this.filtros.getRawValue(),
  });

  private readonly movimientos = signal<Movimiento[]>([]);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly pagina = signal(1);

  readonly filtrados = computed(() => {
    const f = this.valoresFiltro();
    const texto = (f.busqueda ?? '').trim().toLowerCase();
    return this.movimientos().filter((m) => {
      if (texto && !`${m.placa} ${m.cliente} ${m.referencia}`.toLowerCase().includes(texto))
        return false;
      if (f.fecha && diaBogota(m.pago.fecha_pago) !== f.fecha) return false;
      if (f.tipo && m.tipo !== f.tipo) return false;
      if (f.estado && m.estado !== f.estado) return false;
      return true;
    });
  });
  readonly total = computed(() => this.filtrados().length);
  readonly paginas = computed(() => Math.max(1, Math.ceil(this.total() / this.porPagina)));
  readonly visibles = computed(() => {
    const inicio = (this.pagina() - 1) * this.porPagina;
    return this.filtrados().slice(inicio, inicio + this.porPagina);
  });
  readonly rango = computed(() => {
    if (!this.total()) return '0';
    const desde = (this.pagina() - 1) * this.porPagina + 1;
    return `${desde}–${desde + this.visibles().length - 1}`;
  });
  readonly recaudado = computed(() => this.filtrados().reduce((suma, m) => suma + m.valor, 0));
  readonly porTipo = computed(() =>
    this.tipos.map((tipo) => {
      const filas = this.filtrados().filter((m) => m.tipo === tipo);
      return { tipo, pagos: filas.length, valor: filas.reduce((s, m) => s + m.valor, 0) };
    }),
  );

  constructor() {
    this.filtros.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.pagina.set(1));
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set('');
    forkJoin({
      pagos: this.pagosApi.todos(),
      vehiculos: this.vehiculosApi.todos(),
      clientes: this.clientesApi.todos(),
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ pagos, vehiculos, clientes }) => {
          this.loading.set(false);
          this.movimientos.set(this.armar(pagos, vehiculos, clientes));
          this.pagina.set(1);
        },
        error: () => {
          this.loading.set(false);
          this.error.set('No se pudieron cargar los movimientos. Actualiza e intenta de nuevo.');
        },
      });
  }

  armar(pagos: Pago[], vehiculos: Vehiculo[], clientes: Cliente[]): Movimiento[] {
    const hoy = new Date().toISOString().slice(0, 10); // misma referencia (UTC) que el servidor
    const vehiculoPorId = new Map(vehiculos.map((v) => [v.id, v]));
    const clientePorId = new Map(clientes.map((c) => [c.id, c]));
    return [...pagos]
      .sort((a, b) => b.id - a.id)
      .map((pago) => {
        const vehiculo = vehiculoPorId.get(pago.vehiculo_id);
        const estado: EstadoPago =
          pago.periodo_inicio > hoy ? 'Futura' : pago.periodo_fin < hoy ? 'Vencida' : 'Vigente';
        return {
          pago,
          referencia: `PAG-${pago.id}`,
          placa: vehiculo?.placa ?? `#${pago.vehiculo_id}`,
          tipo: vehiculo?.tipo ?? '',
          cliente: (vehiculo && clientePorId.get(vehiculo.cliente_id)?.nombre) ?? '—',
          estado,
          valor: Number(pago.monto),
        };
      });
  }

  limpiar(): void {
    this.filtros.reset({ busqueda: '', fecha: '', tipo: '', estado: '' });
  }

  irA(pagina: number): void {
    this.pagina.set(Math.min(Math.max(1, pagina), this.paginas()));
  }

  // CSV de lo filtrado (no solo de la página visible), con comillas escapadas.
  csv(): string {
    const celda = (v: string | number) => `"${String(v).replace(/"/g, '""')}"`;
    const filas = this.filtrados().map((m) =>
      [
        m.referencia,
        'Mensualidad',
        m.placa,
        m.cliente,
        m.pago.periodo_inicio,
        m.pago.periodo_fin,
        m.valor,
        'Efectivo',
        m.estado,
        m.pago.fecha_pago,
      ]
        .map(celda)
        .join(','),
    );
    const cabecera = [
      'Referencia',
      'Concepto',
      'Placa',
      'Cliente',
      'Inicio',
      'Fin',
      'Valor COP',
      'Método',
      'Estado',
      'Fecha de pago',
    ];
    return [cabecera.map(celda).join(','), ...filas].join('\r\n');
  }

  exportarCsv(): void {
    const blob = new Blob(['﻿', this.csv()], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = 'movimientos-pagos.csv';
    enlace.click();
    URL.revokeObjectURL(url);
  }
}
