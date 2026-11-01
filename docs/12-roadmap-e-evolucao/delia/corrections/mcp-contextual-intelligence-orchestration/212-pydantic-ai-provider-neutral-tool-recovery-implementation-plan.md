# 212 — Plano de execução: Pydantic AI substituível, recuperação tipada e continuidade agnóstica

- **Estado:** PLANNED / IMPLEMENTATION_NOT_RUN. Plano técnico condicionado à reancoragem no HEAD e à prova dos contratos; não constitui aceite de arquitetura nem evidência de runtime.
- **Origem:** Tasks 23, 29–34; doc 210 §20; doc 211; ledger.
- **Baseline de planejamento verificada:** `25a5de36b966eb116b6e27733d0aa9ad6a6a99b8` (2026-11-01).
- **Owner:** DÉLIA — orchestration/application; MCP adapters — infrastructure; schemas/errors e facts — MCP/Domain APIs; Core — AuthZ; Keycloak — identidade.
- **Meta:** consertar a fronteira genérica geração → validação → recuperação de argumentos MCP, preservando LangGraph B1 como runtime e substituibilidade entre backends/LLMs/mecanismos internos.

## 0. Reancoragem e proteção das decisões

Antes de implementar, executar `git status`/HEAD/origin, Project Instructions/AGENTS/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → spec temática → ledger. Identificar fase, CP/RQ, ownership, congelamentos, contratos, deploy e testes. Se houver conflito entre este plano e authority superior, STOP para a parte conflitante e registrar `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`; não reescrever o contrato por conveniência.

## 1. Evidência e hipótese testável

- Task 34 reportou 15 `CapabilityProviderError` por argumentos rejeitados em cinco owners: CLARA 6, CAIO 4, EVA 2, TÉO 2, DAVI 1. Exemplos incluem `topic`, `analysis_type`, `entity`, `view` com enums/discriminadores ausentes ou campos obrigatórios não atendidos. A seleção de ferramenta por vezes foi correta, mas o avaliador atribuiu falsamente `GROUP_SELECTION_ERROR`.
- Score histórico doc 211: 10/28 segundo heurística inadequada; VISTA 4/4 pode ser clarificação genérica sem Outcome. **Não** inferir que 15/28 podem ser resolvidos automaticamente nem que toda falha seja exclusivamente arggen.
- Primeiro inspecionar `_propose_candidate_arguments`, `_EMPTY_RESULT_FEEDBACK`, schema validation, `CapabilityProviderError`, invoke e recovery T23. Classificar feedback tipado do owner vs. erro de transporte, autenticação, authorization, dados ausentes e falha técnica.
- Artefatos brutos de Task 33/34 ficam locais, não no GitHub; preservar link interno autorizado e texto literal na revisão humana.

## 2. Inventário e comparação antes de instalar

Para cada boundary identificar `RESPONSIBILITY`, `OWNER`, `CANONICAL_SOURCE`, `CONSUMERS`, `CONTRACT`, `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`.

Inventariar versões e uso real de Pydantic (já existente), LangGraph B1, MCP SDK/adapter, Pydantic AI (não presumir instalado), recovery T23, interfaces Ports & Adapters, schemas anunciados, uso de modelos locais e métricas. Verificar licenças/compatibilidade Python, tipagem, dependências transitivas, potencial segundo agent loop, modelos suportados, overload da API local Ollama e problemas de tracing.

Comparar três abordagens com os mesmos 15 incidentes e casos novos:
- A: estender recovery T23 com validação JSON Schema/Pydantic e feedback genérico;
- B: usar Pydantic AI **encapsulado exclusivamente na fronteira tipada**, sem trocar LangGraph, planner, MCP owner authority, AuthZ nem aplicar writes;
- C: utilizar Pydantic AI apenas como referência de padrões caso B implique segunda orquestração ou acoplamento excessivo.
Registrar taxa de argumentos válidos, reparos, Outcome, segurança, custo de tokens, latência, retry loops, compatibilidade do LLM. A decisão de integração é `ADOPT`, `ADOPT_BOUNDED` ou `NOT_ADOPT` com evidência. A intenção de produto aprova adoção **se** passar os gates, não a obriga apesar de resultados negativos.

Referências oficiais a verificar no início: https://ai.pydantic.dev/tools-advanced/ ; https://ai.pydantic.dev/toolsets/ ; https://ai.pydantic.dev/mcp/ ; https://docs.langchain.com/oss/python/langgraph/persistence .

## 3. Arquitetura alvo — substituível

