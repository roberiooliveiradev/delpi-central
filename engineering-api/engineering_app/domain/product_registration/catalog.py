"""Catálogo v1 de campos da ficha técnica — única fonte de verdade.

Derivado do contrato PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT §5
(catálogo nativo EN, paths JSONB versionados) e do inventário legado
(11 field tags → SB1/SA5). Nenhum outro módulo pode redefinir paths,
tipos, required de intake ou o mapeamento para o campo oficial TOTVS.

``verifiable=False`` quando o contrato oficial de leitura vigente
(``view=engineering`` da api-delpi) não retorna o campo — a verificação
oficial honesta classifica esse path como ``unverifiable`` e a conclusão
é bloqueada até o owner ampliar o contrato (CONTRACT_GAP registrado).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engineering_app.domain.product_registration.errors import (
    PrcValidationError,
)

PAYLOAD_SCHEMA_VERSION = 1

# Origem oficial única de leitura cadastral (contrato delegado).
OFFICIAL_SOURCE = "api-delpi/totvs"


@dataclass(frozen=True)
class FieldSpec:
    """Especificação de um path técnico da ficha.

    ``kind``:
    - ``code``      — identificador/código (string, zeros à esquerda
      preservados, comparação exata após trim);
    - ``text``      — texto livre (normalização trim+whitespace, comparação
      case-insensitive — TOTVS armazena caixa alta);
    - ``enum``      — conjunto fechado tipado;
    - ``suppliers`` — relação produto×fornecedor (chave composta).
    """

    path: str
    kind: str
    required_create_intake: bool
    verifiable: bool
    official_field: str | None
    official_source: str | None
    enum_values: tuple[str, ...] = ()
    max_length: int = 255
    note: str = ""


# --- Catálogo canônico v1 (matéria-prima / raw_material) -------------------

_PRODUCT_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        path="officialProductCode",
        kind="code",
        required_create_intake=False,  # informado na conclusão (create)
        verifiable=True,
        official_field="code",
        official_source="products.detail",
        max_length=60,
        note="B1_COD — referência ERP; zeros à esquerda preservados.",
    ),
    FieldSpec(
        path="description",
        kind="text",
        required_create_intake=True,
        verifiable=True,
        official_field="description",
        official_source="products.detail",
        max_length=200,
        note="B1_DESC — legado field_tag `descricao`.",
    ),
    FieldSpec(
        path="group",
        kind="code",
        required_create_intake=True,
        verifiable=True,
        official_field="group_code",
        official_source="products.detail",
        max_length=20,
        note="B1_GRUPO — legado `grupo`.",
    ),
    FieldSpec(
        path="productKind",
        kind="code",
        required_create_intake=True,
        verifiable=True,
        official_field="type",
        official_source="products.detail",
        # Opções oficiais do domínio (protheus_product_types da plataforma):
        # MP matéria-prima · PA produto acabado · PI produto intermediário.
        # `kind` permanece "code" — o backend não rejeita outros B1_TIPO
        # legados válidos (MC, II, …); enumValues só anuncia as opções.
        enum_values=("MP", "PA", "PI"),
        max_length=8,
        note="B1_TIPO — legado `tipo` (ex.: MP).",
    ),
    FieldSpec(
        path="defaultWarehouse",
        kind="code",
        required_create_intake=True,
        verifiable=True,
        official_field="default_warehouse",
        official_source="products.detail",
        max_length=8,
        note="B1_LOCPAD — legado `armazem_padrao`.",
    ),
    FieldSpec(
        path="unit",
        kind="code",
        required_create_intake=True,
        verifiable=True,
        official_field="unit",
        official_source="products.detail",
        max_length=8,
        note="B1_UM — legado `unidade`.",
    ),
    FieldSpec(
        path="thirdPartyProduct",
        kind="enum",
        required_create_intake=True,
        verifiable=True,
        official_field="material_type",
        official_source="products.detail",
        enum_values=("1", "2"),
        max_length=2,
        note="B1_TPMAT — legado `produto_terceiro`: 1=NÃO, 2=SIM.",
    ),
    FieldSpec(
        path="accountingAccount",
        kind="code",
        required_create_intake=True,
        verifiable=True,  # B1_CONTA exposto na view=engineering (PO-D3).
        official_field="accounting_account",
        official_source="products.detail",
        max_length=40,
        note="B1_CONTA — legado `cta_contabil`; leitura oficial "
        "autorizada via view=engineering (PRC-D3).",
    ),
    FieldSpec(
        path="customerReference",
        kind="text",
        required_create_intake=True,
        verifiable=True,
        official_field="customer_reference",
        official_source="products.detail",
        max_length=60,
        note="B1_REFEREN — legado `ref_cliente`; string vazia aceita "
        "quando owner não exige referência.",
    ),
    FieldSpec(
        path="suppliers",
        kind="suppliers",
        required_create_intake=True,  # array presente (pode ser vazio)
        verifiable=True,
        official_field="suppliers",
        official_source="products.suppliers",
        note="SA5 — vínculo por (supplierCode, store); partNumber "
        "opcional (A5_CODPRF pode ser vazio — PO-D5.4).",
    ),
)

FIELD_SPECS: tuple[FieldSpec, ...] = _PRODUCT_FIELDS
FIELD_INDEX: dict[str, FieldSpec] = {spec.path: spec for spec in FIELD_SPECS}

# Paths editáveis no draft técnico (PATCH allowlist). officialProductCode
# não é editável via draft — em create é preenchido na conclusão.
EDITABLE_DRAFT_PATHS: frozenset[str] = frozenset(
    spec.path for spec in FIELD_SPECS if spec.path != "officialProductCode"
)

REQUIRED_CREATE_INTAKE_PATHS: tuple[str, ...] = tuple(
    spec.path for spec in FIELD_SPECS if spec.required_create_intake
)

# --- Subcampos de suppliers[] --------------------------------------------

SUPPLIER_REQUIRED_KEYS: tuple[str, ...] = (
    "supplierCode",
    "store",
    "supplierName",
)
# PO-D5.4: partNumber (A5_CODPRF) é opcional — aceita vazio/null/omitido
# quando o cadastro oficial TOTVS não possui o valor. Quando informado,
# a verificação oficial continua obrigatória (nunca wildcard).
SUPPLIER_OPTIONAL_KEYS: tuple[str, ...] = (
    "catalogNumber",  # A5_CODPRCA
    "partNumber",  # A5_CODPRF
)
SUPPLIER_ALLOWED_KEYS: frozenset[str] = frozenset(
    SUPPLIER_REQUIRED_KEYS + SUPPLIER_OPTIONAL_KEYS
)

# Mapeamento supplier native path → campo oficial SA5 (view=engineering).
SUPPLIER_OFFICIAL_MAP: dict[str, str] = {
    "supplierCode": "supplier_code",
    "store": "supplier_store",
    "supplierName": "supplier_name",
    "partNumber": "supplier_part_number",
    "catalogNumber": "catalog_code",
}

PRODUCT_TYPES: tuple[str, ...] = ("raw_material",)


# --- Normalização e validação ---------------------------------------------


def normalize_code(value: Any, *, max_length: int) -> str:
    """Código: strip preservando zeros à esquerda — nunca coage a número."""
    if not isinstance(value, str):
        raise PrcValidationError("Código deve ser string.")
    text = value.strip()
    if not text or len(text) > max_length:
        raise PrcValidationError(
            f"Código inválido (vazio ou > {max_length} caracteres)."
        )
    return text


def normalize_text(value: Any, *, max_length: int) -> str:
    """Texto livre: trim + collapse de whitespace interno."""
    import re

    if not isinstance(value, str):
        raise PrcValidationError("Texto deve ser string.")
    text = re.sub(r"\s+", " ", value.strip())
    if len(text) > max_length:
        raise PrcValidationError(
            f"Texto excede {max_length} caracteres."
        )
    return text


def validate_supplier(item: Any) -> dict[str, Any]:
    """Valida um vínculo produto×fornecedor — required/allowed por chave."""
    if not isinstance(item, dict):
        raise PrcValidationError("suppliers[] deve conter objetos.")
    unknown = set(item) - SUPPLIER_ALLOWED_KEYS
    if unknown:
        raise PrcValidationError(
            "Campos de fornecedor desconhecidos.",
            fields={"suppliers": ",".join(sorted(unknown))},
        )
    out: dict[str, Any] = {}
    fields: dict[str, str] = {}
    for key in SUPPLIER_REQUIRED_KEYS:
        raw = item.get(key)
        text = str(raw).strip() if raw is not None else ""
        if not text:
            fields[f"suppliers.{key}"] = "required"
        elif key in ("supplierCode", "store"):
            if len(text) > 30:
                fields[f"suppliers.{key}"] = "max_length"
            out[key] = text
        elif len(text) > 80:
            fields[f"suppliers.{key}"] = "max_length"
        else:
            out[key] = text
    catalog = item.get("catalogNumber")
    if catalog is not None and str(catalog).strip():
        out["catalogNumber"] = str(catalog).strip()[:80]
    else:
        out["catalogNumber"] = None
    part_number = item.get("partNumber")
    if part_number is not None and str(part_number).strip():
        out["partNumber"] = str(part_number).strip()[:80]
    else:
        out["partNumber"] = ""
    if fields:
        raise PrcValidationError("Fornecedor inválido.", fields=fields)
    return out


def validate_create_payload(payload: Any) -> dict[str, Any]:
    """Valida `requestedData` de create contra o catálogo v1 de intake.

    Retorna objeto normalizado (paths do catálogo). Paths desconhecidos
    são rejeitados — nunca silenciosamente aceitos/descartados.
    """
    if not isinstance(payload, dict):
        raise PrcValidationError("requestedData deve ser objeto.")
    unknown = set(payload) - set(EDITABLE_DRAFT_PATHS)
    if unknown:
        raise PrcValidationError(
            "Campos desconhecidos no payload.",
            fields={path: "unknown" for path in sorted(unknown)},
        )
    fields: dict[str, str] = {}
    out: dict[str, Any] = {}
    for spec in FIELD_SPECS:
        if spec.path == "officialProductCode":
            if spec.path in payload and str(payload[spec.path]).strip():
                # código ERP pode vir pré-informado; validado como código.
                try:
                    out[spec.path] = normalize_code(
                        payload[spec.path], max_length=spec.max_length
                    )
                except PrcValidationError:
                    fields[spec.path] = "invalid"
            continue
        raw = payload.get(spec.path)
        # Chave presente com "" é valor válido apenas para `text`
        # (customerReference pode ser vazio — gate de owner no contrato).
        missing = raw is None or (
            spec.kind != "text"
            and isinstance(raw, str)
            and not raw.strip()
        )
        if missing:
            if spec.required_create_intake:
                fields[spec.path] = "required"
            continue
        try:
            if spec.kind == "code":
                out[spec.path] = normalize_code(
                    raw, max_length=spec.max_length
                )
            elif spec.kind == "text":
                out[spec.path] = normalize_text(
                    raw, max_length=spec.max_length
                )
            elif spec.kind == "enum":
                value = normalize_code(raw, max_length=spec.max_length)
                if value not in spec.enum_values:
                    raise PrcValidationError("enum inválido")
                out[spec.path] = value
            elif spec.kind == "suppliers":
                if not isinstance(raw, list):
                    raise PrcValidationError("suppliers deve ser lista.")
                out[spec.path] = [validate_supplier(i) for i in raw]
        except PrcValidationError as exc:
            fields[spec.path] = "invalid"
            fields.update(exc.fields)
    if fields:
        raise PrcValidationError("Payload de create inválido.", fields=fields)
    return out


def validate_draft_change(path: Any, proposed_value: Any) -> tuple[str, Any]:
    """Valida uma mudança pontual de draft/intake (path + valor).

    ``path`` deve pertencer ao catálogo editável; valor validado pela
    mesma regra do intake. ``proposed_value=None`` é permitido apenas
    para campos opcionais (limpeza explícita de customerReference).
    """
    if not isinstance(path, str) or path not in FIELD_INDEX:
        raise PrcValidationError(
            "Path de campo inválido ou fora da allowlist.",
            fields={"path": str(path)[:80]},
        )
    spec = FIELD_INDEX[path]
    if spec.path == "officialProductCode":
        raise PrcValidationError(
            "officialProductCode não é editável via draft.",
            fields={spec.path: "immutable"},
        )
    if proposed_value is None:
        if spec.required_create_intake and spec.kind != "suppliers":
            raise PrcValidationError(
                "Campo obrigatório não pode ser removido.",
                fields={spec.path: "required"},
            )
        return spec.path, [] if spec.kind == "suppliers" else ""
    if spec.kind == "code":
        return spec.path, normalize_code(
            proposed_value, max_length=spec.max_length
        )
    if spec.kind == "text":
        return spec.path, normalize_text(
            proposed_value, max_length=spec.max_length
        )
    if spec.kind == "enum":
        value = normalize_code(proposed_value, max_length=spec.max_length)
        if value not in spec.enum_values:
            raise PrcValidationError(
                "Valor fora do enum.",
                fields={spec.path: ",".join(spec.enum_values)},
            )
        return spec.path, value
    if spec.kind == "suppliers":
        if not isinstance(proposed_value, list):
            raise PrcValidationError(
                "suppliers deve ser lista de objetos.",
                fields={spec.path: "type"},
            )
        return spec.path, [validate_supplier(i) for i in proposed_value]
    raise PrcValidationError("Tipo de campo desconhecido.")


def validate_update_changes(changes: Any) -> list[dict[str, Any]]:
    """Valida o change set de intake `update` — 1+ campos com motivo."""
    if not isinstance(changes, list) or not changes:
        raise PrcValidationError(
            "update exige lista não vazia de changes.",
            fields={"changes": "required"},
        )
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in changes:
        if not isinstance(item, dict):
            raise PrcValidationError("changes[] deve conter objetos.")
        path, value = validate_draft_change(
            item.get("path"), item.get("proposedValue")
        )
        if path in seen:
            raise PrcValidationError(
                "Change duplicada para o mesmo path.",
                fields={path: "duplicate"},
            )
        seen.add(path)
        # D14 — justificativa individual opcional (máx 250). Ausente ou
        # vazia é válida; acima do limite falha com 422, nunca trunca.
        reason = item.get("reason")
        reason_text = str(reason).strip() if reason else ""
        if len(reason_text) > 250:
            raise PrcValidationError(
                "Justificativa excede 250 caracteres.",
                fields={path: "reason_too_long"},
            )
        out.append({"path": path, "proposedValue": value, "reason": reason_text})
    return out


# --- Comparação oficial (verify) -------------------------------------------


def _norm_for_compare(kind: str, value: Any) -> str:
    """Normalização de comparação determinística — nunca fuzzy."""
    import re

    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value).strip())
    if kind == "code" or kind == "enum":
        return text  # exato após trim — zeros preservados
    return text.upper()  # text/suppliers names: TOTVS é caixa alta


def scalar_values_match(spec: FieldSpec, expected: Any, observed: Any) -> bool:
    """Comparação escalar por tipo — sem fuzzy match."""
    return _norm_for_compare(spec.kind, expected) == _norm_for_compare(
        spec.kind, observed
    )


def supplier_link_key(supplier: dict[str, Any], *, official: bool) -> tuple[str, str]:
    """Identidade do vínculo produto×fornecedor: (supplierCode, store).

    PO-D5.4: partNumber NÃO compõe a chave — é atributo comparado depois
    de localizada a relação (A5_CODPRF pode ser vazio no TOTVS).
    """
    if official:
        return (
            _norm_for_compare("code", supplier.get("supplier_code")),
            _norm_for_compare("code", supplier.get("supplier_store")),
        )
    return (
        _norm_for_compare("code", supplier.get("supplierCode")),
        _norm_for_compare("code", supplier.get("store")),
    )


def compare_suppliers(
    expected: list[dict[str, Any]], observed: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compara relação de fornecedores por vínculo (código, loja).

    partNumber (A5_CODPRF) é atributo comparado: vazio↔vazio matched;
    vazio↔preenchido mismatched (D); preenchido↔divergente mismatched
    (C); atributo ausente no payload oficial → unverifiable (E).
    Vínculos duplicados/ambíguos nunca aceitam a primeira ocorrência.
    Retorna ``{"result": matched|mismatched|unverifiable, "detail": []}``.
    """
    observed_by_link: dict[tuple[str, str], list[dict]] = {}
    for item in observed or []:
        if isinstance(item, dict):
            observed_by_link.setdefault(
                supplier_link_key(item, official=True), []
            ).append(item)
    expected_links: list[tuple[str, str]] = [
        supplier_link_key(item, official=False)
        for item in expected or []
        if isinstance(item, dict)
    ]
    detail: list[dict[str, Any]] = []
    mismatched = False
    unverifiable = False
    seen_links: set[tuple[str, str]] = set()
    for item in expected or []:
        if not isinstance(item, dict):
            continue
        key = supplier_link_key(item, official=False)
        label = ".".join(key)
        if key in seen_links:
            mismatched = True
            detail.append({"key": label, "result": "ambiguous_expected"})
            continue
        seen_links.add(key)
        found_list = observed_by_link.get(key, [])
        if not found_list:
            mismatched = True
            detail.append(
                {"key": label, "result": "missing_in_official"}
            )
            continue
        if len(found_list) > 1:
            mismatched = True
            detail.append({"key": label, "result": "ambiguous_official"})
            continue
        found = found_list[0]
        name_ok = _norm_for_compare("text", item.get("supplierName")) == (
            _norm_for_compare("text", found.get("supplier_name"))
        )
        exp_pn = _norm_for_compare("text", item.get("partNumber"))
        exp_catalog = _norm_for_compare("text", item.get("catalogNumber"))
        obs_catalog = _norm_for_compare("text", found.get("catalog_code"))
        fields_bad = [
            f
            for f, ok_flag in (
                ("supplierName", name_ok),
                (
                    "catalogNumber",
                    not exp_catalog or exp_catalog == obs_catalog,
                ),
            )
            if not ok_flag
        ]
        if "supplier_part_number" not in found:
            unverifiable = True
            detail.append(
                {"key": label, "result": "unverifiable",
                 "fields": ["partNumber"]}
            )
            continue
        obs_pn = _norm_for_compare("text", found.get("supplier_part_number"))
        if obs_pn != exp_pn:
            fields_bad.append("partNumber")
        if fields_bad:
            mismatched = True
            detail.append(
                {"key": label, "result": "mismatched", "fields": fields_bad}
            )
        else:
            detail.append({"key": label, "result": "matched"})
    unexpected = [
        {"key": ".".join(key), "result": "unexpected_in_official"}
        for key in set(observed_by_link) - set(expected_links)
    ]
    if unexpected:
        mismatched = True
        detail.extend(unexpected)
    result = "matched"
    if mismatched:
        result = "mismatched"
    elif unverifiable:
        result = "unverifiable"
    return {"result": result, "detail": detail}


