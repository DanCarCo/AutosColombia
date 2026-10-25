import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ControlAcceso } from './control-acceso';

describe('Control de acceso', () => {
  let http: HttpTestingController;
  let c: ControlAcceso;
  const celda = { id: 2, codigo: 'TEST-C', tipo: 'Libre' };
  const stay = {
    id: 3,
    vehiculo_id: 1,
    celda_id: 2,
    entrada: '2026-10-19T15:00:00Z',
    salida: null,
    operador_entrada_id: 4,
    operador_salida_id: null,
  };
  const state = {
    vehiculo: {
      id: 1,
      placa: 'TEST-A',
      marca: 'Prueba',
      color: 'Azul',
      modelo: 2026,
      tipo: 'MOTO',
      cliente_id: 7,
    },
    esta_dentro: true,
    estancia: { ...stay, celda },
  };
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ControlAcceso],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
    c = TestBed.createComponent(ControlAcceso).componentInstance;
    http
      .expectOne('/celdas?offset=0&limit=100')
      .flush({ items: [celda], total: 2, offset: 0, limit: 100 });
    http
      .expectOne('/celdas?offset=1&limit=100')
      .flush({ items: [{ ...celda, id: 5 }], total: 2, offset: 1, limit: 100 });
  });
  afterEach(() => http.verify());

  it('recorre todas las páginas y registra entrada normalizada sin fecha ni doble envío', () => {
    expect(c.celdas().length).toBe(2);
    c.entrada.setValue({ placa: ' test-a ', celda_id: 2 });
    c.registrarEntrada();
    c.registrarEntrada();
    const req = http.expectOne('/estancias/entrada');
    expect(req.request.body).toEqual({ placa: 'TEST-A', celda_id: 2 });
    req.flush(stay);
    expect(c.exitoEntrada()).toContain('TEST-C');
    expect(c.exitoEntrada()).toContain('Bogotá');
  });
  it('rechaza blancos y muestra los conflictos de ocupación, mensualidad y sesión', () => {
    c.entrada.setValue({ placa: ' ', celda_id: 2 });
    c.registrarEntrada();
    http.expectNone('/estancias/entrada');
    for (const [status, detail] of [
      [409, 'El vehículo ya está dentro.'],
      [409, 'La celda está ocupada.'],
      [402, 'El vehículo no tiene mensualidad vigente.'],
      [401, 'Token inválido.'],
    ] as const) {
      c.entrada.controls.placa.setValue('TEST-A');
      c.registrarEntrada();
      http.expectOne('/estancias/entrada').flush({ detail }, { status, statusText: 'Error' });
      if (status === 401) expect(c.errorEntrada()).toContain('sesión');
      else expect(c.errorEntrada()).toBe(detail);
      expect(c.saving()).toBe(false);
    }
  });
  it('descarta respuestas antiguas y no permite salida al cambiar de placa', () => {
    c.consulta.setValue({ placa: 'TEST-A' });
    c.buscar();
    c.consulta.controls.placa.setValue('TEST-B');
    http.expectOne('/estancias/vehiculo/TEST-A').flush(state);
    expect(c.estado()).toBeNull();
    c.registrarSalida();
    http.expectNone('/estancias/salida');
    c.consulta.controls.placa.setValue('TEST-A');
    c.buscar();
    http.expectOne('/estancias/vehiculo/TEST-A').flush(state);
    c.consulta.controls.placa.setValue('TEST-B');
    expect(c.estado()).toBeNull();
  });
  it('consulta antes de salir, envía solo la placa y consulta fuera tras cerrar', () => {
    c.consulta.setValue({ placa: 'test-a' });
    c.buscar();
    http.expectOne('/estancias/vehiculo/TEST-A').flush(state);
    c.registrarSalida();
    c.registrarSalida();
    const req = http.expectOne('/estancias/salida');
    expect(req.request.body).toEqual({ placa: 'TEST-A' });
    req.flush({ ...stay, salida: '2026-10-19T16:00:00Z', operador_salida_id: 4 });
    http
      .expectOne('/estancias/vehiculo/TEST-A')
      .flush({ ...state, esta_dentro: false, estancia: null });
    expect(c.estado()?.esta_dentro).toBe(false);
    expect(c.exitoSalida()).toContain('Salida registrada');
  });
  it('distingue no registrado y conexión fallida e invalida salida rechazada', () => {
    c.consulta.setValue({ placa: 'TEST-A' });
    c.buscar();
    http
      .expectOne('/estancias/vehiculo/TEST-A')
      .flush({}, { status: 404, statusText: 'Not Found' });
    expect(c.errorConsulta()).toBe('Vehículo no registrado.');
    c.buscar();
    http.expectOne('/estancias/vehiculo/TEST-A').error(new ProgressEvent('error'));
    expect(c.errorConsulta()).toContain('No se pudo conectar');
    c.buscar();
    http.expectOne('/estancias/vehiculo/TEST-A').flush(state);
    c.registrarSalida();
    http
      .expectOne('/estancias/salida')
      .flush({ detail: 'Sin estancia abierta.' }, { status: 409, statusText: 'Conflict' });
    expect(c.estado()).toBeNull();
    expect(c.errorConsulta()).toContain('Consulta nuevamente');
  });
  it('corrige la celda de un vehículo (RF-11) y refresca la consulta si coincide la placa', () => {
    c.consulta.setValue({ placa: 'TEST-A' });
    c.buscar();
    http.expectOne('/estancias/vehiculo/TEST-A').flush(state);
    c.cambioCelda.setValue({ placa: ' test-a ', celda_id: 5 });
    c.cambiarCelda();
    const req = http.expectOne('/estancias/celda');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ placa: 'TEST-A', celda_id: 5 });
    req.flush({ ...stay, celda_id: 5 });
    expect(c.exitoCambioCelda()).toContain('TEST-A');
    http.expectOne('/estancias/vehiculo/TEST-A').flush({ ...state, estancia: { ...stay, celda_id: 5, celda: { ...celda, id: 5 } } });
  });
  it('muestra el error del servicio al fallar el cambio de celda', () => {
    c.cambioCelda.setValue({ placa: 'TEST-A', celda_id: 2 });
    c.cambiarCelda();
    http
      .expectOne('/estancias/celda')
      .flush({ detail: 'La celda está ocupada.' }, { status: 409, statusText: 'Conflict' });
    expect(c.errorCambioCelda()).toBe('La celda está ocupada.');
  });
  it('interpreta el offset recibido y presenta el mismo instante en Bogotá', () => {
    expect(c.fecha('2026-10-19T15:00:00Z')).toBe(c.fecha('2026-10-19T10:00:00-05:00'));
    expect(c.fecha('2026-10-19T15:00:00Z')).toContain('10:00:00');
  });
});