`LangGraph B1 (owner do estado/continuidade)` → `Application semantic capability request` → `Port existente de argument proposal/validation/recovery` → `Infrastructure adapter: existing/Pydantic AI bounded` → `existing governed MCP invocation` → `Evidence/Outcome`.

- Domínio e Application **não importam** `pydantic_ai`, Pydantic runtime specifics, Ollama SDK, MCP client concreto, transport, HTTP ou LangGraph framework; respeitar contrato atual e mínimos diffs.
- Se port real já existir, estendê-lo; se não houver, provar necessidade e aprovar `NEW` apenas na fronteira legítima. Não duplicar planner, engine, registry, modelo de Work ou pipeline de autorização.
- O adapter Pydantic AI pode usar modelos via adapter compatível/injeção, nunca escolher provider por branches de especialista. Suportar alternância de backend pela composição/configuração aprovada, fail-closed; integração opcional/feature flag local, rollback e fallback determinísticos; não disponibilizar chave de API ao modelo nem prompts.
- MCP `tools/list` é fonte dinâmica de capacidades/schema, não autoridade de aprovação; não copiar nome/enum de ferramenta em DÉLIA. Metadata não confiável, validar schemas e proteger contra prompt injection. Não promover `ModelRetry` para writes ou autorização.
- `LangGraph` mantém checkpoint/progresso/continuidade por mecanismos já previstos, sem duplicar agents ou persistir chain-of-thought.

## 4. Contrato de recuperação por categorias

1. Validar contra schema publicado antes do invoke: required, enum, types, ranges, additionalProperties, nested schemas, discriminated unions; se houver schema incompleto, reportar `SCHEMA_INSUFFICIENT`, não inventar enum.
2. Rejeição estruturada de argumento pelo owner: identificar erro recuperável **por contrato documentado**, preservar `tool_id`, owner, identidade delegada, classe READ/ANALYSIS, política e request id; converter em feedback seguro tipado com enum/required, sem dados privados, sem permitir modificar tools/permissions.
3. Repropor argumentos semanticamente uma vez por tentativa bounded; validar novamente schema; invocar quando válido; verificar payload e postcondition do owner.
4. Se o erro indicar semântica fora da ferramenta, reavaliar capability apenas pelo planner já existente e gates normais, nunca trocar capabilities pelo validador; não inventar correspondências de enum por fuzzy coercion silenciosa.
5. Fail-closed: 401/403, authz, unknown tool, ACT/PREPARE, policy deny, injection, stale schema, network/transient error não são `enum retry`; circuit breaker, timeout e budget têm owners próprios. Não reexecutar writes automaticamente. Distinguir idempotência.
6. Limites: budget **global por investigação** de model calls/tool invokes/retries/tokens/deadline além do eventual retry **por tool** de Pydantic AI; sem loop não delimitado e sem contagem resetada contornando budget global. Defaults locais conservadores e parametrizados, baseados em medição.
7. Observabilidade: tipo do erro, stage, schema provenance/version, proposta original, feedback sanitizado, nova proposta, validação, attempts, owner result, custo, latency, Outcome; dados protegidos localmente.

## 5. Slices de implementação autônoma

**S0 — Gate documental e baseline.** Reancorar; caracterizar todos os incidentes Task 34; garantir corpus congelado e novos held-outs; registrar baseline literal.

**S1 — RED & segurança.** Testes parametrizados de enum errado, required ausente, campo extra, nested mismatch, owner error recuperável e erro não recuperável; test cases originais e inéditos; 401/403, ACT, malicious schema/metadata, authorization downgrade, cap spoofing, repeated errors, infinite retry, timeout, timeout cancellation, idempotency. RED no fluxo real.

**S2 — Benchmark A/B isolado.** Prototipar Pydantic AI em adapter/fixture sem mudar o planner nem domínio; fixar mesma LLM/config/corpus/temperatura quando suportado; registrar `ADOPT`/ `ADOPT_BOUNDED`/`NOT_ADOPT` com rationale e testes. Se B não compatível, concluir C sem forçar a dependência.

**S3 — Implementação mínima.** Estender recovery T23, schema validation e error handling tipado; opcionalmente usar Pydantic AI por composition behind existing port; manter LangGraph B1 e owner endpoints atuais; feature flag local, fallback e rollback; nenhum branch por CAIO/CLARA/EVA/TÉO/DAVI.

