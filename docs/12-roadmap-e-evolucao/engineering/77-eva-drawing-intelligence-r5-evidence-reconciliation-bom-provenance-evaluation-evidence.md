# 77 — EVA — Drawing Intelligence R5: Evidence Reconciliation, BOM Provenance, ONDA14 Evaluation & Production Evidence

**Status:** IMPLEMENTED + DEPLOYED (CODE_READY / QUALITY_EVAL_PENDING). **Data:** 2026-10-31. **SHA:** `a8ae3df11c` (main). **Regressão:** `90264302`.

## 1. Reconciliação de evidências (R5-A/B)

`reconciliations[]` no relatório — por subject/field_role: evidências `textual`/`visual`/`official`, `reconciliation_status` (`corroborated|visual_and_official_only|official_only|explicit_conflict|insufficient_evidence|not_comparable|not_checked`), confidence, limitations, provenance.
Findings de ausência textual (ex.: código do produto não localizado pela extração) são **reclassificados** quando observação visual concorda com o cadastro: severidade `warning`→`info`, divergência→`text_coverage_limitation` — limitação de cobertura da extração, não erro do produto. Sem evidência visual, mantém-se como limitação — nunca "ausente do desenho".

## 2. BOM com proveniência pai/filho (R5-C/D)

`_flatten_bom` enriquece cada ocorrência: `_occurrence_id`, `_parent_code` (código do nó pai real — rework: antes era argumento nulo, causava `parent_links=0`), `_depth`, `_path`. `bom_stats`: `total_occurrences`, `unique_codes`, `by_type`, `by_depth`, `parent_links`, `direct_children`, `repeated_codes`, `max_depth`. Payload: `bom_occurrences[]` com hierarquia completa — MP repetida em ramos distintos = ocorrências distintas (10020033×2, 10080106×2 = legítimo). Sem conversão SG1.

## 3. Knowledge / ONDA14 / métricas

Knowledge **v1.3 mantida** — critérios de reconciliação/cobertura já cobertos por IDENT-ROLES-001, TEXT-ABSENCE-NOT-CONFLICT-001, BOM-MULTILEVEL-STATS-001 (sem inflação de regras; avaliação de necessidade aplicada). ONDA14: corpus legado permanece inventariado conceitualmente — fixtures neutras implementadas via árvore 90264302 (PA→2PI→4MP, repetidas). **Ground truth/thresholds: EVAL_PENDING / OWNER_VALIDATION_REQUIRED** — nenhuma métrica inventada.

## 4. Testes

Suite **539 passed / 0 failed** no SHA `a8ae3df11c`. Fixture r2 evoluída para árvore multinível real; r4 ampliado com parent_links/by_depth/repeated_codes. Rework: parent_code efetivo = código do nó pai.

## 5. Deploy / smoke

`origin/main=a8ae3df11c` → prod merge → `--build engineering-api` → `delpi-engineering-api Up (healthy)`. Rollback: SHA anterior + rebuild.

## 6. Matriz R5-01..37 (resumo)

PASS: 01–20 (reconciliação, identidade, ausência textual≠erro, parent links, profundidade, cobertura, DRAFT, knowledge, ENG-REV-001), 25–29, 32–37. TEST_NOT_RUN: 30–31 (MCP/ChatGPT sessões reais). PENDING/EVAL: 21–24 (ONDA14 corpus port + ground truth owner).

## 7. Residuais

1. ONDA14: port real de fixtures com labels aguarda autorização Engenharia.
2. ChatGPT/MCP real E2E: TEST_NOT_RUN (sem sessão no executor).
3. Cobertura visual por ocorrência individual (contexto região/parent): indício por código, não por ocorrência — registrado honestamente.
4. Métricas/thresholds: aguardam corpus aprovado.
5. Prod repo divergido — merge não destrutivo documentado.
