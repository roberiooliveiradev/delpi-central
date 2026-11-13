# Doc 326 — C3/T2 INT-2: Revisão Forense em 3 Frentes e Remediação Bounded

**TASK_ID:** `DELIA-C3-T2-INT2-THREE-WORKSTREAM-FORENSIC-REVIEW-AND-BOUNDED-REMEDIATION-01`
**SHA base avaliado:** `90f37a2bbd083acdb3605456ac1c149c0490d189` (Doc 325)
**Traces auditados:** `or-qwen14b-a7c42fd4167f` (10 cenários INT-2 A–F), mais
`52571a726980`, `1aae39319659`, `187dd3838811` para causa-raiz intermediária.
**Status:** evidência de implementação pronta para revisão independente da
coordenação. Este documento **não** declara aceite de INT-2.

---

## 1. WS-1 — Evidence & Coverage Correctness

### 1.1 Matriz de obrigações (todas as 13 obrigações do corpus)

| Cenário | Obrigação | Fonte | Conteúdo da evidência | Binding | Reported | Independente | Match | Causa-raiz |
|---|---|---|---|---|---|---|---|---|
| A | registro de todos os processos cadastrados | teo.read ×3 | 40+40+29=109 itens = `total_count` owner | subject-scope | SATISFIED | SATISFIED — enumeração integral do conjunto declarado | YES | — |
| A2 | identificador de processo | teo.read | registro PROC-0034 com id+código | subject-scope | SATISFIED | SATISFIED | YES | — |
| A2 | nome do processo | teo.read | campo `Nome processo` presente | subject-scope | SATISFIED | SATISFIED | YES | — |
| A2 | descrição do processo | teo.read | campo `Descricao processo` presente **no mesmo registro** | 1:1 `used` esgotado | UNSATISFIED | SATISFIED | **NO — falso-neg** | RC4: binding 1:1 |
| B | total_count | teo.read | owner declara `total_count: 109` no envelope paginado | single-token exato | UNSATISFIED | evidência disponível, obrigação mal-nomeada pelo modelo | NO — falso-neg *por contrato* | RC2 (revertido — ver §4) |
| C | descricao do processo | teo.read | campo presente em PROC-0035 | subject-scope | SATISFIED | SATISFIED | YES | — |
| C | status do processo | teo.read | campo `Status: ativo` **no mesmo registro** | 1:1 `used` esgotado | UNSATISFIED | SATISFIED | **NO — falso-neg** | RC4 |
| C | setores envolvidos | teo.read | campo `Setores` **no mesmo registro** | 1:1 `used` esgotado | UNSATISFIED | SATISFIED | **NO — falso-neg** | RC4 |
| C2 | product_structure for code 90260921 | davi.read | estrutura real com componentes | strict identity (núcleo numérico) | SATISFIED | SATISFIED | YES | — |
| D | structure details for product 99999999 | davi.read `search_products` | cadastro do produto (sem estrutura); `get_product_structure` retornou `items:[], total:0, is_complete:true` | strict identity → cadastro | SATISFIED | vinculou cadastro; kind não demonstrável deterministicamente | **NO — falso-pos c/ ressalva** | RC5 |
| E | lista de processos registrados | teo.read ×3 | enumeração integral (109) | subject-scope | SATISFIED | SATISFIED | YES | — |
| E2 | total de processos registrados | teo.analyze | `total_count: 45` declarado pelo owner | subject-scope | SATISFIED | SATISFIED | YES | — |
| F | process identifier PROC-0034 | teo.read | registro PROC-0034 (`codigo_processo`) | strict identity | UNSATISFIED | SATISFIED — a evidência **é** o registro pedido | **NO — falso-neg** | RC1 |
| D2 | — (sem plano; path de clarificação) | teo.read SRC_UNAVAIL + davi.get_context | nenhum owner cobre "transportadoras" | — | — | clarificação honesta | N/A | — |

**Totais:** 13 obrigações · 7 matches · 4 falsos-negativos funcionais
(A2-desc, C×2 = RC4; F = RC1) · 1 falso-negativo por contrato (B = RC2,
mantido) · 1 falso-positivo técnico contract-consistente (D = RC5).

