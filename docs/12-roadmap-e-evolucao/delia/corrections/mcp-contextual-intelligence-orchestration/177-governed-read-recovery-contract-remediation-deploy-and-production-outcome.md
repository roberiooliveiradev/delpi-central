# 177 — Governed READ Recovery · Contract Remediation, Deploy Gate & Production Outcome

**TASK_ID:** `DELIA-C3-GOVERNED-READ-RECOVERY-CONTRACT-REMEDIATION-AND-PRODUCTION-DEPLOY-01`
**Executor:** Cursor / Devin
**Implementation base:** `2615d9d97bb2dbfb45726642a971ab91c25dafbd` (doc 176)
**Revisão independente:** doc 176 §12 — VERDICT=REWORK for production candidacy
**Status:** rework de contrato concluído; deploy **bloqueado por gates** (ver §8).

---

## 1. Reancoragem

| Campo | Valor |
|---|---|
| BASE_HEAD | `6e32573572` (revisão independente do doc 176) |
| ORIGIN_MAIN | `6e32573572` no início da task |
| WORKTREE_STATUS | escopo limpo: 5 arquivos modificados + 1 script + doc + ledger |
| AUTHORITIES_READ | 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25; docs 170–176; revisão §12; ledger |
| CURRENT_PHASE | C3 — CP/RQ não avançado |

## 2. Revisão independente → rework exigido

O §12 do doc 176 bloqueou:

1. **Contrato permissivo (blocker):** `_owner_recoverable_rejection_hint` tratava qualquer 400/422 com envelope compartilhado e `message` não vazia como rejeição recuperável — ausência de `recoverable:false` não é declaração.
2. **Cobertura fabricada:** `returned_count=0` quando `facts=None` era indistinguível de página vazia autoritativa.
3. **Dedup:** verificar escopo por capability (revisão pediu comprovação).
4. **Comparação não pareada:** flakes de admissão impediram baseline×candidato no mesmo caminho.
5. **Gate de segurança (doc 174):** pendente, bloqueia clearance produtivo independentemente.

## 3. WP1 — Correção do contrato de erros

### Mecanismo do owner (inventário real)

`api-delpi/app/core/responses.py::error_response(message, status_code, *, code=None, recoverable=True, fields=None)` emite `error: {"code", "recoverable"}` **somente quando `code` é informado**. O owner já usa a declaração deliberadamente: `not_found_response` (recoverable=False), `BRANCH_FORBIDDEN` (False), `SCHEMA_OUTDATED`/`PERSISTENCE_ERROR` (True), `VALIDATION_ERROR` (em rotas de lançamento — código tipado publicado para validação de requisição), `recoverable=exc.status_code in {400,409,422}` (semântica por status).

### Regra corrigida (`http_invoker.py`)

Recuperável **somente** quando existe evidência contratual legítima:

- `error.recoverable is True` — declaração explícita (Alternativa A); **ou**
- `error.code` ∈ `_OWNER_ARG_VALIDATION_CODES = {"VALIDATION_ERROR"}` — código tipado publicado pelo owner, sem negação (Alternativa B).

Fail closed em: 400/422 sem bloco `error`, bloco sem `recoverable:true` e sem código validação, `recoverable:false`, código não-tipado, body não-Mapping, `success != false`, ausência de `message`, qualquer outro status. 401/403 permanecem `mcp_authorization_denied`; 429/5xx permanecem `openapi_invocation_failed` sob a política técnica existente.

**Nenhuma inferência por texto de mensagem, regex de produto ou lista local de erros.**

### Consequência contratual obrigatória

A rota real `GET /products/search` (api-delpi `product_routes.py:237`) responde `error_response(msg, 400)` **sem `code`** → `error:null`. Sob o contrato corrigido essa rejeição é **terminal** — a recuperação READ reparável só dispara quando o owner anotar a rejeição de argumento (mínimo: `code="VALIDATION_ERROR"` ou equivalente + `recoverable`).

**`OWNER_DECISION_REQUIRED` (api-delpi):** anotar rejeições contratuais de argumento com `error.code`/`recoverable`. Mudança de contrato do owner não autorizada nesta task → **deploy do comportamento reparável permanece bloqueado enquanto a dependência estiver aberta** (task §4.4). O rework em si é fail-closed-safe: só restringe o que já existia.

