"""X4.PROD-C1 — full POST + full PUT controlled assay (DELPI_TST01 only).

Creates one fictitious supplier covering EVERY published POST field (53)
through the canonical create use case — feature gate, write-target guard,
codusr resolution, tracking and upstream call all execute exactly as the
public route — then updates EVERY PUT-editable field (51) with distinct
coherent values through the canonical update use case, and reconciles
field-by-field via REST GET + independent SQL read-back in
DELPI_TST01.dbo.SA2010. A DELPI safety check proves nothing leaked into
the production base.

Safety contract:
- refuses to run unless the resolved REST environment matches the
  homologation endpoint and PROTHEUS_REST_EXPECTED_BASE_URL pins it;
- never writes to DELPI; never touches SA2 via SQL (read-only);
- requires PROTHEUS_SUPPLIER_CREATE/UPDATE_ENABLED=true in THIS process
  env only — the running service keeps the gates OFF;
- tracking is fail-closed like the public flow; no automatic retry;
- identity fields (supplier_code/supplier_store/tax_id/branch/codusr) are
  never sent as mutable payload.

Usage (ephemeral container on the infra network, worktree code mounted):
    docker run --rm --network <infra_net> -v <repo>/api-delpi:/app \
        -e PYTHONPATH=/app -e <service env> \
        -e PROTHEUS_SUPPLIER_CREATE_ENABLED=true \
        -e PROTHEUS_SUPPLIER_UPDATE_ENABLED=true \
        -e PROTHEUS_REST_EXPECTED_BASE_URL=http://192.168.1.233:8701/rest \
        infra-api-delpi python scripts/protheus_supplier_c1_full_assay.py
"""

from __future__ import annotations

import json
import sys
from typing import Any
from uuid import UUID

from app.application.services.integrations.protheus_path_resolver import (
    assert_protheus_write_target,
    resolve_protheus_rest_config,
)
from app.application.services.integrations.protheus_supplier_update_payload import (
    PUT_EDITABLE_FIELDS,
)
from app.application.services.integrations.protheus_supplier_create_payload import (
    SUPPLIER_FIELD_SPECS,
)
from app.application.services.integrations.protheus_write_tracker import (
    environment_key_from_config,
)
from app.composition.protheus_rest_composer import (
    build_create_protheus_rest_supplier_use_case,
    build_protheus_params_repository,
    build_protheus_rest_gateway,
    build_protheus_token_service,
    build_update_protheus_rest_supplier_use_case,
)
from app.config import settings
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.infrastructure.providers.totvs.connection_pool import (
    create_totvs_connection,
)

# Authorized assay actor — Core-mapped Protheus user (codusr 000311),
# same identity used by the tracked E2/E5/E6 homologation operations.
ASSAY_ACTOR_USER_ID = UUID("3bfdd634-a3a5-41af-b6b3-607025c2bdf5")

EXPECTED_ENV_MARKER = "192.168.1.233:8701"
EXPECTED_BASE_URL = "http://192.168.1.233:8701/rest"
TARGET_DATABASE = "DELPI_TST01"
CALLER_APP = "x4-prod-c1-assay"

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
    "payment_condition_code": "A2_COND",
    "payment_method_code": "A2_FORMPAG",
    "country_code": "A2_PAIS",
    "bacen_country_code": "A2_CODPAIS",
    "accounting_account": "A2_CONTA",
    "financial_nature_code": "A2_NATUREZ",
    "rohs_indicator": "A2_YROHS",
    "risk_code": "A2_RISCO",
    "swift_code": "A2_SWIFT",
    "purchase_price_table_code": "A2_ZTABPRC",
    "carrier_code": "A2_TRANSP",
    "segment_code": "A2_SATIV1",
    "administrator_code": "A2_CODADM",
    "linked_customer_code": "A2_CLIENTE",
    "linked_customer_store": "A2_LOJCLI",
    "linked_employee_code": "A2_NUMRA",
}

# Runtime lookups against DELPI_TST01 (never production data).
LOOKUP_QUERIES = {
    "carrier_code": ("SA4010", "A4_COD", None),
    "purchase_price_table_code": ("AIA010", "AIA_CODTAB", None),
    "segment_code": ("SX5010", "X5_CHAVE", "X5_TABELA='T3'"),
    "administrator_code": ("SAE010", "AE_COD", None),
    "linked_employee_code": ("SRA010", "RA_MAT", None),
    "payment_condition_code": ("SE4010", "E4_CODIGO", None),
}
# Distinct-from-current lookups also reuse catalog tables.
LINKED_CUSTOMER_LOOKUP = ("SA1010", "A1_COD", "A1_LOJA")

