# 142 — Correção transversal de pertinência semântica + recuperação governada (O2)

- **Task**: `DELIA-C3-SEMANTIC-RELEVANCE-GOVERNED-RECOVERY-CROSSCUTTING-01`
- **Implementação**: `58a7e873c6` (sobre `2e15682b8c`)
- **Autoridade**: adendo prioritário do plano 125 + revisão independente R3 `aac88d40f6` (O2) + PO
- **Escopo**: `delia-api` — implementação + testes locais + A/B isolado. Deploy **não** autorizado.

## 1. Problema reproduzido

`"2 exemplos de terminal bala"` retornou GROUNDED com registros **reais de balanças** apresentados como resposta. Evidência viva no lado A do eval: `GROUNDED OBSERVATION` + `Aqui estão 2 exemplos: BALANCA BALMAK 1000KG…`. Dado real, JSON válido, HTTP 200 — **pertinência não comprovada**.

**Primeiro estágio responsável**: `assess_outcome`/`OutcomeVerdict` declara `answered` assim que há evidência empresarial saneada — pertinência ao objetivo era responsabilidade de um caller inexistente (constatado no adendo do plano 125).

## 2. Owner e contrato (EXISTING_EQUIVALENT=YES_PARTIAL, REUSE_DECISION=EXTEND)

Nenhuma autoridade nova. Estendidos os owners existentes:

- **`outcome_assessment.py`**: novo contrato `GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID` +
  `REASON_GOAL_MISMATCH` / `REASON_RELEVANCE_UNPROVEN` + bounds
  (`MAX_EVIDENCE_RECORD_CHARS`, `MAX_MISMATCH_HINT_CHARS`).
- **`orchestration.py`**: edge pós-`projected_answer` — quando CRI ativo + evidência
  empresarial + classe resumível (DISCOVERY/READ/ANALYSIS), **uma** chamada LLM
  bounded julga `{user_message, goal, evidence}` → `corresponds|irrelevant|uncertain`.
- **Recuperação governada** (`_recover_goal_evidence_relevance`): `irrelevant`/`uncertain`
  → no máximo **uma** rodada READ na mesma capability — re-proposta de argumentos pelo
  estágio legítimo `_build_arguments` com bloco `relevance_feedback`, revalidação pelo
  `_invoke_selected`, re-julgamento único, guard `_RELEVANCE_RECOVERY_USED`
  (contextvar por interação, set/reset em `attempt()`). Argumentos idênticos ⇒
  **não re-executa** (fail-closed). Sem ampliação de autorização; PREPARE/ACT
  retornam antes do edge (invariante preservado).
- **Fail-closed**: mismatch persistente ou pertinência não provada →
  `goal_mismatch`/`relevance_unproven` → `OUTCOME_INSUFFICIENT` →
  `LIMITATION_INSUFFICIENT_EVIDENCE`. O julgamento **nunca** vira FACT nem autorização.
- **`conversational_response.py` + `cri_presentation.delpi.json` v5**: mensagens
  `goal_mismatch`/`relevance_unproven` (pt-BR); `orchestration_instructions.delpi.json`
  v2 com instrução `goal_evidence_relevance` + semântica `relevance_feedback` no
  estágio `arguments`; loader aceita v5/v2 (`cri_instruction_resource.py`).

## 3. RED→GREEN + regressão

- `tests/test_goal_evidence_relevance.py` — **23 testes** (irrelevant→recovered,
  synonyms, partial, ambiguous, failed recovery, boundary PREPARE/DISCOVERY,
  injection-in-hint, ANALYSIS sibling, identical-args no-reinvoke). RED confirmado
  antes da implementação (collection falhava no contrato ausente).
- Suíte completa: **2225 passed / 3 skipped** (baseline 2202 + 17 fixtures de
  evolução de contrato ajustados: snapshot r1, versões vocab sa/e3, chaves de
  fila do fake e2/e3 — asserção zero-model-calls ON→`≤ +1` bounded).
- Gates arquitetura: `audit_platform_guardrails` 0 findings,
  `audit_backend_boundaries` 0 findings, `audit_architecture_phase3` OK,
  import DAG limpo (composer carrega). CRI OFF intocado (edge só existe com CRI ativo).

## 4. A/B isolado — kimi-k3 produtivo

- **A** = prod `delpi-delia-api` `85cdd244f531` (R3). **B** = `delia-api-semrel-eval:58a7e873c6`
  (`sha256:654a23fc2532`), env byte-idêntico, `infra_delpi-network`, **sem portas
  publicadas**, removido pós-eval. Identidade sancionada `user` via token subject
  (impersonation session + authorization-code; **zero mutação** de Keycloak/prod).
- **Matriz `r1r2_integrated_eval`**: **A 11/11 PASS × B 11/11 PASS** — mesmas
  capabilities, mesmo grounding, latências equivalentes (1,5–19,6s).
- **O2 — divergência intencional (o fix)**:
  - A: `GROUNDED` + apresenta `BALANCA BALMAK…` como resposta (bug reproduzido).
  - B: `GROUNDED` mas **retém honestamente**: *"A fonte retornou registros reais,
    mas eles não correspondem ao que foi pedido — não vou apresentá-los como
    resposta"* + `insufficient_evidence`.
  - Logs B provam o caminho governado: `goal_evidence_relevance decision=irrelevant`
    → `relevance_recovery decision=identical_arguments` (sem re-execução)
    → `outcome_assessment decision=insufficient reasons=goal_mismatch`.
- **Sinônimo** (`"2 exemplos de balança"`): A × B retornam os mesmos registros
  reais — **sem over-block** (`decision=corresponds`).
- **Probes**: injeção de escrita recusada nos dois lados; `gen_empty` honesto em
  ambos (B: `coverage_unproven`); `gen_unknown_material` variação provider/modelo
  honesta (A GROUNDED × B `delpi_source_unverified`); `o3` `owner_path_unbound` ×2.
- Zero ERROR/Traceback em B. Overhead do julgamento: ~0,9–2,4s por chamada.
- `TOKEN_USAGE_REAL=NOT_AVAILABLE` (provider não expõe contagem).

## 5. Residuais

- O2 com kimi-k3 resolveu via `identical_arguments` fail-closed (não exercitou
  re-invocação com args distintos em live; caminho coberto em teste).
- `relevance_feedback` depende de o modelo re-propor argumentos distintos —
  bounded pelo guard; pertinência não provada sempre degrada honestamente.
- `n1_contextual` na rodada B de probes: 401 (TTL do bearer expirado); n1 já
  PASS na matriz B — sem impacto.
- CRI OFF live: `TEST_NOT_RUN` (toggle exigiria restart prod; semântica por suíte).
- Deploy pendente de autorização; aceite independente pendente da coordenação.

## 6. Veredito do executor

`RELEASE_READINESS=EVIDENCE_READY_FOR_REVIEW` — correção transversal
provider-neutral implementada, testada e validada A/B com modelo produtivo;
nenhuma engine/autoridade paralela criada. `DEPLOY_STATUS=NOT_EXECUTED`.
`EXECUTION_DRIFT=NONE`. `R4_AUTHORIZED=NO`.
