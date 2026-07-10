"""baseline schema

Revision ID: 104b5ed85f8a
Revises: 
Create Date: 2026-07-09 09:54:56.632910

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '104b5ed85f8a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Marks the schema state as of Phase 5.1 — every table already exists in deployed
    # environments via Base.metadata.create_all (main.py lifespan), which remains the
    # bootstrap path for fresh dev/test databases. This revision intentionally does not
    # recreate those tables; it is a stamping point so subsequent migrations (starting
    # with Phase 1 RBAC columns) have a defined `down_revision` to build on. Run
    # `alembic stamp head` against an existing deployment before applying new revisions.
    pass


def downgrade() -> None:
    pass
