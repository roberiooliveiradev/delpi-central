# 171 — DÉLIA · Model-Neutral Operational Intelligence · P0–P2 Closed Validation

**Task:** `DELIA-C3-MODEL-NEUTRAL-ORCHESTRATION-P0-P2-CLOSED-VALIDATION-01`
**Direção primária:** Documento 170 (PD-1 model-neutral, PD-2 grounded
investigation, PD-3 semantic-simplification). **Escopo:** P0+P1+P2
fechados. ZERO mudança de código/instrução/modelo/deploy/consulta
produtiva.

## 1. Reancoragem (P0)

- `BASE_HEAD=5c70eed4db` `ORIGIN_MAIN=5c70eed4db` `WORKTREE_STATUS=clean`
- `AUTHORITIES_READ=16→50→17→49→51→52→21→20→25` + docs 163–170 +
  ledger em HEAD
- `CURRENT_PHASE=C3` `CURRENT_NEXT=P3 (coordenação)` `CP_RQ=NOT_ADVANCED`
- Nenhum conflito entre doc 170 e autoridades superiores.

## 2. Inventário real da orquestração (P0)

Caminho verificado em código (`orchestration.py::_attempt`, L4227+):

| # | Estágio | Owner | LLM? | Contrato | Segurança |
|---|---------|-------|------|----------|-----------|
| 1 | `_admit_conversational_turn` | orch | sim (`interaction_admission`) | class + owner_required | admissão barata antes do catálogo; `surface_inquiry`→projeção determinística |
| 2 | `_groups` + `_project_surface` | orch | não | CapabilityGroup/surface | catálogo live, falhas tipadas |
| 3 | `_understand_goal` / `_turn_goal_from_proposal` | orch | sim (`turn_goal`) | `_TurnGoal` tipado | parser fail-closed |
| 4 | `_select_target`→`_select_group`→`_select_capability_with_goal` | orch | sim (`select_group`, `select_capability`) | group_key+descriptor(+goal tipado — seam I02-R3B) | capability binding por contrato |
| 5 | reconciliação de intent (write-class vs declared goal) | orch | não | `_WRITE_OPERATION_CLASSES` | demote/clarify fail-closed |
| 6 | `_invoke_selected`→`_propose_candidate_arguments`→AuthZ→`_invoke` | orch+ports | sim (`candidate_arguments`) | argumentos schema-validados | Core/Domain AuthZ, operation class |
| 7 | `_judge_goal_evidence` | orch | sim (`goal_evidence_relevance`) | bloco business_subject/constraints/records | proposta, nunca autoridade |
| 8 | suficiência determinística + `_recover_relevance` | orch | parcial | dedup+bounds+round caps | continuation bounded por deadline |
| 9 | `_apply_outcome_assessment`→`_synthesize_content` | orch | sim (`grounded_synthesis`) | outcome+grounding | provenance, limitations tipadas |
| — | foreign path (`_assess_native_path`/`_select_foreign_capability`/`_invoke_foreign_evidence`) | orch | sim | governed knowledge seam | identidade/AuthZ preservadas |
| — | prepare/act (`_attempt_prepare`/`_execute_prepared_act`/`_invoke_act`) | orch | sim | PREPARE≠ACT | confirmação obrigatória |

14 instruction IDs governados em CRI (`orchestration_instructions
.delpi.json`), fail-closed por composition.

### Matriz de responsabilidades (P0.4.1)

- **KEEP:** todos os estágios 1–9 + gates AuthZ + deadline + dedup +
  provenance + outcome. Nenhum mecanismo é duplicado — a cadeia é
  economicamente mínima em gates determinísticos.
- **SIMPLIFY (candidato, condicional):** admission → decisão coerente
  única de `owner_access` (A1/A3). Evidência: read reach 0.978/0.744,
  write 6/6 — porém a fronteira catalog/read é instável no 3B (abaixo).
- **EXTEND (existente, não criar):** `_select_capability_with_goal`
  já transporta goal tipado com a seleção (I02-R3B) — fusão
  goal+selection disponível sem mecanismo novo; `prior_continuation`
  já transforma evidência OBSERVATION sem nova chamada de owner.
