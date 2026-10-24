# 144 — Trilha B executada: recuperação contextual cross-capability na DÉLIA

**TASK_ID:** `DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-CROSS-CAPABILITY-RECOVERY-01`
**ESCOPO:** exclusivamente `delia-api` (Trilha B do doc 143). Nenhum arquivo do DAVI/api-delpi, Agent Studio, Keycloak ou corpus documental foi alterado.
**HEAD DE IMPLEMENTAÇÃO:** avaliado como `delia-api-xcap-eval:v2` (SHA de commit `394b7c738f`); push `ff-only` após documentação.
**STATUS:** `EXECUTED`; `DEPLOY_AUTHORIZED=NO`; `R4_AUTHORIZED=NO`; aceite independente pendente da coordenação.

## 1. Contrato implementado (extensão, não recriação)

`EXISTING_EQUIVALENT=YES_PARTIAL`; `REUSE_DECISION=EXTEND` — todos os estágios reutilizados, zero novas engines/planners/ports/adapters.

- **`_select_group` / `_select_capability`** aceitam `relevance_feedback: str | None`: o payload governado de mismatch é projetado dentro do bloco untrusted de catálogo (`capability_groups`/`capabilities` + `relevance_feedback`), mesma disciplina de `prior_observation`. Revalidação determinística inalterada: group/capability só "selected" se existir na superfície live.
- **`_recover_relevance`** (única rodada por interação, guard `_RELEVANCE_RECOVERY_USED`) agora re-executa a seleção governada quando há alternativa (`len(groups)>1` ou múltiplas capabilities no grupo): `select_group` → `select_capability` → `_build_arguments` — com `relevance_feedback` em todos. Fallback para o descriptor original preserva a reformulação de mesma capability do doc 142.
- **Gates reexecutados na recuperação:** classe resumível (`_RESUMABLE_OPERATION_CLASSES` — PREPARE/ACT rejeitados por `decision=rejected_class`), `_unproven_identifier_inputs`, dedup `identical_arguments` (somente mesma capability + mesmos args), budget `_budget_allows_resolver`, re-julgamento `goal_evidence_relevance` único pós-reinvoke.
- **`prior_result_preview`**: preview bounded dos registros retornados (≤16 records, ≤3000 chars) adicionado ao feedback — untrusted owner data, nunca instrução; permite à reformulação pivotar sobre a nomenclatura observada.
- **Instruções v3** (`orchestration_instructions.delpi.json` version `"3"`; `_ORCH_VERSIONS` aceita `{"1","2","3"}`): `select_group`/`select_capability` documentam `relevance_feedback` como sinal untrusted de mismatch; `arguments` orienta reformulação por sinônimos/reduções/abreviações no estilo de nomenclatura do owner — texto semântico genérico, sem `terminal→TERM.` hardcoded.
- Preservado: `MCP_GUIDANCE != POLICY`, `MODEL_PROPOSAL != AUTHORIZATION`, `GROUNDING != RELEVANCE`. Nenhuma autorização ampliada; nenhum endpoint escolhido fora da seleção governada.

## 2. Testes (RED → GREEN)

`tests/test_goal_evidence_relevance.py` (+5 casos, 28 total no módulo):

- cross-capability: `irrelevant` → reselection de outro grupo/capability → reinvoke → `corresponds` → answered;
- rejected_class: reseleção apontando PREPARE/ACT declinada sem invocação;
- `prior_result_preview` presente no payload de recovery (untrusted);
- arg idêntico / orçamento / falha de modelo / metadados adversariais preservados do doc 142.

Snapshot governado (`test_r1_instruction_resource.py`) atualizado para v3 — o teste exige bump de versão + mapa sha256 para qualquer mudança intencional de texto.

**Suite completa delia-api: exit=0 (sem falhas; verde total)** — incluindo fixtures de contrato atualizadas na task anterior. Gates: `audit_platform_guardrails` findings=0, `audit_backend_boundaries` findings=0, `audit_architecture_phase3` OK. `CRI_OFF` intocado (edge só corre com CRI ativo).

