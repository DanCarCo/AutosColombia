"""Ajusta el rango del año de vehiculo.modelo a 1900-2200.

Revision ID: 0004
Revises: 0003

El documento del proyecto exige años entre 1900 y 2200 (ya validado en el
esquema Pydantic de la API, ver app/schemas/vehiculo.py). El CHECK de la
base de datos y el validador del modelo seguían en 1-9999 desde la
migración 0001; esta migración corrige el modelo físico para que coincida.

ADVERTENCIA: si ya existen vehículos con modelo fuera de 1900-2200, esta
migración falla hasta corregir esas filas manualmente (no hay backfill
automático razonable para un año inválido).
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_vehiculo_modelo_anio", "vehiculo", type_="check")
    op.create_check_constraint("ck_vehiculo_modelo_anio", "vehiculo", "modelo BETWEEN 1900 AND 2200")


def downgrade() -> None:
    op.drop_constraint("ck_vehiculo_modelo_anio", "vehiculo", type_="check")
    op.create_check_constraint("ck_vehiculo_modelo_anio", "vehiculo", "modelo BETWEEN 1 AND 9999")
