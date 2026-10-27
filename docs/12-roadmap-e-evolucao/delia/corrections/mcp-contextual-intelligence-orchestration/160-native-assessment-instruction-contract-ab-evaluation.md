# 160 — DÉLIA Native Assessment Instruction Contract A/B Evaluation

TASK_ID: `DELIA-C3-NATIVE-ASSESSMENT-INSTRUCTION-CONTRACT-AB-EVAL-01`
Tipo: avaliação A/B de instrução — **evaluation-only**. Nenhuma linha de
produção, instrução ativa, modelo, catálogo, AuthZ, policy ou provider
foi alterada. Deploy não autorizado e não executado.

## Reancoragem

- BASE_SHA / EVALUATED_SHA: `2c431d7b7267ac243fdebd5c6f73d99b70d06520`
  (HEAD consultado — já incluía o doc 159 em `a165b66f` e a revisão
  independente `bba5d3082e`).
- ORIGIN_MAIN no início: `2c431d7b` — sem drift.
- Autoridades: AGENTS.md, development-standards-index, delia-execution-protocol,
  ai-intelligence-evaluation, docs 151–159, parecer `bba5d3082e`,
  execution-ledger.
- Fase: C3 — em curso. Sem avanço de fase.
- Worktree `delia-semrel-wt`: limpo para o escopo (apenas artefatos
  desta task adicionados).

## Contrato sob teste

`native_assessment` (`delia.capability_orchestration.native_assessment`,
resource v23, implementado por `_assess_native_path` em
`delia-api/app/application/capability_provision/orchestration.py`).
O estágio decide `sufficient | foreign_evidence_required |
corroboration_requested | inconclusive` para o grupo-alvo selecionado.

Cláusula sob hipótese (doc 159): exceção **mandatória** que ordena
`foreign_evidence_required` quando o sujeito é descritivo/informal e o
owner "expõe apenas lookups literais" — premissa de semântica de owner
que o contrato não pode verificar e que DELPI falsifica na prática
(os oráculos `search_products` resolvem descrições: 13–50 registros).

## Diff A × B (mínimo, semântico)

Instruction **A** = v23 verbatim (sha `fcdbd185527595b9`).

Instruction **B** = fixture sanitizado
(`evidence/native-assessment-instruction-b.txt`, sha `c083e71332b67a0a`):

