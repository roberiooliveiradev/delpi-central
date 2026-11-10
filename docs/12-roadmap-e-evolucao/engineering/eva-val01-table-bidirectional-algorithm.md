# EVA VAL-01 — Algoritmo bidirecional estrutura oficial ↔ tabela do desenho

**Data:** 2026-11-10 · **Estado:** `PLANNED / SPECIFICATION_ONLY` · **Tracker único:** Issue #131 · **Owners:** Doc 116 e Doc 119. Este arquivo é uma especificação dentro da trilha existente, não uma nova arquitetura, novo serviço ou nova fonte de autoridade. `RUNTIME_IMPLEMENTATION=TEST_NOT_RUN`; `G5/G6/G7=NOT_AUTHORIZED`.

## 1. Levantamento factual da API DELPI

A rota já existente `GET /products/{code}/structure/excel` (`get_product_structure_excel`) exige `API_DELPI_ACCESS`, retorna `format=json` (document_export com `downloadPath`) ou `format=xlsx` (stream).

Cadeia real no código: `product_routes.structure_excel_public` → `ExportProductStructureExcelUseCase` → `ProductStructureRepository.fetch_structure_rows(code, 999)` (SG1010 + SB1010 vigentes) → `BomTreeBuilder.build` → `ExcelStructureBuilder.build`.

Fontes: `api-delpi/app/interface/http/routes/product_routes.py`; `api-delpi/app/application/use_cases/product/export_product_structure_excel_use_case.py`; `api-delpi/app/application/services/bom_tree_builder.py`; `api-delpi/app/application/services/excel_structure_builder.py`; `api-delpi/app/infrastructure/persistence/totvs/product_repositories/product_structure_repository.py`; `api-delpi/tests/test_product_structure_excel_route.py`.

**PROVEN no código:** gera seis colunas `Código | Descrição | Item | QTD | Componente | Descrição`; letras A…Z, AA…; agrupa Código/Descrição do mesmo pai em células verticalmente mescladas; associa componentes a pais durante a geração. A saída exportada é *representação*, não necessariamente árvore integral de níveis.

**Limitações que devem ser preservadas na análise:**
- `ExcelStructureBuilder` expande intermediários com filhos; PI pode não ser linha explícita, e `bom_level` não é coluna de saída.
- `item_map[component_code]` reutiliza letra por **código**, não por ocorrência. `meta_map[component_code]` e `BomTreeBuilder.items[code]` também são indexados por código: risco em repetições sob pais/caminhos distintos; testar antes de assumir identidade preservada.
- Calcula quantidade exibida com `parent_factor` e uma regra condicional para `unit == "PC"` e divisibilidade por 1000; em outros casos usa fallback 1. Portanto quantidade Excel **não equivale automaticamente** a `G1_QUANT`, quantidade de desenho ou consumo real.
- A vigência da BOM não comprova equivalência com a revisão documental do PDF. Sem binding, `NOT_COMPARABLE`.
- O gerador de Excel é referência de **padrão de apresentação** e potencial gerador de fixtures de teste. Não deve ser importado como dependência runtime do `engineering-api` ou usado como source of truth. Extração de contratos cross-context exige decisão de arquitetura.

## 2. Objetivo e independência das direções

**Totus → Desenho:** para cada ocorrência oficial de pai→filho em nível conhecido, verificar que a relação aparece na tabela do desenho coberto e da revisão compatível. Ausência só é conflito candidato se a cobertura visual for suficiente.

**Desenho → Totus:** para cada ocorrência visual pai→filho realmente extraída, verificar se há ocorrência oficial equivalente com o mesmo caminho/nível e quantidade compatível.

A extração visual é **independente** do snapshot Totus. Nunca completar célula, pai, nível, descrição ou quantidade do PDF usando Totus, Excel, códigos de produto ou G1 DRAFT.

## 3. Visões conceituais (não introduzir contratos públicos sem inventário)

