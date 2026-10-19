# 16 — I02-R3A Independent Experiment Review (coordenação)

**DATA:** 2026-10-19  
**REVIEWED_SHA:** `353eec04ce901bde7f26b1a1cbeb0c83086f4e38`  
**SOURCES:** [14](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md), [15](./15-i02r3a-controlled-budget-and-critical-path-experiments.md), `orchestration.py`, `test_i02r3a_budget_and_critical_path_experiments.py` e Execution Ledger.  
**VERDICT:** `ACCEPT_WITH_RESIDUAL`, **somente** para caracterização experimental R3-A. `I02_ACCEPTED=NO`.

## 1. Escopo e prova

Revisão remota de documento 15, implementação de `experimental_arguments_budget_guard` (default `False`), helper `_budget_allows_arguments_propose` e testes sintéticos. A execução da suíte backend/23 testes foi **reportada pelo executor**, não independentemente repetida. Sem avaliação live de variantes nem deploy experimental. Logo, nenhuma melhoria real de K1, p95 ou task outcome pode ser declarada.

## 2. Resultado aceito com limites

- E0 reproduz synthetic success e timeout dos argumentos depois do discovery.
- E1: stage cap 10s antecipa falha de capability; **não** comprova melhoria de K1. **Não aprovar** como produção.
- E2: headroom opt-in evita chamada inviável e devolve limitação honesta; **não alcança** owner methodology READ no cenário de falha. Com stage timeout 30s, fórmula de headroom exige 36s e bloquearia todas essas propostas: **manter OFF**.
- E3: merge tipado goal+capability somente hipótese (potencial menos uma chamada); exige intenção de escrita independente, segurança, compatibilidade e holdouts.
- E4: native assessment já é pulado com grupo único; skip em multi-owner **não comprovado**.
- E5: schema vazio já evita modelo; envelope metodológico opaco permanece `MODEL_REQUIRED`, até evidência contratual contrária.
- Holdouts segurança/provider renomeado/K2/VISTA foram reportados como PASS sintético. K4 e live A/B = `TEST_NOT_RUN`.

## 3. Nota de integridade documental

Ao consultar `main` neste review, o Execution Ledger terminava em §6.254 e **não** continha o §6.255 alegado no report do executor. Registrar/restaurar a entrada R3-A sem tratar o relatório como prova de commit dessa seção. O README do roadmap também deixou de conter a antiga linha narrativa do documento 14, embora documento e direção permaneçam acessíveis; preservar ambos no índice.

## 4. Decisão coordenada e próximo gate

`EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND_CANDIDATE`; `SAFE_FUNCTIONAL_OPTIMIZATION=NOT_PROVEN`.

A sequência vigente continua `R3A_BUDGET_EVIDENCE → R3B_SEPARATE_ARCHITECTURE_GATE`. Priorizar **experimento isolado** de consolidação tipada entre capability e goal, sem alterar a validação determinística de capability, goal/write semantics, foreign/corroboration, discovery e AuthZ. Não alterar default, compositor, runtime ou contratos públicos por hipótese. Requer dependency map, RED/GREEN, providers sintéticos e renomeados, ambiguous WRITE, prompt injection, comparação/foreign, K1-K3, comparação em SHA/config/model e outcome útil. Comparar como segunda candidata elegibilidade estrita de native assessment; só experimentar deterministic args se contrato owner comprovar valores. Qualquer mudança estrutural nova retorna para decisão arquitetural, antes do patch funcional.

## 5. Estado

```text
I02_R3A_INDEPENDENT_REVIEW=ACCEPT_WITH_RESIDUAL_SCOPED
STAGE_CAP_10S_PRODUCTION_APPROVAL=NO
ARGUMENTS_HEADROOM_PRODUCTION_DEFAULT=OFF
K1_FUNCTIONAL_IMPROVEMENT=NOT_PROVEN
R3B_TYPED_MERGE=EXPERIMENT_CANDIDATE_ONLY
INDEPENDENT_TEST_REPLAY=TEST_NOT_RUN
LIVE_EXPERIMENTAL_EVAL=TEST_NOT_RUN
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=I02_R3B_TYPED_SELECTION_CONTRACT_AND_SAFETY_EXPERIMENT_GATE
```
