# GLPI #852 — Data física de recebimento no OTD Compras

**Data da revisão:** 2026-11-18  
**Chamado:** OTD Compras, Adriano de Placido de Carvalho  
**Estado:** implementação em PR, sem merge/deploy e com ativação escura por padrão.

## Problema

A view `dbo.VW_PONTUALIDADE_FORNECEDORES` calcula `DIAS` com
`DATEDIFF(DAY, SD1.D1_DTDIGIT, SC7.C7_DATPRF)` e publica
`DT_DIGITACAO` como eixo temporal. Uma entrega física em 12/08,
digitada em 14/08 e prometida para 12/08 fica indevidamente atrasada.

O módulo `lancamento-notas-fiscais` armazena
`invoice_posting_requests.received_at TIMESTAMPTZ` (data/hora física
informada pelo solicitante), independente de `issue_date` (emissão fiscal)
e `erp_entry_date` (digitação no Protheus). O campo de recebimento é
informável e o formulário sugere o horário corrente: depende da disciplina
de registro; não é prova automática da chegada física.

## Evidências 18/11/2026

- A view foi inspecionada diretamente no SQL Server (somente leitura).
- BlazeSQL/SD1010 01/10 a 17/11: 566 documentos/1.269 itens na
  matriz e 598 documentos/1.633 itens na filial, pela chave fiscal
  filial+documento+série+fornecedor+loja (contagens exploratórias).
- CLARA listagem de até 100 lançamentos conciliados recentes por filial:
  63/100 (01) e 63/100 (02) com data física anterior à digitação ERP.
  Isso NÃO é percentual de erro do OTD, pois as NF podem estar fora do
  universo MP/3019 e do recorte de prazo.
- Contrato de conciliação LNF em `totvs_invoice_posting_sf1_sql.py`:
  filial+SA2 fornecedor/loja+documento normalizado+serie normalizada,
  com `sf1_recno` no estado `posted` e regra especial beneficiamento.

## Arquitetura implementada (feature flag OFF por padrão)

1. **Owner do dado** `controllership-finance-api` disponibiliza
   `GET /internal/otd-receipts?start_date=...&end_date=...&branch=01`
   (branch opcional), apenas sob `X-Delpi-Service-Token` validado
   pelo mesmo mecanismo S2S vigente. NÃO altera router LNF humano,
   nem repassa nomes de fornecedores, usuários ou anexos.
2. Resposta `{complete:true,source:"lancamento_notas_fiscais",items:[...]}`;
   cada item contém filial, fornecedor/loja, documento fiscal 9 dígitos,
   série normalizada, `sf1_recno`, `received_date` já convertida para
   o fuso `America/Sao_Paulo` e `erp_entry_date`.
   Fonte: `posted` + `sf1_recno` válido e modelo NF-e
   (ou legado sem modelo registrado); CT-e/NFS-e ficam fora do OTD
   de recebimentos de mercadorias. Ambiguidade fiscal é
   excluída no owner; fonte truncada (>10.000) recusa o request HTTP 503.
3. **Consumidor** `api-delpi`: flag
   `OTD_PHYSICAL_RECEIPTS_ENABLED=false` por padrão. Com `true`,
   busca o lote físico/ERP em HTTP interno uma vez por objeto repositório.
   Não se conecta ao schema LNF. Falha HTTP, credencial ausente ou
   snapshot `complete!=true` **interrompe o cálculo**, não regrava
   indevidamente como ausência de registro.
4. SQL Server recebe o snapshot por parâmetro `OPENJSON(CAST(? AS NVARCHAR(MAX)))`.
   CTE `OTD_EFFECTIVE` reproduz o **grão da view Protheus original**
   SD1×SC7, acrescenta comparação de filial, fornecedor/loja, nota
   normalizada e série, e calcula:
   - `DT_DIGITACAO_ERP` = SD1.D1_DTDIGIT (não sobreposto);
   - `DT_DIGITACAO` = `COALESCE(received_date, D1_DTDIGIT)`
     (**eixo efetivo usado pelo legado e pelos filtros**);
   - `DIAS` = `DATEDIFF(DAY, data_efetiva, data_prometida)`;
   - `RECEIPT_SOURCE` = `lnf_fisico` ou `erp_digitacao`.
   A SQL nunca faz UPDATE no TOTVS.