- **OfficialStructureSnapshot:** root; árvore de arestas pai/filho e níveis, tipos SB1.B1_TIPO, quantities/UM, vigência/provenance; consultada read-only via Domain API oficial com live AuthZ.
- **DrawingTableObservation:** SHA/revisão do PDF, página/região, bbox/linha/coluna/células, colspan/rowspan, OCR tokens + coordenadas/confiança e cobertura.
- **DrawingOccurrence:** parent visual ou UNKNOWN, child visual ou UNKNOWN, item local, qty/UM/descrição quando comprováveis, caminho visual e nível derivado somente do caminho visível, evidence refs por campo.
- **AlignmentCandidate:** resultado por aresta/caminho com estados candidatos coerentes com contrato existente (ex. MATCH_CANDIDATE, CONFLICT_CANDIDATE, UNKNOWN, NOT_COMPARABLE), proveniência dos dois lados, diferenças e limites de cobertura.
- **DELPI presentation profile:** papéis semânticos `parent_code`, `parent_description`, `item`, `quantity`, `component_code`, `component_description`; variante com coluna `Cabo`; posição/quantidade de colunas e paginação variáveis, rowspan de pais. **Perfil orienta interpretação, não fornece coordenadas fixas nem verdade prévia.**

Identidade de ocorrência visual: `(document_sha, page, region, table, parent_path_or_UNKNOWN, row_band, item_local, component_code)`. Não deduplicar por child_code nem tratar item alfabético como ID global.

## 4. Algoritmo planejado (pseudoespecificação de implementação)

```text
INPUT: pdf D, perfil DELPI P, config/versionamento C, snapshot oficial S opcional
GATE: acesso, SHA, revisão e autorização validados

VISUAL_OBSERVATION(D, P, C):                     // não recebe S
  raster = PDFium.render(D)
  tokens = PaddleOCR.read(raster)                  // text + bbox + confidence
  regions = existing_regioner.detect(raster, tokens)
  for region in regions:
    crop = existing_regioner.bound(region)        // excluir rodapé só com prova geométrica
    cells = SLANet.infer(crop)                     // linhas, colunas, rowspan, colspan
    cells = existing_adapter.associate(tokens, cells, crop)
    roles = Understanding.assign_column_roles(cells, headers, geometry, P)
    occurrences = Understanding.read_occurrences(cells, roles)
    preserve field evidence, confidence, ambiguity, and parent candidates
  graph = reconstruct only observed parent -> child edges
  derive drawing_level only when path to visually identified root is proven
  if parent/qty/description not evidenced: UNKNOWN + reason
  return ObservedDrawingGraph(graph, provenance, coverage)

CONTROLLED_ROUND_TRIP(known_fixture_tree):         // avaliação, não reconhecimento produtivo
  table = existing ExcelStructureBuilder.build(known_fixture_tree)
  record projection_loss: flattened PI, labels, parent factors, qty/UM transforms
  render test document; run VISUAL_OBSERVATION without fixture tree
  compare only invariants actually represented by the generated table
  vary scale, columns, spans, rows, descriptions, borders and page splits
  return metrics + loss origin

BIDIRECTIONAL_ALIGN(observed D, official S):       // somente G6 quando autorizado
  require live AuthZ, revisions/vigence compatible, coverage/qty semantics
  match occurrences by root + parent_path + child + level + multiplicity
  for official edge in S: find equivalent observed edge (S -> D)
  for observed edge in D: find equivalent official edge (D -> S)
  compare quantity/UM only when conversion/denominator is proven
  mark absent only with complete relevant drawing coverage
  emit candidates MATCH/CONFLICT/UNKNOWN/NOT_COMPARABLE + both provenances
  never mutate Totus, generate automatic NC, approve or publish from EVA
```

**Atenção:** A projeção Excel é potencialmente não inversível (achatamento, letras por código, transformação da quantidade). Portanto não exigir round-trip de árvore integral quando o próprio XLSX perde informação. Comparar a representação esperada e os invariantes efetivamente presentes; usar árvore oficial separada para futura verificação de níveis.

## 5. Como configurar capacidades existentes, sem engine paralelo

