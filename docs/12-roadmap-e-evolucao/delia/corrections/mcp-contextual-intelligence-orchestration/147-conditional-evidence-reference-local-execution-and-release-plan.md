# 147 — Decisão de arquitetura e plano executivo: referência condicional de evidência, avaliação local e release R7

**TASK_ID:** `DELIA-R7-CONDITIONAL-EVIDENCE-REFERENCE-LOCAL-IMPLEMENTATION-RELEASE-01`  
**DATA DA DECISÃO PO:** 2026-10-25  
**ESTADO:** `APPROVED_DIRECTION / IMPLEMENTATION_GATED / DEPLOY_CONDITIONALLY_AUTHORIZED_BY_PO`. A autorização do PO abaixo **não substitui** review independente nem gates operacionais de SHA/imagem/rollback.  
**FONTES:** autoridades 16→50→17→49→51→52→21→20→25, ADR58, plano 125, gates 129, runbook 130, spec 146, reviews `982e37cf` e `cc583c8f`, relatório A/B `4ee47ea5fc`, evidência R7 e ledger. Reancorar no HEAD antes da execução.

## 1. Decisão explícita do Product Owner

1. **LLM decide significado, referência e pertinência semântica.** Backend não escolhe sinônimo, nomenclatura técnica, produto ou interpretação; não criar regra `terminal bala → TERM. BALA`.
2. **Backend aceita e valida parâmetros já declarados pelos MCPs / Domain APIs** via contracts/schema/operation class/candidate token; não impõe catálogo semântico paralelo nem inventa parâmetros adicionais. Schema declarado **não** substitui AuthZ e Domain authority.
3. Para valor **exato de evidência que o LLM decidiu usar** em parâmetro READ, **usar seleção por referência validável**, não regeneração livre. Esta obrigação é **condicional à declaração semântica** de uso de valor exato e sua elegibilidade; não tornar `selections` obrigatório em toda interação nem extrapolar para WRITE/ACT.
4. Preservar `apply_evidence_bound_selections`, `_build_arguments`, projeção/lineage e validação existentes, por `EXTEND` se contrato e owner forem comprovados. Não criar engine, planner, registry, matcher semântico, snapping fuzzy ou novo provider.
5. **Não executar novos testes/benchmarks com modelos LLM externos** nesta task, nem comparar modelos externos. Avaliar com **modelo local efetivamente disponível e permitido**, identificado por id, imagem/config/SHA; testes determinísticos sem LLM externo são permitidos. Não assumir que modelo externo mais poderoso garantirá resultado; qualquer afirmação sobre ele fica `NOT_TESTED`.
6. PO autoriza **objetivo de deploy em produção somente após validação local comprovada**, testes/regressões e release gates; autoriza solicitar/realizar o deploy dentro da governança, sem liberar bypass de review independente, confirmação operacional do serviço/SHA, AuthZ, rollback ou higiene de secrets.
7. Corrigir de maneira bounded até passar critérios aprovados. **Sem loop infinito:** uma hipótese causal por diff; RED→GREEN→regressão→local eval; segunda falha material do mesmo pacote causa STOP/review, não tuning contínuo.

## 2. Diagnóstico demonstrado / ainda a demonstrar

**PROVEN pelo relatório do executor, sujeito a revisão:** v16 e v17 O2 `1/10` cada; ao propor `selections`, o binding literal materializou `2/2` válidas; adoção baixa `~3/9`; A/B remoto não melhorou O2 e `gpt-4o-mini` marcou BALANCA como pertinente. **Não** declarar que toda opção do mercado falha ou que há garantia com outro modelo. Separar: `LLM decision → proposal contract → argument materialization → owner read → relevance → outcome`. O efeito de alteração contratual e execução local é **TARGET**, não PROVEN.

## 3. Contrato-alvo, antes do diff

Responsabilidade existente `LLM→arguments` deve oferecer caminho expressivo para duas formas de argumentos:
- **Valor originado do usuário ou contexto permitido, sem dependência documental:** seguir os parâmetros existentes do owner, sujeitos ao schema e gates; nenhuma referência documental compulsória.
- **Valor exato extraído da evidência e declarado como base do argumento pelo LLM:** a proposta carrega `argument` + referência bounded ao bloco/trecho observado + valor literal selecionado; backend resolve só a integridade `source_ref`, presença literal, identidade/turno, schema/campo, enum, limites e policy. Não aceitar texto livre **como equivalente à declaração de referência**; se inválida/ausente, `missing_inputs/insufficient/clarify` pela fronteira existente. A seleção é semântica, não feita pelo código.

