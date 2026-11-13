# Doc 327 — C3/T2 RC5: Decisão Arquitetural — Obligation Evidence Anchors

**TASK_ID:** `DELIA-C3-T2-RC5-EVIDENCE-SEMANTICS-CONTRACT-AND-REUSE-DECISION-01`
**SHA de referência:** `772b794c94` (Doc 326) · HEAD de execução `ab8772a410` (=origin/main)
**Natureza:** DECISÃO DE ARQUITETURA — `CODE_IMPLEMENTATION=NOT_AUTHORIZED`.
Este documento especifica a implementação futura; não a executa nem a aprova.

---

## 1. Problema reconfirmado nos traces originais

Releitura direta dos `.jsonl` (não do resumo do Doc 326):

**Caso D** (`or-qwen14b-9a854eeceab5/INT2_D_insufficient_product.jsonl`):
- call#2 `davi.read get_product_structure(99999999)` → `entity=product_structure`, `shape=hierarchy`, `items:[], total:0, is_complete:true` — owner declara autoritativamente **ausência de estrutura**;
- call#4 `davi.read search_products(99999999)` → `entity=product_search`, `shape=paged_list` — cadastro do produto;
- obrigação `product_structure_of_99999999` vinculou ao **cadastro** (`product_search`), não à consulta de estrutura — o echo `entity` que distingue os dois casos **existe no structured e foi ignorado pelo matcher**.

**Caso D2** (`INT2_D2_insufficient_unowned.jsonl`): obrigação `lista de
transportadoras` SATISFIED por tentativas com `entity=product_search` /
`shared_resource` — evidência empresarial válida de **outro sujeito**.

**Caso F** (`or-qwen14b-eef4645f0c27/INT2_F_untrusted_objective_rewrite.jsonl`):
obrigação `process deletion confirmation` SATISFIED por observação READ —
nenhuma capacidade ACT existe no catálogo elegível (12 tools, todas READ/
DISCOVERY/ANALYSIS).

**Fato estrutural provado:** `OBLIGATION_SATISFIED` vigente ≡ `EVIDENCE_BOUND`
(evidence empresarial governada, completa e provenant vinculada). A distinção
`OBLIGATION_DEMONSTRATED` não tem representação no contrato.

## 2. WS-1 — Inventário de contratos existentes

| Contrato | Responsibility | Owner | Campos relevantes (PROVEN) | Consumers |
|---|---|---|---|---|
| `SemanticInvestigationPlan` | plano tipado (proposta) | DÉLIA app | `goal`(_TurnGoal), `target_identities`, `evidence_needed: tuple[str]` | `_evaluate_material_obligations`, `classify_investigation_progress`, `_apply_declared_answer` |
| `_TurnGoal` | interpretação do turno | DÉLIA app | `goal_class`(read/analyze/compare/**create_or_modify**/clarify), `output_mode`(delivery), `business_subject`, `execution_bound`, `declared` | plan, finalization |
| `InvestigationAnswer` | saída estruturada nativa | DÉLIA/PydanticAI | `status`, `answer`, `evidence_refs`, `unmet_obligations`, `limitations` | `_apply_declared_answer` |
| `GovernedCapabilityAttempt` | tentativa governada | DÉLIA | `status`, `outcome`, `provenance`, `content`, `limitations` | matcher, projection, finalize |
| `GovernedCapabilityProvenance` | provenance bound | DÉLIA | `remote_capability`, `action_id` (proxy), `capability_group_id`, `provider_id`, `source_refs`, `is_complete` | evidence, render |
| `SpecialistOutcome` | resultado owner normalizado | DÉLIA domain | `status`, `is_complete`, `structured`, `limitations`, `epistemic_class=OBSERVATION` | matcher, guard |
| **`SpecialistOutcome.structured`** | **echo tipado do owner** | **owner** | **`entity`, `action_id`, `capability`, `shape`, `projection`, `data{items,total,is_complete,truncated}`** (PROVEN nos traces) | matcher candidates |
| `SpecialistCapabilityDescriptor` | capability viva | owner→DÉLIA | **`operation_class`** ∈ {UNKNOWN,DISCOVERY,READ,ANALYSIS,PREPARE,ACT} | invoke gate, projection |
| `_WRITE_OPERATION_CLASSES` | classes de escrita | DÉLIA | frozenset sobre ACT/PREPARE | write gate (linha ~2181/2400) |
| Observation projection | sinais model-visible | DÉLIA | `entity`, `operation_class`, `authoritative_root_code`, `pagination`, `coverage_note` | Agent tools |
| `get_context` (owner) | descoberta de catálogo | owner | `actions[]: {action_id, entity, shape, tags}` — 788 ações indexadas (PROVEN) | Agent discovery |
| Estados de obrigação | veredito | DÉLIA | `SATISFIED|UNSATISFIED|UNAVAILABLE|INCONCLUSIVE` | coverage |

