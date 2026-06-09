# Roadmap — Apresentação generalizada de dados (jun/2026)

Evolução do chat base para **130 rotas ativas** da api-delpi, indo além do viés produto/estoque/estrutura. O usuário escolhe **Automático · Texto · Tabela · Árvore · Gráfico** no input; o sistema deve **respeitar a preferência**, **gerar o visual certo a partir da forma dos dados** e **escalar sem `if` por path** em dezenas de rotas.

Relacionado: [playbook-09-apresentacao-rica.md](./playbook-09-apresentacao-rica.md), [chat-assistant-content-presentation.md](../architecture/chat-assistant-content-presentation.md), [playbook-10-contrato-respostas-api-delpi.md](./playbook-10-contrato-respostas-api-delpi.md), [vocabulary-centralization-jun2026.md](../architecture/vocabulary-centralization-jun2026.md).

---

## 1. Contexto

| Fato | Implicação |
|------|------------|
| **130 operações** OpenAPI (`api-delpi/app/content/openapi_baseline.json`) | Cobertura rica hoje ≈ **família produto + KPIs nomeados**; demais rotas caem em tabela genérica ou texto vazio |
| Playbook 09 entregou **decisor + MFE unificado** | Base existe; falta **generalizar** presenters e **declarar** perfil por entidade/rota |
| UI expõe 5 modos (`useChatPresentationFormat`) | **Lousa/canvas** não aparece no dropdown; `canvas` na API vira `text` |
| Inteligência transversal no **chat base** | Novas regras em serviços canônicos + JSON PT — **não** em prompt de agente nem `if` no MFE |

---

## 2. Diagnóstico — por que parece «só estoque e estrutura»

### 2.1 Onde a lógica está hoje

```
execute_external_action
  → ExternalActionResultPresenter (muitos builders por /analyser, /stock, /structure, status-*)
  → ExecuteExternalActionUseCase._build_presentation_metadata
       primary = tree > chart > kpi > table  (fixo)
       blocos elif por path (factory/production/shipping/exclusivity/analyser)
  → ChatPresentationRoutePolicyService  (tokens /stock, /structure, /analyser, …)
  → ChatPresentationStackOrderService   (plano humanizado — analyser completo; outras rotas parcial)
  → ChatPresentationDecisionService     (data shape + preferência + intent)
  → MFE buildAssistantContentSegments / ChatAssistantContent
```

### 2.2 Causas raiz (prioridade)

| # | Sintoma | Causa no código | Impacto |
|---|---------|-----------------|---------|
| **R1** | Escolhi **Tabela** e veio árvore/texto | `primary_presentation` prioriza **tree** antes de aplicar preferência; stack força narrativa + múltiplos visuais | Preferência altera `selected`, mas **primário** e ordem stack podem contradizer |
| **R2** | **Automático** ignora expectativa | `sessionResponseFormat` vazio → `ChatPresentationRoutePolicyService.resolve_default_preferred_format` com **heurística por path** (`/stock`, `/structure`, …) | Rotas fora da lista não têm default inteligente |
| **R3** | **Gráfico** não aparece | `build_chart_presentation` só em rotas com builder ou `force=True`; KPI/dashboard têm caminho próprio | ~80% das rotas **nunca** expõem `chart` em `availableFormats` |
| **R4** | Resposta «pobre» em HR, quality, commercial | `ChatApiDelpiResponseProfileService` lista entidades KPI/SQL/LMP, mas presenter genérico não monta narrativa/`textPresentation` | Só tabela crua ou KPI isolado |
| **R5** | Chips genéricos ou ausentes | Playbook 07/09 focados em produto operacional; recomendações atadas a `presentationDecision` com dados shape incompletos | Follow-ups não refletem domínio da rota |

### 2.3 Baseline de cobertura (estimativa jun/2026)

| Tier | Rotas / entidades | Apresentação |
|------|-------------------|--------------|
| **A — Rica** | produto (analyser, stock, structure, guide, status-*, listas) | stack, narrativa, múltiplas tabelas, árvore, gráfico pontual |
| **B — KPI/série** | supplies, financial, commercial, production, quality, hr (entidades em `KPI_PRESENT_ENTITIES`) | KPI + gráfico quando série; texto mínimo |
| **C — Genérico** | demais paths do OpenAPI | `build_presentation` tabela + colunas de `column_labels.json` |
| **D — SQL / system / canvas** | `sql_result`, Protheus schema, lousa | texto/markdown ou tabela ad hoc |

**Meta:** elevar **C → B** de forma declarativa, não rota a rota com copy-paste.

---

## 3. Arquitetura alvo