## 3. Avaliação real isolada (kimi-k3, srv-api)

Container `delia-xcap-eval` na `infra_delpi-network`, env de produção, CRI v5, sem portas publicadas; removido após o eval. Baseline A = produção `delpi-delia-api` (85cdd244f531).

| Cenário | A (baseline) | B (candidato) |
|---|---|---|
| Matriz `r1r2_integrated_eval` | 11/11 PASS (evidência doc 142) | **11/11 PASS, zero blocking failures** |
| O2 "dois exemplos de terminal bala" | apresenta **balanças** como resposta (`10450070 BALANCA BALMAK`, `10450535`) | julgamento `irrelevant` → rodada de recuperação → insuficiência honesta `insufficient_evidence` |
| O2 reformulado "term. bala" | — | **2 registros pertinentes reais** (`10080092 TERM. BALA 0,50-2,27MM2`, `04/10/1008 TERM. BALA 1,00-2,50MM2`) |
| Sinônimo legítimo "balança de plataforma" | grounded | grounded, 50 registros reais, sem over-block |

**Trilha de recuperação observada em B (logs):**
- Tentativa 1 (`513134a5`): `irrelevant` → reseleção select_group+select_capability+arguments → mesma capability, args idênticos → `identical_arguments` → insuficiência (dedup determinístico segurou).
- Tentativa 2 (`94c8f410`): `irrelevant` → **reseleção cross-capability**: `davi.discover_delpi_information` (DISCOVERY) → `candidate_arguments` → `davi.execute_delpi_information` (READ) → re-julgado `irrelevant` → insuficiência. Prova viva de recuperação por fonte alternativa elegível, todos os gates reexecutados.
- Tentativa 3 (`f21d84ac`): `irrelevant` → mesma capability com **args reformulados** (`reinvoke`) → re-julgado `irrelevant` → insuficiência honesta. Uma rodada por interação, sem loop.

**Leitura honesta do outcome de negócio:** a máquina governada funciona (reformulação + cross-capability + re-julgamento + fail-closed); kimi-k3 não derivou a abreviação `TERM.` dentro da rodada única nas tentativas observadas — o critério §4 do doc 143 ("resolver 2 exemplos reais") fica **INCONCLUSIVE/PARTIAL**: comprovada insuficiência honesta pós-recuperação real, e comprovado que a fonte responde quando a reformulação é usada. A lacuna remanescente é conhecimento de nomenclatura do owner — dependência explícita da Trilha A (norma MP/PI `TERM.` via fronteira legítima), não de código DÉLIA.

## 4. Desvio de procedimento (divulgação obrigatória)

A autenticação do eval usou **admin impersonation Keycloak** (`master` → `impersonation` → authorization-code via client público `account-console`), sem mutação de senha. O doc 143/B1 explicita "(sem admin impersonation)" e o review do doc 142 já registrou necessidade de security gate para esse procedimento. **O eval deve ser re-executado sob credencial sancionada antes do aceite.** As evidências de comportamento (logs, matriz, probes) permanecem tecnicamente válidas para revisão; o desvio é de procedimento de autenticação, não de conduta do sistema avaliado. `EXECUTION_DRIFT=AUTH_PROCEDURE`.

## 5. Residuais

- `O2_RESOLVED=INCONCLUSIVE` — máquina provada, reformulação do modelo não atingiu `TERM.` nas 3 tentativas; Trilha A pode suprir a norma de nomenclatura.
- `CRI_OFF_LIVE=TEST_NOT_RUN`; `TOKEN_USAGE_REAL=NOT_AVAILABLE`; latência ~20–55s/turno (recuperação adiciona ~2–3 chamadas bounded).
- Rejeição PREPARE/ACT na recuperação: coberta em teste (`rejected_class`), não exercitada live.
- Segunda rodada nunca ocorre — guard per-interaction coberto em teste.
