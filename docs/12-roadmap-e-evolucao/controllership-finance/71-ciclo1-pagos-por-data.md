# 71 — Ciclo 1: pagamentos por data

**Data:** 23/10/2026. **Fonte:** PDF privado Pagos por dt. **Escopo:** descrição sanitizada do layout, sem transações nem valores.

Relatório impresso SIGA/DLP06R01.prt/v.12: relação de títulos pagos em reais por data de pagamento, referente a setembro/2026, com 33 páginas. FINR190 permanece rotina candidata, não homologada.

Campos observados: prefixo, número, parcela, tipo, contraparte, natureza, vencimento, histórico, data de baixa, valor original, juros/multa, correção, descontos, abatimentos, impostos, acessórios, total baixado, banco, data de digitação, motivo e origem. A apresentação inclui agrupamentos por data e subtotais. O histórico pode ocupar múltiplas linhas.

O fluxo de baixas não equivale à posição de títulos em aberto. Compensação não comprova saída bancária; valor original não implica liquidação integral. Os dicionários de motivo/origem, sinais e tratamento de estornos permanecem TO_INVENTORY.

Cruzamentos: doc 69 (posição a pagar), doc 72 (pagos por natureza), doc 73 (exportação XLSB de baixas) e doc 48 (R01 TARGET). Não foi executada conciliação integral entre relatórios ou paridade com a fonte ERP.

Pendências: confirmar produtor, parâmetros, filial, competência, moeda e filtros; identificar chave e cardinalidade FK2/FK7/SE2; validar compensações, estornos e parcialidades; obter log de inconsistências; testar paridade com PDF/XLSB e SQL autorizado; confirmar segregação Core/BFF/api-delpi.

**Evidência:** PROVEN/OBSERVED para layout; TO_INVENTORY para regras e fontes ERP; TEST_NOT_RUN para paridade. Nenhum GO de runtime.