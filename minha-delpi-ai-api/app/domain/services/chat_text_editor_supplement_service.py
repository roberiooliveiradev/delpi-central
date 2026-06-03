"""Supplements de prompt por subtipo — playbook editor textual (Fases 2–4)."""

from __future__ import annotations

from typing import Any


class ChatTextEditorSupplementService:
    """Templates estruturados sem duplicar orquestração do ChatTextTaskService."""

    _BLOCKS: dict[str, str] = {
        "text_letter": (
            "Carta formal: [Local], [data]; destinatário; corpo objetivo; fechamento. "
            "Placeholders para nome, cargo e número de documento se ausentes."
        ),
        "text_report": (
            "Relatório: # Relatório, ## Contexto, ## Achados, ## Conclusão/Recomendações. "
            "Use «não informado» para lacunas; não invente métricas."
        ),
        "text_documentation": (
            "Documentação: # Título, ## Objetivo, ## Escopo, ## Passo a passo numerado, "
            "## Cuidados. Preserve termos técnicos e siglas."
        ),
        "text_explain": (
            "Explicação: definição clara, por que importa, exemplo breve. "
            "Mantenha precisão; não simplifique além do pedido."
        ),
        "text_eli5": (
            "ELI5: analogia simples + definição correta em uma frase final. "
            "Evite infantilizar; não distorça o conceito."
        ),
        "text_action_plan": (
            "Plano de ação: tabela ou lista | Ação | Responsável | Prazo |. "
            "Use [responsável] e [prazo] quando não informados."
        ),
        "text_adapt_audience": (
            "Adapte vocabulário e profundidade ao público indicado "
            "(executivo, produção, cliente, fornecedor, técnico)."
        ),
        "text_minutes": (
            "Ata: # Ata, data, participantes, pauta, decisões, pendências (responsável/prazo só se citados)."
        ),
        "text_announcement": (
            "Comunicado: # Comunicado, título, corpo objetivo, próximo passo se houver."
        ),
        "text_checklist": (
            "Checklist: itens `- [ ]` com verbo no infinitivo; agrupe por tema se necessário."
        ),
        "text_table": (
            "Tabela markdown com cabeçalhos claros; use | coluna | quando houver "
            "comparação, prazos, responsáveis ou status."
        ),
        "text_memorandum": (
            "Memorando: Para/De/Assunto, corpo objetivo, encaminhamento e prazo se informado."
        ),
        "text_conversation_doc": (
            "Transforme o histórico da conversa em documento estruturado; preserve fatos citados."
        ),
        "text_three_versions": (
            "Entregue três versões nomeadas: Formal, Direta e Cordial; mesmo sentido em todas."
        ),
        "text_before_after": (
            "Use seções ## Antes, ## Depois e ## O que mudou com explicação objetiva."
        ),
        "text_translate": (
            "Tradução natural; preserve termos técnicos e siglas quando indicado."
        ),
        "text_compare": (
            "Compare versões em tabela por critério; indique melhor opção e justificativa breve."
        ),
        "text_review_quality": (
            "Revisão: avalie clareza, tom e estrutura; sugira versão melhorada e pontos de atenção."
        ),
    }

    @classmethod
    def build_block(cls, ctx: dict[str, Any] | None) -> str | None:
        if not isinstance(ctx, dict):
            return None

        subtype = str(ctx.get("subtype") or "").strip()
        block = cls._BLOCKS.get(subtype)

        if not block:
            return None

        audience = ctx.get("audience")

        if audience:
            block = f"{block} Público-alvo: {audience}."

        tone = ctx.get("tone")

        if tone:
            block = f"{block} Tom: {tone}."

        return block

    @classmethod
    def suggest_canvas_for_subtype(cls, subtype: str | None, *, answer: str | None = None) -> bool:
        if subtype in {
            "text_email_create",
            "text_minutes",
            "text_report",
            "text_letter",
            "text_documentation",
            "text_announcement",
        }:
            return len((answer or "").split()) >= 80

        return False
