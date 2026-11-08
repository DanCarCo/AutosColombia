import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.models import Base, Celda, Operador, Vehiculo


def test_normalizes_unique_identifiers_on_creation_and_assignment():
    vehicle = Vehiculo(placa=" \tabc123\n", color="Azul", modelo=2025, marca="Marca", tipo="MOTO")
    cell = Celda(codigo=" a-01 ", tipo="Libre")
    assert vehicle.placa == "ABC123"
    assert cell.codigo == "A-01"
    vehicle.placa = " xyz789 "
    cell.codigo = " b-02 "
    assert vehicle.placa == "XYZ789"
    assert cell.codigo == "B-02"


@pytest.mark.parametrize("model,attribute", [
    (Vehiculo, "placa"), (Vehiculo, "color"), (Vehiculo, "marca"),
    (Vehiculo, "tipo"), (Celda, "codigo"), (Celda, "tipo"),
    (Operador, "nombre"), (Operador, "telefono"),
])
@pytest.mark.parametrize("value", ["", " \t\n", None])
def test_rejects_empty_text(model, attribute, value):
    with pytest.raises(ValueError):
        model(**{attribute: value})


@pytest.mark.parametrize("value", [0, 1899, 2201, 9999, 10000, True, "2025", 2025.5, None])
def test_rejects_invalid_year(value):
    with pytest.raises(ValueError):
        Vehiculo(modelo=value)


@pytest.mark.parametrize("value", [1900, 2025, 2200])
def test_accepts_year_in_1900_2200(value):
    assert Vehiculo(modelo=value).modelo == value


@pytest.mark.parametrize("value", ["MOTO", "AUTOMOVIL", "CAMIONETA"])
def test_vehicle_types(value):
    assert Vehiculo(tipo=value).tipo == value


def test_rejects_unknown_type_and_preserves_phone_text():
    with pytest.raises(ValueError):
        Vehiculo(tipo="CAMION")
    assert Operador(telefono="+57 00123").telefono == "+57 00123"
    assert Celda(tipo="Categoría futura").tipo == "Categoría futura"


def test_required_columns_and_identity():
    for name in ("vehiculo", "celda", "operador"):
        table = Base.metadata.tables[name]
        assert all(not column.nullable for column in table.columns)
        assert isinstance(table.c.id.type, sa.BigInteger)
        assert table.c.id.identity.always is True


def _load_migration(name):
    path = Path(__file__).resolve().parents[1] / "migrations/versions" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_matches_models_without_connecting(monkeypatch):
    """Aplica 0001, 0003 y 0004 (las que crean o alteran vehiculo/celda/operador/cliente/pago)
    sobre un MetaData propio, sin conectar a PostgreSQL, y compara contra los modelos."""
    metadata = sa.MetaData()

    def create_table(name, *args):
        return sa.Table(name, metadata, *args)

    def add_column(table_name, column):
        metadata.tables[table_name].append_column(column)

    def create_foreign_key(name, source, referent, local_cols, remote_cols, ondelete=None):
        metadata.tables[source].append_constraint(sa.ForeignKeyConstraint(
            local_cols, [f"{referent}.{c}" for c in remote_cols], name=name, ondelete=ondelete
        ))

    def create_unique_constraint(name, table_name, columns):
        metadata.tables[table_name].append_constraint(sa.UniqueConstraint(*columns, name=name))

    def create_check_constraint(name, table_name, condition):
        metadata.tables[table_name].append_constraint(sa.CheckConstraint(condition, name=name))

    def drop_constraint(name, table_name, type_=None):
        table = metadata.tables[table_name]
        constraint = next(c for c in table.constraints if getattr(c, "name", None) == name)
        table.constraints.discard(constraint)

    for migration_name in ("0001_modelos_iniciales", "0003_cliente_pago_login", "0004_vehiculo_modelo_1900_2200"):
        migration = _load_migration(migration_name)
        monkeypatch.setattr(migration.op, "create_table", create_table)
        monkeypatch.setattr(migration.op, "add_column", add_column)
        monkeypatch.setattr(migration.op, "create_foreign_key", create_foreign_key)
        monkeypatch.setattr(migration.op, "create_unique_constraint", create_unique_constraint)
        monkeypatch.setattr(migration.op, "create_check_constraint", create_check_constraint)
        monkeypatch.setattr(migration.op, "create_index", lambda *a, **k: None)
        monkeypatch.setattr(migration.op, "drop_constraint", drop_constraint)
        migration.upgrade()

    assert set(metadata.tables) == {"vehiculo", "celda", "operador", "cliente", "pago"}
    for name, table in metadata.tables.items():
        model_table = Base.metadata.tables[name]
        assert [(c.name, str(c.type), c.nullable) for c in table.columns] == [
            (c.name, str(c.type), c.nullable) for c in model_table.columns
        ]
        def constraints(t):
            return {(c.name, str(c.sqltext)) for c in t.constraints if isinstance(c, sa.CheckConstraint)}
        assert constraints(table) == constraints(model_table)
        def unique_columns(t):
            return {tuple(c.columns.keys()) for c in t.constraints if isinstance(c, sa.UniqueConstraint)}
        assert unique_columns(table) == unique_columns(model_table)
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        assert "BIGINT GENERATED ALWAYS AS IDENTITY" in ddl
