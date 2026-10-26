"""Market-data contract readiness — fail-closed (PROC-0076 R1.3).

The rights policy enforced by ``usage_policy`` trusts the recorded
``allowed_use_scope``. That trust is only valid once the contract
revision that *defines* the quarantine semantics is provably applied:
V004 narrowed ``internal_display`` for LME-backed series, so a database
still at V002/V003 (pending or failed migration, degraded boot that
keeps the CNPJ surface alive) carries a legacy catalog whose literal
``internal_display`` grant must **not** be honored.

This module is the single, centralized verification consumed by every
market-data read path and by ingestion. It proves, at read time and
inside the engine:

- the canonical ``external_data`` schema and the migrations ledger
  exist and are readable;
- the required rights-contract revision (V004) is recorded in the
  ledger;
- the ledger checksum for that revision matches the canonical,
  immutable migration file on disk;
- the catalog structures the policy depends on are present.

Any exception, timeout, missing object or divergence raises
``ContractNotReadyError`` — never a silent pass. The check is executed
per use-case invocation (two cheap catalog SELECTs): there is no cache
that could retain authorization after readiness is lost.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.application.contracts import ContractNotReadyError
from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.migrations_runner import (
    MIGRATIONS_DIR,
)

# Minimum ledger revision that defines the fail-closed rights contract.
# V001–V003 predate the license quarantine semantics.
REQUIRED_CONTRACT_REVISION = "V004"


def _canonical_checksum(version: str) -> str:
    """sha256 of the immutable ``VNNN__*.sql`` file shipped with this
    build. Missing/ambiguous file → not ready (the contract cannot be
    proven against this code)."""
    candidates = sorted(MIGRATIONS_DIR.glob(f"{version}__*.sql"))
    if len(candidates) != 1:
        raise ContractNotReadyError(
            f"canonical migration file for {version} unavailable"
        )
    return hashlib.sha256(candidates[0].read_bytes()).hexdigest()


def check_market_contract_ready(conn: Any) -> None:
    """Raise ``ContractNotReadyError`` unless the rights-contract
    revision is provably applied to the connected database."""
    schema = Settings.EXTERNAL_DATA_SCHEMA
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT to_regclass(%s) AS regclass",
                (f"{schema}.schema_migrations",),
            )
            if cur.fetchone()["regclass"] is None:
                raise ContractNotReadyError(
                    "market data migrations ledger is absent"
                )
            cur.execute(
                f'SELECT version, checksum FROM "{schema}".schema_migrations'
            )
            ledger = {
                row["version"]: row["checksum"] for row in cur.fetchall()
            }
            cur.execute(
                "SELECT to_regclass(%s) AS regclass",
                (f"{schema}.market_data_sources",),
            )
            if cur.fetchone()["regclass"] is None:
                raise ContractNotReadyError(
                    "market data catalog is absent"
                )
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = 'market_data_sources'
                  AND column_name = 'allowed_use_scope'
                """,
                (schema,),
            )
            if cur.fetchone() is None:
                raise ContractNotReadyError(
                    "market data catalog lacks the rights contract column"
                )
    except ContractNotReadyError:
        raise
    except Exception as exc:
        # Fail closed on *any* ledger/storage failure — a catalog that
        # cannot be proven is a catalog that cannot serve protected data.
        raise ContractNotReadyError(
            "market data rights contract could not be verified"
        ) from exc

    recorded = ledger.get(REQUIRED_CONTRACT_REVISION)
    if recorded is None:
        raise ContractNotReadyError(
            "market data rights contract revision is not applied"
        )
    if recorded != _canonical_checksum(REQUIRED_CONTRACT_REVISION):
        raise ContractNotReadyError(
            "market data rights contract revision diverged"
        )
