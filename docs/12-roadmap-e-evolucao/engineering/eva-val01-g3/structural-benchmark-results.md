# G3 — Resultados estruturais (90264135 p10/12/13)

**PDF SHA:** `af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3` (`MATCH`)  
**GT:** G1 DRAFT (não homologado)  
**Runtime:** container `delpi-engineering-api`, PaddleOCR `3.3.0`, SLANet em cache  
**Baseline A:** `table_structure_slanet` + OCR tokens PDFium@~200dpi  

Variantes de crop (mesma engine — **não** tuning por produto; testa qualidade do **recorte**):

| Label | Origem do bbox |
|---|---|
| `slanet_u_crop` | crop Understanding/regioner medido no G2 (produtivo amplo) |
| `slanet_g1_draft_crop` | `table_bounding_box_px` G1 DRAFT (região tabular selecionada) |

## Inventário de frameworks

| Framework | Importável | Pesos em cache G0 | Operacional no G3 | Notas |
|---|---|---|---|---|
| SLANet (`TableStructureRecognition`) | sim | sim | **sim** | único motor tabular operacional |
| PP-StructureV3 | sim | **não** | **não** | `RuntimeError` dependency; sem pesos |
| TableRecognitionPipelineV2 | sim | **não** (deps RT-DETR) | **não** | dependency error; exigiria provisionar modelos |
| TableCellsDetection | sim | **não** | **não** | tentativa de download bloqueada/removida; FS read-only parcial |

**Cache restaurado ao baseline G0** após probe (RT-DETR removido). Nenhum framework novo ficou instalado para produção.

## P10 — duas linhas / dois códigos

| Variante | cells | fused `10080192 10090316` | `line_texts` | Understanding fused | dur (s) |
|---|---|---|---|---|---|
| u_crop | 295 | **sim** | sim `['10080192','10090316']` | sim | 1.15 |
| g1_draft_crop | 75 | **sim** | sim | sim (só essa fusão) | 0.35 |

**Conclusão P10:** recorte mais justo **não** separa as células de código no SLANet. OCR já separa tokens. Sinal de recuperação (`line_texts`) existe na saída do adapter. Perda estrutural residual = **consumo Understanding**, não falta de engine alternativa operacional.

## P12 — subset `50225702` + AE/AH/AG

| Variante | cells | giant rowspan | AE/AH/AG células distintas | códigos filhos | `50225702` em células | dur (s) |
|---|---|---|---|---|---|---|
| u_crop | 200 | **sim** (rs=11) | fraco | presentes no blob | no blob gigante | 0.56 |
| g1_draft_crop | 69 | **não** | **AE/AH/AG + códigos FIELD_IDENTIFIED** | sim | **não detectado neste crop/assoc** | 0.35 |

**Conclusão P12:** crop apertado elimina o rowspan monolítico e preserva linhas filhas com item/código — ganho estrutural **via regioner**, mesma SLANet. Vínculo pai visual `50225702` ainda não materializado como `parent_group_candidate` (papel/associação — Understanding). Não declarar “SLANet resolve hierarquia sozinho”.

## P13 — tabela vs rodapé `4 5`

| Variante | crop inclui y≥1580 | célula `4 5` | Understanding `component_code='4 5'` | pass estrutura |
|---|---|---|---|---|
| u_crop | sim | **sim** | **sim** | falha |
| g1_draft_crop | **não** | **não** | **não** | **PASS** |

**Conclusão P13:** rejeição do falso componente é **função do crop** (excluir banda de índices 1…8). Engine alternativa não necessária para este caso.

## Regressão smoke (não holdout)

`90264026` SHA `4d0c2e2f…fec4`: SLANet executou (333 cells, score≈0.959, consistent). Apenas smoke — **não** true-unseen.

## Custo (SLANet nas 3 páginas)

| Página / variante | duration_s | rss_delta_mb (medido) |
|---|---|---|
| p10 u / g1 | 1.15 / 0.35 | ~0 (processo já aquecido) |
| p12 u / g1 | 0.56 / 0.35 | ~0 |
| p13 u / g1 | 0.41 / 0.36 | ~0 |

Alternates não operacionais: PP-Structure ~0.01s fail-fast; TRPV2 fail-fast; CellsDet ~81s tentando download (abortado/limpo).
