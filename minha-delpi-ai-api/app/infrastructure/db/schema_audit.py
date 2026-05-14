from __future__ import annotations

import importlib
import pkgutil
import re
from pathlib import Path

from sqlalchemy import inspect

from app.create_app import create_app
from app.extensions.db import db


def import_all_models() -> None:
    import app.infrastructure.db.models as models_pkg

    for module in pkgutil.iter_modules(models_pkg.__path__):
        importlib.import_module(f"{models_pkg.__name__}.{module.name}")


def read_alembic_heads() -> set[str]:
    versions_dir = Path("migrations/versions")
    revisions: set[str] = set()
    down_revisions: set[str] = set()

    if not versions_dir.exists():
        versions_dir = Path("/app/migrations/versions")

    if not versions_dir.exists():
        return set()

    for file in versions_dir.glob("*.py"):
        content = file.read_text(encoding="utf-8")

        revision_match = re.search(
            r"^revision\s*=\s*['\"]([^'\"]+)['\"]",
            content,
            re.M,
        )
        if revision_match:
            revisions.add(revision_match.group(1))

        down_match = re.search(r"^down_revision\s*=\s*(.+)$", content, re.M)
        if down_match:
            for item in re.findall(r"['\"]([^'\"]+)['\"]", down_match.group(1)):
                down_revisions.add(item)

    return revisions - down_revisions


def run() -> int:
    app = create_app()

    with app.app_context():
        import_all_models()

        inspector = inspect(db.engine)
        db_tables = set(inspector.get_table_names(schema="public"))
        model_tables = set(db.metadata.tables.keys())

        missing_tables = sorted(model_tables - db_tables)
        column_errors: list[str] = []

        for table_name in sorted(model_tables & db_tables):
            model_table = db.metadata.tables[table_name]
            db_columns = {
                column["name"]: column
                for column in inspector.get_columns(table_name, schema="public")
            }

            for column_name in model_table.columns.keys():
                if column_name not in db_columns:
                    column_errors.append(f"{table_name}.{column_name}")

        db_versions = []
        if "alembic_version" in db_tables:
            db_versions = [
                row.version_num
                for row in db.session.execute(
                    db.text("select version_num from alembic_version order by version_num")
                ).fetchall()
            ]

        heads = sorted(read_alembic_heads())

        print("\n=== SCHEMA AUDIT ===")
        print("Models esperados:", len(model_tables))
        print("Tabelas no banco:", len(db_tables))
        print("Alembic banco:", db_versions or "(nenhuma)")
        print("Alembic heads:", heads or "(nenhuma)")

        if missing_tables:
            print("\n[ERRO] Tabelas faltando:")
            for table in missing_tables:
                print(" -", table)

        if column_errors:
            print("\n[ERRO] Colunas faltando:")
            for column in column_errors:
                print(" -", column)

        if heads and not set(db_versions).intersection(heads):
            print("\n[AVISO] alembic_version não está em uma head atual.")

        if missing_tables or column_errors:
            print("\nSTATUS: INCONSISTENTE")
            return 1

        print("\nSTATUS: OK")
        return 0


if __name__ == "__main__":
    raise SystemExit(run())