Antes de impor esse fluxo, provar **como o LLM declara origem documental** no contrato de proposta atual; se não houver representação verificável sem criar autoridade nova, STOP → `ARCHITECTURE_DECISION_REQUIRED` com ADR e alternativa mínima. Não detectar “origem documental” por string regex, nome do provider, prompt heuristic ou presença de `foreign_evidence` isoladamente. A existência de evidência não significa que ela necessariamente deve ser usada.

**As fronteiras de invocation e gates continuam:** identity → Core live AuthZ → capability → Policy/Decision → owner validation → audit/Outcome; candidate token, PREPARE/ACT e read/write preserved. Docs/MCP results UNTRUSTED; guidance não vira business fact. O contrato do owner determina params; schema validar não autoriza executar.

## 4. Testes de execução local (não usar modelo externo)

**Preparação:** inventariar infraestrutura local/Ollama e modelo disponível; registrar `LOCAL_MODEL_ID`, quantization/config, endpoint, versão de instrução, deployment SHA, imagem e timeout. Sem instalar/trocar modelo automaticamente, sem credenciais externas.

**Caracterização:** capturar proposta sanitizada do estágio `arguments`, refs e spans de evidência, argumento materializado e `search_products` final por correlation ID. Distinguir `SELECTION_NOT_EMITTED`, `INVALID_SELECTION`, `VALID_SELECTION_APPLIED`, `OWNER_RESULT_IRRELEVANT`, `JUDGE_FALSE_POSITIVE`, `TRANSPORT_ERROR`.

**RED/GREEN obrigatórios:** condicionamento de seleção documental exata, preservação de pontuação e enum, ausência de evidência, múltiplos candidatos, seleção específica demais, conflito entre evidências, refs forjadas/stale/outro usuário, injeção de metadados MCP, schema/arguments owner, candidate token, negativa AuthZ, write-ineligible/PREPARE/ACT. Relevance deve distinguir **registro empresarial correspondente** de registro falso-positivo (BALANCA), sem hardcode de O2; preferir pré-condições/projeção e Outcome autoritativos já existentes.

**Matriz local frozen:** O2 terminal bala (repetições delimitadas aprovadas); terminal pino; outro assunto MP; PI; D1 MP/PI/PA; TÉO SIPOC; VISTA; business READ direto; ausência/ambiguidade; schema negativo; prompt injection; write-negative. Medir `argument fidelity`, `business outcome`, `false positive`, `latency`, `actual token use` se telemetry disponível. Não excluir falhas da amostra. Critério provisório 70% **não é SLA automático**, precisa decisão explícita na revisão. Nenhum material WRITE produtivo.

**Regression:** focused + full backend, arch/import DAG, AuthZ/security, generalization/metamorphic, CRI ON/OFF local, MCP/Domain API contracts, no new provider branch. Classificar 2 falhas ambientais anteriores corretamente e obter CI owner exception ou reexecução configurada; histórico não pode virar PASS silenciosamente.

## 5. Execução por fases / stop gates

A. REANCHOR + inventário: `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`, owner/consumer/contract.  
B. Characterization payload e contract-first. Se requer novo mecanismo/owner, STOP → decisão, **não redesenhar silenciosamente**.  
C. RED tests → minimal bounded implementation já permitida pela autoridade → GREEN.  
D. Local real-model eval + matriz segurança/generalização + regressão completa. Sem cloud/external LLM.  
E. Documentar SHA/model/config, outcomes e métricas; commit/push main ff-only; **revisão independente**.  
F. **Deploy condicional:** somente após review favorável, requisitos de confiabilidade/segurança aceitos e autorização operacional específica no ambiente, com serviço/SHA/digest/rollback registrado; rollout scoped `api-delpi` somente se realmente requerido e aprovado separadamente, `delia-api` quando necessário.  
G. Smoke READ e outcomes reais em produção pós-deploy; se falhar, contenção/rollback e novo gate para qualquer fix; nunca tuning iterativo em produção.  
H. Revisão final R7: não autoencerrar enquanto C1, CRI OFF live, D1/TÉO/VISTA ou O2 residuais forem bloqueantes.

