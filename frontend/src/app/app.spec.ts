import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';
import { Rol } from './models/operador';

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

async function menu(rol: Rol | null): Promise<string[]> {
  localStorage.clear();
  if (rol) guardarSesion(rol);
  await TestBed.configureTestingModule({
    imports: [App],
    providers: [provideRouter([])],
  }).compileComponents();
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  return Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('nav a')).map(
    (a) => a.textContent?.trim() ?? '',
  );
}

describe('Navegación por rol (RF-16)', () => {
  afterEach(() => localStorage.clear());

  it('sin sesión solo muestra Inicio', async () => {
    expect(await menu(null)).toEqual(['Inicio']);
  }, 20000);

  it('el administrador gestiona operadores, celdas, vehículos y clientes, pero no registra accesos', async () => {
    const links = await menu('ADMINISTRADOR');
    expect(links[0]).toBe('Inicio');
    for (const item of ['Operadores', 'Celdas', 'Vehículos', 'Clientes', 'Mensualidades', 'Reportes']) {
      expect(links).toContain(item);
    }
    expect(links).not.toContain('Control de acceso');
  });

  it('el operador registra accesos, pero no administra usuarios ni celdas', async () => {
    const links = await menu('OPERADOR');
    expect(links[0]).toBe('Inicio');
    for (const item of ['Control de acceso', 'Mensualidades', 'Reportes']) {
      expect(links).toContain(item);
    }
    for (const item of ['Operadores', 'Celdas', 'Vehículos', 'Clientes']) {
      expect(links).not.toContain(item);
    }
  });
});