### 3.1 Princípio: **forma dos dados primeiro**, rota como hint

```
                    ┌─────────────────────────────┐
  Payload api-delpi │ meta.entity + responseSchema │
                    └──────────────┬──────────────┘
                                   ▼
              ChatPresentationResponseProfileRegistry  (NOVO — JSON ou OpenAPI ext.)
                     │ perfil: allowedViews, defaultView, stackPlan, narrativeTemplate
                     ▼
              ExternalActionResultPresenter.build_from_profile()
                     │ table | tree | chart | kpi | text markdown
                     ▼
              ChatPresentationDataShapeAnalyzer  (refina availableViews)
                     ▼
              ChatPresentationDecisionService
                     │ user_preference (sessão) > shape > perfil.defaultView
                     ▼
              presentationDecision + stackPresentationPlan
                     ▼
              MFE ChatAssistantContent (render único)
```

- **Perfil de resposta** por `meta.entity` (já usado em Fase 7) — estender para **todas** as entidades mapeadas no presenter.
- **Path** vira apenas *hint* de ordem stack e títulos (`presenter_content.json`), não decisão de tipo visual.
- **`ChatPresentationRoutePolicyService`** → deprecar tokens hardcoded; migrar para perfis declarativos.

### 3.2 Contrato markdown canônico (`textPresentation`)

Narrativa única autorizada pelo backend (nunca LLM solto no MFE):

```json
{
  "type": "markdown",
  "title": "…",
  "markdown": "### Título\n\nParágrafo.\n\n<!-- section:highlights -->\n- bullet\n<!-- /section:highlights -->"
}
```

| Marcador / bloco | Componente MFE | Quando usar |
|------------------|----------------|-------------|
| Prosa simples | markdown | sempre que houver insight ou contexto |
| `<!-- section:* -->` | framing entre visuais | stack humanizado (já no analyser) |
| Tabela em `tablePresentation` | `ChatRichTable` | listagens, comparações |
| `treePresentation` | `ChatRichTree` | `hasHierarchy` ou perfil `treePreferred` |
| `chartPresentation` / subtipos | `ChatRichChart` | temporal, ranking, participação |
| `presentation.type=kpi` | cards KPI | indicador único ou painel |
| `presentation.type=dashboard` | dashboard composto | LMP, eficiência fabril |
| Conteúdo longo / lousa | `canvas` segment | relatório, plano, anexo — **fora** do dropdown atual |

**Regra:** markdown descreve e interpreta; **números repetidos** só em visual (tabela/gráfico/KPI), alinhado ao Playbook 09 §16.

### 3.3 Preferência de sessão — semântica desejada

| UI (`sessionResponseFormat`) | API | Comportamento |
|------------------------------|-----|---------------|
| `auto` | *(omitido)* | `decide()` só com data shape + perfil entidade |
| `text` | `text` | **single** mode: só markdown (+ KPI inline se perfil exigir) |
| `table` | `table` | promover `tablePresentation` a `presentation`; ocultar tree/chart do stack |
| `tree` | `tree` | idem árvore; gerar flatten table auxiliar se perfil permitir |
| `chart` | `chart` | forçar `build_chart_presentation(..., force=True)` quando shape permitir |
| *(futuro)* `canvas` | `canvas` | abrir lousa; não mapear para `text` silenciosamente |

**Correção R1:** extrair `ChatPresentationPrimaryViewService` — aplica preferência **antes** de fixar `metadata.presentation`, com testes por modo.

---

## 4. Fases de implementação

### Fase 0 — Auditoria e matriz (1 sprint, baixo risco)

**Entregas**

- Script `scripts/audit_presentation_coverage.py`: cruza OpenAPI 130 ops × `meta.entity` × `PROFILE_PRESENT_ENTITIES` × testes existentes.
- Matriz CSV/HTML: rota | entidade | tier A/B/C/D | `availableFormats` hoje | gap.
- Casos de regressão em `tests/fixtures/chat_presentation_regression_cases.py` (mín. 1 por domínio: product, supplies, hr, quality, sql).

**Critério de aceite:** visibilidade 100% das rotas; zero código de produto novo.

---

### Fase 1 — Respeitar preferência ponta a ponta (urgente)

**Problema:** R1 + fluxo `auto` vs explícito.

**Tarefas**

