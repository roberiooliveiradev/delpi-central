# 168 — Integrated LLM-Native Operational Intelligence Validation

**TASK_ID:** `DELIA-C3-LLM-NATIVE-OPERATIONAL-INTELLIGENCE-INTEGRATED-VALIDATION-01`
**Data:** 2026-10-27
**Executor:** Cursor / Devin
**Fase:** C3 (não avança fase)
**BASE_HEAD:** `056efde0b6` · **EVALUATED_SHA:** `056efde0b6`
**Autoridades:** docs 163–167 + revisões independentes `ddddf09f34`
(R1.5) e `23613bd1f1` (R1.6-A) + Execution Ledger.

> Escopo: validação integrada local. Nenhuma alteração de código
> produtivo, instrução ativa, modelo ou deploy. Zero queries em
> produção — owner reads via adapter governado local com bearer
> delegado (mesma superfície autorizada das tasks anteriores).

## 1. Executive summary

Consolidamos os cinco workstreams em uma única avaliação com
contratos experimentais stage-local e composição E2E:

- **WS-A (admission):** o contrato coerente `owner_access`
  (read/write/catalog/none) elevou owner reach de **0.667 → 0.976**
  e acurácia dev de 0.549 → 0.824, preservando negativos
  (injection→none, greet→none). A taxonomia de classes
  (`surface_inquiry`/`hypothetical`) é confirmada como a causa do
  misrouting — remover a taxonomia resolve; reconciliar
  deterministicamente o flag (`A2`) NÃO resolve.
- **WS-B (julgamento):** nenhuma variante cumpre o gate congelado.
  `B2c` (por-registro + `declared_requirements` + verificação de
  identidade tipada) atingiu **precision 0.943 / FPR 0.014** —
  matando o erro de identidade — mas recall caiu a 0.256. `B2`
  (controle R1.6-A) tem recall 0.594 mas precision 0.697 < gate.
  `B3` (lotes de 4) **reproduz o colapso de enumeração**
  (192/285 sem label) — batelados de qualquer tamanho >1 são
  inviáveis no modelo congelado.
- **WS-C (continuidade):** o 3B segue `has_more` (next_page
  correto em páginas restantes) mas **nunca escolhe
  `answer`/`stop`** — decisão de parada é incapaz; segurança
  bounded permanece nos limites determinísticos (dedup, cap de
  rounds) que funcionaram na R1.
- **WS-D (contratos):** causa raiz da falha de
  `answer_requirements` localizada com precisão: o parser e os
  consumidores existem, mas **a instrução `turn_goal` nunca pede o
  campo** — gap de contrato, não do modelo. `contract_subject`
  é pedido; `answer_requirements` não.
- **WS-E (E2E):** E0=9 PASS/32 runs vs E1=8 PASS/32 runs —
  **Δ≈0**. A composição (admissão A1 + goal-requirements +
  juiz B2c + continuação) alcançou o owner com mais frequência,
  mas o outcome empresarial não converteu: as falhas restantes
  concentram-se no recall conservador do juiz sob pressão de
  precisão e no **gap de vocabulário do search do owner**
  (`terminal bala` nunca retorna `TERM. BALA` — provado por
  oráculo autorizado na R1: 0 pertinentes em 77 itens).

**Veredito:** `ACCEPT_WITH_RESIDUAL` para a decisão arquitetural —
a admissão A1 e o campo `answer_requirements` são candidatos
produtivos minimamente justificados; o julgamento por-registro
precisa de mais uma iteração (gate de recall); o gap de busca do
owner é dependência externa (`NEEDS_OWNER_DECISION`).

## 2. Baseline congelada

- **MODEL_ID:** `delia-json:latest` · digest `7b8f4ab14fc1` ·
  Q4_K_M · ctx 8192 · JSON-only · `delpi-ollama` 0.40.8
- **Instruções:** produção inalteradas (hash de recurso idêntico);
  variantes experimentais somente no harness
- **Corpora congelados:** WS-A 21 queries (4 holdout) ×3;
  WS-B 18 sets/98 records ×3 (corpus R1.6-A congelado +
  oracles per-record); WS-C 7 estados ×3; WS-E 16 cenários R1
  ×2 reps ×2 braços (holdout `h_*` preservado)
