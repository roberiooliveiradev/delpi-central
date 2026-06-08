from __future__ import annotations

from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from transformometro_client import TransformometroApiClient


class TransformometroTransformaMaisGateway:
    def __init__(self, client: TransformometroApiClient | None = None) -> None:
        self._client = client or TransformometroApiClient()

    def get_process_summary(
        self,
        *,
        filial_id: str | None,
        start_date: str | None,
        end_date: str | None,
        authorization: str | None = None,
    ) -> dict:
        return self._client.get_engineering_summary(
            params={
                "filial_id": filial_id,
                "start_date": start_date,
                "end_date": end_date,
            },
            authorization=authorization or bearer_authorization_from_context(),
        )
