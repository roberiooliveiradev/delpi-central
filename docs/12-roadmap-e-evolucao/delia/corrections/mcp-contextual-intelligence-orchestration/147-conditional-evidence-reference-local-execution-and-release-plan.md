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


## Revisão independente da implementação v18 — 2026-10-25

**REVIEW_VERDICT=REWORK**; **IMPLEMENTED_SHA=881b05200e78069fc7e6a696823261d452675c71**; **PRODUCTION_DEPLOY_AUTHORIZED=NO**; **R7_FINAL_ACCEPT=NO**. Inspecionado no GitHub commit e caminhos `argument_validation.py`, `orchestration._build_arguments`, instrução v18 e testes de `test_goal_evidence_relevance.py`. Esta revisão **não** reexecutou localmente suíte, Docker, Ollama ou produção; resultados de teste e de execução são `EXECUTOR_REPORTED`.

### Achado bloqueante F1 — campo documental opcional descartado e READ amplo executado

`apply_evidence_bound_selections` remove os valores de `arguments` para todo campo declarado como documental, mas retorna em `unbound_required` **somente** os nomes presentes em `schema.required`. Quando uma seleção é forjada, ausente, inválida ou bare string, um campo documental **opcional** permanece sem binding e `_build_arguments` valida e invoca com argumentos restantes/{}; o guard `if missing and not validated` não bloqueia essa invocação. Os testes novos `test_declared_evidence_argument_without_selection_drops_free_text`, `test_declared_evidence_argument_invalid_selection_stays_unbound` e `test_bare_string_selection_declares_field` comprovam explicitamente `pa.calls[1] == ("search_items", {})`. Isso **não** é fail-closed para a intenção semântica original: uma consulta potencialmente ampla e irrelevante pode ser executada, causando resultado enganoso, aumento de exposição/latência e perda do filtro. O owner schema pode legitimamente tornar `query/description` opcional; não modificá-lo para mascarar o defeito.

**Remediação exigida:** distinguir `declared_unbound` de `schema_required_missing`, preservar proveniência e bloquear ou solicitar clarificação para a **operação que dependia daquele valor documental** mesmo com campo opcional; não construir fallback vazio, não inventar valor nem proibir consultas vazias legitimamente solicitadas **sem** dependência documental. Exigir testes RED/GREEN no caminho real: declarado opcional inválido → **zero segunda invocação**; não declarado com args vazios legitimamente permitidos → comportamento prévio preservado; schema required negativo; seleção válida → invocação com string verbatim. O teste atual que espera a segunda chamada com `{}` deve ser atualizado conforme contrato 147, não mantido por conveniência.

### Achado adicional F2 — schema ausente não trata declaração por selections

No ramo `if not isinstance(schema, Mapping)`, o código remove somente nomes de `declared=evidence_arguments`, mas não reconhece os campos declarados via `raw_selections` (mapping ou bare string), embora o contrato documente que qualquer selection nomeando campo também declara origem documental. O ramo retorna `unbound=()` e pode manter `arguments` livre. Caracterizar se esse ramo é alcançável no pipeline após schema validation; caso seja, fechar a brecha; caso inatingível, provar com teste/invariante. Não criar um novo validador.

### Achados de conformidade e limites

- Não foi localizada lista de strings de produtos, mapeamento `terminal bala→TERM. BALA`, regex de sinônimos, branching DAVI/O2, nova tool MCP ou segundo planner nas mudanças inspecionadas. `evidence_arguments` é uma lista **dinâmica de nomes de campos do schema**, não catálogo hardcoded de negócios; `ORCHESTRATED_FIELDS` é uma proteção técnica preexistente.
- O mecanismo de seleção exata de v17 continua verificando referência a evidence block, presença literal, schema, field, enum e constraints posteriores; isso protege **integridade de transporte** mas não prova pertinência semântica nem autorização.
- Execução LLM local `delia-json`, sem A/B externo nesta task, está conforme a decisão PO. Os resultados reportados `O2 0/10`, `D1 0/3`, `TÉO 0/3`, `VISTA 0/3` (um caso honest-empty), `WRITE-neg 3/3` não sustentam confiabilidade de release; erros de proposta/admission exigem evidência por estágio, não suposição universal de “capacidade 3B”.
- Full suite relatada `2294/2296` com 2 FAIL ambientais, não PASS integral; classificação ambiental ainda requer prova/exception aplicável no SHA efetivo. Ausência de deploy nessa task foi correta.

