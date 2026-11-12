# 310 — INT-1 Semantic Root Cause and Governed Authorization Denial Communication

**TASK_ID:** `DELIA-C3-T2-INT1-SEMANTIC-ROOT-CAUSE-AND-AUTHORIZATION-DENIAL-COMMUNICATION-01`  
**Data:** 2026-11-12  
**EXTERNAL_LLM:** AUTHORIZED — EXECUTED (G1+P1+M1 ×1, AUTH-DENY ×1 efetiva + 2 formulações descartadas)  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**FULL_BATTERY:** NOT_RUN  
**AGENT_CHANGED:** NO (1 Agent Pydantic AI existente; sem router/planner novos)  
**PERMISSIONS_CHANGED:** NO (nenhum grant criado/alterado/removido nesta task)

---

## 1. Reancoragem

| Item | Value |
|---|---|
| REFERENCE_HEAD (task) | `3fa89ca925…` (ancestral do HEAD local) |
| WORK HEAD (início) | `1bee257518…` (22 commits atrás de `origin/main` `22894b0741…`; commits origin = escopo supplies/portal, não-INT-1) |
| PHASE_FROM_16 | C3/T2 APPROVED; `C3_T2_AUTHORIZED=YES`; INT-1 BLOCKED |
| NEXT_FROM_LEDGER | INT-1 pendente de revisão de coordenação |
| FROZEN_DECISIONS | `SELECTION_ONLY_GROUNDED_SYNTHESIS=FROZEN`; `MODEL_AUTHORED_FACTUAL_PROSE=NONE`; autoridade Core/Domain inalterada |
| WIP concorrente | WIP pré-existente identificado como **desta mesma task** (v2-2 + authz denial + testes); preservado e validado |
| Instruction (candidato inicial task) | `generalist-semantic-v2-1-object-continuity` fp `4ebd5260b6cf9ba9` |
| Instruction (aplicada — WIP validado) | `generalist-semantic-v2-2-object-authz-continuity` fp `3692299dac74c26e` MATCH runtime |
| Model / profile / pydantic_ai | `qwen/qwen3-14b` / `openrouter_qwen` / `2.50.0` |
| Config fp | `e4a5b706a3b3156b` |
| Evals | `or-qwen14b-985d439b1653` (G1/P1/M1, sujeito `ti_delpi`); `or-qwen14b-525ed88ac205` (AUTH-DENY, sujeito `e2e-delia`) |
| Isolation | `delpi-delia-eval-int1-or-qwen14b` rede delpi; `PROD_CONTAINER_UNTOUCHED=YES` |

---

## 2. Inventário (mecanismos existentes — REUSE/EXTEND)

| Mecanismo | OWNER / IMPLEMENTAÇÃO | CONTRATO | REUSE_DECISION |
|---|---|---|---|
| Pydantic AI Agent único | `pydantic_ai_investigation.py` | toolsets MCP nativos + `WrapperToolset` envelope/schema hints | REUSE |
| `InvestigationDeps` | idem | tool-call count, no-progress retry state, owner-argument recovery, progress | EXTEND (gate authz no retry) |
| Evidence projection | `_attempt_projection(...)` | observação estruturada model-visible | EXTEND (`authorization_denied`, coverage note terminal) |
| Bounded `ModelRetry` | idem | one-shot NO_PROGRESS recovery | EXTEND (bloqueio para AUTHZ_DENIED) |
| Finalização semântica | `semantic_capability_support.py` | `_finalize_agent_collected_attempts` status governado | EXTEND (precedência AUTHZ_DENIED, `authorization_denied_partial`) |
| Mensagem ao usuário | `handle_interactive_turn.py` | deterministic message kinds | EXTEND (`MESSAGE_KIND_AUTHZ_DENIED`) |
| Contrato erro MCP DAVI | `api-delpi/app/interface/mcp/server.py` | `{"code":"AUTHORIZATION_DENIED","recoverable":false}` | REUSE (descrição de capability clarificada) |
| Contrato erro MCP TÉO | `transformometro-api/tm_app/interface/mcp/server.py` | forbidden/authentication envelopes | REUSE (descrição de domínio clarificada) |
| Instrução semântica | `config/investigation_instructions.delpi.json` | instruction resource versionado + fingerprint | EXTEND (v2-1 → v2-2) |
| Harness eval | `scripts/int1_openrouter_qwen14b_instrumented_eval.py` + `run_...sh` | cenários + traces seguros | EXTEND (cenário AUTH-DENY; override de sujeito por env var efêmera) |

