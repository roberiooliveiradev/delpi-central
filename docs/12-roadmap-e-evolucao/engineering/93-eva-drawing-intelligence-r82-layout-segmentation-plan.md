# 93 — EVA Drawing Intelligence R8.2: plano de segmentação de layout, tabelas e associação técnica

**Status:** PLANNED — plano técnico, não implementação nem aprovação de Engenharia.  
**Data:** 2026-11-01.  
**Owners:** Engineering API (interpretação), API DELPI (desenho oficial), Core (AuthZ), Engenharia DELPI (validação técnica).  
**Princípio:** inteligência ampla + autoridade estreita, explícita e governada.  
**Superfície:** EVA no Portal Engenharia; seis tools MCP, usando `analyze(product.drawing_understanding)` — nenhuma tool nova.

## 1. Evidência real reunida pela EVA (sessão autenticada)

Todas as consultas a seguir foram efetuadas por `read(product.drawing)` e `analyze(product.drawing_understanding)`, com fonte `api_delpi_product_drawing_pdf` e identidade delegada. São resultados candidatos `DRAFT`; não são ground truth nem comprovação de acurácia.

| Código / arquivo | Bytes | SHA-256 do PDF | Resposta real da EVA | Gap observado | Caso R8.2 |
|---|---:|---|---|---|---|
| `90264302` / `90264302.pdf` | 103498 | `f33447b271a3518643559582d79cf54527b85778537cfb1e20a5ccf5d989f0ef` | Tabela candidata, 4 linhas agregadas; `REV: 00`; `643±2`, `663±2` | Tabela inclui campos de carimbo/histórico; `not_in_bom` incluiu `003086` (OV) e `18702881` (cliente) | Delimitar tabela e tipar colunas antes de reconciliar |
| `10210267-2` / `10210267-2.pdf` | 51944 | `43b2cd6ffe74c3cbcae35c41dad2c1078e5e04c022de519f5961847f0d1993be` | 68 tokens; sem carimbo ou tabela candidatos; dimensões candidatas `12.0`, `19.50`, `3,5`, `1020`, `1045` | Dependência de rótulos e ambiguidades de número/cota em imagem raster | Sem bordas/vetores, abstain honesto e detecção geométrica |
| `90263554` / `90263554.pdf` | 6202644 | `89f9b4d574c8c1dbae2d87315e47743b4a75d36279581b7e0d2ef24b149c4f4d` | 200 tokens processados na resposta; carimbo candidato, revisão sem par; tabela candidata 1 linha | Cobertura aparentemente amostrada; referência histórica: multipágina 18p, confirmar via metadado do PDF em run controlado | Paginação e cobertura por página, nenhum resultado global sem completude |
| `90262471` / `90262471.pdf` | 431628 | `a261c2a000c6b2c499fc2f7163ece677123c4c292de5bb88f09c024ebb5f0e0a` | 200 tokens; tabela candidata 2 linhas sem cabeçalhos; várias cotas/números candidatos | Possível falso positivo de tabela; confiança semântica insuficiente | Exigir evidência de estrutura tabular e distinguir notas/inspeção |

**Limites da evidência:** o acesso foi real e autorizado, mas não houve inspeção visual integral das páginas nesta etapa; tipos de desenho são referências operacionais, a classificar formalmente. 200 tokens é o limite observado na resposta de dois casos, não prova de que o PDF contenha somente 200 tokens. SHA histórico pode mudar legitimamente em nova revisão, exigindo nova proveniência.

## 1.1 Atualização de seleção: priorizar produto acabado 9026 e PDFs multipágina (2026-11-01)

**Diretriz do owner:** o corpus primário de R8.2 deve privilegiar códigos iniciados em `9026` (desenhos de produtos acabados). Códigos `10...` são casos complementares — não são representativos por padrão dos desenhos de produto acabado. A prioridade de arquitetura é **múltiplas páginas + diversidade de layout**, e não tamanho de arquivo isolado.

**Descoberta autenticada na EVA:** `read(product.search, filters.code="9026")` retornou 4.306 registros no catálogo; isso **não equivale a 4.306 desenhos existentes ou autorizados**. `read(product.drawing)` verificou a existência dos PDFs abaixo; `analyze(product.drawing_benchmark, benchmark_profile="approved_local_extractors")` verificou a contagem real de páginas pelo pypdf, pdfplumber e PDFium, todos com `status=ok`.

