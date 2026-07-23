"""Formatação canônica de datas de calendário na borda HTTP (resposta).

Contrato: ``YYYY-MM-DD`` (ISO). SQL/TOTVS permanece em ``YYYYMMDD``.
Query params de entrada não passam por este serviço.
"""

from __future__ import annotations

from typing import Any, Iterable

from app.shared.utils.spreadsheet_date import format_date_iso

# Chaves comuns de data de calendário em payloads operacionais.
COMMON_RESPONSE_DATE_KEYS = frozenset(
    {
        "start_date",
        "end_date",
        "date_start",
        "date_end",
        "date_end_exclusive",
        "reference_date",
        "issue_date",
        "loss_date",
        "data_limite",
        "homolog_date",
        "limit_date",
        "next_start_date",
        "panel_start_date",
        "closing_base_date",
        "official_closure_date",
        "last_revision_date",
        "last_sale_date",
        "first_billing_date",
        "last_purchase_date",
        "proposal_date",
        "data_emissao",
        "data_proposta",
        "data",
    }
)


class ResponseDateFormatService:
    """Serializa datas de calendário para ISO ``YYYY-MM-DD`` na resposta HTTP."""

    @staticmethod
    def format_date(value: Any) -> str | None:
        """Converte YYYYMMDD / ISO / dd/mm/yyyy / date → ``YYYY-MM-DD``. Vazio → None."""
        return format_date_iso(value)

    @classmethod
    def format_payload_dates(
        cls,
        payload: dict[str, Any],
        keys: Iterable[str] | None = None,
        *,
        recursive: bool = False,
    ) -> dict[str, Any]:
        """Copia o dict formatando chaves de data para ISO."""
        target_keys = frozenset(keys) if keys is not None else COMMON_RESPONSE_DATE_KEYS
        out = dict(payload)
        for key in target_keys:
            if key not in out:
                continue
            current = out.get(key)
            if current is None or isinstance(current, (dict, list)):
                continue
            formatted = cls.format_date(current)
            if formatted is not None:
                out[key] = formatted
            elif isinstance(current, str) and not current.strip():
                out[key] = None
        if recursive:
            for key, value in list(out.items()):
                if isinstance(value, dict):
                    out[key] = cls.format_payload_dates(
                        value, target_keys, recursive=True
                    )
                elif isinstance(value, list):
                    out[key] = [
                        cls.format_payload_dates(item, target_keys, recursive=True)
                        if isinstance(item, dict)
                        else item
                        for item in value
                    ]
        return out

    @classmethod
    def format_period_dict(cls, period: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(period, dict):
            return period
        return cls.format_payload_dates(
            period,
            ("start", "end", "date_start", "date_end", "data_inicio", "data_fim"),
        )

    @classmethod
    def format_items(cls, items: list[Any] | None) -> list[Any]:
        if not items:
            return []
        return [
            cls.format_payload_dates(item) if isinstance(item, dict) else item
            for item in items
        ]
