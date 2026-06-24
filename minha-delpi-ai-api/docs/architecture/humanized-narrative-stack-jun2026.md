# Narrativa humanizada em stack — qualquer action (jun/2026)

> **Status histórico (jun/2026):** `ChatPresentationHumanizedNarrativeService` e stack rico tier A foram **removidos** do pipeline. Comentário operacional ativo: `ChatDataInsightEnrichmentService` → `dataAnswer`. Pipeline atual: [`presentation-delivered-pure-jun2026.md`](./presentation-delivered-pure-jun2026.md).

Documentação do padrão **texto interpretativo antes dos painéis** (tabela, KPI, gráfico, árvore, dashboard) para respostas de `execute_external_action`.

Relacionado: [chat-assistant-content-presentation.md](./chat-assistant-content-presentation.md), [assistant-content-catalog.md](./assistant-content-catalog.md), [perguntas-teste-chat-jun2026.md](../testing/perguntas-teste-chat-jun2026.md).

**Commits de referência:** `70d9556f` (stack narrativo global), `cc4ce7d8` (enriquecimento generalizado + precificação).

---

## Princípio

O usuário não deve receber **só** tabelas/gráficos/KPIs. A resposta operacional deve:

1. **Contextualizar** o que foi consultado (escopo).
2. **Resumir** o que importa (panorama / leitura rápida).
3. **Alertar** quando houver risco ou dado suspeito (atenção).
4. **Orientar** o uso dos painéis abaixo (conclusão / hint).
5. **Empilhar** visuais como suporte auditável — não como substituto da prosa.

Agentes e projetos **herdam** o pipeline do chat base; não duplicam lógica no MFE nem no prompt.

---

## Pipeline (API)

```
ExternalActionResultPresenter
  → textPresentation.markdown (rota dedicada ou schema-driven)
ExecuteExternalActionUseCase._build_presentation_metadata
  → ChatPresentationHumanizedNarrativeService.enrich_metadata   ← NOVO (jun/2026)
  → ChatPresentationStackOrderService.enrich_metadata
       → ChatPresentationSectionAvailabilityService (perfis por rota)
       → ChatPresentationStackMarkdownService (marcadores <!-- section:* -->)
  → ChatPresentationDecisionService.enrich_metadata
       → selected=text, layoutMode=stack (política rica)
  → ChatRichPresentationTextService.compact_metadata_text
       → não compacta quando humanizedSections=true
```

### Módulos canônicos

| Módulo | Responsabilidade |
|--------|------------------|
| `ChatPresentationHumanizedNarrativeService` | Enriquece markdown **fino** (≤6 linhas úteis) a partir de tabela profile, KPI e listas — **qualquer rota** exceto estoque e `/pricing` (presenter dedicado) |
| `ChatPresentationSectionAvailabilityService` | `humanizedSections`, `sectionVisibility`, `sectionFraming`, `narrativeOrder` por perfil (`sale_pricing`, `raw_material_price_intelligence`, `factory_status`, …) |
| `ChatPresentationStackMarkdownService` | `apply_generic_humanized_stack_plan`, injeção de `<!-- section:scope -->` e demais marcadores |
| `ChatPresentationRichStackPolicyService` | Default `layoutMode=stack` + `selected=text` quando há markdown + painéis (exceto estoque nativo) |
| `ChatRichPresentationTextService` | `should_compact_narrative` → false; preserva narrativa em stack humanizado |
| `presenters/*_presenter.py` | Narrativa **rica por domínio** (MP, fabril, precificação, …) — fonte primária quando existe |
| `ChatSchemaDrivenPresentationService` | Narrativa mínima tier C/B + hint `panelsBelowHint` |

---

## Contrato `textPresentation` (stack humanizado)

```markdown
### Preço de venda — 90260145

<!-- section:scope -->

Tabelas de preço de venda do produto **90260145** (CHICOTE DE LIGAÇÃO).

**Panorama**

O produto **90260145 — CHICOTE DE LIGAÇÃO** (unidade **MI**) possui **21** tabela(s)…
- Menor preço de venda: **R$ 992,54** — tabela **056** (…)
- Maior preço de venda: **R$ 1.606,36** — …

**Leitura rápida**

Os valores formam uma escada progressiva…

**Pontos de atenção**

1. Teto de preço (`max_price`) zerado…

**Conclusão**

Para o **90260145**, o preço de venda de entrada é **R$ 992,54**…
```

| Seção markdown | Marcador (quando aplicável) | Painel stack abaixo |
|----------------|----------------------------|---------------------|
| Escopo / intro | `<!-- section:scope -->` | — |
| Panorama / ficha resumida | `<!-- section:profile -->` (implícito via título) | tabela `role=profile` |
| Destaques | `<!-- section:highlights -->` | — |
| Detalhe operacional | `<!-- section:guide -->` | tabelas `role=list` / guide |
| Visuais | `<!-- section:structure -->` | KPI, gráfico, árvore, dashboard |
| Atenção | `<!-- section:attention -->` | — |

`stackPresentationPlan.sectionFraming` traz **uma frase** por seção visível (não repete tabela). Textos em `presenter_content.json` → `stackSectionFraming` e `product_operational_content.json` (rotas legadas).

---

## Perfis com narrativa dedicada (presenter)