def _cnpj_check_digits(base12: str) -> str:
    def dv(digits: str, weights: list[int]) -> int:
        s = sum(int(d) * w for d, w in zip(digits, weights)) % 11
        return 0 if s < 2 else 11 - s

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6] + w1
    d1 = dv(base12, w1)
    d2 = dv(base12 + str(d1), w2)
    return f"{d1}{d2}"


def _pick_test_cnpj() -> str:
    """First valid mod-11 CNPJ in the 98.887.766/03xx test range not in SA2."""
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        for serial in range(300, 400):
            base12 = f"98887766{serial:04d}"
            cnpj = base12 + _cnpj_check_digits(base12)
            cur.execute(
                f"SELECT COUNT(*) FROM {TARGET_DATABASE}.dbo.SA2010 "
                "WHERE A2_CGC=? AND D_E_L_E_T_=''",
                (cnpj,),
            )
            if int(cur.fetchone()[0]) == 0:
                return cnpj
        raise SystemExit("STOP — no free test CNPJ found in range")
    finally:
        conn.close()


def _fetch_first(table: str, col: str, extra_where: str | None,
                 exclude: str = "") -> str:
    where = f"D_E_L_E_T_='' AND [{col}]<>''"
    if extra_where:
        where += f" AND {extra_where}"
    if exclude:
        where += f" AND [{col}]<>?"
        params = (exclude,)
    else:
        params = ()
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT TOP 1 [{col}] FROM {TARGET_DATABASE}.dbo.{table} "
            f"WHERE {where} ORDER BY [{col}]",
            params,
        )
        row = cur.fetchone()
        return str(row[0]).strip() if row else ""
    finally:
        conn.close()


def _lookup_map(exclude: dict[str, str] | None = None) -> dict[str, str]:
    exclude = exclude or {}
    out = {}
    for field, (table, col, extra) in LOOKUP_QUERIES.items():
        out[field] = _fetch_first(table, col, extra, exclude.get(field, ""))
    return out


def _sa2_value(column: str, exclude: str = "") -> str:
    return _fetch_first("SA2010", column, None, exclude)


def _linked_customer(cur_code: str = "", cur_store: str = "") -> tuple[str, str]:
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT TOP 1 A1_COD, A1_LOJA FROM {TARGET_DATABASE}.dbo.SA1010 "
            "WHERE D_E_L_E_T_='' AND A1_COD<>'' AND NOT (A1_COD=? AND A1_LOJA=?) "
            "ORDER BY A1_COD",
            (cur_code, cur_store),
        )
        row = cur.fetchone()
        return (str(row[0]).strip(), str(row[1]).strip()) if row else ("", "")
    finally:
        conn.close()


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


def _delpi_safety_check() -> dict[str, Any]:
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM DELPI.dbo.SA2010 "
            "WHERE A2_NREDUZ LIKE 'ZZ HOMOLOG C1%' AND D_E_L_E_T_=''"
        )
        return {"delpi_residue_count": int(cur.fetchone()[0])}
    finally:
        conn.close()


def _verdict(sent: str, persisted: str | None) -> str:
    if persisted is None:
        return "INCONCLUSIVE"
    if persisted == sent:
        return "PERSISTED"
    if persisted == "":
        return "IGNORED"
    return "TRANSFORMED"


def _field_report(sent: dict[str, str], stage: str) -> dict[str, Any]:
    return {
        "stage": stage,
        "sent_fields": sorted(sent),
        "coverage": f"{len(sent)} fields",
    }


