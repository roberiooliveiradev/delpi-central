# G2 — Matriz candidata Totus × desenho + casos negativos

**Regra absoluta:** é **proibido** copiar o nível/pai oficial do Totus para preencher relação visual **não** comprovada no PDF.

## Correspondência candidata

| Campo | Totus (oficial) | Desenho (visual) | Regra de alinhamento candidata |
|---|---|---|---|
| Produto raiz | `root.code` (SG1 raiz) | Título/set code impresso (ex. 90264135) | Match de identidade documental |
| Pai | `G1_COD` / ancestral na árvore | Célula de conjunto/subconjunto (rowspan) | Só se o path visual comprovar o mesmo pai |
| Filho | `G1_COMP` / `BomNode.code` | Coluna Componente | Match de código; pai visual deve concordar |
| Nível | `bom_level` / profundidade na árvore | Profundidade do **caminho visual** (set→subset→item) | Níveis só comparáveis com path visual completo |
| Tipo | `B1_TIPO` (MP/PI/PA) | — | **Não inferir** pelo desenho; só Totus |
| Quantidade | `G1_QUANT` + UM | Coluna QTD. | Comparar só com unidade compatível; senão INCONCLUSIVE |
| Ocorrência | nó na árvore (sem occurrence_id) | Item + contexto de tabela/página | Desenho é autoridade da ocorrência visual |
| Revisão | vigência G1_INI/FIM (server_date) | Revisão do PDF (quando tipada) | Sem binding → não declarar equivalência revisional |

## Casos negativos (devem falhar fechado / INCONCLUSIVE)

| ID | Caso | Esperado |
|---|---|---|
| NEG-01 | Código correto, pai diferente | `PARENT_RELATION_MISMATCH` / não promover |
| NEG-02 | Código correto, nível diferente | não equalizar níveis sem path visual |
| NEG-03 | Mesmo componente em dois pais | duas ocorrências; não colapsar |
| NEG-04 | Código só na descrição | não vira `component_code` da linha |
| NEG-05 | Tabela parcialmente lida | não marcar ausências Totus como DRAWING_MISSING na região não anotada |
| NEG-06 | Revisões incompatíveis | INCONCLUSIVE / block |
| NEG-07 | Quantidades/UM não comparáveis | quantity INCONCLUSIVE |
| NEG-08 | `4 5` / índices de rodapé | nunca match Totus como componente |
| NEG-09 | Fusão `10080192 10090316` | não match único; abster ou split |

## Exemplo 90264135 (ilustrativo — payload Totus live não obtido)

| Ocorrência visual | Filho visual | Pai visual | Totus (quando disponível) | Status G2 |
|---|---|---|---|---|
| p10 A2 | 10080192 | 90264135 | CONSULTAR structure live | EVA fundiu com A3 → **não alinhar** até split |
| p10 A3 | 10090316 | 90264135 | CONSULTAR structure live | idem |
| p12 AE sob 50225702 | 10010028 | 50225702 | CONSULTAR se 50225702∈árvore e filho∈seus components | EVA perdeu parent link |
| p13 falso 4 5 | — | — | nenhum | **NEG-08** |

`LIVE_STRUCTURE_SAMPLE_90264135=TEST_NOT_RUN` (AUTH). Inventário de contrato permanece válido para G6 futuro.
