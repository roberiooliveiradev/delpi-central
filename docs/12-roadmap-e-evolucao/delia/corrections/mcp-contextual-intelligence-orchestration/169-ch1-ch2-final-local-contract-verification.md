# DÉLIA — CH-1 / CH-2 Final Local Contract Verification

**Task:** `DELIA-C3-CH1-CH2-FINAL-LOCAL-CONTRACT-VERIFICATION-01`
**Tipo:** verificação local fechada e decisão de prontidão de implementação.
**Escopo:** ZERO mudança de código produtivo, instrução ativa, modelo, consulta de
produção ou deploy. Todas as variantes foram harness-only.

## 1. Reancoragem

- `BASE_HEAD=aeb557a37e` (revisão independente do doc 168)
- `EVALUATED_SHA=9b0b6c93` (origin/main avançou durante a execução —
  `484f39441a`, `8c1f68b3d6`, `5bd8ca1e3a` — rebase preservou trabalho concorrente)
- `WORKTREE_STATUS=clean` (apenas artefatos experimentais novos)
- `AUTHORITIES_READ=16→50→17→49→51→52→21→20→25` + docs 163–168 +
  revisão independente `aeb557a37e` + Execution Ledger
- `CURRENT_PHASE=C3` — `CP_RQ=NOT_ADVANCED`

## 2. Contratos existentes e Reuse Gate

| Seam | Owner | Consumidor | Decisão |
|------|-------|-----------|---------|
| `interaction_admission` / `_admit_conversational_turn` | orchestration.py | roteamento owner-path vs surface vs conversa | REUSE |
| `turn_goal` / `_understand_goal` / `_turn_goal_from_proposal` | orchestration.py | `_TurnGoal.answer_requirements` | REUSE |
| `parse_answer_requirements` | outcome_assessment.py | judge `declared_requirements` | REUSE |
| `select_group` / `select_capability` / CRI resources | orchestration.py | inalterados | REUSE |
| Harnesses docs 165–168 (`iterative_research_eval`, `integrated_intelligence_eval`, `semantic_judgment_reach_eval`) | scripts/ | oracles, `_spy_wire`, `_StageLog`, `_classify` | REUSE |

Nenhum planner, engine, adapter ou mecanismo de autorização novo foi criado.

## 3. Baseline congelada

- `MODEL_ID=delia-json:latest` `MODEL_DIGEST=7b8f4ab14fc1`
- `MODEL_CONFIG=qwen2.5:3b Q4_K_M ctx=8192 JSON-only`
- Instruções produtivas, catálogo e contrato do owner **inalterados** durante
  toda a execução. Variantes existem apenas dentro do harness.

## 4. Protocolo (congelado antes da medição)

- **CH-1** — corpus de 23 consultas (dev + holdout), 3 repetições;
  braços A0 (produção) e A1 (contrato coerente `owner_access` do doc 168) +
  verificação A2-compat (remap do acesso A1 para o schema produtivo).
- **CH-2** — 14 casos (quantificados, não-quantificados, restrições, código,
  comparação, WRITE, hipotético, holdout), 3 repetições; braços G0 (instrução
  produtiva) e G1 (G0 + declaração mínima do campo `answer_requirements`).
- **Combinado** — C0/C1 (admissão coerente remapeada + instrução de goal com
  campo) sobre o corpus E2E congelado de 16 cenários × 2 reps = 32 execuções
  por braço. Gates isolados falharam → classificado como **controle
  exploratório**, não elegível para gate (§17 da tarefa).

## 5. CH-1 — Admission Contract Simplification

Gates congelados: read_recall ≥0.85; non_owner_spec ≥A0; catalog_acc ≥A0;
write/PREPARE sem conversão indevida; inject→none em todas as reps; 0 outputs
inválidos; schema compatível.

| Métrica | A0 (produção) | A1 (coerente) |
|---------|---------------|----------------|
| acc_dev | 0.529 | **0.804** |
| acc_holdout | 0.467 | **0.600** |
| read_recall | 0.622 | **0.978** |
| non_owner_spec | 0.200 | 0.400 |
| catalog_acc | 0.500 | **0.000** |
| write_safety | false (write→read) | **true (6/6)** |
| inject→none (todas reps) | false | **false (2/3)** |
| invalid | 0 | 0 |

Achados:

- O ganho de reach se reproduz (0.622→0.978) e a segurança WRITE melhora
  drasticamente — A0 classificava `write_ask`/`prepare_ask` como `read`; A1
  os classifica `write` em 6/6.
- **Regressão catalog:** a variante possui a classe `catalog` mas o modelo a
  subutiliza — 6/6 consultas de catálogo/discovery roteadas a `read`.
  Sobre-admissão na direção segura (path READ governado alcança as caps de
  discovery), mas viola o gate congelado de preservação de catálogo.
- **Instabilidade inject:** 2/3 reps → `none`; rep1 → `read` (path
  governado, nunca write, mas inconsistência sobre negativo).
- Compat A2: o remap para o schema produtivo é válido por construção —
  a comparação por label de 4 classes colapsa write→read porque a admissão
  produtiva não distingue os dois (ambos vão ao owner path).

**CH1_GATE=FAIL** → `CH1_IMPLEMENTATION_READY=NO` — veredito **REWORK**.

Residual específico: discriminação `catalog`/`none` na redação do contrato —
não é falha conceitual (a decisão coerente provou-se correta para read/write),
mas o contrato como especificado não preserva catálogo nem é estável no
negativo de injeção. Uma iteração de redação futura pode revisitar; **esta
task não itera variantes** (braços congelados).

## 6. CH-2 — Answer Requirements Extraction

Gate congelado: extrair quantidades declaradas; preservar não-quantificados;
sem regressão de goal/subject/restrições; compatibilidade com consumidores;
estabilidade entre reps; negativos corretos.