**DECISÃO:** `REWORK` para corrigir F1 antes de novo aceite técnico; investigar F2, fortalecer matriz de testes de regressão e emitir report no SHA/config final. Sem promoção da versão v18 enquanto `O2_LOCAL=0/10` e o fail-closed não estiver corrigido. Não ampliar escopo para nova engine, heurísticas de nomenclatura ou LLM externo. `NEXT_STEP=DELIA-R7-DECLARED-UNBOUND-OPTIONAL-ARGUMENT-FAIL-CLOSED-REMEDIATION`.


## Esclarecimento PO — recovery orientado ao objetivo

**Decisão PO, 2026-10-25:** falha de binding/argumento interno não é automaticamente falha do objetivo do usuário. Corrigir F1 (não executar consulta potencialmente ampla com parâmetro documental obrigatório para a *intenção* e não validado), **mas** preservar continuidade da investigação por caminhos READ legítimos já existentes. `FAIL_CLOSED` aplica-se à invocação inválida, não à conversação completa. DÉLIA deve tentar recuperação bounded por `goal_evidence_relevance`, `_recover_relevance`, `native_assessment`, `foreign_evidence`, candidate/token/schema e eventual ask-back existente, sem adicionar segunda máquina de estados, bypass de AuthZ ou loop sem limites. Para pedido “três exemplos de terminal bala”, a meta continua sendo **três registros empresariais pertinentes e verificados**, não afirmar êxito com documentos normativos ou busca ampla sem filtro. 

**Revisão dos testes de F1:** (1) declaração documental inválida em parâmetro opcional → **zero invocação sem filtro como substituição silenciosa**; (2) o resultado da tentativa inválida deve propagar `reason`/feedback tipado e consumível pelo mecanismo de recovery existente; (3) recuperação autorizada consegue formular uma nova proposta e consultar owner READ mantendo a intenção original, até o limite governado; (4) se outra superfície legítima tem a resposta, seleção semântica pode utilizá-la sem inventar parâmetros nem escolher designação em código; (5) AuthZ denegada, token inválido, payload malicioso ou operação de escrita **não** podem ser contornados por recovery; (6) quando opções legítimas se esgotarem, comunicar insuficiência honesta, não fabricar registros; (7) test coverage com parâmetros opcionais e obrigatórios, seleção ausente, stale, ambígua e generalização por outra categoria; (8) identificar primeiro estágio divergente e verificar outcome, não somente ausência de segundo invoke.

**Boundary:** antes de mudar estado/recovery, inventariar se o mecanismo já suporta reentrada após `unbound`/argument validation failure; `EXISTING_EQUIVALENT` e `REUSE_DECISION` são obrigatórios. Se a recuperação atualmente ocorre apenas após read irrelevante e não tem contrato para erro de pré-invocação, não simulá-la silenciosamente com uma busca vazia, não acoplar exceções improvisadas ao planner: STOP → `ARCHITECTURE_DECISION_REQUIRED` para a menor extensão contratual. Sem nova permissão, nova rodada ilimitada, prompts específicos O2 ou retries cegos. `O2_LOCAL_PASS` exige resultado útil repetível e verificável no modelo local; persistem gates de review, regressão e deploy.


## Ordem executiva consolidada do PO — 2026-10-25: conclusão local antes de deploy