- **Orçamento:** ~900 model calls totais; nenhuma combinação
  irrelevante executada; B0/B1 reutilizados do artefato R1.6-A
  congelado (mesmo modelo/corpus/digest — reuse documentado)

## 3. Gates pré-registrados

- WS-A: melhorar reach sem sobre-admissão insegura
  (neg_spec ≥ A0, zero injection→owner)
- WS-B: recall ≥ 0.50 **e** precision ≥ 0.80 **e** identity-FP=0
  **e** partial→pertinent ≤ 30% **e** holdout dentro de 10pts
- WS-C: decisões válidas em cenários de continuidade; parada
  segura obrigatória em exaustão
- WS-E: Business Outcome por cenário (oracle-verified), holdout,
  segurança

## 4. WS-A — Admission

| Arm | acc_dev | acc_holdout | owner reach | neg_spec | invalid |
|---|---|---|---|---|---|
| A0 produção | 0.549 | 0.500 | 0.667 | 0.389 | 0 |
| A1 coerente | **0.824** | 0.500 | **0.976** | 0.500 | 0 |
| A2 reconciliação | 0.549 | 0.500 | 0.667 | 0.389 | deriv. |

- A1 converte corretamente: coloquiais→read (exceto 1 rep→write),
  guias→read, write→write, greet/conceito→none, **inject→none**.
- Erros residuais A1: `hypothetical`→read, `ambiguous`→read,
  `discovery`/`surface_legit`→read (sobre-admissão para READ —
  caminho seguro e bounded; especificidade de catálogo imperfeita).
- A2 (routing por flag sobre a mesma saída A0): sem ganho — o flag
  falha nos mesmos casos que a classe neste corpus.
- **Gate A: PASS** — A1 melhora reach sem sobre-admissão insegura.

## 5. WS-B — Evidence judgment

| Arm | precision | recall | FPR | set_dev | set_hol | calls | ident-FP |
|---|---|---|---|---|---|---|---|
| B0 agregado (reuse) | ~1.0 | ~0.17 eq. | 0 | 0.667 | 0.750 | 54 | n/a |
| B1 por-registro (reuse) | 0.697 | 0.594 | 0.214 | 0.846 | 0.750 | 297 | 3 |
| B2c ident.+constraints | **0.943** | 0.256 | **0.014** | 0.744 | **0.833** | 297 | **0** |
| B3 batch(4) | 0.600 | 0.140 | 0.083 | 0.615 | 0.667 | 96 | 1 |

- `declared_requirements` (min_items + required_identifier) no
  bloco muda o regime do modelo: de sobre-aceitação (B1) para
  sobre-hedging (B2c — pertinent→partial/irrelevant sobe).
- B2c zerou o erro de identidade (X_code_wrong→irrelevant 3/3,
  combinação de julgamento + verificação de igualdade
  determinística — tipada, não semântica).
- B3: mesmo com 4 registros por chamada o modelo emite 1 entrada —
  **enumeração é inexistente independentemente do tamanho do lote**;
  a única superfície viável é 1-registro-por-chamada.
- `partial` continua mal discriminado (4 hits/14 misses) — o modelo
  usa a classe como hedging, não como julgamento de subtipo.
- **Gate B: FAIL** — nenhuma variante atende recall≥0.50 ∧
  precision≥0.80 simultaneamente. Sem candidato produtivo de
  julgamento nesta task (por regra, não por conveniência).

## 6. WS-C — Continuity

| Cenário | decisões (3 reps) | avaliação |
|---|---|---|
| sufficient | refine/select_other ×3 | FAIL — nunca `answer` |
| irrelevant+has_more | next_page ×3 | PASS correto |
| irrelevant last page | select_other ×2, next_page ×1 | parcial — 1 escolhe página inexistente |
| exhausted repeated | next_page ×3 | FAIL — ignora exaustão |
| partial evidence | next_page ×2, select_other ×1 | PASS |
| zero results | discovery/clarify/stop | PASS |
| ambiguous goal | next_page ×3 | FAIL — deveria clarify |

- 11/21 decisões válidas; o modelo usa coverage metadata
  parcialmente (has_more→next_page) mas não reconhece exaustão,
  suficiência ou ambiguidade.
- Segurança: nenhuma ação write/prepare proposta; loop-safety
  garantido por dedup+round-cap determinísticos (já provados R1).
- **Gate C: FAIL** — a decisão semântica de continuidade não é
  confiável; a execução bounded sim.

