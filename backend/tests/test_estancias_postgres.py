"""Concurrencia real: datos nuevos confirmados, limpieza exclusiva por sus ids."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
import os
from threading import Barrier
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete, event, func, select, text
from sqlalchemy.orm import Session

from app.auth import crear_token
from app.config import load_auth_settings
from app.database import get_engine
from app.main import app
from app.models import Celda, Cliente, Estancia, Operador, Pago, Vehiculo
from app.security import hash_password

pytestmark = pytest.mark.skipif(os.getenv('RUN_POSTGRES_TESTS') != '1', reason='Requiere PostgreSQL local.')


@pytest.fixture
def datos():
    engine = get_engine()
    with engine.connect() as c:
        assert c.scalar(text('SELECT current_database()')) == 'autos_colombia'
        assert c.scalar(text('SELECT version_num FROM alembic_version')) == '0004'
    token = 'TEST-EST-' + uuid4().hex.upper()
    settings = load_auth_settings()
    with Session(engine) as s, s.begin():
        cliente = Cliente(nombre=token, documento=token, telefono='001')
        s.add(cliente)
        s.flush()
        vehicles = [
            Vehiculo(placa=f'{token}-{n}', color='Prueba', modelo=2026, marca='Prueba', tipo='MOTO',
                     cliente_id=cliente.id)
            for n in range(2)
        ]
        cells = [Celda(codigo=f'{token}-{n}', tipo='Libre') for n in range(2)]
        operators = [
            Operador(nombre=f'{token}-{n}', telefono='001', usuario=f'{token}-{n}',
                     password_hash=hash_password('clave-de-prueba'), turno='DIA')
            for n in range(2)
        ]
        s.add_all(vehicles + cells + operators)
        s.flush()
        hoy = date.today()
        pagos = [
            Pago(vehiculo_id=v.id, operador_id=operators[0].id, monto=100000,
                 periodo_inicio=hoy - timedelta(days=1), periodo_fin=hoy + timedelta(days=30))
            for v in vehicles
        ]
        s.add_all(pagos)
        s.flush()
        data = {
            'v': [v.id for v in vehicles], 'placas': [v.placa for v in vehicles],
            'c': [c.id for c in cells], 'o': [o.id for o in operators],
            'cliente': cliente.id, 'pagos': [p.id for p in pagos],
            'tokens': [crear_token(o, settings)[0] for o in operators],
        }
    try:
        yield data
    finally:
        with Session(engine) as s, s.begin():
            s.execute(delete(Pago).where(Pago.id.in_(data['pagos'])))
            s.execute(delete(Estancia).where(Estancia.vehiculo_id.in_(data['v'])))
            s.execute(delete(Vehiculo).where(Vehiculo.id.in_(data['v'])))
            s.execute(delete(Celda).where(Celda.id.in_(data['c'])))
            s.execute(delete(Operador).where(Operador.id.in_(data['o'])))
            s.execute(delete(Cliente).where(Cliente.id == data['cliente']))
        with Session(engine) as s:
            assert s.scalar(select(func.count()).select_from(Estancia).where(Estancia.vehiculo_id.in_(data['v']))) == 0


def auth(d, o=0):
    return {'Authorization': f"Bearer {d['tokens'][o]}"}


def entrada(d, v=0, c=0):
    return {'placa': d['placas'][v], 'celda_id': d['c'][c]}


def cantidad(d):
    with Session(get_engine()) as s:
        return s.scalar(select(func.count()).select_from(Estancia).where(Estancia.vehiculo_id.in_(d['v'])))


def test_recorrido_y_rechazos_sin_cambios_parciales(datos):
    d = datos
    with TestClient(app) as client:
        url = '/estancias/vehiculo/' + d['placas'][0]
        outside = client.get(url)
        assert outside.status_code == 200
        assert outside.json()['estancia'] is None and not outside.json()['esta_dentro']
        assert outside.json()['vehiculo']['id'] == d['v'][0]

        # Sin token, ninguno de los tres endpoints protegidos se puede usar (RF-16).
        for ruta, metodo, cuerpo in (
            ('/estancias/entrada', 'post', entrada(d)),
            ('/estancias/salida', 'post', {'placa': d['placas'][0]}),
            ('/estancias/celda', 'patch', {'placa': d['placas'][0], 'celda_id': d['c'][0]}),
        ):
            assert getattr(client, metodo)(ruta, json=cuerpo).status_code == 401

        for field, value in [('placa', 'INEXISTENTE-' + uuid4().hex), ('celda_id', 9223372036854775807)]:
            assert client.post('/estancias/entrada', json={**entrada(d), field: value},
                                headers=auth(d)).status_code == 404
            assert cantidad(d) == 0
        missing = 'INEXISTENTE-' + uuid4().hex
        assert client.get('/estancias/vehiculo/' + missing).status_code == 404
        assert client.post('/estancias/salida', json={'placa': missing}, headers=auth(d)).status_code == 404

        before = datetime.now(timezone.utc)
        result = client.post(
            '/estancias/entrada',
            json={**entrada(d), 'placa': ' ' + d['placas'][0].lower() + ' '},
            headers=auth(d),
        )
        assert result.status_code == 201
        opened = result.json()
        assert before <= datetime.fromisoformat(opened['entrada']) <= datetime.now(timezone.utc)
        assert opened['salida'] is None and opened['operador_salida_id'] is None
        assert opened['operador_entrada_id'] == d['o'][0]
        inside = client.get(url).json()
        assert inside['esta_dentro'] and inside['estancia']['id'] == opened['id']
        assert inside['estancia']['celda']['id'] == d['c'][0]

        for payload in (entrada(d, c=1), entrada(d, v=1)):
            assert client.post('/estancias/entrada', json=payload, headers=auth(d)).status_code == 409
            assert cantidad(d) == 1

        closed = client.post('/estancias/salida', json={'placa': d['placas'][0]}, headers=auth(d, o=1))
        assert closed.status_code == 200
        assert closed.json()['operador_salida_id'] == d['o'][1]
        assert datetime.fromisoformat(closed.json()['salida']) >= datetime.fromisoformat(opened['entrada'])
        assert client.post('/estancias/salida', json={'placa': d['placas'][0]}, headers=auth(d)).status_code == 409
        assert client.get(url).json()['estancia'] is None
        with Session(get_engine()) as s:
            saved = s.get(Estancia, opened['id'])
            assert saved.operador_salida_id == d['o'][1]
            assert saved.salida == datetime.fromisoformat(closed.json()['salida'])

        # celda 0 quedó libre al salir el vehículo 0; el vehículo 1 entra ahí "por error".
        assert client.post('/estancias/entrada', json=entrada(d, v=1), headers=auth(d)).status_code == 201
        assert cantidad(d) == 2
        assert client.get('/estancias/vehiculo/' + d['placas'][1]).json()['estancia']['celda']['id'] == d['c'][0]

        # RF-11: corrige la celda del vehículo 1 (estaba en la 0, equivocada) a la 1, que está libre.
        cambio = client.patch('/estancias/celda', json={'placa': d['placas'][1], 'celda_id': d['c'][1]},
                              headers=auth(d))
        assert cambio.status_code == 200
        assert cambio.json()['celda_id'] == d['c'][1]
        assert client.get('/estancias/vehiculo/' + d['placas'][1]).json()['estancia']['celda']['id'] == d['c'][1]
        # El vehículo 0 (fuera) no tiene estancia abierta que mover.
        assert client.patch('/estancias/celda', json={'placa': d['placas'][0], 'celda_id': d['c'][0]},
                            headers=auth(d)).status_code == 409
        # Celda inexistente.
        assert client.patch('/estancias/celda', json={'placa': d['placas'][1], 'celda_id': 9223372036854775807},
                            headers=auth(d)).status_code == 404

        for route in ('/health', '/vehiculos?limit=1', '/celdas?limit=1', '/operadores?limit=1',
                      '/clientes?limit=1', '/celdas/disponibles', '/reportes/resumen'):
            assert client.get(route).status_code == 200


def test_entrada_rechaza_sin_mensualidad_vigente(datos):
    """RF-14: ningún vehículo entra sin mensualidad vigente, sin excepción."""
    d = datos
    with Session(get_engine()) as s, s.begin():
        s.execute(delete(Pago).where(Pago.id.in_(d['pagos'])))
    try:
        with TestClient(app) as client:
            result = client.post('/estancias/entrada', json=entrada(d), headers=auth(d))
            assert result.status_code == 402
            assert 'mensualidad' in result.json()['detail']
            assert cantidad(d) == 0
    finally:
        # El fixture solo limpia los ids de pago que él mismo creó, ya eliminados aquí.
        d['pagos'].clear()


@pytest.mark.parametrize('caso', ['vehiculo', 'celda', 'salida'])
def test_concurrencia_real(datos, caso):
    d = datos
    if caso == 'salida':
        with TestClient(app) as client:
            assert client.post('/estancias/entrada', json=entrada(d), headers=auth(d)).status_code == 201
        path = '/estancias/salida'
        payloads = [({'placa': d['placas'][0]}, auth(d, o=o)) for o in range(2)]
    else:
        path = '/estancias/entrada'
        segunda = entrada(d, v=1 if caso == 'celda' else 0, c=1 if caso == 'vehiculo' else 0)
        payloads = [(entrada(d), auth(d)), (segunda, auth(d, o=1))]
    barrier = Barrier(2, timeout=15)

    def sincronizar(conn, cursor, statement, parameters, context, executemany):
        # Fuerza la carrera después de las consultas previas de entrada, o antes del bloqueo de salida.
        if (caso != 'salida' and statement.startswith('INSERT INTO estancia ')) or (
            caso == 'salida' and 'FROM estancia' in statement and 'FOR UPDATE' in statement
        ):
            barrier.wait()

    def enviar(par):
        payload, headers = par
        with TestClient(app) as client:
            return client.post(path, json=payload, headers=headers)

    engine = get_engine()
    event.listen(engine, 'before_cursor_execute', sincronizar)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(enviar, payloads))
    finally:
        event.remove(engine, 'before_cursor_execute', sincronizar)
    success = 200 if caso == 'salida' else 201
    assert sorted(r.status_code for r in responses) == [success, 409]
    assert cantidad(d) == 1
    winner = next(r.json() for r in responses if r.status_code == success)
    loser = next(r.json() for r in responses if r.status_code == 409)
    assert ('abierta' if caso == 'salida' else 'dentro' if caso == 'vehiculo' else 'ocupada') in loser['detail']
    with Session(engine) as s:
        saved = s.get(Estancia, winner['id'])
        assert saved.operador_entrada_id == winner['operador_entrada_id']
        assert saved.operador_salida_id == winner['operador_salida_id']
        assert saved.salida == (datetime.fromisoformat(winner['salida']) if winner['salida'] else None)
