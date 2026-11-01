# 213 — Modernização arquitetural: inventário, frameworks e arquitetura-alvo

- **Estado:** Etapas 1–2 entregues (inventário + decisões + alvo); Etapa 3 parcial.
- **Baseline:** `d199686f92` (pós-Task 36 — envelopes tipados nos 6 owners, recovery e2e provado em cmp_10).
- **Princípio norteador:** reutilizar mecanismos maduros quando superiores; não criar segunda engine; não acoplar Domain/Application a frameworks.

## 1. Inventário real da DÉLIA (runtime B1, verificado por código)

| Componente | Implementação real | Fonte |
|---|---|---|
| Runtime/sequencing | LangGraph `StateGraph` + `add_conditional_edges` (1 grafo por turno governado) | `app/infrastructure/orchestration/langgraph_engine.py` (~400 linhas) |
| Planner semântico | Modelo via `InvokeModel` + prompts purpose-tagged (`arguments`, `select_group`, `select_capability`, `native_assessment`) | `capability_provision/orchestration.py` |
| Discovery | `tools/list` live por request; sem catálogo local (dinâmico comprovado — testes A–F da Task 33) | `SpecialistInterop` + `McpCapabilityProvider` |
| Registry aprovado | `_SPECIALIST_IDENTITY` fonte única (display,owner,client_id,audience); `APPROVED_SPECIALIST_IDS` fail-closed | `app/domain/specialist_interop/rules.py` |
| Arggen | Proposta tipada do modelo + validação de schema + bounded re-proposal | `capability_provision/orchestration.py` |
| Recovery | `_recover_relevance` (1 rodada bounded, `owner_hint` sanitizado reintroduzido ao prompt, dedup+live-surface revalidation, `_RELEVANCE_RECOVERY_USED`) — T23+T36 | `orchestration.py:6210,10714+` |
| Error taxonomy | `SpecialistInteropError.code` + `OWNER_ARGUMENT_REJECTED`/`owner_hint` (envelope owner tipado — Task 36) | `specialist_interop/errors.py` |
| Budgets | Global por investigação (calls, invokes, retries, tokens, deadline, dedup) | orchestration + `remaining_budget` |
| Checkpoint/continuidade | Parcial: workspace context + prior_turns por turno; **sem** checkpointer LangGraph (durable/resume não usados) | `langgraph_engine` + contexto de turno |
| Paralelismo | Fan-out custom por specialist no provider (`list_groups` com budget global); sem `Send`/`interrupt` nativos | `mcp_provider.list_groups` |
| Evidence/Outcome | `GoalEvidenceJudgment`, `EvidenceFacts`, Business Outcome com rubrica (rubrica por subobjetivo ainda heurística) | app/domain evidence |

## 2. Matriz de frameworks (documentação oficial + uso real)

| Framework | Uso atual | Capacidade nativa não aproveitada | Decisão |
|---|---|---|---|
| **LangGraph 1.2.16** | Sequencing por turno | `Send` (fan-out dinâmico), checkpointers (SqliteSaver), `interrupt`/resume, subgraphs, reducers, retry policies | **EXTEND** — adotar `Send` para fan-out de subobjetivos + checkpointer local para retomada; sem trocar runtime |
| **Pydantic AI** | Não instalado | Structured outputs tipados, `ModelRetry`, toolsets, usage tracking | **ADOPT_BOUNDED** — candidato à validação pré-invoke/arggen tipada atrás do port existente; **não** como substituto do gate de erros do owner (Task 35 provou que só o owner declara recuperabilidade) |
| **MCP Python SDK** | Já em uso (protocol 2024-11-05) | Sessions, tools/list, structured results — já coberto | **REUSE_EXISTING** — sem ganho de substituição |
| **LangChain MCP Adapters** | langchain-core 1.7.1 presente | Conversão tools→LangChain | **REJECT** — segunda camada sem ganho (adapter próprio + interop já provam a cadeia) |
| **LlamaIndex Workflows** | Não instalado | Event-driven fan-out/fan-in, checkpoints | **DEFER** — LangGraph cobre o mesmo papel com a stack já instalada; dois orquestradores = anti-padrão |

## 3. Arquitetura-alvo (substituível, sem novo port)

```text
LangGraph B1 (sequencing + Send fan-out + checkpointer)
  → Application semantic contracts (já existentes)
    → arggen tipado + validação (existing; Pydantic AI opcional bounded)
      → SpecialistInterop + McpCapabilityProvider (existing)
        → 7 MCP owners (envelopes tipados T36) → Evidence/Outcome
```

Decisões: LLM decide; contratos restringem; owners validam/executam; EvidenceFacts provam. Sem branches por especialista; sem registry paralelo; sem segunda engine.

## 4. Etapa 3 — estado de implementação

- **S1 contratos/composição:** já conforme (Ports&Adapters, composition root, substituibilidade por config — providers ligados por env-driven `specialist_connections_from_settings`).
- **S2 arggen tipada:** envelope+recovery implementados (T36); residual = arggen do modelo 4B não ancora em enums — hipótese bounded = Pydantic AI structured-output na re-proposta (pendente de benchmark S2/doc212).
- **S3 investigação composta:** parcial — re-proposta bounded existe; subobjetivos ainda implícitos no turno, sem estado de checkpoint.
- **S4 paralelismo:** fan-out custom funcional; `Send` do LangGraph é a evolução candidata (não implementado nesta iteração).
- **S5 checkpoints:** pendente — LangGraph checkpointer local é o caminho aprovado.
- **S6 evidência/síntese:** rubrica por subobjetivo pendente (Doc 211 §10-11).
- **S7 limpeza:** registry consolidado (T32); envelopes uniformizados (T36).

> **Continuidade vinculante (coordenação, 2026-11-01):** Documento 214 — `214-s2-s6-binding-implementation-acceptance-contract.md` — fixa escopo de implementação S2–S6, critérios objetivos não delegáveis, provas E2E, testes e procedimento de handoff. Os passos de §5 abaixo são referências, **não autorizam encerramento docs-only**. O executor deve seguir o Documento 214 após reancoragem canônica.

## 5. Residuais e próximos bounded steps

1. Benchmark S2: Pydantic AI structured-output na re-proposta de args vs mecanismo atual (mesmos 15 casos + held-out).
2. `Send` API para fan-out de subobjetivos independentes (medir latência/tokens vs fan-out custom).
3. Checkpointer local para retomada de investigação multi-turno.
4. Rubrica por subobjetivo no avaliador (Doc 211 §10-11).
5. Etapa 4: doc211 ×3 com a arquitetura revisada.

`PRODUCTION_DEPLOY=NO`; `FABRICATIONS=0`; `UNAUTHORIZED_ACT=0`.
