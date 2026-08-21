"""Memória episódica de sessão — Playbook memória e contexto (Fase 6)."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.services.chat_memory_intent_content_service import (
    ChatMemoryIntentContentService,
)


class ChatEpisodicMemoryService:
    @classmethod
    def max_episodes(cls) -> int:
        return ChatMemoryIntentContentService.limit_int(
            "episodic", "limits", "maxEpisodes", default=8
        )

    @classmethod
    def _recall_re(cls):
        return ChatMemoryIntentContentService.compile_pattern(
            "episodic", "patterns", "recall"
        )

    @classmethod
    def _delete_re(cls):
        return ChatMemoryIntentContentService.compile_pattern(
            "episodic", "patterns", "delete"
        )

    @classmethod
    def _save_re(cls):
        return ChatMemoryIntentContentService.compile_pattern(
            "episodic", "patterns", "save"
        )

    @classmethod
    def apply_pre_turn(
        cls,
        snapshot: dict,
        *,
        message: str | None,
        previous_messages: list[Any] | None = None,
    ) -> dict:
        result = dict(snapshot)
        episodes = cls._load_episodes(previous_messages)
        stored = list(result.get("episodicMemory") or [])

        if stored:
            merged = {str(item.get("episodeId") or ""): item for item in episodes if isinstance(item, dict)}

            for item in stored:
                if not isinstance(item, dict):
                    continue

                key = str(item.get("episodeId") or "")

                if key:
                    merged[key] = item

            episodes = list(merged.values())[-cls.max_episodes() :]

        normalized = (message or "").strip()

        if cls._delete_re().search(normalized):
            result["episodicMemory"] = []
            result["episodicMemoryCleared"] = True
            result["episodicRecall"] = None
            return result

        result["episodicMemory"] = episodes[-cls.max_episodes() :]

        if normalized and cls._recall_re().search(normalized):
            recall = cls.find_relevant_episode(normalized, episodes, snapshot=result)

            if recall:
                result["episodicRecall"] = recall
            else:
                result["episodicRecallMissing"] = True

        return result

    @classmethod
    def apply_post_turn(
        cls,
        snapshot: dict,
        *,
        message: str | None,
        answer: str | None = None,
    ) -> dict:
        result = dict(snapshot)

        if result.get("episodicMemoryCleared"):
            return result

        episodes = list(result.get("episodicMemory") or [])
        normalized = (message or "").strip()
        force_save = bool(cls._save_re().search(normalized))

        if not cls._should_record(result, answer=answer, force=force_save):
            return result

        episode = cls._build_episode(result, message=message, answer=answer)
        episodes = [episode, *episodes]
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in episodes:
            if not isinstance(item, dict):
                continue

            key = str(item.get("episodeId") or "")

            if not key or key in seen:
                continue

            seen.add(key)
            deduped.append(item)

        result["episodicMemory"] = deduped[: cls.max_episodes()]
        result["lastEpisodeRecorded"] = episode.get("episodeId")
        return result

    @classmethod
    def find_relevant_episode(
        cls,
        message: str,
        episodes: list[dict[str, Any]],
        *,
        snapshot: dict | None = None,
    ) -> dict[str, Any] | None:
        lowered = message.lower()
        snap = snapshot or {}
        task = (snap.get("conversationState") or {}).get("activeTask")
        task_type = str(task.get("type") or "").lower() if isinstance(task, dict) else ""

        best: tuple[float, dict[str, Any]] | None = None

        for episode in reversed(episodes):
            if not isinstance(episode, dict):
                continue

            score = 0.2
            topic = str(episode.get("topic") or "").lower()
            summary = str(episode.get("summary") or "").lower()
            episode_task = str(episode.get("taskType") or "").lower()

            if topic and topic in lowered:
                score += 0.5

            if episode_task and episode_task in lowered:
                score += 0.4

            if task_type and episode_task == task_type:
                score += 0.35

            if "playbook" in lowered and "playbook" in summary:
                score += 0.25

            if "sql" in lowered and "sql" in episode_task:
                score += 0.25

            if score > (best[0] if best else 0):
                best = (score, episode)

        if not best:
            return None

        recalled = dict(best[1])
        recalled["recallConfidence"] = min(1.0, best[0])
        recalled["recallLimitation"] = (
            "Episódio recuperado apenas desta sessão; não substitui documentação oficial."
        )
        return recalled

    @classmethod
    def build_recall_direct_answer(cls, snapshot: dict | None) -> str | None:
        if not (snapshot or {}).get("episodicRecallMissing"):
            return None

        return (
            "Não encontrei um episódio anterior parecido nesta sessão. "
            "Descreva a tarefa (playbook, SQL, e-mail) ou peça para salvar o progresso atual."
        )

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        recall = (snapshot or {}).get("episodicRecall")

        if isinstance(recall, dict):
            summary = str(recall.get("summary") or "").strip()
            topic = str(recall.get("topic") or "").strip()
            confidence = recall.get("recallConfidence")

            lines = ["Episódio recuperado desta sessão:"]

            if topic:
                lines.append(f"- Assunto: {topic}.")

            if summary:
                lines.append(f"- Resumo: {summary[:400]}.")

            if confidence is not None:
                lines.append(f"- Confiança: {float(confidence):.2f}.")

            limitation = str(recall.get("recallLimitation") or "").strip()

            if limitation:
                lines.append(f"- Limite: {limitation}")

            return "\n".join(lines)

        episodes = (snapshot or {}).get("episodicMemory") or []

        if len(episodes) >= 2:
            last = episodes[0] if isinstance(episodes[0], dict) else {}

            if last.get("summary"):
                return (
                    "Episódios recentes nesta sessão:\n"
                    f"- Último: {str(last.get('summary'))[:220]}"
                )

        return None

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        episodes = (snapshot or {}).get("episodicMemory") or []
        recall = (snapshot or {}).get("episodicRecall")

        return {
            "storedCount": len(episodes),
            "recallActive": bool(recall),
            "recallTopic": (recall or {}).get("topic") if isinstance(recall, dict) else None,
            "missingRecall": bool((snapshot or {}).get("episodicRecallMissing")),
        }

    @classmethod
    def _load_episodes(cls, previous_messages: list[Any] | None) -> list[dict[str, Any]]:
        episodes: list[dict[str, Any]] = []

        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)
            snapshot = metadata.get("contextSnapshot")

            if not isinstance(snapshot, dict):
                continue

            stored = snapshot.get("episodicMemory")

            if isinstance(stored, list) and stored:
                episodes = [dict(entry) for entry in stored if isinstance(entry, dict)]
                break

        return episodes[-cls.max_episodes() :]

    @classmethod
    def _should_record(
        cls,
        snapshot: dict,
        *,
        answer: str | None,
        force: bool = False,
    ) -> bool:
        from app.domain.services.chat_context_safety_filter_service import (
            ChatContextSafetyFilterService,
        )

        if not ChatContextSafetyFilterService.should_allow_persist(snapshot):
            return False

        if force:
            return True

        snippet = (answer or "").strip()

        if len(snippet) < 120:
            return False

        state = snapshot.get("conversationState") or {}
        task = state.get("activeTask")

        if not isinstance(task, dict):
            return False

        return str(task.get("status") or "") in ("in_progress", "completed")

    @classmethod
    def _build_episode(
        cls,
        snapshot: dict,
        *,
        message: str | None,
        answer: str | None,
    ) -> dict[str, Any]:
        state = snapshot.get("conversationState") or {}
        task = state.get("activeTask") if isinstance(state.get("activeTask"), dict) else {}
        summary = str(answer or "").strip()[:400]
        topic = str(state.get("activeTopic") or task.get("label") or "tarefa").strip()
        objective = str(task.get("objective") or message or "").strip()

        if objective and objective not in summary:
            summary = f"{objective[:160]}. {summary}"[:400]

        return {
            "episodeId": str(uuid.uuid4()),
            "taskType": task.get("type"),
            "topic": topic,
            "summary": summary or objective or (message or "")[:200],
            "confidence": 0.75,
            "source": "session_snapshot",
        }

    @staticmethod
    def _message_metadata(message: Any) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}
