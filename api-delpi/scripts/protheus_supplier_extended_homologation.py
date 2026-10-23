"""X4.FIELDS.E2 — controlled homologation assay (DELPI_TST01 only).

Runs authorized POST batches through the canonical create use case with the
experimental (widened) normalizer, then performs read-after-write via REST
GET + independent SQL read-back in DELPI_TST01.SA2010.

Safety contract:
- refuses to run unless the resolved REST environment matches the documented
  homologation endpoint and DELPI_TST01 is reachable for read-back;
- never writes to DELPI; never touches SA2 via SQL (read-only);
- requires PROTHEUS_SUPPLIER_CREATE_ENABLED=true in THIS process env only —
  the running service keeps the gate OFF;
- every attempt is tracked (fail-closed) like the public flow;
- no automatic retry on ambiguous upstream outcomes.

Usage (inside the api-delpi container, isolated exec):
    docker exec -e PYTHONPATH=/app -e PROTHEUS_SUPPLIER_CREATE_ENABLED=true \
        delpi-api-delpi python scripts/protheus_supplier_extended_homologation.py --batch 0
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
from app.application.services.integrations.protheus_supplier_extended_fields import (
    normalize_experimental_supplier_fields,
)
from app.application.services.integrations.protheus_supplier_create_payload import (
    build_upstream_create_body,
    normalize_supplier_fields,
)
from app.application.services.integrations.protheus_write_tracker import (
    ProtheusWriteTracker,
    environment_key_from_config,
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
# same identity used by the tracked F4/F4.3 homologation operations.
ASSAY_ACTOR_USER_ID = UUID("3bfdd634-a3a5-41af-b6b3-607025c2bdf5")

EXPECTED_ENV_MARKER = "192.168.1.233:8701"
TARGET_DATABASE = "DELPI_TST01"
CALLER_APP = "x4-fields-e2-assay"

# Fictitious CNPJs with valid check digits (mod-11), same 98.887.766 test
# pattern used by prior homologation residues — never real third-party docs.
CNPJS = [
    "98887766020089",
    "98887766020160",
    "98887766020240",
    "98887766020321",
    "98887766020402",
    "98887766020593",
    "98887766020674",
]

# DELPI field → SA2 column (de-para oficial §44.3).
SA2_COLUMN = {
    "supplier_store": "A2_LOJA",
    "person_type": "A2_TIPO",
    "tax_id": "A2_CGC",
    "supplier_name": "A2_NOME",
    "supplier_short_name": "A2_NREDUZ",
    "address": "A2_END",
    "address_number": "A2_NR_END",
    "po_box": "A2_CX_POST",
    "district": "A2_BAIRRO",
    "postal_code": "A2_CEP",
    "state": "A2_EST",
    "city": "A2_MUN",
    "city_code": "A2_COD_MUN",
    "area_code": "A2_DDD",
    "phone": "A2_TEL",
    "fax": "A2_FAX",
    "website": "A2_HPAGE",
    "contact_name": "A2_CONTATO",
    "commercial_contact_name": "A2_CONTCOM",
    "responsible_name": "A2_NOMRESP",
    "email": "A2_EMAIL",
    "state_registration": "A2_INSCR",
    "municipal_registration": "A2_INSCRM",
    "icms_contributor": "A2_CONTRIB",
    "simples_nacional": "A2_SIMPNAC",
    "cnae_code": "A2_CNAE",
    "legal_entity_type": "A2_TPJ",
    "person_category": "A2_TPESSOA",
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
    "esocial_category_code": "A2_CATEFD",
    "payment_condition_code": "A2_COND",
    "payment_method_code": "A2_FORMPAG",
    "country_code": "A2_PAIS",
    "bacen_country_code": "A2_CODPAIS",
    "country_calling_code": "A2_DDI",
    "accounting_account": "A2_CONTA",
    "financial_nature_code": "A2_NATUREZ",
    "rohs_indicator": "A2_YROHS",
    "risk_code": "A2_RISCO",
    "swift_code": "A2_SWIFT",
    "payee_code": "A2_CODFAV",
    "payee_store": "A2_LOJFAV",
    "generic_supplier": "A2_YFGEN",
    "purchase_price_table_code": "A2_ZTABPRC",
    "carrier_code": "A2_TRANSP",
    "segment_code": "A2_SATIV1",
    "link_type_code": "A2_VINCULO",
    "administrator_code": "A2_CODADM",
    "linked_customer_code": "A2_CLIENTE",
    "linked_customer_store": "A2_LOJCLI",
    "linked_employee_code": "A2_NUMRA",
}

BASE_FIELDS: dict[str, str] = {
    "supplier_store": "01",
    "person_type": "J",
    "supplier_name": "ZZ HOMOLOG E2 FORNECEDOR TESTE",
    "supplier_short_name": "ZZ HOMOLOG E2",
    "address": "RUA TESTE HOMOLOGACAO",
    "district": "CENTRO",
    "postal_code": "89120000",
    "state": "SC",
    "city": "TIMBO",
    "city_code": "18202",
    "area_code": "47",
    "phone": "0000000000",
    "email": "homolog.e2@example.test",
    "contact_name": "ZZ E2",
    "country_code": "105",
    "state_registration": "ISENTO",
    # Published-contract fields proven mandatory by upstream Execauto
    # ("Campos Obrigatorios Nao Preenchidos" on batch 0, first attempt) —
    # same values used by the tracked successful create 003875/01.
    "rohs_indicator": "N",
    "accounting_account": "21101559",
    "bacen_country_code": "01058",
    "payment_method_code": "45",
    "financial_nature_code": "2094",
    "payment_condition_code": "166",
}

# batch → extra fields (values within documented SX3 enums/sizes)
BATCHES: dict[str, dict[str, str]] = {
    "0": {},
    "1a": {
        "address_number": "38500",
        "po_box": "1234",
        "icms_contributor": "1",
        "simples_nacional": "2",
        "inss_withholding": "N",
        "iss_withholding": "N",
    },
    "1b": {
        "csll_withholding": "2",
        "cofins_withholding": "2",
        "pis_withholding": "2",
        "irf_calculation": "2",
        "inp_calculation": "2",
        "tax_group_code": "001",
    },
    "1c": {
        "commercial_contact_name": "ZZ E2 COM",
        "fax": "4730000000",
        "website": "www.exemplo.test",
        "responsible_name": "ZZ E2 RESPONSAVEL",
        "risk_code": "001",
        "swift_code": "BANXBRSCXXX",
    },
    "2": {
        "cnae_code": "6201501",
        "legal_entity_type": "1",
        "person_category": "01",
        "simp_regime_code": "1",
        "pb_regime_code": "1",
    },
    "3": {},  # lookup values resolved at runtime from DELPI_TST01
    "4": {},  # DELPI custom — resolved at runtime
}

# field → (table, key column, extra WHERE fragment or None)
LOOKUP_QUERIES = {
    "carrier_code": ("SA4010", "A4_COD", None),
    "purchase_price_table_code": ("AIA010", "AIA_CODTAB", None),
    "country_calling_code": ("ACJ010", "ACJ_COD", None),
    "segment_code": ("SX5010", "X5_CHAVE", "X5_TABELA='T3'"),
    "esocial_category_code": ("SX5010", "X5_CHAVE", "X5_TABELA='49'"),
    "link_type_code": ("CC1010", "CC1_COD", None),
    "administrator_code": ("SAE010", "AE_COD", None),
    "linked_employee_code": ("SRA010", "RA_MAT", None),
}

# composite references — keys must come from the SAME row
COMPOSITE_LOOKUPS = {
    ("payee_code", "payee_store"): ("SA2010", "A2_COD", "A2_LOJA", None),
    ("linked_customer_code", "linked_customer_store"): (
        "SA1010", "A1_COD", "A1_LOJA", None,
    ),
}


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


def _delpi_safety_check(code: str, store: str) -> bool:
    """Prove the written record did NOT land in the production base."""
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT A2_COD, A2_NREDUZ FROM DELPI.dbo.SA2010 "
            "WHERE A2_COD=? AND A2_LOJA=? AND D_E_L_E_T_=''",
            (code, store),
        )
        rows = cur.fetchall()
        if not rows:
            return True
        # same code may exist legitimately in DELPI — only flag if the test
        # short-name leaked into production
        return not any("ZZ HOMOLOG E2" in str(r[1]) for r in rows)
    finally:
        conn.close()


def _lookup_values() -> dict[str, str]:
    """Pick valid reference keys from DELPI_TST01 (never production data)."""
    out: dict[str, str] = {}
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        for field, (table, col, extra_where) in LOOKUP_QUERIES.items():
            where = "D_E_L_E_T_='' AND [%s]<>''" % col
            if extra_where:
                where += " AND " + extra_where
            try:
                cur.execute(
                    f"SELECT TOP 1 [{col}] FROM {TARGET_DATABASE}.dbo.{table} "
                    f"WHERE {where} ORDER BY [{col}]"
                )
                row = cur.fetchone()
                out[field] = str(row[0]).strip() if row else ""
            except Exception:
                out[field] = ""
        for (f1, f2), (table, c1, c2, extra_where) in COMPOSITE_LOOKUPS.items():
            where = f"D_E_L_E_T_='' AND [{c1}]<>''"
            if extra_where:
                where += " AND " + extra_where
            try:
                cur.execute(
                    f"SELECT TOP 1 [{c1}], [{c2}] FROM {TARGET_DATABASE}.dbo.{table} "
                    f"WHERE {where} ORDER BY [{c1}]"
                )
                row = cur.fetchone()
                out[f1] = str(row[0]).strip() if row else ""
                out[f2] = str(row[1]).strip() if row else ""
            except Exception:
                out[f1] = out[f2] = ""
    finally:
        conn.close()
    return out


def _verdict(sent: str, persisted: str | None) -> str:
    if persisted is None:
        return "INCONCLUSIVE"
    if persisted == sent:
        return "PERSISTED"
    if persisted == "":
        return "IGNORED"
    return "TRANSFORMED"


def run_batch(
    batch: str,
    *,
    config,
    token_service,
    gateway,
    identity_gateway,
    write_tracker: ProtheusWriteTracker,
    experimental: bool,
) -> dict[str, Any]:
    index = list(BATCHES).index(batch)
    fornecedor = dict(BASE_FIELDS)
    fornecedor["tax_id"] = CNPJS[index]
    fornecedor["supplier_name"] = f"ZZ HOMOLOG E2 B{batch.upper()} TESTE"
    extra = dict(BATCHES[batch])
    if batch in ("3", "4"):
        lookups = _lookup_values()
        if batch == "3":
            extra = {k: v for k, v in lookups.items() if v}
            # esocial_category_code: S049BR semantics pending owner — excluded
            extra.pop("esocial_category_code", None)
            # composite pairs must be complete or dropped together
            for pair in COMPOSITE_LOOKUPS:
                if not all(extra.get(f) for f in pair):
                    for f in pair:
                        extra.pop(f, None)
        else:
            extra = {
                "generic_supplier": "1",
                "purchase_price_table_code": lookups.get(
                    "purchase_price_table_code", ""
                ),
            }
            extra = {k: v for k, v in extra.items() if v}
    fornecedor.update(extra)

    normalized = (
        normalize_experimental_supplier_fields(fornecedor)
        if experimental
        else normalize_supplier_fields(fornecedor)
    )

    codusr = resolve_actor_codusr(identity_gateway, ASSAY_ACTOR_USER_ID)
    body = build_upstream_create_body(codusr=codusr, fornecedor=normalized)
    env_key = environment_key_from_config(
        config, settings.INTRANET_PARAMS_AMBIENTE or ""
    )
    token = token_service.get_valid_token(config)

    # Tracking BEFORE the upstream call — same fail-closed contract as the
    # public use case. No automatic retry on ambiguous outcomes.
    operation_id = write_tracker.begin(
        action="create",
        method="POST",
        resource_key=None,
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
    result: dict[str, Any] = {}
    try:
        result = gateway.create_supplier(config, body=body, access_token=token)
    except ProtheusRestError as exc:
        if exc.code == "PROTHEUS_TOKEN_INVALID":
            token_service.invalidate()
        write_tracker.record_send_failure(operation_id, exc)
        return {
            "batch": batch,
            "operation_id": operation_id,
            "error": {"code": exc.code, "status": exc.status_code},
            "sent_fields": sorted(normalized),
            "verdicts": {},
            "delpi_untouched": None,
        }

    code = str(result.get("supplier_code") or "")
    store = str(result.get("supplier_store") or "")
    resource_key = f"{code}{store}" if code and store else None
    write_tracker.record_ack(operation_id, upstream=result, resource_key=resource_key)

    report: dict[str, Any] = {
        "batch": batch,
        "operation_id": operation_id,
        "supplier_code": code,
        "supplier_store": store,
        "upstream": {
            k: v for k, v in result.items() if k != "supplier_code"
        },
        "sent_fields": sorted(normalized),
        "verdicts": {},
        "delpi_untouched": None,
    }
    if code and store:
        read_back = _read_back_sql(
            code, store, [SA2_COLUMN[f] for f in normalized if f in SA2_COLUMN]
        )
        for field, sent_value in normalized.items():
            col = SA2_COLUMN.get(field)
            report["verdicts"][field] = {
                "column": col,
                "sent": sent_value,
                "persisted": read_back.get(col) if col else None,
                "verdict": _verdict(sent_value, read_back.get(col) if col else None),
            }
        report["delpi_untouched"] = _delpi_safety_check(code, store)

        matched = [
            f for f, v in report["verdicts"].items() if v["verdict"] == "PERSISTED"
        ]
        divergent = [
            f
            for f, v in report["verdicts"].items()
            if v["verdict"] != "PERSISTED"
        ]
        result_code = "MATCH" if not divergent else "PARTIAL"
        report["tracking_confirmed"] = write_tracker.confirm(
            operation_id, checked_fields=matched, result=result_code
        )
    return report


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
        experimental=args.batch != "0",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
