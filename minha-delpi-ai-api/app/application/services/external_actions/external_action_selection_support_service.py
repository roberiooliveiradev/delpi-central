"""Candidatos, ranking e histórico de tools — Fase 3B lote 22."""

from __future__ import annotations

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_manifest_text_service import (
    ExternalActionManifestTextService,
)


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
        from app.domain.services.external_actions.external_action_candidate_discovery_service import (
            ExternalActionCandidateDiscoveryService,
        )

        allowed = {str(item) for item in allowed_action_ids}
        by_id: dict[str, dict] = {}

        for action in self.repository.find_candidate_actions(
            message,
            limit=limit,
            allowed_action_ids=allowed_action_ids,
        ):
            action_id = str(action.get("actionId") or "")
            if action_id in allowed:
                by_id[action_id] = action

        markers = ExternalActionCandidateDiscoveryService.resolve_path_markers(message)
        list_actions = getattr(self.repository, "list_actions", None)
        if markers and callable(list_actions):
            for action in list_actions():
                action_id = str(action.get("actionId") or "")
                if action_id not in allowed or action_id in by_id:
                    continue
                path = str(action.get("path") or "").lower()
                operation_id = str(action.get("operationId") or "").lower()
                if any(
                    marker.lower() in path or marker.lower() in operation_id
                    for marker in markers
                ):
                    by_id[action_id] = action

        results = list(by_id.values())
        if markers:
            return results[: max(limit, 120)]
        return results[:limit]

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
            ranked = self.semantic_ranker.rank(
                message,
                candidates,
                allowed_action_ids=allowed_action_ids,
            )
            if ranked and any(action.get("selectionScore") is not None for action in ranked):
                return ranked
            return self.ensure_lexical_ranking(message, ranked or candidates)

        return self.ensure_lexical_ranking(message, candidates)

    @classmethod
    def ensure_lexical_ranking(cls, message: str, candidates: list[dict]) -> list[dict]:
        """Reordena por overlap lexical quando não há score semântico."""
        if not candidates:
            return []

        if any(action.get("selectionScore") is not None for action in candidates):
            # Já ranqueado semanticamente — só anexa flag lexical auxiliar.
            scored = []
            for action in candidates:
                row = dict(action)
                lexical = cls.lexical_overlap_score(message, row)
                if lexical > 0:
                    row["selectionLexicalMatched"] = True
                scored.append(row)
            return scored

        scored: list[tuple[float, dict]] = []
        for action in candidates:
            row = dict(action)
            lexical = cls.lexical_overlap_score(message, row)
            row["selectionScore"] = round(lexical, 4)
            if lexical > 0:
                row["selectionLexicalMatched"] = True
                row["selectionReason"] = row.get("selectionReason") or ""
            scored.append((lexical, row))

        scored.sort(
            key=lambda item: (
                -item[0],
                0 if str(item[1].get("method") or "").upper() == "GET" else 1,
                len(str(item[1].get("path") or "")),
            )
        )
        return [row for _, row in scored]

    @classmethod
    def lexical_overlap_score(cls, message: str, action: dict) -> float:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        tokens = [
            token
            for token in normalized.replace("/", " ").replace("-", " ").replace("_", " ").split()
            if len(token) >= 2
        ]
        if not tokens:
            return 0.0

        haystack = ChatMessageNormalizationService.normalize_for_matching(
            ExternalActionManifestTextService.build(action).lower()
        )

        hits = 0.0
        for token in tokens:
            if token in haystack:
                # Tokens mais específicos pesam mais.
                hits += 1.0 + min(len(token), 12) * 0.05
        return hits

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