1. `ChatPresentationPrimaryViewService.align_metadata_with_preference(metadata, preference)` — chamado em `ExecuteExternalActionUseCase` **após** montar visuais, **antes** `enrich_metadata`.
2. Garantir `sessionResponseFormat` no turno: já injetado em `ChatToolContextExecutionService`; validar persistência MFE → `behaviorInstructions.responseFormat` (chip `kind=format`).
3. Quando preferência = `table|tree|chart|text`: `layoutMode=single` salvo perfil declarar stack explícito.
4. Testes: `test_presentation_session_format_respected.py` — mesma rota `/products/{code}/structure` com 4 preferências → `presentationDecision.selected` e `presentation.type` coerentes.
5. Smoke: `scripts/smoke_presentation_format_refinement.py` estendido para commercial/hr.

**Não fazer:** novo `if` por path no use case — só realinhamento genérico.

---

### Fase 2 — Registry declarativo de perfis (generalização)

**Objetivo:** substituir crescimento de `elif` em `ExecuteExternalActionUseCase` e tokens em `ChatPresentationRoutePolicyService`.

**Artefato:** `app/content/pt-BR/assistant/presentation_profiles.json` (+ loader `ChatPresentationProfileService`).

Exemplo de entrada:

```json
{
  "product_structure": {
    "defaultView": "tree",
    "allowedViews": ["tree", "table", "text", "chart"],
    "stackPlan": "structure",
    "narrative": "product_operational_content.structure",
    "chartPolicy": "composition_donut"
  },
  "supplies_cpv": {
    "defaultView": "kpi",
    "allowedViews": ["kpi", "line_chart", "table", "text"],
    "stackPlan": "kpi_series",
    "narrative": "presenter_content.kpi.supplies_cpv"
  }
}
```

**Tarefas**

1. Gerar esqueleto a partir de `ENTITY_PATH_HINTS` + OpenAPI tags.
2. Migrar regras de `ChatPresentationRoutePolicyService` para perfis (`defaultView`, `viewOrder`).
3. `ChatPresentationStackOrderService` lê `stackPlan` do perfil — analyser vira um plano nomeado, não código especial.
4. Documentar no [assistant-content-catalog.md](../architecture/assistant-content-catalog.md).

**Critério:** adicionar nova rota = editar JSON + schema labels, não Python (salvo shape novo).

---

### Fase 3 — Presenter genérico orientado a schema

**Objetivo:** tier C → B sem builder manual por rota.

**Tarefas**

1. `ExternalActionResultPresenter.build_from_openapi_schema(data, schema, profile)`:
   - detecta lista vs objeto vs série temporal (reuso `ChatPresentationDataShapeAnalyzer`);
   - aplica `column_labels.json` + `schemaExplore` de `sql_intent_vocabulary.json` onde couber.
2. Narrativa mínima via templates em `presenter_content.json` (`generic.listSummary`, `generic.timeSeriesLead`, …).
3. Gráfico automático quando `allowedViews` contém `chart` e shape temporal/categórico (policies já em `ChatPresentationChartPolicyService`).
4. Árvore só quando payload traz `children`/`components` normalizados (`ChatPresentationFieldNormalizationService`).

**Critério:** rotas commercial/quality/hr sem builder dedicado passam a ter texto + (tabela ou gráfico) coerente em **Automático**.

---

### Fase 4 — Markdown stack e componentes estendidos

**Tarefas**

1. Padronizar marcadores `<!-- section:id -->` para **todos** os `stackPlan` (não só analyser).
2. Framing por seção via `presenter_content.json` → `sectionFraming` no metadata (padrão já usado no analyser).
3. **Lousa:** opção UI «Documento» ou reuso modo canvas; parar de mapear `canvas → text` em `ExecuteExternalActionUseCase`.
4. Registrar renderers extras no MFE via `assistantContentRegistry` (checklist, timeline) conforme Playbook 09 P7+.

**MFE:** manter regra — zero `if` de layout fora de `assistantContentLayout.ts` / `chatPresentation.ts`.

---

### Fase 5 — Chips, recomendações e refinamento conversacional

**Tarefas**

1. Generalizar `presentationDecision.recommendations` — chaves em JSON por **família de entidade** (`presenter_content.recommendations.*`), não só produto.
2. Chips pós-resposta: «Ver em gráfico», «Exportar», «Detalhar filial» — derivados de `availableViews` ∩ perfil (Playbook 07).
3. `ChatPresentationFormatRefinementService`: vocabulário migrado para `text_context_vocabulary.json` / `operational_pipeline_vocabulary.json` (evitar duplicata com `ChatToolContextFormatService`).
4. Paginação/consolidação respeita último formato (`ChatPaginationConsolidationService`) — testes cross-turn.

---

### Fase 6 — Cobertura 130 rotas + CI

**Tarefas**

