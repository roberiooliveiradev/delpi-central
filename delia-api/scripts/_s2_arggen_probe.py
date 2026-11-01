#!/usr/bin/env python3
"""S2 probe: run DELIA's real argument stage (_build_arguments) against
live owner capabilities and verify proposed discriminator values are
inside the owner-published enum vocabulary.

Proves mechanism A (current arggen) on the S2 causal cases — the same
code path the governed turn executes, not a reimplementation.
"""
import json
import sys

sys.path.insert(0, "/app/scripts")
sys.path.insert(0, "/app")

from local_orchestration_reliability_eval import (
    _compose,
    _find_orchestrator,
    _mint_bearer,
)
from app.application.interaction.argument_validation import (
    validate_arguments,
)
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)

# (scenario, group, remote_name, causal question)
CASES = [
    ("cmp_05", "clara", "get_context",
     "fechamentos mensais dos últimos três períodos"),
    ("cmp_05b", "clara", "analyze",
     "analise os últimos três fechamentos mensais disponíveis"),
    ("cmp_03", "caio", "analyze",
     "propostas e oportunidades abertas dos últimos 120 dias"),
    ("cmp_03b", "caio", "knowledge",
     "orientação de uso das ferramentas semânticas"),
    ("cmp_13", "eva", "analyze",
     "demandas e solicitações de engenharia recentes"),
    ("cmp_19", "teo", "analyze",
     "iniciativas com atrasos repetidos ou mudanças de prazo"),
    ("cmp_suri", "suri", "analyze",
     "resumo de pedidos de compra recentes"),
]


def _enum_values(prop_schema):
    """Collect closed-vocabulary values from a property schema
    (top-level enum/const or anyOf/oneOf branches)."""
    found = set()
    if not isinstance(prop_schema, dict):
        return found
    for key in ("enum", "const"):
        value = prop_schema.get(key)
        if isinstance(value, list):
            found.update(v for v in value if isinstance(v, str))
        elif isinstance(value, str):
            found.add(value)
    for comb in ("anyOf", "oneOf"):
        for branch in prop_schema.get(comb) or []:
            found.update(_enum_values(branch))
    return found


def _closed_fields(schema):
    props = (schema or {}).get("properties") or {}
    return {
        name: values
        for name, spec in props.items()
        if (values := _enum_values(spec))
    }


def main() -> None:
    handler, _guarded, _mcp = _compose()
    orch = _find_orchestrator(handler)
    bearer = _mint_bearer()
    binding = bind_subject_bearer(bearer)
    try:
        providers = orch._providers
        if hasattr(providers, "values"):
            providers = list(providers.values())
        caps_by_key = {}
        for provider in providers:
            surface = provider.list_groups(correlation_id="s2-arggen")
            for group in surface.groups:
                for cap in group.capabilities:
                    caps_by_key[(group.group_id, cap.remote_name)] = cap
        results = []
        for scenario, gid, remote, question in CASES:
            cap = caps_by_key.get((gid, remote))
            if cap is None:
                results.append(
                    {"scenario": scenario, "error": "capability absent"}
                )
                continue
            schema = cap.input_schema or {}
            closed = _closed_fields(schema)
            try:
                args, missing = orch._build_arguments(
                    question,
                    cap,
                    business_subject=question,
                    correlation=f"s2-arggen-{scenario}",
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "scenario": scenario,
                        "capability": f"{gid}.{remote}",
                        "error": f"{type(exc).__name__}: {str(exc)[:160]}",
                    }
                )
                continue
            enum_check = {}
            enum_ok = True
            for field, allowed in closed.items():
                value = (args or {}).get(field)
                if value is not None and value not in allowed:
                    enum_ok = False
                enum_check[field] = {
                    "value": value,
                    "allowed_n": len(allowed),
                    "in_enum": value in allowed if value is not None else None,
                }
            schema_valid = None
            if args is not None:
                schema_valid = (
                    validate_arguments(args, schema) is not None
                )
            results.append(
                {
                    "scenario": scenario,
                    "capability": f"{gid}.{remote}",
                    "closed_fields": {k: len(v) for k, v in closed.items()},
                    "args": args,
                    "missing": list(missing or ()),
                    "enum_check": enum_check,
                    "enum_ok": enum_ok,
                    "schema_valid": schema_valid,
                }
            )
        for r in results:
            print(json.dumps(r, ensure_ascii=False)[:1200])
        json.dump(
            results,
            open("/app/.battery/task37/s2_arggen.json", "w"),
            indent=2,
            ensure_ascii=False,
        )
    finally:
        unbind_subject_bearer(binding)


if __name__ == "__main__":
    main()