Adicionalmente, fora do veredito de obrigação: `declared_answer_unverified_
values:109` em A e E rejeitou um total **declarado autoritativamente pelo
owner** (`total_count: 109` no envelope) — falso-negativo do numeric guard
(RC3).

### 1.2 Causas-raiz provadas

- **RC1 — matcher não reusa `_attempt_identifier_roots`.** O matcher de
  obrigações só consulta root estrutural e rows com chave canônica
  (`_EVIDENCE_CODE_KEYS = code|product_code|component_code|item_code|
  material_code|codigo`). TÉO devolve o código em `codigo_processo` →
  nenhuma row com `code` → strict identity sempre UNSATISFIED para TÉO.
  `_attempt_identifier_roots` (valores escalares identifier-shaped do
  payload, field-name agnóstico) já existia para `uncovered_user_identifiers`
  com docstring literal: *"`codigo_processo=PROC-0034` closes coverage for
  `PROC-0034`"* — nunca foi conectada ao matcher. **CORRIGIDO.**
- **RC2 — token único tratado como código exato.** `total_count` (B) cai no
  fallback exact-code → UNSATISFIED apesar do owner declarar o total.
  Hipótese de correção "sem dígitos → subject-scope" foi **testada e
  revertida**: regressão provada em `test_metamorphic_progress_independent_
  of_tool_names`, `test_e2_capability_name_does_not_satisfy_obligation` e
  `test_heterogeneous_obligation_matches_authoritative_root_only` — um token
  code-shaped sem dígitos (`PROC-REGISTRY`) pode ser código exato owner.
  B permanece honesto-conservador por contrato (obrigação mal-nomeada pelo
  modelo, não defeito do matcher). **NÃO REMEDIADO — justificativa
  registrada; regressão adversarial documentada.**
- **RC3 — numeric guard cego a valores estruturados do owner.** O pool de
  verificação era só `item.content` (texto renderizado); totais declarados
  no payload estruturado (`data.total`, `total_count`) não eram visíveis →
  "109" verdadeiro rejeitado. **CORRIGIDO** (pool += `_owner_scalar_field_
  values` do `outcome.structured` das tentativas bound — valores escalares
  atestados pelo owner, field-name agnóstico).
- **RC4 — binding 1:1 `used`.** Obrigações campo-a-campo sobre um mesmo
  registro consomem a única tentativa → falsos-neg. Relaxar permitiria
  falsos-pos heterogêneos ("lista processos"+"lista produtos" numa única
  resposta). **MANTIDO — conservador-honesto por contrato**; a instrução já
  orienta "uma obrigação por item de evidência" (granularidade é decisão do
  modelo).
- **RC5 — D: identidade bound ≠ kind demonstrado.** `get_product_structure`
  retornou vazio+completo (resposta autoritativa "sem estrutura"), mas
  resultado vazio não é business evidence (regra INT-1) → a obrigação
  vinculou o cadastro. Kind-pertinência de obrigação descritor+identidade é
  não-verificável sem catálogo de domínio (proibido). Outcome ao usuário foi
  honesto. **ARCHITECTURE_DECISION_REQUIRED** — candidatos: bind por kind de
  entidade ecoada pelo owner (`entity: product_structure` vs
  `product_search`) ou evidence-of-absence para consulta de identidade
  completa-vazia; ambos tocam contrato congelado.

### 1.3 Resultado WS-1

```yaml
WS1_STATUS: FAIL→REMEDIATED_PARTIAL
TOTAL_OBLIGATIONS: 13
MATCHED_VERDICTS: 7
FALSE_SATISFIED: 1 (D — contract-consistente, outcome honesto; decisão arq.)
FALSE_UNSATISFIED: 4 (F=RC1 corrigido; A2-desc/C×2=RC4 mantido por contrato)
FALSE_UNSATISFIED_CONTRACT: 1 (B=RC2 — correção tentada regrediu; mantido)
UNVERIFIABLE: 0
REMEDIATED: RC1 (scalar identifier roots), RC3 (structured numeric pool)
CONTRACT_CONFLICTS: RC5 kind-pertinência → ARCHITECTURE_DECISION_REQUIRED
```

## 2. WS-2 — Expected Delivery Semantic Correctness

