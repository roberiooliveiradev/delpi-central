# 72 - Ciclo 1 | Pagamentos por natureza

Data de revisao: 2026-10-22. PROC-0072. Inventario documental conceitual de fonte privada; sem valores, titulos, terceiros, documentos fiscais ou anexos.

## Estrutura comprovada
O layout do relatorio `SIGA/nat.prt/v.12` apresenta eventos de baixa ordenados por natureza financeira, com subtotais por codigo e descricao de natureza e fechamento geral. Referencia 30/09/2026; emissao 01/10/2026; 35 paginas. Campos funcionais: identificacao do titulo/parcela e contraparte; natureza, vencimento, historico, baixa, digitacao; valor original, acrescimos, descontos, abatimentos, impostos, total baixado; banco, motivo e origem.

## Regras de interpretacao
- Comparar ao layout `DLP06R01` por data (analise do Ciclo 1 ainda pendente de registro no repositorio). Os dois layouts reorganizam eventos, mas equivalencia completa de cobertura e totais **nao foi demonstrada**.
- Natureza financeira e classificacao de titulo/baixa, nao automaticamente conta da DRE ou centro de custo.
- Compensacoes, baixas vinculadas a faturas e pagamentos convivem no relatorio. Nao converter todo total baixado em desembolso bancario.
- Eventos parciais e adiantamentos relacionados exigem chave de baixa, motivo, natureza e regras anti-dupla-contagem.
- O fechamento exibe categorias separadas de baixa e aviso para avaliar log de inconsistencias; o log nao foi fornecido.
- `FINR190` e rotina candidata da lista de acessos da Contabilidade, enquanto `nat.prt` e identificador impresso do layout. Correlacao tecnica pendente.

## Ciclo 2
PAYNAT-01: confirmar rotina de menu, producer, versao, parametros e filtros.
PAYNAT-02: inventariar origem e dicionario de naturezas, chaves de titulo e baixa.
PAYNAT-03: homologar tratamento de compensacoes, parcialidades, motivos e origens.
PAYNAT-04: reconciliar detalhamento por natureza com agrupamento diario sob mesmo cutoff.
PAYNAT-05: obter resultado do log de inconsistencias por canal autorizado.
PAYNAT-06: confrontar com posicao em aberto, arquivos de baixas e contratos R01/R02 sem promover paridade nao testada.
PAYNAT-07: mapear evidencia ao checklist P2 e pacote P5 ja aprovados.

Status: `LAYOUT=PROVEN_DOCUMENT`; `NATURE_GROUPING=PROVEN_DOCUMENT`; `LOG_WARNING=PROVEN_DOCUMENT`; `LOG_RESULT=TO_INVENTORY`; `FINR190_MAPPING=TO_INVENTORY`; `CROSS_LAYOUT_PARITY=TEST_NOT_RUN`; `RUNTIME=NO_GO`.