**TASK_ID:** `DELIA-R7-LOCAL-GOAL-RECOVERY-TO-PRODUCTION-ACCEPTANCE-01`. **MODE:** REANCHOR → CHARACTERIZE → CONTRACT → RED → MINIMAL DIFF → GREEN → LOCAL MODEL EVAL → REGRESSION → INDEPENDENT REVIEW → RELEASE AUTHORIZATION → DEPLOY → PROD READ OUTCOME. O PO solicita execução contínua dentro dos gates, com correções causais sucessivas **até satisfazer critérios locais**; não encerrar uma iteração parcial como `PASS` ou entrega final. Porém, segurança, decisão arquitetural, segunda falha material do mesmo pacote, ausência de ambiente/modelo capaz, limite de recursos e autorização operacional são **STOP obrigatórios**, com reporte `BLOCKED_WITH_EVIDENCE`, nunca bypass ou promessa de sucesso incondicional.

### Requisitos de produto e critérios de aceite concretos

- Exemplo de alvo: `Traga três exemplos de terminal bala`. Aceite exige **3 códigos distintos**, descrições pertinentes e validação de cada registro na Domain API; 2 registros ou 3 trechos da norma **não** satisfazem. O2 original (2 registros) continua teste de regressão.
- **Falha de operação != falha do objetivo:** argumento documental declarado inválido não autoriza invocação READ ampla sem filtro; produz feedback tipado ao flow existente e **permite recuperação bounded e semanticamente guiada**. Não exibir ao usuário erro de programação/contrato se o objetivo ainda puder ser resolvido por path legítimo. Ao esgotar paths governados, comunicar insuficiência honesta, sem fabricar.
- Não confundir `schema.required` com campo necessário ao *plano semântico corrente*. Campo opcional para MCP ainda pode ser indispensável à intenção; manter comportamento preexistente para READ legitimamente sem filtros e sem dependência documental.
- Implementar correção F1 (optional declared-unbound) e caracterizar F2 (schema ausente), com RED→GREEN em invocation real. Verificar `missing_inputs`, decisão de recovery pré-invocação, `_build_arguments`, `_recover_relevance` e chamadas de owner. **Sem artificializar recuperação via invocação vazia.** Se a recuperação atual não admite feedback pré-invocação, propor extensão mínima contratual e gate da autoridade antes do diff; reutilizar estado/serviço/Policy existentes.
- LLM decide designação, escolha e caminhos; backend valida parâmetros dos MCP/Domain APIs, integridade de evidence refs e owner schema; **nenhum** dicionário de sinônimos, lista de strings de negócios, regex para produtos, `if terminal bala`, second planner, provider branch ou aumento informal de autonomia/loop.
- Relevance: dados reais mas semanticamente errados (`BALANCA` em resposta a terminal bala) não satisfazem; orientação documental não é registro; `MCP result != FACT`. Incluir negativos gerais sem codificar regras semânticas no backend.

### Plano de execução local e governança