`EXISTING_EQUIVALENT=YES` para todos os mecanismos utilizados. Nenhuma camada nova de classificação, RBAC paralelo, agente extra ou roteamento por keyword.

---

## 3. Frente A — Investigação causal da seleção semântica

### 3.1 Hipóteses

| Hipótese | Resultado | Evidência |
|---|---|---|
| H1 — Contratos insuficientes | PARCIALMENTE PROVEN → remediado | Docs 307–308: boundary B3 íntegro, mas descrições TÉO/DAVI permitiam falso amigo "árvore/composição" (processo vs produto). Correção: descrição DAVI `read` menciona registros produto/item e composição/BOM; TÉO `read` declara domínio engenharia de processos e nega capacidade de estrutura de materiais de produto — wording neutro, sem cenário/ID hardcoded. |
| H2 — Instrução semântica insuficiente | PROVEN → remediado | v2-1 não orientava continuidade de objeto após seleção incompatível nem tratamento de AUTHZ_DENIED; v2-2 adiciona vocabulário hierárquico compartilhado, continuidade de objeto e regra explícita de negação. |
| H3 — Escolha inadequada do modelo | PROVEN_IN_SAMPLE (307–309) | Qwen 14B selecionava TÉO para objetivo produto/BOM apesar de contratos visíveis; atrator semântico estocástico, não determinístico. |
| H4 — Continuidade inadequada | PROVEN → remediado | Doc 308 introduziu `ModelRetry` one-shot para NO_PROGRESS; sem gate de autorização o retry poderia tentar owner equivalente para o mesmo dado protegido — corrigido (§4). |
| H5 — Contratos semanticamente concorrentes | PROVEN (corolário H1) | Descrições estruturalmente semelhantes ("decomposição/árvore") entre TÉO e DAVI; a palavra "árvore" não é a causa definitiva isolada — é a sobreposição de vocabulário hierárquico sem distinção de objeto empresarial. |
| H6 — Limitação do modelo | INCONCLUSIVE | Com v2-2 + contratos clarificados, G1/P1/M1 selecionaram DAVI; amostra única não prova estabilidade, mas remove a necessidade de invocar limitação de modelo. |

### 3.2 Primeira divergência material

`MODEL-VISIBLE TOOL CONTRACTS → SEMANTIC TOOL SELECTION`: sobreposição vocabular de decomposição hierárquica (processo × produto) sem âncora de objeto empresarial dominava a decisão do modelo. Correção aplicada nos **owners legítimos** (descrições MCP TÉO/DAVI) + instrução generalista — não na DÉLIA, sem if de roteamento.

### 3.3 Evidência real Qwen (v2-2, fp `3692299dac74c26e`, sujeito autorizado `ti_delpi`)

Eval `or-qwen14b-985d439b1653` — 3 model requests, 4 remote invocations, ~170s total:

| Cenário | Sequência | Status final |
|---|---|---|
| G1 `Mostre a árvore de componentes e relações do item 90260921` | `davi.get_context`(catalog) → `davi.read get_product_structure(code=90260921)` | GROUNDED / complete — resposta com BOM real (CHICOTE DE LIGACAO) |
| P1 `Qual é a estrutura do produto 90260921?` | `davi.read get_product_structure` first | GROUNDED / complete |
| M1 `…árvore de componentes e relações que compõem o produto…` | `davi.read get_product_structure` first | GROUNDED / complete |

**Contraste com 309 (v2-1):** G1 era TÉO-first com recuperação DAVI; em v2-2 os três cenários ancoram em DAVI sem passar por TÉO. `FIRST_TOOL_SUITABILITY=IMPROVED_IN_SAMPLE` — não declarada `SELECTION_FIXED` por generalização (n=3, cenários conhecidos).

---

## 4. Frente B — Propagação de autorização negada

### 4.1 Defeito comprovado e correção

Antes da correção, uma negação `AUTHORIZATION_DENIED` do owner era projetada como falha genérica e podia ativar o `ModelRetry` de NO_PROGRESS — i.e., a DÉLIA tentaria outro owner para o mesmo dado protegido (bypass semântico) e a mensagem final era indistinguível de indisponibilidade técnica.

Correções mínimas sobre mecanismos existentes:

