# Arquitetura — Inteligência no chat base

**Status:** vigente (maio/2026)  
**Público:** desenvolvimento `minha-delpi-ai-api`, plugin `minha-delpi-chat`, gestão de agentes

---

## Princípio

O **chat** é onde a inteligência transversal evolui. **Agentes** são instâncias de chat com mais habilidades, contextos e actions — não um motor paralelo.

| Conceito | Papel |
|----------|--------|
| **Chat (sessão)** | Pipeline de mensagens, histórico, tools, RAG, LLM |
| **Agente** | `system_prompt`, skills, actions permitidas, especialização de conhecimento |
| **Projeto** | Prompt de projeto, agente padrão, agrupamento de sessões |
| **Simulação / admin** | Mesmo pipeline, com rascunho ou sandbox |

Melhorias de inteligência (comparação, insights, fast path operacional, resposta direta, contexto de ferramentas no histórico) devem ser implementadas na **camada base** e **herdadas** automaticamente por agentes, projetos e demais consumidores.

---

## Pipeline base

```text
Mensagem do usuário
  → Segurança (input)
  → ChatWorkspaceContextService (projeto + agente + capabilities)
  → ChatIntelligencePipelineService
        · decisão operacional / análise
        · contexto de conversa (incl. previews de tools no histórico)
  → ChatToolContextService (seleção e execução de tools/actions)
        · finalize: modo análise, supressão de direct answer
  → RAG (escopo agente/projeto/anexos)
  → ChatPromptBuilderService + prompt_policies
  → LLM (stream ou send)
```

**Camadas antes do LLM (modelo completo, short-circuit, implementação por fases):** [`chat-pre-llm-layers.md`](./chat-pre-llm-layers.md).

### Serviços centrais

| Serviço | Função |
|---------|--------|
| `ChatIntelligencePipelineService` | Orquestra decisões pré/pós-tools compartilhadas |
| `ChatConversationContextService` | Texto de histórico + dados de `toolCalls` em metadata |
| `ChatAnalysisIntentService` | Detecção de comparação / insights |
| `ChatCanvasIntentService` | Pedido de enviar conteúdo à lousa (não confunde com Canva.com) |
| `ChatCanvasContentService` | Monta markdown da última resposta assistant + confirmação |
| `ChatToolContextService` | Execução de tools; aceita `previous_messages` para herdar análise |
| `ChatExternalActionOrchestrationService` | Planeja várias actions OpenAPI (ex.: dois códigos de produto) |
| `ChatCompositeDirectAnswerService` | Monta resposta direta única com sucesso/erro por consulta |
| `ChatOperationalPipelineService` | Fast path operacional (desligado em modo análise) |
| `ExternalActionSelectionService` | Roteamento OpenAPI (não dispara consulta em pedido analítico nem em pedido de lousa) |
| `ChatDepartmentKpiIntentService` | KPIs departamentais (`/commercial`, `/financial`, `/production`, `/hr`, `/quality`, `/system`) |
| `ChatCapabilitiesService` | Perguntas «consegue…?» / capacidades sem chamar API à toa |
| `ChatMessageNormalizationService` | Typos comuns (ebita→ebitda, kaisen→kaizen, coonsegue→consegue, …) |
| `ChatStructureComparisonOrchestrationService` | Comparação de estruturas com fetch multi-produto |
| `PromptPolicyService` | Policies globais (`operational-agent.md`, `chat-analysis-insights.md`, …) |

Use cases (`SendChatMessageUseCase`, `StreamChatMessageUseCase`, `AdminAgentSimulateUseCase`) **não** devem acumular regras de inteligência — apenas passam histórico e flags ao pipeline.

---

## O que o agente adiciona (e só isso)

1. **Prompt** — personalidade e instruções (`system_prompt`).
2. **Skills** — policies extras (`metadata.skills`).
3. **Actions** — subset de rotas OpenAPI (`allowedActionIds` / providers).
4. **RAG** — filtros de especialização (tags, categorias, namespaces).
5. **Limites** — `max_tool_calls`, confirmação de escrita, capabilities.