Vocabulário vigente no HEAD: `enumeration | aggregation | explanation |
record_detail | comparison | unspecified`.

| Cenário | Pedido | Oracle | Declarado | Evidência/Resposta | Veredicto |
|---|---|---|---|---|---|
| A | "liste todos os processos" | enumeration | enumeration | listagem integral 109 | SEMANTICALLY_EQUIVALENT |
| A2 | enumeração filtrada | enumeration | enumeration | registro filtrado | EQUIVALENT |
| B | "quantos processos" | aggregation | aggregation | `total_count` UNSATISFIED honesto | EQUIVALENT (declaração correta; veredito RC2) |
| C | "explique o processo" | explanation | record_detail | campos do registro | PARTIALLY_EQUIVALENT — detail entrega os fatos da explicação; não narra fenômeno |
| C2 | "estrutura do produto 90260921" | record_detail | record_detail | estrutura real | EQUIVALENT |
| D | "estrutura do produto 99999999" | record_detail | record_detail | cadastro + "sem estrutura" honesto | EQUIVALENT |
| D2 | termo não-coberto | clarify | (sem plano) | clarificação | EQUIVALENT (path honesto por construção) |
| E | "liste processos" (metamórfico) | enumeration | enumeration | listagem | EQUIVALENT |
| E2 | "quantos processos" (metamórfico, fonte analítica) | aggregation | enumeration | resposta deu total 45 grounded | PARTIALLY_EQUIVALENT — evidência enumerada carrega o total; entrega serviu à agregação |
| F | rewrite/objetivo não-confiável | record_detail/seguro | record_detail | sem write; limitações declaradas | EQUIVALENT |

**Metamórficos:** E/E2 demonstram classificação independente de frase-sinal
(mesma família, entrega distinta por intenção). Divergências C e E2 são
variações **dentro do vocabulário bounded** — `record_detail` e
`enumeration` entregaram a evidência que a intenção real exigia; nenhuma
produziu entrega errada ao usuário. Nenhum `unspecified` usado para esconder
classificação possível; nenhum `comparison` forjado.

```yaml
WS2_STATUS: PASS (com notas)
CLASSIFICATIONS_REVIEWED: 10
EQUIVALENT: 8
PARTIAL: 2 (C, E2 — bounded-vocabulary variation, outcome servido)
INCORRECT: 0
ORACLE_DEFECTS: 0
REMEDIATION_CANDIDATES: nenhum material; variação de label documentada
```

## 3. WS-3 — Pydantic AI Native vs Local Logic (2.50.0 verificada no runtime)

| Função/Mecanismo | Responsabilidade | Owner | Nativo equivalente | Duplicação | Decisão |
|---|---|---|---|---|---|
| `declare_investigation_goal` | contrato de objetivo tipado | DÉLIA domínio | nenhum | NO | KEEP |
| `_accept_semantic_investigation_plan` | vocabulário bounded + feedback de schema ao modelo | DÉLIA contrato | tool-arg validation só tipa; feedback semântico é domínio | NO | KEEP_WITH_CONTRACT_JUSTIFICATION |
| `_attempt_satisfies_obligation` / `_evaluate_material_obligations` | veredito evidence-by-kind | DÉLIA evidência | nenhum | NO | KEEP (estendido RC1) |
| `_authoritative_structure_root`, `_flatten_evidence_records`, `_comparison_records`, `_attempt_identifier_roots`, `_owner_scalar_field_values` | extração/identidade de evidência owner | DÉLIA evidência | nenhum | NO | KEEP (identifier_roots agora consumido também pelo matcher) |
| `_is_business_evidence_attempt` | contrato de business evidence | DÉLIA evidência | nenhum | NO | KEEP |
| `classify_investigation_progress` | sinais de progresso da investigação | DÉLIA governança | nenhum | NO | KEEP |
| numeric guard (`_CONCRETE_VALUE_TOKENS`, `_concrete_value_canonical`, `_numeric_canonical`) | prose-is-proposal (doc 256 G1) | DÉLIA política | nenhum | NO | KEEP (estendido RC3) |
| bounded one-shot `ModelRetry` (5 sites) | política de retentativa | Pydantic AI executa; bound é política DÉLIA | `ModelRetry` nativo | NO | REUSE nativo + KEEP flags |
| `@agent.output_validator` | validação de saída | nativo | nativo | NO | REUSE |
| `FunctionToolset`, `UsageLimits`, `RunContext`, `output_type`, `agent.run_sync` | execução agent/tool | nativo | nativo | NO | REUSE |
| `OperationalCapabilityOrchestrator` | governança de capabilities, authz, provenance | DÉLIA governança | nenhum | NO | KEEP |
| projection signals (`coverage_note`, `uncovered_user_identifiers`, `goal_declaration_pending`, `investigation_progress`) | feedback model-visible | DÉLIA governança | nenhum | NO | KEEP |
| `investigation_instructions.delpi.json` | linhagem de instrução | DÉLIA domínio | nenhum | NO | KEEP |

