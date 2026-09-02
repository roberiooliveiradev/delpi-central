"""Amarração NF de frete x NF de origem (SF8010) — vocabulário Protheus.

A SF8010 grava um vínculo por par CT-e x NF de compra. Versões diferentes do
Protheus gravam a série em campos distintos (``F8_SEDIFRE``/``F8_SDOCFRE`` para
o CT-e e ``F8_SERORIG``/``F8_SDOCORI`` para a NF), por isso o candidato usado no
SQL é resolvido por ``COALESCE`` em vez de um campo fixo.

Base Delpi (set/2026): ``F8_SEDIFRE`` e ``F8_SERORIG`` populados; os pares
``F8_SDOCFRE``/``F8_SDOCORI`` existem na tabela e estão 100% vazios.
"""

from __future__ import annotations

# F8_TIPO do vínculo de frete. Outros tipos não entram na análise de frete.
FREIGHT_LINK_TYPE = "F"

# Ordem de preferência para a série. O primeiro campo não vazio vence.
FREIGHT_SERIES_COLUMNS: tuple[str, ...] = ("F8_SEDIFRE", "F8_SDOCFRE")
ORIGIN_SERIES_COLUMNS: tuple[str, ...] = ("F8_SERORIG", "F8_SDOCORI")

# F1_TPCTE do CT-e. Vazio = documento legado, tratado como não reconhecido.
FREIGHT_DOCUMENT_TYPE_NORMAL = "N"

# F1_ESPECIE aceita como CT-e comum. Demais espécies viram exceção.
FREIGHT_DOCUMENT_KIND_NORMAL = "CTE"


def series_coalesce_expr(columns: tuple[str, ...], *, table_alias: str) -> str:
    """Monta ``COALESCE(NULLIF(RTRIM(alias.COL), ''), ...)`` para a série.

    Nomes de coluna vêm sempre destas constantes — nunca de entrada do usuário.
    """
    if not columns:
        raise ValueError("columns não pode ser vazio.")

    candidates = [f"NULLIF(RTRIM({table_alias}.{column}), '')" for column in columns]
    return f"COALESCE({', '.join(candidates)}, '')"
