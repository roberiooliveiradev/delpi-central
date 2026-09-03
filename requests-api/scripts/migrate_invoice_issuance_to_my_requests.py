#!/usr/bin/env python3
"""One-shot migration: invoice_issuance.* → my_requests.* (E8 cutover).

Default mode is --dry-run (no writes). Use --apply to persist.

Example (inside delpi-requests-api):

  python scripts/migrate_invoice_issuance_to_my_requests.py
  python scripts/migrate_invoice_issuance_to_my_requests.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow `python scripts/...` from package root.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from requests_app.application.services.invoice_issuance_migration_mapping import (  # noqa: E402
    build_history_row,
    build_payload,
    map_legacy_status,
    should_create_assignment,
)
from requests_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E402
    plugins_connection,
)


@dataclass
class MigrationReport:
    legacy_requests: int = 0
    legacy_items: int = 0
    legacy_history: int = 0
    legacy_attachments: int = 0
    already_migrated: int = 0
    to_migrate: int = 0
    migrated: int = 0
    attachments_copied: int = 0
    missing_attachment_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _env_path(name: str, default: str) -> Path:
    return Path(os.getenv(name, default) or default)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fetch_type_id(cur: Any) -> str:
    cur.execute(
        """
        SELECT id::text AS id
        FROM my_requests.request_types
        WHERE code = 'invoice-issuance'
        LIMIT 1
        """
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(
            "Tipo my_requests.request_types.code=invoice-issuance não encontrado. "
            "Aplique migrations do requests-api (V006) antes da migração."
        )
    return str(row["id"])


def _next_request_number(cur: Any) -> str:
    year = datetime.now(timezone.utc).year
    cur.execute("SELECT nextval('my_requests.request_number_seq') AS n")
    row = cur.fetchone()
    return f"REQ-{year}-{int(row['n']):06d}"


def _load_legacy_bundle(cur: Any, request_id: str) -> dict[str, Any]:
    cur.execute(
        """
        SELECT *
        FROM invoice_issuance.invoice_issuance_requests
        WHERE id = %s::uuid
        """,
        (request_id,),
    )
    request = cur.fetchone()
    if not request:
        raise RuntimeError(f"Request legado ausente: {request_id}")

    cur.execute(
        """
        SELECT *
        FROM invoice_issuance.invoice_issuance_request_items
        WHERE request_id = %s::uuid
        ORDER BY line_number ASC
        """,
        (request_id,),
    )
    items = list(cur.fetchall())

    cur.execute(
        """
        SELECT *
        FROM invoice_issuance.invoice_issuance_history
        WHERE request_id = %s::uuid
        ORDER BY created_at ASC
        """,
        (request_id,),
    )
    history = list(cur.fetchall())

    cur.execute(
        """
        SELECT *
        FROM invoice_issuance.invoice_issuance_attachments
        WHERE request_id = %s::uuid
        ORDER BY created_at ASC
        """,
        (request_id,),
    )
    attachments = list(cur.fetchall())

    return {
        "request": dict(request),
        "items": [dict(item) for item in items],
        "history": [dict(entry) for entry in history],
        "attachments": [dict(att) for att in attachments],
    }


def _already_migrated(cur: Any, request_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM my_requests.requests WHERE id = %s::uuid LIMIT 1",
        (request_id,),
    )
    return cur.fetchone() is not None


def _attachment_source_path(legacy_dir: Path, request_id: str, stored_name: str) -> Path:
    return legacy_dir / str(request_id) / stored_name


def _plan_attachments(
    attachments: list[dict[str, Any]],
    *,
    request_id: str,
    legacy_dir: Path,
    report: MigrationReport,
) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    for att in attachments:
        stored_name = str(att["stored_name"])
        src = _attachment_source_path(legacy_dir, request_id, stored_name)
        if not src.is_file():
            report.missing_attachment_files.append(str(src))
            continue
        storage_key = f"{request_id}/{stored_name}"
        planned.append(
            {
                "id": str(att["id"]),
                "original_name": att["original_name"],
                "stored_name": stored_name,
                "storage_key": storage_key,
                "mime_type": att["mime_type"],
                "size_bytes": int(att["size_bytes"]),
                "created_by_user_id": att["created_by_user_id"],
                "created_at": att.get("created_at"),
                "source_path": src,
            }
        )
    return planned


def _insert_migrated_request(
    cur: Any,
    *,
    bundle: dict[str, Any],
    type_id: str,
    legacy_dir: Path,
    dest_dir: Path,
    report: MigrationReport,
    skip_missing_attachments: bool,
    migrated_at: datetime,
) -> None:
    row = bundle["request"]
    request_id = str(row["id"])
    payload = build_payload(
        row,
        bundle["items"],
        legacy_id=request_id,
        migrated_at=migrated_at,
    )
    status = map_legacy_status(row.get("status"))
    request_number = _next_request_number(cur)

    completed_at = row.get("issued_at") if status == "completed" else None
    cancelled_at = row.get("cancelled_at") if status == "cancelled" else None

    cur.execute(
        """
        INSERT INTO my_requests.requests (
            id, request_number, request_type_id, status, priority, branch_code,
            created_by_user_id, created_by_name, payload,
            return_reason, cancel_justification, version,
            created_at, updated_at, completed_at, cancelled_at
        ) VALUES (
            %s::uuid, %s, %s::uuid, %s, 'normal', %s,
            %s, %s, %s::jsonb,
            %s, %s, 1,
            %s, %s, %s, %s
        )
        """,
        (
            request_id,
            request_number,
            type_id,
            status,
            row.get("branch_code"),
            row.get("created_by_user_id"),
            row.get("created_by_name"),
            json.dumps(payload, ensure_ascii=False),
            row.get("return_reason"),
            row.get("cancel_justification"),
            row.get("created_at"),
            row.get("updated_at"),
            completed_at,
            cancelled_at,
        ),
    )

    for entry in bundle["history"]:
        mapped = build_history_row(entry)
        to_status = mapped["to_status"]
        if to_status is None:
            to_status = status
        cur.execute(
            """
            INSERT INTO my_requests.request_status_history (
                request_id, from_status, to_status, action,
                actor_user_id, actor_name, justification, changes, created_at
            ) VALUES (
                %s::uuid, %s, %s, %s,
                %s, %s, %s, %s::jsonb, %s
            )
            """,
            (
                request_id,
                mapped["from_status"],
                to_status,
                mapped["action"],
                mapped["actor_user_id"],
                mapped["actor_name"],
                mapped["justification"],
                json.dumps(mapped["changes"], ensure_ascii=False),
                mapped["created_at"] or migrated_at,
            ),
        )

    if should_create_assignment(row):
        cur.execute(
            """
            INSERT INTO my_requests.request_assignments (
                request_id, role, assignee_user_id, assigned_at
            ) VALUES (
                %s::uuid, 'processor', %s, COALESCE(%s, NOW())
            )
            """,
            (
                request_id,
                row.get("assignee_user_id"),
                row.get("updated_at") or row.get("created_at"),
            ),
        )

    planned = _plan_attachments(
        bundle["attachments"],
        request_id=request_id,
        legacy_dir=legacy_dir,
        report=report,
    )
    if (
        len(planned) < len(bundle["attachments"])
        and not skip_missing_attachments
    ):
        missing = [
            str(_attachment_source_path(legacy_dir, request_id, str(a["stored_name"])))
            for a in bundle["attachments"]
            if not _attachment_source_path(
                legacy_dir, request_id, str(a["stored_name"])
            ).is_file()
        ]
        raise FileNotFoundError(
            "Anexos ausentes no volume legado: " + "; ".join(missing)
        )

    for att in planned:
        src: Path = att["source_path"]
        dest = dest_dir / request_id / att["stored_name"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        checksum = _sha256_file(dest)
        created_by_name = str(row.get("created_by_name") or "migrated")
        cur.execute(
            """
            INSERT INTO my_requests.request_attachments (
                id, request_id, original_name, stored_name, storage_key,
                mime_type, size_bytes, checksum_sha256,
                created_by_user_id, created_by_name, created_at
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
            """,
            (
                att["id"],
                request_id,
                att["original_name"],
                att["stored_name"],
                att["storage_key"],
                att["mime_type"],
                att["size_bytes"],
                checksum,
                att["created_by_user_id"],
                created_by_name,
                att.get("created_at") or migrated_at,
            ),
        )
        report.attachments_copied += 1


def collect_counts(cur: Any) -> dict[str, int]:
    cur.execute("SELECT COUNT(*) AS n FROM invoice_issuance.invoice_issuance_requests")
    requests_n = int(cur.fetchone()["n"])
    cur.execute("SELECT COUNT(*) AS n FROM invoice_issuance.invoice_issuance_request_items")
    items_n = int(cur.fetchone()["n"])
    cur.execute("SELECT COUNT(*) AS n FROM invoice_issuance.invoice_issuance_history")
    history_n = int(cur.fetchone()["n"])
    cur.execute("SELECT COUNT(*) AS n FROM invoice_issuance.invoice_issuance_attachments")
    attachments_n = int(cur.fetchone()["n"])
    return {
        "legacy_requests": requests_n,
        "legacy_items": items_n,
        "legacy_history": history_n,
        "legacy_attachments": attachments_n,
    }


def run_migration(
    *,
    apply: bool,
    skip_missing_attachments: bool,
    legacy_dir: Path | None = None,
    dest_dir: Path | None = None,
) -> MigrationReport:
    legacy_dir = legacy_dir or _env_path(
        "INVOICE_ISSUANCE_UPLOAD_DIR", "/app/data/invoice-issuance"
    )
    dest_dir = dest_dir or _env_path(
        "MY_REQUESTS_ATTACHMENT_UPLOAD_DIR",
        "/app/data/my-requests-attachments",
    )
    report = MigrationReport()
    migrated_at = datetime.now(timezone.utc)

    with plugins_connection() as conn:
        with conn.cursor() as cur:
            counts = collect_counts(cur)
            report.legacy_requests = counts["legacy_requests"]
            report.legacy_items = counts["legacy_items"]
            report.legacy_history = counts["legacy_history"]
            report.legacy_attachments = counts["legacy_attachments"]

            type_id = _fetch_type_id(cur)

            cur.execute(
                """
                SELECT id::text AS id
                FROM invoice_issuance.invoice_issuance_requests
                ORDER BY created_at ASC
                """
            )
            ids = [str(row["id"]) for row in cur.fetchall()]

            for request_id in ids:
                if _already_migrated(cur, request_id):
                    report.already_migrated += 1
                    continue
                report.to_migrate += 1
                bundle = _load_legacy_bundle(cur, request_id)

                if not apply:
                    _plan_attachments(
                        bundle["attachments"],
                        request_id=request_id,
                        legacy_dir=legacy_dir,
                        report=report,
                    )
                    continue

                try:
                    _insert_migrated_request(
                        cur,
                        bundle=bundle,
                        type_id=type_id,
                        legacy_dir=legacy_dir,
                        dest_dir=dest_dir,
                        report=report,
                        skip_missing_attachments=skip_missing_attachments,
                        migrated_at=migrated_at,
                    )
                    conn.commit()
                    report.migrated += 1
                except Exception as exc:  # noqa: BLE001 — surface per-request failure
                    conn.rollback()
                    report.errors.append(f"{request_id}: {exc}")
                    raise

    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migra invoice_issuance → my_requests (dry-run por padrão)."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persiste inserts + copia anexos (sem esta flag: somente relatório).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Somente relatório (implícito quando --apply não é passado).",
    )
    parser.add_argument(
        "--skip-missing-attachments",
        action="store_true",
        help=(
            "Em --apply, ignora anexos cujo arquivo não existe no volume "
            "(ainda assim lista no relatório)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    apply = bool(args.apply)

    report = run_migration(
        apply=apply,
        skip_missing_attachments=bool(args.skip_missing_attachments),
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    if report.errors:
        return 1
    if not apply and report.missing_attachment_files:
        print(
            f"Aviso: {len(report.missing_attachment_files)} arquivo(s) de anexo ausente(s).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
