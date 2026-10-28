# 189 — DÉLIA · Registro prioritário de avaliação de soluções de mercado (REUSE BEFORE BUILD)

**Data:** 2026-10-28. **Status:** PRIORIDADE DE INVESTIGAÇÃO / PLANNED; **não** é ADR de adoção, mudança de arquitetura, autorização de dependência, mudança de fase ou de deploy.
**Origem:** decisão do Product Owner de avaliar bibliotecas Python, frameworks de agentes, ferramentas MCP, automação, observabilidade e execução antes de continuar construindo grandes fluxos manualmente.
**Ligação:** Documentos 187 (contexto e eficiência) e 188 (diagnóstico WP0/WP1); task H6 já autorizada permanece independente.

> **REGRA DE RECUPERAÇÃO PARA PRÓXIMAS SESSÕES:** ANTES DE PROPOR NOVO PLANNER/ENGINE/WORKFLOW/STORE/GATEWAY/ADAPTER, CONSULTAR ESTE REGISTRO E AS AUTHORITIES VIGENTES. Avaliar solução madura do mercado por boundary legítimo e exigir EXISTING_EQUIVALENT, REUSE_DECISION, custo de integração e prova A/B local. Este documento é backlog de discovery, não tem precedência sobre 16→50→17→49→51→52→21→20→25, specs temáticas e ledger.

## 1. Problema e objetivo

No diagnóstico 188, o fluxo produtivo dos turnos T3/T4.2 apresentou 16/19 chamadas ao modelo, aproximadamente 23,7k/32,3k tokens de entrada e 113/193 s, sem entregar o Business Outcome de dois produtos com códigos. Parte das chamadas repetidas foi identificada; o gap estruturado em select_candidate está na task H6. Isso **não prova** que adotar um framework melhora o resultado.

**Diretriz de produto, prioridade ALTA:** reduzir implementação caseira de infraestrutura commodity e longas iterações de refatoração, aproveitando bibliotecas/frameworks já mantidos, **sem substituir** owner, autorização, contratos nem capacidade semântica por um novo sistema paralelo.

## 2. Catálogo de candidatos para análise (não instalados/não aprovados)

| Frente | Ferramentas candidatas | O que avaliar | Boundary / ressalva |
|---|---|---|---|
| Estado e continuidade intra-turno | **LangGraph**; LangChain/Deep Agents | estado, nós, checkpoints, interrupções, selective context; overhead e volume de chamadas | Somente infraestrutura sob DÉLIA; não criar novo planner ou source of truth |
| MCP + tool schemas tipados | **Pydantic AI**; **mcp-agent**; **OpenAI Agents SDK** | discovery/toolsets, validação, output estruturado, retry, delegação; adaptadores provider-neutral | MCP é interoperabilidade, não permission ou FACT; preservar DAVI-only para DELPI |
| Multi-agent e workflows de agentes | **Microsoft Agent Framework**; **Google ADK**; **CrewAI**; **Agno**; **Strands Agents** | coordenação, loops limitados, handoffs, paralelismo real, supervision e custo de integração | Evitar criar multi-agent para problema resolvido com uma seleção e um executor |
| Retrieval/documentos | **LlamaIndex Workflows**; **Haystack** | pipelines de recuperação, evidência e avaliação, somente se houver gap comprovado | Não substituir Domain API por RAG nem transformar retrieval em authority |
| MCP server/gateway | **FastMCP**; **Microsoft MCP Gateway**; bibliotecas oficiais **MCP Python SDK** | transporte, auth, lifecycle, roteamento, telemetry e aproveitamento de shared MCP existente | Primeiro inventariar shared/delpi_mcp, DAVI e adapters DÉLIA; gateway não autoriza sozinho |
| Execução durável e jobs | **Temporal**; **Prefect**; **Dagster**; **Dapr Workflow**; **DBOS** | retries, persistência, schedules, replay, observability, long-running Work | Verificar owner e mecanismo existentes no Automation Hub antes de propor engine novo |
| Low-code/no-code workflows | **n8n**; **Windmill**; **Activepieces** | integrações prontas, automação, approval, conectores, triggers e scripts | Potencial executor/adapter **dentro da boundary do Automation Hub**, não segundo planner; avaliar licença/self-host |
| Observabilidade e evals | **OpenTelemetry**; **Langfuse**; **Arize Phoenix**; **LangSmith**; **Braintrust** | traces por estágio, correlação de provider IDs, token/cost, comparação A/B e outcome | Reutilizar ModelCallLedger e telemetria existente; não persistir prompts/CoT/secrets sem governança |
| Structured outputs e schema | **Pydantic**; **Instructor**; **Guardrails AI** | conformidade JSON/schema, erro/retry e budgets | Avaliar se resolve os invalid_structured_output existentes sem duplicar validação |
| UI/automação governada | **Playwright**; **Robocorp** (e alternativas RPA existentes) | quando não houver API legítima; testes de UI, workflows repetitivos | Executar via owner técnico, nunca ferramenta de planner nem autorização implícita |

