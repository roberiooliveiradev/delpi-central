"""Convenções Delpi — apontamento de operação em chão de fábrica (HZA010).

A ``HZA010`` registra o início e o fim de cada operação apontada no coletor do
PCP. É a única fonte que responde "esta operação está sendo produzida agora?".

Sonda no TOTVS Delpi (ago/2026):

- A tabela física é ``HZA010`` — **não** existe ``SHZA010``.
- A chave casa 1:1 com a alocação da ``SH8010``:
  ``HZA_FILIAL``/``HZA_OP``/``HZA_OPERAC`` = ``H8_FILIAL``/``H8_OP``/``H8_OPER``.
- ``HZA_STATUS`` ``1`` = em andamento (sem ``HZA_DTFIM``), ``2`` = encerrado com
  apontamento gerado (``HZA_IDAPON`` preenchido) e ``3`` = encerrado sem gerar
  apontamento (descartado). Só ``1`` significa produção em curso.
- ``HZA_TPTRNS`` ``1`` = transação de mão de obra e ``2`` = de máquina (traz o
  recurso em ``HZA_RECUR``). Ambos indicam a operação rodando.
- ``HZA_OPERAD`` é o **usuário Protheus** (``SYS_USR.USR_ID``), não a matrícula
  do RH: ``SRA010`` não cobre esses códigos.

Doc canônica: api-delpi/docs/api/padroes-totvs/apontamento-operacao-hza.md
"""

from __future__ import annotations

OPERATION_APPOINTMENT_TABLE = "HZA010"

APPOINTMENT_STATUS_RUNNING = "1"
APPOINTMENT_STATUS_CLOSED = "2"
APPOINTMENT_STATUS_DISCARDED = "3"

APPOINTMENT_TYPE_LABOR = "1"
APPOINTMENT_TYPE_MACHINE = "2"

# Turno noturno cruza a meia-noite, então "produzindo agora" precisa de folga de
# mais de um dia. Acima disso o registro aberto é apontamento esquecido: a base
# acumula milhares deles desde 2023 e marcá-los como ativos mentiria na tela.
ACTIVE_APPOINTMENT_LOOKBACK_DAYS = 2

# Janela para dizer "esta operação já passou por produção" sem varrer a tabela
# inteira a cada consulta.
APPOINTMENT_HISTORY_LOOKBACK_DAYS = 30

# Marcador ordenável que elege o apontamento ativo mais recente numa única
# agregação: HZA_DTINI (8) + HZA_HRINI (8) + HZA_OPERAD (6) + nome do operador.
# O nome viaja junto porque resolver SYS_USR fora do agregado, contra a SH8
# inteira, custava mais de um minuto por consulta.
ACTIVE_MARKER_DATE_LENGTH = 8
ACTIVE_MARKER_TIME_LENGTH = 8
ACTIVE_MARKER_OPERATOR_LENGTH = 6

PRODUCTION_STATUS_IN_PROGRESS = "in_progress"
PRODUCTION_STATUS_STARTED = "started"
PRODUCTION_STATUS_NOT_STARTED = "not_started"


def active_appointment_predicate_sql(alias: str, *, since_placeholder: str = "?") -> str:
    """Predicado SQL de apontamento em curso (aberto e dentro da recência)."""
    return (
        f"{alias}.HZA_STATUS = '{APPOINTMENT_STATUS_RUNNING}'"
        f" AND LTRIM(RTRIM(ISNULL({alias}.HZA_DTFIM, ''))) = ''"
        f" AND {alias}.HZA_DTINI >= {since_placeholder}"
    )


def _fixed_width_sql(expr: str, width: int) -> str:
    return f"LEFT(ISNULL({expr}, '') + '{' ' * width}', {width})"


def active_marker_sql(alias: str, *, operator_name_expr: str) -> str:
    """Chave ordenável do apontamento — o MAX elege o início mais recente.

    Largura fixa nos três primeiros segmentos para que o fatiamento por offset
    não dependa do padding do driver nem de campo vazio. O nome do operador vai
    por último, com tamanho livre.
    """
    return " + ".join(
        (
            _fixed_width_sql(f"{alias}.HZA_DTINI", ACTIVE_MARKER_DATE_LENGTH),
            _fixed_width_sql(f"{alias}.HZA_HRINI", ACTIVE_MARKER_TIME_LENGTH),
            _fixed_width_sql(f"{alias}.HZA_OPERAD", ACTIVE_MARKER_OPERATOR_LENGTH),
            operator_name_expr,
        )
    )


def split_active_marker(marker: str | None) -> tuple[str, str, str, str]:
    """Marcador → (data YYYYMMDD, hora HH:MM:SS, código e nome do operador)."""
    text = marker or ""
    if len(text.strip()) < ACTIVE_MARKER_DATE_LENGTH:
        return "", "", "", ""
    date_end = ACTIVE_MARKER_DATE_LENGTH
    time_end = date_end + ACTIVE_MARKER_TIME_LENGTH
    operator_end = time_end + ACTIVE_MARKER_OPERATOR_LENGTH
    return (
        text[:date_end].strip(),
        text[date_end:time_end].strip(),
        text[time_end:operator_end].strip(),
        text[operator_end:].strip(),
    )