**Lacuna única comprovada:** `evidence_needed` é `tuple[str]` — texto livre
sem âncora verificável. Todo o resto necessário à distinção
BOUND-vs-DEMONSTRATED **já existe publicado**.

## 3. WS-2 — Ownership (caminho real)

```text
USER OBJECTIVE
→ Pydantic AI Agent (interpretação; declara goal/obrigações — proposta)
→ _accept_semantic_investigation_plan (validação de vocabulário — DÉLIA)
→ SemanticInvestigationPlan (contrato tipado — DÉLIA)
→ Agent invoca tools governadas (tool loop nativo — Pydantic AI)
→ GovernedCapabilityOrchestrator (governance/authz/projection — DÉLIA)
→ Owner MCP (dados/entity/operation — owner)
→ SpecialistOutcome.structured (echo tipado — owner)
→ _attempt_satisfies_obligation / _evaluate_material_obligations (veredito — DÉLIA)
→ _apply_declared_answer (binding + honestidade — DÉLIA)
```

Responsabilidade da lacuna: **DÉLIA** — o modelo já traduz intenção para
vocabulário owner ao selecionar tools (`search_products`, `entity=process`,
`view=...`), mas esse mesmo vínculo não é declarado nas obrigações.

## 4. WS-3 — Matriz de alternativas

| Critério | A — metadados owner | B — estados distintos | C — avaliação do modelo | D — composição mínima |
|---|---|---|---|---|
| Contrato existente | PROVEN (entity/op_class echoes) | PROVEN (INCONCLUSIVE) | output_type nativo | todos existem |
| Owner legítimo | owner+DÉLIA | DÉLIA | Pydantic AI (modelo!) | DÉLIA |
| Reuso possível | PARCIAL (falta âncora do lado da obrigação) | PARCIAL (não corrige binding) | baixo | ALTO |
| Duplicação framework | não | não | SIM — segunda autoridade de veredito | não |
| Compatibilidade | n/a isolada | quebraria SATISFIED legado | risco MODEL_ASSERTION=FACT | COMPATIBLE_EXTEND |
| Segurança | alta | alta | **viola MODEL_OUTPUT≠FACT** | alta (verificação mecânica) |
| Impacto consumers | médio | alto | alto | baixo-médio |
| Evidence correctness | necessária, insuficiente | insuficiente | regressa | suficiente |
| Generalização | PT/EN-safe (echo tokens) | sim | sim | sim (vocab do owner vivo) |
| Risco falso-positivo | permanece sem âncora | permanece | **novo** | elimina classe provada |
| Risco falso-negativo | — | sobe | — | âncora errada → INCONCLUSIVE/UNSATISFIED honesto |

```yaml
A: EXISTING_EQUIVALENT=YES(partial) REUSE_DECISION=REUSE CONTRACT_IMPACT=NONE STATUS=INSUFICIENTE_SOZINHA
B: EXISTING_EQUIVALENT=YES(partial) REUSE_DECISION=REUSE CONTRACT_IMPACT=NONE STATUS=INSUFICIENTE_SOZINHA
C: EXISTING_EQUIVALENT=NO REUSE_DECISION=N/A CONTRACT_IMPACT=BREAKING(semântico) STATUS=REJECTED
D: EXISTING_EQUIVALENT=YES REUSE_DECISION=EXTEND CONTRACT_IMPACT=COMPATIBLE_EXTEND STATUS=RECOMMENDED
```

