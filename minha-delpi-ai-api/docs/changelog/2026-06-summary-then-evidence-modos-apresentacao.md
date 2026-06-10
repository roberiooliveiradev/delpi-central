# Changelog — `summary_then_evidence`: narrativa no chat e modos de apresentação (jun/2026)

## Contexto

Pergunta de referência: *«qual o status do produto 90262404 na fábrica hoje?»* (`factory_status`, perfil `summary_then_evidence`).

**Problemas corrigidos:**

1. Card de decisão (`storyPresentation` / `ChatDecisionCard`) **destoava** do fluxo do chat — conteúdo duplicado (card + markdown).
2. Modo **Automático** passou a renderizar tudo como markdown (tabelas GFM, composição em code fence, fallback de gráfico) em vez de componentes ricos.
3. Modo **Painel** repetia tabelas e explicação antes do dashboard.
4. Divisões numeradas («1. Escopo da consulta», «2. Roteiro de produção») quebravam o fluxo conversacional.
5. Painel fabril (`dashboard`) aparecia no **Automático** sem o usuário pedir.
6. Regressão: ao omitir o painel, `tailVisualOrder` ficava vazio — árvore/gráfico viravam blocos `TEXT`/tabela no markdown em vez de componentes nativos.
7. Regressão: MFE `appendTailVisuals` tinha fallback órfão que **reinjetava `dashboard`** mesmo fora do `tailVisualOrder` (allowlist violada).

**Princípio:** em `summary_then_evidence`, a interpretação vive na **prosa do chat**; visuais são **evidência** renderizada por componentes. Markdown embutido (tabelas, árvore, gráfico, composição) é exclusivo do modo **Texto** explícito.

Relacionado: [playbook-13](../roadmap/playbook-13-respostas-humanizadas-dados.md), [chat-assistant-content-presentation.md](../architecture/chat-assistant-content-presentation.md), commit `fe62999f` (narrativa sem card).

---

## Comportamento por modo de sessão

| Modo (`explicitSessionFormat`) | Markdown (`textPresentation`) | Componentes MFE |
|--------------------------------|------------------------------|-----------------|
| **Automático** (ausente / `auto`) | Prosa compacta: resumo, fatos, leitura — **sem** tabelas GFM, composição em fence nem títulos de seção duplicados | TABELA + árvore + gráfico/KPI nativos (`tailVisuals`); `sectionFraming` inline; **sem** `dashboard` |
| **Texto** (`text`) | Markdown completo: tabelas embutidas, composição em code fence, gráfico em markdown quando aplicável | Segmentos visuais suprimidos ou secundários conforme layout texto |
| **Painel** (`dashboard`) | Lead curto (`_compact_native_view_lead`) — sem repetir dados do dashboard | Apenas componente dashboard; `operationalTables` vazio no plano |

### `factory_status` — painel sob demanda, árvore/gráfico nativos

No modo **Automático**, `tailVisualOrder` **não** inclui `dashboard` — o painel fabril só entra com `explicitSessionFormat: "dashboard"`. Em vez de deixar o tail vazio (`dashboard_only`), a API preenche com visuais nativos disponíveis (`kpi`, `tree`, `chart`) e mantém o slot `tailVisuals` no plano. Assim a composição não fica como bloco `TEXT` no markdown: vai para o componente **árvore**; gráficos vão para **gráfico**, não para fallback em tabela no texto.

`finalize_narrative_after_embeds` reaplica o strip de markdown embutido após os serviços de embed (segurança).

### Contrato `tailVisualPolicy: allowlist` (Playbook 13)

A API define no `stackPresentationPlan`:

- `tailVisualOrder` — lista fechada de visuais no tail (`kpi`, `tree`, `chart`; `dashboard` só com Painel explícito)
- `tailVisualPolicy: "allowlist"` — o MFE **não** faz fallback de visuais órfãos

O MFE (`visualSegmentCollector`, `appendTailVisuals`) só materializa `dashboard` quando `explicitSessionFormat: "dashboard"` ou o token está no `tailVisualOrder`.

---

## Módulos canônicos (API)

| Serviço | Mudança |
|---------|---------|
| `ChatPresentationEvidenceFirstLayoutService` | `compose()` sem `storyPresentation`; `_apply_evidence_first_stack_plan` com `tailVisualPolicy: allowlist`; tail sem `dashboard` no Automático; `finalize_narrative_after_embeds` pós-embed |
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
| `presentationStackBlueprint.ts` | `usesStrictTailVisualAllowlist` — sem fallback órfão; `shouldRenderDashboardSegment` no tail |
| `visualSegmentCollector.ts` | Não coleta `dashboard` fora do contrato allowlist |
| `presentationStackPlan.ts` | Parse de `tailVisualPolicy` + `presentationMode` |

---

## Testes de regressão

| Pacote | Arquivo | O que valida |
|--------|---------|--------------|
| API | `test_playbook_presentation_pipeline_regression.py` | Automático: `dashboard` ausente, `tree` no tail, slot `tailVisuals` presente |
| API | `test_chat_presentation_evidence_first_layout_service.py` | Troca `dashboard` por `tree`/`chart`; `finalize_narrative_after_embeds` remove Composição |
| API | `test_chat_rich_presentation_text_service.py` | Strip de visuais embutidos em stack automático |
| API | `test_chat_presentation_table_markdown_service.py` | Embed exige `explicitSessionFormat: "text"` |
| API | `test_chat_presentation_tree_markdown_service.py` | Idem |
| MFE | `richStackPresentation.test.ts` | Strip de Composição em code fence |
| MFE | `presentationStackPlan.humanized.test.ts` | Sem `stackSection`; árvore no tail; **sem dashboard** com allowlist |
| MFE | `visualSegmentCollector.test.ts` | Coleta omite dashboard no Automático; mantém no Painel explícito |

## Commits do arco (jun/2026)

| Hash | Escopo |
|------|--------|
| `fe62999f` | Narrativa no chat sem card de decisão |
| `9aee91bb` | Componentes ricos no Automático; embed markdown só no Texto |
| `0eba2dbc` | Sem divisões numeradas; painel só sob demanda |
| `7fe2fc41` | Árvore/gráfico nativos no tail ao omitir dashboard |

**Nota:** `test_factory_status_auto_quality_matches_fixture_analyst_narrative` pode falhar em `reference_date` no markdown auto — qualidade de narrativa, não regressão de layout.

---

## Validação manual sugerida

1. Nova conversa; pergunta status fabril 90262404.
2. **Automático:** prosa + tabelas + **árvore** + **gráfico** nativos; **sem** bloco `TEXT` de Composição, divisões numeradas nem painel fabril.
3. **Texto:** markdown completo com tabelas e composição.
4. **Painel:** lead curto + dashboard único, sem tabelas soltas repetindo o painel.

Rebuild local:

```bash
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env up --build -d --force-recreate minha-delpi-ai-api minha-delpi-chat gateway
```
