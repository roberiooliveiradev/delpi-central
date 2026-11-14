"""Query object for the entry-audit Protheus reads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

_BRANCHES = frozenset({"01", "02"})
_SPECIES = frozenset({"SPED", "CTE"})
_MAX_WINDOW_DAYS = 366
_ACCESS_KEY_LENGTH = 44
_MAX_ACCESS_KEYS_GET = 50
_MAX_ACCESS_KEYS_POST = 500
_DATE_FIELDS = (
    "issue_date",
    "received_date",
    "cancelled_on",
    "entered_on",
)


class EntryAuditQueryError(ValueError):
    """Invalid filter. The route maps this to HTTP 422."""


@dataclass(frozen=True)
class EntryAuditPeriodQuery:
    branch: str
    received_from: str
    received_to: str
    species: tuple[str, ...]
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @classmethod
    def from_query(
        cls,
        *,
        branch: str | None,
        received_from: str | None,
        received_to: str | None,
        species: list[str] | None,
        page: int,
        page_size: int,
    ) -> EntryAuditPeriodQuery:
        normalized_branch = (branch or "").strip()
        if normalized_branch not in _BRANCHES:
            raise EntryAuditQueryError("branch must be 01 or 02.")
        start = _parse_iso(received_from, "received_from")
        end = _parse_iso(received_to, "received_to")
        if start > end:
            raise EntryAuditQueryError("received_from must be on or before received_to.")
        if (end - start).days > _MAX_WINDOW_DAYS:
            raise EntryAuditQueryError("The receipt window cannot exceed 366 days.")
        chosen = _normalize_species(species)
        if page < 1:
            raise EntryAuditQueryError("page must be at least 1.")
        if page_size < 1 or page_size > 200:
            raise EntryAuditQueryError("page_size must be between 1 and 200.")
        return cls(
            branch=normalized_branch,
            received_from=start.strftime("%Y%m%d"),
            received_to=end.strftime("%Y%m%d"),
            species=chosen,
            page=page,
            page_size=page_size,
        )


@dataclass(frozen=True)
class EntryAuditAccessKeyQuery:
    branch: str
    access_keys: tuple[str, ...]

    @classmethod
    def from_values(
        cls,
        *,
        branch: str | None,
        access_keys: list[str] | None,
        limit: int,
    ) -> EntryAuditAccessKeyQuery:
        normalized_branch = (branch or "").strip()
        if normalized_branch not in _BRANCHES:
            raise EntryAuditQueryError("branch must be 01 or 02.")
        chosen: list[str] = []
        for item in access_keys or []:
            key = "".join(character for character in str(item or "") if character.isdigit())
            if not key:
                continue
            if len(key) != _ACCESS_KEY_LENGTH:
                raise EntryAuditQueryError("access_keys must contain 44-digit keys.")
            if key not in chosen:
                chosen.append(key)
        if not chosen:
            raise EntryAuditQueryError("access_keys is required.")
        if len(chosen) > limit:
            raise EntryAuditQueryError(
                f"access_keys accepts at most {limit} keys on this route."
            )
        return cls(branch=normalized_branch, access_keys=tuple(chosen))


def access_key_get_limit() -> int:
    return _MAX_ACCESS_KEYS_GET


def access_key_post_limit() -> int:
    return _MAX_ACCESS_KEYS_POST


def _parse_iso(value: str | None, name: str) -> date:
    text = (value or "").strip()
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise EntryAuditQueryError(f"{name} must be YYYY-MM-DD.") from exc


def _normalize_species(species: list[str] | None) -> tuple[str, ...]:
    raw = species or ["SPED", "CTE"]
    chosen: list[str] = []
    for item in raw:
        code = (item or "").strip().upper()
        if not code:
            continue
        if code not in _SPECIES:
            raise EntryAuditQueryError("species must be SPED or CTE.")
        if code not in chosen:
            chosen.append(code)
    if not chosen:
        raise EntryAuditQueryError("species must be SPED or CTE.")
    return tuple(chosen)


def page_payload(rows: list[dict], *, page: int, page_size: int) -> dict:
    total = int(rows[0]["total_count"]) if rows else 0
    items = []
    for row in rows:
        item = {key: _json_value(key, value) for key, value in row.items() if key != "total_count"}
        items.append(item)
    total_pages = (total + page_size - 1) // page_size if total else 0
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }


def _json_value(key: str, value):
    if key in _DATE_FIELDS:
        return _iso_date(value)
    if hasattr(value, "quantize"):
        return float(value)
    return value


def _iso_date(value) -> str | None:
    text = "" if value is None else str(value).strip()
    if len(text) != 8 or not text.isdigit():
        return None
    return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