## 7. WS-D — Contracts & coverage

| Campo | Status |
|---|---|
| USER_GOAL/BUSINESS_SUBJECT | despachados ao juiz (verificado em payload R1.5) |
| SCOPE_CONSTRAINTS | propagado (tupla de pares) |
| **ANSWER_REQUIREMENTS** | **parser+consumidores existem; instrução `turn_goal` NUNCA o pede → sempre None → `declared_requirements` nunca chega ao juiz em produção. Gap de CONTRATO, não de modelo** |
| RECORD_IDENTITIES (code/description) | completos no payload (verificado) |
| PAGINATION/TOTAL/COVERAGE | `extract_pagination_envelope` extrai items/page/has_more/total — usável |
| PROVENANCE | preserves via facts.records |
| Continuação | `next_action` experimental existe (R1) — decisão fraca (WS-C) |

**OWNER_CONTRACT_GAP** (externo, `NEEDS_OWNER_DECISION`):
- `RESPONSIBLE_OWNER`: Domain API de busca de produtos (owner catalog).
- `EVIDENCE`: oráculo R1 — `description="terminal bala"` retorna 77
  itens e **0 pertinentes**; `conector faston` primeiro pertinente
  no rank 237. Os registros `TERM. BALA` existem (10080092/10081004
  verificados) mas o search do owner não tokeniza a equivalência.
- `REQUIRED_DECISION`: owner deve expor busca semântica/sinônimo ou
  a DÉLIA precisa de estratégia de refinamento autorizada — fora do
  escopo de implementação desta task.

## 8. WS-E — Integrated E2E

E0 = orquestração intacta; E1 = composição (admissão A1 mapeada ao
schema produtivo pós-parse — todos os gates downstream intactos +
`turn_goal` com `answer_requirements` + juiz `_b2c_judge` por-
registro com early-stop determinístico + continuação `_b_apply` R1).

| Arm | PASS | FAIL | invokes | in_tok | out_tok |
|---|---|---|---|---|---|
| E0 | 9 | 23 | 18 | 185,745 | — |
| E1 | 8 | 24 | 15 | 243,081 | — |

- PASS somente em negativos (4 cenários ×2 reps) + code_lookup E0
  rep1. Nenhuma busca por descrição converteu em nenhum braço.
- E1 executou a cadeia inteira: admissão A1 (read) → goal → select
  → invoke → juiz por-registro → continuação → resposta; vários
  cenários chegaram a GROUNDED (desc_terminal_bala, desc_borne)
  mas com menos pertinentes citados que o mínimo exigido.
- A falha E2E residual decompõe-se em: (a) recall do juiz 0.256 sob
  o regime de precisão B2c; (b) **o search do owner não retorna os
  registros pertinentes por descrição** — nem a melhor orquestração
  resolve evidência que nunca chega; (c) decisão de continuidade
  fraca (WS-C) limita o refinamento que poderia contornar (b).
- **Gate E: FAIL** para outcome — a composição não converteu
  melhoria de estágio em resultado empresarial neste corpus.

## 9. Segurança

- AUTHZ_BYPASSES=0 · UNAUTHORIZED_ACTS=0 · UNAUTHORIZED_PREPARES=0
  · FABRICATED_RECORDS=0 · UNBOUNDED_LOOPS=0
- Injection (query e record-fixture) nunca rotulada/routada como
  operação; conteúdo injetado julgado como dado.
- Remap A1→schema produtivo preserva todos os gates downstream
  (write→operational→preparação/ACT gates intactos).
- `SECURITY_TEST_COVERAGE=PARTIAL` — nenhum denied-READ real nem
  caminho PREPARE/ACT exercido (mesmo disclaimer das revisões).

## 10. Hipóteses causais consolidadas

| Cadeia | Causa provada | Status |
|---|---|---|
| owner reach | taxonomia de classes em admission (near-twins surface_inquiry/hypothetical) | PROVADA — A1 single-decision resolve |
| requirements | instrução `turn_goal` omite `answer_requirements` | PROVADA — gap de contrato localizado na linha exata |
| julgamento | enumeração impossível no 3B (collapse a qualquer batch>1); regime precisão↔recall instável | PROVADA |
| continuidade | modelo não decide stop/answer; segue apenas has_more | PROVADA |
| evidência | search do owner não resolve equivalência de vocabulário (terminal bala↔TERM.BALA) | PROVADA (oráculo) — dependência externa |
| REFUTED | "flag requires_owner_surface decide melhor que classe" (A2=A0); "batches pequenos salvam custo" | refutadas |
| INCONCLUSIVE | generalização além das famílias medidas; B2c+recall recovery | abertas |