| Prioridade | Produto | PDF | Páginas comprovadas | Bytes | Tipo/descrição conhecida | Papel no corpus |
|---|---|---|---:|---:|---|---|
| P0 | `90263554` | `90263554.pdf` | **18** | 6202644 | Desenho de código 9026, multipágina | Caso primário de cobertura multi-page e detecção independente por página |
| P0 | `90264135` | `90264135.pdf` | **13** | 4434155 | Catálogo: CHICOTE - P66 | Segundo caso primário multipágina, testar layout heterogêneo e revisões por folha |
| P0 | `90264302` | `90264302.pdf` | **1** (benchmark R7) | 103498 | CHICOTE DE LIGACAO | Regressão de região, tabela, carimbo, BOM/cotas |
| P1 | `90264161` | `90264161.pdf` | **1** | 202428 | CABO DE LIGACAO 15.5M-3X2.5 | Controle de uma página, layout de PA |
| P1 | `90264094` | `90264094.pdf` | **1** | 157700 | CABO DE LIGAÇÃO 15.5M-4X10 | Segundo controle de uma página |
| P1 (metadado apenas) | `90263792` | `90263792.pdf` | A verificar | 78347 | CABO 3X1,5MM²...25,3M | Candidato adicional se ampliar corpus |
| P1 (metadado apenas) | `90263793` | `90263793.pdf` | A verificar | 76890 | CABO 3X1,5MM²...20.4M | Candidato adicional |
| P1 (metadado apenas) | `90263247` | `90263247.pdf` | A verificar | 88629 | CABO 4X10MM2 - 500V | Candidato adicional |
| P1 (metadado apenas) | `90263397` | `90263397.pdf` | A verificar | 69398 | CABO 4X2.5MM²X30M | Candidato adicional |
| P1 (metadado apenas) | `90264282` | `90264282.pdf` | A verificar | 138129 | CABOS LIGACAO...CHICOTE | Candidato adicional |
| P2 | `10210267-2` | `10210267-2.pdf` | 1 (R7 benchmark) | 51944 | Exemplo escaneado não-9026 | **Controle complementar de OCR**, não integrar amostra central de PA |
| P2 | `90262471` | `90262471.pdf` | A verificar | 431628 | Inspeção/esparso (histórico) | Caso adversarial, sem presumir produto acabado |

**Atenção à análise multipágina:** o benchmark textual comprovou processamento de 18/18 e 13/13 páginas. Isso não comprova que `drawing_understanding.v1` analisou todas elas: nas consultas anteriores essa ação apresentou 200 tokens no relatório, com cobertura por folha não transparente. R8.2 precisa separar `document_page_count` de `pages_rendered`, `pages_ocr_processed`, `pages_understood`, `tokens_total`, `tokens_used` e `sampled`.

**Aceite adicional obrigatório:**
1. Primeira fase com `90263554` e `90264135` como **multipágina 9026 P0**; confirmar hash atual na nova execução, não assumir imutabilidade de revisões.
2. Provar resultado **por folha** (18 e 13), ou registrar `PARTIAL/NOT_RUN` por folha conforme limites de OCR (5 páginas/300 DPI) e recursos do host. Não remover limites para declarar sucesso.
3. Usar extração textual nas páginas todas quando autorizada e OCR **seletivo** com critério de cobertura, custo/segurança e autorização — sem carregar automaticamente 31 páginas pesadas de OCR no runtime da API.
4. Inferir layout e regiões em cada página separadamente; não reutilizar automaticamente template da página 1, nem agregar cotas/revisões/tabelas de folhas distintas como se fossem uma única região.
5. Desenhos que começam em `10` só entram como controles raster/escaneados ou exceções tecnicamente justificadas; **nunca dominar o corpus primário**.
6. Para descobrir outros multi-page `9026`, usar a listagem oficial governada `GET /products/drawings` (contrato e acesso sob API DELPI) quando disponível ao consumer; paginar e pré-filtrar por código, sem rastrear filesystem diretamente. Confirmar `page_count` lendo o PDF oficial pelo gateway autorizado, **não inferir pelo tamanho em bytes**.
7. Preparar ground truth para Engenharia por página e região, incluindo folhas sem tabela e folhas com carimbos/revisões diferentes.

## 2. Diagnóstico do algoritmo vigente (`engineering-api/engineering_app/application/drawing/understanding.py`)

