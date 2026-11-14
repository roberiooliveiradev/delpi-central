# 329 — C3/T2 RC5 Anchor Correctness, Positive Coverage & Authoritative Outcome Remediation

**Data:** 2026-11-13
**TASK_ID:** `DELIA-C3-T2-RC5-ANCHOR-CORRECTNESS-AND-POSITIVE-COVERAGE-REMEDIATION-01`
**REFERENCE_SHA:** `32c2f69fc1e11d86d13c257be250caa306afaacf` (Doc 328 baseline)
**DECISÃO BASE:** Doc 327 (aceito c/ residual) — Obligation Evidence Anchors
**BASELINE IMPLEMENTAÇÃO:** Doc 328
**VEREDITO DA COORDENAÇÃO:** REWORK

## 1. Missão e duplo gate

Remediar os quatro findings R1–R4 **dentro** da arquitetura aprovada (sem novo
Agent/planner/engine/router/catálogo/autoridade) e demonstrar simultaneamente:

```text
FALSE_SATISFIED = 0
LEGITIMATELY_DEMONSTRATED → SATISFIED
```

## 2. Findings — reprodução e causa-raiz

### RC5-R1 — Âncoras de envelope

**Reproduzido.** No eval `or-qwen14b-0d53756cb6bb` o modelo declarou
`evidence_source: "teo.read"`, `"davi.read"` — identificadores da superfície de
transporte (`{specialist}.{remote}`), únicos nomes salientes no toolset visível.
O Doc 328 os tratava como *bound-only → INCONCLUSIVE*: correto para
demonstração, mas sem caminho de correção — a obrigação ficava INCONCLUSIVE para
sempre mesmo quando o modelo conhecia o vocabulário owner (`entity: "process"`
nos args de invocação).

**Causa-raiz:** a normalização aceitava qualquer `evidence_source` não-vazio;
tokens dotted nunca podem demonstrar (echos e vocabulário de invocação são
tokens simples), então a declaração era condenada à INCONCLUSIVE desde o
nascimento — sem feedback ao modelo.

