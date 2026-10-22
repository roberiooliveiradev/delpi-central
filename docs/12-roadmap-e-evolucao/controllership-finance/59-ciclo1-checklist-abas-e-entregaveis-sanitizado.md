# 59 - Ciclo 1: checklist de entregaveis - leitura das tres abas

**Processo:** PROC-0072. **Data:** 22/10/2026. **Fonte:** documento privado do PO (planilha de entregas); este resumo preserva somente conceitos, sem linhas ou valores operacionais, dados fiscais, bancos/contas, identificadores de documentos, anexos ou imagens originais.

## Proposito confirmado pelo PO

A planilha e a **referencia operacional consultada pela responsavel pelo fechamento para saber o que precisa preparar e enviar**, por contexto de unidade/filial e destinatario. **Celula verde, conforme legenda "Enviar", significa entrega esperada nesse contexto**, nao status de envio ou aceite. A ausencia de verde e sinais suplementares nao devem ser traduzidos automaticamente como dispensado/N-A sem homologacao.

**Escopo vigente informado pelo PO:** matriz e filial da empresa de componentes. A antiga coluna de empresa/segmento industrial e legada e deve ser desconsiderada para configuracao de entregas ativas, mantendo historico privado.

## Abas e significado

| Aba | Conteudo conceitual | Aprendizado e papel no produto |
|---|---|---|
| **Eletronico** | Relatorios e arquivos digitais: extratos e comprovantes externos, baixas a pagar/receber, importacoes/cambio, P7/estoque, CPV/Kardex/inventario, faturamento versus MOD, material em processo, faturamento por unidade, classificacao CC e excecoes fiscais | Identificar **arquivos/relatorios digitais esperados** para cada pacote e seu contexto de origem; nem tudo vem do TOTVS |
| **Fisico** | Evidencias fiscais: notas e comprovantes de materiais/consumo, embalagem, fretes, devolucoes, ativos, utilidades e servicos; evidencias contabeis: despesas, beneficios, seguros, guias, adiantamentos, viagens e pagamentos diversos | Identificar **documentos comprobatórios esperados**, com natureza e finalidade, e distinguir necessidade de comprovante de existencia de relatorio |
| **Planilha1** | Lista auxiliar repetida de categorias de materiais, consumo e despesas (ex.: embalagem comum/apresentacao, manutencao, EPI, limpeza, insumos e ativos) | **Vocabulario candidato de classificacao**, nao checklist de envio executado nem codificacao automaticamente igual a TES, tipo produto, centro de custo ou plano contabil |

As tres abas nao requerem tres paginas novas. Elas enriquecem o modelo preexistente de checklist e evidencias. A aba auxiliar deve ser homologada como catalogo ou orientacao, com owner e versao, antes de qualquer vinculacao tecnica.

## Encadeamento com a arquitetura aprovada

- **P6 / doc 13:** template mestre de entregaveis, categorias, regra de aplicabilidade; nao alterar retroativamente snapshots.
- **P2 / doc 09:** checklist por competencia, itens aplicaveis, requisitos, evidencia, pendencias, validacao/rejeicao/historico; separacao explicita entre esperado, preparado, anexado e validado.
- **P5 / docs 12 e 37:** pacote por destinatario, PackageVersion, finalizacao distinta de submissao e revisao, disponibilizacao in-portal para revisor humano autorizado, notificacao pela plataforma; sem pacote anexado por email.
- **P1 / doc 08:** acompanhamento de progresso e bloqueios, sem confundir verde com entregue.
- **Core:** identidade, effective permissions e elegibilidade; filial como dimensao, nunca permission code.

A planilha identifica **que entrega e esperada**, mas nao modifica quem pode aprovar, quorum, lifecycle ou estados ja decididos. A definicao de recipients/required areas deve seguir contratos existentes e homologacao do owner.

## Matriz para continuidade do Ciclo 1 e levantamento tecnico do Ciclo 2

| ID | Verificacao requerida | Evidencia/status |
|---|---|---|
| CK-A | Para cada item verde em matriz/filial, identificar artefato, origem, competencia, responsavel, destinatario, formato e dependencia | TO_INVENTORY |
| CK-B | Conferir variacoes de obrigatoriedade, celulas sem verde e sinais auxiliares | TO_INVENTORY |
| CK-C | Distinguir digital/fisico e tipo de evidencia sem presumir upload obrigatorio para todas as fontes | TO_INVENTORY |
| CK-D | Confirmar criterios contabeis/fiscais de categorias e descricoes de finalidade | TO_INVENTORY |
| CK-E | Confrontar arquivos de P7, CPV, MOD, SD1, financeiros e documentos externos com contratos/producers e outputs reais | TEST_NOT_RUN |
| CK-F | Confirmar matriz/filial no cadastro organizacional atual, excluindo contexto industrial legado dos templates vigentes | PO_CONFIRMED; ERP_TO_INVENTORY |
| CK-G | Comparar catalogo candidato com RQ/AC P2/P5/P6, corrigir lacunas sem novas decisions de review | TO_INVENTORY |

## Limites e classificacoes

`THREE_TAB_STRUCTURE=PROVEN_DOCUMENT`; `CHECKLIST_PURPOSE=PO_CONFIRMED`; `GREEN_LEGEND_SEND=PROVEN_SCREENSHOT_AND_PO_CONFIRMED`; `LEGACY_ORG_EXCLUSION=PO_CONFIRMED`; `DELIVERY_STATUS=TEST_NOT_RUN`; `REVIEW_ACCEPTANCE=TEST_NOT_RUN`; `RUNTIME_IMPLEMENTATION=NOT_AUTHORIZED`.

**Protecao:** este documento nao contem registros, valores, fornecedores, identificadores empresariais individualizados, extratos, capturas nem hashes de arquivos privados. Nao reproduzir a planilha original no repositorio.