| Ponto | Correção |
|---|---|
| `pydantic_ai_investigation.py` | `_is_authorization_denied(...)` reconhece `AUTHORIZATION_DENIED`/`authz_denied`/`mcp_authorization_denied`; `continuity_model_retry_allowed(...)` **nega retry** para tentativa negada; `_attempt_projection(...)` emite `authorization_denied: true`, `evidence_citable: false` e coverage note explícita ("not missing data, not an argument error, not technical unavailability; do not retry equivalent access through another capability"). |
| `semantic_capability_support.py` | finalização preserva `AUTHZ_DENIED` + código canônico mesmo se falha não relacionada ocorrer depois; `authorization_denied_partial` quando observações autorizadas coexistem com negação. |
| `handle_interactive_turn.py` | `MESSAGE_KIND_AUTHZ_DENIED` determinístico: "Você não possui permissão para consultar essa informação. O acesso é controlado pelas permissões do Minha DELPI. Nenhum dado operacional foi verificado. Caso necessite desses dados, solicite a autorização ao responsável pelo acesso." — sem afirmar inexistência, sem roles/tokens/stack. |
| Instrução v2-2 | orienta o modelo a reconhecer AUTHZ_DENIED como limite de autoridade (não como gap de investigação), mantendo proibição de fatos inventados. |

### 4.2 Identidades (sem alteração de permissões)

| Sujeito | Estado | Uso |
|---|---|---|
| `ti_delpi` | `delia.access`, `transformometro.access`, `tv-dashboard.read`, `api-delpi.access` | AUTH-ALLOW (G1/P1/M1) |
| `e2e-delia` / `e2e-delia@delpi.e2e` | usuário **Core pré-existente** com `delia.access` + `transformometro.access`, **sem** `api-delpi.access` | AUTH-DENY |

O usuário `e2e-delia` existia no Core DB mas não tinha identidade no Keycloak DEV. Foi **provisionada identidade Keycloak** (mesmo e-mail → binding por `email` claim no `auth_middleware` da Core) — nenhum grant foi criado, alterado ou removido. Senha de DEV gravada apenas no usuário Keycloak local; não commitada.

Caminho testado: `Keycloak(token) → Core RBAC (bind por e-mail, grants efetivos) → api-delpi MCP admission (exige api-delpi.access) → DENY`.

### 4.3 Evidência real AUTH-DENY

Eval `or-qwen14b-525ed88ac205`, sujeito `e2e-delia`, pergunta idêntica a P1 (`Qual é a estrutura do produto 90260921?`), 1 model request, 1 remote invocation, 23.3s:

```text
invoke: davi.read capability=get_product_structure arguments={code:90260921}
owner:  RemoteToolOutcome is_error=true
        structured={code:AUTHORIZATION_DENIED, recoverable:false, message:Forbidden}
projection: status=AUTHZ_DENIED, evidence_citable=false,
            investigation_progress_class=NO_PROGRESS,
            coverage_note="Authorization denied by the governing authority.
            This is not missing data, not an argument error, and not technical
            unavailability. Do not retry equivalent access through another
            capability for the same protected evidence. ..."
continuity: sem ModelRetry; investigação encerrada (1 chamada)
final user message: "Você não possui permissão para consultar essa informação.
            O acesso é controlado pelas permissões do Minha DELPI. Nenhum dado
            operacional foi verificado. Caso necessite desses dados, solicite a
            autorização ao responsável pelo acesso."
declared_answer (modelo): status=insufficient, sem evidência citável,
            sem dado protegido vazado
```

Critérios §21:

```text
AUTH_DENIAL_PRESERVED=YES
AUTH_DENIAL_NOT_TREATED_AS_NOT_FOUND=YES
NO_AUTHORIZATION_BYPASS=YES (retry bloqueado; 1 única invocação)
NO_PROTECTED_DATA_LEAK=YES (payload de erro sem dado empresarial)
USER_FACING_EXPLANATION=PASS
```

### 4.4 Formulações descartadas (dentro do orçamento)

| Tentativa | Eval | Resultado |
|---|---|---|
| `Quais pedidos de venda estão em aberto?` | `or-qwen14b-7ab79ffda5b0` | Falso amigo: modelo foi para `teo.read` (tasks) → argument errors → clarification. INCONCLUSIVE para authz; evidencia residual de ambiguidade "pedidos/tarefas em aberto". |
| `Mostre o resumo de inadimplência dos clientes.` | `or-qwen14b-ff1b27905b0e` | Capabilities de inadimplência têm `davi_status=NEEDS_MODEL_SAFE_PROJECTION` → **não executáveis**, ausentes do catálogo elegível (94/794). Modelo não achou capability → insufficient. INCONCLUSIVE para authz. |