# --- supplierLinkChanges (D12) -------------------------------------------------
# Operações granulares sobre vínculos produto×fornecedor (SA5). A chave é
# sempre (supplierCode, store) oficial; nunca razão social nem posição.
# "remove" de vínculo oficial não é autorizado.
SUPPLIER_LINK_OPERATIONS = ("update", "add", "remove")
SUPPLIER_LINK_EDITABLE_FIELDS = ("partNumber", "catalogNumber")


def validate_supplier_link_changes(
    ops: Any,
) -> tuple[list[dict[str, Any]], str | None]:
    """Valida o shape de ``supplierLinkChanges``.

    Regras de existência/duplicidade são autoritativas no verify oficial
    (o estado pode ter mudado entre a leitura do contexto e a aplicação).
    Retorna ``(ops_normalizadas, erro|None)``.
    """
    if ops is None:
        return [], None
    if not isinstance(ops, list):
        return [], "supplierLinkChanges deve ser uma lista."
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for i, op in enumerate(ops):
        if not isinstance(op, dict):
            return [], f"supplierLinkChanges[{i}] deve ser objeto."
        operation = str(op.get("operation") or "").strip()
        if operation not in SUPPLIER_LINK_OPERATIONS:
            return [], (
                f"supplierLinkChanges[{i}].operation deve ser "
                "'update' ou 'add'."
            )
        key = op.get("key") or {}
        code = str(key.get("supplierCode") or "").strip()
        store = str(key.get("store") or "").strip()
        if not code or not store:
            return [], (
                f"supplierLinkChanges[{i}].key exige supplierCode e store."
            )
        fields = op.get("fields") or {}
        if not isinstance(fields, dict):
            return [], f"supplierLinkChanges[{i}].fields inválido."
        if not fields and operation != "remove":
            return [], (
                f"supplierLinkChanges[{i}].fields deve conter ao menos "
                "um atributo."
            )
        if fields and operation == "remove":
            return [], (
                f"supplierLinkChanges[{i}].fields não se aplica a "
                "'remove' — a remoção é integral do vínculo."
            )
        unknown = set(fields) - set(SUPPLIER_LINK_EDITABLE_FIELDS)
        if unknown:
            return [], (
                f"supplierLinkChanges[{i}].fields contém atributo não "
                f"editável: {sorted(unknown)}."
            )
        reason = str(op.get("reason") or "").strip()
        if len(reason) > 250:
            return [], (
                f"supplierLinkChanges[{i}].reason excede 250 "
                "caracteres."
            )
        field_reasons = op.get("fieldReasons") or {}
        if not isinstance(field_reasons, dict):
            return [], f"supplierLinkChanges[{i}].fieldReasons inválido."
        fr_out: dict[str, str] = {}
        for fr_key, fr_val in field_reasons.items():
            if fr_key not in SUPPLIER_LINK_EDITABLE_FIELDS:
                return [], (
                    f"supplierLinkChanges[{i}].fieldReasons contém "
                    f"campo não editável: {fr_key}."
                )
            txt = str(fr_val or "").strip()
            if len(txt) > 250:
                return [], (
                    f"supplierLinkChanges[{i}].fieldReasons."
                    f"{fr_key} excede 250 caracteres."
                )
            if txt:
                fr_out[fr_key] = txt
        if (code, store) in seen:
            prev = next(
                (x for x in out
                 if x["key"]["supplierCode"] == code
                 and x["key"]["store"] == store),
                None,
            )
            prev_op = (prev or {}).get("operation")
            if prev_op and prev_op != operation:
                return [], (
                    f"supplierLinkChanges[{i}] conflita com operação "
                    f"'{prev_op}' já declarada para o vínculo "
                    f"{code}/{store} (proibido add/update/remove "
                    "simultâneos na mesma chave)."
                )
            return [], (
                f"supplierLinkChanges[{i}] duplica o vínculo "
                f"{code}/{store}."
            )
        seen.add((code, store))
        out.append(
            {
                "operation": operation,
                "key": {"supplierCode": code, "store": store},
                "fields": {
                    k: ("" if fields[k] is None else str(fields[k]))
                    for k in fields
                },
                "reason": reason,
                "fieldReasons": fr_out,
            }
        )
    return out, None