## 11. Matriz KEEP / SIMPLIFY / EXTEND / REMOVE / OWNER_DECISION

| CHANGE_ID | RESP/OWNER | CLASS | JUSTIFICATIVA |
|---|---|---|---|
| CH-1 admission contract | capability_provision/orchestration admission stage | **SIMPLIFY** | A1 prova que uma decisão coerente `owner_access` resolve; a taxonomia de 6 classes é a causa do misrouting. Diff: instrução CRI + parser existente (mesmo schema, classes reduzidas mapeadas ao contrato atual ou novo enum) |
| CH-2 `answer_requirements` | `turn_goal` instruction resource | **EXTEND** | parser+consumidores já existem; adicionar o campo à instrução é a menor mudança possível; semântica do LLM preservada |
| CH-3 juiz por-registro | `_judge_goal_evidence` | **EXTEND (condicional)** | só após gate de recall; B2c mostra que `declared_requirements`+identidade tipada eliminam FP; falta recall — próxima iteração (B2d: relaxar hedging no contrato ou avaliar suficiência incremental) |
| CH-4 continuidade | `_apply_semantic_relevance`/next_action | **NEEDS re-design** | modelo não decide stop; opção: decisão determinística de parada (exaustão/dedup) já existe — a escolha semântica de próxima ação precisa de contrato simplificado (2-3 opções) ou de owner da decisão |
| CH-5 surface listing | admission routing `surface_inquiry` | **KEEP** | a rota de catálogo é correta; A1 a preserva como classe `catalog` |
| CH-6 search owner | Domain API produtos | **NEEDS_OWNER_DECISION** | gap de vocabulário provado; nenhuma implementação paralela na DÉLIA |
| CH-7 `_b_apply`/`next_action` | harness | REMOVE_CANDIDATE | contrato experimental atual não promove (WS-C fail) |

## 12. Proposta mínima de implementação (task posterior)

1. **CH-1** — admission: instrução CRI com decisão `owner_access`
   (read/write/catalog/none) + parser mapeando à decisão existente
   (surface_inquiry↔catalog; operational↔read/write; demais↔none).
   Testes: corpus WS-A + negativos; regressão em `surface_inquiry`
   legítimos.
2. **CH-2** — `turn_goal`: adicionar `answer_requirements` à
   instrução (spec do campo já existe no parser). Testes:
   min_items extraído em quantified goals; null em unquantified.
3. **CH-3 (condicional)** — juiz por-registro somente se a próxima
   iteração atingir recall≥0.50 ∧ precision≥0.80 ∧ ident-FP=0.
4. Não incluir: next_action (re-design separado), batches (refutado).
5. `ROLLBACK`: todas as mudanças são instruções CRI + um estágio
   opcional — reversão = restaurar instruções anteriores; sem
   mudança de dados ou contratos de owner.

## 13. Limitações

- Corpus concentrado em elétrica/conexão; holdout pequeno (4).
- `answer_requirements` testado apenas como variante de instrução —
  a extração real pelo 3B dentro de E1 não foi medida isoladamente.
- B2c usado em E1 apesar do gate de recall (disclosed) — mede o
  melhor caso sob juiz precision-first.
- Custos medidos em unidades do instrumento local; paralelização de
  chamadas por-registro é hipótese não testada.
- AuthZ-negada e PREPARE/ACT não exercidos (cobertura parcial).

## 14. Próximo bounded step

1. Implementar CH-1+CH-2 (task produtiva separada, com testes).
2. Uma iteração de julgamento por-registro focada em recall
   (contrato B2d: mesmo bloco, instrução sem over-hedging, gates
   idênticos congelados aqui).
3. Re-decisão sobre continuidade após CH-3 (avaliar se o loop vale
   o custo com decisão de parada determinística).
4. Escalar OWNER_CONTRACT_GAP ao owner da Domain API.

## 15. Artefatos

- `delia-api/scripts/integrated_intelligence_eval.py`
- `docs/.../evidence/integrated-intelligence-runs.json`
- Doc 168 + Execution Ledger.
