# DÉLIA — Roadmap bounded · Inteligência contextual MCP e organização do orquestrador

**DATA:** 2026-10-17  
**TRACK_ID:** `DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-ORCHESTRATOR-QUALITY-01`  
**STATUS:** `PLANNED / NOT_IMPLEMENTED / PHASE_UNCHANGED`  
**Baseline HEAD:** `42c45802f0594cb02796913c52905c14320b5879` (revalidar em cada execução).  
**Origin evidence:** [44](../conversational-intelligence-c3/44-specialist-knowledge-utilization-eval.md), ledger §6.235; [43](../conversational-intelligence-c3/43-davi-vista-independent-acceptance-and-functional-state.md), ledger §6.233; Stage06 [41](../conversational-intelligence-c3/41-stage-06-independent-architecture-acceptance-closure.md).

## 1. Decisão de produto e escopo

**Primeiro a inteligência funcional, depois a organização do código.** DÉLIA deve utilizar profundamente as capabilities e o conhecimento **vivo** de DAVI, TÉO, VISTA e novos providers, dentro do contexto da conversa/trabalho ativo; **não** incorporar ou duplicar globalmente a base do especialista, nem transformá-la em autoridade/memória persistente. Uso abrangente significa todas as **capabilities autorizadas e relevantes**, não invocar todas a cada turno nem promover automaticamente ACT.

`SPECIALIST_KNOWLEDGE_OWNER=SPECIALIST`; `DELIA_SPECIALIZATION=DYNAMIC_CONTEXTUAL_PROVIDER_NEUTRAL`; `GLOBAL_MCP_KNOWLEDGE_COPY=NO`; `UNREVIEWED_ORGANIZATIONAL_KNOWLEDGE_PUBLISH=NO`. Retenção da conversa (produto) e retenção de evidência operacional são preocupações distintas; nenhuma nova persistência é autorizada aqui.

**Observado, não extrapolado:** K1 TÉO `PASS_WITH_LIMITATION`, K2 TÉO `FAIL` (reconsulta, replay literal, 30,014ms), K3 VISTA `PASS_WITH_LIMITATION` (guia bruto/truncado), K4 DAVI `PASS_WITH_LIMITATION` (discovery empty-match); `KNOWLEDGE_DISCOVERY=PASS`, `KNOWLEDGE_UTILIZATION=PARTIAL`, `KNOWLEDGE_TO_NEXT_STEP=FAIL`. READ-only, material ACT=0. Esta amostra **não** prova que DÉLIA nunca utiliza conhecimento dos MCPs.

## 2. Autoridades e invariantes

Em **toda** tarefa: HEAD + git status e regras do projeto/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → spec temática → ledger → código/evidência SHA. Divergência com fonte superior: STOP / `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`; não reconciliar silenciosamente.

