# 95 — Contrato de execução R8.2: detecção integral de layout governado

**State:** PLANNED. **Data:** 2026-11-01. **Owner:** Engineering API. **Relacionado:** docs 93 (plano/evidência), 94 (roadmap R8.2–R8.6). **Missão:** `EVA.DRAWING.INTELLIGENCE.R8.2.LAYOUT.SEGMENTATION.EXECUTION.E2E`.

## Objetivo e boundaries

Implementar a **primeira etapa** completa de reconhecimento de regiões (não reconhecimento completo de todos símbolos): detectar delimitadores e candidatos de carimbo, histórico, tabela de estrutura, notas e área gráfica em PDFs `9026` de layouts variados, independente da posição; separar ownership de tokens/células para não misturar carimbo/tabela/OV/cliente; revisar comparação BOM por campos tipados; produzir resultados `DRAFT` com evidência espacial e abstention. NÃO implementar aqui R8.3 multipágina completo, R8.4 balões/símbolos, R8.5 grafo ou R8.6 aprovação — registrar interfaces/requirements sem implementações prematuras. `drawing_understanding.v1` deve continuar compatível.

**Fatos baselines:** no PDF `90264302.pdf`, a R8.1 identificou 4 agrupamentos de linhas, mas misturou `COD/DES/REV/CLIENTE` e histórico. `not_in_bom` classificou erroneamente `003086` (OV) e `18702881` (cliente); `643±2`, `663±2`, `REV: 00` são bons casos positivos. Outros dois desenhos P0: `90263554` 18 páginas, `90264135` 13 páginas (texto nativo nas 18/13; OCR multipágina **não** comprovado).

## Plano operacional e gates

1. **Authority/reanchor.** Ler `AGENTS.md`, always-on, docs 83–95, ENG-REV-001, owners/contratos. Registrar `BASE_HEAD`, `origin/main`, status e alterações paralelas; usar clone/worktree isolado, sem stash/reset/force-push de terceiros.
2. **Inventário e Abstraction Gate.** Inspecionar `engineering-api/engineering_app/application/drawing/understanding.py`, `visual_benchmark.py`, ports/adapters OCR/PDFium/OpenCV, `semantic_bridge.py`, `semantic_registry.py`, tests R8. Evitar novo LLM/modelo/serviço/bounded context sem evidência.
3. **Contrato antes do código.** Definir owner/consumer/request/response/errors/AuthN/Z/rate/limites/observabilidade/compatibilidade e pós-condição. Extensões candidatas: `region_id,region_kind,page,polygon,bbox_pdf_points,bbox_px,source_token_ids,graphic_evidence_ids,region_role,field_role,confidence_kind,alternatives,coverage_status`. Fazer version bump só se breaking; antiga resposta não pode quebrar.
4. **Adapters de evidência gráfica.** Inventariar uso vetorial de PDF (quando permitido por porta existente), bordas/linhas/contornos e Hough/morfologia OpenCV. Guardar orientação/DPI/transformação e provenance. Aplicar CPU/RAM/timeout/semaphore existentes — não sobrecarregar serviço para OCR.
5. **Segmentação de layout.** Usar *evidência combinada* visual + OCR semântica + estrutura. Gerar regiões candidatas de tabela, carimbo, histórico, notas, área gráfica. Separar regiões adjacentes/encaixadas, regiões com rótulos duplicados; permitir UNKNOWN e ambiguidades. Não assumir canto/percentual fixo.
6. **Ownership espacial.** Política por token: pertencimento a exatamente uma região primária, com referências secundárias explicitamente ambíguas; nenhuma cell da BOM pode consumir token de carimbo, histórico, cliente ou OV. Coordenadas/bbox + evidências de decisão expostas.
7. **Reconstrução tabular.** Só dentro da região delimitada; cabeçalho→colunas (`ITEM,QTD,COMPONENTE,DESCRIÇÃO`), linhas físicas e células; se não tiver cabeçalho/limites confiáveis marcar `TABLE_CANDIDATE_UNSTRUCTURED`, não `COMPARED_PARTIAL`.
8. **Tipagem técnica.** Identificar sem inventar `component_code,item,quantity,description,customer_reference,order_reference,revision`; contexto rótulo + região, não regex isolada. Reconciliar linhas para códigos `50226113,50226114,10020033,10080106` apenas se evidenciarem coluna componente.
9. **Revisão/cotas.** Preservar `REV:00`, revisão TOTVS independente; preservar `643±2`/`663±2` como candidatos de região; excluir números de item, grid e história. NÃO alegar relação cota↔geometria verificada.
10. **BOM sem falso alerta.** Comparação exige tabela tipada, escopo/nível de BOM compatível e cobertura suficiente. `Counter(tokens)` NÃO = quantidade nem estrutura multinível. Não colocar cliente/OV em `not_in_bom`. Ausência de tabela/escopo/completude: `NOT_COMPARABLE`, arrays de divergência vazios, limitations claras. Em `COMPARED_PARTIAL` sinalizar só diferenças dentro do escopo comprovado como **candidatas**.
11. **Multipágina no escopo R8.2.** Não implementar workflow R8.3 inteiro; testar layout em **folhas selecionadas** autorizadas dos PDFs 18p e 13p. Registrar `document_page_count,pages_sampled,pages_understood,OCR_pages_processed,sampled`. Não simular cobertura integral e não aumentar limites do worker arbitrariamente.
12. **Testes sintéticos diversos.** Carimbo superior/inferior/lateral, tabela com/sem bordas, tabela adjacente ao carimbo, 2 tabelas, folha sem tabela, histórico revisão, código cliente/OV, rotated, raster, fragmentação OCR, 2 páginas, amostra limitada, documento corrompido, coordenadas inválidas. Provar exclusão `003086/18702881` da BOM, tipagem `50226113/50226114/10020033/10080106`, e abstain honesto.
13. **Matriz real autorizada.** `90264302` (baseline); `90263554` (18p); `90264135` (13p); controles `90264161` e `90264094` (1p). Comparar antes/depois por documento/folha/região com SHA e resultado. Preferência para `9026` PA. `10210267-2` apenas adversarial secundário.
14. **Qualidade.** Medir falsos positivos explícitos, region ownership violations, tabelas verdadeiramente delimitadas, células tipadas, carimbos/revisões, latência, RAM, page coverage. Precisão/recall só com GT aprovado pela Engenharia; caso contrário `EVAL_PENDING`.
15. **Segurança.** Core autorização live, identidade delegada, no direct fileserver runtime, no SaaS egress/no JWT to worker, no secret logs, read-only, flag fail-closed, 6 tools MCP zero legadas. Tests registry↔dispatch e drawing_analysis.v3.
16. **Entrega e deploy.** SHA completo com testes no mesmo SHA, residual search, commit/push preservando concorrência. Implantar somente via procedimento SSH Operator canônico autorizado; comparar loaded SHA, flags, image digest, resources/health. Controlar rollback SHA/flag. E2E autenticado `analyze(product.drawing_understanding)` quando sessão disponível; se não, `TEST_NOT_RUN` (assistente pode testar posteriormente pela EVA).
17. **Documentação/evidência.** Registrar implementação num novo documento de evidências, sem sobrescrever docs 93–95, com code diff, why, hashes, testes e resultados por arquivo/folha.