| Métrica | G0 (produção) | G1 (campo declarado) |
|---------|---------------|----------------------|
| qty_recall | 0.000 | **0.000** |
| qty_exact | 0.000 | 0.000 |
| unq_null | 1.000 | 1.000 |
| goal_class acc | 0.718 | 0.641 |
| subject_hit | 0.857 | 0.857 |
| invalid | 0 | 0 |
| declared_when_req | (vacuo) | (vacuo) |

Diagnóstico de causa:

- A instrução G1 despachada **contém** a especificação do campo (verificado no
  harness — `"answer_requirements": {"min_items": N}; null otherwise`).
- Proposta crua inspecionada: o modelo emite apenas
  `{"goal_class","business_subject"}` — o campo está **ausente**, não
  malformado. `parse_answer_requirements` nunca é exercido com dado real.
- Parser fail-closed confirmado: não-mapping rejeitado; `min_items`
  string/negativo/enorme→`None`; `{}`→`None`; campos desconhecidos rejeitados.
- Regressão leve de `goal_class` (0.718→0.641) — adicionar o campo piora
  marginalmente a fidelidade de classe.

**CH2_GATE=FAIL** → `CH2_IMPLEMENTATION_READY=NO` — veredito **REWORK**.

Hipótese refutada: "declaração mínima do campo basta" é **falsa** no
qwen2.5:3b congelado — o modelo ignora campos de instrução que não reconhece
como essenciais. O gap do doc 168 é real (a instrução não pedia o campo), mas
pedir o campo não resolve. Extração de `answer_requirements` exige mecanismo
diferente (ex.: exemplar few-shot na instrução, ou um estágio dedicado de
proposta de requisitos) — decisão da coordenação, fora desta task.

## 7. Combinado (controle exploratório — não elegível)

| | C0 | C1 (A1+G1) |
|--|-----|------------|
| PASS | 9/32 | 10/32 |
| owner_invokes | 15 | 17 |
| tokens in | 168,396 | 226,354 (+34%) |
| tokens out | 4,918 | 6,813 |
| errors (invalid_model_output) | 1 | 2 |

- Δ+1 = ruído; nenhum ganho de Business Outcome, consistente com o doc 168:
  gargalos downstream inalterados (vocabulario do search owner + recall do
  juiz + continuidade).
- `stages` não populados neste harness (instrumentação limita evidência do
  combinado a outcome/grounding/invokes/tokens — evidência por estágio coberta
  pelas WPs isoladas). **Limitação divulgada.**
- `h_doc_manual`: `invalid_model_output` ×3 (C0×1, C1×2) — falha fechada,
  sem efeito colateral.
- Nenhuma regressão de contrato observada mecanicamente; composição roda o
  loop produtivo real com gates downstream intactos.

## 8. Segurança

- `AUTHZ_BYPASSES=0` `UNAUTHORIZED_ACTS=0` `UNAUTHORIZED_PREPARES=0`
  `FABRICATED_RECORDS=0`
- WRITE/PREPARE: A1 classifica corretamente `write` → path governado, jamais
  executado; A0 era pior (classificava write como read).
- Sobre-admissão observada sempre na direção segura (READ governado), nunca
  em direção a write/ACT.
- `SECURITY_TEST_COVERAGE=PARTIAL` — sem denied-READ real exercido (mock
  local; evidência simulada onde aplicável).
- Invariantes preservadas: `IDENTITY→LIVE CORE AUTHZ→DOMAIN AUTHORITY`,
  `READ!=WRITE`, `PREPARE!=ACT`, `DISCOVERY!=APPROVAL`, `MODEL OUTPUT!=FACT`.

## 9. Custo

- CH-1: ~140 model calls (23q × 3 reps × ~2 braços + remap).
- CH-2: 84 calls + 5 parser checks.
- Combinado: ~300 calls; 394,750 in / 11,731 out tokens (ambos braços).
- Total ~520–550 calls, latência ~50 min.

## 10. Decisão

| Mudança | Gate | Veredito | Bloqueio específico |
|---------|------|----------|---------------------|
| CH-1 | FAIL | **REWORK** | catalog_acc 0.0 (regressão); inject 1/3→read |
| CH-2 | FAIL | **REWORK** | qty_recall 0.0 — campo ausente de todas as propostas |

Nenhuma mudança é `IMPLEMENTATION_READY`. Não há proposta de diff mínima —
os gates falharam; promover qualquer uma violaria os critérios congelados.
Esta é uma decisão de **não-promoção** com residuais específicos documentados
para re-trabalho futuro, não uma indicação de que a direção está errada: a
decisão coerente de admissão provou-se conceitualmente correta para
read/write (reach 0.978, write_safety 6/6) e o parser de requirements é
correto — os contratos como especificados é que não passam.

## 11. Próximo bounded step (sugestão para coordenação)

- CH-1-R: revisão de redação do contrato coerente com discriminação explícita
  catalog/none + re-verificação nos mesmos gates congelados (braço novo
  autorizado apenas por task futura).
- CH-2-R: mecanismo alternativo de extração de requisitos (few-shot ou
  estágio dedicado) — hipótese de instrução-mínima encerrada.
- Escalar ao owner Domain API o gap de vocabulário do product-search
  (`terminal bala` → 0/77 pertinentes; `TERM. BALA` existe) — **limita todo
  outcome E2E independentemente de orquestração**.

---
`DEPLOY=NO` `INDEPENDENT_REVIEW=PENDING` `PRODUCTION_CODE_MODIFIED=NO`
`PRODUCTION_INSTRUCTIONS_MODIFIED=NO` `MODEL_CHANGED=NO`
`PRODUCTION_QUERIES=0`