- **Somente modelo local** autorizado; identificar seu real contexto/janela, quantização, qualidade de saída e limites. Investigar previamente timeout, `invalid_model_output`, truncamento de prompt, estágios/admission e orçamento antes de atribuir incapacidade à quantidade de parâmetros. Não utilizar nenhum LLM remoto. Se modelo local atual não consegue chegar aos estágios, buscar alternativa **local existente e autorizada**, ou solicitar decisão específica de modelo/infra; não instalar nem baixar automaticamente.
- Congelar SHA/model/config/CRI/corpus/env e matriz antes de executar. Avaliar fluxo completo e separadamente (a) segurança da tentativa; (b) recuperação; (c) 3 registros do pedido; (d) O2 2 registros; (e) terminal pino, outra família, D1/TÉO/VISTA, ambiguidade, injection, inexistente, AuthZ, PREPARE/ACT. Amostras bounded com denominadores completos e critério de confiabilidade definido pela autoridade. Não declarar `PASS` por teste unitário ou sucesso único.
- Corrigir um primeiro estágio divergente por vez, no owner legítimo. Cada pacote: hipótese causal/owner/contract → RED → minimal diff → GREEN → full regression → local-model eval → evidência. Segunda falha material do **mesmo pacote causal**: STOP e decisão; isso não impede avançar a nova causa independente comprovada dentro da fase/autorização.
- Suíte backend completa (falhas históricas classificadas fielmente, nunca `EXIT=0` com `2 FAIL` dito PASS), architecture/import DAG, security/AuthZ, write-negative, CRI local, provider-neutral generalization. Registrar tokens **medidos**, latência e erros por estágio, com correlação e sem secrets.
- Commit/push ff-only `main` após evidência, review independente do SHA/config real. **Autorização PO de objetivo de deploy é condicional**: revisão independente favorável, critérios locais, resolução/exceção formal C1, autorização operacional específica por serviço/SHA/digest/rollback e readiness de produção. Somente depois rollout scoped (preferir `[1/1] delia-api`, DAVI separado se necessário) e homologação READ em produção; se falhar, rollback/review, nunca tuning direto na produção. `R7_FINAL_ACCEPT` não se autoatribui.

### Entrega verificável

`LOCAL_THREE_RECORDS_OUTCOME`, `O2_LOCAL_OUTCOME`, `RECOVERY_FROM_PREINVOKE_FAILURE`, `F1`, `F2`, `MODEL_ID/CONFIG`, `SHA`, `FULL_TESTS`, `FIRST_DIVERGENT_STAGE`, `FALSE_POSITIVES`, `SECURITY`, `INDEPENDENT_REVIEW`, `OPERATIONAL_AUTHORIZATION`, `DEPLOY_SHA/DIGEST`, `PROD_OUTCOME`, `ROLLBACK`. Permitidos `FINAL_ACCEPT_READY` com prova ou `BLOCKED_WITH_EVIDENCE` para gate impeditivo real; **não** apresentar progresso parcial como tarefa concluída.


### Remediação F1/F2 — execução — 2026-10-25 (task `DELIA-R7-LOCAL-GOAL-RECOVERY-TO-PRODUCTION-ACCEPTANCE-01`)

**F1 (revisão):** `apply_evidence_bound_selections` só devolvia campos *required* não vinculados. Um campo **opcional declarado** documental que falhasse a vinculação tinha seu free-text removido mas `_build_arguments` validava `{}` e invocava o owner **sem filtro** — degradação silenciosa da proposta dependente.

**Correção (owner `argument_validation.py` + `_build_arguments`):** o 4º retorno passa a ser `unbound_declared` — **todo** campo declarado (via `evidence_arguments` ou `selections`, mapping ou string solta) que não materializou seleção literal verificada. `_build_arguments` com `unbound` não-vazio retorna `(None, missing_inputs)` — **zero invocação** da proposta dependente. Os nomes entram em `missing_inputs` e seguem o mecanismo existente `_resolve_missing_inputs` (resolver bounded §6.140) → clarify honesto. Nenhum planner novo, nenhum segundo state machine, nenhum retry ilimitado.

**F2 (schema ausente):** `input_schema=None` é valor válido do contrato `ProviderCapability` — o ramo é alcançável. Antes, `selections` não declaravam nomes sem schema: free-text de campo auto-declarado sobrevivia. Agora o ramo não-Mapping coleta declarações de `evidence_arguments` **e** de itens `selections` (str/Mapping, não-orquestrados), remove o free-text e devolve todos como `unbound` → fail-closed sem inventar propriedades de schema.

**Recuperação pré-invocação:** suportada pelo contrato existente — `arguments=None` + `missing_inputs` já alimenta resolver bounded e ask-back; na `_recover_relevance` o mesmo retorno encerra honesto (bounded, sem rodada extra). Falha de binding bloqueia a operação inválida, **não** o objetivo (doc 147, esclarecimento PO `18b86597e3`).

