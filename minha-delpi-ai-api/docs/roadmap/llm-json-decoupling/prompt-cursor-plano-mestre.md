# Prompt para Cursor — plano completo de desacoplamento JSON + LLM/OpenAPI

Copie o bloco abaixo para o Cursor em **Plan mode**. O objetivo inicial é revalidar o repositório e produzir/atualizar um plano executável; não implementar até existir autorização explícita.

---

## Prompt

Você está trabalhando no monorepo `delpi-central`, com foco em `minha-delpi-ai-api`.

### Objetivo

Investigue o código e os contratos atuais e construa um plano completo para remover acoplamentos residuais em `minha-delpi-ai-api/app/content`, substituindo:

1. catálogos técnicos duplicados por **OpenAPI + Action Catalog**;
2. árvores de NLU/intent baseadas em terms/regex/excludes/predicates por **Turn Understanding + retrieval + planner LLM estruturado**;
3. follow-up/refinement por path/route markers por **estado conversacional estruturado + schema**;
4. mini catálogos manuais de actions/capabilities por **metadata materializada do Action Catalog**;
5. recomendações/sugestões estáticas por geração contextual grounded, preferencialmente reutilizando a síntese LLM já existente no turno;
6. path/entity-specific presentation residual quando `responseSchema + payload + metadata` forem suficientes.

Não aplique `JSON -> LLM` indiscriminadamente. Preserve como determinísticos: RBAC, sensitivity, confirmation, required/type/enum/format, regras factuais, regras de negócio, limites, timeout/retry, formatação determinística e policies. Preserve copy/UX/prompts legítimos como conteúdo configurável.

### Ordem de autoridade obrigatória

