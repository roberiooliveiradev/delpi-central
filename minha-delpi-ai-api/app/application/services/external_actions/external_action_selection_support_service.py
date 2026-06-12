"""Candidatos, ranking e histórico de tools — Fase 3B lote 22."""

from __future__ import annotations


class ExternalActionSelectionSupportService:
    def __init__(self, repository, *, semantic_ranker=None) -> None:
        self.repository = repository
        self.semantic_ranker = semantic_ranker

    def list_allowed_candidates(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        limit: int,
    ) -> list[dict]:
        allowed = {str(item) for item in allowed_action_ids}

        return [
            action
            for action in self.repository.find_candidate_actions(
                message,
                limit=limit,
                allowed_action_ids=allowed_action_ids,
            )
            if str(action.get("actionId")) in allowed
        ]

    def rank_candidates(
        self,
        message: str,
        candidates: list[dict],
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]:
        if not candidates:
            return []

        if self.semantic_ranker:
            return self.semantic_ranker.rank(
                message,
                candidates,
                allowed_action_ids=allowed_action_ids,
            )

        return candidates

    def find_allowed_actions_by_path_token(
        self,
        *,
        path_token: str,
        operation_token: str,
        allowed_action_ids: list[str],
        method: str = "GET",
    ) -> list[dict]:
        token = str(path_token or "").lower().strip()
        op_token = str(operation_token or "").lower().strip()
        allowed = {str(item) for item in allowed_action_ids}

        if not allowed or (not token and not op_token):
            return []

        matches: list[dict] = []
        list_actions = getattr(self.repository, "list_actions", None)

        if not callable(list_actions):
            return []

        for action in list_actions():
            if str(action.get("actionId")) not in allowed:
                continue

            if str(action.get("method") or "").upper() != method.upper():
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if token and token in path:
                matches.append(action)
                continue

            if op_token and op_token in operation_id:
                matches.append(action)
                continue

            if token and token.replace("-", "_") in operation_id:
                matches.append(action)

        return matches

    def find_catalog_actions_by_path_token(
        self,
        *,
        path_token: str,
        operation_token: str = "",
        provider_key: str | None = "api-delpi",
        method: str = "GET",
    ) -> list[dict]:
        token = str(path_token or "").lower().strip()
        op_token = str(operation_token or "").lower().strip()

        if not token and not op_token:
            return []

        list_actions = getattr(self.repository, "list_actions", None)

        if not callable(list_actions):
            return []

        matches: list[dict] = []

        for action in list_actions(provider_key=provider_key):
            if str(action.get("method") or "").upper() != method.upper():
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if token and token in path:
                matches.append(action)
                continue

            if op_token and op_token in operation_id:
                matches.append(action)
                continue

            if token and token.replace("-", "_") in operation_id:
                matches.append(action)

        return matches

    @staticmethod
    def resolve_previous_external_action_id(
        previous_messages: list | None,
        *,
        path_fragment: str,
    ) -> str | None:
        fragment = str(path_fragment or "").strip().lower()

        if not fragment:
            return None

        for item in reversed((previous_messages or [])[-14:]):
            metadata = (
                item.get("metadata")
                if isinstance(item, dict)
                else getattr(item, "metadata", None)
            )

            if not isinstance(metadata, dict):
                continue

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").lower()

                if fragment not in path:
                    continue

                action_id = tool_meta.get("actionId")

                if action_id:
                    return str(action_id)

        return None