**RED→GREEN:** 5 testes v18 atualizados para a semântica F1 (declarado-não-vinculado ⇒ `pa.calls` sem re-invocação não filtrada) + 2 novos (`test_primary_declared_unbound_blocks_invocation`, `test_no_schema_declaration_never_bypasses`). Focused 192/192; full backend **2296 PASS / 2298** — 2 falhas ambientais pré-existentes preservadas (`test_fixture_matches_current_producer_output`, `test_http_timeout_maps_to_504`).

**Reavaliação local (`delia-json` ≈ qwen2.5 3.1B Q4_K_M, `http://ollama:11434/v1`, SHA=worktree pós-fix, instructions v18):**
- "Traga três exemplos de terminal bala" **0/10** — todas em `interaction_admission` (bypass conversacional/recusa honesta; ~1.6k in / ~110 out).
- O2 0/3 (2 admission, 1 `invalid_model_output`); pino 0/3; D1 0/3 conversacional; TÉO 0/3 honesto (cadeia completa → insuficiência); VISTA 0/3 admission honesto.
- **READ direto 1/3 GROUNDED** — estoque real do item `10080092` via Domain API (3 registros, branch/armazém, proveniência); 1 clarify ask-back; 1 insuficiência honesta.
- WRITE-neg 3/3 recusa honesta (zero ACT); AuthZ 401; **zero falsos positivos**.
- `evidence_bound` nunca disparou em runtime — o modelo 3.1B não emite `selections`/`evidence_arguments`; o contrato permanece provado por teste, não por adoção e2e.

**Veredito de gate:** confiabilidade e2e local ainda < critério de release → `BLOCKED_WITH_EVIDENCE` para deploy; residuais F1/F2 do contrato **fechados**; residual aberto = capacidade do modelo local autorizado.


### Revisão independente F1/F2 commit 8c01caa99f — 2026-10-25

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL (F1/F2 code)**; **LOCAL_GOAL_OUTCOME=FAIL**; **R7_FINAL_ACCEPT=NO**; **DEPLOY_AUTHORIZED=NO**. Revisados no GitHub `8c01caa99f`, diff de `argument_validation.py`, `orchestration._build_arguments`, casos de `test_goal_evidence_relevance.py` e relatório do executor. Inspeção estática independente; suítes/Docker/Ollama não reexecutados por este reviewer. Report do executor de 192 testes focados verdes, 2296 de 2298 backend (2 FAIL ambientais), e 0/10 três registros é `EXECUTOR_REPORTED`.

**F1 está corrigido no caminho caracterizado:** `unbound_declared` agora contempla campo documental declarado ausente independentemente de `schema.required`, e `_build_arguments` devolve `(None, missing)` **antes** de validar e invocar a proposta. Testes atualizados deixam de esperar `search_items({})` como recuperação. **F2 caracterizado e corrigido:** `input_schema=None` é possível; ramo sem Mapping agora recolhe declaração por `evidence_arguments` e `selections` e devolve campo não-vinculado, bloqueando sua invocação. No diff não surgiram mapas de sinônimos, hardcodes de produtos, provider branches, planner ou engine novos.

**Residual R1 — recuperação do objetivo não comprovada:** evidência de `arguments=None/missing_inputs` e do resolver/ask-back prova apenas um **encaminhamento contratual** (ou encerramento honesto dentro de `_recover_relevance`), não prova que o LLM prossegue de forma autônoma até registros corretos. O executor reporta que o modelo local `delia-json` quase sempre diverge em `interaction_admission` e nunca emite `selections/evidence_arguments`; `RECOVERY_SUCCESS_RATE` não é mensurável a partir da avaliação. Pedido de 3 registros continua `0/10 FAIL`; O2 `0/3`; o único READ grounded foi pergunta distinta sobre estoque.

