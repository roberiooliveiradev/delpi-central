# INT-1 — Model-Agnostic Production Outcome Reconciliation and Final Independent Acceptance

**TASK:** `DELIA-C3-T2-INT1-MODEL-AGNOSTIC-PRODUCTION-OUTCOME-AND-FINAL-ACCEPTANCE-01`
**Data:** 2026-11-13 · **Base:** `19ef59cf90` (=origin/main após ff; REFERENCE `c6bc49290b` era HEAD válido no início)
**Escopo:** reconciliação model-agnostic dos outcomes produtivos + classificação formal de P2 + submissão à decisão independente de fechamento. **Sem novo código de inteligência, sem novo deploy, sem troca de perfil/modelo.**

## 1. Reancoragem

- `HEAD` inicial `c6bc49290b` (minha Publication B); `origin/main` avançou → `19ef59cf90` (it-portal SEC + docs engineering — alheio à INT-1); ff-only aplicado, working tree limpo.
- `PHASE_FROM_16`: C3/T2 — INT-1 com engenharia aceita + deploy executado, aguardando decisão de fechamento.
- `NEXT_FROM_LEDGER`: `COORDINATION_INT1_PRODUCTION_OUTCOME_INDEPENDENT_ACCEPTANCE_REVIEW`.
- `ENGINEERING_ACCEPTED_SHA=413baef618` · `PRODUCTION_RELEASE_SHA=b8a31f8c12` (árvore deployada ≡ código do release) · `PRODUCTION_RUNTIME_PROFILE=openrouter_kimi` (reportado corretamente no Doc 321).

## 2. Decisão arquitetural — model-agnostic (ratificada, inalterada)

DÉLIA é standalone COI; o modelo é dependência substituível por configuração. `AGENT_COUNT=1` · `PYDANTIC_AI_NATIVE=YES` · `MCP_TOOLSET_LIVE=YES` · `NEW_ROUTER/PLANNER/RESOLVER_ENGINE=NO` · `PROVIDER_SPECIFIC_PLANNER_RULES=NO` · `RBAC_MUTATION=NO`. Ownership preservado: Keycloak=identidade · Core=autorização · Domain APIs=autoridade de negócio · DÉLIA=política de evidência/outcome · MCP=interop.

**Nenhuma adaptação específica de Qwen/Kimi foi criada.** Os dois fixes da rodada anterior (`c774b45655`, `50d107b3ba`) foram exclusivamente no **harness de eval** (parâmetros de ambiente), não no runtime.

## 3. Runtime produtivo ativo — inspeção efetiva (container `delpi-delia-api`)

| Invariante | Valor efetivo | Veredito |
|---|---|---|
| `ACTIVE_MODEL_REPORTED_CORRECTLY` | `openrouter_kimi` / `moonshotai/kimi-k3` (fp `fd70f7df67a06954`) | YES — confere com Doc 321 |
| `PYDANTIC_AI_RUNTIME_ACTIVE` | `pydantic_ai 2.50.0` | YES — idêntico ao perfil avaliado |
| `MCP_TOOLSET_CONTRACT` | registry `core`; davi/teo/vista `ENABLED=true`; `Host: minhadelpi.com.br` ×3 | YES |
| `CORE_AUTHZ` / exchange | `DELIA_EXCHANGE_CLIENT_ID=delia-api`; delegated `mcp:tools` 200 provado | YES |
| `EVIDENCE_POLICY` / `OUTCOME_CONTRACT` | mesma revisão de código deployada (instrução/outcome layer são code-frozen, não perfil-dependentes) | YES |

Perfil produtivo **não modificado** (`PRODUCTION_MODEL_CHANGE=NOT_AUTHORIZED` respeitado). A diferença kimi (serviço) × qwen (eval isolado) é diferença de provider, não de contrato — registrada como residual externo, conforme §4 da task.

## 4. Investigação P2 — classificação formal

Pergunta: *"Quais processos de transformação estão cadastrados?"* — trace real `or-qwen14b-49cc26d53beb` / `P2_processes_registered`:

```text
SELECTED_OWNER=TEO · TOOL=read · ARGS={entity:process, action:search, params:{q:"transformação"}}
OWNER_RESPONSE={success:true, data:{total:1, items:[PROC-0001 ...]}}
DECLARED_STATUS=complete · GROUNDING=GROUNDED · epistemic=OBSERVATION
LIMITATIONS=[coverage_unknown ×2, declared_status_overridden,
  declared_limitation:"...apenas 1 processo foi encontrado com o termo 'transformação'...
  pode-se refinar a busca com filtros adicionais como filial, setor ou familia_processo"]
```

**Análise:**

- `params.q="transformação"` é **model-authored** — a regra v2-3 de intenção de enumeração (Doc 316) prescreve enumeração sem filtro inventado; o termo veio da própria formulação do usuário ("processos de transformação"), tornando o filtro defensável mas restritivo em cobertura.
- Owner respondeu autoritativamente `total:1` para aquele filtro — `OWNER_RESULT_COVERAGE` é verdadeira para a query emitida.
- O modelo declarou `complete`, mas a camada de Outcome **não promoveu completude**: `plan=None` → `declared_status_overridden` + `coverage_unknown` — a declaração COMPLETE fica honestamente marcada como não-provada (ver `_synthesize` em `semantic_capability_support.py`).
- A resposta ao usuário apresenta 1 processo **e** declara a limitação do escopo do filtro, convidando refinamento — proveniência preservada, zero inventividade.