## 6. Critérios de aceite

- LLM continua owner da seleção semântica; backend valida integridade e params **declarados** no MCP/API, sem inferir nomenclatura.
- `selected_value` legítimo e sem ambiguidade chega literalmante ao inputSchema do owner; nenhuma seleção inválida aplicada.
- `selections` não é compulsória para pedidos sem uso de valor exato evidenciado; quando o modelo declara depender da evidência, a ausência de ref válida não vira texto livre disfarçado.
- Dados governados continuam orientação para READ, não são AUTHORITY empresarial; produtos são verificados na Domain API.
- O2 mostra dois códigos pertinentes/verdadeiros, com denominações e proveniência, confiabilidade aprovada em multirun local; nenhum false-positive relevante, nenhum ACT.
- Falhas e lacunas são rotuladas `FAIL/INCONCLUSIVE/TEST_NOT_RUN`, não `PASS`; `O2_LOCAL_PASS != PROD_PASS`.
- Release executado somente sob gated authorization; `R7_FINAL_ACCEPT` independente.

## 7. Report mínimo ao Devin/coordenação

```text
TASK_ID=DELIA-R7-CONDITIONAL-EVIDENCE-REFERENCE-LOCAL-IMPLEMENTATION-RELEASE-01
BASE_SHA=
FINAL_HEAD=
ORIGIN_MAIN=
PUSH_VERIFIED=
AUTHORITIES_READ=
PHASE_CP_RQ=
EXISTING_EQUIVALENT=
REUSE_DECISION=
SEMANTIC_ORIGIN_CONTRACT=
MCP_OWNER_PARAMS_REUSED=
CODE_DIFF=
RED_GREEN=
FULL_BACKEND=
ARCH_SECURITY_AUTHZ=
LOCAL_MODEL_ID_CONFIG=
EVALUATED_SHA=
O2_LOCAL_N_SUCCESS_FAIL=
ARGUMENT_FIDELITY=
FALSE_POSITIVES=
D1_TEO_VISTA=
CRI_ON_OFF=
REAL_TOKEN_USAGE=
INDEPENDENT_REVIEW=
CI_EXCEPTION_C1=
OPERATIONAL_AUTHORIZATION=
DAVI_DEPLOY_SHA_DIGEST=
DELIA_DEPLOY_SHA_DIGEST=
PROD_READ_SMOKE=
PROD_O2_OUTCOME=
ROLLBACK=
EXECUTION_DRIFT=
R7_FINAL_ACCEPT_READY=
FINAL_VERDICT=
```

**Nota:** Não interpretar a autorização condicional de deploy do PO como revisão independente nem autorização para alterar modelos/provedores externos. Respeitar o próximo gate de autoridade presente no HEAD.

## 8. Evidência de execução — 2026-10-25 (executor report)

**Implementado:** `evidence_arguments` (declaração de origem documental) + declaração implícita por item de `selections`; campo declarado aceita somente seleção literal verificada — texto livre é dropado e nunca substitui a referência; required desvinculado → `missing_inputs`/clarify; entradas orquestradas/inválidas ignoradas; fail-closed sem schema do owner. Owner: `argument_validation.py` (EXTEND); boundary: `_build_arguments`. Instrução arguments → **v18**. RED→GREEN: 6 testes pelo orquestrador real + conflito invertido conforme §3. Focused 104/104; backend 2294/2296 (2 env-failures pré-existentes preservadas como FAIL ambiental).

**Avaliação local (`delia-json` 3.1B, único modelo autorizado):** O2 0/10, pino 0/3, D1 0/3, TÉO 0/3, VISTA 0/3, READ direto 0/3 — gargalo em `interaction_admission`/`model_propose` (capacidade do modelo, anterior ao estágio do contrato); WRITE-ineligible 3/3 recusa (0 ACT); AuthZ 401; `FALSE_POSITIVES=0`; `SELECTION_ADOPTION=0` (estágio não alcançado sob evidência documental).

**Estado:** contrato implementado e provado deterministicamente; confiabilidade E2E sob o modelo local **não atingida** → `DEPLOY=BLOCKED`, `INDEPENDENT_REVIEW=PENDING`, `R7_FINAL_ACCEPT=NO`. Detalhes no relatório R7 e ledger.
