"""PRC-TRACK T01 — snapshot técnico consolidado e diff canônico.

Cada revisão publicada carrega o estado técnico consolidado do
catálogo PRC (``catalog.FIELD_SPECS``) com cobertura e proveniência
honestas por campo — nunca uma cópia integral do TOTVS nem o draft
bruto. Leitura dual: revisões legadas (``schema_version=1``, dict
plano do draft) permanecem legíveis como ``registered_unverified``,
sem promoção retroativa a ``official_verified``.

T02 — diff técnico canônico: compara somente valores técnicos.
Metadados de evidência, timestamps e proveniência isoladamente não
constituem alteração técnica. Estados ilegíveis devolvem
``incomparable`` (fail-closed), nunca inferência.
"""

from __future__ import annotations

import copy
from typing import Any

from engineering_app.domain.product_registration import catalog

SNAPSHOT_SCHEMA_VERSION = 2
LEGACY_SCHEMA_VERSION = 1

COVERAGE_PRESENT = "present"
COVERAGE_UNKNOWN = "unknown"
COVERAGE_NOT_APPLICABLE = "not_applicable"

ORIGIN_OFFICIAL_VERIFIED = "official_verified"
ORIGIN_INHERITED_CONFIRMED = "inherited_confirmed"
ORIGIN_REGISTERED_UNVERIFIED = "registered_unverified"
ORIGIN_UNKNOWN = "unknown"

CHANGE_BASELINE_INITIAL = "baseline_initial"
CHANGE_TECHNICAL = "technical_change"
CHANGE_NO_TECHNICAL = "no_technical_change"

# Paths operacionais do draft que não são campos técnicos do catálogo.
_NON_TECHNICAL_DRAFT_KEYS = frozenset(
    {"officialProductCode", "supplierLinkChanges"}
)


def _scalar_paths() -> list[str]:
    return [
        spec.path
        for spec in catalog.FIELD_SPECS
        if spec.kind != "suppliers" and spec.path != "officialProductCode"
    ]


def _field_entry(value: Any, coverage: str, origin: str) -> dict:
    return {
        "value": value,
        "coverageState": coverage,
        "valueOrigin": origin,
    }


def _link_key(code: Any, store: Any) -> str | None:
    code_s = str(code or "").strip()
    store_s = str(store or "").strip()
    if not code_s or not store_s:
        return None
    return f"{code_s}|{store_s}"


def _draft_link_attrs(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item.get(key)
        for key in ("supplierName", "partNumber", "catalogNumber")
    }


# --- dual-read --------------------------------------------------------------


def _extract_values(
    snapshot: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], bool]:
    """(fields, links, legible) — valores técnicos por path/link.

    Formato novo (schemaVersion=2): lê ``value`` dos entries marcados
    ``present``. Legado plano: chaves de primeiro nível viram campos
    ``registered_unverified`` e ``suppliers`` é normalizado por
    ``supplierCode+store``. Snapshot inexistente → vazio legível;
    tipo inesperado → ``legible=False`` (incomparable).
    """
    if snapshot is None:
        return {}, {}, True
    if not isinstance(snapshot, dict):
        return {}, {}, False
    if snapshot.get("schemaVersion") == SNAPSHOT_SCHEMA_VERSION:
        raw_fields = snapshot.get("fields")
        raw_links = snapshot.get("supplierLinks")
        if not isinstance(raw_fields, dict) or not isinstance(
            raw_links, dict
        ):
            return {}, {}, False
        fields = {
            path: entry.get("value")
            for path, entry in raw_fields.items()
            if isinstance(entry, dict)
            and entry.get("coverageState") == COVERAGE_PRESENT
        }
        links = {
            key: {
                attr: av.get("value")
                for attr, av in (link.get("attributes") or {}).items()
                if isinstance(av, dict)
            }
            for key, link in raw_links.items()
            if isinstance(link, dict)
            and link.get("linkState") == COVERAGE_PRESENT
        }
        return fields, links, True
    fields = {
        path: value
        for path, value in snapshot.items()
        if path not in _NON_TECHNICAL_DRAFT_KEYS
        and path != "suppliers"
        and path in set(_scalar_paths())
    }
    links: dict[str, dict[str, Any]] = {}
    for item in snapshot.get("suppliers") or []:
        if not isinstance(item, dict):
            continue
        key = _link_key(item.get("supplierCode"), item.get("store"))
        if key is None:
            continue
        links[key] = _draft_link_attrs(item)
    return fields, links, True