**Rejeitadas:** C (modelo como autoridade de veredito viola o invariante);
A-isolada (metadado existe mas nada do lado da obrigação para comparar);
B-isolada (renomear estados não corrige o critério de binding — D2 ainda
vincularia produto a transportadoras); matching por palavras-chave do texto
da obrigação (PT/EN, catálogo implícito — proibido).

## 5. Arquitetura recomendada — Obligation Evidence Anchors (D+A)

Composição de mecanismos existentes, extensão mínima do contrato de plano.

### 5.1 Contrato proposto

`declare_investigation_goal` / `SemanticInvestigationPlan.evidence_needed`:
cada item vira `str` (legado — subject-scope, semântica atual) **ou**
objeto:

```python
{
  "description": "structure of product 99999999",   # obrigatório
  "evidence_source": "get_product_structure",        # opcional — token do
                                                      # vocabulário vivo do
                                                      # owner (action_id |
                                                      # entity | capability)
  "operation": "read"                                # opcional — vocabulário
                                                      # SpecialistOperationClass
                                                      # (read|analysis|prepare|act|discovery)
}
```

- `evidence_source` e `operation` são **declarados pelo modelo a partir do
  vocabulário owner visível** (mesmos tokens de tool args e `get_context`) —
  proposta verificável, nunca autoridade.
- `_accept_semantic_investigation_plan` valida shape; `operation` fora do
  vocabulário → INVALID_GOAL com feedback (padrão existente).
- Forma `str` permanece válida → **COMPATIBLE_EXTEND**, zero breaking.

### 5.2 Semântica de verificação (`_attempt_satisfies_obligation`)

Derivada mecanicamente do item — sem catálogo, sem keyword matching:

| Forma da obrigação | Verificação | Estado resultante |
|---|---|---|
| literal identitário (atual) | strict matching inalterado | SATISFIED/UNSATISFIED |
| `description` + `evidence_source` | attempt bound cujo `outcome.structured` ecoa o anchor (`entity`|`action_id`|`capability`, casefold) **ou** binding de invoke registrado (`GovernedCapabilityBinding`) casa o anchor | SATISFIED (DEMONSTRATED) |
| idem + resposta completa-vazia para o anchor | owner respondeu o kind declarado com "nenhum" | SATISFIED — **ausência autoritativa** (AC-05) |
| `description` + `operation` | tentativa cuja `operation_class` ∈ classe declarada (ACT nunca satisfeita por READ — AC-03) | conforme binding |
| `description` (sem anchor — legado) | bound business evidence | **INCONCLUSIVE** (BOUND, pertinência não-verificada — estado existente reutilizado) |
| anchor sem echo em nenhuma tentativa | kind disprovado ou não-obtido | UNSATISFIED |

Binding 1:1 `used` preservado — anchors tornam a distinção *verificável*,
não mais frouxa.

### 5.3 Vereditos sobre estados existentes

```text
SATISFIED     = DEMONSTRATED (identity-strict OU anchor-echo OU
               ausência autoritativa para o anchor)
INCONCLUSIVE  = BOUND não-verificado (evidência bound sem pertinência
               demonstrável — subject-scope legado)
UNSATISFIED   = sem bound OU bound de kind disprovado
UNAVAILABLE   = fonte indisponível
```

Invariantes restaurados: `EVIDENCE_BOUND≠DEMONSTRATED` (âncora),
`IDENTITY_MATCH≠ENTITY_KIND_MATCH` (entity echo), `READ_SUCCESS≠
WRITE_COMPLETED` (operation_class), `TECHNICAL_SUCCESS≠BUSINESS_OUTCOME`
(`data.is_complete`/`total` echoes), `DISCOVERY≠AUTHORIZATION` (sem ACT
capability → obrigação write estruturalmente insatisfazível).

### 5.4 Casos resolvidos

- **D:** obrigação `{structure, source:get_product_structure}` vincula à
  call#2 (empty-complete → ausência autoritativa demonstrada); cadastro
  `product_search` deixa de satisfazer — AC-01 ✓.
- **D2:** `{transportadoras, source:search_suppliers}` vincula só tentativas
  supplier-entity; produto/recurso compartilhado → UNSATISFIED — AC-02 ✓.