def build_post_payload() -> dict[str, str]:
    lookups = _lookup_map()
    cust_code, cust_store = _linked_customer()
    payload: dict[str, str] = {
        "supplier_store": "01",
        "person_type": "J",
        "tax_id": _pick_test_cnpj(),
        "supplier_name": "ZZ HOMOLOG C1 FORNECEDOR TESTE",
        "supplier_short_name": "ZZ HOMOLOG C1",
        "address": "RUA TESTE HOMOLOGACAO C1",
        "address_number": "777",
        "po_box": "4321",
        "district": "CENTRO",
        "postal_code": "89120000",
        "state": "SC",
        "city": "TIMBO",
        "city_code": "18202",
        "area_code": "47",
        "phone": "4733330000",
        "fax": "4733330001",
        "website": "www.c1assay.test",
        "contact_name": "ZZ C1 CONTATO",
        "commercial_contact_name": "ZZ C1 COM",
        "responsible_name": "ZZ C1 RESPONSAVEL",
        "email": "homolog.c1@example.test",
        "state_registration": "ISENTO",
        "municipal_registration": "123456",
        "icms_contributor": "1",
        "simples_nacional": "2",
        "cnae_code": "6201501",
        "legal_entity_type": "1",
        "simp_regime_code": "1",
        "pb_regime_code": "1",
        "inss_withholding": "N",
        "iss_withholding": "N",
        "csll_withholding": "2",
        "cofins_withholding": "2",
        "pis_withholding": "2",
        "irf_calculation": "2",
        "inp_calculation": "2",
        "tax_group_code": _sa2_value("A2_GRPTRIB") or "001",
        "payment_condition_code": lookups["payment_condition_code"] or "166",
        "payment_method_code": "45",
        "country_code": "105",
        "bacen_country_code": "01058",
        "accounting_account": "21101559",
        "financial_nature_code": "2094",
        "rohs_indicator": "N",
        "risk_code": _sa2_value("A2_RISCO") or "001",
        "swift_code": "BANXBRSCXXX",
        "purchase_price_table_code": lookups["purchase_price_table_code"],
        "carrier_code": lookups["carrier_code"],
        "segment_code": lookups["segment_code"],
        "administrator_code": lookups["administrator_code"],
        "linked_customer_code": cust_code,
        "linked_customer_store": cust_store,
        "linked_employee_code": lookups["linked_employee_code"],
    }
    return {k: v for k, v in payload.items() if v != ""}


def build_put_payload(before: dict[str, str]) -> dict[str, str]:
    cur = before
    lookups = _lookup_map(exclude={
        f: cur.get(SA2_COLUMN[f], "") for f in LOOKUP_QUERIES if f in SA2_COLUMN
    })
    payload: dict[str, str] = {
        "person_type": cur.get("A2_TIPO", "J"),  # CNPJ doc — J is the only
        # coherent value; recorded as UNCHANGED_REQUIRED, not a fake change.
        "supplier_name": "ZZ HOMOLOG C1 ALTERADO PUT",
        "supplier_short_name": "ZZ HOMOLOG C1 ALT",
        "address": "RUA ALTERACAO C1 PUT",
        "address_number": "888",
        "po_box": "8765",
        "district": "VILA NOVA",
        "postal_code": "89130000",
        "state": "SC",
        "city": "INDAIAL",
        "city_code": "07502",
        "area_code": "49",
        "phone": "4733339999",
        "fax": "4733339998",
        "website": "www.c1put.test",
        "contact_name": "ZZ C1 ALT",
        "commercial_contact_name": "ZZ C1 ALT COM",
        "responsible_name": "ZZ C1 ALT RESP",
        "email": "homolog.c1.put@example.test",
        "state_registration": "987654321",
        "municipal_registration": "654321",
        "icms_contributor": "2",
        "simples_nacional": "1",
        "cnae_code": "6202300",
        "legal_entity_type": "2",
        "simp_regime_code": "2",
        "pb_regime_code": "2",
        "inss_withholding": "S",
        "iss_withholding": "S",
        "csll_withholding": "1",
        "cofins_withholding": "1",
        "pis_withholding": "1",
        "irf_calculation": "3",
        "inp_calculation": "1",
        "tax_group_code": _sa2_value("A2_GRPTRIB", cur.get("A2_GRPTRIB", "")),
        "payment_condition_code": lookups["payment_condition_code"],
        "payment_method_code": "90" if cur.get("A2_FORMPAG") != "90" else "45",
        "country_code": "105",  # Brazil — coherent with SC city/state
        "bacen_country_code": "01058",  # Brazil — coherent; UNCHANGED_REQUIRED
        "accounting_account": _sa2_value("A2_CONTA", cur.get("A2_CONTA", "")),
        "financial_nature_code": _sa2_value("A2_NATUREZ", cur.get("A2_NATUREZ", "")),
        "rohs_indicator": "S",
        "risk_code": _sa2_value("A2_RISCO", cur.get("A2_RISCO", "")),
        "swift_code": "BRASBRRJXXX",
        "purchase_price_table_code": lookups["purchase_price_table_code"],
        "carrier_code": lookups["carrier_code"],
        "segment_code": lookups["segment_code"],
        "administrator_code": lookups["administrator_code"],
        "linked_employee_code": lookups["linked_employee_code"],
    }
    # Linked customer: store change with the code companion pinned to the
    # current value (E6 semantic — isolated code change is ignored upstream).
    cur_code = cur.get("A2_CLIENTE", "")
    cur_store = cur.get("A2_LOJCLI", "")
    if cur_code:
        _, new_store = _linked_customer(cur_code, cur_store)
        payload["linked_customer_code"] = cur_code
        payload["linked_customer_store"] = new_store or cur_store
    return {k: v for k, v in payload.items() if v != ""}