Implementação R8.1 é **determinística**, sem modelo de layout: token OCR + bounding box; `_detect_title_block` agrupa >=2 rótulos; `_detect_component_table` exige >=2 códigos de 6–11 dígitos alinhados por X; linhas aproximadas por Y; `_structure_table` forma colunas por cluster X; revisão por rótulo à direita/abaixo; cotas por regex + região. Permanecem margens proporcionais à página e fallback posicional.

Causas verificadas: (i) agrupamento por faixa Y pode misturar tabela e carimbo; (ii) identificação de código numérico não é tipagem de coluna; (iii) OCR sem relações de borda não segmenta tabela adequadamente; (iv) amostra limitada não representa cobertura multipágina; (v) comparação BOM pode emitir falsos positivos `not_in_bom`/contagens não equivalentes.

## 3. Arquitetura-alvo R8.2 (proposta, sujeita ao Abstraction Gate)

```text
PDF oficial (API DELPI + identidade delegada + SHA)
    |--> PDFium: render controlado + transformação px/pt
    |--> texto PDF / vetores, quando disponibilizados por contrato vigente
    |--> OCR local isolado: tokens, polígonos, confidence
                 |
         Region candidate generation
            A. estrutura gráfica: linhas, contornos, bordas, células
            B. estrutura semântica: rótulos, cabeçalhos e padrões
            C. evidência espacial: interseção, alinhamento, projeções
                 |
         Region fusion / non-overlapping ownership
                 |
       [title_block] [revision_table] [component_table] [notes] [drawing_area] [unknown]
                 |
         reconstrução APENAS dentro da região, com evidência de cabeçalho
                 |
         tipos de célula (product, PI, MP, quantity, item, customer ref, OV, rev)
                 |
         comparação BOM condicionada a escopo/completude/semântica
                 |
         drawing_understanding (DRAFT/CANDIDATE) + provenance
```

Reutilizar ports existentes `PdfRenderingPort`, `OcrExtractionPort`, `ImagePreprocessingPort`. Bibliotecas OpenCV/PDFium somente em infrastructure/adapters; Application não importa `cv2`, `paddleocr`, `pypdfium2`. Não criar novo serviço ou authority; integração por contratos oficiais. Não gerar/descarregar desenho fora de autorização.

## 4. Plano de implementação (gates ordenados)

### R82-G01 — Reanchor e baseline
Ler `AGENTS.md`, authorities, docs 83–93, ENG-REV-001 e contratos. Verificar HEAD, origin/main, worktree/status; inventariar módulos e equivalentes. Trabalhar em clone/worktree isolado diante de agentes concorrentes. Nunca stash de terceiros, reset destrutivo ou force-push. Congelar respostas baseline desses quatro desenhos e métricas por SHA.

### R82-G02 — Contrato de regiões e proveniência
Definir adições compatíveis a `drawing_understanding.v1` (ou versionar só se breaking): `region_id`, `page`, `bbox_px`, `bbox_pdf_points`, `evidence_token_ids`, `geometry_evidence_ids`, `region_type`, `source_provider`, `detection_method`, `ambiguities`, `coverage_status`, `validation=DRAFT`. Distinguir `UNKNOWN` / `AMBIGUOUS` / `NOT_COMPARABLE`. Confidence OCR não é confidence técnico. Owners, consumers, request/response, erros, limites, AuthN/Z, compatibilidade, observabilidade e postconditions antes do código.

### R82-G03 — Primitivas gráficas por adapter
Inventariar se PDFium ou outro adapter já expõe linhas/retângulos/vetores. Preferir dados vetoriais quando disponíveis. Para raster, OpenCV com binarização adaptativa, morfologia orientada e Hough/contornos apenas conforme experimentos. Normalizar coordenadas, rotação, DPI, escalas e limites de memória/CPU. Falsos contornos nunca viram tabela por si. Evitar processamento extra fora do executor OCR isolado sem gate de capacidade.

### R82-G04 — Segmentação independente da posição
Gerar regiões candidatas por interseção de bordas/retângulos, distribuição de OCR, vizinhança e cabeçalhos; admitir carimbo lateral/superior/inferior, tabela com/sem borda, páginas rotacionadas. Criar ownership por token e política para regiões sobrepostas (associação ambígua ou exclusão controlada). Não usar % da página como evidência decisiva. Preservar `unknown` quando não há indício suficiente.

