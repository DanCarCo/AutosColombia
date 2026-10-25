import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;
  const respuesta = {
    access_token: 'token-de-prueba',
    token_type: 'bearer',
    expira_minutos: 480,
    operador: { id: 1, nombre: 'Prueba', telefono: '001', usuario: 'prueba', turno: 'DIA' as const },
  };

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('empieza sin sesión', () => {
    expect(service.estaAutenticado()).toBe(false);
    expect(service.token()).toBeNull();
    expect(service.operador()).toBeNull();
  });

  it('guarda el token y el operador al iniciar sesión, y los persiste', () => {
    service.login({ usuario: 'prueba', password: 'clave' }).subscribe();
    const request = http.expectOne('/auth/login');
    expect(request.request.body).toEqual({ usuario: 'prueba', password: 'clave' });
    request.flush(respuesta);
    expect(service.estaAutenticado()).toBe(true);
    expect(service.token()).toBe('token-de-prueba');
    expect(service.operador()?.usuario).toBe('prueba');
    expect(JSON.parse(localStorage.getItem('autos-colombia.sesion')!)).toEqual(respuesta);
  });

  it('restaura la sesión guardada al crear una nueva instancia del servicio', () => {
    localStorage.setItem('autos-colombia.sesion', JSON.stringify(respuesta));
    // El servicio lee localStorage solo al construirse: fuerza una instancia nueva.
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    const otra = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
    expect(otra.estaAutenticado()).toBe(true);
    expect(otra.token()).toBe('token-de-prueba');
  });

  it('cierra sesión y limpia el almacenamiento', () => {
    service.login({ usuario: 'prueba', password: 'clave' }).subscribe();
    http.expectOne('/auth/login').flush(respuesta);
    service.logout();
    expect(service.estaAutenticado()).toBe(false);
    expect(localStorage.getItem('autos-colombia.sesion')).toBeNull();
  });
});