def _coverage_check(sent: dict[str, str], allowed: set, label: str) -> None:
    missing = sorted(set(allowed) - set(sent))
    extra = sorted(set(sent) - set(allowed))
    print(f"[{label}] sent={len(sent)} allowed={len(allowed)} "
          f"missing={missing} extra={extra}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--put-only",
        metavar="SUPPLIER_ID",
        help="Skip POST; run the PUT assay against an existing supplier "
        "(8 digits: code+store) already created by this assay.",
    )
    parser.add_argument(
        "--post-tax-id",
        metavar="CNPJ",
        help="With --put-only: the tax_id used on the original POST, so the "
        "create verdicts can be reconstructed from the current row.",
    )
    args = parser.parse_args()

    if settings.PROTHEUS_REST_EXPECTED_BASE_URL != EXPECTED_BASE_URL:
        raise SystemExit(
            "STOP — PROTHEUS_REST_EXPECTED_BASE_URL mismatch: "
            f"{settings.PROTHEUS_REST_EXPECTED_BASE_URL!r}"
        )
    params_repo = build_protheus_params_repository()
    config = resolve_protheus_rest_config(params_repo.load_raw_params())
    assert_protheus_write_target(config, settings.PROTHEUS_REST_EXPECTED_BASE_URL)
    env_key = environment_key_from_config(
        config, settings.INTRANET_PARAMS_AMBIENTE or ""
    )
    if EXPECTED_ENV_MARKER not in env_key:
        raise SystemExit(f"STOP — REST environment unexpected: {env_key}")
    print(f"[guard] env_key={env_key} TARGET=DELPI_TST01 VERIFIED")

    report: dict[str, Any] = {"env_key": env_key, "post": {}, "put": {}}

    # ---------- T2: full POST ----------
    post_payload = build_post_payload()
    _coverage_check(post_payload, set(SUPPLIER_FIELD_SPECS), "POST")
    gateway = build_protheus_rest_gateway()
    if args.put_only:
        if not args.post_tax_id:
            raise SystemExit("--put-only requires --post-tax-id")
        supplier_id = args.put_only
        code, store = supplier_id[:6], supplier_id[6:]
        post_payload["tax_id"] = args.post_tax_id
        report["post"] = _field_report(post_payload, "create")
        report["post"]["supplier_code"] = code
        report["post"]["supplier_store"] = store
        report["post"]["mode"] = "put-only — POST verdicts reconstructed "
        "from the row created by the earlier full POST of this assay"
    else:
        create_uc = build_create_protheus_rest_supplier_use_case()
        try:
            post_result = create_uc.execute(
                actor_user_id=ASSAY_ACTOR_USER_ID,
                fornecedor=post_payload,
                caller_app=CALLER_APP,
            )
        except ProtheusRestError as exc:
            report["post"] = {"error": {"code": exc.code,
                                        "status": exc.status_code,
                                        "detail": str(exc)[:300]}}
            print(json.dumps(report, indent=2, default=str))
            return 1
        code = str(post_result.get("supplier_code") or "")
        store = str(post_result.get("supplier_store") or "")
        report["post"] = _field_report(post_payload, "create")
        report["post"]["operation_id"] = post_result.get("operation_id")
        report["post"]["supplier_code"] = code
        report["post"]["supplier_store"] = store
        report["post"]["upstream"] = {
            k: v for k, v in post_result.items()
            if k not in {"supplier_code", "request_fields", "outbound_body"}
        }
        if not (code and store):
            print(json.dumps(report, indent=2, default=str))
            return 1
        supplier_id = f"{code}{store}"
        # read-after-write: REST GET + SQL
        rest_get = gateway.get_supplier(
            config, supplier_id=supplier_id,
            access_token=build_protheus_token_service().get_valid_token(config),
        )
        report["post"]["rest_get_keys"] = (
            sorted(rest_get.keys())[:20] if isinstance(rest_get, dict)
            else str(rest_get)[:200]
        )
        report["post"]["rest_get_name"] = (
            (rest_get or {}).get("A2_NOME")
            or (rest_get or {}).get("supplier_name")
        )
    sql_before = _read_back_sql(code, store, list(SA2_COLUMN.values()))
    post_verdicts = {}
    for field, sent in post_payload.items():
        col = SA2_COLUMN.get(field)
        persisted = sql_before.get(col) if col else None
        post_verdicts[field] = {
            "column": col, "sent": sent, "persisted": persisted,
            "verdict": _verdict(sent, persisted),
        }
    report["post"]["verdicts"] = post_verdicts

    # ---------- T3: full PUT ----------
    put_payload = build_put_payload(sql_before)
    _coverage_check(put_payload, set(PUT_EDITABLE_FIELDS), "PUT")
    update_uc = build_update_protheus_rest_supplier_use_case()
    try:
        put_result = update_uc.execute(
            actor_user_id=ASSAY_ACTOR_USER_ID,
            supplier_id=supplier_id,
            fornecedor=put_payload,
            caller_app=CALLER_APP,
        )
    except ProtheusRestError as exc:
        report["put"] = {"error": {"code": exc.code, "status": exc.status_code,
                                   "detail": str(exc)[:300]},
                         "payload": put_payload}
        print(json.dumps(report, indent=2, default=str))
        return 1
    report["put"] = _field_report(put_payload, "update")
    report["put"]["operation_id"] = put_result.get("operation_id")
    report["put"]["upstream"] = {
        k: v for k, v in put_result.items()
        if k not in {"request_fields", "outbound_body"}
    }

    sql_after = _read_back_sql(code, store, list(SA2_COLUMN.values()))
    rest_get2 = gateway.get_supplier(
        config, supplier_id=supplier_id,
        access_token=build_protheus_token_service().get_valid_token(config),
    )
    put_verdicts = {}
    for field, sent in put_payload.items():
        col = SA2_COLUMN.get(field)
        after = sql_after.get(col) if col else None
        before = sql_before.get(col) if col else None
        v = _verdict(sent, after)
        if sent == before:
            v = "UNCHANGED_REQUIRED" if after == sent else v
        put_verdicts[field] = {
            "column": col, "before": before, "sent": sent,
            "persisted": after, "verdict": v,
        }
    report["put"]["verdicts"] = put_verdicts
    report["put"]["identity_preserved"] = {
        "A2_COD": sql_after.get("A2_COD") == code,
        "A2_LOJA": sql_after.get("A2_LOJA") == store,
        "A2_CGC": sql_after.get("A2_CGC") == sql_before.get("A2_CGC"),
    }

    # Omitted-field preservation: partial PUT changing only supplier_name,
    # then confirm a sample of previously-set fields stayed untouched.
    partial = {"supplier_short_name": "ZZ HOMOLOG C1 P2"}
    try:
        update_uc.execute(
            actor_user_id=ASSAY_ACTOR_USER_ID,
            supplier_id=supplier_id,
            fornecedor=partial,
            caller_app=CALLER_APP,
        )
        sql_p2 = _read_back_sql(code, store, list(SA2_COLUMN.values()))
        sample = ["A2_BAIRRO", "A2_CNAE", "A2_RISCO", "A2_TRANSP", "A2_RECPIS"]
        report["put"]["omitted_preserved"] = {
            c: sql_p2.get(c) == sql_after.get(c) for c in sample
        }
        report["put"]["partial_applied"] = (
            sql_p2.get("A2_NREDUZ") == "ZZ HOMOLOG C1 P2"
        )
    except ProtheusRestError as exc:
        report["put"]["omitted_preserved"] = {
            "error": {"code": exc.code, "detail": str(exc)[:200]}
        }

    report["delpi_safety"] = _delpi_safety_check()
    print(json.dumps(report, indent=2, default=str))
    divergent_post = [f for f, v in post_verdicts.items() if v["verdict"] != "PERSISTED"]
    divergent_put = [
        f for f, v in put_verdicts.items()
        if v["verdict"] not in {"PERSISTED", "UNCHANGED_REQUIRED"}
    ]
    print(f"\nSUMMARY post_divergent={divergent_post}")
    print(f"SUMMARY put_divergent={divergent_put}")
    print(f"SUMMARY delpi_safety={report['delpi_safety']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
