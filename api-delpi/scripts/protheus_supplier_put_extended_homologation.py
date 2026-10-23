"""X4.FIELDS.E5 — controlled PUT homologation assay (DELPI_TST01 only).

Runs authorized partial-PUT batches against the E2 fictitious suppliers
(`ZZ HOMOLOG E2*`) through the canonical update gateway path, then performs
read-after-write via REST GET + independent SQL read-back in
DELPI_TST01.SA2010, including preservation checks for non-sent fields.

Safety contract:
- refuses to run unless the resolved REST environment matches the documented
  homologation endpoint and DELPI_TST01 is reachable for read-back;
- never writes to DELPI; never touches SA2 via SQL (read-only);
- requires PROTHEUS_SUPPLIER_UPDATE_ENABLED=true in THIS process env only —
  the running service keeps the gate OFF;
- every attempt is tracked (fail-closed) like the public flow;
- no automatic retry on ambiguous upstream outcomes;
- identity fields (supplier_code/supplier_store/tax_id/branch/codusr) are
  never sent as mutable payload.

Usage (inside the api-delpi container, isolated exec):
    docker exec -e PYTHONPATH=/app -e PROTHEUS_SUPPLIER_UPDATE_ENABLED=true \
        delpi-api-delpi python scripts/protheus_supplier_put_extended_homologation.py --batch 1
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from uuid import UUID

from app.application.services.integrations.protheus_actor_codusr import (
    resolve_actor_codusr,
)
from app.application.services.integrations.protheus_supplier_create_payload import (
    normalize_supplier_field_value,
)
from app.application.services.integrations.protheus_supplier_update_payload import (
    build_upstream_update_body,
)
from app.application.services.integrations.protheus_write_tracker import (
    ProtheusWriteTracker,
    compare_sent_fields,
    environment_key_from_config,
    extract_supplier_fields,
)
from app.composition.integration_tracking_composer import (
    build_integration_tracking_service,
)
from app.composition.protheus_rest_composer import (
    build_core_protheus_identity_gateway,
    build_protheus_params_repository,
    build_protheus_rest_gateway,
    build_protheus_token_service,
)
from app.application.services.integrations.protheus_path_resolver import (
    resolve_protheus_rest_config,
)
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.config import settings
from app.infrastructure.providers.totvs.connection_pool import (
    create_totvs_connection,
)

# Authorized assay actor — Core-mapped Protheus user (codusr 000311),
# same identity used by the tracked F4/E2 homologation operations.
ASSAY_ACTOR_USER_ID = UUID("3bfdd634-a3a5-41af-b6b3-607025c2bdf5")

EXPECTED_ENV_MARKER = "192.168.1.233:8701"
TARGET_DATABASE = "DELPI_TST01"
CALLER_APP = "x4-fields-e5-put-assay"

# DELPI field → SA2 column (de-para oficial §44.3) — same map as E2.
SA2_COLUMN = {
    "supplier_name": "A2_NOME",
    "address_number": "A2_NR_END",
    "po_box": "A2_CX_POST",
    "commercial_contact_name": "A2_CONTCOM",
    "fax": "A2_FAX",
    "website": "A2_HPAGE",
    "responsible_name": "A2_NOMRESP",
    "icms_contributor": "A2_CONTRIB",
    "simples_nacional": "A2_SIMPNAC",
    "cnae_code": "A2_CNAE",
    "legal_entity_type": "A2_TPJ",
    "simp_regime_code": "A2_REGESIM",
    "pb_regime_code": "A2_REGPB",
    "inss_withholding": "A2_RECINSS",
    "iss_withholding": "A2_RECISS",
    "csll_withholding": "A2_RECCSLL",
    "cofins_withholding": "A2_RECCOFI",
    "pis_withholding": "A2_RECPIS",
    "irf_calculation": "A2_CALCIRF",
    "inp_calculation": "A2_CALCINP",
    "tax_group_code": "A2_GRPTRIB",
    "risk_code": "A2_RISCO",
    "swift_code": "A2_SWIFT",
    "purchase_price_table_code": "A2_ZTABPRC",
    "carrier_code": "A2_TRANSP",
    "segment_code": "A2_SATIV1",
    "administrator_code": "A2_CODADM",
    "linked_customer_code": "A2_CLIENTE",
    "linked_customer_store": "A2_LOJCLI",
    "linked_employee_code": "A2_NUMRA",
    # identity canary — read-only, never sent
    "tax_id": "A2_CGC",
}

# batch → (supplier_id, {field: new value}). Literal values differ from the
# E2-persisted ones so an actual change is provable; LOOKUP-marked fields
# are resolved at runtime to a valid TST01 reference distinct from the
# current column value.
_LOOKUP = "@lookup@"
_LOOKUP_SA2 = "@sa2_distinct@"  # value already in use by another supplier

BATCHES: dict[str, tuple[str, dict[str, str]]] = {
    # Lote 1 — endereço e contato (003877/01: E2 persisted 38500/1234)
    "1": (
        "00387701",
        {
            "address_number": "1024",
            "po_box": "9876",
            "commercial_contact_name": "ZZ E5 COM",
            "fax": "4730009999",
            "website": "www.e5.test",
            "responsible_name": "ZZ E5 RESP",
        },
    ),
    # Lote 2 — fiscal e tributário (003879/01: E2 persisted batch 1b values)
    "2": (
        "00387901",
        {
            "icms_contributor": "2",
            "simples_nacional": "1",
            "inss_withholding": "S",
            "iss_withholding": "S",
            "csll_withholding": "1",
            "cofins_withholding": "1",
            "pis_withholding": "1",
            "irf_calculation": "3",
            "inp_calculation": "1",
            "tax_group_code": _LOOKUP_SA2,
            "legal_entity_type": "2",
            "simp_regime_code": "2",
            "pb_regime_code": "2",
        },
    ),
    # Lote 3 — compras e referências (003880/01: E2 persisted risk/swift)
    "3": (
        "00388001",
        {
            "risk_code": _LOOKUP_SA2,
            "swift_code": "BRASBRRJXXX",
            "purchase_price_table_code": _LOOKUP,
            "carrier_code": _LOOKUP,
            "segment_code": _LOOKUP,
            "administrator_code": _LOOKUP,
        },
    ),
    # Lote 4 — condicionais e relacionamentos (003882/01: E2 lookups)
    "4": (
        "00388201",
        {
            "cnae_code": "6202300",
            "linked_customer_code": _LOOKUP,
            "linked_customer_store": _LOOKUP,
            "linked_employee_code": _LOOKUP,
        },
    ),
}

# Reference lookups — same tables as the E2 assay.
LOOKUP_QUERIES = {
    "carrier_code": ("SA4010", "A4_COD", None),
    "purchase_price_table_code": ("AIA010", "AIA_CODTAB", None),
    "segment_code": ("SX5010", "X5_CHAVE", "X5_TABELA='T3'"),
    "administrator_code": ("SAE010", "AE_COD", None),
    "linked_employee_code": ("SRA010", "RA_MAT", None),
}

# composite reference — linked customer code+store from the SAME SA1 row
LINKED_CUSTOMER_LOOKUP = ("SA1010", "A1_COD", "A1_LOJA")


def _guard_environment(config) -> str:
    env_key = environment_key_from_config(
        config, settings.INTRANET_PARAMS_AMBIENTE or ""
    )
    if EXPECTED_ENV_MARKER not in env_key:
        raise SystemExit(
            f"STOP — REST environment unexpected: {env_key}. "
            "Ensaio autorizado somente contra homologação."
        )
    return env_key


def _read_back_sql(code: str, store: str, columns: list[str]) -> dict[str, str]:
    cols = ", ".join(f"[{c}]" for c in sorted(set(columns)))
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT {cols} FROM {TARGET_DATABASE}.dbo.SA2010 "
            "WHERE A2_COD=? AND A2_LOJA=? AND D_E_L_E_T_=''",
            (code, store),
        )
        rows = cur.fetchall()
        desc = [d[0] for d in cur.description]
        if not rows:
            return {}
        return {k: str(v).strip() for k, v in dict(zip(desc, rows[0])).items()}
    finally:
        conn.close()


def _sa2_distinct_value(column: str, current: str) -> str:
    """Pick a value already in use by another TST01 supplier (≠ current)."""
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT TOP 1 [{column}] FROM {TARGET_DATABASE}.dbo.SA2010 "
            f"WHERE D_E_L_E_T_='' AND [{column}]<>'' AND [{column}]<>? "
            f"ORDER BY [{column}]",
            (current,),
        )
        row = cur.fetchone()
        return str(row[0]).strip() if row else ""
    finally:
        conn.close()


def _lookup_distinct(field: str, current: str) -> str:
    table, col, extra_where = LOOKUP_QUERIES[field]
    where = f"D_E_L_E_T_='' AND [{col}]<>'' AND [{col}]<>?"
    if extra_where:
        where += " AND " + extra_where
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT TOP 1 [{col}] FROM {TARGET_DATABASE}.dbo.{table} "
            f"WHERE {where} ORDER BY [{col}]",
            (current,),
        )
        row = cur.fetchone()
        return str(row[0]).strip() if row else ""
    finally:
        conn.close()


def _linked_customer_distinct(cur_code: str, cur_store: str) -> tuple[str, str]:
    table, c1, c2 = LINKED_CUSTOMER_LOOKUP
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT TOP 1 [{c1}], [{c2}] FROM {TARGET_DATABASE}.dbo.{table} "
            f"WHERE D_E_L_E_T_='' AND [{c1}]<>'' AND NOT ([{c1}]=? AND [{c2}]=?) "
            f"ORDER BY [{c1}]",
            (cur_code, cur_store),
        )
        row = cur.fetchone()
        if not row:
            return "", ""
        return str(row[0]).strip(), str(row[1]).strip()
    finally:
        conn.close()


def _delpi_safety_check() -> bool:
    """Confirm no E2/E5 test residue leaked into the production base."""
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM DELPI.dbo.SA2010 "
            "WHERE A2_NREDUZ LIKE 'ZZ HOMOLOG%' AND D_E_L_E_T_=''"
        )
        row = cur.fetchone()
        return not row or int(row[0]) == 0
    finally:
        conn.close()


def _put_verdict(sent: str, before: str | None, after: str | None) -> str:
    if after is None:
        return "PUT_INCONCLUSIVE"
    if after == sent and before != sent:
        return "PUT_PERSISTENCE_PROVEN"
    if after == sent:
        return "PUT_PERSISTENCE_PROVEN_SAME_VALUE"
    if after == (before or ""):
        return "PUT_IGNORED"
    return "PUT_TRANSFORMED"


def run_batch(
    batch: str,
    *,
    config,
    token_service,
    gateway,
    identity_gateway,
    write_tracker: ProtheusWriteTracker,
) -> dict[str, Any]:
    supplier_id, template = BATCHES[batch]
    code, store = supplier_id[:6], supplier_id[6:]

    # --- before snapshot -------------------------------------------------
    all_cols = sorted(set(SA2_COLUMN.values()))
    before_sql = _read_back_sql(code, store, all_cols)
    if not before_sql:
        return {"batch": batch, "error": "test supplier not found in TST01"}

    # --- resolve lookup values ------------------------------------------
    fields: dict[str, str] = {}
    skipped: dict[str, str] = {}
    for field, value in template.items():
        if value == _LOOKUP_SA2:
            resolved = _sa2_distinct_value(
                SA2_COLUMN[field], before_sql.get(SA2_COLUMN[field], "")
            )
        elif value == _LOOKUP:
            if field in ("linked_customer_code", "linked_customer_store"):
                continue  # composite pair handled below
            resolved = _lookup_distinct(
                field, before_sql.get(SA2_COLUMN[field], "")
            )
        else:
            resolved = value
        if resolved:
            fields[field] = resolved
        else:
            skipped[field] = "no valid lookup value in TST01"
    if "linked_customer_code" in template:
        c, s = _linked_customer_distinct(
            before_sql.get(SA2_COLUMN["linked_customer_code"], ""),
            before_sql.get(SA2_COLUMN["linked_customer_store"], ""),
        )
        if c and s:
            fields["linked_customer_code"] = c
            fields["linked_customer_store"] = s
        else:
            skipped["linked_customer_code"] = "no SA1 row in TST01"
            skipped["linked_customer_store"] = "no SA1 row in TST01"

    if not fields:
        return {"batch": batch, "error": "no resolvable fields", "skipped": skipped}

    normalized = {
        f: normalize_supplier_field_value(f, v) for f, v in fields.items()
    }

    codusr = resolve_actor_codusr(identity_gateway, ASSAY_ACTOR_USER_ID)
    body = build_upstream_update_body(codusr=codusr, fields=normalized)
    env_key = environment_key_from_config(
        config, settings.INTRANET_PARAMS_AMBIENTE or ""
    )
    token = token_service.get_valid_token(config)

    # REST before-read for the report (authoritative verdicts use SQL).
    try:
        before_rest = extract_supplier_fields(
            gateway.get_supplier(
                config, supplier_id=supplier_id, access_token=token
            )
        )
    except ProtheusRestError:
        before_rest = {}

    # Tracking BEFORE the upstream call — fail-closed like the public flow.
    operation_id = write_tracker.begin(
        action="update",
        method="PUT",
        resource_key=supplier_id,
        environment_key=env_key,
        caller_app=CALLER_APP,
        actor_user_id=ASSAY_ACTOR_USER_ID,
        codusr=codusr,
        request_fields=normalized,
        outbound_body=body,
        correlation_id=None,
        request_id=None,
        field_provenance=None,
    )

    try:
        upstream = gateway.update_supplier(
            config,
            supplier_id=supplier_id,
            body=body,
            access_token=token,
        )
    except ProtheusRestError as exc:
        if exc.code == "PROTHEUS_TOKEN_INVALID":
            token_service.invalidate()
        write_tracker.record_send_failure(operation_id, exc)
        return {
            "batch": batch,
            "operation_id": operation_id,
            "error": {"code": exc.code, "status": exc.status_code},
            "sent_fields": sorted(normalized),
            "skipped_fields": skipped,
            "verdicts": {
                f: "PUT_REJECTED" for f in normalized
            },
            "delpi_untouched": _delpi_safety_check(),
        }

    write_tracker.record_ack(
        operation_id, upstream=upstream, resource_key=supplier_id
    )

    # --- after snapshot ----------------------------------------------------
    try:
        after_rest = extract_supplier_fields(
            gateway.get_supplier(
                config, supplier_id=supplier_id, access_token=token
            )
        )
    except ProtheusRestError:
        after_rest = {}
    after_sql = _read_back_sql(code, store, all_cols)

    verdicts: dict[str, Any] = {}
    for field, sent in normalized.items():
        col = SA2_COLUMN[field]
        verdicts[field] = {
            "column": col,
            "sent": sent,
            "before_sql": before_sql.get(col),
            "after_sql": after_sql.get(col),
            "before_rest": before_rest.get(field),
            "after_rest": after_rest.get(field),
            "verdict": _put_verdict(
                sent, before_sql.get(col), after_sql.get(col)
            ),
        }

    # Preservation: every non-sent mapped column must be unchanged.
    sent_cols = {SA2_COLUMN[f] for f in normalized}
    preserved = {
        field: before_sql.get(col) == after_sql.get(col)
        for field, col in SA2_COLUMN.items()
        if col not in sent_cols
    }
    untouched = all(preserved.values())

    comparison = compare_sent_fields(normalized, after_rest)
    divergent = [
        f for f, v in verdicts.items() if v["verdict"] != "PUT_PERSISTENCE_PROVEN"
    ]
    result_code = "MATCH" if not divergent and untouched else "PARTIAL"
    confirmed = write_tracker.confirm(
        operation_id,
        checked_fields=[
            f
            for f, v in verdicts.items()
            if v["verdict"] == "PUT_PERSISTENCE_PROVEN"
        ],
        result=result_code,
    )

    return {
        "batch": batch,
        "supplier_id": supplier_id,
        "operation_id": operation_id,
        "sent_fields": sorted(normalized),
        "skipped_fields": skipped,
        "verdicts": verdicts,
        "untouched_preserved": untouched,
        "preservation_violations": [
            f for f, ok in preserved.items() if not ok
        ],
        "rest_comparison": comparison,
        "delpi_untouched": _delpi_safety_check(),
        "tracking_confirmed": confirmed,
        "result": result_code,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True, choices=list(BATCHES))
    args = parser.parse_args()

    params_repo = build_protheus_params_repository()
    config = resolve_protheus_rest_config(params_repo.load_raw_params())
    env_key = _guard_environment(config)
    print(f"[gate] environment_key={env_key} target_db={TARGET_DATABASE}")

    report = run_batch(
        args.batch,
        config=config,
        token_service=build_protheus_token_service(),
        gateway=build_protheus_rest_gateway(),
        identity_gateway=build_core_protheus_identity_gateway(),
        write_tracker=ProtheusWriteTracker(build_integration_tracking_service()),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
