from __future__ import annotations

from abc import ABC, abstractmethod


class AppConfigPort(ABC):
    """Flags e limites usados pelo domain sem importar Settings."""

    @abstractmethod
    def chat_external_action_direct_response_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_direct_response_stream_chunk_chars(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_direct_response_stream_delay_ms(self) -> int:
        raise NotImplementedError
