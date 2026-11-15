import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';
import { Rol } from '../models/operador';
import { rolGuard } from './rol.guard';

function guardarSesion(rol: Rol): void {
  localStorage.setItem(
    'autos-colombia.sesion',
    JSON.stringify({
      access_token: 't',
      token_type: 'bearer',
      expira_minutos: 480,
      operador: { id: 1, nombre: 'Ana', telefono: '001', usuario: 'ana', turno: 'DIA', rol },
    }),
  );
}

describe('rolGuard', () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
  });
  afterEach(() => localStorage.clear());

  const ejecutar = (...roles: Rol[]) =>
    TestBed.runInInjectionContext(() =>
      rolGuard(...roles)({} as never, { url: '/gestion/celdas' } as never),
    );

  it('permite el acceso cuando el rol coincide', () => {
    guardarSesion('ADMINISTRADOR');
    expect(ejecutar('ADMINISTRADOR')).toBe(true);
  });

  it('redirige a Inicio cuando el rol no corresponde', () => {
    guardarSesion('OPERADOR');
    const resultado = ejecutar('ADMINISTRADOR') as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(resultado)).toBe('/');
  });

  it('redirige a /login con la ruta pedida cuando no hay sesión', () => {
    const resultado = ejecutar('ADMINISTRADOR') as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(resultado)).toBe('/login?volver=%2Fgestion%2Fceldas');
  });
});