# --- reasons do intake create (D14-FIX) --------------------------------------
# CREATE não tem baseline/diff: a justificativa opcional é por campo
# preenchido e por vínculo incluído, transportada em canal próprio do
# contrato (`reasons`), nunca injetada em requestedData/suppliers[] —
# o snapshot técnico permanece estritamente de dados oficiais.
REASON_MAX_LENGTH = 250


def _reason_text(value: Any, label: str) -> tuple[str, str | None]:
    text = str(value or "").strip()
    if len(text) > REASON_MAX_LENGTH:
        return "", f"{label} excede {REASON_MAX_LENGTH} caracteres."
    return text, None


def validate_create_reasons(
    reasons: Any,
    supplier_keys: set[tuple[str, str]],
) -> tuple[dict[str, Any], str | None]:
    """Valida o canal opcional de justificativas do intake ``create``.

    Shape: ``{"fields": {path: texto}, "supplierLinks": [{key, reason,
    fieldReasons}]}``. Cada texto é opcional (omito/vazio = sem razão) e
    limitado a 250 caracteres — acima falha 422, nunca trunca. Razões de
    vínculo só são aceitas para (supplierCode, store) presentes no
    ``requestedData.suppliers`` do mesmo intake.

    Retorna ``(normalizado, erro|None)``; normalizado omite entradas
    vazias para não poluir o payload auditado.
    """
    if reasons is None:
        return {}, None
    if not isinstance(reasons, dict):
        return {}, "reasons deve ser objeto."
    unknown = set(reasons) - {"fields", "supplierLinks"}
    if unknown:
        return {}, (
            f"reasons contém chaves desconhecidas: {sorted(unknown)}."
        )
    out: dict[str, Any] = {}

    fields = reasons.get("fields") or {}
    if not isinstance(fields, dict):
        return {}, "reasons.fields deve ser objeto."
    f_out: dict[str, str] = {}
    for path, raw in fields.items():
        spec = FIELD_INDEX.get(str(path))
        if (
            spec is None
            or spec.kind == "suppliers"
            or spec.path == "officialProductCode"
        ):
            return {}, f"reasons.fields contém path inválido: {path}."
        text, err = _reason_text(raw, f"reasons.fields.{path}")
        if err:
            return {}, err
        if text:
            f_out[str(path)] = text
    if f_out:
        out["fields"] = f_out

    links = reasons.get("supplierLinks") or []
    if not isinstance(links, list):
        return {}, "reasons.supplierLinks deve ser lista."
    l_out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for i, item in enumerate(links):
        if not isinstance(item, dict):
            return {}, f"reasons.supplierLinks[{i}] deve ser objeto."
        key = item.get("key") or {}
        code = str(key.get("supplierCode") or "").strip()
        store = str(key.get("store") or "").strip()
        if not code or not store:
            return {}, (
                f"reasons.supplierLinks[{i}].key exige supplierCode "
                "e store."
            )
        if (code, store) not in supplier_keys:
            return {}, (
                f"reasons.supplierLinks[{i}] referencia vínculo "
                f"{code}/{store} ausente do payload."
            )
        if (code, store) in seen:
            return {}, (
                f"reasons.supplierLinks[{i}] duplica o vínculo "
                f"{code}/{store}."
            )
        seen.add((code, store))
        reason, err = _reason_text(
            item.get("reason"), f"reasons.supplierLinks[{i}].reason"
        )
        if err:
            return {}, err
        frs = item.get("fieldReasons") or {}
        if not isinstance(frs, dict):
            return {}, (
                f"reasons.supplierLinks[{i}].fieldReasons inválido."
            )
        fr_out: dict[str, str] = {}
        for fr_key, fr_val in frs.items():
            if fr_key not in SUPPLIER_LINK_EDITABLE_FIELDS:
                return {}, (
                    f"reasons.supplierLinks[{i}].fieldReasons contém "
                    f"campo não editável: {fr_key}."
                )
            text, err = _reason_text(
                fr_val,
                f"reasons.supplierLinks[{i}].fieldReasons.{fr_key}",
            )
            if err:
                return {}, err
            if text:
                fr_out[fr_key] = text
        entry: dict[str, Any] = {
            "key": {"supplierCode": code, "store": store}
        }
        if reason:
            entry["reason"] = reason
        if fr_out:
            entry["fieldReasons"] = fr_out
        if len(entry) > 1:
            l_out.append(entry)
    if l_out:
        out["supplierLinks"] = l_out
    return out, None