## 4. WP3 — Revisão da recuperação existente

| Item | Resultado |
|---|---|
| Dedup por capability | **Verificado:** `_recover_relevance` fixa `sel_descriptor`/`sel_group_key` antes do loop de reparo; toda re-invocação usa a mesma capability; comparação com `prior_arguments` já é gated por `same_capability`; `prior_candidate` é loop-local. Args iguais em capabilities distintas nunca se confundem — não há cross-capability false dedup. |
| Budget | Teto = 2 re-invocações dentro da MESMA rodada única de recovery; deadline conferido antes do 2º reparo (`_budget_allows_resolver`); cancelamento/dedup/identifier-provenance revalidados por proposta. |
| Resultado pós-recuperação | Outcome recuperado retorna ao pipeline normal e é re-julgado por `goal_evidence_relevance` antes de síntese — sucesso técnico ≠ pertinência (prova: sequência de proposals nos testes). |
| Cobertura desconhecida | `returned_count` agora `null` quando `facts=None` (era `0`); `total_count`/`coverage_complete`/`explicit_empty` já eram `null`. Nenhum campo fabricado. |

## 5. WP2 — RED → GREEN

**RED no impl doc-176 (B0):** os 3 testes da matriz estrita falham exatamente nos casos permissivos —
`undeclared_400 → owner_argument_rejected` (deveria ser terminal), `untyped_code_400 → rejected`, `bare_422 → rejected`. GREEN no rework.

**Adapter (+9 testes):** declared `recoverable:true` → rejected+hint; typed `VALIDATION_ERROR` 400 e 422 → rejected; undeclared envelope → `openapi_invocation_failed`; untyped code → terminal; `recoverable:false` → terminal; `recoverable:false` vence código; bare 422 → terminal; bare 400 sem envelope → terminal.

**Orquestrador (+1):** `test_recovery_feedback_unknown_coverage_when_no_facts` — rejeição no primeiro invoke → feedback com coverage todo `null` + `owner_error.owner_hint` sanitizado.

## 6. WP4 — Avaliação pareada B0 × B1

Harness `delia-api/scripts/governed_read_contract_eval.py`: `FakeProposalModel` (entrada controlada, proposals idênticos) → orquestrador real + instruções/CRI reais → **adapter HTTP real** → `http_get` falso com envelopes enfileirados. Mesmos argumentos iniciais, mesma rejeição do owner, mesma proposta de reparo — flake de admissão eliminado por design. O MESMO script roda nas duas árvores.

| Cenário | B0 (`2615d9d97b`) | B1 (rework) | Veredito |
|---|---|---|---|
| undeclared_400 | SUCCESS, 2 wire calls (recuperou sem declaração) | SOURCE_UNAVAILABLE, 1 call | **B0 = o blocker; B1 fail-closed** |
| untyped_code_400 (`BUSINESS_RULE`) | SUCCESS, 2 calls | terminal, 1 call | **B1 correto** |
| bare_422 | SUCCESS, 2 calls | terminal, 1 call | **B1 correto** |
| declared `recoverable:true` 400 | SUCCESS, 2 calls | SUCCESS, 2 calls | recuperação legítima preservada |
| `VALIDATION_ERROR` 422 | SUCCESS, 2 calls | SUCCESS, 2 calls | preservada |
| `recoverable:false` | terminal, 1 call | terminal, 1 call | inalterado |
| 403 | AUTHZ_DENIED, 1 call | AUTHZ_DENIED, 1 call | fail-closed |
| 500 | SOURCE_UNAVAILABLE, 1 call | idem | política técnica inalterada |
| rejeição declarada persistente | 2 calls, bounded stop (dedup) | 2 calls, bounded stop | teto/dedup inalterados |
| coverage sem facts | `returned_count: 0` | `returned_count: null` | **B1 honesto** |

**`MATCHED_EVAL` conclusivo:** entrada idêntica, wire idêntico — B0 re-executava em erros não declarados (risco bloqueante); B1 fecha e preserva recuperação apenas sob declaração legítima. `FALSE_POSITIVES=0, FABRICATED_RECORDS=0, UNAUTHORIZED_RETRIES=0, UNBOUNDED_LOOPS=0`.

