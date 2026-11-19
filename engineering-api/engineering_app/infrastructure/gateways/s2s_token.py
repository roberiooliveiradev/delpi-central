"""S2S service token provider — credencial client-credentials desta API.

Fonte única do JWT S2S que a Engineering API apresenta à api-delpi em
``X-Delpi-Service-Authorization``: a autorização do contrato BFF é o
cliente técnico + escopos, enquanto o Bearer humano delegado permanece
o ator de negócio (``codusr``/auditoria). Cache process-wide; falha no
provider deve propagar — nunca degrada para token legado compartilhado.
"""

from __future__ import annotations

import threading

from delpi_auth.service_token_provider import ClientCredentialsTokenProvider

_provider_lock = threading.Lock()
_shared_provider: ClientCredentialsTokenProvider | None = None


def get_s2s_service_token() -> str:
    """Token client-credentials desta API (cache process-wide)."""
    global _shared_provider
    if _shared_provider is None:
        with _provider_lock:
            if _shared_provider is None:
                _shared_provider = ClientCredentialsTokenProvider.from_env()
    return _shared_provider.get_token()


def reset_s2s_provider() -> None:
    """Test hook — descarta o provider cacheado para recarregar env."""
    global _shared_provider
    with _provider_lock:
        _shared_provider = None