**Residual R2 — precisão de testes de recovery:** `test_primary_declared_unbound_blocks_invocation` verifica ausência de `search_items` inválido e um status permissivo, não assert do caminho `_resolve_missing_inputs` e de uma segunda proposta válida com resultado de 3 registros. Requer caracterização de caller e teste de integração governada demonstrando recovery positivo, se suportado pelo contrato existente; sem forçar nova rodada ou fabricar invocação vazia. Nos cenários de `_recover_relevance` o retorno `None` pode encerrar a recuperação; isso precisa ser expresso como limite e não como auto-recovery funcional.

**Residual R3 — ordenação/limites:** `declared_names` é `set`, e `unbound_declared` é obtido pela iteração desse set. A ordem do `missing_inputs` pode variar entre processos; inspecionar impacto sobre testes/UX/determinismo e normalizar pela ordem de schema/proposta quando necessário, sem semântica nova. O limite `MAX_EVIDENCE_SELECTIONS` trunca declarações excessivas; verificar que valores declarados além do limite não ficam aceitos como texto livre sem sinalizar invalid/over-limit. Este é risco a caracterizar, não violação provada em execução.

**Gates:** backend ainda tem 2 FAIL ambientais reportados e precisa exceção formal ou runner corrigido; CRI OFF live segue não executado. Nenhum deploy nesta task foi correto. Não usar o argumento "modelo local 3B incapaz" como prova universal; caracterizar contexto, timeout e invalid_model_output no SHA final. `NEXT_STEP=RECOVERY_OUTCOME_AND_DECLARATION_LIMIT_CHARACTERIZATION`; sem modelos externos conforme PO; qualquer novo diff depende de causa/owner/contrato e RED.


### Remediação R1/R2/R3 (revisão `abccde87ac`) — execução — 2026-10-25 (task `DELIA-R7-EXISTING-RECOVERY-AND-OUTCOME-CLOSURE-01`)

**R1 — recuperação positiva provada:** novo teste `test_declared_unbound_recovers_via_resolver_to_owner_outcome` demonstra o caminho real completo: campo documental declarado não vinculado → `(None, missing_inputs)` → consumidor existente `_resolve_missing_inputs`/`_select_resolver` → READ resolver same-owner → rebuild com `owner_evidence` → nova proposta válida (`query=TERM. BALA` provada no payload do resolver) → READ do owner → veredito `corresponds` → `SUCCESS`. Asserts: consumidor (`select_resolver` no trace de purposes), contagem de tentativas (2 builds de argumentos), chamadas do owner (`list_nomenclatures({})` → `search_items({"query":"TERM. BALA"})`), resultado. Nenhum planner/engine novo — o canal existente bastava.

**Defeito encontrado durante a prova (mesma família F1, uma borda abaixo):** o tail de `_resolve_missing_inputs` ignorava `still_missing` e `_resolved_values_proven` pula campos ausentes — um rebuild que retornava `{}` "resolvia" e invocava o owner **sub-filtrado** (na prática `search_items({})`). Correção no mesmo owner: nova checagem de cobertura `_missing_inputs_bound` — a resolução só conta quando todo input originalmente faltante está ligado; caso contrário fail-closed para clarify. Aplicado também ao branch ambíguo (`ambiguous_proven_selection`).

**R2 — precisão dos testes de recovery:** o teste positivo asserta consumidor, número de tentativas de proposta, proposta gerada, owner invocado e Outcome; `test_resolver_rebuild_without_missing_inputs_never_invokes` prova o negativo (rebuild sem cobertura nunca invoca).

**R3 — ordenação/limites:** `declared_names` era `set` — `unbound_declared`/`missing_inputs` tinham ordem não determinística. Agora `dict` ordenado preserva a ordem da proposta (determinístico, sem semântica nova). `MAX_EVIDENCE_SELECTIONS=8` truncava a coleta de declarações — um item `selections`/`evidence_arguments` além do cap declarava nada e seu free-text escapava como argumento comum. Agora a **declaração** varre a lista completa (scan barato de strings); o cap limita apenas materialização. Declarado além do cap → unbound → bloqueio tipado, nunca escape silencioso.