## 7. WP5 — Regressão

- Arquivos tocados: 81 testes verdes (adapter + relevance/recovery).
- Suíte completa `delia-api/tests/`: **única falha = `test_cri_instruction_variant_carries_requirements_clause` — `PRE_EXISTING_CRI_CONTRACT_DRIFT`** (idêntica ao HEAD base; v24 embute `answer_requirements` inline e a cláusula CRI injeta de novo). Não afeta o comportamento publicado deste diff — residual do owner da instrução/CRI; não corrigida nem mascarada.
- `audit_architecture_phase3 --base HEAD --check`: OK.
- Residual search: 17 catch sites revisados (doc 176 §7) — a mudança de classificação é mais estrita; nenhum caminho passa a recuperar mais do que antes.

## 8. WP6/WP7 — Gates de deploy

| Gate | Estado |
|---|---|
| Contrato de recuperabilidade | corrigido localmente; **dependência owner aberta** — api-delpi não anota `error.code`/`recoverable` na rejeição de `product_type` → sem deploy do comportamento reparável (§4.4 da task) |
| RED/GREEN + regressão | PASS (única falha pré-existente documentada) |
| Avaliação pareada | PASS — comparação causal idêntica executada |
| Segurança — `SECRET_EXPOSURE_STATUS` | exposta: contexto OpenRouter + `sessions.db`/WAL (127 matches, plataforma Devin) |
| `LOCAL_CLEANUP_STATUS` | DONE (doc 174) |
| `EXTERNAL_EXPOSURE_STATUS` | **UNREMEDIATED** — só rotação contém |
| `SECURITY_OWNER_DECISION` | **nenhuma ratificação registrada** no ledger |
| `RISK_ACCEPTANCE_STATUS` | `RISK_ACCEPTANCE_PENDING_SECURITY_OWNER` |
| `RELEASE_SECURITY_GATE` | **BLOCKED** — sem evidência de remediação suficiente nem aceitação formal |

**`DEPLOY_BLOCKED_SECURITY_GATE` + `OWNER_DECISION_REQUIRED` → deploy NÃO executado.** Runtime produtivo preservado (v24/kimi-k3 inalterado). A correção local aprovada é publicada sem afirmar entrada em produção (task §14).

## 9. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `delia-api/app/infrastructure/openapi/http_invoker.py` | `_owner_recoverable_rejection_hint` exige declaração explícita; `_OWNER_ARG_VALIDATION_CODES` com código publicado pelo owner |
| `delia-api/app/application/capability_provision/contracts.py` | docstring da constante alinhada ao contrato estrito |
| `delia-api/app/application/capability_provision/orchestration.py` | coverage `returned_count` null quando facts ausentes |
| `delia-api/tests/test_openapi_capability_provider.py` | matriz contratual reescrita (9 cenários) |
| `delia-api/tests/test_goal_evidence_relevance.py` | +teste de cobertura desconhecida |
| `delia-api/scripts/governed_read_contract_eval.py` | harness pareado B0×B1 |
| doc 177 + `execution-ledger.md` | evidência factual |

## 10. Rollback / segurança

- Rollback do diff: `git revert` — o rework só restringe classificação; reverter restaura o comportamento doc-176 sem efeitos colaterais.
- Zero secrets em logs/testes/doc; eval usa HTTP falso, sem rede, sem modelo.
- AuthZ, WRITE/PREPARE/ACT, Domain authority: inalterados e fail-closed.

## 11. Veredito

**REWORK_CORRECTED / DEPLOY_BLOCKED** — a correção contratual exigida pela revisão está implementada, provada RED→GREEN e validada em comparação pareada idêntica; a promoção a produção fica bloqueada por (a) `OWNER_DECISION_REQUIRED` na anotação de recuperabilidade da Domain API e (b) `RELEASE_SECURITY_GATE` pendente de remediação/ratificação do security owner. Classificação final da task: **INCONCLUSIVE para produção / ACCEPT_WITH_RESIDUAL para o rework local** — ver relatório executor para o veredito consolidado.