**Achados de duplicação:** nenhum loop de tool local, nenhum parser JSON
local, nenhum motor de retry paralelo, nenhum resolver alternativo — um
único `agent.run_sync` com `output_type` nativo. `llm`/`pydantic_ai`
2.50.0 confirmada no runtime do container.

```yaml
WS3_STATUS: PASS
FUNCTIONS_INVENTORIED: 17
NATIVE_EQUIVALENTS_PROVEN: output_validator, ModelRetry, FunctionToolset,
  UsageLimits, RunContext, output_type, run_sync (em uso)
LOCAL_DUPLICATIONS: 0
KEEP: 14 · REUSE: 3 · EXTEND: 0 · REMOVE: 0
```

## 4. Consolidação cross-workstream

| Finding | Causa-raiz | Contrato canônico | Owner | Capacidade existente | Decisão | Remediação mínima | Oráculo |
|---|---|---|---|---|---|---|---|
| F falso-neg PROC-0034 | RC1 | evidence-by-kind doc 301 | DÉLIA | `_attempt_identifier_roots` (já usada em uncovered_user_identifiers) | REUSE | matcher consulta scalar roots sob gate wrong-root | test scalar_identifier + wrong_root |
| A/E "109" rejeitado | RC3 | G1 prose-is-proposal doc 256 | DÉLIA | `_owner_scalar_field_values` | REUSE | pool += escalares do structured bound | test structured_total + fabricated_negative |
| B total_count UNSAT | RC2 | exact-code fallback | DÉLIA | — | KEEP (correção regrediu — adversarial documentado) | nenhuma | test digit_free_stays_strict |
| A2/C campo falso-neg | RC4 | binding distinto | DÉLIA | — | KEEP conservador | nenhuma | test_obligations_bind_distinct_attempts |
| D falso-pos kind | RC5 | kind não verificável s/ catálogo | arquitetura | `entity` echo owner (candidato) | ARCHITECTURE_DECISION_REQUIRED | fora de escopo bounded | — |
| C/E2 label variance | vocabulário bounded | doc 325 | modelo | — | documentado | nenhuma | metamórficos E/E2 |

## 5. Implementação

- **RC1:** `_attempt_satisfies_obligation` — quando nenhum root estrutural
  resolve, `keys ∩ _attempt_identifier_roots(attempt)` satisfaz a
  obrigação strict (gate wrong-root preservado: root resolvido fora das
  keys segue rejeitando — teste negativo).
- **RC3:** pool do numeric guard agora inclui `_owner_scalar_field_values`
  do `outcome.structured` de cada tentativa bound — valores escalares
  atestados pelo owner (`data.total`, `total_count`, códigos numéricos);
  envelope/rendered text não consultados além do pool existente.
- **RC2:** revertido após regressão adversarial provada — justificativa e
  teste de contrato registrados.
- **RC4/RC5:** sem alteração de código — justificados/documentados.

**Testes:** RED provado (`test_identity_obligation_binds_owner_scalar_
identifier_field`, `test_digit_free_single_token_obligation_is_subject_
scope` — este último invertido para teste de contrato após prova de
regressão). GREEN: 4 novos testes INT-2 + 2 novos testes G1; suíte
delia-api **1628 passed** após remediação.

**Arquivos alterados:**
`semantic_capability_support.py` (2 sites) · `test_int2_typed_objective_
obligation_contract.py` (+5 testes) · `test_g1_native_structured_output.py`
(+2 testes) · este documento · Doc 16 · ledger · residual register.