Leia antes de qualquer decisão:

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc`
3. `.cursor/rules/evidence-driven-execution.mdc`
4. `.cursor/rules/plan-construction.mdc`
5. `.cursor/rules/plan-execution.mdc`
6. `.cursor/rules/test-and-commit.mdc`
7. `.cursor/rules/openapi-first-universal-tool-routing.mdc`
8. `.cursor/rules/assistant-content-json.mdc`
9. `.cursor/rules/ai-intelligence-evaluation.mdc`
10. regras especializadas adicionais indicadas pelo index para chat, tools, LLM stack, schema-first presentation, help e budget.

Depois leia:

- `minha-delpi-ai-api/docs/roadmap/openapi-first-universal-tool-routing.md`
- `minha-delpi-ai-api/docs/api/04-actions-openapi.md`
- `minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md`
- `minha-delpi-ai-api/docs/roadmap/llm-json-decoupling/README.md`
- `minha-delpi-ai-api/docs/roadmap/llm-json-decoupling/roadmap.md`
- todos os arquivos em `minha-delpi-ai-api/docs/roadmap/llm-json-decoupling/planos/`.

### Regras da investigação

- Código/contrato/testes atuais prevalecem sobre este roadmap se houver drift.
- Se uma decisão do roadmap estiver superada, registrar `EXECUTION_DRIFT` com evidência e corrigir o plano antes de implementar.
- Não assumir que um JSON está acoplado só pelo nome: localizar todos os producers/consumers/fallbacks/tests/docs.
- Não assumir que algo deve ir para LLM: classificar primeiro.
- Não criar nova regra `.cursor` para esta tarefa salvo lacuna de governança comprovada.
- Não duplicar source of truth.
- Não corrigir apenas `api-delpi`: a prova real é provider OpenAPI externo desconhecido.
- Não introduzir `capabilityGroup`, `routeFamily`, `pathClass` ou metadata manual por endpoint como simples substituto do catálogo removido.
- Não criar service/selector/presenter por API ou endpoint.
- Não criar MegaLabelService/MegaIntentService/God service.
- Não adicionar chamadas LLM independentes para action label, title, framing, recommendations e routing se a mesma inferência de turno puder produzir esses dados estruturados.

### Classificação obrigatória por nó JSON

Para cada chave material classifique exatamente como uma das categorias:

```text
TECHNICAL_CONTRACT_DUPLICATION
SEMANTIC_ROUTING_HEURISTIC
SEMANTIC_PRESENTATION_METADATA
LLM_COMPOSITION_CANDIDATE
LLM_LOCALIZATION_CANDIDATE
DETERMINISTIC_POLICY
BUSINESS_RULE
FACTUAL_GUARDRAIL
UX_COPY
VOCABULARY
FAST_PATH
TEST_FIXTURE
GENERATED_SNAPSHOT
DEAD_CONTENT
UNKNOWN_REQUIRES_EVIDENCE
```

E escolha o destino:

```text
OPENAPI_DIRECT
ACTION_CATALOG_MATERIALIZED
SCHEMA_DIRECT
TURN_UNDERSTANDING
ACTION_RETRIEVAL_PLANNER
OPENAPI_ARGUMENT_BINDER
EXISTING_TURN_LLM_SYNTHESIS
DETERMINISTIC_SERVICE
KEEP_JSON
KEEP_GENERATED
DELETE_AFTER_CUTOVER
INVESTIGATE_FIRST
```

### Arquivos/fluxos que exigem investigação prioritária

Não limite a análise a estes arquivos, mas cubra explicitamente:

#### Routing técnico

- `app/content/pt-BR/assistant/operational_route_registry.json`
- `app/content/pt-BR/assistant/api_route_domains.json`
- consumers de `pathMarkers`, `operationIdMarkers`, `routeSegment`, `parameterStrategy`, priority e routeId.

#### NLU/intent manual

- `product_query_intent.json`
- `production_operational_intent.json`
- `department_kpi_rules.json`
- `intent_router.json`
- `analysis_intent_vocabulary.json`
- `operational_pipeline_vocabulary.json`
- `turn_understanding.json`

Mapear terms, excludes, anyOf/allOf/noneOf, customPredicate, regex, keyword scoring e pathTokens.

#### Follow-up/refinement/arguments

- `operational_follow_up_routing.json`
- `operational_group_by_refinement.json`
- `operational_refinement.json`
- `operational_parameters.json`
- conversation state/result references/pending requirements relacionados.

#### Capabilities e composição

- `capabilities.json`, especialmente `pathRules`
- `capability_registry.json`, especialmente `action.*` e `routeHints`
- `entity_capability_catalog.json`
- `department_meta_composition.json`
- `product_enrichment_composition.json`

#### Recommendations/composer

- `humanized_data_response.json`, especialmente `recommendationQueries`, `nextActions` e consumers
- `composer_route_questions.json`
- produtores de `structuredRecommendations` e sugestões do composer.

#### Presentation residual

- `presentation_profiles.json`
- `column_labels.json`
- `product_operational_content.json`
- `presenter_content.json`
- `data_interpretation.json`

Separar: schema/shape, order/format/policy, display semantic metadata e contextual prose.

#### Skills/help/content

- `app/content/pt-BR/skills/catalog.json`
- endpoint/execution hints existentes em help/features/capabilities.

### Arquitetura alvo obrigatória

Provar como o repositório atual converge para:

```text
USER MESSAGE
+ structured conversation context
        |
        v
STRUCTURED TURN UNDERSTANDING
        |
        v
goals/subtasks/entities/references/presentation intent
        |
        v
ALLOWED ACTION CATALOG
        |
        v
semantic retrieval per goal
        |
        v
STRUCTURED PLANNER
        |
        v
OpenAPI argument binding + deterministic validation
        |
        v
RBAC + sensitivity + confirmation policy
        |
        v
generic executor
        |
        v
responseSchema + payload + metadata
        |
        v
schema-driven presentation
        |
        v
existing grounded LLM synthesis
        |
        +--> contextual recommendations/follow-ups