| Fronteira | Ajustes admissíveis | Limites |
|---|---|---|
| PDFium | DPI, orientação, transformações de coordenadas estáveis, SHA do documento | Não condicionar render ao gabarito Totus |
| PaddleOCR | bboxes/tokens/confiança; preservar `line_texts` e bandas Y | Não forçar texto para código esperado |
| Regioner da EVA | localizar regiões e crops com evidência geométrica; distinguir tabela/rodapé/desenho | Sem box GT em runtime, sem hardcode por PDF |
| SLANet | consumir células/spans/HTML e confiança pelo adapter atual | Sem segundo parser, VLM ou novo peso fora dos gates |
| Understanding | mapear papéis de colunas e pai→filho com evidência, abster-se se incompleto | Não deduzir MP/PI/PA por prefixo nem nível visual a partir do Totus |
| Comparador via porta existente | só G6; relação por caminho/multiplicidade e revisões | Sem banco alheio, source of truth EVA ou write |

**Risco atual de acoplamento:** `understanding.py` possui `_hierarchical_code_pair_crop` com gates geométricos relativos (70%/90%), herança por centro Y/rowspan e `_trim_sheet_index_margin`. Considerá-los **hipóteses generalizáveis a testar**, não evidência de generalização. Não criar uma exceção por página a cada falha; rastrear first-loss e testar famílias de layout.

## 6. Plano de testes de generalização e aceitação

**Famílias:** MP direto; vários MP sob um conjunto; PI com filhos; mesmo código sob pais/níveis diferentes; rowspan longo/curto e rótulo centralizado; descrições multiline; seis colunas e coluna Cabo adicional; colunas reordenadas; espaçamento/escala diferentes; quantidade 1/2 sem célula SLANet; índices de rodapé; folhas e tabelas parciais; tabelas divididas entre páginas; revisões inconsistentes.

**Métricas distintas:** IoU/recall crop e falsa inclusão de rodapé; F1 linhas/colunas/células/spans; associações OCR↔célula; precision/recall de papéis; parent→child e nível visual; quantidade/UM comparáveis; falso componente/pai; taxa de abstenção segura; no futuro, comparador bidirecional por ocorrência com cobertura e precisão de divergências.

**Conjuntos e status:** fixtures geradas são testes controlados e podem cobrir invariantes, mas não bastam para generalização; os 13 PDFs expostos do Doc 120 são regressão, **não holdout cego**. Sem GT/split/threshold homologado por owner e holdout independente, `G5_QUALITY_PASS` e generalização seguem `INCONCLUSIVE / OWNER_BLOCKED`. Nunca inventar números de precisão.

**Casos conhecidos no momento:** p10 A2=10080192/16 e A3=10090316/1 separados, descrições ainda null (relato G4); p12 50225702→AE/10010028/1, AH/10080897/qty UNKNOWN, AG/10110676/2 (relato G4); p13 falso `4 5` bloqueado; corpus 13 live `TEST_NOT_RUN`. Não declarar problemas solucionados fora dessas evidências.

## 7. Gates, owner e rastreabilidade

**G4 ATIVO:** completar associação de campos dentro da autorização da Issue #131; este documento **não altera código produtivo**.
**G5:** após decisão da Coordination; testes de generalização e qualidade requerem GT/thresholds/split/holdout legítimos.
**G6:** implementar comparação bidirecional somente após contrato Totus e autorização; AuthZ live e documentação/revisão comparáveis.
**G7:** deploy/approval sob gate próprio.
**Ownership:** Totus/Domain API é autoridade do cadastro e BOM; Keycloak identidade; Core RBAC; Portal host; EVA interpreta/gera candidatos; owner Engenharia aprova. MCP/adapters não criam autoridade. Mudança de owner ou boundary: `ARCHITECTURE_DECISION_REQUIRED`.

**Critérios desta especificação:** contrato factual do Excel documentado, pseudoalgoritmo de duas direções e round-trip controlado, framework-first, negativos e confidência, limites de identidade/quantidade/revisão e proibição de inventar resultado. `SPECIFICATION_ONLY`, `TESTS_NOT_RUN`, `VAL01_COMPLETED=false`.