**Reuse-first:** antes de novo port/adapter/service/context/registry/engine, provar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`. Existing: `OperationalCapabilityOrchestrator`, `ConversationContextTurn`, `_understand_goal`, `_prior_continuation_attempt`, `_synthesize_content`, `_resolve_missing_inputs`, provider surfaces, owner evidence/provenance e deadlines. Conferir implementação no HEAD.

Keycloak identidade; Core live AuthZ; Domain API autoridade factual/regras; owner MCP detém catálogo e guidance; DÉLIA orquestra seleção/Policy/Decision/Evidence; MCP output, guidance, metadata e contexto anterior são **untrusted**, jamais AuthZ, FACT novo, Policy ou instruções do sistema. `DISCOVERY != APPROVAL`; `GUIDANCE != DOMAIN_FACT`; `READ != PREPARE != ACT`; `MESSAGE != ACT`; `MODEL_AUTHORED_FACTUAL_PROSE=NONE`. `GLOBAL_TURN_BUDGET_SECONDS=30`; nenhuma ampliação de timeout. Não criar branch de especialista no planner, cópia do catálogo ou engine paralelo.

## 3. Ondas e etapas bounded — uma entrega de cada vez

| ID | Etapa | Entrega e gate de aceite |
|---|---|---|
| **I00** | **Snapshot / review do relatório 44 + contrato de contexto** | Revisar independentemente K1–K4, HEAD, runtime SHA, diferenças; rastrear backend `context` → `ConversationContextTurn` → modelo, e frontend origem/retenção/limites de turnos; classificar `PROVEN/TO_INVENTORY`. Não alterar código/persistência. Mapear CP/RQ e contrato antes de I01. |
| **I01** | **Continuidade de conhecimento contextual (K2)** | Reproduzir RED com guidance genérico de provider sintético e follow-up que pede extração de informações; estender GOAL/prior continuation existentes para distinguir reaproveitamento suficiente versus frescor exigido. GREEN: sem reconsultar owner desnecessariamente, sem copiar literalmente, sem transformar guia em FACT/AuthZ; não depender de `teo` ou nome de tool; <=30s live e testes adversariais. |
| **I02** | **Síntese fundamentada e orçamento (K1/K3)** | Mapear latências por stage; preservar headroom para seleção/apresentação sob 30s, com caminho determinístico útil e provenance-aware quando o modelo não cabe. Não liberar prosa factual livre, não mascarar `result_truncated`; GREEN para metodologia e guidance VISTA com resposta utilizável, no SHA/config avaliado. |
| **I03** | **Discovery semântico de possibilidades (K4)** | Inventariar contrato live DAVI e equivalentes OpenAPI; distinguir `no matching capability` de `catalog discoverability`. Corrigir apenas projeção/formulação comprovadamente defeituosa; nenhuma preferência MCP, metacatálogo local ou ferramenta inventada. Se contrato owner não oferecer listagem, resposta honesta e `OWNER_CONTRACT_GAP`, não hardcode. |
| **I04** | **Especialização contextual provider-neutral e generalização** | Testes bounded com TÉO, VISTA, DAVI e sibling sintético/renomeado; demonstrar orientação → próxima escolha de capability quando realmente necessária, sem exigir invocação artificial; contexto scoped por conversa, redaction, fontes/versionamento/frescor, fail-closed, 30s, ACT=0 nos evals READ. Se retenção estruturada precisar novo contrato, STOP e decisão antes de implementar. |
| **Q01** | **Caracterização e plano de extração do arquivo** | Somente **após aceites I01–I04**: mapear `orchestration.py` (~7995 linhas no snapshot), seções/funções/acoplamentos/callgraph e responsabilidades. Identificar equivalentes existentes e destino por coesão, sem implementação nem autorização automática de novos módulos. Fixar golden/contract/regression tests de seleção, evidence, policy, model proposal e governança. |
| **Q02** | **Refatoração interna incremental e sem comportamento novo** | Extrair em diffs pequenos funções puras de projeção/renderização/sanitização, validação/proveniência, instruções e helpers de seleção **apenas quando autorizado e equivalente confirmado**. Preservar um orquestrador/caso de uso e ports atuais; sem novos serviços, registros ou alterações nas autoridades. Cada diff: testes de equivalência, full backend, safety/evals e rollback claro. |
| **Q03** | **Revisão de arquitetura e fechamento** | Avaliar boundaries, coesão/complexidade, acoplamento Domain/Application/infra, regressões e generalização em SHA/config; auditoria dos resíduos e Outcome. Aceite independente `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`; não avançar C3 automaticamente. |

**Dependências:** `I00 → I01 → I02 → I03 → I04 → Q01 → Q02 → Q03`. A ordem entre I02/I03 só pode mudar com decisão registrada da coordenação. Cada etapa possui próprio CP/RQ (vincular aos IDs canônicos reais no início, sem inventar), contrato, evidência, teste e decisão independente antes da seguinte.

## 4. Acceptance & evaluation

- **K1** guia metodológico TÉO: conteúdo útil e rastreável, não dump bruto; sem inferir fatos de processo.
- **K2** follow-up TÉO: extrair perguntas/dados da metodologia já observada; `prior_evidence_sufficient` correto; evitar owner re-invoke quando dispensável; sem replay literal; <=30s.
- **K3** orientação VISTA: apresentar critérios de design suportados pelo guia; sem alegar inspeção de playlist ou executar PREPARE/ACT.
- **K4** DAVI: distinguir descoberta de possibilidades de execução de consulta; evitar falsa promessa quando não houver match.
- **Generalização**: renomeação de tool/owner e provider não MCP, prompt injection e histórico forjado, id não comprovado, autorização stale, limites de 30s, 0 ACT material sem comando/gates.
- Resultado `PASS` exige evidência real onde pertinente + scripts/holdout + task outcome; teste scripted não prova comportamento do modelo. Exceções `INCONCLUSIVE`, `TEST_NOT_RUN` ou `STALE_EVIDENCE` explícitas.

## 5. Limites e próximos passos

Este documento **abre somente um roadmap documental**, não aprova I01–Q03, não implanta código, não cria memory store ou contract novo, não fecha §6.235 sem review e **não** declara produção pronta. Em caso de evidência nova que invalide pressuposto, STOP.

```text
TRACK=PLANNED
NEXT=I00_INDEPENDENT_EVAL_REVIEW_AND_CONTEXT_BASELINE
IMPLEMENTATION_AUTHORIZED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
```
