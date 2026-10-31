# 76 — EVA — Drawing Intelligence R4: Typed Identifiers, Revision Evidence, BOM Coverage & Quality Evaluation

**Status:** IMPLEMENTED + DEPLOYED. **Data:** 2026-10-31. **SHA:** `5ae95c01af` (main). **Regressão:** `90264302`.

## 1. Identificadores tipados (R4-A)

`DrawingVisualObservation.identifiers[]` — aditivo, `{role,value}` fechado: `product_code|customer_reference|drawing_code|component_code|unknown_identifier`. Texto legado classificado por labels documentados: `COD`→customer_reference, `DES`→drawing_code, `PRODUTO/PRODUCT`→product_code, `REF`→customer_reference; dígitos sem label → `unknown_identifier` (nunca comparados ao produto).
Comparação oficial só dentro do mesmo role: `product_code`×`official_code`; "Produto 90264302, COD 18702881, DES 10013396831" → **agreement, zero conflito** (falso positivo eliminado — valor só entra se ancorado em dígito; descritores como "cliente"/"desenho" não poluem).

## 2. Revisão visual com proveniência (R4-B + ENG-REV-001 preservada)

`identification.revision_domains`: `customer_totvs_revision` (001), `engineering_drawing_revision` (texto extraído — pode ser null), `engineering_drawing_revision_visual` (`{values, provenance=chatgpt_visual_observation, promoted_to_official=false}` — REV 00 observada aparece sem virar fato), `drawing_library_revision`, `totvs_vs_drawing_comparable=false`, `rule=ENG-REV-001`. Nenhuma comparação cross-domain gera finding.

## 3. BOM multinível (R4-C)

`executive_summary.bom_stats`: `total_occurrences`, `unique_codes`, `by_type{}`, `parent_links` — ocorrências ≠ códigos únicos; sem conversão SG1 inventada.

## 4. Knowledge v1.3

+3 regras governadas: `IDENT-ROLES-001`, `TEXT-ABSENCE-NOT-CONFLICT-001`, `BOM-MULTILEVEL-STATS-001` (10 regras; ENG-REV-001 + superseded DRAW-REV-MATCH preservados).

## 5. Testes

6 novos (`test_drawing_analysis_r4.py`): classificação por label, 3 identificadores sem conflito, código errado → no_evidence/conflict, identifiers tipados no payload, revisão visual não promovida, bom_stats. Rework: regex de label — valor ancorado em dígito (`re.I` capturava "cliente"/"desenho"). **Suite: 539 passed / 0 failed.**

## 6. Deploy e smoke

Push → `origin/main=5ae95c01af`; prod merge + `--build engineering-api` → container `health: starting`/healthy. Rollback: SHA anterior + rebuild.

## 7. Matriz R4-01..35 (resumo honesto)

PASS: 01–17, 18, 23–27, 30–35. TEST_NOT_RUN: 28–29 (MCP/ChatGPT E2E sem sessão). PENDING: 19–22 (ONDA14 corpus inventariado como conceito; ground-truth owner ainda não aprovado → EVAL_PENDING, nenhuma métrica inventada).

## 8. Residuais

1. ONDA14 port real de fixtures → owner Engenharia (EVAL_PENDING).
2. E2E consumidor não exercitado — TEST_NOT_RUN.
3. Cobertura por nível de profundidade (by_level) — parcial; by_type implementado.
4. Extraction de tabela com coordenadas — limitação pypdf (PyMuPDF bloqueado por AGPL).
5. Prod repo divergido — merge documentado.
