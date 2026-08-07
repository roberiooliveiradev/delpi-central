#!/usr/bin/env python3
"""Backfill pedidos_venda_abertos → commercial (carteiras, clientes, avatars)."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

from commercial_app.application.services.customer_avatar_storage import CustomerAvatarStorage
from commercial_app.infrastructure.persistence.plugins.migrations_runner import (
    get_connection,
    run_migrations,
)

load_dotenv()


def _legacy_avatar_dir() -> Path | None:
    raw = os.getenv("PEDIDOS_VENDA_ABERTOS_AVATAR_UPLOAD_DIR", "").strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_dir() else None


def _commercial_avatar_dir() -> Path:
    raw = os.getenv("COMMERCIAL_AVATAR_UPLOAD_DIR", "/app/data/commercial-avatars").strip()
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _copy_avatar_files(*, dry_run: bool) -> int:
    source_root = _legacy_avatar_dir()
    target_root = _commercial_avatar_dir()
    if source_root is None:
        print("[backfill] PEDIDOS_VENDA_ABERTOS_AVATAR_UPLOAD_DIR não configurado — pulando arquivos.")
        return 0

    copied = 0
    for entry in source_root.iterdir():
        if not entry.is_dir():
            continue
        target_dir = target_root / entry.name
        if dry_run:
            print(f"[dry-run] copiaria {entry} -> {target_dir}")
            copied += 1
            continue
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(entry, target_dir)
        copied += 1
    return copied


def backfill(*, dry_run: bool = False) -> None:
    if not dry_run:
        run_migrations()

    with get_connection() as conn:
        with conn.cursor() as cur:
            if dry_run:
                cur.execute("SELECT COUNT(*) AS total FROM pedidos_venda_abertos.sellers")
                sellers_count = int(cur.fetchone()["total"])
                print(f"[dry-run] sellers legado: {sellers_count}")
                return

            cur.execute(
                """
                INSERT INTO commercial.seller_portfolios (
                    id, user_id, display_name, active, created_by_user_id, created_at, updated_at
                )
                SELECT
                    id, user_id, display_name, active, created_by_user_id, created_at, updated_at
                  FROM pedidos_venda_abertos.sellers
                ON CONFLICT (id) DO NOTHING
                """
            )
            cur.execute(
                """
                INSERT INTO commercial.seller_customers (
                    id, seller_portfolio_id, customer_code, customer_store, customer_name, created_at
                )
                SELECT
                    sc.id, sc.seller_id, sc.customer_code, sc.customer_store, sc.customer_name, sc.created_at
                  FROM pedidos_venda_abertos.seller_customers sc
                  INNER JOIN commercial.seller_portfolios sp ON sp.id = sc.seller_id
                ON CONFLICT (seller_portfolio_id, customer_code, customer_store) DO NOTHING
                """
            )
            cur.execute(
                """
                SELECT id, customer_code, customer_store, file_name, content_type,
                       uploaded_by_user_id, created_at, updated_at
                  FROM pedidos_venda_abertos.customer_avatars
                """
            )
            avatar_rows = cur.fetchall()
            storage = CustomerAvatarStorage(base_dir=str(_commercial_avatar_dir()))
            for row in avatar_rows:
                code = str(row["customer_code"])
                store = str(row["customer_store"])
                file_name = str(row["file_name"])
                dir_name = storage.identity_dir_name(customer_code=code, customer_store=store)
                storage_key = f"{dir_name}/{file_name}"
                cur.execute(
                    """
                    INSERT INTO commercial.customer_avatars (
                        id, customer_code, customer_store, file_name, storage_key,
                        content_type, byte_size, uploaded_by_user_id, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, NULL, %s, %s, %s)
                    ON CONFLICT (customer_code, customer_store) DO NOTHING
                    """,
                    (
                        row["id"],
                        code,
                        store,
                        file_name,
                        storage_key,
                        row["content_type"],
                        row.get("uploaded_by_user_id"),
                        row["created_at"],
                        row["updated_at"],
                    ),
                )
        conn.commit()

    copied = _copy_avatar_files(dry_run=False)
    print(f"[backfill] Arquivos de avatar copiados: {copied}")
    print("[backfill] Concluído.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill carteira/avatars para schema commercial.")
    parser.add_argument("--dry-run", action="store_true", help="Somente inspeciona origem.")
    args = parser.parse_args()
    backfill(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
