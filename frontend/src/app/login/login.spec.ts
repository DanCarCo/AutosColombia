import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter, Router } from '@angular/router';
import { vi } from 'vitest';
import { Login } from './login';

describe('Inicio de sesión', () => {
  let fixture: ComponentFixture<Login>;
  let component: Login;
  let http: HttpTestingController;
  let router: Router;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: { get: () => null } } } },
      ],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });
  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('no envía la solicitud con campos vacíos', () => {
    component.entrar();
    http.expectNone('/auth/login');
    expect(component.form.controls.usuario.touched).toBe(true);
    expect(component.form.controls.password.touched).toBe(true);
  });

  it('inicia sesión y navega a Control de acceso por defecto', () => {
    component.form.setValue({ usuario: ' ana ', password: 'clave' });
    component.entrar();
    const request = http.expectOne('/auth/login');
    expect(request.request.body).toEqual({ usuario: 'ana', password: 'clave' });
    request.flush({
      access_token: 'token',
      token_type: 'bearer',
      expira_minutos: 480,
      operador: { id: 1, nombre: 'Ana', telefono: '001', usuario: 'ana', turno: 'DIA' },
    });
    expect(router.navigateByUrl).toHaveBeenCalledWith('/control-acceso');
  });

  it('muestra 401 sin revelar cuál campo falló', () => {
    component.form.setValue({ usuario: 'ana', password: 'mala' });
    component.entrar();
    http
      .expectOne('/auth/login')
      .flush({ detail: 'Usuario o contraseña incorrectos.' }, { status: 401, statusText: 'Unauthorized' });
    expect(component.error()).toBe('Usuario o contraseña incorrectos.');
    expect(component.saving()).toBe(false);
  });

  it('vuelve a la ruta pedida con el parámetro volver', async () => {
    await TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [Login],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: { get: () => '/gestion/vehiculos' } } },
        },
      ],
    });
    await TestBed.compileComponents();
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    component.form.setValue({ usuario: 'ana', password: 'clave' });
    component.entrar();
    http.expectOne('/auth/login').flush({
      access_token: 'token',
      token_type: 'bearer',
      expira_minutos: 480,
      operador: { id: 1, nombre: 'Ana', telefono: '001', usuario: 'ana', turno: 'DIA' },
    });
    expect(router.navigateByUrl).toHaveBeenCalledWith('/gestion/vehiculos');
  });
});
