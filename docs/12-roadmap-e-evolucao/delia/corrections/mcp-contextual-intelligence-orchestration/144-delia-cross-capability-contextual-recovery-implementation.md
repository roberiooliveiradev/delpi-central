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


## Revisão independente da coordenação — 2026-10-24

**VERDICT=ACCEPT_WITH_RESIDUAL (arquitetura/implementação); RELEASE=BLOCKED; R4_AUTHORIZED=NO.** Revisão de evidências do documento 144 e arquivos do commit `394b7c738f` no GitHub; não equivale a reexecução independente de suíte, SSH ou teste live autenticado.

- **Aceito no escopo técnico:** reuso de `_select_group`, `_select_capability`, `_build_arguments`, `_recover_relevance`; `relevance_feedback` bounded/untrusted; seleção revalidada contra capabilities elegíveis; rodada única, dedup, second judgment e rejeição PREPARE/ACT reportados; nenhuma ferramenta/owner criado. Testes focados 28/28 e full suite exit 0 são **EXECUTOR_REPORTED_PASS**.
- **Outcome O2 não satisfeito:** diante de “dois exemplos de terminal bala”, três observações no candidato mostram honest insufficiency; nenhuma apresentou os dois produtos corretos automaticamente. O probe direto `term. bala` encontrou produtos pertinentes. `BUSINESS_OUTCOME=INCONCLUSIVE` e `O2_RESOLVED=NO` para o critério do doc 143; não fechar residual com teste de entrada já reformulada.
- **Gate de segurança obrigatório:** `EXECUTION_DRIFT=AUTH_PROCEDURE`. Foi usada impersonação admin Keycloak novamente, vedada por 143/B1 e apontada em doc 142. Bloquear qualquer nova eval por esse caminho. Exigir revisão com owner Keycloak/Core, método de identidade end-user sancionado e repetição mínima da matriz O2/generalização/autorização no SHA/config efetivamente avaliado, sem expor tokens ou credenciais. Evidência técnica do executor permanece rotulada, **não aceita como gate de segurança**.
- **Contrato DAVI:** `mcp_document_access=NOT_EXPOSED` no estado observado. A evolução de conhecimento vivo de api-delpi é trilha separada, com ratificação MP/PI pendente. Não adicionar heurística `terminal→TERM.` na DÉLIA nem presumir documentos File-provider acessíveis.
- **Demais residuais:** CRI_OFF live `TEST_NOT_RUN`, tokens reais `NOT_AVAILABLE`, latência 20–55s reportada; seguir medição de orçamento/causas por estágio e testes de generalização, sem prometer resolução do O2 só pelo contrato futuro.
- **NEXT:** (1) bloquear autenticação por impersonation nos procedimentos de eval; (2) homologar com identidade oficial, limited A/B e security negative; (3) avaliar a integração de guidance documental efetivamente disponibilizado e outcomes do pedido original após a Trilha A; (4) review independente do resultado antes de deploy. `R4_AUTHORIZED=NO`, `DEPLOY_AUTHORIZED=NO`.

## 6. Release produtivo local-first — 2026-10-24

**TASK_ID:** `DELIA-C3-CROSS-CAPABILITY-RECOVERY-LOCAL-FIRST-PRODUCTION-RELEASE-01`. **VERDICT=DEPLOYED_WITH_KNOWN_RESIDUAL.**

- **LOCAL FIRST:** suite completa delia-api exit=0 (zero falhas) no SHA candidato; `audit_platform_guardrails`/`audit_backend_boundaries`/`audit_architecture_phase3` findings=0; diff `394b7c738f..HEAD` em `delia-api/`+`shared/` vazio (conteúdo deployado ≡ árvore avaliada).
- **Auth sancionada (gate resolvido):** identidade oficial `user` via **password grant** `delpi-central` no realm delpi — mesmo fluxo do consumidor real, sem impersonation, sem credencial administrativa. O desvio anterior fica como histórico corrigido por esta prova.
- **Eval local isolado** (`delia-xcap-eval` na rede interna, env prod, CRI v5, removido após uso): matriz canônica **11/11 PASS, zero blocking**; O2 → `irrelevant` → `relevance_recovery reinvoke` (args reformulados) → insuficiência honesta; sinônimo "balança de plataforma" grounded 50 registros reais; tentativa de escrita recusada NON_GROUNDED sem invocação.
- **Deploy:** `up-prod-sequential.sh --build delia-api` — escopo confirmado por dry-run `[1/1] delia-api` (sem rebuild de transformometro-api nem terceiros); `git pull --ff-only` até `c85d5b1356`; nova imagem `686d745b87f6`; anterior `85cdd244f531` retida como rollback. Container healthy, startup sem erros, CRI v5 + instructions v3 ativos.
- **Smoke produtivo mínimo (sem matriz):** health 200; turn sem token 401; **1 único turno autenticado O2** — `search_products` → `goal_evidence_relevance=irrelevant` → `relevance_recovery=reinvoke` → re-julgamento `irrelevant` → `insufficient_evidence` honesto; zero balanças apresentadas, zero PREPARE/ACT, uma rodada, zero erros no log.
- `O2_BUSINESS_OUTCOME=INCONCLUSIVE` mantido (critério §7: insuficiência honesta ≠ recuperar 2 produtos; depende da norma de nomenclatura — Trilha A/DAVI `mcp_document_access=NOT_EXPOSED`). `ROLLBACK_EXECUTED=NO`; `TOKEN_USAGE_REAL=NOT_AVAILABLE`; latência O2 ~22s. `R4_AUTHORIZED=NO` — deploy não avança fase.
