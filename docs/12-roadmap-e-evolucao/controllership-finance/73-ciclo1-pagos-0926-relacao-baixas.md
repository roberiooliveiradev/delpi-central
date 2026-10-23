# 73 — Ciclo 1: relação tabular de baixas (setembro/2026)

**Processo:** PROC-0072. **Data de análise:** 23/10/2026. **Proveniência:** arquivo XLSB privado fornecido pelo PO. Este registro contém somente estrutura, conceitos e estatísticas não monetárias. Não inclui títulos, contrapartes, valores, identificadores bancários ou arquivo original.

## Evidência observada
Uma aba denominada `01-01 - Relacao de Baixas`, com 22 colunas, 948 registros de baixa, 18 cabeçalhos repetidos e 60 naturezas distintas na amostra. Campos funcionais: identificação e parcela do título, tipo, contraparte, natureza, vencimento, histórico, data da baixa, data da digitação, valor original, encargos, descontos, abatimentos, impostos, total baixado, banco, motivo e origem.

Códigos de motivo observados na amostra: `DEB` (600), `CMP` (186), `FAT` (83), `NOR` (65) e `DAC` (14). São descrições da amostra, não semântica homologada. Em 68 registros o valor original difere do total baixado. O grão de evento de baixa não pode ser substituído pelo grão de título. Não considerar toda baixa desembolso bancário.

## Vínculos e limites
- PDF por data: layout `DLP06R01`, análise documental anterior ainda sem commit confirmado.
- PDF por natureza: layout `nat.prt`, documento 72.
- Rotina `FINR190`: candidata funcional no inventário de acessos da Contabilidade (documento 60), sem comprovação de que produziu esta exportação.
- Contratos R01/R02: consultas a liquidações, documento 48; paridade oficial não demonstrada e `officialTotals:false` permanece.
- A semelhança dos campos não comprova mesma população, filtros, parâmetros ou totais entre as três fontes.

## Ciclo 2 — validações
1. Identificar produtor, versão, parâmetros, competência e filial.
2. Inventariar chave técnica de evento de baixa e relacionamentos com títulos.
3. Homologar significado e efeitos financeiros de `DEB/CMP/FAT/NOR/DAC`.
4. Verificar parcialidade, compensações, estornos e critérios anti-duplicidade.
5. Conciliar cobertura, motivos, naturezas e subtotais com os dois PDFs.
6. Investigar o aviso de log de inconsistências mencionado nos PDFs, em ambiente autorizado.
7. Vincular a evidência homologada a P2/P5, sem alterar contratos nem permissões por inferência.

**Classificação:** `STRUCTURE=PROVEN_DOCUMENT`; `REASON_CODES=PROVEN_DOCUMENT`; `PRODUCER_FINR190=TO_INVENTORY`; `REPORT_PARITY=TEST_NOT_RUN`; `R01_R02_PARITY=TEST_NOT_RUN`; `RUNTIME=NO_GO`.
