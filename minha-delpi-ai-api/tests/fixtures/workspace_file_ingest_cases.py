"""Casos de regressão — Playbook 17 (ingestão unificada de arquivos)."""

READING_STATUS_LABEL_CASES = [
    ("indexed", "Indexado"),
    ("indexing", "Indexando para consulta"),
    ("uploaded", "Processando leitura"),
    ("unsupported", "Leitura limitada"),
    ("index_failed", "Falha na leitura"),
    ("default", "Aguardando envio"),
]

POLICY_EXTENSION_CASES = [
    ("session_attachment", "foto.png", True),
    ("session_attachment", "doc.pdf", True),
    ("agent_source", "foto.png", False),
    ("agent_source", "manual.pdf", True),
    ("project_source", "planilha.xlsx", True),
    ("context_paste", "ctx.csv", True),
    ("context_paste", "ctx.pdf", False),
    ("global_knowledge", "policy.md", True),
]

STORAGE_SCOPE_CASES = [
    ("project", "project_source"),
    ("agent", "agent_source"),
    ("unknown", "project_source"),
]