- **REMOVE_CANDIDATE:** nenhum — remoção exige prova de equivalência
  que não existe.
- **NEEDS_OWNER_CONTRACT:** vocabulário do product-search da Domain
  API (`terminal bala`→0/77 pertinentes com `TERM. BALA` existentes).

### Reuse Gate (P0.4.2)

Todas as necessidades da composição candidata foram satisfeitas por
mecanismos existentes: `_propose`, CRI instructions, ADMISSION_MAP
(remap para o schema produtivo), `_spy_wire`/`_StageLog`/oracles dos
harnesses 165–169. `EXISTING_EQUIVALENT=YES` para cada item;
`REUSE_DECISION=REUSE` (nenhum planner/engine/adapter/registry novo).

## 3. Baseline congelada (P0.5)

- `MODEL_ID=delia-json:latest` `MODEL_DIGEST=7b8f4ab14fc1`
  `MODEL_CONFIG=qwen2.5:3b Q4_K_M ctx=8192 JSON-only`
- Instruções/catálogo/owner-contract inalterados; variante apenas no
  harness. Arquitetura candidata model-neutral (sem branch por nome
  de modelo).
- Corpus: P1 = 22 consultas congeladas (doc-169 CH-1) ×3 reps;
  P2 = 16 cenários E2E congelados ×2 reps por braço.
- Gates P1 congelados pré-medição: read_recall ≥0.85; non_owner_spec
  ≥A0; catalog_acc ≥A0; write/PREPARE sem colapso; inject→none em
  todas as reps; holdout ≥A0; 0 invalid.
- Orçamento: ~500 calls; deadline por turn `TURN_BUDGET_S`; sem
  paralelismo.

## 4. Hipóteses (P1.6.2)

- **H1 — redundância de classificação:** PARCIALMENTE SUPORTADA.
  A decisão coerente única funciona para read/write; a fronteira
  catalog↔read não é estável no modelo congelado — limitação de
  capacidade, não de desenho de contrato.
- **H2 — fragmentação de seleção:** moderada; select_group +
  select_capability são 2 chamadas — fusível via contrato existente
  (goal já pode viajar com seleção), mas não avaliada nesta task
  (fora do menor candidato).
- **H3 — pertinência vs suficiência:** separação correta (LLM
  propõe correspondência; determinístico mede suficiência). Manter.
- **H4 — continuidade:** `_recover_relevance` existe e é bounded;
  falha residual é decisão stop/answer do modelo (doc 168 WS-C).
- **H5 — contrato insuficiente:** `answer_requirements` refutado em
  doc 169 (instrução-mínima não basta no 3B); fora do candidato.

## 5. Candidato mínimo (P1)

**A3 — admissão coerente refinada.** Mesmo schema JSON de A1
(`owner_access`+`reason`); refinamento confinado às definições de
classe — os dois residuais diagnosticados do CH-1: (a) `catalog`
ganha semântica explícita de meta-pergunta (cobertura/superfície vs.
pedido de registro); (b) `none` ganha secrets/system-internals/
override-attempts. Restante da orquestração = produção intacta.

## 6. Resultados P1 (22q × 3 reps)

| Métrica | A0 | A3 |
|---------|-----|-----|
| acc_dev | 0.627 | 0.686 |
| acc_holdout | 0.467 | **0.733** |
| read_recall | 0.744 | 0.744 |
| catalog_acc | 1.000 | 0.833 |
| write_safety | FAIL (write→read) | **6/6** |
| inject→none | FAIL | **3/3** |
| compat remap | — | 0 mismatch |
| invalid | 0 | 0 |

Achados:

- O refinamento **corrigiu** os residuais do CH-1: inject→none 3/3,
  catalog 5/6 (vs 0/6 em A1), write 6/6, melhor holdout observado
  (0.733).
- **Mas o trade off moveu-se:** as consultas documentais
  (`guide_process`, `guide_format`, `guide_product` — expected
  `read`) passaram a `catalog` — a definição de meta-pergunta
  capturou perguntas que exigem conteúdo do owner. read_recall caiu
  de 0.978 (A1) para 0.744.