1. Suite parametrizada: uma asserção mínima por entidade (`selected` ∈ `allowedViews`, markdown não vazio quando perfil exige).
2. Gate CI: diff OpenAPI → alerta se nova operação sem perfil.
3. Homologação manual amostral (10 rotas/domínio) documentada em `docs/testing/presentation-homologation-jun2026.md`.
4. Métricas: `% rotas tier B+`, `% turnos com preferência respeitada`, `% stack vs single`.

---

## 5. Mapa de módulos canônicos (onde implementar)

| Mudança | Módulo canônico | Evitar |
|---------|-----------------|--------|
| Escolha visual | `ChatPresentationDecisionService`, **novo** `ChatPresentationPrimaryViewService` | toolbar logic duplicada no MFE |
| Ordem stack | `ChatPresentationStackOrderService` + perfis JSON | ordem fixa no presenter |
| Textos PT | `presenter_content.json`, `product_operational_content.json` | strings em `ExecuteExternalActionUseCase` |
| Colunas/rótulos | `column_labels.json`, `ExternalActionColumnLabelService` | headers hardcoded |
| Render | MFE `assistantProseRendering.ts`, `ChatAssistantContent` | `ChatMessageList` ad hoc |
| Preferência sessão | `ChatToolContextFormatService`, chip `format` na working memory | localStorage só no MFE |

---

## 6. Priorização sugerida

| Ordem | Fase | Valor | Esforço |
|-------|------|-------|---------|
| 1 | **Fase 1** — preferência respeitada | Alto (confiança UI) | Médio |
| 2 | **Fase 0** — matriz 130 rotas | Alto (planejamento) | Baixo |
| 3 | **Fase 2** — registry perfis | Alto (escala) | Alto |
| 4 | **Fase 3** — presenter schema-driven | Alto (generalização) | Alto |
| 5 | **Fase 5** — chips | Médio (UX) | Médio |
| 6 | **Fase 4** — lousa + marcadores | Médio | Médio |
| 7 | **Fase 6** — CI/homologação | Médio (regressão) | Médio |

---

## 7. Critérios de aceite globais

1. Usuário seleciona **Tabela** → resposta principal é tabela em **≥95%** das rotas com dado tabular (amostra homologação).
2. **Automático** não usa tokens `/stock`/`/structure` hardcoded — usa perfil + data shape.
3. Nova rota api-delpi: adicionar perfil JSON documentado; CI falha se ausente.
4. Nenhuma string PT nova em Python de apresentação — catálogo JSON + teste de chave.
5. Agentes de plataforma **herdam** comportamento sem alteração de `system_prompt`.

---

## 8. Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Regressão analyser multi-rota | Manter fixtures `2026-06-apresentacao-multi-rota-produto`; tier A congelado até Fase 2 migrar plano |
| Gráfico enganoso em dados esparsos | Manter `ChatPresentationChartPolicyService` + fallback tabela |
| Payload heterogêneo entre rotas | Normalização em `ChatPresentationFieldNormalizationService` + testes por entidade |
| Duplicação MFE/API textos | sync documentado; presenter_content como fonte |

---

## 9. Referências de código

| Arquivo | Papel |
|---------|-------|
| `execute_external_action_use_case.py` | Montagem metadata; **principal alvo de simplificação** |
| `chat_presentation_route_policy_service.py` | Heurística path — **deprecar** |
| `chat_presentation_decision_service.py` | Decisão final + insight |
| `chat_api_delpi_response_profile_service.py` | Entidades críticas / KPI / SQL |
| `external_action_result_presenter.py` | Builders ricos |
| `chat_tool_context_format_service.py` | Sessão + override pós-tool |
| `useChatPresentationFormat.ts` | Dropdown UI |
| `chatPresentation.ts` / `assistantContentLayout.ts` | Segmentos MFE |

---

## 10. Próximo passo imediato

Abrir **Fase 1** com PR focado:

1. `ChatPresentationPrimaryViewService` + testes structure/stock/analyser/hr.
2. Ajuste copy UI: placeholder do input mencionar modo ativo; opcional badge quando `selected ≠ preferred` (debug).

Atualizar este doc ao concluir cada fase (checkbox no topo).

**Status jun/2026:** ✅ Fase 0 concluída — matriz 130 rotas (`presentation-coverage-baseline.json`, `audit_presentation_coverage.py`). Fase 1 em andamento.

### Fase 0 — entregue

| Artefato | Caminho |
|----------|---------|
| Serviço | `app/domain/services/chat_presentation_coverage_service.py` |
| Script | `scripts/audit_presentation_coverage.py` |
| Baseline | `docs/architecture/presentation-coverage-baseline.json` |
| Fixtures | `tests/fixtures/chat_presentation_regression_cases.py` |
| Testes | `tests/unit/domain/services/test_chat_presentation_coverage_service.py` |
