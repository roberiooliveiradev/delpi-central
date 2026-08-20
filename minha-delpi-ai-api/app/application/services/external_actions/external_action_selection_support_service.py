"""Candidatos, ranking e histórico de tools — Fase 3B lote 22."""

from __future__ import annotations

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_manifest_text_service import (
    ExternalActionManifestTextService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
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
                # Sempre anota overlap lexical (não reordena) — score-gap e execute
                # precisam distinguir empate semântico com evidência lexical real.
                return self.ensure_lexical_ranking(message, ranked)
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
                    row["selectionLexicalScore"] = round(lexical, 4)
                scored.append(row)
            return scored

        scored: list[tuple[float, dict]] = []
        for action in candidates:
            row = dict(action)
            lexical = cls.lexical_overlap_score(message, row)
            row["selectionScore"] = round(lexical, 4)
            if lexical > 0:
                row["selectionLexicalMatched"] = True
                row["selectionLexicalScore"] = round(lexical, 4)
                row["selectionReason"] = row.get("selectionReason") or ""
            scored.append((lexical, row))

        scored.sort(
            key=lambda item: (
                -item[0],
                0 if str(item[1].get("method") or "").upper() == "GET" else 1,
                len(str(item[1].get("path") or "")),
            )
        )
        # Sem overlap lexical → lista vazia (evita top-2 com score 0 e score-gap falso).
        return [row for score, row in scored if score > 0]

    @classmethod
    def _lexical_settings(cls) -> dict:
        node = ExternalActionResponseContentService.get_node(
            "actionSelection",
            "lexicalOverlap",
        )
        if not isinstance(node, dict):
            node = {}

        try:
            min_token_len = int(node.get("minTokenLength", 3))
        except (TypeError, ValueError):
            min_token_len = 3

        stopwords_raw = node.get("stopwords") or []
        stopwords = {
            str(item).strip().lower()
            for item in stopwords_raw
            if str(item).strip()
        }

        return {
            "minTokenLength": max(2, min_token_len),
            "stopwords": stopwords,
        }

    @classmethod
    def _tokenize_for_lexical(cls, text: str, *, min_token_len: int) -> list[str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(text)
        if not normalized:
            return []

        raw = (
            normalized.replace("/", " ")
            .replace("-", " ")
            .replace("_", " ")
            .replace("=", " ")
            .replace("|", " ")
            .replace(";", " ")
            .replace(":", " ")
            .replace(",", " ")
            .replace(".", " ")
            .replace("«", " ")
            .replace("»", " ")
        )
        return [
            token
            for token in raw.split()
            if len(token) >= min_token_len
        ]

    @classmethod
    def lexical_overlap_score(cls, message: str, action: dict) -> float:
        settings = cls._lexical_settings()
        min_len = int(settings["minTokenLength"])
        stopwords = settings["stopwords"]

        tokens = [
            token
            for token in cls._tokenize_for_lexical(message, min_token_len=min_len)
            if token not in stopwords
        ]
        if not tokens:
            return 0.0

        haystack = ExternalActionManifestTextService.build_for_lexical(action)
        hay_tokens = set(
            cls._tokenize_for_lexical(haystack, min_token_len=min_len)
        )
        if not hay_tokens:
            return 0.0

        hits = 0.0
        for token in tokens:
            # Match por token inteiro — nunca substring (evita ok∈playbook).
            if token in hay_tokens:
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