## Critérios de aceite mensuráveis

**AC01:** layout not tied to absolute location, test upper/bottom/side; **AC02:** table/other regions disjoint or explicit ambiguous ownership; **AC03:** `90264302` excludes `18702881`/`003086` from component cells/`not_in_bom`; **AC04:** table cells have row/column/header evidence, no merged carimbo history; **AC05:** `REV:00` preserved; **AC06:** `643±2`,`663±2` preserved without false geometrical association; **AC07:** BOM `NOT_COMPARABLE` when missing proper scope, no misleading mismatch; **AC08:** `90263554` and `90264135` have selected-page evidenced runs and explicit coverage; **AC09:** all four `9026` samples authorized and reported as executed/blocked with reason (90264302,90263554,90264135, one of 90264161/90264094); **AC10:** tests include raster/rotated/table-less and false positive cases; **AC11:** no new MCP tool and `drawing_analysis.v3` unchanged; **AC12:** AuthZ/no egress/read-only/pass; **AC13:** tests at tested SHA; **AC14:** production deployed code/runtime SHA when authorized; **AC15:** live authenticated MCP E2E `PASS` or honest `TEST_NOT_RUN`; **AC16:** GT/EVAL_PENDING and rollback documented.

**Success is semantic**: `success:true` alone does not prove AC02–AC09. Executing one page out of 18 does not prove whole drawing coverage. No promises of universal `any PDF` correctness. Evidence labels: `PROVEN | TO_INVENTORY | PLANNED | TARGET`; execution `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | OWNER_BLOCKED | STALE_EVIDENCE`.

## Expected report

```text
TASK: EVA.DRAWING.INTELLIGENCE.R8.2.LAYOUT.SEGMENTATION.EXECUTION.E2E
BASE_HEAD: / ORIGIN_MAIN_BEFORE: / FINAL_HEAD: / DEPLOYED_SHA:
AUTHORITIES_READ: / ABSTRACTION_GATE: / CONTRACTS:
FILES_CHANGED: / REGION_ADAPTER: / REGION_ALGORITHM: / TOKEN_OWNERSHIP:
TABLE_BOUNDS: / HEADER_MAPPING: / CELL_TYPING: / REVISION: / DIMENSIONS:
BOM_GATES: / SECURITY: / SIX_TOOL_COUNT:
90264302: PDF_SHA, PAGES_COVERED, CARIMBO, TABLE, FALSE_POSITIVES, BOM
90263554: PDF_SHA, PAGES_TOTAL, PAGES_SAMPLED, PAGES_PROCESSED, LIMITATIONS
90264135: PDF_SHA, PAGES_TOTAL, PAGES_SAMPLED, PAGES_PROCESSED, LIMITATIONS
90264161_OR_90264094: PAGE, REGIONS, LIMITATIONS
TESTS: / TESTED_SHA: / COMMITS: / PUSH: / PROD_SHA: / MCP_E2E:
QUALITY_GATE: / GROUND_TRUTH: / ROLLBACK: / DOCUMENT_PATH:
EXECUTION_DRIFT: / OWNER_BLOCKERS: / ARCHITECTURE_DECISION_REQUIRED:
NEXT_BOUNDED_STEP:
```

**Postcondition:** EVA fornece mapas de regiões, células e associações **candidatas e rastreáveis** com mais precisão estrutural; o owner de Engenharia aprova qualquer conclusão técnica. R8.3–R8.6 permanecem PLANNED (doc 94).