### R82-G05 — Tabela verdadeiramente delimitada
Reconstruir linhas/colunas **somente dentro da região** `component_table`. Exigir evidências combinadas: cabeçalhos, alinhamento repetido, código + descrição/quantidade, bordas quando presentes; permitir `TABLE_CANDIDATE_UNSTRUCTURED` se incompleto. Em `90264302`, impedir que `COD`, `DES`, `REV`, `CLIENTE`, `003086`, `18702881` entrem como células de componentes. Reportar linhas físicas e relações corretas; não forçar contagem específica antes do ground truth.

### R82-G06 — Reconhecimento de tipo/escopo de célula
Tipar colunas por associação ao cabeçalho e contexto: `item`, `quantity`, `component_code`, `description`, `reference`; não classificar todo código numérico como componente. Preservar códigos de PI/MP `50226113`, `50226114`, `10020033`, `10080106` como candidatos com linha/coluna/provenance, sujeitos a conferência. Revisões `00`, cliente `18702881` e OV `003086` são campos separados.

### R82-G07 — Histórico de revisão e carimbo
Separar `title_block` de `revision_history`; lidar com `REV: 00` no carimbo e `REV/DATA/LMP/OV` em tabela própria. Revisão TOTVS de cadastro e revisão gráfica permanecem independentes segundo ENG-REV-001. Não transformar `LIBERADO` visual em aprovação efetiva.

### R82-G08 — Cotas e geometria (escopo controlado)
Preservar `643±2`, `663±2`; filtrar grid, item, revisão e referências; experimentar linhas de cota, extensão e setas por estrutura gráfica. Emitir `DIMENSION_GEOMETRY_ASSOCIATION_CANDIDATE` somente com evidência explícita de vínculo; nunca `VERIFIED` automaticamente. Outras unidades/tolerâncias somente quando escritas.

### R82-G09 — Comparação BOM fail-closed
**Pré-requisitos:** tabela delimitada, célula tipada `component_code`, escopo de BOM conhecido, cobertura por página e multiplicidade comparável. `Counter` de tokens não equivale a quantidade BOM nem a número de ocorrências por si. Usar quantidade de célula e papel da linha, distinguindo PI, MP e produto pai. Se insuficiente, `NOT_COMPARABLE` ou `COMPARED_PARTIAL` sem alegação de ausência/divergência. `not_in_bom` e `missing_in_drawing_table` vazios quando não comparável. Qualquer mismatch permanece candidato para Engenharia.

### R82-G10 — Multipágina e amostragem
Expor `page_count`, `pages_requested`, `pages_processed`, `tokens_total`, `tokens_used`, `sampled` e `coverage_status`. A atual resposta de 200 tokens exige inventário do limite e prova de completude. Nunca comparar BOM global de 18 páginas com primeira página/amostra parcial. Respeitar limites de rendering, OCR e execução isolada; falha parcial mantém status honesto.

### R82-G11 — Corpus + ground truth owner
Corpus obrigatório: `90264302`, `10210267-2`, `90263554`, `90262471` (verificar autorização/documento atual). Expandir com desenhos sem bordas, carimbo inferior, lateral, rotacionado, tabelas múltiplas e páginas escaneadas, via busca governada. Preparar pacote de regiões/células para revisão de Engenharia; saída EVA jamais aprova seu próprio ground truth. Não incluir PDF confidencial no Git. Sem GT: `EVAL_PENDING`.

### R82-G12 — Testes de regressão e matriz semântica
Casos sintéticos: carimbos em 4 posições; tabela superior/lateral/inferior; tabela sem borda; carimbo adjacente; histórico REV/OV; códigos de cliente confundíveis; tabela parcial; linhas repetidas; cabeçalho ausente; 2 tabelas; PDFs escaneados; páginas rotacionadas; 200-token sample; documento sem tabela; BOM com multiplicidade e quantidades independentes; false positive `003086` e `18702881`. Testar não-divergência fail-closed, coordenadas, hash, AuthZ, feature flags, limites de CPU/RAM, ausência de writes/SaaS e seis tools MCP. Testes no SHA final, nunca em SHA anterior.

### R82-G13 — Experimento, deploy e MCP E2E
Comparar antes/depois nos quatro documentos oficiais: region boundaries, table cell ownership, field association, false positives, dimension candidates, runtime/memory, cobertura por página. Registrar resultados por desenho sem inventar acurácia. Integrar via mecanismo governado; deploy SSH Operator após testes e gates; confirmar SHA no container e dispatcher; fazer chamada MCP autenticada de `analyze(product.drawing_understanding)` + regressões `drawing_analysis`/`drawing_benchmark`. Flag/rollback; aprovação técnica continua owner. Falta de sessão => `TEST_NOT_RUN`, não PASS.