**Fontes de partida** (validar versão, suporte, licença, SLA e segurança na data da avaliação):
- https://docs.langchain.com/oss/python/langgraph/overview
- https://ai.pydantic.dev/
- https://docs.mcp-agent.com/workflows/orchestrator
- https://openai.github.io/openai-agents-python/
- https://learn.microsoft.com/en-us/agent-framework/
- https://google.github.io/adk-docs/
- https://docs.crewai.com/
- https://docs.agno.com/
- https://strandsagents.com/
- https://docs.llamaindex.ai/
- https://haystack.deepset.ai/
- https://gofastmcp.com/
- https://github.com/modelcontextprotocol/python-sdk
- https://microsoft.github.io/mcp-gateway/
- https://docs.temporal.io/
- https://docs.prefect.io/
- https://docs.dagster.io/
- https://docs.dapr.io/
- https://docs.dbos.dev/
- https://docs.n8n.io/
- https://www.windmill.dev/docs
- https://www.activepieces.com/docs
- https://opentelemetry.io/docs/
- https://langfuse.com/docs
- https://arize.com/docs/phoenix
- https://docs.langchain.com/langsmith/
- https://www.braintrust.dev/docs

## 3. Como decidir, sem framework-driven redesign

**Passo 0:** reancorar HEAD/git status/AGENTS/.cursor; sources 16→50→17→49→51→52→21→20→25; arquitetura técnica, Product Spec, spec MCP/A2A/automation/AI/observability e ledger. Verificar as decisões DÉLIA → DAVI/MCP → API DELPI e ownership.

**Passo 1:** mapear por responsabilidade e código real a solução já existente (por exemplo _TurnGoal, EvidenceFacts, ModelCallLedger, recovery, model invocation, shared/delpi_mcp e Automation Hub). Registrar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`. Search miss não prova ausência.

**Passo 2:** preencher matriz de cada candidato: responsabilidade real; capacidade documentada vs comprovada; adequação Python/LLM local e provider-neutral; interoperabilidade MCP; estado/checkpoints; segurança/AuthN/AuthZ delegada; retries/idempotência; operabilidade; licença e custos; suporte e maturidade; esforço de integração; risco de lock-in; convivência com contratos/owners existentes.

**Passo 3:** reduzir a shortlist a no máximo duas alternativas por problema real. Preferir integrar **biblioteca específica** à infraestrutura existente a migrar todo o orquestrador. Novas abstrações exigem Abstraction Gate e aprovação de coordenação.

**Passo 4:** se justificado, propor POC **local e isolada** com fake DAVI, fixtures determinísticas e modelos locais (se disponíveis); mesmos cenários e critérios de baseline, incluindo dois produtos/códigos, irrelevância→recovery, generalização, context provenance, segurança e false positives. Registrar task outcome + chamadas/tokens reais disponíveis + latência + esforço de manutenção. POC não significa adoção.

**Passo 5:** decisão `KEEP_CURRENT | ADOPT_LIBRARY_IN_ADAPTER | BOUNDED_MIGRATION_CANDIDATE | REJECT | INCONCLUSIVE` com evidência e owner/contrato. Não trocar runtime, não fazer deploy, não criar provider e não mudar fase sem gate específico.

## 4. Invariantes

- **DÉLIA standalone**; não usar runtime Minha DELPI Chat.
- **LLM = proposta semântica**; DÉLIA/Core/Domain = validações, autoridade, Policy/Decision.
- **DÉLIA → DAVI/MCP → API DELPI**; sem OpenAPI DELPI direto.
- Discovery != approval; tool metadata != permission; MCP result != FACT.
- **Keycloak** identidade; **Core** autorização de plataforma; **Domain APIs** autoridade de negócio; **DÉLIA** intelligence/Work/Outcome; **Automation Hub** execução técnica.
- Read != write; PREPARE != ACT; simulate != apply; technical success != business outcome.
- Não persistir CoT, secrets ou tokens em telemetry/memory; reduzir payload e preservar evidence refs/provenance.
- Não criar scheduler, memória, registry, engine, gateway ou segundo planner por conveniência; verificar equivalentes.
- n8n não assume automaticamente Automation Hub nem Policy; proposta de integração exige avaliação do owner, contratos e licença.
- Software de mercado não é solução aprovada só por popularidade; comparar em A/B local.

## 5. Backlog priorizado de avaliação

**P0 — Infraestrutura do fluxo de inteligência:** comparação read-only do código real com Pydantic AI, mcp-agent, LangGraph, OpenAI Agents SDK; avaliar especialmente candidate binding, continuidade, schemas, bounded recovery e redução de repetições. Entrega: matriz existente x solução x gap comprovado.

**P1 — Telemetria/qualidade:** OpenTelemetry/Langfuse/Phoenix e ferramentas atuais; correlação por stage/attempt/provider generation ID, tokens, regressão semântica, custo e Outcome.

**P2 — Work/Automation:** verificar Automation Hub e se n8n/Windmill/Activepieces/Temporal/Prefect são adaptadores úteis ou duplicariam execução técnica.

**P3 — Outras alternativas:** Google ADK, Microsoft Agent Framework, CrewAI, Agno, Strands, LlamaIndex/Haystack, MCP gateway; somente em caso de problema material correspondente.

**NEXT sugerido:** criar task bounded `DELIA-C3-MARKET-REUSE-FRAMEWORK-FIT-ASSESSMENT-01` (read-only, sem nova dependência/POC automática), mantendo H6 já autorizado. A fase/NEXT efetivos sempre vêm do 16 e ledger; este registro não altera essas authorities.

## 6. Estado e evidência

`DOCUMENTATION_REGISTERED=YES`; `RUNTIME_ADOPTION=NO`; `CODE_CHANGED=NO`; `TESTS=NOT_RUN`; `DEPLOY=NO`; `FRAMEWORK_FIT=TO_INVENTORY`; `PRODUCTION_OUTCOME=UNCHANGED`. Registrar decisão futura em ADR próprio somente após inventário e avaliação.
