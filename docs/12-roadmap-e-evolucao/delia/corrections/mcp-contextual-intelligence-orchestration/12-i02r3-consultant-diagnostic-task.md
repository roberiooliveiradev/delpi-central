# 12 — I02-R3 · Briefing de execução do consultor: evidências, dependências e testes

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-MCP-I02-R3-TEO-PREOWNER-LATENCY-DIAGNOSTIC-01`  
**HEAD DE REFERÊNCIA:** `06cf0f22dab4ad4e294f882b3844027f170d1e28`  
**STATUS:** `CONSULTANCY_TASK_DEFINED / NOT_EXECUTED`  
**MODE:** `REANCHOR → EVIDENCE INVENTORY → CAUSAL TRACE → DEPENDENCY MAP → CHARACTERIZATION TESTS → CONTROLLED COMPARISON → RECOMMENDATION → DOCS/LEDGER → COMMIT/PUSH/VERIFY → HANDOFF`

## 1. Papel e objetivo
Atuar como **consultor executor técnico**, não como autoridade de produto ou arquitetura. Investigar por que K1 TÉO às vezes estoura o orçamento global de 30s antes do READ, apesar de owner DISCOVERY/READ rápidos no caminho de sucesso. Comprovar qual estágio timeout no caso R2, mapear dependências entre as propostas sequenciais, medir custo e riscos das alternativas A/B/C/D/E/F do [doc 11](./11-i02r3-coordination-latency-architecture-investigation.md). **Não implementar otimização funcional nem fazer deploy nesta task.**

## 2. Reancoragem e gates
Executar `git status`, `git rev-parse HEAD`, `git fetch origin`, `git rev-parse origin/main`; preservar trabalho concorrente. Ler Project Instructions e `.cursor` e hierarquia canônica **16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → spec temática → ledger** pelos paths efetivos. Relacionar CP/RQ existentes, owner/consumers/contract, não inferir de texto deste prompt. Ler roadmap, docs 07–11 e ledger §§6.245–6.249. Caso drift conflitante: `STOP→EXECUTION_DRIFT|ARCHITECTURE_DECISION_REQUIRED`.

Conservar `C3_EXECUTED=NO`, `C4_AUTHORIZED=NO`, `C5_AUTHORIZED=NO`, `I02_ACCEPTED=NO`. `EXISTING_EQUIVALENT=YES` (observado no HEAD de referência); revalidar e justificar `REUSE_DECISION=REUSE|EXTEND_CANDIDATE` por boundary. Sem planner novo, memória/catálogo global, import do Chat, migração ou mudança de contrato.

## 3. Evidência e hipótese — não misturar
Relatório 07: K1 TÉO em sucesso ~17.816ms: group 4088, capability 2803, goal 3146, native 1775, owner catalog 79, arguments ~5531 inferidos, READ 39. Relatório 09: K1 em falha `model_timeout` ~30.014ms; etapa exata do timeout **não demonstrada pelo relato agregado**. K3 R2 VISTA corrigiu index_probe mas topic parcialmente relevante. Esses resultados são **executor-reported**. Não promover inferência a causa `PROVEN`.

## 4. Gate A — reconstrução de traces no SHA/config
Inventariar fontes autorizadas de logs por correlation ID, SHA implantado, model/provider, config fingerprint e limites; usar telemetry já existente de `model_propose purpose/timing_ms`. Recuperar um K1 sucesso histórico, um K1 FAIL histórico e K3 de controle, se os dados estiverem disponíveis; usar correlações dos relatórios e marcar ausência de acesso `TO_INVENTORY`. **Não reproduzir dados empresariais, tokens, prompts ou payloads sensíveis.**

Para cada estágio real: `correlation_id, purpose, start/end ou offset, duration_ms, remaining_before/after_ms, timeout_cap_ms, result/error, model_call_count, owner_call_count, owner_read_reached`. Diferenciar:
- timeout do modelo versus deadline compartilhado;
- seleção e avaliação semântica versus owner DISCOVERY/READ;
- duração medida versus diferença entre logs (inferida);
- timeout isolado, variância de modelo/provider e necessidade da etapa.

Apontar exatamente qual proposta falhou em K1 R2, ou `INCONCLUSIVE` se os traces forem insuficientes. Não dizer que o TÉO é lento sem medição.

## 5. Gate B — mapa contratual das dependências
Inspecionar no HEAD `orchestration.py`, `turn_budget.py`, contrato `ModelInvocationRequest` e testes pertinentes. Construir matriz de `_select_group`, `_select_capability`, `_understand_goal`, `_assess_native_path`, `_build_arguments`, owner DISCOVERY, owner READ e síntese.

Para cada: entradas reais, resultados utilizados, pré-condições, custo, papel na segurança, dependência do estágio anterior, possibilidade de reuso determinístico, motivo por que **não** pode ser omitido, testes negativos. Atenção especial:
- GOAL e seleção de capability podem compartilhar inferência, mas o **gate de intenção de escrita** deve continuar independente e determinístico;
- `_assess_native_path` só vê superfície do grupo alvo antes da decisão de foreign evidence; preservar `foreign_evidence_required`, corroboração solicitada e isolamento;
- `_build_arguments` já devolve `{}` em schemas sem campos não orquestrados; campos livres/id precisam de fonte e validação;
- `TurnDeadline` único, nenhuma chamada após expiração;
- owner index/provenance/AuthZ nunca inferidos de resultado do modelo.

## 6. Gate C — testes e experimentos controlados
**Obrigatórios, se ambiente e fixtures permitirem**, com `TEST_NOT_RUN` quando não for possível:
1. Caracterização do caminho atual de K1 com fake model/owner e fake clock; confirmar ordem, número de chamadas, argumentos e deadline.
2. K1 sucesso rápido e cenário com timeout em cada estágio de modelo individualmente; registrar comportamento fail-closed, ACT=0.
3. K2 continuação após K1 suficiente, após K1 falho e com histórico forjado/truncado (epistemics preservadas).
4. K3 índice→seleção→READ + guia aninhado: nenhum regressão do fix R2.
5. READ simples, owner DISCOVERY obrigatório, provider renomeado/não MCP, schema vazio, identificador requerido/inventado, multi-owner foreign_required, comparação explícita, write-class selecionada por engano e pedido PREPARE/ACT.
6. Prompt injection no catálogo, outcome e histórico; `MCP_METADATA!=AUTHORITY`, `MESSAGE!=ACT`, `MODEL_OUTPUT!=FACT`.

Executar as suites relevantes e, se suportado pelo ambiente, a suite backend completa; capturar comandos, totais, tempo e SHA. Instrumentação adicional pode existir só em testes/diagnóstico, sem alterar a semântica de produção. Experimentos comparativos alternativos podem usar harness isolado, sem merge de código funcional.

**Live READ-only opcional e condicionado à autorização e à config:** no máximo um K1 e K2 na mesma conversa, um K3 controle; sem retries automáticos para obter PASS. Não interferir no deploy existente; verificar versão e limites antes. Se não autorizado, `TEST_NOT_RUN`.

## 7. Gate D — comparação arquitetural
Avaliar separadamente:
- A: aproveitar telemetria/custo por `purpose` (REUSE);
- B: eliminar somente repetição real comprovada, não “duas chamadas” por si;
- C: consolidar `goal` e seleção tipada quando semântica, output schema e write gate permitirem;
- D: omitir `native_assessment` somente com prova formal de elegibilidade sem perder foreign_required/corroboration;
- E: ampliar proposta determinística de argumentos apenas para dados schema/owner comprovados;
- F: reduzir tokens/config de modelo mantendo acurácia, timeouts e budget.

Para cada alternativa, registrar `EXISTING_MECHANISM, CONTRACT, COST_BASELINE, ESTIMATED_OR_TESTED_GAIN, ACCURACY/GENERALIZATION, SAFETY, FAILURE_MODE, RESIDUAL, REUSE_DECISION`. Não confundir ganho estimado com performance testada. **Não** paralelizar estágios dependentes nem criar novo planner/cache.

Comparação deve conter correctness por cenário, número de LLM calls, wall-clock, budget total<=30s, índice/tópico/provedor escolhidos, false write, qualidade real do resultado; p50/p95 **somente** com amostragem suficiente, nunca inferidos de 1–3 runs.

## 8. Saídas e Git
Criar relatório **13-i02r3-consultant-evidence-and-dependency-analysis.md** na mesma pasta, com traces saneados, mapa, matriz de casos com status, alternativas avaliadas, CP/RQ, SHA/config, provas, lacunas e recomendação explícita de **um próximo diff candidato** ou `INCONCLUSIVE`.

Registrar se a falha é de seleção, goal, native, arguments, modelo/provider, contrato ou infraestrutura; não inventar root cause quando não houver evidência. Testes somente de caracterização podem ser commitados separadamente, com diff mínimo. **Código funcional e deploy são proibidos.** Atualizar README e ledger após a evidência real, commit/push na main mediante regras canônicas, sem force push, conferir HEAD remoto.

## 9. Relatório final obrigatório

```text
TASK_ID=DELIA-C3-MCP-I02-R3-TEO-PREOWNER-LATENCY-DIAGNOSTIC-01
BASE_HEAD=
FINAL_HEAD=
PUSH_VERIFIED=
CANONICAL_AUTHORITIES_REVALIDATED=
CP_RQ=
EXISTING_EQUIVALENT=
REUSE_DECISION=
EVALUATED_SHA=
DEPLOYED_SHA=
MODEL_CONFIG_FINGERPRINT=
K1_SUCCESS_CORRELATION=
K1_FAIL_CORRELATION=
K1_TIMEOUT_EXACT_STAGE=
K1_PREOWNER_MODEL_CALL_COUNT=
K1_PREOWNER_OWNER_CALL_COUNT=
K1_STAGES_DURATIONS_EVIDENCE=
K2_CONTINUITY_STATUS=
K3_REGRESSION_STATUS=
STAGE_DEPENDENCY_MAP=
ALTERNATIVES_COMPARED=
SAFE_OPTIMIZATION_PROVEN=
CHARACTERIZATION_TESTS=
FULL_BACKEND_TESTS=
SECURITY_EVAL=
LIVE_EVAL=
GLOBAL_TURN_BUDGET_SECONDS=30
UNAUTHORIZED_MATERIAL_ACT_COUNT=0
SOURCE_CODE_CHANGED=NO
PERFORMANCE_FIX_IMPLEMENTED=NO
DEPLOY_PERFORMED=NO
DOCUMENTATION_UPDATED=
LEDGER_UPDATED=
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
RESIDUALS=
RECOMMENDATION_FOR_COORDINATION=
NEXT=I02_R3_COORDINATION_ARCHITECTURE_DECISION
```

**Princípio:** consultor coleta evidência e compara opções; a coordenação escolhe a correção; Cursor executor de implementação só recebe prompt fechado depois do gate de decisão. Não fazer auto-aceite.
