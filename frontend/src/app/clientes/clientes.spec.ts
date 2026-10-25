import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Clientes } from './clientes';

describe('Gestión de clientes', () => {
  let fixture: ComponentFixture<Clientes>;
  let http: HttpTestingController;
  const client = { id: 1, nombre: 'Juan Pérez', documento: '123456', telefono: '3000000000' };
  const page = { items: [client], total: 1, offset: 0, limit: 10 };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Clientes],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(Clientes);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Cargando clientes');
    http.expectOne('/clientes?offset=0&limit=10').flush(page);
  });
  afterEach(() => http.verify());

  it('crea un cliente recortando los campos de texto', () => {
    const c = fixture.componentInstance;
    c.newClient();
    c.form.setValue({ nombre: ' Juan Pérez ', documento: ' 123456 ', telefono: ' 3000000000 ' });
    c.save();
    const request = http.expectOne({ method: 'POST', url: '/clientes' });
    expect(request.request.body).toEqual({
      nombre: client.nombre,
      documento: client.documento,
      telefono: client.telefono,
    });
    request.flush(client);
    http.expectOne('/clientes?offset=0&limit=10').flush(page);
    expect(c.success()).toContain('registrado');
  });

  it('rechaza campos en blanco sin enviar la solicitud', () => {
    const c = fixture.componentInstance;
    c.newClient();
    c.form.setValue({ nombre: ' \t', documento: '', telefono: ' ' });
    c.save();
    expect(c.fieldError('nombre')).toContain('obligatorio');
    expect(c.fieldError('documento')).toContain('obligatorio');
    http.expectNone('/clientes');
  });

  it('señala documento duplicado y permite corregirlo', () => {
    const c = fixture.componentInstance;
    c.newClient();
    c.form.setValue({ nombre: client.nombre, documento: client.documento, telefono: client.telefono });
    c.save();
    http
      .expectOne('/clientes')
      .flush({ detail: 'Ya existe.' }, { status: 409, statusText: 'Conflict' });
    expect(c.fieldError('documento')).toContain('Ya existe');
    c.form.controls.documento.setValue('654321');
    expect(c.form.controls.documento.valid).toBe(true);
  });

  it('consulta antes de editar y guarda con PATCH sin id', () => {
    const c = fixture.componentInstance;
    c.edit(client);
    http.expectOne('/clientes/1').flush(client);
    c.form.controls.telefono.setValue(' 3100000000 ');
    c.save();
    const request = http.expectOne({ method: 'PATCH', url: '/clientes/1' });
    expect(request.request.body).toEqual({
      nombre: client.nombre,
      documento: client.documento,
      telefono: '3100000000',
    });
    request.flush({ ...client, telefono: '3100000000' });
    http.expectOne('/clientes?offset=0&limit=10').flush(page);
    expect(c.success()).toContain('actualizado');
  });

  it('identifica al cliente, permite cancelar y elimina una sola vez', () => {
    const c = fixture.componentInstance;
    c.confirmDelete(client);
    fixture.detectChanges();
    const confirmation = fixture.nativeElement.querySelector('[role="alertdialog"]').textContent;
    expect(confirmation).toContain(client.nombre);
    expect(confirmation).toContain(client.documento);
    c.cancel();
    c.remove();
    http.expectNone((r) => r.method === 'DELETE');
    c.confirmDelete(client);
    c.remove();
    c.remove();
    http
      .expectOne({ method: 'DELETE', url: '/clientes/1' })
      .flush(null, { status: 204, statusText: 'No Content' });
    http.expectOne('/clientes?offset=0&limit=10').flush({ ...page, items: [], total: 0 });
    fixture.detectChanges();
    expect(c.success()).toContain('eliminado');
    expect(fixture.nativeElement.textContent).toContain('Aún no hay clientes');
  });

  it('muestra conflicto de eliminación cuando el cliente tiene vehículos', () => {
    const c = fixture.componentInstance;
    c.confirmDelete(client);
    c.remove();
    http.expectOne('/clientes/1').flush({}, { status: 409, statusText: 'Conflict' });
    expect(c.actionError()).toContain('vehículos');
    expect(c.pendingDelete()).toEqual(client);
  });

  it('informa 404 al editar un cliente ya eliminado', () => {
    const c = fixture.componentInstance;
    c.edit(client);
    http.expectOne('/clientes/1').flush({}, { status: 404, statusText: 'Not Found' });
    expect(c.actionError()).toContain('ya no existe');
  });
});
