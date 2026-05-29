"""Mapa de cobertura: GPT_instructions (api-delpi-py) × conhecimento do agente minha-delpi-chat."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GptInstructionCoverage(str, Enum):
    INDEXED_AGENT = "indexed_agent"
    INDEXED_GLOBAL = "indexed_global"
    PARTIAL = "partial"
    PROMPT_POLICY = "prompt_policy"
    MISSING = "missing"
    SKIP = "skip"


@dataclass(frozen=True)
class GptInstructionEntry:
    source_file: str
    coverage: GptInstructionCoverage
    indexed_as: str | None
    notes: str
    ingest_to_agent: bool = False
    tags: tuple[str, ...] = ()


# Estado conhecido em 29/05/2026 (agente minha-delpi-chat + base global).
GPT_INSTRUCTIONS_COVERAGE: tuple[GptInstructionEntry, ...] = (
    GptInstructionEntry(
        "api-delpi-rotas-agente.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "api-delpi-rotas-agente.md",
        "Guia curado minha-delpi (não vem da pasta GPT_instructions); 5 chunks no agente.",
        ingest_to_agent=False,
        tags=("rotas", "operacional"),
    ),
    GptInstructionEntry(
        "Analista SQL DELPI — Produção, Suprimentos e Perdas.txt",
        GptInstructionCoverage.PARTIAL,
        "Analista SQL DELPI — Produção, Suprimentos e Perdas.txt",
        "Playbook SQL customizado no agente; complementa mas não substitui data_sql_api_instructions.md.",
        ingest_to_agent=False,
        tags=("sql", "producao"),
    ),
    GptInstructionEntry(
        "Analista SQL DELPI — Oportunidades, Processos e Estágios LMP.txt",
        GptInstructionCoverage.PARTIAL,
        "Analista SQL DELPI — Oportunidades, Processos e Estágios LMP.txt",
        "Playbook SQL LMP/engenharia no agente.",
        ingest_to_agent=False,
        tags=("sql", "lmp"),
    ),
    GptInstructionEntry(
        "data_sql_api_instructions.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "data_sql_api_instructions.md",
        "Guia completo POST /data/sql, SC2010, exemplos de produção — ingerido via sync_gpt_instructions_knowledge.py.",
        ingest_to_agent=True,
        tags=("sql", "data", "producao"),
    ),
    GptInstructionEntry(
        "product_api_instructions.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "product_api_instructions.md",
        "Detalhe por rota/tabela Protheus; paths adaptados para api-delpi atual.",
        ingest_to_agent=True,
        tags=("produtos", "operacional"),
    ),
    GptInstructionEntry(
        "system_api_instructions.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "system_api_instructions.md",
        "Metadados SX2/SX3; descoberta de tabelas antes de SQL.",
        ingest_to_agent=True,
        tags=("sistema", "sql"),
    ),
    GptInstructionEntry(
        "GPT_instructions.md",
        GptInstructionCoverage.INDEXED_GLOBAL,
        "GPT_instructions.md",
        "Regras gerais do agente GPT; escopo global (company-knowledge), 9 chunks.",
        ingest_to_agent=False,
        tags=("comportamento",),
    ),
    GptInstructionEntry(
        "O_ARQUITETO_DO_CODIGO.md",
        GptInstructionCoverage.INDEXED_GLOBAL,
        "O_ARQUITETO_DO_CODIGO.md",
        "Identidade/plataforma; escopo global.",
        ingest_to_agent=False,
        tags=("plataforma",),
    ),
    GptInstructionEntry(
        "Normas_Tecnicas_DELPI.md",
        GptInstructionCoverage.MISSING,
        None,
        "Normas técnicas; recomendado base global (admin), não agent_source.",
        ingest_to_agent=False,
        tags=("normas",),
    ),
    GptInstructionEntry(
        "drawing_analyser_instructions.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "drawing_analyser_instructions.md",
        "Analyser / desenhos técnicos; rotas /products/{code}/analyser.",
        ingest_to_agent=True,
        tags=("engenharia", "analyser"),
    ),
    GptInstructionEntry(
        "drawing_analyser_instructions_full.md",
        GptInstructionCoverage.SKIP,
        None,
        "Versão estendida; preferir drawing_analyser_instructions.md no agente geral.",
        ingest_to_agent=False,
        tags=("engenharia",),
    ),
    GptInstructionEntry(
        "drawing_rules_delpi.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "drawing_rules_delpi.md",
        "Regras gráficas de desenho.",
        ingest_to_agent=True,
        tags=("engenharia", "desenho"),
    ),
    GptInstructionEntry(
        "drawing_requirements_delpi.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "drawing_requirements_delpi.md",
        "Requisitos obrigatórios em desenhos.",
        ingest_to_agent=True,
        tags=("engenharia", "desenho"),
    ),
    GptInstructionEntry(
        "validation_rules_delpi.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "validation_rules_delpi.md",
        "Critérios de conformidade automática.",
        ingest_to_agent=True,
        tags=("engenharia", "qualidade"),
    ),
    GptInstructionEntry(
        "Understanding DELPI Intermediate Product Codes.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "Understanding DELPI Intermediate Product Codes.md",
        "Codificação intermediários 50xx.",
        ingest_to_agent=True,
        tags=("produtos", "engenharia"),
    ),
    GptInstructionEntry(
        "diretrizes_criacao_de_descricao.md",
        GptInstructionCoverage.INDEXED_AGENT,
        "diretrizes_criacao_de_descricao.md",
        "Padronização de descrições de produto.",
        ingest_to_agent=True,
        tags=("produtos", "normas"),
    ),
    GptInstructionEntry(
        "instructions.md",
        GptInstructionCoverage.SKIP,
        None,
        "Aponta para GPT_instructions.md; sem conteúdo próprio.",
        ingest_to_agent=False,
    ),
)


class GptInstructionsCoverageService:
    @classmethod
    def entries(cls) -> tuple[GptInstructionEntry, ...]:
        return GPT_INSTRUCTIONS_COVERAGE

    @classmethod
    def agent_ingest_sources(cls) -> tuple[GptInstructionEntry, ...]:
        return tuple(entry for entry in GPT_INSTRUCTIONS_COVERAGE if entry.ingest_to_agent)

    @classmethod
    def find_by_source(cls, source_file: str) -> GptInstructionEntry | None:
        for entry in GPT_INSTRUCTIONS_COVERAGE:
            if entry.source_file == source_file:
                return entry
        return None

    @classmethod
    def build_markdown_report(cls) -> str:
        lines = [
            "# Mapa GPT_instructions × agente minha-delpi-chat",
            "",
            "Gerado a partir de `GptInstructionsCoverageService`. "
            "Reindexe com `scripts/sync_gpt_instructions_knowledge.py`.",
            "",
            "| Fonte (api-delpi-py) | Cobertura | Indexado como | Ação |",
            "|----------------------|-----------|---------------|------|",
        ]

        coverage_labels = {
            GptInstructionCoverage.INDEXED_AGENT: "✅ agente",
            GptInstructionCoverage.INDEXED_GLOBAL: "✅ global",
            GptInstructionCoverage.PARTIAL: "⚠️ parcial",
            GptInstructionCoverage.PROMPT_POLICY: "📋 policy",
            GptInstructionCoverage.MISSING: "❌ ausente",
            GptInstructionCoverage.SKIP: "⏭️ omitir",
        }

        for entry in GPT_INSTRUCTIONS_COVERAGE:
            action = "ingerir no agente" if entry.ingest_to_agent else "—"
            lines.append(
                f"| `{entry.source_file}` | {coverage_labels[entry.coverage]} | "
                f"{entry.indexed_as or '—'} | {action} |"
            )

        lines.extend(["", "## Notas por documento", ""])

        for entry in GPT_INSTRUCTIONS_COVERAGE:
            lines.append(f"### `{entry.source_file}`")
            lines.append(f"- **Cobertura:** {entry.coverage.value}")
            if entry.indexed_as:
                lines.append(f"- **Indexado:** `{entry.indexed_as}`")
            lines.append(f"- **Notas:** {entry.notes}")
            if entry.tags:
                lines.append(f"- **Tags:** {', '.join(entry.tags)}")
            lines.append("")

        return "\n".join(lines)