- Diagnóstico: fronteira "meta-pergunta sobre superfície" vs
  "pedido de documentação/conteúdo" não é estável sob formulações de
  contrato no 3B — o erro migra entre lados da fronteira conforme a
  redação. Limitação de capacidade do modelo, consistente com PD-1.

**P1_GATE=FAIL** — read_recall 0.744 < 0.85; catalog_acc 0.833 < A0
1.0 (nesta execução A0 acertou 6/6 — variância: doc 169 mediu A0=0.5).

## 7. Resultados P2 (controle exploratório — não elegível)

E1 executado como diagnóstico (gate P1 falhou; §9.1):

| | E0 | E1 (A3) |
|--|-----|---------|
| PASS | 9/32 | 10/32 |
| owner_invokes | 13 | **20** |
| tokens in | 157,101 | 193,819 (+23%) |
| tokens out | 4,833 | 5,755 |
| errors | 1 | 0 |

- Δ+1 = ruído. E1 alcança o owner muito mais (`desc_borne`×2,
  `olhal`×1, `h_desc_disjuntor`, `h_desc_ilhos`, `terminal_bala`×2 —
  todos GROUNDED com evidência) e **não converte**: evidência chega,
  julgamento/continuidade downstream falha — gargalo confirmado a
  jusante da admissão (docs 168/169).
- Negativos preservados nos dois braços; nenhuma conversão
  WRITE/PREPARE indevida; 0 fabricated records; 0 authz bypass.

## 8. Segurança

`AUTHZ_BYPASSES=0` `UNAUTHORIZED_ACTS=0` `UNAUTHORIZED_PREPARES=0`
`FABRICATED_RECORDS=0` `UNBOUNDED_LOOPS=0`
`SECURITY_TEST_COVERAGE=PARTIAL` (sem denied-READ real; mocks
declarados). Sobre-admissão sempre na direção READ governada.
Invariantes READ≠WRITE / PREPARE≠ACT / MODEL OUTPUT≠FACT
preservadas.

## 9. Decisão

**`P0_GATE=PASS`** (inventário+reuse completos) → **`P1_GATE=FAIL`**
→ **`P2_GATE=NOT_APPLICABLE`** (E1 exploratório, sem evidência de
ganho) → veredito final:

## **`NO_PROMOTION`**

- Nenhuma composição avaliada atende aos gates congelados; a menor
  mudança promissora (admissão coerente) desloca o erro na fronteira
  catalog/read em vez de eliminá-lo — limitação de capacidade do
  modelo congelado, não de contrato.
- Nenhum ganho de Business Outcome em qualquer braço experimental
  desde o doc 165 — o outcome permanece limitado por: (a) vocabulário
  do search da Domain API (`NEEDS_OWNER_DECISION`), (b) recall do
  julgador sob precisão, (c) decisão de parada da continuidade.
- **KEEP** todo o runtime atual — nenhum estágio provou-se
  removível; as duplicações reais (admissão↔goal, goal↔seleção)
  existem mas sua fusão não melhora outcome enquanto os gargalos de
  jusante persistirem.
- Pacote P3: ver seção 10 — nenhum diff promovível; recomendação de
  manter baseline e tratar dependências externas.

## 10. Pacote para decisão P3 (coordenação)

| Item | Owner | Contrato | Evidência | Classificação |
|------|-------|----------|-----------|---------------|
| Admissão coerente única | orchestration | instruction CRI `interaction_admission` | reach +write segurança ganhos reais; fronteira catalog instável no 3B | SIMPLIFY-condicional: revisitar sob modelo mais capaz (PD-1) — hoje NO_PROMOTION |
| Goal tipado via seleção | orchestration | `_select_capability_with_goal` (I02-R3B) | seam existe em produção, reduziria 1 chamada LLM no cold-start | EXTEND-candidato para P3 futuro com eval próprio |
| `answer_requirements` | outcome_assessment | parser pronto | instrução-mínima REFUTADA (doc 169) | NEEDS mecanismo diferente (few-shot/estágio dedicado) |
| Julgamento por registro | outcome_assessment | B2c precision 0.943/recall 0.256 | gate de recall falhou | HOLD — depende de capacidade de modelo |
| Search de produto | Domain API | owner contract | 0/77 `terminal bala`; `faston` rank 237 | NEEDS_OWNER_DECISION — bloqueia todo outcome E2E |
| Continuidade next_action | orchestration | contrato experimental falhou | stop/answer não confiável | REWORK (fora desta task) |

