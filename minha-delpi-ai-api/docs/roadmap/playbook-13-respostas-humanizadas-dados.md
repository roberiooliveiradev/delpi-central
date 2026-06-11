# Playbook 13 — Apresentação humanizada e generalizada de dados

**Projeto:** Minha DELPI Chat IA  
**Escopo:** qualquer resposta baseada em dados — financeiro, vendas, estoque, produção, atendimento, RH, projetos, qualidade, indicadores, relatórios, integrações, APIs ou bases internas.  
**Status:** P1–P5 entregues (jun/2026) · **P6 planejada** — MFE render-only (sem lógica duplicada)  
**Público:** backend, frontend MFE, revisores de PR, agentes Cursor

> **Regra de ouro:** a IA não deve mostrar primeiro os dados. Deve primeiro explicar o que os dados significam. A apresentação visual é **evidência** da resposta, não substituto da interpretação.

```text
Dados brutos → interpretação estruturada → decisão de visual → narrativa humana → evidências auditáveis
```

Relacionado:

- [`chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) — pipeline único herdado por agentes e projetos
- [`humanized-narrative-stack-jun2026.md`](../architecture/humanized-narrative-stack-jun2026.md) — narrativa antes dos painéis
- [`playbook-09-apresentacao-rica.md`](./playbook-09-apresentacao-rica.md) — decisão de formato, insight, data shape
- [`playbook-12-apresentacao-declarativa-refatoracao.md`](./playbook-12-apresentacao-declarativa-refatoracao.md) — perfis declarativos e stack (onda 1 concluída)
- [`playbook-10-contrato-respostas-api-delpi.md`](./playbook-10-contrato-respostas-api-delpi.md) — contrato api-delpi → presenter
- [`assistant-content-catalog.md`](../architecture/assistant-content-catalog.md) — bundles JSON PT-BR

**Regras Cursor obrigatórias:** `chat-intelligence-base.mdc`, `centralized-rules-first.mdc`, `assistant-content-json.mdc`, `clean-architecture-chat-api.mdc`.

---

## 1. Objetivo

Evoluir a apresentação do Minha DELPI Chat para que **qualquer** retorno com dados seja convertido em resposta clara, humana, visual e orientada à decisão.

A IA deve explicar:

```text
O que foi encontrado.
O que isso significa.
Qual é o ponto de atenção.
Qual é o próximo passo recomendado.
Quais evidências sustentam a conclusão.
```

**Critérios de sucesso:**

| Métrica | Hoje (jun/2026) | Alvo |
|---------|-----------------|------|
| Conclusão antes dos visuais | Parcial (`<!-- section:summary -->` + `dataCommentary`) | 100% dos turnos com dados |
| Camada semântica (`dataAnswer`) | `dataCommentary` parcial | `dataAnswer` unificado em metadata |
| Perfis com interpretação estruturada | `factory_status`, `stock`, `production_status`, `shipping_status` | ≥ 90% rotas tier A/B + shapes genéricos |
| Decisão por forma dos dados | `ChatPresentationDataShapeAnalyzer` + perfis | Score auditável em `presentationDecision.scores` |
| Preferência explícita ponta a ponta | Composer + `ChatPresentationPrimaryViewService` | Pipeline ordenado (§5) sem drift API↔MFE |
| Visual com propósito | `reason` parcial | `purpose` + pergunta respondida por visual |
| Recomendações clicáveis | Chips removidos pós-resposta; JSON parcial | `recommendations[]` com `label` + `query` |
| Testes por shape | Casos por rota (P1–P16) | Fixture por shape genérico (§17) |
| Auditoria de cobertura | `audit_presentation_coverage.py` (rotas) | + colunas narrativa/limitações/recomendações |

---

## 2. Princípio de arquitetura

Inteligência **no chat base** — agentes adicionam restrições; não reimplementam narrativa nem decisão de formato.

### 2.1 Pipeline alvo

```text
Dados brutos (api-delpi / SQL / action)
  → ChatDataInsightService                    ← interpretação estruturada (dataAnswer)     [P1]
  → ChatPresentationDataShapeAnalyzer         ← forma dos dados (shape)                  [existe]
  → Presenter / visual builders               ← evidências (table/chart/tree/kpi/…)      [existe]
  → ChatPresentationDecisionService           ← preferência + score + primário           [P3]
  → ChatPresentationHumanizedNarrativeService ← narrativa markdown                       [P1 evoluir]
  → ChatPresentationStackOrderService         ← stack summary_then_evidence              [existe]
  → MFE ChatAssistantContent                  ← DecisionCard / story / painéis           [P4]
  → LLM                                       ← complemento; nunca substituto base
```

### 2.2 Separação de responsabilidades

| Camada | Responsabilidade | Não faz |
|--------|------------------|---------|
| **Insight** (`ChatDataInsightService`) | Significado: fatos, análise, hipótese, risco, métricas derivadas, limitações, `visualHints` | Renderizar tabela/gráfico |
| **Presenter** | Montar `presentation`, `tablePresentation`, `chartPresentation`, … | Decidir «o que significa» para o usuário |
| **Decisor** (`ChatPresentationDecisionService`) | Formato primário, score, `purpose`, ordem do stack | Texto PT hardcoded |
| **MFE** | Renderizar segmentos na ordem do metadata | Decidir formato, suprimir visuais, strip de markdown, dedup estrutural |

### 2.3 Ordem de decisão de formato (generalização)

```text
1. Preferência explícita do usuário (composer / mensagem)
2. Forma dos dados (shape)
3. Perfil da entidade (presentation_profiles.json)
4. Rota/path como hint
5. Default global
```

### 2.4 Regras shape → visual

| Forma dos dados | Visual preferencial |
|-----------------|---------------------|
| Objeto campo/valor | Ficha / card resumo / KPI |
| Lista de registros | Tabela |
| Lista categoria + valor | Gráfico de barras |
| Série temporal | Gráfico de linha |
| Partes de um total | Composição / donut |
| Hierarquia pai-filho | Árvore |
| Poucos indicadores | KPI cards |
| Múltiplos blocos ricos | Dashboard / stack |
| Texto longo / relatório | Canvas / lousa |

**Proibido:**

- Conclusão só no `system_prompt` do agente
- `if` de domínio no MFE para narrativa, formato ou supressão de visuais (ver **P6 §8.6**)
- Strings PT em Python/TS fora de `assistant/*.json`
- Preferência que altera só `selected` mas a UI mostra outro primário
- Gráfico/tabela «decorativa» sem `purpose`

---

## 3. Mapa unificado — diretriz → módulo canônico

Consolida a diretriz de apresentação generalizada (§1–§18) com o playbook anterior.

| § | Diretriz | Módulo canônico | Contrato / artefato | Status |
|---|----------|-----------------|---------------------|--------|
| A1 | Resposta começa pela conclusão | `ChatHumanizedDataResponseService` + enrichment | `dataAnswer.summary` / `dataCommentary` + `<!-- section:summary -->` | 🟡 |
| A2 | Camada semântica antes do visual | **`ChatDataInsightService`** (evolui commentary) | `metadata.dataAnswer` | ⬜ |
| A3 | Fato / análise / hipótese / recomendação | `ChatDataInsightService` | `facts[]`, `analysis[]`, `hypotheses[]`, `recommendations[]` | 🟡 |
| A4 | Generalizar por forma, não por path | `ChatPresentationDataShapeAnalyzer` + `presentation_profiles.json` | `dataShape`, perfis `generic_*` | 🟡 |
| A5 | Preferência ponta a ponta | `ChatPresentationPrimaryViewService` + `ExecuteExternalActionUseCase` | Pipeline §5.4 | 🟡 |
| A6 | Serviço de insights desacoplado | **`ChatDataInsightService`** | Produz interpretação; presenter produz visuais | ⬜ |
| A7 | Narrativa humanizada evoluída | `ChatPresentationHumanizedNarrativeService` | Consome `dataAnswer`; detectores genéricos | 🟡 |
| A8 | Perfis declarativos | `presentation_profiles.json` + `ChatPresentationProfileService` | `defaultView`, `stackPlan`, `narrativePolicy`, `followUps` | 🟡 |
| A9 | Modo automático por score | `ChatPresentationDecisionService` | `presentationDecision.scores` | ⬜ |
| A10 | Visual com propósito | `ChatPresentationDecisionService` + builders | `purpose`, `message`, `reason` | 🟡 |
| A11 | Métricas derivadas antes do gráfico | `ChatDataInsightService` | `derivedMetrics[]`, `computedBy` | ⬜ |
| A12 | Limitações humanizadas | `ChatDataCoverageNoticeService` + insight | `limitations[]`, `coverageNotice` | 🟡 |
| A13 | Card de decisão (MFE) | **`ChatDecisionCard`** + segment registry | Segmento `decision` / `story.verdict` | ⬜ |
| A14 | Tipo visual `story` | API presentation + MFE renderer | `{ type: "story", blocks[] }` | ⬜ |
| A15 | Simplificar MFE (hooks) | `assistantContentSegments` (split) | Hooks §15 | ✅ |
| A19 | MFE render-only (P6) | `ChatPresentationRenderPlanService` + prune payload | `renderPlan` / omissão de campos | 🟡 |
| A16 | Recomendações clicáveis | `ChatPresentationRecommendationService` (evoluir) | `{ label, query, reason }` | 🟡 |
| A17 | Testes por shape | `humanized_data_response_cases.py` + shape fixtures | Critérios §17 | ✅ |
| A18 | Auditoria de cobertura | `scripts/audit_presentation_coverage.py` | Colunas narrativa/limitações/gaps | ✅ |

Legenda: ✅ entregue · 🟡 parcial · ⬜ planejado

### 3.1 Migração `dataCommentary` → `dataAnswer`

H1 entregou `dataCommentary` normalizado. P1 unifica sob `dataAnswer` sem quebrar consumidores:

```json
{
  "dataAnswer": {
    "summary": {
      "answer": "Conclusão principal",
      "meaning": "O que isso significa na prática",
      "riskLevel": "ok | attention | critical | undefined",
      "nextAction": "Próximo passo sugerido",
      "attention": "Ponto de atenção principal"
    },
    "facts": [{ "text": "…" }],
    "analysis": [{ "text": "…" }],
    "hypotheses": [{ "text": "…", "confirmed": false }],
    "recommendations": [
      { "label": "Ver apenas itens críticos", "query": "mostre apenas os itens críticos", "reason": "…" }
    ],
    "limitations": ["…"],
    "derivedMetrics": [
      { "key": "coverage_days", "label": "Cobertura estimada", "value": "2,1", "unit": "dias", "computedBy": "platform" }
    ],
    "visualHints": ["categorical_ranking", "kpi_set"],
    "profileKey": "factory_status",
    "anomalies": []
  }
}
```

| Campo legado (`dataCommentary`) | Campo novo (`dataAnswer`) |
|--------------------------------|---------------------------|
| `summary` | `summary.answer` |
| `interpretation` | `summary.meaning` |
| `alertLevel` | `summary.riskLevel` |
| `nextAction` | `summary.nextAction` |
| `attention[]` | `summary.attention` + bloco diagnóstico |
| `highlights[]` | `facts[]` (migração gradual) |
| `narrativeInsight` | derivado de `summary` (compat) |

`ChatOperationalCommentaryEnrichmentService` passa a gravar **ambos** durante P1; consumidores migram para `dataAnswer` em P2.

---

## 4. Contratos de metadata (coexistência)

```text
dataAnswer          ← interpretação (novo, canônico P1+)
dataCommentary      ← alias legado H1 (deprecar em P3)
textPresentation    ← markdown narrativo
presentation*       ← visuais (table, chart, tree, kpi, dashboard)
presentationDecision← formato, score, purpose, readingLayers
stackPresentationPlan← ordem de seções e perfil
humanizedSummary    ← linhas curtas para tool context / LLM
```

### 4.1 Bloco de decisão (camada 1 — antes de qualquer visual)

Formato recomendado na UI e no markdown:

```text
Resumo: [conclusão]
Interpretação: [significado prático]
Ponto de atenção: [risco / pendência / oportunidade]
Próxima ação: [ação sugerida]
Nível de risco: OK | Atenção | Crítico | Indefinido
```

Implementação atual: `ChatHumanizedDataResponseService.render_quick_layer_markdown()` + evolução para `ChatDecisionCard`.

### 4.2 `presentationDecision` com score (P3)

```json
{
  "presentationDecision": {
    "selected": "chart",
    "fallback": "table",
    "reason": "Dados categóricos com métrica numérica; barras facilitam comparação.",
    "purpose": "Quais itens concentram o saldo disponível?",
    "message": "Três códigos respondem por 92% do total.",
    "scores": {
      "text": 40,
      "table": 70,
      "chart": 92,
      "tree": 0,
      "kpi": 35,
      "dashboard": 20,
      "canvas": 0
    },
    "readingLayers": {
      "quick": ["summary", "riskLevel", "nextAction"],
      "diagnostic": ["facts", "analysis", "attention"],
      "evidence": ["tables", "charts", "tree"]
    }
  }
}
```

Exemplos de pontuação (heurística inicial):

```text
Série temporal        → score_chart.line +40
Categoria + valor     → score_chart.bar +45
Hierarquia            → score_tree +50
Lista grande          → score_table +35
Poucos indicadores    → score_kpi +40
Pergunta resumo/status→ score_text +30
Pergunta ranking      → score_chart +25
Relatório longo       → score_canvas +35
```

### 4.3 Tipo `story` (P4)

```json
{
  "type": "story",
  "title": "Status fabril — 90262404",
  "blocks": [
    { "kind": "verdict", "title": "Conclusão", "text": "…", "status": "attention" },
    { "kind": "fact", "text": "…" },
    { "kind": "analysis", "text": "…" },
    { "kind": "hypothesis", "text": "…", "confirmed": false },
    { "kind": "recommendation", "text": "…", "query": "…" },
    { "kind": "limitation", "text": "…" }
  ]
}
```

Reduz dependência de markdown para blocos críticos; alimentado por `dataAnswer`.

### 4.4 Perfis genéricos mínimos (P2)

Evoluir `presentation_profiles.json`:

```text
generic_object
generic_list
field_value_profile
time_series
categorical_ranking
composition
hierarchy
kpi_set
dashboard_bundle
document_report
```

Esqueleto declarativo por perfil:

```json
{
  "defaultView": "text",
  "allowedViews": ["text", "table", "chart"],
  "stackPlan": "summary_then_evidence",
  "narrativePolicy": "generic_data_summary",
  "chartPolicy": "auto_if_possible",
  "commentaryProfileKey": null,
  "followUps": []
}
```

---

## 5. Pipeline de preferência explícita (§5)

Fluxo canônico — **ordem obrigatória** no `ExecuteExternalActionUseCase`:

```text
1. Montar todos os visuais disponíveis (presenter + visual bundle)
2. Gerar dataAnswer (ChatDataInsightService)
3. Detectar preferência explícita (sessão + mensagem)
4. Aplicar preferência antes de fixar primário
5. Calcular presentationDecision (score + selected)
6. Enriquecer narrativa (HumanizedNarrative + stack markdown)
7. Montar stack final (StackOrder + section markers)
```

Serviços envolvidos (já existentes / evoluir):

- `ChatPresentationVisualBundleService` — passo 1
- `ChatOperationalCommentaryEnrichmentService` → `ChatDataInsightEnrichmentService` — passo 2
- `ChatPresentationPrimaryViewService` — passo 3–4
- `ChatPresentationDecisionService` — passo 5
- `ChatPresentationHumanizedNarrativeService` + `ChatPresentationStackMarkdownService` — passo 6–7

---

## 6. Bundles JSON e policies

| Tipo | Arquivo | Serviço |
|------|---------|---------|
| Templates resumo / alerta / limitações | `humanized_data_response.json` | `ChatHumanizedDataResponseContentService` |
| Insights por domínio operacional | `presenter_content.json` → `compositeAnalysisInsights` | `ChatOperationalDataCommentaryService` → `ChatDataInsightService` |
| Perfis e shapes | `presentation_profiles.json` | `ChatPresentationProfileService` |
| Motivos de decisão / score labels | `presentation_vocabulary.json` | `ChatPresentationVocabularyService` |
| Recomendações clicáveis | `humanized_data_response.json` → `recommendations` | `ChatPresentationRecommendationService` |
| Cobertura / escopo | `data_coverage.json` | `ChatDataCoverageNoticeService` |
| Policy LLM | `prompt_policies/humanized-data-response.md` | `PromptPolicyService` |

---

## 7. Frontend — diretrizes MFE (P4)

### 7.1 `ChatDecisionCard`

Segmento semântico **antes** dos painéis, alimentado por `dataAnswer.summary`:

```text
Conclusão · Status · Nível de risco · Ponto de atenção · Próxima ação · Escopo/confiança
```

Registro: `registerAssistantSegmentRenderer("decision", …)` — mesmo padrão de `assistantContentRegistry`.

### 7.2 Refatoração de componentes (§15)

Extrair hooks; componentes como orquestradores:

```text
useAssistantContentSegments
useAssistantContentRouteSections
useAssistantContentChrome
useDecisionCard
useChartExplanationTrigger
```

Dividir `assistantContentSegments.ts`:

```text
sqlMarkdownNormalizer.ts
visualSegmentCollector.ts
stackSegmentBuilder.ts
markerSegmentBuilder.ts
nativeSingleViewBuilder.ts
segmentDedupe.ts
```

**Regra (alvo P6):** MFE **não** reimplementa score, shape, interpretação, modo de sessão nem supressão de visuais — só materializa o que a API já decidiu enviar. Ver **§8.6**.

---

## 8. Roadmap macro — fases P1 a P5

Atualizar **Status** ao concluir cada fase.

| Fase | Tema | Entregas principais | Testes / CI | Status |
|------|------|---------------------|-------------|--------|
| **P1** | Interpretação universal | `ChatDataInsightService`; `dataAnswer`; detectores genéricos; narrativa consome insight; migração `dataCommentary` | `test_chat_data_insight_service.py`; casos H-01–H-10 | ✅ |
| **P2** | Perfis declarativos | Perfis `generic_*`; `commentaryProfileKey` no perfil; redução de `if` por path; registry documentado | `audit_presentation_coverage --check-commentary-profiles`; tier A | ✅ |
| **P3** | Preferência e automático | Pipeline §5 ordenado; `presentationDecision.scores`; `purpose` obrigatório; readingLayers no metadata | `test_chat_presentation_decision_scores.py` | ✅ |
| **P4** | UX premium | `ChatDecisionCard`; renderer `story`; recomendações clicáveis; coverage notice humanizado; split hooks MFE | `assistantContentVisualFormats.test.ts` | ✅ |
| **P5** | Governança e testes | `audit_presentation_coverage` estendido; fixtures por shape; `ChatHumanizedResponseQualityService`; smoke E2E | CI playbook-13 gate | ✅ |
| **P6** | MFE render-only | Payload final na API; remoção de `if` de apresentação no MFE; contrato `renderPlan` / omissão de campos suprimidos | `test_presentation_render_contract.py`; gate anti-duplicação MFE | 🟡 P6-A/B/C parcial |

### 8.1 P1 — Interpretação universal (detalhamento)

**Já entregue (sprints H0–H1):**

- `humanized_data_response.json`
- `ChatHumanizedDataResponseService` / `ChatHumanizedDataResponseContentService`
- Policy `humanized-data-response.md` no `PromptPolicyService`
- `<!-- section:summary -->` no markdown

**Entregue (P1 — jun/2026):**

- `ChatDataInsightService` + `ChatDataAnomalyDetectionService`
- `ChatDataInsightEnrichmentService` (alias `ChatOperationalCommentaryEnrichmentService`)
- Contrato `dataAnswer` + espelho `dataCommentary`
- `derivedMetrics` simples (contagem, total, média)
- `ChatPresentationHumanizedNarrativeService` prioriza `dataAnswer.summary`
- Detectores: lista vazia, zerados, negativos, truncamento

**Pendente pós-P1 (H3+):** pico, queda, outlier simples; score automático (P3).

### 8.2 P2 — Perfis declarativos

**Em curso (jun/2026):**

- Perfis `generic_list`, `generic_kpi_series` em `presentation_profiles.json`
- `commentaryProfileKey` + `narrativePolicy` em perfis operacionais e `table_list` / `generic`
- `ChatPresentationProfileService.commentary_profile_key()`
- `ChatOperationalDataCommentaryService.resolve_profile_key()` lê perfil declarativo (sem `if` por path)

**Entregue (P2 — jun/2026):**

- `commentaryProfileKey` / `narrativePolicy` nos perfis operacionais, `table_list`, `generic`, `kpi_series`
- `ChatPresentationProfileService.commentary_profile_key()`
- `resolve_profile_key` sem mapa hardcoded por path
- Audit `--check-commentary-profiles` + colunas CSV `commentary_profile_key`, `narrative_policy`

### 8.3 P3 — Preferência e automático

**Entregue (jun/2026):**

- Pipeline reordenado: insight → decision → narrative → stack (ponto único de enrichment)
- `ChatPresentationDecisionService.compute_scores()` + `readingLayers` + `purpose`/`message` de `dataAnswer`
- `_apply_automatic_score_selection()` — maior `scores` quando sem preferência explícita (respeita text-first e stack integrado)
- `_ensure_purpose()` — `purpose` obrigatório com visual (`dataAnswer` → mensagem → `purposeDefaults` JSON)
- Paridade MFE: tipos `scores`/`purpose`/`readingLayers` em `chatTypes.ts` + getters em `chatPresentation.ts`

**Próximo (P4):** `ChatDecisionCard`, `storyPresentation`, chips de recomendação.

### 8.4 P4 — UX premium

**Entregue (jun/2026):**

- `ChatPresentationStoryService` → `metadata.storyPresentation` quando `dataAnswer` presente
- `ChatDecisionCard` + segmento `decision` no registry e `buildAssistantContentSegments`
- Recomendações de `dataAnswer` mescladas em `getPresentationRecommendationsFromToolCalls` (chips com `query`)
- Deduplicação do bloco `<!-- section:summary -->` quando o card de decisão está ativo

**Entregue (continuação P4 — jun/2026):**

- `assistantContentDecisionLayer.ts` — camada de decisão extraída de `assistantContentSegments`
- `useAssistantContentSegments` + `useAssistantContentChrome` — hooks do §15
- `resolveHumanizedCoverageNotice` — mescla `dataCoverageNotice` + `dataAnswer.limitations`
- Modo Texto preserva segmento `decision` (fix visibilidade do card)

**Entregue (`summary_then_evidence` — jun/2026):**

Perfil `summary_then_evidence` (ex.: `factory_status`, `stock`, status operacionais): interpretação na **prosa do chat**, sem `storyPresentation` / `ChatDecisionCard` duplicando o markdown. Changelog: [`2026-06-summary-then-evidence-modos-apresentacao.md`](../changelog/2026-06-summary-then-evidence-modos-apresentacao.md).

| Modo de sessão | Comportamento |
|----------------|---------------|
| **Automático** | Prosa compacta + tabelas/árvore com `sectionFraming` inline; **sem** divisões `stackSection` nem `dashboard` no tail |
| **Texto** | Markdown completo com embeds GFM (`should_embed_in_markdown` só com `explicitSessionFormat: "text"`) |
| **Painel** | Lead curto + `dashboard`; plano sem `operationalTables` repetindo o painel |

Módulos: `ChatPresentationEvidenceFirstLayoutService`, `ChatRichPresentationTextService`, serviços `*MarkdownService` (table/tree/chart), MFE `chatPresentation.ts` + `presentationStackBlueprint.ts`.

**Entregue (split §15 — jun/2026):**

- `sqlMarkdownNormalizer.ts`, `visualSegmentCollector.ts`, `stackSegmentBuilder.ts`
- `markerSegmentBuilder.ts`, `nativeSingleViewBuilder.ts`, `segmentDedupe.ts`
- `assistantContentSegments.ts` reduzido a orquestrador fino


### 8.5 P5 — Governança

**Entregue (jun/2026):**

1. `audit_presentation_coverage.py` — colunas CSV `data_shape`, `supported_formats`, `default_view`, `has_narrative`, `has_limitations`, `has_recommendations`, `has_shape_test`, `humanized_gaps`
2. `ChatHumanizedResponseQualityService.evaluate(metadata)` — checklist §13 automatizado
3. `tests/fixtures/humanized_data_response_cases.py` — 10 shapes §17 + gate `humanized_data_response_gate.py`
4. CI `--check-humanized-answer` no workflow `minha-delpi-ai-api-presentation.yml`

### 8.6 P6 — MFE render-only (próxima fase)

**Motivação (jun/2026):** correções de regressão (`tailVisualPolicy: allowlist`, supressão de `dashboard` no Automático) reintroduziram **lógica de decisão no MFE** (`shouldRenderDashboardSegment`, fallback órfão em `appendTailVisuals`, inferência de `allowlist` quando o campo falta). Isso viola §2.2 e gera drift API↔MFE — o sintoma reaparece no frontend mesmo com o backend correto.

**Princípio:**

```text
API decide e filtra → metadata contém só o que deve aparecer → MFE monta segmentos mecanicamente
```

O MFE permanece responsável por **mecânica de UI** (registry de componentes, markdown/prosa, streaming reveal, toolbar de formato do composer, dedupe de keys React). Toda **regra de negócio de apresentação** fica na API.

#### 8.6.1 Inventário de lógica duplicada no MFE (auditoria jun/2026)

**P6-A entregue (jun/2026 — parcial):**

- `ChatPresentationPayloadPruningService.prune()` — omite `*Presentation` fora de `tailVisualOrder` quando `tailVisualPolicy: allowlist`
- Encaixe no pipeline: fim de `ExecuteExternalActionUseCase._build_presentation_metadata`
- `renderHints.suppressedKinds` no `stackPresentationPlan` (telemetria)
- Testes: `test_presentation_render_contract.py`
- MFE: removido uso de `shouldRenderDashboardSegment` em `visualSegmentCollector` e `presentationStackBlueprint` (função mantida `@deprecated`)

**P6-B/C entregue (jun/2026 — parcial):**

- `renderHints.textRenderMode` (`compact`|`full`) + `tailVisualPolicy` sempre explícito (`legacy`|`allowlist`)
- `ChatPresentationRenderPlanService.build()` → `metadata.renderPlan` (lead, highlights, attention, tabelas, tail)
- MFE: `renderPlanSegmentBuilder.ts` + `buildSegmentsFromRenderPlan` — executor mecânico priorizado em `buildCanonicalStackSegments`
- MFE: `nativeSingleViewBuilder` consome `renderPlan` em layout não-stack
- MFE: `shouldApplyClientMarkdownCompaction` — não recompacta quando API enviou `textRenderMode`
- MFE: removidas `shouldRenderDashboardSegment` / `isExplicitDashboardSession`
- CI: `scripts/audit_mfe_presentation_logic.py`

| Área | Arquivo(s) MFE | O que decide hoje | Canônico API (alvo) |
|------|----------------|-------------------|---------------------|
| Modo de sessão | `chatPresentation.ts` — `isExplicitTextSessionMode`, `isExplicitDashboardSession`, `hasExplicitPresentationFormatChoice` | Texto vs Painel vs escolha explícita | `explicitSessionFormat` já na metadata; **não re-interpretar** — usar flags do plano |
| Perfil evidence-first | `isSummaryThenEvidenceMode`, `assistantContentDecisionLayer.ts` | Suprimir card / stackSection | `presentationDecision.presentationMode` + API já omite `storyPresentation` |
| Tail / painel | `shouldRenderDashboardSegment`, `usesStrictTailVisualAllowlist`, `visualSegmentCollector.ts`, `presentationStackBlueprint.ts` | Coletar ou não `dashboard`; fallback órfão | `ChatPresentationEvidenceFirstLayoutService` + **omitir** `dashboardPresentation` do payload quando fora do tail |
| Inferência de policy | `presentationStackPlan.ts` — default `allowlist` se `summary_then_evidence` | Política quando campo ausente | API **sempre** envia `tailVisualPolicy` explícito |
| Strip de markdown | `stripRichUiRedundantProseFromMarkdown`, `stripCompositionCodeFenceFromMarkdown` em `chatPresentation.ts` | Remover embeds/composição no Automático | `ChatRichPresentationTextService.prepare_evidence_first_chat_narrative` — texto final no `textPresentation` |
| Dedup estrutural | `presentationStructureDedup.ts` — `shouldSkipTableSegment`, heurística de colunas/título | Ocultar tabela plana quando há árvore | Presenter + `structureDedupApplied: true` (padrão já usado); API não envia tabela duplicada |
| Seções humanizadas | `planUsesHumanizedSections` + gate em `presentationStackBlueprint.ts` | `stackSection` numerado vs prosa inline | `stackPresentationPlan.humanizedSections` + `sectionVisibility` — API define slots; MFE só expande |
| Roteamento de layout | `assistantContentSegments.ts`, `nativeSingleViewBuilder.ts` | stack vs single vs markers vs texto | `presentationDecision.layoutMode` + plano fechado; evoluir para `renderPlan` |
| Formato visual ativo | `assistantContentVisualFormats.ts` | Toolbar quando há escolha explícita | `presentationDecision.availableViews` + `explicitSessionFormat` — sem heurística de `preferredFormat`≠`selected` |

**Dívida introduzida na hotfix `allowlist` (commit `c1c455f6`):** funções `shouldRenderDashboardSegment` / `isExplicitDashboardSession` são **paliativo** até P6 — documentadas como removíveis quando a API deixar de enviar `dashboardPresentation` fora do contrato.

#### 8.6.2 Contrato alvo (metadata)

Evolução incremental — não quebrar consumidores atuais:

**Fase P6-A — omissão no payload (quick win)**

A API **não serializa** campos suprimidos no turno (em vez do MFE filtrar na coleta):

```text
Automático + summary_then_evidence:
  ✓ textPresentation (prosa final, sem embeds)
  ✓ tablePresentation / treePresentation / chartPresentation conforme tailVisualOrder
  ✗ dashboardPresentation (omitido)
  ✗ storyPresentation (já omitido)

Painel explícito:
  ✓ dashboardPresentation
  ✗ operationalTables no stackPlan (já feito)
```

Flags existentes reforçadas: `structureDedupApplied`, `tailVisualPolicy`, `tailVisualOrder`, `sectionVisibility`.

**Fase P6-B — `stackPresentationPlan.renderHints` (opcional)**

Campos declarativos só para telemetria/depuração — **não** para o MFE re-decidir:

```json
{
  "renderHints": {
    "suppressedKinds": ["dashboard"],
    "textRenderMode": "compact",
    "tailVisualPolicy": "allowlist"
  }
}
```

**Fase P6-C — `renderPlan` (estado final)**

Lista ordenada de segmentos já resolvidos pela API (espelho do que `buildAssistantContentSegments` produz hoje):

```json
{
  "renderPlan": {
    "version": 1,
    "segments": [
      { "kind": "markdown", "slot": "lead", "source": "textPresentation" },
      { "kind": "table", "slot": "operationalTables", "source": "tablePresentation" },
      { "kind": "tree", "slot": "tailVisuals", "source": "treePresentation" }
    ]
  }
}
```

MFE: `buildSegmentsFromRenderPlan(metadata)` — substitui `presentationStackBlueprint` progressivamente.

#### 8.6.3 Serviços API a estender (módulo canônico)

| Serviço | Entrega P6 |
|---------|------------|
| `ChatPresentationEvidenceFirstLayoutService` | `_prune_suppressed_presentations(metadata)` — remove `dashboardPresentation` e visuais fora de `tailVisualOrder` |
| `ChatPresentationStackOrderService` | Garantir `tailVisualPolicy` sempre explícito no plano |
| `ExternalActionResultPresenter` / presenters | Dedup estrutural antes de gravar metadata (sem depender de heurística MFE) |
| `ChatRichPresentationTextService` | Único responsável por markdown compacto vs completo |
| **`ChatPresentationRenderPlanService`** (novo) | Monta `renderPlan` ou valida paridade com builder MFE legado |

Ponto de encaixe no pipeline (após §5 passo 7):

```text
… ChatPresentationEvidenceFirstLayoutService.compose()
  → ChatPresentationRenderPlanService.build(metadata)   [P6-C]
  → ChatPresentationPayloadPruningService.prune(metadata) [P6-A]
```

#### 8.6.4 Plano de remoção no MFE (ordem)

```text
1. P6-A API omite dashboard → remover shouldRenderDashboardSegment + filtro em visualSegmentCollector
2. P6-A API omite tabelas duplicadas → remover shouldSkipTableSegment / isHierarchyDuplicateTable
3. P6-A texto final na API → remover stripRichUi* do resolveAssistantRenderableMarkdown
4. API tailVisualPolicy obrigatório → remover inferência em presentationStackPlan.parsePlan
5. API renderPlan estável → reduzir presentationStackBlueprint a executor de renderPlan
6. Remover fallback órfão legacy em appendTailVisuals (manter só allowlist)
```

**Permanece no MFE:** `assistantProseRendering.ts` (reveal/streaming), `assistantContentRegistry`, toolbar do composer (`useChatPresentationFormat`), testes de snapshot de componentes.

#### 8.6.5 Testes e governança P6

| Artefato | Função |
|----------|--------|
| `tests/unit/domain/services/test_presentation_render_contract.py` | Por modo (auto/text/dashboard) + perfil: campos presentes/ausentes, ordem do tail |
| `tests/unit/application/test_presentation_mfe_parity.py` | Opcional: JSON fixture → segmentos esperados (contrato, não reimplementação TS) |
| `scripts/audit_mfe_presentation_logic.py` | Lista símbolos proibidos no MFE (`shouldRender*`, `isExplicit*Session`, `stripRich*`) — gate CI |
| Atualizar `presentationStackPlan.humanized.test.ts` | Assertar comportamento via metadata **pruned**, não via `if` local |

**Critérios de aceite P6:**

```text
[ ] Nenhum `if` de modo de sessão em chatPresentation.ts para suprimir visuais
[ ] dashboardPresentation ausente no JSON quando Automático + summary_then_evidence
[ ] textPresentation sem embeds no Automático (assert API, não strip MFE)
[ ] tailVisualPolicy sempre presente no stackPresentationPlan
[ ] Regressão 90262404: Automático sem painel — validada só com payload API
[ ] Gate CI falha se novos shouldRender*/isExplicit* forem adicionados ao MFE
```

#### 8.6.6 PR checklist (P6)

1. Regra nova só em serviço API (§8.6.3)?
2. MFE alterado apenas para **consumir** campo novo ou **remover** `if`?
3. Teste de contrato de payload (não só snapshot MFE)?
4. Changelog + este §8.6 atualizados?
5. Sem texto PT novo fora de JSON?

---

## 9. Sprints legadas H0–H6 (referência)

Mapa das sprints anteriores dentro do roadmap macro:

| Sprint | Conteúdo | Fase macro |
|--------|----------|------------|
| H0 | Baseline playbook | P1 |
| H1 | Contrato + JSON + policy | P1 ✅ |
| H2 | Commentary multi-perfil | P1 🟡 |
| H3 | Anomalias + derivedMetrics | P1 |
| H4 | readingLayers + purpose | P3 |
| H5 | Interpretação + chips | P4 |
| H6 | Qualidade + E2E | P5 |

---

## 10. Detectores genéricos (`ChatDataInsightService`)

| Detector | Entrada | Saída |
|----------|---------|-------|
| Valores zerados relevantes | coluna numérica + contexto | `anomalies[]` |
| Valores negativos | estoque, saldo, quantidade | `attention` + `riskLevel` |
| Campos ausentes | schema / linhas | `limitations[]` |
| Lista vazia | `items.length === 0` | `riskLevel: undefined` |
| Lista muito grande | cardinalidade | `limitations` + hint tabela |
| Paginação incompleta | `total > shown` | `limitations` |
| Queda / pico | série temporal | `analysis` + `hypothesis` |
| Empenho > saldo | estoque | `attention` |
| Status pendente | enums operacionais | `facts` |

Hipóteses: **sempre** `confirmed: false` quando causa não está nos dados.

---

## 11. Template universal (markdown + story)

```markdown
### {título}

<!-- section:summary -->
**Resumo:** {answer}
**Interpretação:** {meaning}
**Ponto de atenção:** {attention}
**Próxima ação:** {nextAction}
**Nível de risco:** {riskLevel}

<!-- section:facts -->
**Fatos principais**
- …

<!-- section:diagnostic -->
**Leitura dos dados** / **Pontos de atenção**

<!-- section:limitations -->
**Escopo da análise:** …

<!-- section:panels -->
{painéis — evidência}

<!-- section:next_steps -->
**Próximos passos sugeridos**
```

Marcadores compatíveis com `ChatPresentationStackMarkdownService`.

---

## 12. Testes por forma de dados (§17)

| Shape | Fixture | Critérios de aceite |
|-------|---------|-------------------|
| `field_value_profile` | objeto campo/valor | conclusão + ficha/KPI |
| `generic_list` | lista simples | tabela + summary |
| `categorical_ranking` | categoria + métrica | chart bar + purpose |
| `time_series` | datas + valores | chart line + derivedMetrics variação |
| `hierarchy` | pai-filho | tree na evidência; resumo primeiro |
| `kpi_set` | poucos números | KPI cards + interpretação |
| `empty_list` | `items: []` | `riskLevel: undefined` + limitations |
| `large_list` | > N linhas | tabela + aviso paginação |
| `truncated` | partial coverage | limitations humanizadas |
| `logical_error` | erro API 422 | sem dataAnswer; erro amigável |

Arquivos:

- `tests/fixtures/humanized_data_response_cases.py`
- `tests/fixtures/rich_presentation_cases.py` (evoluir)
- `plugins/minha-delpi-chat/src/ui/components/assistantContentVisualFormats.test.ts`

---

## 13. Checklist de validação (antes de merge P5)

```text
[ ] Resposta começa com conclusão (dataAnswer.summary.answer)?
[ ] Números importantes têm interpretação (meaning / derivedMetrics)?
[ ] Separação fato / análise / hipótese / recomendação?
[ ] Anomalias em pontos de atenção quando aplicável?
[ ] Cada visual tem purpose claro?
[ ] Limitações e escopo informados?
[ ] Próximas ações com label + query?
[ ] Preferência explícita respeitada ponta a ponta?
[ ] presentationDecision.scores auditável?
[ ] Textos PT só em JSON?
[ ] Nenhuma causa não confirmada afirmada como fato?
```

Automação: `ChatHumanizedResponseQualityService.evaluate(metadata)`.

---

## 14. Integração com entregas existentes (jun/2026)

| Entrega | Fase | Próximo passo |
|---------|------|---------------|
| `ChatOperationalDataCommentaryService` | P1 | Absorvido por `ChatDataInsightService` |
| `ChatHumanizedDataResponseService` | P1 | Mapper `dataCommentary` → `dataAnswer` |
| `ChatPresentationDataShapeAnalyzer` | P2/P3 | Alimentar score automático |
| `presentation_profiles.json` (130 rotas) | P2 | Perfis `generic_*` |
| `audit_presentation_coverage.py` | P5 | Colunas humanização |
| `ChatPresentationRecommendationService` | P4 | `label` + `query` + chips |
| Remoção toggle pós-resposta | P3 | Preferência só no composer |
| Cores Recharts / Mermaid tema | P4 | Legibilidade evidência |

---

## 15. PR checklist

1. Regra no **módulo canônico** (§3)?
2. Domain sem import de infra?
3. Texto PT só em `assistant/*.json`?
4. Send/stream mesmo serviço?
5. Teste por **shape** ou regressão?
6. `chat-intelligence-base.md` + catálogo atualizados?
7. Agente sem lógica exclusiva de narrativa/decisão?
8. Preferência não altera só metadata sem efeito no MFE?

---

## 16. Ordem de execução recomendada

```text
P1 (dataAnswer + ChatDataInsightService + perfis operacionais restantes)
  → P2 (perfis generic_* + menos if por path)
    → P3 (score + pipeline preferência + purpose)
      → P4 (DecisionCard + story + chips + hooks MFE)
        → P5 (auditoria + qualidade + CI)
          → P6 (MFE render-only — API envia payload final, sem lógica duplicada no frontend)
```

**Quick win atual (P6-A):** `ChatPresentationEvidenceFirstLayoutService` passa a **omitir** `dashboardPresentation` no Automático — permite remover `shouldRenderDashboardSegment` do MFE na mesma sprint.

---

## 17. Referências — corpos de diretriz

Este playbook consolida:

1. **Diretrizes gerais** — respostas humanizadas com dados (19 seções, jun/2026).
2. **Diretriz de apresentação generalizada** — camada semântica, shape-first, score, DecisionCard, story (18 seções, jun/2026).

**Regra de ouro (ambas):**

```text
A IA não deve mostrar primeiro os dados.
Ela deve primeiro explicar o que os dados significam.

A apresentação visual deve ser evidência da resposta,
não substituto da interpretação.

A escolha do visual deve nascer da forma dos dados,
da preferência do usuário e da decisão que ele precisa tomar.
```