| Perfil / rota | Presenter | Seções típicas |
|---------------|-----------|----------------|
| `sale_pricing` | `product_pricing_presenter.py` | Panorama, leitura, atenção (teto zero, desconto, vigência), conclusão |
| `raw_material_price_intelligence` | `product_raw_material_price_presenter.py` | Resumo produto, histórico, variação, atenção, recomendação |
| `factory_status` / `production_status` / `shipping_status` | `product_composite_analysis_presenter.py` | Escopo + corpo playbook |
| `cost_impact_simulation` | `product_raw_material_price_presenter.py` (simulador) | Ranking + simulação |
| `stock` | `product_stock_presenter.py` | Resumo + detalhe por filial (exceção: não força text stack default) |
| Tier C/B genérico | `ChatSchemaDrivenPresentationService` | Lead + `panelsBelowHint` |

### Precificação — regras de negócio (jun/2026)

- Template `primarySalePriceLine` usa `{price}` **sem** prefixo `R$` duplicado (`format_field_value` já formata moeda).
- KPI **Maior preço de venda** quando `max_price` cadastrado é zero; **Teto de preço** só quando há `max_price > 0`.
- Árvore de pricing: rótulo `treeTableLeafLabel` sem `R$` duplicado.

---

## Enriquecimento genérico (`ChatPresentationHumanizedNarrativeService`)

Dispara quando:

- Há pelo menos um painel complementar (tabela, KPI ou gráfico);
- Markdown autorizado tem ≤6 linhas de corpo (excluindo título e marcador de escopo);
- Ainda **não** contém `**Panorama**` e `**Pontos de atenção**` juntos;
- Rota **não** é estoque nem `/pricing`.

O serviço monta:

| Bloco | Fonte |
|-------|--------|
| Escopo | linhas já existentes no markdown |
| Panorama | linhas KV da tabela `role=profile` |
| Leitura rápida | cartões de `kpiPresentation` |
| Atenção | heurística (ex.: lista >25 linhas) |
| Conclusão | hint `humanizedNarrative.conclusionPanelsHint` |

Textos: `presenter_content.json` → seção `humanizedNarrative`.

---

## Decisão de apresentação

Para rotas ricas com painéis:

```json
{
  "presentationDecision": {
    "selected": "text",
    "layoutMode": "stack",
    "visualOrder": ["text", "table", "kpi", "chart", "tree", "dashboard"]
  },
  "stackPresentationPlan": {
    "humanizedSections": true,
    "presentationProfile": "product_pricing",
    "sectionVisibility": { "scope": true, "profile": true, "guide": true, "structure": true, "attention": true },
    "sectionFraming": { "scope": "…", "profile": "…", "guide": "…", "structure": "…", "attention": "…" },
    "narrativeOrder": ["lead", "operationalTables", "tailVisuals", "attention"]
  }
}
```

A aba **Completo** no MFE empilha narrativa + painéis na ordem do plano. Abas isoladas (KPI, Gráfico, Árvore) mostram o painel; o usuário deve ter lido o texto em **Completo** ou **Texto** antes.

---

## Testes de regressão

| Arquivo | O que valida |
|---------|----------------|
| `tests/unit/application/use_cases/test_roteiro_rapido_humanization.py` | R1–R5: `humanizedSections`, `layoutMode=stack`, markdown ≥120 chars, sem `R$ R$` |
| `tests/unit/application/use_cases/test_mp_price_10080001_humanization.py` | MP: leitura histórico, atenção, recomendação |
| `tests/unit/domain/services/test_product_pricing_presenter.py` | Panorama, leitura, conclusão, KPI maior preço |
| `tests/unit/domain/services/test_chat_presentation_humanized_narrative_service.py` | Enriquecimento genérico; skip em `/pricing` |
| `tests/unit/domain/services/test_chat_rich_presentation_text_service.py` | Narrativa não compactada em stack humanizado |

Comando:

```bash
docker exec delpi-minha-delpi-ai-api pytest \
  tests/unit/application/use_cases/test_roteiro_rapido_humanization.py \
  tests/unit/application/use_cases/test_mp_price_10080001_humanization.py \
  tests/unit/domain/services/test_product_pricing_presenter.py \
  tests/unit/domain/services/test_chat_presentation_humanized_narrative_service.py \
  -q
```

Smoke manual (E2E): [`perguntas-teste-chat-jun2026.md`](../testing/perguntas-teste-chat-jun2026.md) — R1–R5, especialmente `analise de preço 90260145` (precificação com 21 tabelas).

---

## O que não fazer

- Narrativa só no prompt do agente ou strings no use case.
- `setStreamingStatus` / `<h3>` no MFE para contornar markdown vazio.
- Duplicar `getPresentationTitle` / `stripLeadingMarkdownTitle` fora de `assistantProseRendering.ts`.
- Compactar `textPresentation` quando `humanizedSections=true`.
- KPI de contagem (`Tabelas ativas`) com unidade `R$` no MFE.

---

## Catálogo JSON (novas chaves)

Ver [assistant-content-catalog.md](./assistant-content-catalog.md) — seções `humanizedNarrative`, `stackSectionFraming.byProfile.sale_pricing`, `routes.salePricing` (panorama, leitura, atenção, conclusão).
