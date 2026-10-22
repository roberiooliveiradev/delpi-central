"""Use case — authenticated consumer looks up a CNPJ via the configured source.

Order matters: input validation, then the shared limiter (consumer/cnpj/
global in one atomic acquisition), then the provider. A blocked or
unavailable limiter never reaches the external provider.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from app.application.contracts import CnpjDataSource, InvalidTaxIdError
from app.domain.external_data import digits_only


class LookupCnpjUseCase:
    def __init__(self, *, provider: CnpjDataSource, limiter: Any) -> None:
        self._provider = provider
        self._limiter = limiter

    def execute(
        self,
        *,
        tax_id: str,
        consumer: str,
        correlation_id: str,
    ) -> Mapping:
        normalized = digits_only(tax_id)
        if len(normalized) != 14:
            # X0/S1: digits-only numeric CNPJ; alphanumeric forms are an
            # explicit incompatibility, never a silent fallback.
            raise InvalidTaxIdError("tax id is not a numeric 14-digit CNPJ")

        cnpj_key = hashlib.sha256(normalized.encode()).hexdigest()[:20]
        self._limiter.acquire_many(
            [
                ("consumer", consumer or "unknown"),
                ("cnpj", cnpj_key),
                ("global", "all"),
            ]
        )
        return self._provider.fetch(normalized, correlation_id=correlation_id)
