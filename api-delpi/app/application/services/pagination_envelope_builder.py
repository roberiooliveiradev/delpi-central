"""Canonical pagination envelope builder for api-delpi responses."""

from __future__ import annotations

from typing import Any, Literal

PaginationShape = Literal["paged_count", "overfetch", "has_next", "full_tree"]


class PaginationEnvelopeBuilder:
    """Build nested ``pagination`` dicts without ad-hoc literals in use cases."""

    @staticmethod
    def build(
        *,
        shape: PaginationShape,
        page: int | None = None,
        page_size: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        total: int | None = None,
        total_pages: int | None = None,
        returned: int | None = None,
        is_complete: bool | None = None,
        has_next: bool | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if shape == "paged_count":
            payload = PaginationEnvelopeBuilder.paged_count(
                page=page or 1,
                page_size=page_size if page_size is not None else (limit or 50),
                total=total or 0,
                total_pages=total_pages,
            )
        elif shape == "overfetch":
            if is_complete is None:
                raise ValueError("overfetch shape requires is_complete")
            payload = PaginationEnvelopeBuilder.overfetch(
                limit=limit if limit is not None else (page_size or 50),
                offset=offset or 0,
                returned=returned if returned is not None else 0,
                is_complete=is_complete,
                total=total,
            )
        elif shape == "has_next":
            if has_next is None and is_complete is None:
                raise ValueError("has_next shape requires has_next or is_complete")
            payload = PaginationEnvelopeBuilder.has_next(
                page=page or 1,
                page_size=page_size if page_size is not None else (limit or 50),
                has_next=bool(has_next) if has_next is not None else (not bool(is_complete)),
            )
        elif shape == "full_tree":
            payload = PaginationEnvelopeBuilder.full_tree(
                page_size=page_size,
                returned=returned,
                is_complete=True if is_complete is None else is_complete,
            )
        else:
            raise ValueError(f"Unknown pagination shape: {shape}")
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def paged_count(
        *,
        page: int,
        page_size: int,
        total: int,
        total_pages: int | None = None,
    ) -> dict[str, Any]:
        pages = total_pages
        if pages is None:
            pages = (total + page_size - 1) // page_size if page_size and total else 0
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": pages,
            "is_complete": page >= pages if pages else True,
        }

    @staticmethod
    def overfetch(
        *,
        limit: int,
        offset: int,
        returned: int,
        is_complete: bool,
        total: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "returned": returned,
            "is_complete": is_complete,
        }
        if total is not None:
            payload["total"] = total
        return payload

    @staticmethod
    def has_next(*, page: int, page_size: int, has_next: bool) -> dict[str, Any]:
        return {
            "page": page,
            "page_size": page_size,
            "is_complete": not bool(has_next),
        }

    @staticmethod
    def full_tree(
        *,
        page_size: int | None = None,
        returned: int | None = None,
        is_complete: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"is_complete": is_complete}
        if page_size is not None:
            payload["page_size"] = page_size
        if returned is not None:
            payload["returned"] = returned
        return payload
