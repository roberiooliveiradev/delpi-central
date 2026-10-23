# 77 — Reconciliação de identificadores históricos do Ciclo 1

**Data:** 23/10/2026. **Processo:** PROC-0072. **Escopo:** documentação conceitual, sem anexar arquivos privados, sem alterar contrato ou autorizar implementação.

## Identificação e resolução de colisões

| Referência no handoff anterior | Artefato privado | Identidade vigente | Conclusão |
|---|---|---|---|
| Documento histórico 53 | `CC matriz.xlsb` | Este documento 77, seção CC matriz, para rastreabilidade atual; não equivale ao doc 53 de UX | identificador antigo é alias de conversa, não caminho canônico |
| Documento histórico 58 | `Analise.xlsx` | Este documento 77, seção Análise, para rastreabilidade atual; path anterior não comprovado | alias de conversa sem documento preexistente confirmado |

O **doc 53 vigente** no mesmo diretório é `53-table-ux-final-3-interactions-execution-roadmap.md`, que trata de roadmap de interface. Não renomear, editar ou tratá-lo como análise de CC. Buscas negativas por palavras-chave ou caminhos presumidos não provam inexistência de outro registro antigo. Este novo documento estabelece referência estável para os dois materiais, preservando a proveniência histórica.

## CC matriz — observação documental

Fonte: `CC matriz.xlsb`, privado, fornecido pelo PO. Layout observado: exportação de itens de entrada associada ao alias SD1; campos de filial, documento/item, produto, tipo, quantidade, valores e centro de custo. Finalidade: identificar classificação e conferências de despesas por centro de custo. Owner de validação funcional: Contabilidade/Controladoria; regra e fonte TOTVS canônica: api-delpi. A aplicação correta de centro de custo, filtros, joins e excepcões continua `TO_INVENTORY`. Paridade `TEST_NOT_RUN`.

## Análise — observação documental

Fonte: `Analise.xlsx`, privada, fornecida pelo PO. Planilha `Relatorio` com dimensão de filial, produto, grupo, armazém, moeda, custos médios inicial e final, status/variação. Finalidade: triagem de variações de custo médio durante o fechamento. Owner funcional: Controladoria/Custos; regra TOTVS canônica: api-delpi. Fórmula oficial, política de variação, efeitos de moeda e cutoff continuam `TO_INVENTORY`; paridade `TEST_NOT_RUN`.

## Cruzamentos e gate

Relacionar estes artefatos com o roteiro da Joici (docs 55–57), os relatórios de custos 61–68 e a matriz de encerramento 76. Nenhum dado original, valor, identificador de contraparte ou linha transacional foi versionado. `PROVEN/OBSERVED` apenas para estrutura informada no inventário; conclusões financeiras e SQL não homologadas. Resolução de referências documentais: `ACCEPT_WITH_RESIDUAL`, pois a origem do número histórico não é commit verificável. Fechamento formal do Ciclo 1 segue `PENDING`, Ciclo 2 `NO_GO`.
