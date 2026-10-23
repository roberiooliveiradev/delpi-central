# 70 - Ciclo 1 | Contas a receber - posicao de titulos

Data: 2026-10-22. Processo PROC-0072. Fonte privada: A Receber.xlsb. Somente metadados estruturais e conceitos; **nao publicar clientes, lojas, titulos, valores, codigos bancarios, dados fiscais ou arquivo original**.

## Evidencia documental

Uma aba `01-01 - Posicao dos Titulos a ` com referencia **30/09/2026** e emissao **01/10/2026**. A exportacao tem **17 colunas**, **560 linhas com valores de titulo** e **11 linhas de cabecalho repetidas** intercaladas em 574 linhas fisicas. Trata-se de snapshot de titulos **em aberto**, e nao relatorio de recebimentos/baixas.

Campos da origem: `Codigo-Lj-Nome do Cliente`, `Prf-Numero Parcela`, `TP`, `Natureza`, `Data de Emissao`, `Vencto Titulo`, `Vencto Real`, `Bco St`, `Valor Original`, `Tit Vencidos Valor Atual`, `Tit Vencidos Valor Corrigido`, `Titulos a Vencer Valor Atual`, `Num Banco`, `Vlr.juros ou permanencia`, `Dias Atraso`, `Historico`, `(Vencidos+Vencer)`.

Tipos encontrados na amostra: `NF`, `NCC`, `RA` e `BOL`. Interpretacao desses tipos, efeitos de compensacao/notas de credito e semantica de codigos bancarios requerem dicionario ERP. Campo de juros/permanencia aparece vazio na amostra; isso **nao prova ausencia global**. A coluna final nominal `(Vencidos+Vencer)` nao contem valores de dados na amostra: **nao inferir que essa coluna seja o total oficial**. Datas foram armazenadas como numeros seriais Excel no XLSB; converter antes de qualquer regra temporal.

## Relacao com demais fontes

- `FINR130` no doc 60 e candidato funcional a produtor da posicao de receber. O arquivo nao traz comprovacao de codigo/versao/parametros da rotina.
- Doc 69 descreve a posicao a pagar: ambos sao snapshots de titulos **abertos**, mas com entidades, tipos, campos e regras distintas.
- `FINR190` trata liquidacoes/baixas: nao somar titulos abertos aos eventos recebidos ou atribuir paridade direta. Um mesmo titulo pode figurar em fluxos de baixas parciais e saldo remanescente dependendo do corte.
- Relatorios de recebidos/baixados e contratos R01/R02 (doc 48) carecem de validacao de filtros, chaves, sinal, motivo de baixa, abatimento e corte antes de qualquer conciliacao.
- Documento pode ser candidato a evidencia do checklist P2/P5, sujeito a owner, destinatario e autorizacao definidos; a consulta via MFE exige BFF do Portal, que depende das authorities Core/api-delpi.

## Ciclo 2: roteiro
| ID | Validacao requerida |
|---|---|
| AR-01 | Identificar programa/versao/parametros, filial, competencia e data efetiva do snapshot |
| AR-02 | Inventariar tabelas, dicionario de cliente/loja, titulo, prefixo, parcela, natureza e bancos |
| AR-03 | Homologar interpretacao de NF/NCC/RA/BOL e como creditos/adiantamentos afetam aberto |
| AR-04 | Validar vencimento contratual vs real, atraso, feriados, correcao e juros |
| AR-05 | Homologar valor original, vencido atual/corrigido e a vencer; campos vazios e arredondamentos |
| AR-06 | Conciliar FINR130 vs eventos de recebidos, FINR190 e R01/R02 sem confundir posicao com fluxo |
| AR-07 | Definir evidencias P2/P5, escopo de dados e permissoes existentes do Portal |

**Status:** `STRUCTURE=PROVEN_DOCUMENT`; `OPEN_RECEIVABLE_SNAPSHOT=PROVEN_DOCUMENT`; `FOUR_SAMPLE_TYPES=PROVEN_DOCUMENT`; `PRODUCER_FINR130=TO_INVENTORY`; `ERP_PARITY=TEST_NOT_RUN`; `SETTLEMENT_RECONCILIATION=TEST_NOT_RUN`; `RUNTIME_IMPLEMENTATION=NO_GO`.

Este registro nao contem clientes, bancos, valores, documentos individuais, linhas transacionais nem planilha original.
