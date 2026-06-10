# Changelog — `summary_then_evidence`: narrativa no chat e modos de apresentação (jun/2026)

## Contexto

Pergunta de referência: *«qual o status do produto 90262404 na fábrica hoje?»* (`factory_status`, perfil `summary_then_evidence`).

**Problemas corrigidos:**

1. Card de decisão (`storyPresentation` / `ChatDecisionCard`) **destoava** do fluxo do chat — conteúdo duplicado (card + markdown).
2. Modo **Automático** passou a renderizar tudo como markdown (tabelas GFM, composição em code fence, fallback de gráfico) em vez de componentes ricos.
3. Modo **Painel** repetia tabelas e explicação antes do dashboard.

**Princípio:** em `summary_then_evidence`, a interpretação vive na **prosa do chat**; visuais são **evidência** renderizada por componentes. Markdown embutido (tabelas, árvore, gráfico, composição) é exclusivo do modo **Texto** explícito.

Relacionado: [playbook-13](../roadmap/playbook-13-respostas-humanizadas-dados.md), [chat-assistant-content-presentation.md](../architecture/chat-assistant-content-presentation.md), commit `fe62999f` (narrativa sem card).

---

## Comportamento por modo de sessão

| Modo (`explicitSessionFormat`) | Markdown (`textPresentation`) | Componentes MFE |
|--------------------------------|------------------------------|-----------------|
| **Automático** (ausente / `auto`) | Prosa compacta: resumo, fatos, leitura — **sem** tabelas GFM, seção Composição, fences ` ```text `, fallback de gráfico nem seções operacionais tituladas que duplicam painéis | TABELA, árvore, gráfico, dashboard conforme `stackPresentationPlan` e `tailVisualOrder` |
| **Texto** (`text`) | Markdown completo: tabelas embutidas, composição em code fence, gráfico em markdown quando aplicável | Segmentos visuais suprimidos ou secundários conforme layout texto |
| **Painel** (`dashboard`) | Lead curto (`_compact_native_view_lead`) — sem repetir dados do dashboard | Apenas componente dashboard; `operationalTables` vazio no plano |

### `factory_status` — ordem do tail

`tailVisualOrder` delega a `ChatPresentationStackOrderService`: para status fabril o tail é **`["dashboard"]`**, não apenas `chart`.

---

## Módulos canônicos (API)

| Serviço | Mudança |
|---------|---------|
| `ChatPresentationEvidenceFirstLayoutService` | `compose()` não gera `storyPresentation`; `tailVisualOrder` via stack order; `_apply_native_view_stack_plan` para Painel (`tableRoleOrder` vazio, sem `operationalTables`) |
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
| `presentationStackBlueprint.ts` | `operationalTableRoles` vazio se `tableRoleOrder` vazio; sem `dashboardExplanation` duplicado; sem `chartExplanation` quando tail é só dashboard |

---

## Testes de regressão

| Pacote | Arquivo | O que valida |
|--------|---------|--------------|
| API | `test_playbook_presentation_pipeline_regression.py` | `tailVisualOrder` → `["dashboard"]` em factory_status |
| API | `test_chat_rich_presentation_text_service.py` | Strip de visuais embutidos em stack automático |
| API | `test_chat_presentation_table_markdown_service.py` | Embed exige `explicitSessionFormat: "text"` |
| API | `test_chat_presentation_tree_markdown_service.py` | Idem |
| MFE | `richStackPresentation.test.ts` | Strip de Composição em code fence |

**Nota:** `test_factory_status_auto_quality_matches_fixture_analyst_narrative` pode falhar em `reference_date` no markdown auto — qualidade de narrativa, não regressão de layout.

---

## Validação manual sugerida

1. Nova conversa; pergunta status fabril 90262404.
2. **Automático:** prosa no topo + tabela/árvore/gráfico/dashboard como componentes; sem card de decisão.
3. **Texto:** markdown completo com tabelas e composição.
4. **Painel:** lead curto + dashboard único, sem tabelas soltas repetindo o painel.

Rebuild local:

```bash
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env up --build -d --force-recreate minha-delpi-ai-api minha-delpi-chat gateway
```