**Reavaliação local `delia-json`:** pendente de nova execução no SHA final — comportamento esperado dominado por `interaction_admission` (capacidade do modelo 3.1B), contrato provado por teste.

**Veredito:** residuais R1/R2/R3 fechados por teste; residual aberto permanece a capacidade do modelo local autorizado para o Outcome empresarial end-to-end.


### Revisão independente do recovery e96a669d51 — 2026-10-25

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL** para o diff bounded `e96a669d51`; **BUSINESS_OUTCOME_LOCAL=FAIL**; **DEPLOY_GATE=BLOCKED**; **R7_FINAL_ACCEPT=NO**. Revisão estática de commit, diff e testes no GitHub, **sem reexecutar** Ollama/backend; resultados do executor são `EXECUTOR_REPORTED`. O HEAD da main avançou após o commit revisado, portanto validar novamente o SHA efetivo na próxima promoção.

**Aceitos com ressalva:** `_missing_inputs_bound` e dois pontos de verificação no `_resolve_missing_inputs` impedem a reconstrução vazia de resolver em substituição aos argumentos semanticamente necessários; a validação de cobertura complementa `_resolved_values_proven`, que ignora campos ausentes. Ordenação de `unbound_declared` agora é estável pela ordem da proposta; coleta de nomes vai além do cap de materialização para impedir escape de free-text documental. Sem nova lista de strings empresariais, tabela de sinônimos, branches provider-specific, registry, engine ou planner no diff revisado.

**Limites de prova:** `test_declared_unbound_recovers_via_resolver_to_owner_outcome` usa modelo de propostas fake e `FakeProvider`; confirma a cadeia interna `declared-unbound→resolver→rebuild→READ→SUCCESS` no teste, **não** capacidade autônoma de LLM local nem Outcome empresarial da Domain API. O critério '3 registros reais' continua `FAIL` (`0/10`), O2 `0/3`, e nenhum caso local atingiu `evidence_bound`. Portanto R1 é `PASS_CONTRACT_TEST` mas `PENDING_REAL_MODEL_OUTCOME`. Foco de próxima etapa é `interaction_admission` sob modelo local autorizado, não refatorar binding/recovery sem defeito novo.

**Riscos residuais a caracterizar antes de aceite final:** (1) `_missing_inputs_bound` verifica presença normalizada, não suficiência semântica do valor (delegada às validações/provenance/LLM); confirmar negativos para valor vazio, `None`, alias normalizado e payload inválido nas duas branches do resolver; (2) varredura completa de declarações é permitida somente sob limites globais de payload/top-level/bytes, confirmar que listas grandes não criam custo sem bound; (3) teste positivo usa fixture com designações específicas, aceitável em **teste** desde que não transborde para código produtivo; (4) dois testes ambientais reportados como FAIL exigem exceção formal ou ambiente correto para full-suite PASS. Nenhum desses riscos comprova sozinho regressão produtiva, mas não podem ser omitidos do fechamento R7.

**Decisão:** `RECOVERY_CODE=ACCEPT_WITH_RESIDUAL`; `NO_NEW_HARDCODE_IDENTIFIED`; `LOCAL_OUTCOME=FAIL`; `INDEPENDENT_REEXECUTION=TEST_NOT_RUN`; `NEXT_ACTION=LOCAL_ADMISSION_OUTCOME_CAUSAL_REVIEW`; `DEPLOY_AUTHORIZED=NO`.


### Revisão independente da v19 6e51626b1b — 2026-10-25