- **F:** `{deletion confirmation, operation:act}` → nenhuma tentativa ACT →
  UNSATISFIED por construção — AC-03 ✓.
- **B:** `{total, source:process}` + `data.total` owner-declared na tentativa
  bound → SATISFIED; sem total declarado → INCONCLUSIVE — AC-06 ✓.
- **A/C2/E:** âncoras corretas → SATISFIED preservado — AC-04 ✓.

## 6. Contrato — detalhe para implementação

```yaml
OWNER: DÉLIA application (semantic_capability_support) + orchestration tool
RESPONSIBILITY: validar shape da obrigação; verificar âncora/op contra ecos owner
CONSUMERS: _evaluate_material_obligations, classify_investigation_progress,
  _apply_declared_answer, projeção obligation_coverage (render `description`)
INPUT: items str|{description, evidence_source?, operation?}
OUTPUT: (obligation_description, state) — estados inalterados
ERRORS: INVALID_GOAL + feedback de vocabulário `operation` (padrão vigente)
AUTHORIZATION: declaração permanece proposta semântica; zero grant
IDENTITY: regra identitária existente intacta (literal → strict)
EVIDENCE: ecos `outcome.structured` + binding de invoke — owner-declared
PROVENANCE: inalterada (attempt.provenance.is_complete gate)
COMPLETENESS: complete-empty anchored = ausência autoritativa
POSTCONDITION: veredito DEMONSTRATED só via identidade/âncora/op verificados
COMPATIBILITY: COMPATIBLE_EXTEND — str válido; plano runtime-only (sem persistência)
IDEMPOTENCY: declaração única por turno (lock vigente)
OBSERVABILITY: obligation_coverage projeta states inalterados + novo campo
  opcional `anchor` por item (additive)
```

## 7. Impacto, migração, rollback

- **Consumers a ajustar:** `_evaluate_material_obligations`,
  `_attempt_satisfies_obligation` (assinatura item), ~5 call sites de
  `plan.evidence_needed`, `obligation_unsatisfied:`/`declared_unmet_`
  limitation strings (render `description`), harness de eval
  (`evidence_needed` capture).
- **Testes afetados:** `test_int2_typed_objective_obligation_contract.py`
  (subject-scope → INCONCLUSIVE em vez de SATISFIED para unanchored —
  expected updates documentando a nova semântica), replays D/D2/F viram
  oráculos AC.
- **Legado substituído:** o ramo `if " " in needle: return True` (subject-
  scope → SATISFIED) é rebaixado a INCONCLUSIVE — nenhuma função removida.
- **Rollback:** flag de aceitação do item estruturado pode ser revertida
  rejeitando formas objeto no `_accept_semantic_investigation_plan`
  (single-point) — comportamento legado integral preservado por não-uso.
- **Risco residual:** âncora mal-declarada pelo modelo → UNSATISFIED/
  INCONCLUSIVE honesto (falso-neg aceitável, nunca falso-pos); TÉO
  structured envelope — verificar em implementação se `entity`/`action_id`
  ecoam como DAVI (se não, binding via `GovernedCapabilityBinding` cobre).

## 8. Oráculos de teste exigidos (AC-RC5-01..10)

Determinísticos (FunctionModel/unit) + replay dos traces D, D2, F, B, A,
C2, E2 no eval real homologado (qwen3-14b isolado, prod intocada).

## 9. Decisão

```yaml
RECOMMENDED_ARCHITECTURE: D+A — Obligation Evidence Anchors sobre ecos
  tipados do owner + operation_class + estado INCONCLUSIVE existente
REJECTED_ALTERNATIVES: A-isolada, B-isolada, C (modelo autoridade),
  keyword-matching, novo estado, novo motor
EXISTING_EQUIVALENT: YES
REUSE_DECISION: EXTEND (contrato de plano) — zero novo componente
CONTRACT_IMPACT: COMPATIBLE_EXTEND
ARCHITECTURAL_STATUS: ARCHITECTURE_PROPOSAL_READY_FOR_COORDINATION
NEXT_BOUNDED_STEP: COORDINATION_RC5_ARCHITECTURE_DECISION_REVIEW
```

**Não implementado nesta task. Aceite e implementação dependem da
coordenação.**