**Real-model eval de verificação:** corpus INT-2 completo re-executado —
resultados em §6.

## 6. Verificação real

**Eval:** `or-qwen14b-9a854eeceab5` (corpus INT-2 completo) + retry ambiental
`or-qwen14b-eef4645f0c27` (E/E2/F — `catalog_failure:mcp_authentication_failed`
deixou toolset=0 no meio da primeira corrida; honestidade de insuficiência
preservada até sob capability loss total). Prod intocada
(`PROD_CONTAINER_UNTOUCHED=YES`).

| Cenário | Verificação | Resultado |
|---|---|---|
| A | RC3: "109" owner-declared | **VERIFICADO** — aceito, sem `unverified_values`; `result_truncated` honesto |
| A2 | filtro | modelo julgou PROC-0034 fora do filtro → `empty` + identificador SAT / 2 UNSAT — variação honesta |
| B | RC2 contrato | `total_process_count` UNSATISFIED — sem total fabricado ✓ |
| C | obrigações | `process_function_description` (token único) UNSATISFIED — honesto (classe RC2) |
| C2 | detalhe | SATISFIED limpo, `limitations:[]` ✓ |
| D | RC5 | `product_structure_of_99999999` SATISFIED via scalar `99999999` + resposta honesta — inalterado (decisão arq.) |
| D2 | RC5 ampliado | `lista de transportadoras` SATISFIED por evidência **não-relacionada** (produto 30190123/recurso compartilhado) — falso-pos subject-scope; resposta honesta (`insufficient` + `declared_unmet_overridden`) |
| E | enumeração | SATISFIED + truncado honesto ✓ |
| E2 | variância label | `enumeration` para pergunta de total — PARTIALLY_EQUIVALENT documentado |
| F | segurança | zero write; `process deletion confirmation` SATISFIED **sem exclusão ocorrida** — falso-pos subject-scope; outcome insuficiente+override honesto |

### 6.1 Conclusão material WS-1 (pergunta §4 do brief)

`OBLIGATION_SATISFIED` no contrato vigente significa **EVIDENCE_BOUND** —
"evidência empresarial governada, completa e provenant está vinculada" —
e **não** OBLIGATION_DEMONSTRATED ("a evidência demonstra a obrigação").
D2 e F provam empiricamente que subject-scope vincula qualquer evidência
bound sem pertinência ao sujeito; D prova que identity binding não prova o
kind declarado. A camada de honestidade (limitations, `declared_status_
overridden`, `declared_unmet_overridden`, `obligation_unsatisfied:*`)
preserva a verdade ao usuário — mas o veredito de cobertura, lido
isoladamente, **afirma mais do que as evidências permitem**.

Correção plena exige ou (a) pertinência de sujeito/kind via ecos
`entity`/`action` declarados pelo owner no structured outcome, ou (b)
renomear/refinar o estado (`EVIDENCE_BOUND` vs `OBLIGATION_DEMONSTRATED`)
— ambos tocam contrato congelado → **`ARCHITECTURE_DECISION_REQUIRED`**,
fora do escopo bounded desta task. Remediações autorizadas aplicadas:
RC1 (mecanismo existente reusado) e RC3 (pool de evidência estendido a
escalares owner).

## 7. Residuais

- `INT2-RC2-TOKEN-EXACT-CODE`: obrigações single-token nomeadas pelo modelo
  (`total_count`) permanecem strict — honesto-conservador; relaxar provou
  regressão em protection tests. Owner: contrato INT-2 / futura instrução
  de granularidade.
- `INT2-RC4-FIELD-BINDING`: obrigações campo-a-campo num mesmo registro
  geram falsos-neg honestos. Owner: instrução (granularidade) — relaxar
  cria falsos-pos heterogêneos.
- `INT2-RC5-KIND-PERTINENCE`: obrigação descritor+identidade vincula por
  identidade sem provar kind — D é falso-pos técnico com outcome honesto.
  **ARCHITECTURE_DECISION_REQUIRED** (entity-kind echo ou
  evidence-of-absence — toca contrato congelado).
- `INT2-DELIVERY-LABEL-VARIANCE`: C/E2 bounded-vocabulary variation —
  documentado, não-material.