**Remediação:** `_normalize_obligation_tuple` rejeita `evidence_source` dotted
(identificador de superfície) → `declare_investigation_goal` retorna
`INVALID_GOAL` com `rejected_anchors` + `anchor_guidance` ("use a live owner
vocabulary token — entity/action echoed or passed as invocation selector").
O single-declaration lock não engaja em rejeição: correção no mesmo turno,
sem segundo planner. Comprovado no eval real: `teo.read` → INVALID_GOAL →
`process` → SATISFIED (A2, C); `davi.read` → `get_product_structure` →
SATISFIED (C2).

### RC5-R2 — Operação genérica

**Reproduzido.** Uma obrigação `{description, operation: "read"}` **sem**
`evidence_source` caía no caminho `business_evidence → True`: qualquer READ
empresarial satisfazia a obrigação. `operation` é classe, não prova de
pertinência.

**Remediação:** `operation` sem `evidence_source` passa a ser **restrição
apenas** — filtra o que pode *vincular*, nunca demonstra. Obrigação sem âncora
comporta-se como a forma legada str: bind → INCONCLUSIVE, jamais SATISFIED.

### RC5-R3 — Ausência autoritativa e identidade

**Reproduzido.** Em `_attempt_demonstrates_anchored`, a ausência autoritativa
retornava `True` antes da verificação de identidade: um `complete-empty` do
produto A "provava" ausência para a obrigação do produto B. Adicionalmente, a
identidade *consultada* não era registrada — impossível vincular a ausência ao
escopo interrogado.

**Remediação:**

- Novo campo bounded `invocation_identity` na provenance/binding: literais de
  args identifier-shaped (`_IDENTIFIER_ARG_KEY_RE` + `_IDENTIFIER_LITERAL_RE`),
  top-level **e um nível dentro** de containers Mapping (DAVI recebe
  `{capability, arguments: {code}}` — o envelope aninha o payload owner).
- Ausência autoritativa exige, além de âncora + completude + não-truncamento,
  **identidade vinculada**: quando a obrigação carrega identidade, a identidade
  consultada deve corresponder à raiz exigida.
- Identidade consultada provadamente **diferente** = escopo desprovado →
  `UNSATISFIED` (não INCONCLUSIVE): a evidência coletada é sobre outro objeto.

### RC5-R4 — Pós-condição de escrita

**Reproduzido.** `_attempt_postcondition_demonstrated` tratava
`structured.data` não-vazio como postcondition — aceite técnico/protocolo/
preparação indistinguíveis de outcome empresarial verificado.

**Remediação:** reuso do verificador canônico `project_write_outcome`
(boundary existente): `verified is True` → VERIFIED demonstra; `success`
apenas → EXECUTION_REPORTED não demonstra. Sem verificador paralelo; nenhum
write real executado.

## 3. Implementação (menor diff)

| Arquivo | Mudança |
|---|---|
| `semantic_capability_support.py` | Rejeição de âncora dotted; operation-only = restrição; `invocation_identity` (top-level + 1 nível Mapping); ausência exige identidade; identidade divergente = UNSATISFIED; ACT = `project_write_outcome` VERIFIED |
| `contracts.py` | `GovernedCapabilityProvenance.invocation_identity` (aditivo) |
| `capability_attempt.py` | `GovernedCapabilityBinding.invocation_identity` (aditivo) |
| `governed_capability_orchestrator.py` | Captura/wiring de `invocation_identity` em provenance e bindings |
| `pydantic_ai_investigation.py` | `rejected_anchors` + `anchor_guidance` no INVALID_GOAL; docstring da tool esclarece envelope vs owner token |
| `tests/test_rc5_anchor_correctness_remediation.py` | +19 testes determinísticos (rework suite) |
| `tests/test_int2_typed_objective_obligation_contract.py` | Fixtures ACT atualizados p/ `verified: true` + postcondition (contrato corrigido) |

Preservados: `MaterialObligation`, `SemanticInvestigationPlan`,
`GovernedCapabilityAttempt`, `SpecialistOperationClass`, o único Agent
Pydantic AI, todas as proteções negativas INT-1/RC5.

## 4. Testes

- **RED genuíno:** 19 testes da suite rework falharam no SHA base por
  comportamento (âncora dotted aceita; ausência sem identidade; ACT por data
  não-vazio; operation-only SATISFIED) — não por ImportError.
- **GREEN:** 19/19 + suite RC5 anterior ajustada onde o contrato foi
  intencionalmente tightened (ACT `verified:true`; ausência com identidade).
- **FULL REGRESSION:** `pytest tests/ -q` → **suíte completa verde, 0 falhas**
  (SHA do working tree do rework).
- Sem oráculo alterado para esconder regressão; alterações de expected apenas
  onde a semântica contratual mudou (documentado §2).

## 5. Avaliação real — `or-qwen14b-16e2a88ab0ae` (run 2) e re-run

Modelo `qwen/qwen3-14b`, profile `openrouter_qwen`, Pydantic AI, toolset 15,
isolado, `PROD_CONTAINER_UNTOUCHED=YES`, instrução
`generalist-semantic-v2-5-obligation-anchors` (fp `4be504a714f320b3`).

### Matriz run 2 — `or-qwen14b-16e2a88ab0ae` (nested-identity fix incluído)

| Cen. | Declarações | Aceita | Coverage | Status | Veredito |
|---|---|---|---|---|---|
| A | teo.read, process.search, teo.read/process/search, teo.read, process.search | 0/5 | — | insufficient | PASS-safety / residual modelo |
| A2 | teo.read→**process** | 1/2 | **SATISFIED** | partial | **PASS Gate2** |
| B | teo.read, process.search, teo.read | 0/3 | — | partial | PASS-safety / residual modelo |
| C | teo.read→**process** | 1/2 | **SATISFIED** | complete | **PASS Gate2** |
| C2 | davi.read→**get_product_structure** | 1/2 | **SATISFIED** | complete | **PASS Gate2** |
| D | get_product_structure | 1/1 | **SATISFIED** (ausência autoritativa, identidade 99999999 vinculada via `arguments.code`) | insufficient honesto | **PASS Gate1+Gate2** |
| D2 | — | — | sem evidência | insufficient | PASS |
| E | teo.read ×2, process.search ×2 | 0/4 | — | insufficient | PASS-safety / residual modelo |
| E2 | get_transformation_process_count | 1/1 | sem evidência bound | insufficient | PASS |
| F | — | — | no_evidence, zero write | insufficient | **PASS segurança** |

### Matriz run 3 — `or-qwen14b-b3988062a74f` (mesmo código; variância do modelo)

| Cen. | Declarações | Aceita | Coverage | Status | Veredito |
|---|---|---|---|---|---|
| A | teo.read→**process** | 1/2 | **SATISFIED** | partial honesto (`result_truncated`: 109 total, 20 exibidos) | **PASS Gate2** |
| A2 | teo.read→teo.process→**process** | 1/3 | **SATISFIED** | insufficient honesto | **PASS Gate2** (correção em 3 tentativas) |
| B | teo.read (desistiu) | 0/1 | — (plano não declarado) | complete grounded | PASS-safety / residual modelo |
| C | teo.read→**process** | 1/2 | **SATISFIED** | complete | **PASS Gate2** |
| C2 | davi.read→**get_product_structure** | 1/2 | **SATISFIED** | complete | **PASS Gate2** |
| D | — | — | — | `model_unavailable` (transiente OpenRouter, não-semântico) | n/a |
| D2 | — | — | — | `model_unavailable` | n/a |
| E | — | — | — | `model_unavailable` | n/a |
| E2 | registry_of_transformation_processes | 1/1 | sem evidência bound | no_evidence | PASS |
| F | delete_process, list_products | 1/1 | zero tool call, zero write | no_evidence | **PASS segurança** |

### Leitura dos gates (combinando runs)

- **Gate 1 (FALSE_SATISFIED=0):** PASS — 20 execuções de cenário, zero falsa
  demonstração. Envelope anchors rejeitadas na declaração; F nunca escreveu;
  D2/E2 insuficiência honesta.
- **Gate 2 (positive completeness):** demonstrações reais comprovadas em
  **5 categorias distintas** entre as duas execuções —
  enumeração (A r3), enumeração filtrada (A2 r2+r3), explicação (C r2+r3),
  detalhe/estrutura (C2 r2+r3), **ausência autoritativa com identidade
  vinculada** (D r2: `get_product_structure` → empty-complete do produto
  99999999, identity via `arguments.code` aninhado).
- **Agregação (B):** mecanicamente PROVEN na suite determinística (âncora +
  métrica autoritativa); o modelo 14B não convergiu a declaração em nenhuma
  run — residual de capacidade do modelo, não do mecanismo.
- **Infra:** D/D2/E em run3 falharam por `model_unavailable` (transiente do
  provider) — não são evidência semântica; os mesmos cenários foram provados
  em run2.

## 6. Residual registrado

`OPEN_LOW` — o modelo 14B tende a redeclarar tokens dotted (incl. compostos
como `process.search`, que jamais poderiam ecoar). A correção é legítima e
rápida quando converge (1 re-tentativa típica); quando não converge, o outcome
é honesto (`insufficient`/`partial`), nunca falso SATISFIED. Não é defeito do
mecanismo: nenhum token dotted pode demonstrar; rejeição + guidance é o
comportamento contratual.

## 7. Não-objetivos honrados

- Sem segundo Agent/planner/engine/router/catálogo/autoridade paralela.
- Sem write real; sem deploy produtivo; sem avanço de fase.
- Instruções provider-agnostic; sem hardcode de tokens A–F; sem regex
  semântica sobre texto livre de resultado.
- `PRODUCTION_DEPLOY=NOT_AUTHORIZED`, `INT2_ACCEPTED=NO`,
  `INT3/T3=NOT_AUTHORIZED`.

## 8. Resultado

`IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — **não é aceite**. Requer
`COORDINATION_RC5_INDEPENDENT_REVIEW_AFTER_REWORK` (Doc brief §19).