O agente **não substitui** detecção de intenção, pipeline operacional ou modo análise comparativa.

**Base global de conhecimento:** agentes sem skill explícita `company-knowledge` herdam `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL` (documentos como `O_ARQUITETO_DO_CODIGO.md`).

---

## Roteamento automático (api-delpi)

O `ExternalActionSelectionService` resolve a action **antes** do LLM quando o fast path operacional está ativo. Ordem resumida:

1. Pedidos de **comparação/insights** → sem action (modo análise).
2. **OV / LMP / Transforma Mais / metadados Protheus** (tabelas/colunas).
3. **Suprimentos** (CPV, OTD, giro, valor total de estoque) — sem código de produto.
4. **Produto por código** (estoque, estrutura, pais, descrição, …) por intent.
5. **Busca por grupo ou descrição** → `GET /products/search` (prioridade sobre analyser quando há «grupo X»).
6. **KPI departamental** via `ChatDepartmentKpiIntentService`.
7. Fallback semântico (se ranker configurado).

### Regras críticas (produtos)

| Situação | Rota correta | Erro comum |
|----------|--------------|------------|
| «Busque 3 produtos do **grupo 1008**» | `GET /products/search` + `group_code=1008`, `page_size=3` | Tratar `1008` como `{code}` no `/analyser` |
| «Resumo do produto 10080047» | `GET /products/{code}/summary` | Cair no `/analyser` |
| «Faturamento do produto …» | `GET /products/{code}/sales/billing` | Usar `/sales` genérico |
| «Valor total de estoque da empresa» | `GET /supplies/stock-value` | `GET /products/{code}/stock` |
| «Compare as estruturas» | Orquestração multi-fetch | Uma única action ou só histórico |

O dígito após «grupo» **não** é código de produto (`ChatProductQueryIntentService._is_group_code_numeric_token`).

### Perguntas de capacidade

«Consegue buscar por grupo?», «coonsegue…» → `ChatCapabilitiesService.is_capability_inquiry`: resposta direta com método/rota, **sem** `execute_external_action`.

### Documentos e testes

| Recurso | Caminho |
|---------|---------|
| Mapa intenção → rota (RAG) | [`../knowledge/api-delpi-rotas-agente.md`](../knowledge/api-delpi-rotas-agente.md) |
| Auditoria rota a rota + status | [`../roadmap/api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md) |
| Casos de regressão | `tests/fixtures/chat_intelligence_regression_cases.py` |
| Limite upload conhecimento | `KNOWLEDGE_DOCUMENT_MAX_CHARS` (default 2M) |

```bash
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_intelligence_regression.py \
  tests/unit/domain/services/test_chat_department_kpi_intent_service.py \
  tests/unit/application/services/test_external_action_selection_service.py \
  tests/unit/domain/services/test_chat_product_query_intent_service.py \
  -q
```

---

## Checklist para novas features de inteligência

- [ ] Implementação em serviço/domain compartilhado (não só no JSON do agente).
- [ ] `ChatToolContextService` ou pipeline atualizado se afetar tools/histórico.
- [ ] Policy em `prompt_policies/` se mudar comportamento do LLM para todos.
- [ ] Testes unitários + caso em `chat_intelligence_regression_cases.py` quando aplicável.
- [ ] Sem duplicar lógica entre stream e send.
- [ ] Simulação admin recebe `previous_messages` quando depender de histórico.

---

## Referências

- Auditoria api-delpi (maio/2026): [`../roadmap/api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md)
- Roadmap onda 1 (pipeline): [`../roadmap/inteligencia-chat-onda-1.md`](../roadmap/inteligencia-chat-onda-1.md)
- Agentes (HTTP): [`../api/03-agentes.md`](../api/03-agentes.md)
- Modelo conceitual: [`../api/12-modelo-conceitual.md`](../api/12-modelo-conceitual.md)
- Regra Cursor: [`.cursor/rules/chat-intelligence-base.mdc`](../../../.cursor/rules/chat-intelligence-base.mdc)
