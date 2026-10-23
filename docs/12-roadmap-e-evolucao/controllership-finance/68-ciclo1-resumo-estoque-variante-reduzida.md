# 68 - Ciclo 1 | Registro de Inventario: variante reduzida e divergencia de abrangencia

**Data:** 22/10/2026. **Processo:** PROC-0072. Fonte: PDF privado de uma pagina, comparado com outro Registro de Inventario de uma pagina recebido anteriormente e inventariado no doc 63. Apenas conceitos/regras/gaps; os PDFs originais, nomes/identificadores fiscais, valores monetarios e screenshots **nao** sao versionados.

## Estrutura observada

O PDF intitula-se **REGISTRO DE INVENTARIO**, com posicao **30/09/2026**, contexto matriz, resumo **EM ESTOQUE**, resumo **EM PROCESSO** e **TOTAL GERAL**. Na secao EM ESTOQUE aparecem apenas materia-prima (MP), produto acabado (PA) e produto intermediario (PI). Na secao EM PROCESSO aparecem MP e PI.

E compatível conceitualmente com a variante reduzida do P7 mencionada pela Joici como documento de entrega a Contabilidade, mas o PDF **nao traz codigo `MATR460`, parametro do programa nem nome do layout Bloco H**. Fonte/variante = `TO_INVENTORY`; nao atribuir origem comprovada.

## Comparacao controlada com PDF anterior de estoque (doc 63)

| Dimensao | Registro anterior | Resumo atual | Resultado |
|---|---|---|---|
| Contexto temporal | posicao de fechamento do mes | mesma data de posicao | `PROVEN_DOCUMENT` |
| Matriz | sim | sim | `PROVEN_DOCUMENT` |
| Categorias EM ESTOQUE | MP, PA, PI e outras categorias de materiais | apenas MP, PA, PI | escopo por categoria mais estreito |
| Categorias EM PROCESSO | MP, PI e duas outras categorias | apenas MP e PI | escopo por categoria mais estreito |
| PA EM ESTOQUE | categoria presente | mesma categoria | **total monetario de PA coincide** nas duas paginas |
| PI EM ESTOQUE | categoria presente | mesma categoria | **total monetario de PI coincide** |
| PI EM PROCESSO | categoria presente | mesma categoria | **total monetario de PI coincide** |
| MP EM ESTOQUE | categoria presente | mesma categoria | **totais NAO coincidem** |
| MP EM PROCESSO | categoria presente | mesma categoria | **totais NAO coincidem** |
| TOTAL GERAL | maior abrangencia aparente | menor abrangencia aparente | totais distintos, nao atribuir causa |

**Observacao decisiva:** o PDF reduzido **nao e comprovadamente apenas um filtro visual de categorias** do PDF anterior, pois o valor da categoria MP tambem se altera dentro das secoes de estoque e processo. Ha necessidade de investigar filtros adicionais por local/armazem, tipo, situacao de terceiros, regra fiscal, deposito, periodo ou versao do custeio, sem escolher uma causa sem evidencia.

A coincidencia da data e de alguns subtotais nao prova paridade global nem que MP deva ser reconciliada sem ajuste. A conciliacao deve isolar filtros, chaves e estado de custeio.

## Relacao com processo e produto

- Doc 57/video: Joici diferencia P7 completo de variante para Contabilidade, mencionando categorias MP/PI/PA. O PDF atual oferece evidencia documental compativel, **nao a prova tecnica do layout H**.
- Docs 61/62/63/64: rastrear pontos de reconciliacao com Kardex, MATR320 e saldo analitico em processo, sobretudo MP que diverge entre os dois resumos.
- Doc 59 e contratos P2/P5/P6: entregavel digital candidato de estoque para Contabilidade; vincular a forma exata exigida no checklist sem criar nova pagina ou fluxo de revisao.
- A pagina refere-se a matriz da empresa de componentes; nao supor que represente a filial ou a empresa industrial legada.

## Investigacoes obrigatorias do Ciclo 2

| ID | Pergunta e prova necessaria |
|---|---|
| P7R-01 | Confirmar programa de origem, versao, menu e parametros de cada uma das duas exportacoes |
| P7R-02 | Identificar diferencas de filtro de tipo, armazem, terceiros, produto, grupo, filial e deposito |
| P7R-03 | Explicar especificamente a divergencia MP EM ESTOQUE e MP EM PROCESSO, sem ajustar por diferenca residual arbitraria |
| P7R-04 | Verificar valores de PA/PI coincidentes sob parametros e status do custeio controlados |
| P7R-05 | Confirmar designacao exata do layout fiscal/Bloco H ou variante contabil com owner |
| P7R-06 | Testar reconciliacao com MATR320, Kardex e material em processo, garantindo mesma data/cutoff e universo |
| P7R-07 | Vincular variante homologada ao deliverable P2 e recipient package P5, com validação humana preexistente |

**Gates:** `STRUCTURE=PROVEN_DOCUMENT`; `NARROWER_CATEGORY_SET=PROVEN_DOCUMENT`; `MP_VALUES_DIFFER=PROVEN_DOCUMENT`; `PA_PI_VALUES_MATCH=PROVEN_DOCUMENT`; `VARIANT_BLOCO_H=TO_INVENTORY`; `EXACT_CAUSE_OF_MP_DIFFERENCE=TO_INVENTORY`; `SOURCE_ROUTINE=TO_INVENTORY`; `CROSS_REPORT_PARITY=TEST_NOT_RUN`; `IMPLEMENTATION_AUTHORIZED=NO`.

**Seguranca:** manter todos os registros/valores e identificadores do material de origem restritos, nunca anexar ou publicar PDF/screenshot.
