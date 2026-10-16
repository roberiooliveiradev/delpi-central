# 22 — Revisão complementar e correção da confirmação inválida (Etapa 02/B2)

**DATA:** 2026-10-16  
**TASK:** DELIA-C3-STAGE-02-B2-PENDING-INVALID-CLAIM-REWORK-01  
**BASE_REMOTE_HEAD_AFTER_IMPLEMENTATION:** `9bc63c2bf799a891366b13d69d5bb0a8a98ce855`  
**MODE:** implementação bounded via GitHub connector + static source review; **sem checkout local**, sem pytest/vitest/browser executados.  
**VERDICT:** `CODE_CHANGE_RECORDED`; `TESTS=TEST_NOT_RUN`; `INDEPENDENT_REVIEW=PENDING`; `B2=NOT_ACCEPTED`; `STAGE_02_ACCEPTED=NO`.

## 1. Reancoragem e escopo

Authorities: Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02 → 24 → 60/69/70/personality → ledger §§6.126/6.130/6.133/6.140/6.141/6.145/6.183–6.188. Documento [18](./18-execution-scope-architecture-contract-closure.md) continua contrato de direção B2. [20](./20-stage-02-b2-independent-implementation-review.md) identificou RW-01/RW-02/UX-01; [21](./21-stage-02-b2-postreview-concurrency-contract-ux-rework-report.md) registra correções já publicadas na main **antes deste task**, com testes ainda TEST_NOT_RUN.

O GitHub remoto **já** contém: `PendingWriteStore.take_if_current` com `RLock` e identity claim, `command_type` propagado até Application com validação direta, e cartões pendentes preservados após MESSAGE não relacionada. Por isso não reaplicar essas correções nem relatar que foram implementadas nesta task.

## 2. Novo defeito encontrado (PROVEN por inspeção de código)

Em `OperationalCapabilityOrchestrator._confirm_proposal`, a versão pós-RW-01 verificava `bind_confirmation`, mas **executava `take_if_current` antes de verificar se `bound.state` era `INVALIDATED`/ `EXPIRED`**. Uma confirmação com digest correto e fingerprint errado poderia vencer o claim, consumir o pending e só então retornar `confirmation_mismatch`, impedindo uma confirmação legítima posterior. Isso não permitia ACT indevido; era um problema de integridade e disponibilidade da operação preparada. Uma rejeição por outro ator já passava pelo gate `actor_mismatch` anterior.

**Correção limitada:** validar `bound.state in {CONFIRMED, REJECTED}` **antes do claim**, com auditoria de `CONFIRMATION_INVALID` e `WRITE_REJECTED/confirmation_mismatch` sem retirar o pending. Somente CONFIRMED/REJECTED válidos disputam `take_if_current`, e somente o vencedor pode continuar para governança de ACT. Não segurar lock durante rede/owner. Sem alteração no contrato D1/D2/D3, Policy/Decision, Core/Domain ou owner confirmation.

## 3. Alterações publicadas

- `d1028e2bf11b235b8dbbc4b578d162be710d965b`: duas novas regressões em `delia-api/tests/test_stage02_b2_concurrent_decisions.py`; confirmação com fingerprint incorreto não deve consumir pending, e REJECT de outro actor não deve cancelar.
- `2916804e25899df625660c2938b9e955f4966e7e`: correção em `delia-api/app/application/capability_provision/orchestration.py` para invalidar binding antes do claim atômico.
- `9bc63c2bf799a891366b13d69d5bb0a8a98ce855`: ajuste do segundo teste à semântica **existente** de `AUTHZ_DENIED/actor_mismatch` na camada anterior ao `bind_confirmation`.

**Arquivos funcionais alterados nesta correção:** 1 código + 1 teste. Nenhum outro runtime, migration, frontend, MCP ou owner foi editado por esta task.

## 4. Evidência e limites

| Gate | Estado nesta sessão |
| --- | --- |
| Fonte remota dos três fixes originais RW-01/RW-02/UX-01 | `PROVEN` por leitura, entregas anteriores |
| Fonte remota do novo validation-before-claim | `PROVEN` por leitura e commits |
| Duas novas regressões escritas | `PROVEN` existência; resultado `TEST_NOT_RUN` |
| RED reproduzido executando testes | `TEST_NOT_RUN` (não afirmar que ocorreu) |
| Teste concorrente APPLY×APPLY e APPLY×REJECT | `TEST_NOT_RUN` nesta sessão; código/harness já publicados |
| Full `delia-api` pytest, frontend Vitest e tsc/federation | `TEST_NOT_RUN` nesta sessão |
| CI de arquitetura no SHA final | `TO_INVENTORY`, não substitui suíte funcional |
| Browser QA, live model, Domain business Outcome | `TEST_NOT_RUN` |
| Local git status / produção multi-worker | `TO_INVENTORY` (GitHub connector não oferece checkout ou runtime) |

**Execução mínima obrigatória em checkout limpo para revisão independente:** 
`cd delia-api && pytest -q tests/test_stage02_b2_concurrent_decisions.py tests/test_interaction_runtime.py tests/test_stage02r2_execution_bound_diagnosis.py`; depois `pytest` full. Em `plugins/delia`, `vitest run`, `tsc -p tsconfig.app.json`, `vite build` pelos scripts do projeto. Registrar versions/exits no SHA exato; testar concorrência real contra fakes, single-winner e idempotência. Confirmar semântica de cards em browser. Avaliar topologia multi-worker como `TO_INVENTORY` sem afirmar exactly-once distribuído.

## 5. Reuse, security, NEXT

`EXISTING_EQUIVALENT=YES` (`PendingWriteStore.take_if_current`, `bind_confirmation`, audit gate, harness). `REUSE_DECISION=EXTEND` in-place; sem nova abstração, provider branch ou permission paralela.

**NÃO declarar Stage 02 finalizada**: ainda faltam evidência de execução das regressões no HEAD/config, validação independente, resolução factual do `tsc` relatado FAIL, browser QA e avaliação de Outcomes/generalization quando autorizadas. O código novo aguarda aceitação independente, não a concede a si mesmo. Fase e NEXT continuam com 16+ledger.

`B1=PASS_STRUCTURAL`; `B2_IMPLEMENTATION=EVIDENCE_RECORDED`; `B2_SECURITY_ACCEPTANCE=NO`; `STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`; `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`.
