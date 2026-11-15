import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Mensualidades } from './mensualidades';

describe('Mensualidades (RF-14)', () => {
  let fixture: ComponentFixture<Mensualidades>;
  let http: HttpTestingController;
  const vehiculo = {
    id: 7,
    placa: 'ABC123',
    color: 'Rojo',
    modelo: 2021,
    marca: 'Mazda',
    tipo: 'AUTOMOVIL',
    cliente_id: 1,
  };
  const pago = {
    id: 1,
    vehiculo_id: 7,
    operador_id: 1,
    monto: '250000.00',
    periodo_inicio: '2026-11-01',
    periodo_fin: '2026-11-30',
    fecha_pago: '2026-11-01T10:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Mensualidades],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(Mensualidades);
    fixture.detectChanges();
    http
      .expectOne('/vehiculos?offset=0&limit=100')
      .flush({ items: [vehiculo], total: 1, offset: 0, limit: 100 });
    http
      .expectOne('/pagos?offset=0&limit=100')
      .flush({ items: [], total: 0, offset: 0, limit: 100 });
  });
  afterEach(() => http.verify());

  it('registra la mensualidad sin enviar monto (lo calcula el servidor)', () => {
    const c = fixture.componentInstance;
    c.form.controls.vehiculo_id.setValue(7);
    c.registrar();
    const req = http.expectOne({ method: 'POST', url: '/pagos' });
    expect(req.request.body).toEqual({ vehiculo_id: 7 });
    expect(Object.keys(req.request.body)).not.toContain('monto');
    req.flush(pago);
    http
      .expectOne('/pagos?offset=0&limit=100')
      .flush({ items: [pago], total: 1, offset: 0, limit: 100 });
    expect(c.success()).toContain('ABC123');
    expect(c.estado()?.vigente).toBe(true);
  });

  it('exige seleccionar un vehículo antes de registrar', () => {
    const c = fixture.componentInstance;
    c.registrar();
    http.expectNone('/pagos');
    expect(c.error()).toContain('Selecciona el vehículo');
  });

  it('informa cuando el vehículo no tiene mensualidad vigente', () => {
    const c = fixture.componentInstance;
    c.form.controls.vehiculo_id.setValue(7);
    c.consultar();
    http
      .expectOne('/vehiculos/7/mensualidad')
      .flush({ vehiculo_id: 7, vigente: false, pago: null });
    expect(c.estado()?.vigente).toBe(false);
  });

  it('pide iniciar sesión ante un 401', () => {
    const c = fixture.componentInstance;
    c.form.controls.vehiculo_id.setValue(7);
    c.registrar();
    http
      .expectOne({ method: 'POST', url: '/pagos' })
      .flush({ detail: 'x' }, { status: 401, statusText: 'No autorizado' });
    expect(c.error()).toContain('Inicia sesión');
  });
});
