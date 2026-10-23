# 69 - Ciclo 1 | Contas a pagar - posicao de titulos

Data 22/10/2026. Processo PROC-0072. Fonte privada: planilha binaria A pagar.xlsb. **Somente informacoes conceituais e esquema funcional; nao publicar credores, titulos, valores, IDs, linhas ou original.**

## Identificacao e estrutura
Uma aba `01-01 - Posicao dos Titulos a ` com referencia **30/09/2026** e emissao **01/10/2026**. Foram identificadas **648 linhas de titulos**, **12 ocorrencias de cabecalho repetido** e **15 colunas**. Os dados sao uma posicao de **obrigacoes em aberto**, nao uma lista de pagamentos/baixas.

As colunas sao: Codigo-Nome do Fornecedor; Prf-Numero Parcela; Tp; Natureza; Data de Emissao; Data de Vencto; Vencto Real; Valor Original; Tit Vencidos Valor nominal; Tit Vencidos Valor corrigido; Titulos a vencer Valor nominal; Porta-dor; Vlr.juros ou permanencia; Dias Atraso; Historico(Vencidos+Vencer). A grafia reflete os rotulos de origem; os dados das datas sao serializados no XLSB e exigem conversao/corte explicitos.

A amostra inclui tipos `NF`, `PA`, `FT`, `PR`, `NDF`, `CC`, `INV`, `BOL`, `RES`, `FOL` e `TX`; essas abreviaturas sao **codigos observados**, nao semantica homologada. Contagens nao devem ser tratadas como volume normativo. As colunas Porta-dor e Vlr.juros ou permanencia aparecem vazias na amostra, o que **nao prova** que nunca sejam retornadas. Valores vencidos e a vencer sao distribuidos em colunas distintas, exigindo tratamento de nulos/vazios.

## Confronto com inventarios e contrato
- `FINR150` (doc 60) e **candidato funcional** a produtor do relatorio de titulos a pagar em aberto. Codigo do executavel, parametros, layout, branch e integracao ainda `TO_INVENTORY`.
- `FINR190` e os layouts de titulos pagos/baixados tratam **eventos liquidados**. Nao equiparar o saldo de obrigacoes em aberto a baixas, nem somar os dois sem reconstruir o ciclo de vida por chave/tipo/parcela.
- Os contratos de R01/R02 descritos no doc 48 referem-se a liquidacoes read-only; **nao cobrem automaticamente uma posicao de AP em aberto**. Nao atribuir `officialTotals:true` nem homologar paridade por coincidencia.
- Datas de emissao, vencimento contratual, vencimento real e data de referencia nao sao equivalentes. O relatorio nao exibe diretamente data de baixa: por definicao do recorte, trata-se de snapshot de aberto.
- Contexto de fornecedor, natureza e historico e sensivel; ambiente do Portal deve verificar `access/manage` via Core, resource scope e business rule, sem criar permissions por titular, natureza, filial ou tipo.
- No fluxo P2/P5, o PDF ou export homologado pode representar item de evidência, com owner e destinatario definidos pelo checklist atual. A existencia da planilha nao autoriza automaticamente consulta online ou divulgacao de dados de terceiros.

## Fila Ciclo 2
| ID | Validacao necessaria |
|---|---|
| AP-01 | Confirmar programa/versao/parametros, data e contexto organizacional da exportacao |
| AP-02 | Identificar fontes oficiais de titulo aberto, chave composta, fornecedor, natureza, prefixo e parcela |
| AP-03 | Homologar regra de saldo vencido/a vencer, correcao, juros, abatimento, valores parciais e snapshots |
| AP-04 | Investigar tipos NF, PA, FT, PR, NDF, CC, INV, BOL, RES, FOL e TX conforme dicionario ERP |
| AP-05 | Separar vencimento original e real; calculo de dias de atraso e tratamento de fins de semana |
| AP-06 | Confrontar FINR150 com FINR190 e contratos R01/R02 sem misturar aberto com baixado |
| AP-07 | Definir o entregavel do checklist/P5 e governanca de acesso aos dados sensiveis |

**Evidencias:** `ONE_SHEET=PROVEN_DOCUMENT`; `FIELDS_AND_LAYOUT=PROVEN_DOCUMENT`; `OPEN_POSITION=PROVEN_DOCUMENT`; `PRODUCER_FINR150=TO_INVENTORY`; `ERP_SOURCE_PARITY=TEST_NOT_RUN`; `SETTLEMENT_CROSSCHECK=TEST_NOT_RUN`; `RUNTIME_AUTHORIZATION=NO_GO`.

Nenhum valor monetario, fornecedor ou titulo individual foi publicado.
