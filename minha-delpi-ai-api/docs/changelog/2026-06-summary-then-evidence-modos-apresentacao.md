# Changelog — `summary_then_evidence`: narrativa no chat e modos de apresentação (jun/2026)

## Contexto

Pergunta de referência: *«qual o status do produto 90262404 na fábrica hoje?»* (`factory_status`, perfil `summary_then_evidence`).

**Problemas corrigidos:**

1. Card de decisão (`storyPresentation` / `ChatDecisionCard`) **destoava** do fluxo do chat — conteúdo duplicado (card + markdown).
2. Modo **Automático** passou a renderizar tudo como markdown (tabelas GFM, composição em code fence, fallback de gráfico) em vez de componentes ricos.
3. Modo **Painel** repetia tabelas e explicação antes do dashboard.
4. Divisões numeradas («1. Escopo da consulta», «2. Roteiro de produção») quebravam o fluxo conversacional.
5. Painel fabril (`dashboard`) aparecia no **Automático** sem o usuário pedir.

**Princípio:** em `summary_then_evidence`, a interpretação vive na **prosa do chat**; visuais são **evidência** renderizada por componentes. Markdown embutido (tabelas, árvore, gráfico, composição) é exclusivo do modo **Texto** explícito.

Relacionado: [playbook-13](../roadmap/playbook-13-respostas-humanizadas-dados.md), [chat-assistant-content-presentation.md](../architecture/chat-assistant-content-presentation.md), commit `fe62999f` (narrativa sem card).

---

## Comportamento por modo de sessão

| Modo (`explicitSessionFormat`) | Markdown (`textPresentation`) | Componentes MFE |
|--------------------------------|------------------------------|-----------------|
| **Automático** (ausente / `auto`) | Prosa compacta: resumo, fatos, leitura — **sem** tabelas GFM, composição em fence nem títulos de seção duplicados | TABELA e árvore como evidência; `sectionFraming` vira prosa inline antes de cada bloco; **sem** `dashboard` no tail |
| **Texto** (`text`) | Markdown completo: tabelas embutidas, composição em code fence, gráfico em markdown quando aplicável | Segmentos visuais suprimidos ou secundários conforme layout texto |
| **Painel** (`dashboard`) | Lead curto (`_compact_native_view_lead`) — sem repetir dados do dashboard | Apenas componente dashboard; `operationalTables` vazio no plano |

### `factory_status` — painel sob demanda

No modo **Automático**, `tailVisualOrder` **não** inclui `dashboard` — o painel fabril só entra com `explicitSessionFormat: "dashboard"` (composer **Painel** ou pedido explícito). Tabelas e árvore permanecem como evidência com texto explicativo inline (sem divisões «1. Escopo…» / «2. Roteiro…»).

---

## Módulos canônicos (API)

| Serviço | Mudança |
|---------|---------|
| `ChatPresentationEvidenceFirstLayoutService` | `compose()` sem `storyPresentation`; `_resolve_evidence_first_tail_visual_order` omite `dashboard` no Automático; `_prune_empty_tail_visual_slot` remove slot `tailVisuals` vazio; `_apply_native_view_stack_plan` para Painel explícito |
| `ChatRichPresentationTextService` | `prepare_evidence_first_chat_narrative`: em stack automático remove embutidos de tabela/árvore/gráfico/composição; em `explicitSessionFormat=dashboard` compacta lead |
| `ChatPresentationTableMarkdownService` | `should_embed_in_markdown` — embed só com Texto explícito |
| `ChatPresentationTreeMarkdownService` | Idem |
| `ChatPresentationChartMarkdownService` | Idem |

---

## Módulos canônicos (MFE)

| Módulo | Mudança |
|--------|---------|
| `assistantContentDecisionLayer.ts` | `withDecisionLayer` não injeta card quando perfil é `summary_then_evidence` |
| `chatPresentation.ts` | `stripCompositionCodeFenceFromMarkdown`, `stripChartMarkdownFallbackFromMarkdown`; `stripRichUiRedundantProseFromMarkdown` quando há `treePresentation`/`chartPresentation` |
| `presentationStackBlueprint.ts` | Sem `stackSection` numerado em `summary_then_evidence`; `sectionFraming` vira prosa antes das tabelas; painel omitido no tail automático |

---

## Testes de regressão

| Pacote | Arquivo | O que valida |
|--------|---------|--------------|
| API | `test_playbook_presentation_pipeline_regression.py` | `tailVisualOrder` vazio em `summary_then_evidence` automático; `["dashboard"]` só fora do modo |
| API | `test_chat_presentation_evidence_first_layout_service.py` | Omite dashboard no Automático; mantém com `explicitSessionFormat: "dashboard"` |
| API | `test_chat_rich_presentation_text_service.py` | Strip de visuais embutidos em stack automático |
| API | `test_chat_presentation_table_markdown_service.py` | Embed exige `explicitSessionFormat: "text"` |
| API | `test_chat_presentation_tree_markdown_service.py` | Idem |
| MFE | `richStackPresentation.test.ts` | Strip de Composição em code fence |
| MFE | `presentationStackPlan.humanized.test.ts` | Sem `stackSection` numerado em `summary_then_evidence`; framing inline antes da tabela |

**Nota:** `test_factory_status_auto_quality_matches_fixture_analyst_narrative` pode falhar em `reference_date` no markdown auto — qualidade de narrativa, não regressão de layout.

---

## Validação manual sugerida

1. Nova conversa; pergunta status fabril 90262404.
2. **Automático:** prosa no topo + frases explicativas + tabelas/árvore; **sem** divisões numeradas nem painel fabril.
3. **Texto:** markdown completo com tabelas e composição.
4. **Painel:** lead curto + dashboard único, sem tabelas soltas repetindo o painel.

Rebuild local:

```bash
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env up --build -d --force-recreate minha-delpi-ai-api minha-delpi-chat gateway
```
