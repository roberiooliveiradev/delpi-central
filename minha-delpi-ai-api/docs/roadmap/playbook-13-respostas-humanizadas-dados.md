# Playbook 13 — Respostas humanizadas com dados

**Projeto:** Minha DELPI Chat IA  
**Escopo:** qualquer resposta que envolva dados — financeiro, vendas, estoque, produção, atendimento, RH, projetos, qualidade, indicadores, relatórios, integrações, APIs ou bases internas.  
**Status:** H0 documentado (jun/2026) · H1–H6 planejadas  
**Público:** backend, frontend MFE, revisores de PR, agentes Cursor

> **Regra central:** a IA não deve apenas apresentar dados. Deve transformar dados em **entendimento, contexto e próximos passos**.

Relacionado:

- [`chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) — pipeline único herdado por agentes e projetos
- [`humanized-narrative-stack-jun2026.md`](../architecture/humanized-narrative-stack-jun2026.md) — narrativa antes dos painéis
- [`playbook-09-apresentacao-rica.md`](./playbook-09-apresentacao-rica.md) — decisão de formato e insight
- [`playbook-12-apresentacao-declarativa-refatoracao.md`](./playbook-12-apresentacao-declarativa-refatoracao.md) — perfis declarativos e stack
- [`playbook-10-contrato-respostas-api-delpi.md`](./playbook-10-contrato-respostas-api-delpi.md) — contrato api-delpi → presenter
- [`assistant-content-catalog.md`](../architecture/assistant-content-catalog.md) — bundles JSON PT-BR

**Regras Cursor obrigatórias:** `chat-intelligence-base.mdc`, `centralized-rules-first.mdc`, `assistant-content-json.mdc`, `clean-architecture-chat-api.mdc`.

---

## 1. Objetivo

Padronizar respostas com dados para que **toda** consulta operacional (action, SQL, KPI, multi-rota) siga a mesma lógica:

```text
Primeiro responde → depois mostra evidências
Primeiro orienta  → depois detalha
Primeiro explica o impacto → depois apresenta campos técnicos
```

**Critério de sucesso:**

| Métrica | Hoje (jun/2026) | Alvo |
|---------|-----------------|------|
| Perfis com `dataCommentary` estruturado | `factory_status` (+ narrativa parcial em outras rotas) | ≥ 90% das rotas tier A/B com commentary ou narrativa equivalente |
| Resposta começa com conclusão | Parcial (stack texto + insight) | 100% dos turnos com dados via gate de qualidade |
| Separação fato / análise / hipótese | Implícita no LLM | Explícita no metadata + prosa |
| Níveis de alerta padronizados | Pontos de atenção livres | `OK` / `Atenção` / `Crítico` / `Indefinido` em metadata |
| Visualizações com propósito | `presentationDecision` + perfis | Toda visual com `purpose` + pergunta respondida |
| Checklist §19 automatizado | Manual | Fixture de regressão + smoke E2E |

---

## 2. Princípio de arquitetura

Inteligência **no chat base** — agentes adicionam restrições e escopo, não reimplementam narrativa.

```text
Dados brutos (api-delpi / SQL / action)
  → Presenter (tabela, gráfico, KPI, árvore)          ← evidência (camada 3)
  → ChatOperationalDataCommentaryService (+ extensões) ← diagnóstico determinístico (camada 2)
  → ChatPresentationHumanizedNarrativeService          ← prosa fina no markdown
  → ChatPresentationDecisionService                    ← ordem, formato, insight
  → ChatOperationalCommentaryEnrichmentService         ← metadata.dataCommentary
  → MFE ChatAssistantContent                           ← render em camadas (texto → KPI → gráfico → tabela)
  → LLM (quando necessário)                          ← complemento, nunca substituto do commentary base
```

**Proibido:**

- Regra de «começar pela conclusão» só no `system_prompt` de um agente
- `if` de domínio no MFE para decidir narrativa
- Strings PT novas em Python/TS fora de `app/content/pt-BR/assistant/*.json`
- Duplicar a mesma regra em `Send*` e `Stream*` sem serviço compartilhado

---

## 3. Mapa das diretrizes → módulo canônico

| § | Diretriz | Módulo canônico | Artefato / contrato | Status |
|---|----------|-----------------|---------------------|--------|
| 1 | Começar pela resposta | `ChatOperationalDataCommentaryService` + `ChatPresentationHumanizedNarrativeService` | `dataCommentary.summary`, `textPresentation.markdown` (seção Resumo) | 🟡 Parcial |
| 2 | Fato / análise / hipótese / recomendação | **Novo** `ChatHumanizedDataResponseService` | `dataCommentary.facts[]`, `analysis[]`, `hypotheses[]`, `recommendations[]` | ⬜ |
| 3 | Números com significado | Commentary + `ChatPresentationFieldNormalizationService` | Frases com interpretação por métrica em JSON de perfil | 🟡 |
| 4 | Estrutura padrão de resposta | `ChatPresentationStackOrderService` + `presentation_profiles.json` | Ordem fixa: resumo → KPI → atenção → prosa → visuais → detalhes → ações | 🟡 |
| 5 | Níveis de leitura (rápida / diagnóstico / evidência) | `ChatPresentationDecisionService` + MFE segmentos | `presentationDecision.readingLayers` | ⬜ |
| 6 | Priorizar indicadores relevantes | Commentary + `ChatPresentationKpiAssemblyService` | KPI cards filtrados por `relevanceScore` | 🟡 |
| 7 | Destacar anomalias | **Novo** `ChatDataAnomalyDetectionService` | `dataCommentary.anomalies[]` | ⬜ |
| 8 | Visualizações com propósito | `ChatPresentationDecisionService` + `ChatChartTypeSelectionService` | `presentation.purpose`, `presentationDecision.reason` | 🟡 |
| 9 | Métricas derivadas | Commentary (cálculo determinístico) | `dataCommentary.derivedMetrics[]` com flag `computedBy: "ai"` | ⬜ |
| 10 | Níveis de alerta | Commentary + JSON | `dataCommentary.alertLevel`: `ok` \| `attention` \| `critical` \| `unknown` | ⬜ |
| 11 | Limitações da consulta | `ChatPresentationCoverageService` + commentary | `dataCommentary.limitations[]`, `coverageNotice` existente | 🟡 |
| 12 | Linguagem natural | `humanized_data_response.json` + policies | Templates de frase por perfil | ⬜ |
| 13 | Precisão adequada | `ChatPresentationFieldNormalizationService` | Arredondamento por `fieldFormats` | ✅ |
| 14 | Próximas ações | `ChatFollowUpRecommendationService` (evoluir) | Chips sugeridos em JSON, não hardcoded | 🟡 |
| 15 | Não inventar causa | Policy + commentary | `hypotheses[]` obrigatório com `confirmed: false` | ⬜ |
| 16 | Template universal | `humanized_data_response.json` | Seções e placeholders | ⬜ |
| 17 | Prompt desacoplado | `prompt_policies/humanized-data-response.md` | Registro em `PromptPolicyService` (modo global) | ⬜ |
| 18 | Regra central | Este playbook + `chat-intelligence-base.md` | — | ✅ |
| 19 | Checklist de validação | **Novo** `ChatHumanizedResponseQualityService` | Fixture `humanized_data_response_cases.py` | ⬜ |

Legenda: ✅ entregue · 🟡 parcial · ⬜ planejado

---

## 4. Contrato alvo — `metadata.dataCommentary`

Evolução do contrato já consumido por `ChatDataInterpretationAnswerService`, `chat_tool_context_external_action_formatter` e enrichment pós-tool.

```json
{
  "profileKey": "factory_status",
  "alertLevel": "attention",
  "summary": "O produto está em produção, com cobertura de MP baixa em dois componentes.",
  "interpretation": "Na prática, a fábrica pode seguir no curto prazo, mas há risco de ruptura se o consumo se mantiver.",
  "nextAction": "Verificar saldo detalhado dos códigos 10080063 e 10130006 e comparar com consumo médio.",
  "highlights": ["Indicador 1: …", "Indicador 2: …"],
  "attention": ["Cobertura de MP abaixo de 3 dias para PA."],
  "facts": [
    { "label": "Saldo PA consolidado", "value": "4.638", "unit": "UN" }
  ],
  "analysis": [
    { "text": "A queda de saldo está concentrada em duas MPs." }
  ],
  "hypotheses": [
    { "text": "Pode haver atraso de recebimento de MP.", "confirmed": false }
  ],
  "recommendations": [
    { "text": "Listar apenas exceções de estoque.", "intent": "filter_exceptions" }
  ],
  "anomalies": [
    { "type": "zero_value", "field": "available_quantity", "scope": "Fil.01", "impact": "Indefinido sem histórico" }
  ],
  "derivedMetrics": [
    { "key": "mp_coverage_days", "label": "Cobertura estimada de MP", "value": "2,1", "unit": "dias", "computedBy": "platform" }
  ],
  "limitations": [
    "Análise considera apenas estoque autorizado na consulta atual; histórico completo não foi avaliado."
  ],
  "narrativeInsight": "…",
  "readingLayer": {
    "quick": ["summary", "alertLevel", "nextAction"],
    "diagnostic": ["highlights", "attention", "analysis", "anomalies"],
    "evidence": ["tables", "charts", "sourceMeta"]
  }
}
```

**Compatibilidade:** campos legados `highlights`, `attention`, `narrativeInsight` permanecem; novos campos são opcionais na H1 e obrigatórios por perfil a partir da H3.

---

## 5. Bundles JSON e policies

| Tipo | Arquivo | Serviço |
|------|---------|---------|
| Templates de seção (Resumo, Diagnóstico, …) | `humanized_data_response.json` (**novo**) | `ChatHumanizedDataResponseContentService` (**novo**) |
| Insights por perfil operacional | `presenter_content.json` → `compositeAnalysisInsights` | `ChatOperationalDataCommentaryService` |
| Interpretação pós-consulta | `data_interpretation.json` | `ChatDataInterpretationContentService` |
| Chips de próxima ação | `follow_up_recommendations.json` (evoluir) | `ChatFollowUpRecommendationService` |
| Activity / direct answer | `turn_preparation.json` | `ChatTurnPreparationContentService` |
| Policy global LLM | `prompt_policies/humanized-data-response.md` (**novo**) | `PromptPolicyService` |

---

## 6. Pipeline alvo por camada de leitura

### Camada 1 — Visão rápida (§5)

```text
Resumo + alertLevel + próxima ação
```

- Fonte: `dataCommentary.summary` + `alertLevel` + `nextAction`
- Render: primeiro segmento `text` no stack; KPI compacto quando `presentationDecision.selected` incluir `kpi`
- MFE: sem scroll obrigatório; título do painel opcionalmente oculto em modo «rápido»

### Camada 2 — Diagnóstico (§5)

```text
Indicadores-chave, comparações, tendências, anomalias
```

- Fonte: `highlights`, `attention`, `analysis`, `anomalies`, `derivedMetrics`
- Render: markdown estruturado + KPI grid + insight (`presentationDecision.insight`)

### Camada 3 — Evidência (§5)

```text
Tabelas, gráficos, árvore, fonte, filtros, período
```

- Fonte: `tablePresentation`, `chartPresentation`, `treePresentation`, `apiDelpiResponseMeta`
- Render: painéis ricos; detalhes técnicos e metadados em rodapé discreto ou seção colapsável (futuro)

---

## 7. Regras de visualização (§8)

Integrar ao decisor existente — **não** criar segundo decisor.

| Pergunta do usuário | Formato | Serviço |
|---------------------|---------|---------|
| Comparar registros / auditar | `table` | `ChatPresentationDecisionService` |
| Ranking / maiores / menores | `horizontal_bar` ou `bar` | `ChatChartTypeSelectionService` |
| Evolução / tendência | `line` / `multi_line` | idem |
| Participação no total | `donut` / composição | idem + `ChatPresentationChartPolicyService` |
| Hierarquia / BOM | `tree` | `ChatPresentationCompositeVisualBuilder` |
| Poucos números decisivos | `kpi` | `ChatPresentationKpiAssemblyService` |

**Nova chave em metadata:**

```json
{
  "presentationDecision": {
    "purpose": "Responder: quais MPs concentram o saldo disponível?",
    "message": "Três códigos respondem por 92% do saldo consolidado."
  }
}
```

Textos de `purpose` e `message` → JSON (`presenter_content.json` ou `humanized_data_response.json`), nunca string literal no decisor.

---

## 8. Roadmap por fases

Atualizar **Status** ao concluir cada fase.

| Fase | Tema | Entregas | Testes | Status |
|------|------|----------|--------|--------|
| **H0** | Baseline e playbook | Este documento; inventário §3; alinhamento com narrativa stack jun/2026 | — | ✅ |
| **H1** | Contrato e conteúdo base | `humanized_data_response.json`; `ChatHumanizedDataResponseContentService`; extensão opcional de `dataCommentary`; policy `humanized-data-response.md` registrada | `test_humanized_data_response_content.py` | ⬜ |
| **H2** | Commentary determinístico multi-perfil | Estender `ChatOperationalDataCommentaryService` para `stock`, `production_status`, `shipping_status`, SQL tabular genérico; `alertLevel` + `summary` + `nextAction` | `test_chat_operational_data_commentary_service.py` + casos em `chat_intelligence_regression_cases.py` | ⬜ |
| **H3** | Anomalias e métricas derivadas | `ChatDataAnomalyDetectionService` (zeros, picos, quedas, ausência, outliers simples); `derivedMetrics` com `computedBy`; separação `facts` / `analysis` / `hypotheses` | `test_chat_data_anomaly_detection_service.py` | ⬜ |
| **H4** | Camadas de leitura e propósito visual | `presentationDecision.readingLayers` + `purpose`; ordem de segmentos no MFE via metadata (sem `if` local); integração com `ChatPresentationInsightService` | `assistantContentVisualFormats.test.ts` + `test_rich_presentation.py` | ⬜ |
| **H5** | Próximas ações e interpretação | Evoluir `ChatDataInterpretationAnswerService` para novo contrato; chips de continuidade em JSON; LLM só preenche lacunas (`confirmed: false` em hipóteses) | `test_chat_data_interpretation_answer_service.py` | ⬜ |
| **H6** | Qualidade e encerramento | `ChatHumanizedResponseQualityService` + checklist §19; smoke E2E «status fabril», «estoque», «SQL»; métrica admin `% respostas com summary` | `humanized_data_response_cases.py` + `smoke_e2e_scenarios.json` | ⬜ |

### H1 — Detalhamento (próxima sprint)

1. Criar bundle `humanized_data_response.json` com:
   - templates de seção (§16);
   - rótulos de `alertLevel`;
   - frases de limitação (§11);
   - marcadores «Cálculo da plataforma» vs «Estimativa» (§9).
2. Criar `ChatHumanizedDataResponseContentService` (domain) com `get` / `format`.
3. Adicionar `prompt_policies/humanized-data-response.md` (§17) e registrar em `PromptPolicyService` como policy global em turnos com `dataCommentary` ou `presentationDecision`.
4. Documentar contrato em [`assistant-content-catalog.md`](../architecture/assistant-content-catalog.md).

### H2 — Detalhamento

1. Generalizar builders em `ChatOperationalDataCommentaryService` (hoje só `factory_status` completo).
2. Mapear perfis em `presentation_profiles.json` → `commentaryProfileKey`.
3. Garantir enrichment em **um** ponto: `ChatOperationalCommentaryEnrichmentService` (já ligado ao pipeline pós-tool).
4. Prosa inicial no stack: `ChatPresentationHumanizedNarrativeService` consome `summary` antes de montar markdown longo.

### H3 — Detalhamento

1. `ChatDataAnomalyDetectionService` recebe linhas normalizadas + perfil; retorna `anomalies[]` tipadas.
2. Regras iniciais (sem ML): valor zero inesperado, negativo, queda > X% vs mediana, campo nulo crítico, contagem zerada.
3. Limiares por perfil em JSON (`humanized_data_response.json` → `anomalyThresholds`).
4. Hipóteses **só** quando anomalia sem causa nos dados; sempre `confirmed: false`.

### H4 — Detalhamento

1. API passa `readingLayers` no `presentationDecision`.
2. MFE `buildAssistantContentSegments` respeita ordem sem reordenar por heurística local.
3. Cada visual inclui `purpose` (pergunta) visível no título auxiliar ou `insight` — não gráfico decorativo.

### H5 — Detalhamento

1. Perguntas «explique», «resuma», «traduz» usam camadas 1–2 do commentary antes do LLM.
2. Chips «Próximos passos» derivados de `recommendations[]` (máx. 5), textos no JSON.
3. Policy reforça §15: causa não confirmada → hipótese, nunca afirmação.

### H6 — Detalhamento

1. Serviço de qualidade valida checklist §19 no metadata antes de persistir mensagem do assistente (warn em dev, métrica em prod).
2. Fixture com 15 cenários cross-domínio.
3. Atualizar [`perguntas-teste-chat-jun2026.md`](../testing/perguntas-teste-chat-jun2026.md).

---

## 9. Integração com trabalho recente (jun/2026)

| Entrega recente | Relação com Playbook 13 |
|-----------------|-------------------------|
| `ChatOperationalDataCommentaryService` | Núcleo do H2 — expandir perfis |
| `ChatOperationalCommentaryEnrichmentService` | Ponto único de merge no metadata |
| Narrativa stack (`humanized-narrative-stack-jun2026.md`) | Camada 1–2 no markdown |
| `presentationDecision` + remoção de toggle pós-resposta | Evidência fixa (camada 3); foco em prosa inicial |
| Cores Recharts / tema claro | Legibilidade da camada evidência — não substitui commentary |
| `ChatPresentationInsightService` | Insight curto alinhado ao §3 (significado do número) |

---

## 10. Template universal (referência §16)

Ordem canônica para **qualquer** domínio — implementada via stack + commentary, não copiada no prompt do agente.

```markdown
### {título da consulta}

<!-- section:summary -->
**Resumo:** {conclusão principal}. Na prática, {interpretação}.
**Status:** {alertLevel}
**Próxima ação:** {nextAction}

<!-- section:indicators -->
**Indicadores principais**
- {indicador}: {valor} — {significado}

<!-- section:diagnostic -->
**Diagnóstico**
{analysis em prosa curta}
{anomalies destacadas}

<!-- section:limitations -->
_{limitations}_

<!-- section:panels -->
{painéis: KPI, gráfico, tabela, árvore — conforme presentationDecision}

<!-- section:next_steps -->
**Próximos passos sugeridos**
{recommendations como lista ou chips}
```

Marcadores `<!-- section:* -->` já compatíveis com `ChatPresentationStackMarkdownService`.

---

## 11. Checklist de validação (§19)

Antes de merge em H6, cada resposta com dados deve passar:

```text
[ ] A resposta começa com uma conclusão (summary)?
[ ] Os principais números foram interpretados (highlights / derivedMetrics)?
[ ] Há separação entre fato, análise, hipótese e recomendação?
[ ] Existem alertas ou anomalias destacados quando aplicável?
[ ] As visualizações têm propósito claro (purpose / reason)?
[ ] As limitações foram informadas quando relevantes?
[ ] Há próximas ações sugeridas (nextAction / recommendations)?
[ ] A linguagem está simples e orientada à decisão?
[ ] Nenhuma causa não confirmada foi afirmada como fato?
[ ] Textos PT vieram de JSON, não de literals no código?
```

Automação alvo: `ChatHumanizedResponseQualityService.evaluate(metadata) → { passed, failures[] }`.

---

## 12. Testes de regressão planejados

| ID | Cenário | Esperado |
|----|---------|----------|
| H-01 | Status fabril com MP crítica | `alertLevel=attention`, summary primeiro, gráfico com `purpose` |
| H-02 | Estoque multi-filial com zero | anomalia `zero_value`, recomendação «ver exceções» |
| H-03 | SQL com 1 linha KPI | camada rápida só KPI + summary |
| H-04 | Ranking vendas | `horizontal_bar`, não tabela completa primeiro |
| H-05 | BOM / estrutura | árvore na evidência, resumo na camada 1 |
| H-06 | Dados insuficientes | `alertLevel=unknown`, limitations preenchido |
| H-07 | «Explique esse painel» | `ChatDataInterpretationAnswerService` usa commentary sem nova tool |
| H-08 | Queda abrupta série temporal | anomalia `sharp_drop`, hipótese não confirmada |
| H-09 | Métrica derivada cobertura | `derivedMetrics` com `computedBy=platform` |
| H-10 | Comparação dois produtos | analysis + facts; sem causa inventada |

Arquivos alvo:

- `tests/fixtures/humanized_data_response_cases.py`
- `tests/unit/domain/services/test_chat_operational_data_commentary_service.py`
- `tests/unit/application/services/test_chat_data_interpretation_answer_service.py`
- `plugins/minha-delpi-chat/src/ui/components/assistantContentVisualFormats.test.ts`

---

## 13. Prompt desacoplado (§17 — implementar em H1)

Arquivo: `app/domain/prompt_policies/humanized-data-response.md`

```markdown
Ao responder perguntas que envolvam dados, não apresente apenas os dados brutos.
Transforme os dados em uma explicação clara, humana e acionável.

Use o bloco metadata.dataCommentary e textPresentation como fonte primária.
A resposta deve começar com a conclusão principal, o significado, o ponto de atenção e a próxima ação.

Organize em camadas: resumo executivo → indicadores → atenção → interpretação → visuais → detalhes → próximas ações.
Para cada número importante, explique o significado prático.
Diferencie fatos, análises, hipóteses (sempre não confirmadas) e recomendações.
Não invente causas quando os dados não permitirem concluir.
Informe limitações, filtros, período e dados ausentes quando forem relevantes.

Use tabelas, gráficos, cards, árvores ou fluxos somente quando ajudarem a responder melhor.
Todo gráfico deve ter uma pergunta clara (presentationDecision.purpose).
Linguagem simples, direta e orientada à decisão.
```

Registrar em `PromptPolicyService` para turnos com tools operacionais — **complementa**, não substitui, o commentary determinístico.

---

## 14. PR checklist (obrigatório por fase)

1. Regra nova está no **módulo canônico** da tabela §3?
2. Domain sem import de infra?
3. Texto PT novo só em `assistant/*.json`?
4. Send e stream usam o mesmo serviço?
5. Teste ou caso em fixture de regressão?
6. `chat-intelligence-base.md` atualizado se novo serviço público?
7. Agente default **não** ganhou lógica exclusiva de narrativa?

---

## 15. Ordem de execução recomendada

```text
H1 (contrato + JSON + policy)
  → H2 (commentary multi-perfil)     ← maior impacto visível
    → H3 (anomalias + métricas)
      → H4 (camadas + purpose visual)
        → H5 (interpretação + chips)
          → H6 (qualidade + CI)
```

**Quick win imediato (pode antecipar H2):** completar commentary de `stock` e `production_status` reutilizando padrão `factory_status` — valida o playbook com o caso **90262404** (status fabril + saldo MP) antes da generalização completa.

---

## 16. Referência — diretrizes originais

As 19 seções do documento de diretrizes gerais («Começar pela resposta», «Separar fato/análise», … «Checklist rápido») são a **especificação funcional** deste playbook. Este arquivo traduz essas diretrizes em módulos, contratos, fases e testes do repositório Minha DELPI.

**Regra central (§18):**

```text
A IA deve converter dados em entendimento.
Primeiro responde, depois mostra evidências.
Primeiro orienta, depois detalha.
Primeiro explica o impacto, depois apresenta os campos técnicos.
```
