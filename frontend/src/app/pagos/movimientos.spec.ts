import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Pago } from '../models/pago';
import { Movimientos } from './movimientos';

function pagina<T>(items: T[]) {
  return { items, total: items.length, offset: 0, limit: 100 };
}

describe('Movimientos (RF-19)', () => {
  let fixture: ComponentFixture<Movimientos>;
  let http: HttpTestingController;
  const hoy = new Date().toISOString().slice(0, 10);
  const sumarDias = (dias: number) => {
    const d = new Date();
    d.setUTCDate(d.getUTCDate() + dias);
    return d.toISOString().slice(0, 10);
  };
  const vehiculos = [
    {
      id: 1,
      placa: 'ABC123',
      color: 'Rojo',
      modelo: 2021,
      marca: 'Mazda',
      tipo: 'AUTOMOVIL',
      cliente_id: 1,
    },
    {
      id: 2,
      placa: 'MOT001',
      color: 'Negro',
      modelo: 2022,
      marca: 'Yamaha',
      tipo: 'MOTO',
      cliente_id: 2,
    },
  ];
  const clientes = [
    { id: 1, nombre: 'Juan Pérez', documento: '1', telefono: '3' },
    { id: 2, nombre: 'María Torres', documento: '2', telefono: '3' },
  ];
  const pago = (
    id: number,
    vehiculo_id: number,
    monto: string,
    inicio: string,
    fin: string,
  ): Pago => ({
    id,
    vehiculo_id,
    operador_id: 1,
    monto,
    periodo_inicio: inicio,
    periodo_fin: fin,
    fecha_pago: '2026-11-20T15:00:00Z',
  });

  function crear(pagos: Pago[]) {
    fixture = TestBed.createComponent(Movimientos);
    fixture.detectChanges();
    http.expectOne('/pagos?offset=0&limit=100').flush(pagina(pagos));
    http.expectOne('/vehiculos?offset=0&limit=100').flush(pagina(vehiculos));
    http.expectOne('/clientes?offset=0&limit=100').flush(pagina(clientes));
    fixture.detectChanges();
    return fixture.componentInstance;
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Movimientos],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());

  const base = () => [
    pago(1, 1, '250000.00', sumarDias(-40), sumarDias(-11)),
    pago(2, 2, '100000.00', sumarDias(-5), sumarDias(24)),
    pago(3, 1, '250000.00', hoy, sumarDias(29)),
  ];

  it('suma lo recaudado, lo separa por tipo y ordena del más reciente al más antiguo', () => {
    const c = crear(base());
    expect(c.total()).toBe(3);
    expect(c.recaudado()).toBe(600000);
    expect(c.porTipo().find((t) => t.tipo === 'MOTO')).toEqual({
      tipo: 'MOTO',
      pagos: 1,
      valor: 100000,
    });
    expect(c.porTipo().find((t) => t.tipo === 'AUTOMOVIL')?.valor).toBe(500000);
    expect(c.visibles().map((m) => m.referencia)).toEqual(['PAG-3', 'PAG-2', 'PAG-1']);
    expect(c.visibles()[0].cliente).toBe('Juan Pérez');
  });

  it('marca cada pago como vigente, vencido o futuro según su periodo', () => {
    const c = crear([...base(), pago(4, 2, '100000.00', sumarDias(3), sumarDias(32))]);
    const estados = Object.fromEntries(c.visibles().map((m) => [m.referencia, m.estado]));
    expect(estados).toEqual({
      'PAG-1': 'Vencida',
      'PAG-2': 'Vigente',
      'PAG-3': 'Vigente',
      'PAG-4': 'Futura',
    });
  });

  it('filtra por placa o cliente, por tipo y por estado, y recalcula los totales', () => {
    const c = crear(base());
    c.filtros.patchValue({ busqueda: 'mot001' });
    expect(c.filtrados().map((m) => m.referencia)).toEqual(['PAG-2']);
    expect(c.recaudado()).toBe(100000);
    c.filtros.patchValue({ busqueda: 'pérez', tipo: '' });
    expect(c.total()).toBe(2);
    c.filtros.patchValue({ busqueda: '', tipo: 'AUTOMOVIL', estado: 'Vencida' });
    expect(c.filtrados().map((m) => m.referencia)).toEqual(['PAG-1']);
    c.limpiar();
    expect(c.total()).toBe(3);
  });

  it('filtra por la fecha de pago en hora de Bogotá', () => {
    const c = crear(base());
    c.filtros.patchValue({ fecha: '2026-11-20' });
    expect(c.total()).toBe(3);
    c.filtros.patchValue({ fecha: '2026-11-21' });
    expect(c.total()).toBe(0);
  });

  it('pagina de 10 en 10 y vuelve a la primera página al filtrar', () => {
    const muchos = Array.from({ length: 12 }, (_, i) =>
      pago(i + 1, 1, '250000.00', sumarDias(-2), sumarDias(27)),
    );
    const c = crear(muchos);
    expect(c.paginas()).toBe(2);
    expect(c.visibles().length).toBe(10);
    expect(c.rango()).toBe('1–10');
    c.irA(2);
    expect(c.visibles().length).toBe(2);
    expect(c.rango()).toBe('11–12');
    c.irA(99);
    expect(c.pagina()).toBe(2);
    c.filtros.patchValue({ busqueda: 'abc' });
    expect(c.pagina()).toBe(1);
  });

  it('genera un CSV con todo lo filtrado y las comillas escapadas', () => {
    const c = crear(base());
    c.filtros.patchValue({ tipo: 'MOTO' });
    const lineas = c.csv().split('\r\n');
    expect(lineas.length).toBe(2);
    expect(lineas[0]).toContain('"Referencia"');
    expect(lineas[1]).toContain('"PAG-2","Mensualidad","MOT001","María Torres"');
    expect(lineas[1]).toContain('"100000","Efectivo"');
  });

  it('muestra un aviso si no se pueden cargar los datos', () => {
    fixture = TestBed.createComponent(Movimientos);
    fixture.detectChanges();
    http.expectOne('/pagos?offset=0&limit=100').error(new ProgressEvent('error'));
    // forkJoin cancela las demás solicitudes al fallar una
    http.match('/vehiculos?offset=0&limit=100');
    http.match('/clientes?offset=0&limit=100');
    fixture.detectChanges();
    expect(fixture.componentInstance.error()).toContain('No se pudieron cargar los movimientos');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('No se pudieron cargar');
  });
});
