"""Sinalização de resultado incompleto em respostas operacionais (playbook_report)."""

from __future__ import annotations

from typing import Any, Callable


class ChatOperationalResultCompletenessService:
    @classmethod
    def resolve_pagination(cls, root: dict[str, Any]) -> dict[str, Any] | None:
        pagination = root.get("pagination")

        if isinstance(pagination, dict):
            return pagination

        return None

    @classmethod
    def branch_filter_applied(cls, root: dict[str, Any]) -> bool | None:
        summary = root.get("summary")

        if isinstance(summary, dict) and "branch_filter_applied" in summary:
            return bool(summary.get("branch_filter_applied"))

        if isinstance(summary, dict):
            branch = summary.get("branch")

            if branch is not None:
                return bool(str(branch).strip())

        return None

    @classmethod
    def is_incomplete(cls, root: dict[str, Any]) -> bool:
        pagination = cls.resolve_pagination(root)

        if isinstance(pagination, dict):
            if pagination.get("is_complete") is False:
                return True

            if pagination.get("is_complete") is True:
                return False

            total = pagination.get("total")
            returned = pagination.get("returned")

            if total is not None and returned is not None:
                return int(returned) < int(total)

            limit = pagination.get("limit")

            if limit is not None and returned is not None:
                return int(returned) >= int(limit)

        summary = root.get("summary")

        if isinstance(summary, dict) and summary.get("is_complete") is False:
            return True

        return False

    @classmethod
    def build_notice_lines(
        cls,
        root: dict[str, Any],
        *,
        text: Callable[..., str],
    ) -> list[str]:
        if not cls.is_incomplete(root):
            return []

        pagination = cls.resolve_pagination(root) or {}
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        returned = pagination.get("returned", summary.get("total_records", 0))
        limit = pagination.get("limit")
        total = pagination.get("total")
        branch_applied = cls.branch_filter_applied(root)
        lines: list[str] = []

        if branch_applied is False:
            lines.append(
                text(
                    "incompleteResultNoBranchFilter",
                    returned=str(returned),
                    limit=str(limit or "—"),
                )
            )
        elif total is not None:
            lines.append(
                text(
                    "incompleteResultWithTotal",
                    returned=str(returned),
                    total=str(total),
                    limit=str(limit or "—"),
                )
            )
        else:
            lines.append(
                text(
                    "incompleteResult",
                    returned=str(returned),
                    limit=str(limit or "—"),
                )
            )

        hint = text("incompleteResultHint")

        if hint:
            lines.append(hint)

        return lines