Observação arquitetural: para `ti_delpi` (que possui `api-delpi.access`), praticamente todas as capabilities DAVI executáveis aceitam o código geral — negação de domínio real exige sujeito sem a permissão de admissão do owner. O sujeito `e2e-delia` cobre exatamente esse caso.

---

## 5. Testes determinísticos (container `delpi-delia-api`, imagem dev)

| Suíte | Resultado |
|---|---|
| `test_int1_authz_denial_communication.py` (novo) | PASS — projeção AUTHZ_DENIED/`mcp_authorization_denied`/`evidence_citable=false`; bloqueio de retry para negação; retry permitido para NO_PROGRESS não-authz; precedência AUTHZ sobre timeout posterior; mensagem de permissão sem roles/tokens/stack/dado protegido |
| `test_int1_semantic_continuity_remediation.py` | PASS |
| `test_investigation_instruction_resource.py` | PASS — v2-2 fp `3692299dac74c26e` |
| `test_interaction_runtime.py` | PASS — mensagem de negação exige vocabulário de permissão/Minha DELPI e rejeita "não há registro" |
| `transformometro-api/test_teo_mcp_contract.py` | PASS — descrição TÉO declara domínio processo e nega BOM de produto |
| Suíte delia-api pontual | 3 falhas **pré-existentes no HEAD** (`test_runtime_profiles_share_execution_policy` e 2 correlatas em config de perfis) — arquivos não tocados pelo WIP; fora do escopo |

Fingerprint de instrução confirmado em runtime: `generalist-semantic-v2-2-object-authz-continuity`, `3692299dac74c26e`.

---

## 6. Arquivos alterados

```text
api-delpi/app/interface/mcp/server.py                       (descrição read: produto/BOM)
transformometro-api/tm_app/interface/mcp/server.py          (descrição read: domínio processo, nega BOM produto)
transformometro-api/tests/test_teo_mcp_contract.py
delia-api/config/investigation_instructions.delpi.json      (v2-2)
delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py
delia-api/app/application/capability_provision/semantic_capability_support.py
delia-api/app/application/interaction/handle_interactive_turn.py
delia-api/tests/test_int1_authz_denial_communication.py     (novo)
delia-api/tests/test_int1_semantic_continuity_remediation.py
delia-api/tests/test_interaction_runtime.py
delia-api/tests/test_investigation_instruction_resource.py
delia-api/scripts/int1_openrouter_qwen14b_instrumented_eval.py (cenário AUTH-DENY)
delia-api/scripts/run_int1_openrouter_qwen14b_instrumented_eval.sh (override de sujeito efêmero)
docs/.../310-int1-semantic-root-cause-and-governed-authorization-denial-communication.md (este)
```

## 7. Residuais e recomendações

| Residual | Classificação |
|---|---|
| Seleção semântica melhorada mas amostra n=3 conhecida; ambiguidade "pedidos/tarefas em aberto" segue como atrator TÉO | `GENERALIZATION_NOT_PROVEN` — candidato a corpus ampliado em estágio posterior |
| Capabilities DAVI não executáveis (`NEEDS_*_PROJECTION`) indisponíveis para o modelo — domínio legítimo de negação fina sem rota alcançável | `TO_INVENTORY` — decisão de catálogo/projeção do owner, fora do escopo INT-1 |
| Token usage/cost não reportados pelo provider (0s) | `EVIDENCE_GAP` inerente ao harness atual |
| 3 falhas pré-existentes em config de perfis de runtime | `STALE_EVIDENCE` — não relacionadas; inventariar em task de config |
| Identidade `e2e-delia` no Keycloak DEV é provisionamento local de avaliação; grants Core inalterados | documentado; não versionado em repo |

## 8. Estado final

```text
FULL_BATTERY=NOT_RUN
PRODUCTION_DEPLOY=NOT_AUTHORIZED
INT1_STAGE_ACCEPTANCE=PENDING_COORDINATION_REVIEW
INT1_CLOSED=NO
INT2_IMPLEMENTATION_AUTHORIZED=NO
INT3_IMPLEMENTATION_AUTHORIZED=NO
T3_AUTHORIZED=NO
NEXT=COORDINATION_INT1_SEMANTIC_AND_AUTHZ_INDEPENDENT_REVIEW
```