**S4 — Continuidade.** Conferir como o LangGraph B1 retoma e checkpointa decisões, elimina repetição, usa Evidence e coordena subobjetivos em cenários multi-MCP; extender **somente** lacuna provada; não criar nova memory authority nem segunda engine.

**S5 — Verificação funcional.** Unit + contract + integration contra MCP sandbox e os 7 owners autorizados no local; 15 casos causais, casos negativos, teste de troca de backend/modelo sem mudança Domain/Application; regression interop e full backend; avaliar artefatos de execução completos.

**S6 — Avaliação empresarial.** Executar doc 211 28×3 com mesmo SHA/config/oráculo e held-out independente; manter um snapshot pre-fix e pós-fix, respostas reais integrais `QUESTION_FULL_TEXT`+`RESPONSE_FULL_TEXT` e `NO_FINAL_RESPONSE` quando aplicável, trace, arguments, evidence, first divergence, rubrica por subobjetivo, percentuais por owner, business Outcome, tokens/latency/custo e possíveis regressões. Não reescrever respostas e não guardar chain-of-thought. 80% por especialista e global é meta/gate final, sem maquiar PASS; ausências ficam FAIL/INCONCLUSIVE.

**S7 — Documentar, commit, push.** Atualizar doc 210, doc 211 (sem alterar perguntas congeladas), este doc 212, ledger e runbook(s) de owner quando aplicável. Commit por slice, stage paths explícitos, conferir `git diff --cached`; preservar workstreams concorrentes. Push `main` somente alterações legítimas e conferir HEAD. Não fazer deploy produção.

## 6. Gates de aceite e correção sem retornos rotineiros

- `ARCHITECTURE_GATE`: nenhum port indevido, imports de infra no Domain/Application, segunda engine, Catálogo MCP paralelo, privilégio inferido ou acoplamento por specialist.
- `RECOVERY_GATE`: rejeição de enum e required recuperável com evidência, sem troca não autorizada de tool e com bounded retries; erros não recuperáveis permanecem fail-closed.
- `MODEL_TOOL_AGNOSTIC_GATE`: trocar LLM e backend do recovery por configuração/composição validada, sem alteração em Domain/Application. Sem obrigação de garantir resultado idêntico de modelos diferentes.
- `LANGGRAPH_GATE`: preservar B1 e demonstrar continuidade real em 2+ etapas sem perder subobjetivo.
- `SAFETY_GATE`: zero writes/ACT não autorizados, zero authz bypass, zero metadata authority, zero segredos/logs comuns.
- `EVAL_GATE`: 84 execuções doc211 quando final; respostas reais disponíveis por canal protegido; rubrica individual e held-out; baseline comparável; business Outcome ≥80% por especialista e global, sem simplesmente relabel.
- `EVIDENCE_GATE`: testes reais rastreados ao SHA/config, sem chamar de PASS só porque HTTP200.
- `DEPLOY_GATE`: produção intacta.

Executor resolve autonomamente questões dentro de owners/contratos existentes, iterando RED→fix mínimo→GREEN→regressão; não solicita decisões rotineiras. STOP apenas por boundary de segurança, segredo/credencial indisponível, isolamento não provado, conflito de authority, nova dependency/owner que exija decisão, ou regressão de segurança sem reparo legítimo. Nesses casos documentar `INCONCLUSIVE` ou `ARCHITECTURE_DECISION_REQUIRED` e avançar nos slices independentes. Nunca mascarar `FAIL`.

## 7. Artefatos de entrega

- `implementation-decision.md`: matriz A/B/C, evidence, dependências e motivo da decisão.
- `contract-and-coupling-matrix.md`: owner, source, consumers, ports, diff.
- `test-evidence.md`: RED/GREEN/suites/negative/heldout e comparação pre/pós.
- `response-review-package`: manifests e **respostas reais integrais** das 84 execuções em armazenamento de acesso autorizado; GitHub somente sanitizado quando permitido.
- Report final: BASE/FINAL SHA, alteração local/prod, `EXISTING_EQUIVALENT`, `REUSE_DECISION`, biblioteca/version pin, adapter/fallback/rollback, budget global e per-tool, 15 incidentes, modelos, 7 owners, 28×3, exemplos reais, métricas, gates, gaps, links verificados, próximo bounded step.

## 8. Não objetivos

Não migrar runtime inteiro para Pydantic AI; não instalar LlamaIndex/Microsoft Agent Framework/Deep Agents por antecipação; não aplicar ACT produtivo; não alterar identidade/políticas de Core; não aceitar biblioteca não testada só por marketing; não usar o score binário `want_owner` como resultado de negócio.
