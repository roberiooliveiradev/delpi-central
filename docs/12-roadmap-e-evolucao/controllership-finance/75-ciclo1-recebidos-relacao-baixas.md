# 75 — Ciclo 1: relação tabular de recebimentos (PROC-0072)

> Análise documental: 23/10/2026. Fonte: exportação XLSB privada fornecida pelo PO. Este documento é **sanitizado**: não contém arquivo original, valores, identificadores, dados de terceiros, linhas de transação nem evidências privadas. **Sem GO de runtime.**

## A. Identificação e proveniência

- Material de origem: `Recebidos.xlsb` (privado; não versionado).
- Referência do arquivo: setembro/2026; emissão registrada no início de outubro/2026.
- Produtor de layout: família de relação de baixas; possível associação ao relatório `DLP06R01` pela apresentação e ao `FINR190` como rotina **candidata**, não comprovada por parâmetros, execução de menu ou metadados do ERP.
- Estágio: inventário documental Ciclo 1; source-of-truth técnico permanece no owner `api-delpi`, sujeito à homologação no Ciclo 2.

## B. Estrutura observada

- Uma aba: `01-01 - Relacao de Baixas`.
- 22 campos de saída: `Prf`, `Numero`, `Prc`, `TP`, `Cli/For`, `Nome Cli/For`, `Natureza`, `Vencto`, `Historico`, `Dt Baixa`, `Valor Original`, `Jur/Multa`, `Correcao`, `Descontos`, `Abatim.`, `Impostos`, `Valor Acessorio`, `Total Baixado`, `Bco`, `Dt Dig.`, `Mot`, `Orig`.
- Extração documental identificou 657 registros tabulares de baixa, 23 linhas adicionais de cabeçalho repetido e 21 datas distintas de baixa. Esses números descrevem **este artefato**, não o universo de eventos no ERP.
- Motivos presentes: `NOR`, `CMP`, `DAC`, `DEB`; tipos observados: `NF`, `PA`, `NCC`, `RA`, `BOL`. Significados canônicos, origem e efeito bancário não homologados.
- O layout não expõe identificador interno estável de evento `FK1`. Identificação por título isolado não é confiável; há ocorrências com chave aparente de título repetida.

## C. Aprendizados e regras observadas

- Granularidade operacional aparente: **linha de evento de baixa**, e não saldo de título em aberto; confirmar cardinalidade no ERP.
- Em 18 registros, `Valor Original` e `Total Baixado` diferem. Não somar `Valor Original` como fluxo liquidado nem pressupor liquidação integral.
- Existem componentes separados de juros/multa, correção, descontos, abatimento, impostos e acessórios. A fórmula oficial do valor liquidado, o sinal dos ajustes, a moeda e o tratamento de estorno/compensação continuam pendentes.
- `Mot`, `Orig`, `Historico` e `Bco` requerem dicionários e validação do efeito financeiro; baixa contabilizada não prova recebimento bancário.
- Esta leitura não demonstra que todos os movimentos e filiais estejam cobertos; ausência de linha não é valor zero.

## D. Cruzamentos e contratos

- **Doc 74 / `Recebidos.pdf`**: mesma família funcional de relatório de recebimentos por data e campos correspondentes. O PDF contém agrupamentos diários e subtotais; a planilha oferece detalhe tabular. Não foi executado pareamento completo linha a linha nem conciliação de totais.
- **Doc 70 / `A Receber.xlsb`**: posição de recebíveis em aberto, diferente de eventos de baixa; requer reconciliação por título, parcela, data e contexto.
- **Doc 73 / `pagos 09 26.xlsb`**: estrutura de baixa análoga no lado pagar, com composição e códigos de motivo distintos. Não presumir que R01 e R02 sejam simétricos em todas as regras.
- **Doc 48 — R01/R02**: contrato TARGET read-only propõe grão `FK1` para eventos de recebimento e reconciliação com `FK7/SE1`, mas os relacionamentos e totais oficiais permanecem não homologados. Nenhum endpoint ganha GO pelo presente inventário.
- **Doc 47 / T01**: registrar achado como evidência documental, sem promover G4/G5/G6 a PASS.

## E. Pendências para o Ciclo 2

1. Confirmar rotina/programa efetivo e versão do layout, filtros, competência, filial, empresa, moeda, data e parâmetros de geração.
2. Confirmar tabela de eventos, identificador físico, cardinalidade com título e regra de parcelamento, compensações, estornos e baixa parcial.
3. Homologar os códigos `NOR/CMP/DAC/DEB`, tipos de título, origem, histórico, referência bancária e sinais financeiros.
4. Obter e revisar o **log de inconsistências** associado à geração oficial, ainda não fornecido.
5. Testar paridade de população, contagens e totais por dia/natureza/motivo entre XLSB, PDF, `FINR190` e leitura autorizada do ERP, incluindo casos negativos.
6. Resolver escopo de filial/empresa e autorização efetiva, conforme contratos R01/R02, antes de qualquer exposição de dados.

## F. Classificação e gates

- Estrutura, campos, códigos presentes e contagens do artefato: `PROVEN / OBSERVED`.
- Produtor `FINR190`, semântica dos códigos, joins, chave estável e total oficial: `TO_INVENTORY`.
- Paridade SQL/ERP/PDF: `TEST_NOT_RUN`.
- Implementação de R01/R02, BFF ou MFE: **não autorizada por este documento**.
- Dados do arquivo permanecem privados; GitHub mantém exclusivamente o mapa conceitual sanitizado.

## G. Próximo passo

Conferir pendência do Documento 71 e cobertura dos arquivos originais, depois preparar matriz consolidada do Ciclo 1 (relatório, rotina candidata, finalidade, regras observadas, evidências, owner, pendências e gate seguinte). Não iniciar Ciclo 2 nem runtime sem novo gate.
