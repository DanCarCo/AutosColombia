import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let backend: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    backend = TestBed.inject(HttpTestingController);
  });
  afterEach(() => {
    backend.verify();
    localStorage.clear();
  });

  it('no agrega Authorization sin sesión iniciada', () => {
    http.get('/celdas').subscribe();
    const request = backend.expectOne('/celdas');
    expect(request.request.headers.has('Authorization')).toBe(false);
    request.flush({});
  });

  it('agrega el token cuando hay sesión iniciada', () => {
    localStorage.setItem(
      'autos-colombia.sesion',
      JSON.stringify({
        access_token: 'token-de-prueba',
        token_type: 'bearer',
        expira_minutos: 480,
        operador: { id: 1, nombre: 'Ana', telefono: '001', usuario: 'ana', turno: 'DIA' },
      }),
    );
    http.get('/estancias/vehiculo/ABC123').subscribe();
    const request = backend.expectOne('/estancias/vehiculo/ABC123');
    expect(request.request.headers.get('Authorization')).toBe('Bearer token-de-prueba');
    request.flush({});
  });
});