**Recomendação P3:** manter baseline produtivo inalterado; a
hipótese estrutural mais forte continua sendo o contrato de search
da Domain API (owner), e a capacidade do modelo (PD-1) para as
fronteiras semânticas instáveis. Nenhum diff de orquestração
demonstra melhoria de Business Outcome no estado atual.

## 11. Limitações

- Stage-trace por cenário não populado no harness E2E (evidência por
  estágio coberta pelas WPs isoladas) — divulgado.
- Variância do A0 entre execuções (catalog 0.5→1.0) — 3B estocástico;
  gates comparativos absorvem parcialmente.
- AuthZ negado real não exercitado (ambiente local).
- Generalização restrita às famílias do corpus congelado.

---
`DEPLOY=NO` `INDEPENDENT_REVIEW=PENDING` `PRODUCTION_CODE_MODIFIED=NO`
`PRODUCTION_INSTRUCTIONS_MODIFIED=NO` `MODEL_CHANGED=NO`
`PRODUCTION_QUERIES=0` `PHASE_ADVANCED=NO`


## 12. Revisão independente da coordenação — 2026-10-27

**PARECER: ACCEPT_WITH_RESIDUAL para execução documental/experimental P0–P2; P3 DECISION=NO_PROMOTION; IMPLEMENTATION_AUTHORIZED=NO.** Revisão estática do Documento 171 na main `0d65aac21a6680d12bf78cc8612471966bc9fe6d`. Não houve reexecução independente de modelo local, autorização Core/Domain nem deploy. A baseline e o produto permanecem inalterados.

**Gates e Outcome:** P1 A3 falhou nos critérios congelados: READ recall 0.744 < 0.85 e catálogo 0.833 < A0 1.0. O E1 da P2 foi exploratório por P1=FAIL: E0 9/32, E1 10/32, sem demonstração de melhora de Business Outcome, com +23% tokens de entrada. Portanto não há candidato elegível ao P3. Manter `P2_GATE=NOT_APPLICABLE` e `NO_PROMOTION`, sem transferir ganhos de estágio para autorização produtiva.

**Limites das inferências:** a frase 'orquestração não é mais o gargalo' NÃO está provada. Admission ainda reduz READ reach nos casos documentais, o julgador rejeita relevantes e o loop de continuação tem decisões de stop/answer inadequadas: estes são mecanismos internos da orquestração e continuam gargalos observados, ao lado da busca do Domain owner. O exemplo `terminal bala` sem resultados pertinentes para aquele contrato de consulta não prova que a Domain API seja *o principal limitante de todas as famílias* nem que só um modelo maior resolva os erros de classificação. A afirmação de 'limitação de capacidade do 3B, não de contrato' é hipótese plausível, mas não isolada por comparação controlada entre modelos nem por contratos equivalentes. O `goal-via-selection` oferece seam de reuso, mas a suposta economia de uma chamada é TARGET, não medição.

**Pesquisa encerrada:** este plano fechado termina em `NO_PROMOTION`; não iniciar ciclos de prompts A4/CH-1-R/CH-2-R ou reescrita de judges automaticamente. Preservar a direção aprovada no Documento 170 (model-neutral, investigação grounded/parciais, simplificação por reuse). Próxima ação de coordenação deve ser **decisão de roadmap/produto**, com ownership separado para Domain API e, se autorizado, comparação de capacidade/modelo com métricas de segurança/custo; não vender isso como etapa produtiva já aprovada. `SECURITY_TEST_COVERAGE=PARTIAL`: denied READ e material PREPARE/ACT não exercidos. Documento 171 não altera fase, CP/RQ, contratos ou deploy.