def _extract_entries(
    snapshot: dict[str, Any] | None,
) -> tuple[dict[str, dict], dict[str, dict], bool]:
    """Entries completos (value/coverage/origin) para preservação.

    Mesmo dual-read de ``_extract_values``, devolvendo o entry
    consolidado para que UPDATE omitido preserve proveniência.
    """
    fields, links, ok = _extract_values(snapshot)
    if not ok or snapshot is None:
        return {}, {}, ok
    if snapshot.get("schemaVersion") == SNAPSHOT_SCHEMA_VERSION:
        # deepcopy — entries preservados nunca podem compartilhar
        # estrutura mutável com a revisão histórica imutável.
        return (
            copy.deepcopy(snapshot["fields"]),
            copy.deepcopy(snapshot["supplierLinks"]),
            True,
        )
    legacy_fields = {
        path: _field_entry(
            value, COVERAGE_PRESENT, ORIGIN_REGISTERED_UNVERIFIED
        )
        for path, value in fields.items()
    }
    legacy_links = {
        key: {
            "linkState": COVERAGE_PRESENT,
            "valueOrigin": ORIGIN_REGISTERED_UNVERIFIED,
            "attributes": {
                attr: {
                    "value": v,
                    "valueOrigin": ORIGIN_REGISTERED_UNVERIFIED,
                }
                for attr, v in attrs.items()
            },
        }
        for key, attrs in links.items()
    }
    return legacy_fields, legacy_links, True


# --- construção consolidada --------------------------------------------------


def build_consolidated_snapshot(
    *,
    request_type: str,
    draft_data: dict[str, Any],
    changed_paths: list[dict[str, Any]],
    link_ops: list[dict[str, Any]],
    field_results: dict[str, Any],
    prior_snapshot: dict[str, Any] | None,
    baseline: dict[str, Any] | None,
    verification_id: str | None,
) -> tuple[dict[str, Any], bool]:
    """Monta o snapshot candidato V1/Vn+1 (T01).

    Retorna ``(snapshot, buildable)``. ``buildable=False`` quando o
    snapshot anterior é ilegível — o chamador decide fail-closed.

    Regras:
    - campo verificado nesta conclusão (``matched``) →
      ``official_verified`` + evidenceRef da verificação;
    - campo declarado sem verificação → ``registered_unverified``;
    - UPDATE: path omitido preserva entry anterior (valor+origem);
      sem anterior, cai no baseline oficial capturado no intake como
      ``inherited_confirmed``;
    - CREATE: paths ausentes do draft ficam ``unknown``;
    - ``null``/vazio nunca é CLEAR — o valor declarado é registrado
      como está (limpeza exige contrato explícito, inexistente hoje).
    """
    prior_fields, prior_links, legible = _extract_entries(prior_snapshot)
    if not legible:
        return {}, False
    matched = {
        path
        for path, res in (field_results or {}).items()
        if isinstance(res, dict) and res.get("result") == "matched"
    }
    baseline_fields = (baseline or {}).get("fields") or {}
    declared = (
        set(draft_data.keys())
        if request_type == "create"
        else {c.get("path") for c in (changed_paths or [])}
    )
    declared.discard(None)

    fields: dict[str, dict] = {}
    for path in _scalar_paths():
        if path in declared and path in matched:
            entry = _field_entry(
                draft_data.get(path),
                COVERAGE_PRESENT,
                ORIGIN_OFFICIAL_VERIFIED,
            )
            if verification_id:
                entry["evidenceRef"] = f"verification:{verification_id}"
        elif path in declared:
            entry = _field_entry(
                draft_data.get(path),
                COVERAGE_PRESENT,
                ORIGIN_REGISTERED_UNVERIFIED,
            )
        elif path in prior_fields:
            prior = prior_fields[path]
            entry = {
                "value": prior.get("value"),
                "coverageState": prior.get(
                    "coverageState", COVERAGE_PRESENT
                ),
                "valueOrigin": prior.get(
                    "valueOrigin", ORIGIN_REGISTERED_UNVERIFIED
                ),
            }
            if prior.get("evidenceRef"):
                entry["evidenceRef"] = prior["evidenceRef"]
        else:
            bmeta = baseline_fields.get(path)
            if isinstance(bmeta, dict) and bmeta.get("present"):
                entry = _field_entry(
                    bmeta.get("value"),
                    COVERAGE_PRESENT,
                    ORIGIN_INHERITED_CONFIRMED,
                )
                fp = (baseline or {}).get("fingerprint")
                if fp:
                    entry["evidenceRef"] = f"baseline:{fp}"
            else:
                entry = _field_entry(
                    None, COVERAGE_UNKNOWN, ORIGIN_UNKNOWN
                )
        fields[path] = entry

    links = _build_links(
        request_type=request_type,
        draft_data=draft_data,
        link_ops=link_ops,
        suppliers_matched="suppliers" in matched,
        prior_links=prior_links,
        baseline=baseline,
        verification_id=verification_id,
    )
    return (
        {
            "schemaVersion": SNAPSHOT_SCHEMA_VERSION,
            "fields": fields,
            "supplierLinks": links,
        },
        True,
    )


