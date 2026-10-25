"""Crea cliente y pago; añade vehiculo.cliente_id y el inicio de sesión de operador.

Revision ID: 0003
Revises: 0002

ADVERTENCIA: vehiculo.cliente_id y operador.usuario/password_hash/turno se
crean NOT NULL y sin valor por defecto. Si la base ya tiene vehículos u
operadores, esta migración falla hasta que cada fila reciba un valor válido
(por ejemplo, creando un cliente de respaldo y asignando cliente_id a cada
vehículo existente, y usuario/password_hash/turno a cada operador existente)
antes de aplicarla. No se incluye un backfill automático porque no hay un
cliente u operador "por defecto" razonable para datos reales.
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cliente",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("documento", sa.Text(), nullable=False),
        sa.Column("telefono", sa.Text(), nullable=False),
        sa.UniqueConstraint("documento", name="uq_cliente_documento"),
        sa.CheckConstraint("nombre ~ '[^[:space:]]'", name="ck_cliente_nombre_no_vacio"),
        sa.CheckConstraint("documento ~ '[^[:space:]]'", name="ck_cliente_documento_no_vacio"),
        sa.CheckConstraint("telefono ~ '[^[:space:]]'", name="ck_cliente_telefono_no_vacio"),
    )

    op.add_column("vehiculo", sa.Column("cliente_id", sa.BigInteger(), nullable=False))
    op.create_foreign_key(
        "fk_vehiculo_cliente", "vehiculo", "cliente", ["cliente_id"], ["id"], ondelete="RESTRICT"
    )

    op.add_column("operador", sa.Column("usuario", sa.Text(), nullable=False))
    op.add_column("operador", sa.Column("password_hash", sa.Text(), nullable=False))
    op.add_column("operador", sa.Column("turno", sa.Text(), nullable=False))
    op.create_unique_constraint("uq_operador_usuario", "operador", ["usuario"])
    op.create_check_constraint("ck_operador_usuario_no_vacio", "operador", "usuario ~ '[^[:space:]]'")
    op.create_check_constraint("ck_operador_password_hash_no_vacio", "operador", "password_hash ~ '[^[:space:]]'")
    op.create_check_constraint("ck_operador_turno", "operador", "turno IN ('DIA', 'NOCHE')")

    op.create_table(
        "pago",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("vehiculo_id", sa.BigInteger(), nullable=False),
        sa.Column("operador_id", sa.BigInteger(), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("periodo_inicio", sa.Date(), nullable=False),
        sa.Column("periodo_fin", sa.Date(), nullable=False),
        sa.Column("fecha_pago", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["vehiculo_id"], ["vehiculo.id"], name="fk_pago_vehiculo", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["operador_id"], ["operador.id"], name="fk_pago_operador", ondelete="RESTRICT"),
        sa.CheckConstraint("monto > 0", name="ck_pago_monto_positivo"),
        sa.CheckConstraint("periodo_fin >= periodo_inicio", name="ck_pago_periodo_orden"),
    )
    op.create_index("ix_pago_vehiculo_periodo", "pago", ["vehiculo_id", "periodo_fin"])


def downgrade() -> None:
    # Elimina pago, cliente y los campos de inicio de sesión; pierde ese historial.
    op.drop_index("ix_pago_vehiculo_periodo", table_name="pago")
    op.drop_table("pago")

    op.drop_constraint("ck_operador_turno", "operador", type_="check")
    op.drop_constraint("ck_operador_password_hash_no_vacio", "operador", type_="check")
    op.drop_constraint("ck_operador_usuario_no_vacio", "operador", type_="check")
    op.drop_constraint("uq_operador_usuario", "operador", type_="unique")
    op.drop_column("operador", "turno")
    op.drop_column("operador", "password_hash")
    op.drop_column("operador", "usuario")

    op.drop_constraint("fk_vehiculo_cliente", "vehiculo", type_="foreignkey")
    op.drop_column("vehiculo", "cliente_id")

    op.drop_table("cliente")
