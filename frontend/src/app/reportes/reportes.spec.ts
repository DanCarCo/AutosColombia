import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Reportes } from './reportes';

describe('Reportes (RF-15)', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Reportes],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());

  it('muestra celdas disponibles, totales y clientes registrados', () => {
    const fixture = TestBed.createComponent(Reportes);
    fixture.detectChanges();
    http
      .expectOne('/reportes/resumen')
      .flush({ celdas_totales: 80, celdas_disponibles: 78, clientes_registrados: 3 });
    fixture.detectChanges();
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('78');
    expect(texto).toContain('80');
    expect(texto).toContain('3');
  });

  it('muestra un error si el servicio no responde', () => {
    const fixture = TestBed.createComponent(Reportes);
    fixture.detectChanges();
    http
      .expectOne('/reportes/resumen')
      .flush('x', { status: 503, statusText: 'No disponible' });
    expect(fixture.componentInstance.error()).toContain('No se pudo cargar');
  });
});
