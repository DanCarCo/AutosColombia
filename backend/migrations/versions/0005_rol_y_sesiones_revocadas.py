"""Roles de operador (ADMINISTRADOR / OPERADOR) y sesiones revocadas.

Revision ID: 0005
Revises: 0004

- operador.rol: NOT NULL con CHECK. Las cuentas existentes pasan a OPERADOR, salvo la de
  menor id, que pasa a ADMINISTRADOR para que siempre quede alguien capaz de crear usuarios
  (POST /operadores exige ese rol). Revisar después con backend/crear_administrador.py.
- token_revocado: guarda el jti de cada sesión cerrada con POST /auth/logout.
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("operador", sa.Column("rol", sa.Text(), nullable=True))
    op.execute("UPDATE operador SET rol = 'OPERADOR'")
    op.execute("UPDATE operador SET rol = 'ADMINISTRADOR' WHERE id = (SELECT min(id) FROM operador)")
    op.alter_column("operador", "rol", nullable=False)
    op.create_check_constraint("ck_operador_rol", "operador", "rol IN ('ADMINISTRADOR', 'OPERADOR')")
    op.create_table(
        "token_revocado",
        sa.Column("jti", sa.Text(), nullable=False),
        sa.Column("expira", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("jti", name="pk_token_revocado"),
    )
    op.create_index("ix_token_revocado_expira", "token_revocado", ["expira"])


def downgrade() -> None:
    op.drop_index("ix_token_revocado_expira", table_name="token_revocado")
    op.drop_table("token_revocado")
    op.drop_constraint("ck_operador_rol", "operador", type_="check")
    op.drop_column("operador", "rol")
