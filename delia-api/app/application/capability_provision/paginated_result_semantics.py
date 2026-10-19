"""Provider-neutral pagination and personal-ticket count semantics.

R4/R5 (DELIA-C3-HELPDESK-PERSONAL-TICKET-COUNT-AND-PAGINATION-REMEDIATION-01):

- PAGE_SIZE / returned items are never treated as an authoritative total
  when ``has_more`` is true or aggregation is incomplete.
- Personal scopes (assigned / requested / ambiguous) are distinguished
  without inventing GLPI identity or fabricating totals.
- Authoritative ``total_count`` / ``total`` is used only when present on
  the owner payload; otherwise bounded aggregation or honest unknown.

This module is pure projection: no Helpdesk client, no AuthZ, no ACT.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class PersonalTicketScope(str, Enum):
    ASSIGNED_TO_ME = "ASSIGNED_TO_ME"
    REQUESTED_BY_ME = "REQUESTED_BY_ME"
    MY_TICKETS_AMBIGUOUS = "MY_TICKETS_AMBIGUOUS"
    ALL_VISIBLE_TICKETS = "ALL_VISIBLE_TICKETS"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResultIntent(str, Enum):
    COUNT = "COUNT"
    LIST = "LIST"
    OTHER = "OTHER"


class CountResolutionKind(str, Enum):
    AUTHORITATIVE_TOTAL = "AUTHORITATIVE_TOTAL"
    COMPLETE_AGGREGATE = "COMPLETE_AGGREGATE"
    PARTIAL_UNKNOWN = "PARTIAL_UNKNOWN"
    EMPTY = "EMPTY"
    PAGE_SLICE_NOT_TOTAL = "PAGE_SLICE_NOT_TOTAL"


# Default operational bound for governed page walks (R5).
DEFAULT_MAX_PAGES = 20
DEFAULT_PAGE_SIZE_CAP = 50

_TICKET_DOMAIN_RE = re.compile(
    r"\b("
    r"chamados?|tickets?|helpdesk|glpi|incidente|incidentes|"
    r"solicita[cç][aã]o(?:es)?\s+de\s+suporte"
    r")\b",
    re.IGNORECASE,
)
_COUNT_INTENT_RE = re.compile(
    r"\b("
    r"quantos?|quantas?|how\s+many|count|total|"
    r"n[uú]mero\s+de|quantidade"
    r")\b",
    re.IGNORECASE,
)
_LIST_INTENT_RE = re.compile(
    r"\b("
    r"liste|listar|lista|quais|mostre|mostrar|show|list"
    r")\b",
    re.IGNORECASE,
)
_ASSIGNED_RE = re.compile(
    r"("
    r"atribu[ií]d[oa]s?\s+a\s+mim|"
    r"sou\s+respons[aá]vel|"
    r"respons[aá]vel|"
    r"assigned\s+to\s+me|"
    r"i(?:'m|\s+am)\s+responsible|"
    r"pelos?\s+quais\s+sou\s+respons[aá]vel"
    r")",
    re.IGNORECASE,
)
_REQUESTED_RE = re.compile(
    r"("
    r"eu\s+abri|"
    r"que\s+eu\s+abri|"
    r"solicitei|"
    r"abri\s+eu|"
    r"requested\s+by\s+me|"
    r"i\s+opened|"
    r"como\s+solicitante"
    r")",
    re.IGNORECASE,
)
_PERSONAL_AMBIGUOUS_RE = re.compile(
    r"("
    r"para\s+mim|"
    r"meus?\s+chamados?|"
    r"meus?\s+tickets?|"
    r"my\s+tickets?|"
    r"for\s+me"
    r")",
    re.IGNORECASE,
)
_ALL_VISIBLE_RE = re.compile(
    r"("
    r"todos\s+os\s+chamados|"
    r"all\s+(?:visible\s+)?tickets?|"
    r"chamados\s+vis[ií]veis"
    r")",
    re.IGNORECASE,
)

_TOTAL_KEYS = ("total_count", "total", "totalcount", "count_total")
_ID_KEYS = ("id", "ticket_id", "ticketid")


@dataclass(frozen=True, slots=True)
class PaginationEnvelope:
    items: tuple[Mapping[str, Any], ...]
    page: int | None
    page_size: int | None
    has_more: bool | None
    total_count: int | None

    @property
    def returned_count(self) -> int:
        return len(self.items)


@dataclass(frozen=True, slots=True)
class PageAggregationResult:
    items: tuple[Mapping[str, Any], ...]
    pages_fetched: int
    complete: bool
    duplicate_ids: tuple[str, ...]
    failed: bool
    failure_reason: str | None
    authoritative_total: int | None

    @property
    def unique_count(self) -> int:
        return len(self.items)


@dataclass(frozen=True, slots=True)
class CountResolution:
    kind: CountResolutionKind
    total: int | None
    returned_on_page: int
    has_more: bool | None
    message: str


PERSONAL_SCOPE_CLARIFICATION = (
    "Para contar ou listar corretamente, preciso saber o escopo: "
    "chamados atribuídos a você (responsável) ou chamados que você "
    "abriu (solicitante)? Sem esse esclarecimento não afirmo um total "
    "pessoal."
)

ASSIGNED_IDENTITY_LIMITATION = (
    "Não posso determinar chamados atribuídos a você sem o "
    "identificador de técnico autorizado pela fonte Helpdesk/GLPI. "
    "Não invento assignee_id a partir do nome ou do token. Vinculação "
    "GLPI e filtro autorizado são necessários; sem eles não confirmo "
    "o total atribuído."
)

REQUESTER_FILTER_LIMITATION = (
    "O contrato atual de listagem Helpdesk não expõe filtro de "
    "solicitante (requester). Não posso afirmar quantos chamados você "
    "abriu sem essa capacidade na fonte. Não fabrico esse total."
)

GLPI_LINK_NO_COUNT = (
    "A consulta de chamados exige vinculação GLPI. Sem o vínculo "
    "autorizado não apresento contagem nem lista pessoal."
)

UNKNOWN_TOTAL_MESSAGE = (
    "Consultei uma parte dos chamados, mas não tenho evidência "
    "suficiente para confirmar o total."
)

PAGE_SLICE_LIST_HEADER = (
    "Mostrando {count} registro(s) nesta página; há mais resultados "
    "além desta página — este número não é o total."
)

COMPLETE_COUNT_MESSAGE = "Total confirmado nesta consulta: {total}."

AUTHORITATIVE_COUNT_MESSAGE = (
    "Total informado pela fonte nesta consulta: {total}."
)

EMPTY_COUNT_MESSAGE = "Nenhum chamado encontrado nesta consulta."

VISIBLE_NOT_PERSONAL_NOTE = (
    " Este total refere-se aos chamados retornados pela consulta "
    "autorizada, não a um escopo pessoal de responsável ou solicitante "
    "sem filtro comprovado."
)


def classify_result_intent(input_text: str) -> ResultIntent:
    text = (input_text or "").strip()
    if not text:
        return ResultIntent.OTHER
    if _COUNT_INTENT_RE.search(text):
        return ResultIntent.COUNT
    if _LIST_INTENT_RE.search(text) and _TICKET_DOMAIN_RE.search(text):
        return ResultIntent.LIST
    return ResultIntent.OTHER


def classify_personal_ticket_scope(input_text: str) -> PersonalTicketScope:
    text = (input_text or "").strip()
    if not text or not _TICKET_DOMAIN_RE.search(text):
        return PersonalTicketScope.NOT_APPLICABLE
    assigned = bool(_ASSIGNED_RE.search(text))
    requested = bool(_REQUESTED_RE.search(text))
    if assigned and not requested:
        return PersonalTicketScope.ASSIGNED_TO_ME
    if requested and not assigned:
        return PersonalTicketScope.REQUESTED_BY_ME
    if assigned and requested:
        return PersonalTicketScope.MY_TICKETS_AMBIGUOUS
    if _ALL_VISIBLE_RE.search(text) and not _PERSONAL_AMBIGUOUS_RE.search(
        text
    ):
        return PersonalTicketScope.ALL_VISIBLE_TICKETS
    if _PERSONAL_AMBIGUOUS_RE.search(text):
        return PersonalTicketScope.MY_TICKETS_AMBIGUOUS
    return PersonalTicketScope.NOT_APPLICABLE


def _as_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _read_total(node: Mapping[str, Any]) -> int | None:
    for key in _TOTAL_KEYS:
        if key in node:
            total = _as_int(node.get(key))
            if total is not None and total >= 0:
                return total
    return None


def extract_pagination_envelope(
    structured: object,
) -> PaginationEnvelope | None:
    """Detect owner list pages: items + pagination metadata.

    Recognizes top-level or single-envelope payloads. Returns None when
    the shape is not a paginated item list.
    """
    if not isinstance(structured, Mapping):
        return None
    candidates: list[Mapping[str, Any]] = [structured]
    for key in ("data", "result", "payload", "response"):
        inner = structured.get(key)
        if isinstance(inner, Mapping):
            candidates.append(inner)
    for node in candidates:
        items = node.get("items")
        if not isinstance(items, list):
            continue
        has_page_meta = any(
            k in node for k in ("page", "page_size", "has_more", *_TOTAL_KEYS)
        )
        if not has_page_meta and not items:
            # Empty non-paginated items list is not a count envelope.
            continue
        if not has_page_meta and items:
            # Bare items without pagination metadata — still usable as a
            # complete page only when the caller treats has_more as None.
            pass
        normalized_items = tuple(
            item for item in items if isinstance(item, Mapping)
        )
        return PaginationEnvelope(
            items=normalized_items,
            page=_as_int(node.get("page")),
            page_size=_as_int(node.get("page_size")),
            has_more=_as_bool(node.get("has_more")),
            total_count=_read_total(node),
        )
    return None


def item_stable_id(item: Mapping[str, Any]) -> str | None:
    for key in _ID_KEYS:
        if key in item and item[key] is not None:
            text = str(item[key]).strip()
            if text:
                return text
    return None


def _is_first_page(page: int | None) -> bool:
    """True when the envelope is the first page of a query.

    Missing ``page`` is treated as first-page only when the owner also
    signals explicit completion (``has_more=False``) — never when
    completeness is unsigned.
    """
    return page is None or page <= 1


def aggregate_paginated_pages(
    pages: Sequence[Mapping[str, Any] | PaginationEnvelope | None],
    *,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> PageAggregationResult:
    """Merge ordered owner pages with integrity checks.

    ``complete`` requires explicit evidence of a finished walk:

    - authoritative owner total, or
    - walk that starts at the first page, contiguous page numbers (when
      present), last page ``has_more is False``, no duplicate ids, no
      page failures, and no missing stable ids when counting.

    ``has_more is None`` never proves completion. An isolated last page
    (``page>1``) never proves the full query total.
    """
    merged: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    pages_fetched = 0
    authoritative: int | None = None
    last_has_more: bool | None = None
    started_at_first = False
    expected_page: int | None = None
    seen_page_numbers: set[int] = set()
    missing_stable_ids = 0
    failure_reason: str | None = None

    bounded = list(pages)[: max(0, max_pages)]
    for raw in bounded:
        if raw is None:
            return PageAggregationResult(
                items=tuple(merged),
                pages_fetched=pages_fetched,
                complete=False,
                duplicate_ids=tuple(duplicates),
                failed=True,
                failure_reason="page_failure",
                authoritative_total=authoritative,
            )
        envelope = (
            raw
            if isinstance(raw, PaginationEnvelope)
            else extract_pagination_envelope(raw)
        )
        if envelope is None:
            return PageAggregationResult(
                items=tuple(merged),
                pages_fetched=pages_fetched,
                complete=False,
                duplicate_ids=tuple(duplicates),
                failed=True,
                failure_reason="malformed_page",
                authoritative_total=authoritative,
            )

        page_num = envelope.page
        if pages_fetched == 0:
            started_at_first = _is_first_page(page_num)
            if page_num is not None:
                expected_page = page_num
        if page_num is not None:
            if page_num in seen_page_numbers:
                failure_reason = "duplicate_page"
            elif expected_page is not None and page_num != expected_page:
                failure_reason = (
                    "out_of_order"
                    if page_num < expected_page
                    else "missing_intermediate_page"
                )
            seen_page_numbers.add(page_num)
            expected_page = page_num + 1

        if failure_reason is not None:
            return PageAggregationResult(
                items=tuple(merged),
                pages_fetched=pages_fetched,
                complete=False,
                duplicate_ids=tuple(duplicates),
                failed=True,
                failure_reason=failure_reason,
                authoritative_total=authoritative,
            )

        pages_fetched += 1
        if envelope.total_count is not None:
            if (
                authoritative is not None
                and envelope.total_count != authoritative
            ):
                return PageAggregationResult(
                    items=tuple(merged),
                    pages_fetched=pages_fetched,
                    complete=False,
                    duplicate_ids=tuple(duplicates),
                    failed=True,
                    failure_reason="authoritative_total_conflict",
                    authoritative_total=authoritative,
                )
            authoritative = envelope.total_count
        last_has_more = envelope.has_more
        for item in envelope.items:
            item_id = item_stable_id(item)
            if item_id is None:
                missing_stable_ids += 1
                merged.append(item)
                continue
            if item_id in seen:
                duplicates.append(item_id)
                continue
            seen.add(item_id)
            merged.append(item)
        if envelope.has_more is False:
            break

    if missing_stable_ids and authoritative is None:
        # Without stable ids we cannot prove uniqueness → never exact.
        return PageAggregationResult(
            items=tuple(merged),
            pages_fetched=pages_fetched,
            complete=False,
            duplicate_ids=tuple(duplicates),
            failed=False,
            failure_reason="missing_stable_ids",
            authoritative_total=authoritative,
        )

    if duplicates:
        return PageAggregationResult(
            items=tuple(merged),
            pages_fetched=pages_fetched,
            complete=False,
            duplicate_ids=tuple(duplicates),
            failed=False,
            failure_reason="duplicate_ticket_ids",
            authoritative_total=authoritative,
        )

    if authoritative is not None:
        # Owner total is authoritative even mid-walk; uniqueness still
        # required above. Do not recompute from page lengths.
        return PageAggregationResult(
            items=tuple(merged),
            pages_fetched=pages_fetched,
            complete=True,
            duplicate_ids=(),
            failed=False,
            failure_reason=None,
            authoritative_total=authoritative,
        )

    # Explicit last-page signal only closes a walk that started at page 1.
    if (
        last_has_more is False
        and started_at_first
        and pages_fetched > 0
    ):
        return PageAggregationResult(
            items=tuple(merged),
            pages_fetched=pages_fetched,
            complete=True,
            duplicate_ids=(),
            failed=False,
            failure_reason=None,
            authoritative_total=None,
        )

    reason = "partial_unknown"
    if last_has_more is None:
        reason = "unsigned_completeness"
    elif not started_at_first:
        reason = "not_started_at_first_page"
    elif pages_fetched >= max_pages and last_has_more is True:
        reason = "max_pages_exceeded"
    elif last_has_more is True:
        reason = "has_more_remaining"

    return PageAggregationResult(
        items=tuple(merged),
        pages_fetched=pages_fetched,
        complete=False,
        duplicate_ids=(),
        failed=False,
        failure_reason=reason,
        authoritative_total=None,
    )


def resolve_count_semantics(
    envelope: PaginationEnvelope | None,
    *,
    aggregation: PageAggregationResult | None = None,
) -> CountResolution:
    """Map owner page / aggregation evidence to count wording."""
    if aggregation is not None:
        if aggregation.failed:
            return CountResolution(
                kind=CountResolutionKind.PARTIAL_UNKNOWN,
                total=None,
                returned_on_page=aggregation.unique_count,
                has_more=True,
                message=UNKNOWN_TOTAL_MESSAGE,
            )
        if aggregation.authoritative_total is not None:
            return CountResolution(
                kind=CountResolutionKind.AUTHORITATIVE_TOTAL,
                total=aggregation.authoritative_total,
                returned_on_page=aggregation.unique_count,
                has_more=False,
                message=AUTHORITATIVE_COUNT_MESSAGE.format(
                    total=aggregation.authoritative_total
                ),
            )
        if aggregation.complete and not aggregation.duplicate_ids:
            total = aggregation.unique_count
            if total == 0:
                return CountResolution(
                    kind=CountResolutionKind.EMPTY,
                    total=0,
                    returned_on_page=0,
                    has_more=False,
                    message=EMPTY_COUNT_MESSAGE,
                )
            return CountResolution(
                kind=CountResolutionKind.COMPLETE_AGGREGATE,
                total=total,
                returned_on_page=total,
                has_more=False,
                message=COMPLETE_COUNT_MESSAGE.format(total=total),
            )
        return CountResolution(
            kind=CountResolutionKind.PARTIAL_UNKNOWN,
            total=None,
            returned_on_page=aggregation.unique_count,
            has_more=True,
            message=UNKNOWN_TOTAL_MESSAGE,
        )

    if envelope is None:
        return CountResolution(
            kind=CountResolutionKind.PARTIAL_UNKNOWN,
            total=None,
            returned_on_page=0,
            has_more=None,
            message=UNKNOWN_TOTAL_MESSAGE,
        )

    if envelope.total_count is not None:
        return CountResolution(
            kind=CountResolutionKind.AUTHORITATIVE_TOTAL,
            total=envelope.total_count,
            returned_on_page=envelope.returned_count,
            has_more=envelope.has_more,
            message=AUTHORITATIVE_COUNT_MESSAGE.format(
                total=envelope.total_count
            ),
        )

    if envelope.returned_count == 0 and envelope.has_more is not True:
        # Empty last page with page>1 does not prove a zero global total.
        if envelope.has_more is False and not _is_first_page(envelope.page):
            return CountResolution(
                kind=CountResolutionKind.PARTIAL_UNKNOWN,
                total=None,
                returned_on_page=0,
                has_more=False,
                message=UNKNOWN_TOTAL_MESSAGE,
            )
        if envelope.has_more is None:
            return CountResolution(
                kind=CountResolutionKind.PAGE_SLICE_NOT_TOTAL,
                total=None,
                returned_on_page=0,
                has_more=None,
                message=UNKNOWN_TOTAL_MESSAGE,
            )
        return CountResolution(
            kind=CountResolutionKind.EMPTY,
            total=0,
            returned_on_page=0,
            has_more=envelope.has_more,
            message=EMPTY_COUNT_MESSAGE,
        )

    if envelope.has_more is True:
        return CountResolution(
            kind=CountResolutionKind.PARTIAL_UNKNOWN,
            total=None,
            returned_on_page=envelope.returned_count,
            has_more=True,
            message=UNKNOWN_TOTAL_MESSAGE,
        )

    if envelope.has_more is False:
        # A last page in isolation (page>1) is not the query total.
        if _is_first_page(envelope.page):
            total = envelope.returned_count
            return CountResolution(
                kind=CountResolutionKind.COMPLETE_AGGREGATE,
                total=total,
                returned_on_page=total,
                has_more=False,
                message=COMPLETE_COUNT_MESSAGE.format(total=total),
            )
        return CountResolution(
            kind=CountResolutionKind.PARTIAL_UNKNOWN,
            total=None,
            returned_on_page=envelope.returned_count,
            has_more=False,
            message=UNKNOWN_TOTAL_MESSAGE,
        )

    # No has_more signal — page length is not a proven total.
    return CountResolution(
        kind=CountResolutionKind.PAGE_SLICE_NOT_TOTAL,
        total=None,
        returned_on_page=envelope.returned_count,
        has_more=None,
        message=UNKNOWN_TOTAL_MESSAGE,
    )


def personal_scope_response(
    scope: PersonalTicketScope,
    *,
    glpi_link_required: bool = False,
) -> str | None:
    """Deterministic user-facing text for personal-scope gates.

    Returns None when the orchestrator should continue with ordinary
    list/count projection (non-personal / all-visible).
    """
    if glpi_link_required:
        return GLPI_LINK_NO_COUNT
    if scope is PersonalTicketScope.MY_TICKETS_AMBIGUOUS:
        return PERSONAL_SCOPE_CLARIFICATION
    if scope is PersonalTicketScope.ASSIGNED_TO_ME:
        return ASSIGNED_IDENTITY_LIMITATION
    if scope is PersonalTicketScope.REQUESTED_BY_ME:
        return REQUESTER_FILTER_LIMITATION
    return None


def list_header_for_envelope(
    envelope: PaginationEnvelope,
    *,
    prior_excerpt: bool = False,
) -> str:
    """Honest list introduction — never equates page size to total."""
    count = envelope.returned_count
    if prior_excerpt:
        noun = "itens" if count != 1 else "item"
        return f"Recuperei {count} {noun} da orientação anterior:"
    if envelope.has_more is True:
        return PAGE_SLICE_LIST_HEADER.format(count=count)
    noun = "registros" if count != 1 else "registro"
    if envelope.has_more is False:
        return f"Encontrei {count} {noun}:"
    # Unknown pagination completeness — avoid total claim.
    return (
        f"Mostrando {count} {noun} retornados pela fonte "
        f"(total não confirmado nesta página):"
    )


def count_message_for_visible_query(resolution: CountResolution) -> str:
    """Count message for non-personal / all-visible authorized queries."""
    if resolution.kind in {
        CountResolutionKind.AUTHORITATIVE_TOTAL,
        CountResolutionKind.COMPLETE_AGGREGATE,
    }:
        return resolution.message + VISIBLE_NOT_PERSONAL_NOTE
    return resolution.message


def arguments_include_personal_assignee(
    arguments: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(arguments, Mapping):
        return False
    for key, value in arguments.items():
        canon = str(key).strip().lower().replace("-", "_")
        if canon in {"assignee_id", "assigned_user_id"} and value not in (
            None,
            "",
        ):
            return True
    return False


def arguments_include_requester_filter(
    arguments: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(arguments, Mapping):
        return False
    for key, value in arguments.items():
        canon = str(key).strip().lower().replace("-", "_")
        if canon in {"requester_id", "requester"} and value not in (None, ""):
            return True
    return False


def is_ticket_domain_inquiry(input_text: str) -> bool:
    """True when the user message is about tickets/helpdesk/chamados."""
    return bool(_TICKET_DOMAIN_RE.search((input_text or "").strip()))


def schema_supports_ticket_list_action(input_schema: object) -> bool:
    """Owner schema advertises an ``action`` enum including ``tickets``.

    Structural only — never matches on capability/provider display names.
    """
    if not isinstance(input_schema, Mapping):
        return False

    def _walk(node: object, depth: int = 0) -> bool:
        if depth > 5 or not isinstance(node, Mapping):
            return False
        props = node.get("properties")
        if isinstance(props, Mapping):
            action = props.get("action")
            if isinstance(action, Mapping):
                enum_values = action.get("enum")
                if isinstance(enum_values, (list, tuple)):
                    normalized = {
                        str(v).strip().lower() for v in enum_values
                    }
                    if "tickets" in normalized:
                        return True
        for value in list(node.values())[:32]:
            if isinstance(value, Mapping) and _walk(value, depth + 1):
                return True
        return False

    return _walk(input_schema)


def unique_structural_ticket_list_capability(
    capabilities: Sequence[Any],
    input_text: str,
) -> Any | None:
    """Return the sole invocable capability that can list tickets.

    Provider-neutral recovery for ticket COUNT/LIST asks when the owner
    surface advertises exactly one READ schema with ``action=tickets``.
    Returns None for write/ambiguous intents, non-ticket asks, or when
    0/N>1 match — never invents a capability and never picks among
    multiples. Avoids a redundant model capability-selection stage that
    historically exhausted the turn budget before owner READ.
    """
    if classify_result_intent(input_text) not in {
        ResultIntent.COUNT,
        ResultIntent.LIST,
    }:
        return None
    if not is_ticket_domain_inquiry(input_text):
        return None
    matches: list[Any] = []
    for cap in capabilities:
        op = getattr(cap, "operation_class", None)
        op_name = getattr(op, "name", None) or getattr(op, "value", None) or op
        if str(op_name).upper() not in {"READ", "QUERY"}:
            continue
        if schema_supports_ticket_list_action(
            getattr(cap, "input_schema", None)
        ):
            matches.append(cap)
    if len(matches) != 1:
        return None
    return matches[0]
