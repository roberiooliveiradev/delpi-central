"""Catálogo de códigos de Problema de Processo (tipo process-issue).

Fonte canônica dos motivos reportáveis pelo cockpit de produção (P2). O
snapshot da solicitação carrega issueCode — os rótulos PT ficam aqui para
não espalhar strings no domínio/frontend.
"""

from __future__ import annotations

PROCESS_ISSUE_TYPE_CODE = "process-issue"
PROCESS_ISSUE_PERMISSION_PREFIX = "my-requests.process-issue"
PROCESS_ISSUE_PROCESS_PERMISSION = "my-requests.process-issue.process"

ISSUE_CODE_LABELS: dict[str, str] = {
    "work_center_incompatible": "CT / posto não adequado",
    "machine_limitation": "Limitação da máquina ou bancada",
    "tool_not_linked": "Ferramenta não informada ou não vinculada",
    "material_not_linked": "Matéria-prima não vinculada à operação",
    "process_information_missing": "Informação de processo incompleta",
    "other": "Outro problema de processo",
}

ISSUE_CODES: frozenset[str] = frozenset(ISSUE_CODE_LABELS)


def issue_code_label(code: str | None) -> str:
    """Rótulo amigável do motivo; fallback para o próprio código/—."""
    text = str(code or "").strip()
    if not text:
        return "—"
    return ISSUE_CODE_LABELS.get(text, text)