## 5. Matriz de sucesso por código

| Código | Resultado esperado (não pré-aprovado) | Rejeitar |
|---|---|---|
| `90264302` | regiões não misturadas; `REV: 00`; tabela apenas com componentes candidatos; `643±2` e `663±2`; BOM conforme escopo | cliente/OV classificados como MP/PI; falso mismatch |
| `10210267-2` | detecção raster quando evidência suficiente; números/cotas com contexto ou abstain; provenance | tratar todo número OCR como dimensão |
| `90263554` | processamento e relatório por página; `sampled` e completude explícitos; regiões isoladas | conclusão global a partir de 200 tokens ou 1 página |
| `90262471` | identificar se existe tabela de fato; não considerar cluster de códigos suficiente por si só | `COMPARED_PARTIAL` por falso positivo de tabela |

## 6. Gates de aceite

`G01` HEAD e authorities PASS; `G02` contratos/ownership PASS; `G03` evidência gráfica testada; `G04` regiões independentes; `G05` células sem contaminação; `G06` tipos e cabeçalhos; `G07` carimbo/revisão independentes; `G08` dimensão sem promoção indevida; `G09` BOM fail-closed; `G10` cobertura multipágina; `G11` corpus autorizado e GT pendente explícito; `G12` testes no SHA; `G13` deploy e MCP E2E autenticado; `G14` seis tools/zero legadas; `G15` ausência de mutação; `G16` rollback e documentação.

Estados: `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | OWNER_BLOCKED | FEATURE_GATED | STALE_EVIDENCE`.

**BLOQUEADORES DE AUTHORITY:** nova permission Core; acesso ampliado à biblioteca; promoção de modelo ou infraestrutura externa; aprovação de ground truth — `ARCHITECTURE_DECISION_REQUIRED`, retornar à Coordination.

## 7. Entregáveis de código esperados (não implementados por este documento)

- Extensão mínima ao contrato `drawing_understanding`, se necessária.
- Adapter de evidência gráfica em `engineering-api/engineering_app/infrastructure/extraction/` **após inventário**.
- Region boundary/ownership e table reconstruction na camada adequada de Application sem dependência de OpenCV.
- Células com tipagem contextual e comparação BOM segura.
- Paginação/cobertura explícita.
- Testes por layout e regressões no diretório `engineering-api/tests/`.
- Documento de evidências posterior com hashes, SHA, testes, métricas, failures e decisões.

**Exemplo de pseudocódigo (não pronto para produção):**

```python
visual_regions = geometry_adapter.detect_regions(rendered_page)  # Infrastructure
candidate_regions = region_service.fuse(visual_regions, ocr_tokens)  # Application
for region in candidate_regions:
    if region.type == "component_table" and region.has_structural_evidence:
        cells = table_service.reconstruct(region.tokens, region.geometry)
        eligible = table_service.only_typed_component_cells(cells)
        compare_bom_if_scope_comparable(eligible, official_bom)
    else:
        report_not_comparable(region)
```

Não criar port/infrastructure desnecessários; usar os existentes. Não incorporar OCR em `drawing_analysis.v3` ou promover resultados a fatos técnicos.

## 8. Report de execução exigido na futura implementação

```text
TASK: EVA.DRAWING.INTELLIGENCE.R8.2.LAYOUT.SEGMENTATION.BOM.SEMANTICS
BASE_HEAD:
FINAL_HEAD:
DEPLOYED_SHA:
FILES_CHANGED:
CONTRACT_CHANGES:
REGION_ALGORITHM:
GRAPHIC_PRIMITIVES:
TABLE_BOUNDARIES:
CELL_TYPES:
BOM_SCOPE_POLICY:
MULTIPAGE_COVERAGE:
90264302_BEFORE_AFTER:
10210267-2_BEFORE_AFTER:
90263554_BEFORE_AFTER:
90262471_BEFORE_AFTER:
GROUND_TRUTH:
TESTS_AND_TESTED_SHA:
AUTHZ:
MCP_TOOLS:
RUNTIME_SHA:
E2E_AUTHENTICATED:
ROLLBACK:
QUALITY_GATE:
ARCHITECTURE_DECISION_REQUIRED:
UNRESOLVED:
```

**Decisão:** R8.2 é um plano de implementação governado. Código, testes e deploy deverão ocorrer em missão de execução separada, seguindo os gates acima.