def _build_links(
    *,
    request_type: str,
    draft_data: dict[str, Any],
    link_ops: list[dict[str, Any]],
    suppliers_matched: bool,
    prior_links: dict[str, dict],
    baseline: dict[str, Any] | None,
    verification_id: str | None,
) -> dict[str, dict]:
    """Estado consolidado dos vínculos por ``supplierCode+store``.

    UPDATE: baseline oficial/intake ou revisão anterior como base
    (``inherited_confirmed``/preservado) + ops explícitas aplicadas.
    CREATE: lista ``suppliers`` do draft como estado declarado.
    """
    links: dict[str, dict] = {}

    def seed(key: str, attrs: dict[str, Any], origin: str) -> None:
        links[key] = {
            "linkState": COVERAGE_PRESENT,
            "valueOrigin": origin,
            "attributes": {
                attr: {"value": v, "valueOrigin": origin}
                for attr, v in attrs.items()
            },
        }

    if request_type == "create":
        for item in draft_data.get("suppliers") or []:
            if not isinstance(item, dict):
                continue
            key = _link_key(
                item.get("supplierCode"), item.get("store")
            )
            if key is None:
                continue
            origin = (
                ORIGIN_OFFICIAL_VERIFIED
                if suppliers_matched
                else ORIGIN_REGISTERED_UNVERIFIED
            )
            seed(key, _draft_link_attrs(item), origin)
            if suppliers_matched and verification_id:
                links[key]["evidenceRef"] = (
                    f"verification:{verification_id}"
                )
        return links

    # UPDATE — base: revisão anterior, depois baseline oficial.
    for key, link in prior_links.items():
        links[key] = copy.deepcopy(link)
    fp = (baseline or {}).get("fingerprint")
    for item in (baseline or {}).get("links") or []:
        if not isinstance(item, dict):
            continue
        key = _link_key(item.get("supplierCode"), item.get("store"))
        if key is None or key in links:
            continue
        seed(
            key,
            {
                a: item.get(a)
                for a in (
                    "supplierName",
                    "partNumber",
                    "catalogNumber",
                )
            },
            ORIGIN_INHERITED_CONFIRMED,
        )
        if fp:
            links[key]["evidenceRef"] = f"baseline:{fp}"
    # Ops explícitas — ADD/UPDATE/REMOVE governadas pelo contrato.
    origin = (
        ORIGIN_OFFICIAL_VERIFIED
        if suppliers_matched
        else ORIGIN_REGISTERED_UNVERIFIED
    )
    for op in link_ops or []:
        if not isinstance(op, dict):
            continue
        k = op.get("key") or {}
        key = _link_key(k.get("supplierCode"), k.get("store"))
        if key is None:
            continue
        op_name = op.get("operation")
        if op_name == "remove":
            if key in links:
                links[key]["linkState"] = "removed"
                links[key]["valueOrigin"] = origin
            continue
        attrs = op.get("fields") or {}
        target = links.setdefault(
            key,
            {
                "linkState": COVERAGE_PRESENT,
                "valueOrigin": origin,
                "attributes": {},
            },
        )
        target["linkState"] = COVERAGE_PRESENT
        target["valueOrigin"] = origin
        for attr, value in attrs.items():
            target["attributes"][attr] = {
                "value": value,
                "valueOrigin": origin,
            }
        if suppliers_matched and verification_id:
            target["evidenceRef"] = f"verification:{verification_id}"
    return links


# --- diff canônico ------------------------------------------------------------


def compute_technical_diff(
    prior_snapshot: dict[str, Any] | None,
    candidate_snapshot: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool]:
    """Diferença técnica real entre revisão vigente e candidato.

    Retorna ``(changes, comparable)``. ``comparable=False`` sinaliza
    estado ilegível — publicação deve falhar (nunca inferir igual).
    """
    old_fields, old_links, ok_old = _extract_values(prior_snapshot)
    new_fields, new_links, ok_new = _extract_values(candidate_snapshot)
    if not (ok_old and ok_new):
        return [], False
    changes: list[dict[str, Any]] = []
    for path in sorted(set(old_fields) | set(new_fields)):
        before = old_fields.get(path)
        after = new_fields.get(path)
        if before != after or (path in old_fields) != (path in new_fields):
            changes.append(
                {"path": path, "before": before, "after": after}
            )
    for key in sorted(set(old_links) | set(new_links)):
        if key not in old_links:
            changes.append(
                {
                    "path": f"suppliers[{key}]",
                    "before": None,
                    "after": new_links[key],
                    "linkState": "added",
                }
            )
            continue
        if key not in new_links:
            changes.append(
                {
                    "path": f"suppliers[{key}]",
                    "before": old_links[key],
                    "after": None,
                    "linkState": "removed",
                }
            )
            continue
        attrs = set(old_links[key]) | set(new_links[key])
        for attr in sorted(attrs):
            before = old_links[key].get(attr)
            after = new_links[key].get(attr)
            if before != after or (attr in old_links[key]) != (
                attr in new_links[key]
            ):
                changes.append(
                    {
                        "path": f"suppliers[{key}].{attr}",
                        "before": before,
                        "after": after,
                    }
                )
    return changes, True