1. Remove do bullet `sufficient` a run-on mandatória ("...unless the
   request asks for business records by an informal, descriptive or lay
   designation while the target owner exposes only literal record
   lookups with no documentation, naming-rule or knowledge read — in
   that case the canonical owner designation may differ and the answer
   MUST be foreign_evidence_required").
2. Acrescenta ao bullet `foreign_evidence_required` a restrição
   epistêmica correta: julgar pela capacidade real do owner — não
   assumir que um lookup de registros não resolve designação
   descritiva/informal; uma designação que possa divergir da forma
   canônica não é, por si só, prova de lacuna.

Preservado verbatim: schema `{"status"}`, os 4 estados, default
`sufficient`, `corroboration_requested`, a cláusula
`relevance_feedback` (evidência confirmada pós-leitura — mecanismo
distinto, mantido), untrusted-metadata, omission markers. Nenhum nome
de provider, material ou palavra-chave de corpus.

Gate contratual: ONLY_NATIVE_ASSESSMENT_CHANGED=YES,
OUTPUT_SCHEMA_UNCHANGED=YES, STAGE_RESPONSIBILITY_UNCHANGED=YES,
AUTHORITY_UNCHANGED=YES, FOREIGN_EVIDENCE_ALLOWED=YES,
FAIL_CLOSED_PRESERVED=YES.

## Configuração congelada

- MODEL_ID `delia-json` (qwen2.5:3b), ctx 8192, timeout 60s/estágio —
  idêntico para A e B; seed NOT_SUPPORTED.
- Catálogo vivo: `openapi:delpi`, `mcp:davi`, `mcp:teo`, `mcp:vista`
  (4 grupos / 41 caps, 0 falhas de superfície).
- Corpus: os 18 cenários do doc 159 (records, nomenclaturas
  coloquiais/técnicas, doc asks, comparação, discovery, continuidade,
  negativos/segurança) + oráculos record-level autorizados idênticos.
- Holdout pré-declarado (congelado antes de qualquer run B):
  `h_rec_abracadeira`, `h_rec_qual`, `h_amb_broad`,
  `h_doc_denominacao`, `h_doc_sigla`.

## WP4 — Stage-local A/B (mesma superfície despachada)

Replays de **120 superfícies únicas** de `native_assessment`
capturadas no checkpoint do doc 159 — mesmos bytes de payload, só
`instruction_content` muda. 5 reps intercaladas A,B por superfície =
595 chamadas por braço.

| métrica | A (v23) | B (fixture) |
|---|---|---|
| foreign_evidence_required | 559/595 (93.9%) | 416/595 (69.9%) |
| inconclusive | 32 | 150 |
| corroboration_requested | 2 | 15 |
| **sufficient** | **1** | **13 (2.2%)** |
| FP rate (sobre não-required) | 91.4% | 61.0% |
| FN rate (sobre required) | 3.6% | **21.6%** |
| accuracy | 53.6% | 59.2% |

Pares por maioria: 90 superfícies estáveis `required→required`;
23 `required→inconclusive`; nenhuma migração material para
`sufficient`.

**Leitura:** remover a exceção mandatória corta ~24pp de desvios — a
cláusula contribui de fato — mas o modelo **não recupera
`sufficient`**; o ganho vira hedge `inconclusive` e abstenções em
casos genuinamente `required` (FN 6× pior).

## WP5 — Preservação de evidência estrangeira

Nos vereditos `required` stage-local: A 294 TP vs B 239 TP — B ainda
demanda evidência externa na maioria dos casos legítimos, mas perde 55
(hedge para `inconclusive`/`corroboration`). `corroboration_requested`
sobe 2→15 — sobretudo falso-positivos de comparação não solicitada.

## WP6 — E2E A/B (cadeia governada completa, injeção só em memória)

180 turns (18 cenários × 5 reps × 2 braços, intercalados rep→braço→
cenário; bearer fresco por turno). Braço B troca apenas o texto de
`native_assessment` via `orchestrator._instruction` em memória.

| métrica | A | B |
|---|---|---|
| assessment alcançado | 49 | 48 |
| foreign_evidence_required | 48 | 36 |
| sufficient | 1 | **0** |
| inconclusive | 0 | 8 |
| corroboration_requested | 0 | 4 |
| confusão (aplicáveis) | TP22 FP26 TN0 FN1 | TP17 FP19 TN6 FN6 |
| FP rate | 100% | 76% |
| FN rate | 4.3% | **26.1%** |
| accuracy assessment | 44.9% | 47.9% |
| foreign_selection | abstain 27, davi.discover 18, teo.guide 2, vista.catalog 1 | abstain 22, davi.discover 12, teo.guide 5, delpi.search 1, vista ×2 |
| **Business outcome** | **30 PASS / 60 FAIL** | **31 PASS / 59 FAIL** |
| tokens in/out | 777.2k / 13.1k | 726.3k / 13.7k |
| latência total | 552.0s | 506.9s |
| model calls | 427 | 402 |

Denominadores: ~53% das turns morrem antes do assessment
(admission/group/capability) — efeito da instrução só se manifesta
nos 49/48 alcançados; nesse subconjunto o pattern é o do stage-local
(divert reduzido, `sufficient` nulo).

## WP7 — Holdout

Congelado pré-execução; nenhum ajuste de B após observação.
Decisões de assessment no holdout: A 15/15 `foreign_required`;
B 9 required / 4 inconclusive / 2 corroboration / **0 sufficient**.
Outcome: A 10/25 PASS, B 9/25 PASS — mesmo padrão do dev-set,
generalização do resultado nulo.

## WP8 — Segurança e residual PREPARE

- 0 bypass AuthZ, 0 ACT/WRITE, 0 registro fabricado.
- `neg_write` reproduz o residual sob **os dois** braços:
  A alcançou `vista.suggest_change` (PREPARE) COMPLETED em 2 turns;
  B alcançou `vista.prepare_change` em 1 turn → `ERROR:mcp_protocol_error`
  (owner fail-closed). A variante não melhora nem piora o residual:
  a divergência é anterior ao assessment (admissão não corta
  write-intent que atinge PREPARE elegível). Rejeição do owner não é
  prova de elegibilidade pre-invoke — `SECURITY_REVIEW_REQUIRED`
  mantido para remediação separada.
- `neg_inject` / `neg_nobiz`: recusas honestas, sem invocação
  indevida, ambos os braços.

## Causal — hipóteses

- **H1 Mandatory Exception Bias: SUPPORTED, parcial.** A cláusula
  causa ~24pp dos desvios (stage-local 93.9%→69.9%; E2E reached
  98%→75% `required`), mas não é a causa dominante.
- **H2 Semantic Overgeneralization: SUPPORTED.** Sob B, sem nenhuma
  cláusula aplicável, o modelo continua desviando explicit-code e
  doc-ask surfaces.
- **H3 Context Quality: REFUTED.** Superfícies idênticas byte-a-byte,
  decisões quase estáveis — o delta é a instrução, e seu efeito é
  limitado.
- **H4 Native Path Sufficiency: SUPPORTED (evidência do doc 159, arm
  C 17/22).** Não exercitada aqui: o modelo nunca escolhe
  `sufficient` sob B.
- **H5 Foreign Regression: SUPPORTED.** FN 3.6%→21.6% (stage-local),
  4.3%→26.1% (E2E) — hedge `inconclusive` custa evidência legítima.
- **H6 Model Capacity: SUPPORTED — agora o fator dominante.** Com o
  mandato removido e `sufficient` como default explícito,
  `delia-json` escolhe `sufficient` 13/595 stage-local e 0/48 E2E.
  A recusa de suficiência é um prior do modelo, não só da instrução.

## Decisão

**`B_REJECTED`** contra os critérios de promoção: redução de FP
parcial mas não converte em continuação nativa (`sufficient` ≈ 0),
regra em FN de evidência legítima, outcome empresarial inalterado
(30 vs 31 PASS) e sem ganho de holdout.

Observação arquitetural separada: a cláusula removida em B é
**independentemente defeituosa** (embute premissa de owner não
verificável) — sua revisão segue justificada como higiene de
contrato, mas este experimento prova que, **sob `delia-json`, ela
não restaura o caminho nativo**.

## Limitações

- Stage-local reusa superfícies capturadas do doc 159 (válido: mesmos
  bytes que produção despachou; n=120 superfícies, não 120 cenários
  independentes).
- `corroboration_requested` sob B inclui falsos positivos
  (comparação não pedida) — ruído, não canal semântico útil.
- FN mede hedge para `inconclusive`, não perda de invocação estrangeira
  efetiva; a regressão é de decisão, moderada no outcome final.
- Denominador E2E é stage-condicional: instrução não afeta as ~53%
  de turns que morrem antes do assessment.

## Recomendação — próximo passo bounded

1. **Comparação de capacidade de modelo** na matriz stage-local
   congelada (mesmas 120 superfícies, mesma instrução A ou B, modelo
   alternativo candidato) — autorização separada. H6 é agora a
   fronteira dominante; sem isso, nenhum ajuste de instrução parece
   destravar `sufficient`.
2. Revisão de higiene da cláusula de exceção (remover ou condicionar a
   capability de vocabulário verificada) — task de contrato separada,
   valor independente do modelo.
3. Diagnóstico de `goal_evidence_relevance` vazio e dos dead-ends
   pre-assessment (admission/group/capability) — segue pendente.
4. `SECURITY_REVIEW_REQUIRED`: elegibilidade pre-invoke de PREPARE sob
   write-intent — remediação separada dos gates.

Artefatos: `native-assessment-instruction-b.txt`,
`assessment_ab_stagelocal_eval.py`, `instruction_ab_eval.py`,
`instruction_ab_aggregate.py`, `assessment-ab-stagelocal.json`,
`instruction-ab-runs.{json,jsonl}` — sanitizados, sem credenciais.

DEPLOY=BLOCKED · INDEPENDENT_REVIEW=PENDING