```

### Regra sobre chamadas LLM

Para cada proposta de LLM responda no plano:

1. O dado já existe no OpenAPI/schema/Action Catalog?
2. É uma transformação determinística?
3. É semântica estável que pode ser materializada/cacheada no import?
4. É contextual e precisa da mensagem/resultado atual?
5. Pode ser produzido pela chamada LLM já existente no turno?
6. O que acontece se o modelo falhar/timeout?
7. Qual é o budget de latência/tokens?
8. O output será validado por schema/allowlist/policy?

Preferência:

```text
canonical source
> deterministic transform
> cached/materialized LLM
> reuse existing turn LLM
> new per-request LLM call
```

### Segurança

O plano deve provar:

- planner só escolhe `actionId` presente nas candidates autorizadas;
- nenhuma URL arbitrária vem do LLM;
- provider/action enabled e `allowed_action_ids` são validados;
- writes/admin/destructive respeitam RBAC/sensitivity/confirmation;
- OpenAPI/tool/RAG descriptions são dados não confiáveis quanto a instruções;
- required ausente não é inventado;
- arguments são validados por schema após inferência;
- fallback de linguagem amigável não causa capability outage.

### Evals obrigatórios

Antes de qualquer implementação significativa:

```text
freeze dataset
-> BASELINE
-> immutable run evidence
-> implement candidate
-> same dataset/config
-> CANDIDATE
-> R1-R11
-> live/surface
-> rollout decision
```

Cobrir no mínimo:

- action específica vs genérica;
- semantic siblings;
- multi-provider;
- no-tool;
- required presente;
- required ausente -> clarify;
- enum/type inválido;
- pedido longo com múltiplas subtarefas;
- multi-turn/follow-up;
- typo/sinônimo/linguagem informal;
- unknown external OpenAPI;
- metamorphic rename de provider/path/operationId preservando semântica;
- unauthorized action;
- write/destructive confirmation;
- tool-output/prompt injection;
- send/stream/simulate;
- persist/reload/F5;
- outcome/task success;
- P50/P95, tokens, LLM calls e tool count.

### Métricas do programa

O plano deve criar baseline e metas para:

```text
task_decomposition_recall
action_top_k_recall
action_selection_accuracy
argument_extraction_accuracy
missing_required_argument_accuracy
false_tool_call_rate
unnecessary_follow_up_rate
multi_request_completion_rate
multi_turn_reference_accuracy
unknown_api_task_success_rate
metamorphic_rename_pass_rate
task_success_rate
safety_violation_rate
p50/p95_latency
llm_calls_per_turn
tokens_per_turn
tool_calls_per_turn
catalog_path_coupling_count
manual_intent_rule_count
```

### Formato obrigatório do plano produzido pelo Cursor

Use `plan-construction.mdc` integralmente. Entregue:

1. **Overview**.
2. **Leitura do pedido**.
3. **Ledger RQ** com todos os requisitos.
4. **Inventário real**: JSON -> key -> consumers -> fallback -> tests -> docs.
5. **Matriz de classificação** de cada chave material + destino.
6. **Hipóteses concorrentes** e evidências.
7. **CURRENT -> TARGET** com Mermaid.
8. **Grafo producer/transformer/owner/consumer/persistence/surface**.
9. **Estado antes x depois + invariantes**.
10. **Decisões travadas** com readiness (`READY_CONFIRMED`, `READY_BOUNDED`, `NOT_READY`).
11. **Matriz fluxo x superfície x P0/herança/fora** incluindo send/stream/simulate/F5/admin/UI/Ajuda.
12. **Riscos e rollout/rollback**.
13. **Etapas E1...En e subetapas E*.S***.
14. Para cada subetapa: Objetivo, RQ, Fazer, Não fazer, Evidência, Dependências, Teste, Pronto quando, Commit sugerido.
15. **Rastreabilidade RQ -> decisão -> subetapa -> teste -> aceite**.
16. **Revisão adversarial** com pelo menos 20 perguntas.
17. **verify-final** com checklist do pedido original.
18. **Relatório de completude**: quantos JSONs/chaves foram investigados, quantos consumers, quais ficaram fora e por quê.

### Sequenciamento sugerido — validar antes de travar

Use como hipótese inicial, não como ordem cega:

```text
E0 baseline + inventory + classification
E1 routing registry/OpenAPI
E2 semantic understanding/intents
E3 follow-up/refinement/argument binding
E4 capabilities/action catalog
E5 composition/enrichment
E6 recommendations/composer
E7 presentation schema-first residuals
E8 skills/help/residual content cleanup
E9 shadow/canary/cutover/legacy cleanup
E10 verify-final
```

### Proibições finais

Não:

- implementar durante a construção inicial do plano;
- alterar expectativa de eval para esconder regressão;
- substituir hardcode JSON por hardcode Python;
- substituir pathMarkers por nova taxonomia manual por endpoint;
- criar intent service por domínio novo;
- confiar em prompt para enforcing de RBAC/schema/safety;
- apagar fallback antes de medir divergência;
- declarar sucesso só porque unit tests passaram;
- declarar "mais inteligente" sem R1-R11 + outcome + eficiência;
- manter roadmap concluído como fonte arquitetural permanente: decisões finais devem voltar para docs canônicas e o roadmap concluído deve ser limpo conforme política documental.

Ao final, pare no plano. Não implemente nem faça commit/push de runtime até autorização explícita.
