import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
  });
  afterEach(() => localStorage.clear());

  it('permite el acceso con sesión iniciada', () => {
    localStorage.setItem(
      'autos-colombia.sesion',
      JSON.stringify({
        access_token: 't',
        token_type: 'bearer',
        expira_minutos: 480,
        operador: { id: 1, nombre: 'Ana', telefono: '001', usuario: 'ana', turno: 'DIA' },
      }),
    );
    const resultado = TestBed.runInInjectionContext(() =>
      authGuard({} as never, { url: '/control-acceso' } as never),
    );
    expect(resultado).toBe(true);
  });

  it('redirige a /login con la ruta pedida cuando no hay sesión', () => {
    const resultado = TestBed.runInInjectionContext(() =>
      authGuard({} as never, { url: '/control-acceso' } as never),
    ) as UrlTree;
    const router = TestBed.inject(Router);
    expect(router.serializeUrl(resultado)).toBe('/login?volver=%2Fcontrol-acceso');
  });
});
