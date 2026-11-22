import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RegistrarPago } from './registrar-pago';

describe('RegistrarPago (RF-14, RF-19)', () => {
  let fixture: ComponentFixture<RegistrarPago>;
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
  const cliente = { id: 1, nombre: 'Juan Pérez', documento: '1', telefono: '3' };
  const pago = {
    id: 5,
    vehiculo_id: 7,
    operador_id: 1,
    monto: '250000.00',
    periodo_inicio: '2026-12-22',
    periodo_fin: '2027-01-21',
    fecha_pago: '2026-11-22T10:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RegistrarPago],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(RegistrarPago);
    fixture.detectChanges();
    http
      .expectOne('/vehiculos?offset=0&limit=100')
      .flush({ items: [vehiculo], total: 1, offset: 0, limit: 100 });
    http
      .expectOne('/clientes?offset=0&limit=100')
      .flush({ items: [cliente], total: 1, offset: 0, limit: 100 });
    fixture.detectChanges();
  });
  afterEach(() => http.verify());

  it('al elegir el vehículo muestra su cliente y su mensualidad actual', () => {
    const c = fixture.componentInstance;
    c.form.controls.vehiculo_id.setValue(7);
    http
      .expectOne('/vehiculos/7/mensualidad')
      .flush({ vehiculo_id: 7, vigente: false, pago: null });
    fixture.detectChanges();
    expect(c.cliente()?.nombre).toBe('Juan Pérez');
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Sin mensualidad vigente');
    expect(texto).toContain('Efectivo');
  });

  it('confirma el pago enviando solo el vehículo (el valor y el periodo los calcula el servidor)', () => {
    const c = fixture.componentInstance;
    c.form.controls.vehiculo_id.setValue(7);
    http
      .expectOne('/vehiculos/7/mensualidad')
      .flush({ vehiculo_id: 7, vigente: false, pago: null });
    c.confirmar();
    const req = http.expectOne({ method: 'POST', url: '/pagos' });
    expect(req.request.body).toEqual({ vehiculo_id: 7 });
    req.flush(pago);
    fixture.detectChanges();
    expect(c.pagado()?.id).toBe(5);
    expect(c.estado()?.vigente).toBe(true);
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('PAG-5');
    expect(texto).toContain('2026-12-22 a 2027-01-21');
  });

  it('exige elegir un vehículo antes de confirmar', () => {
    const c = fixture.componentInstance;
    c.confirmar();
    http.expectNone('/pagos');
    expect(c.error()).toContain('Selecciona el vehículo');
  });

  it('informa si el vehículo ya no existe', () => {
    const c = fixture.componentInstance;
    c.form.controls.vehiculo_id.setValue(7);
    http
      .expectOne('/vehiculos/7/mensualidad')
      .flush({ vehiculo_id: 7, vigente: false, pago: null });
    c.confirmar();
    http
      .expectOne({ method: 'POST', url: '/pagos' })
      .flush({ detail: 'x' }, { status: 404, statusText: 'Not Found' });
    expect(c.error()).toContain('ya no existe');
    expect(c.pagado()).toBeNull();
  });
});