**REVIEW_VERDICT=REWORK** (arquitetura/projeção a reconciliar, business Outcome falhou); `DEPLOY=BLOCKED`; `R7_FINAL_ACCEPT=NO`. Inspecionados no GitHub commit `6e51626b1b`, `orchestration.py`, instruções v19 e relatórios. Sem reexecução independente da suíte/infra: números permanecem `EXECUTOR_REPORTED`.

**A1 — possível DRIFT: admission recebeu `owner_surface_kinds` estático** com categorias literais de registros/produtos/materiais/peças, guidance, dashboards/painéis e tickets. Essas categorias são genéricas, não um mapeamento de `terminal bala`, mas podem constituir uma taxonomia/copied knowledge de superfícies desligada do catálogo MCP/OpenAPI **live**. Verificar owner, consumidores, origem canônica e invariantes de dynamically discovered capabilities; se `_group_summaries` exige carregar grupos depois da admissão, avaliar menor projeção read-only de superfícies permitida pela fase/contrato, sem trazer owner catalog excessivo nem introduzir authority paralela. Não remover a lista por suposição: provar se é hint autorizado e source-aligned ou emitir `EXECUTION_DRIFT/ARCHITECTURE_DECISION_REQUIRED`. Proibir branch por catálogo fixo nas decisões de autorização/execução.

**A2 — melhorias bounded verificadas no diff:** remoção da premissa `no owner catalog`; threading de `goal.business_subject` para `_invoke_foreign_evidence` e `_propose_candidate_arguments` dentro da fronteira existente; instruções versionadas v19. `business_subject` vem de proposta/modelo, não autoridade empresarial; verificar alcance nas duas chamadas, bounded serialization e fallback `None`, compatibilidade `schema` no prompt e contrapartes contratuais. Testar com troca de providers/capabilities, sem hardcode por nome.

**A3 — falso positivo de pertinência é BLOQUEANTE:** o executor reportou retorno `GROUNDED` para rotas `VISTA` do catálogo de warehouse-balance como se fossem três registros de terminal bala. `MCP result != FACT`, `control plane metadata != business outcome`; exigir teste negativo reproduzindo payload, stage `goal_evidence_relevance` e projeção, sem transformar o judge do LLM em autoridade. Preservar proprietário de dados (Domain API), checagem de quantidade, tipo e provenance. Não criar `if VISTA`/blacklist de strings.

**A4 — limites da evidência:** o relato documenta `0/10` business Outcome apesar de admissão `~10/10`; GPU restart e retry até 3 são configurações locais, não garantias de prod; teto governado 60s não pode ser contornado; não atribuir tudo ao modelo 3B sem separar falhas de contexto, token, schema e relevância. O deploy corretamente não ocorreu. Falhas backend ambientais (2) e CRI OFF live permanecem abertas.

**NEXT:** proof-first A1 e regressões contratuais A2; reproduzir e fechar A3 em testes locais determinísticos + teste de modelo local quando possível. Documentar `EXISTING_EQUIVALENT`/`REUSE_DECISION`, corrigir diff mínimo, reavaliar matriz e obter nova revisão independente. Mudança de modelo local exige gate/capacidade operacional específica; usuário proibiu testes com modelos externos. `R7_CLOSED=NO`.


## Encaminhamento de coordenação — Plano 148 (2026-10-25)

O review v19 A1/A3 e ausência de Outcome exigem plano de remediação arquitetural orientado por padrões de produção; ver [148 — arquitetura, drift e Outcome](./148-r7-architecture-drift-remediation-and-outcome-closure-plan.md). Este plano prevalece como próximo bounded step para A1/A3: inventorizar origem de `owner_surface_kinds` e substituir conhecimento estático não autorizado por contexto de superfícies live/agnóstico, e impedir metadados de control-plane de serem apresentados como business records sem Domain API, com gates estruturais de provenance/role e relevância semântica LLM. Proibidos nova engine, nova taxonomia hardcoded, provider branches, external LLM eval. Deploy permanece BLOCKED até evidência e revisão.