5. Preserva universo atual `MP OR 3019%` para `/supplies/otd`
   e só `MP` para a família `/supplies/purchase-order-otd`.
   Resumo, série, rankings, painel paginado e detalhamento de
   atrasados usam a mesma regra de data.
6. Filtros por período são aplicados **sobre a data efetiva** após
   vincular a NF. A consulta SQL inclui linhas digitadas fora da janela
   quando tiverem correspondência física na janela (virada de mês).
7. O painel mantém `receipt_entry_date` como **data ERP real** e
   acrescenta `receipt_effective_date` e `receipt_source`.
   A tabela de Entregas no Portal Suprimentos oferece a nova
   coluna `Recebimento OTD` com indicação de origem física; os
   controles de ordenação, paginação e exportação seguem o BFF.
8. Chaves de cache da API DELPI foram separadas por modo LEGADO/FÍSICO.
   Após virar a flag, reiniciar o container para limpar qualquer cache
   anterior de processo. Verificar caches SI/BFF em consumidores.

## Regras negativas e riscos residuais

- Sem registro LNF conciliado, registro cancelado, nota ambígua ou
  chave fiscal não coincidente → data de digitação como hoje.
- Beneficiamento com partido SA1 diferente de SA2: a associação só
  ocorre se a chave física SD1/SA2 coincidir; caso contrário mantém ERP.
- A leitura da fonte está limitada aos registros com data física **OU**
  data de digitação fiscal da solicitação **dentro da janela**. Divergência
  extraordinária entre F1_DTDIGIT e D1_DTDIGIT fora dessas duas datas
  pode exigir investigação; observar na comparação de rollout.
- A rota LNF não garante que `received_at` foi confirmado por hardware
  ou operador: o campo pode ser preenchido manualmente.
- Outras famílias que usam diretamente a view, como
  `supplier_performance_sql.py` (IDF), continuam no contrato próprio;
  **não** foram alteradas silenciosamente. Se for desejada paridade
  do IDF, desenvolver critérios separados e homologados.
- Não executar o modo físico antes de comparar amostras por filial e
  viradas de mês; a mudança altera inclusive a competência histórica.

## Implantação controlada (não feita nesta PR)

1. Merge PR após CI completo e revisão. Não há migração PostgreSQL ou
   alteração de tabelas Protheus nesta entrega.
2. Publicar **primeiro** `controllership-finance-api` (rota interna
   S2S), mantendo `OTD_PHYSICAL_RECEIPTS_ENABLED=false`.
3. Conferir health da BFF e testar diretamente o endpoint interno com
   token de serviço, sem imprimir o token nos logs/console.
4. Publicar `api-delpi`, `supplies-api` e `supplies` com flag OFF.
   Coletar baseline dos OTDs 01/02 e consolidado em agosto e
   setembro de 2026; salvar totais, prazos, % e exemplos.
5. Alterar **somente** `OTD_PHYSICAL_RECEIPTS_ENABLED=true` no
   `infra/.env`; recriar `api-delpi` e conferir logs.
   Validar mês de virada (31/08 física, 02/09 fiscal), nota não
   cadastrada, nota cancelada, vários itens em mesma NF, duas séries
   do mesmo número, múltiplos pedidos, Matriz/Filial, 3019, SI e TV.
6. Verificar contagens: cada linha SD1/SC7 pode mudar **mês** e
   **situação**, mas não pode se duplicar. O percentual consolidado
   deve continuar sendo calculado sobre a união de 01+02, não média
   simples de percentuais.
7. Rollback **não destrutivo:** retornar
   `OTD_PHYSICAL_RECEIPTS_ENABLED=false` e recriar apenas `api-delpi`.
   As rotas legadas e dados ERP não mudam.

**Critérios de aceite:** fonte física prioritária onde conciliada,
fallback somente por ausência de correspondência, erros de dependência
explícitos, data de competência corrigida, sem duplicação, todos os
consumidores do OTD canônico consistentes, e evidências reais aprovadas
pelo responsável de Suprimentos antes de solucionar #852.