**Classificação: CASO B — cobertura parcial honesta.**

```text
P2_GROUNDING=GROUNDED
P2_COVERAGE=PARTIAL
P2_OBJECTIVE_SATISFACTION=PARTIAL
P2_OUTCOME_HONEST=YES
```

Não é Caso C: `declared_status_overridden`+`coverage_unknown`+`declared_limitation` são os marcadores honestos do Outcome layer — a "completude" não foi apresentada sem ressalva. Não é Caso A: a cobertura sob o objetivo estrito de enumeração é parcial (1 de N). Não é Caso D: trace completo permite verificação ponta-a-ponta. A tensão status-declared × cobertura é o residual já registrado `INT1-ATTEMPT-STATUS-CONFLATION` (OPEN_MINOR) — a camada de Outcome a trata corretamente.

Comparativo de homologação: Doc 317 registrou `total=109` com params vazios no ambiente de eval dev (corpus diferente). Em produção a query emitida foi filtrada — não é regressão de código; é diferença de escolha cognitiva dentro do contrato.

## 5. Contratos de governança — preservados sob evidência produtiva

`AUTHENTICATION≠AUTHORIZATION` (raw subject 401 vs delegated 200) · `DISCOVERY≠APPROVAL` (tools/list ≠ grant) · `READ≠WRITE`/`PREPARE≠ACT` (somente caps read-family invocadas; write-class não implementadas na superfície) · `TECHNICAL_SUCCESS≠BUSINESS_OUTCOME` (distinção mantida em todas as finalizações) · `MODEL_OUTPUT≠DOMAIN_AUTHORITY` (hallucination guard: tokens numéricos exigem verbatim na evidência — ativo no código deployado).

## 6. Residuais — reconciliação de materialidade

| Residual | Owner | Material p/ INT-1 | Disposição |
|---|---|---|---|
| INT1-ATTEMPT-STATUS-CONFLATION | DÉLIA | **NO** — Outcome layer já marca `declared_status_overridden`/`coverage_unknown`; sem apresentação de completude indevida | OPEN_MINOR, mantido |
| INT1-MCP-HEAVY-VIEW-TIMEOUT | DÉLIA/owners | NO — reliability não-bloqueante; P1/P2/P3 provados | OPEN_MINOR |
| INT1-DAVI-NONEXECUTABLE-CAPS | DAVI | NO — caps não-executáveis fora da superfície read homologada | OPEN (owner DAVI) |
| INT1-EVAL-ENV-FLAKES | Eval | NO — ambiente de eval, não runtime | OPEN_OPERATIONAL |
| INT1-PROD-RUNTIME-PROFILE (novo, Doc 321) | Ops/PO | NO — model-agnostic por decisão PO; contratos preservados | OPEN_EXTERNAL |
| INT1-SEC01-API-DELPI | SEC-01 task | NO — task independente, fora de escopo | OPEN_EXTERNAL |

`ZERO_OPEN_MATERIAL=YES` sob o critério do Doc 293.

## 7. Gates e estado formal

```text
L_GATE=PASS · A_GATE=PASS · O_GATE=PASS · R_GATE=PASS (Doc 321, evidência válida)
ENGINEERING_ACCEPTANCE=ACCEPT
PRODUCTION_DEPLOY_EXECUTED=YES (4 serviços, healthy/running)
PRODUCTION_RUNTIME_VALIDATION=PASS (or-qwen14b-49cc26d53beb)
BUSINESS_OUTCOME_ACCEPTANCE=P1 GROUNDED/complete · P2 GROUNDED/partial-honest · P3 GROUNDED/complete
NO_AUTHORITY_DRIFT=YES · OUTCOME_EVIDENCE_VALID=YES
```

`PRODUCTION_VALIDATION=PASS` e o outcome empresarial foram **reportados com evidência** — a decisão `INT1_FINAL_ACCEPTANCE` e `INT1_CLOSED` pertencem à revisão independente da coordenação, **não ao executor**.

## 8. Estado

```text
INT1_FINAL_ACCEPTANCE=SUBMITTED_FOR_INDEPENDENT_REVIEW
INT1_CLOSED=NO (aguarda decisão independente — §10 do protocolo)
PHASE_ADVANCEMENT=NO
INT2/INT3/T3=NOT_AUTHORIZED
NEW_PRODUCTION_DEPLOY=NO
NEXT=COORDINATION_INT1_FINAL_INDEPENDENT_ACCEPTANCE_DECISION
```

**Pacote completo submetido:** Docs 317–322 + traces `or-qwen14b-e069f3b33be8` (homologação dev) e `or-qwen14b-49cc26d53beb` (produção) + imagens/deploy registrados + residuais classificados. Nenhum defeito material da DÉLIA identificado nesta reconciliação.
