# HD #1565 — Lembretes diários de aprovação de SC

Data: 15/11/2026. Solicitante: Joici Motta. Chamado **Alçada SC**, categoria Compras.

## Objetivo e rastreabilidade

O chamado pede que quem insere a SC saiba que ela depende de aprovação e tenha ciência de rejeição. O PO autorizou implementar avisos diários também para quem tem a aprovação na alçada atual.

| Requisito | Implementação | Aceite/evidência |
|---|---|---|
| RQ-1 — Avisar diariamente o solicitante | `DispatchDailyApprovalRemindersUseCase`, categoria `purchase_request_pending_requester` | Destinatário derivado de `C1_USER`; renovação pelo dia de São Paulo |
| RQ-2 — Avisar os aprovadores ativos | Mesmo dispatcher, categoria `purchase_request_pending_approver` | SCR `CR_TIPO=SC`, `CR_STATUS=02`, `CR_APROV` → SAK `AK_COD` → `AK_USER` → identidade do portal |
| RQ-3 — SC, filial, produtos e aprovadores nos detalhes | Conteúdo PT-BR e HTML escapado, com link para abrir a SC | Preview ≤500 caracteres; detalhes HTML completos; link inclui data de emissão para SC antiga |
| RQ-4 — Pendência atual, sem cobranças após encerramento/rejeição | Feed consulta SC1/SCR em cada página; não guarda payload para reenvio | SC bloqueada `B`, saldo de quantidade, sem resíduo `S`, sem item rejeitado `R`; etapas futuras `01` não entram |
| RQ-5 — Renovação diária e controle de repetição | V006, chave `(dia, filial, SC, usuário, papel)` e lease com token | Concorrência, restart, recuperação de lease e virada UTC/Brasil testados |
| RQ-6 — Preservar avisos de decisão e de pedido/recebimento | Pollers existentes preservados | Avisos aprovado/rejeitado são herdados da rotina de decisões existente; regressões incluídas na suíte |
| RQ-7 — Respeitar identidade, acesso e preferências | Resolvedor de identidade existente; despacho pelo Core | Sem associação de identidade não envia; Core aplica acesso ao app e silenciamento/destaque/e-mail |

## Fluxo e contrato

O lifespan de `purchase-requests-api` inicia um poller adicional sob o mesmo gate `PURCHASE_REQUESTS_PO_NOTIFICATIONS_ENABLED`. Cada ciclo consulta **uma página de até 100 SCs**, resolve identidades, disputa leases e envia avisos. Intervalo: `PURCHASE_REQUESTS_APPROVAL_NOTIFICATIONS_INTERVAL_SECONDS`, mínimo 60s (default existente 120s). Ao encerrar a página final, a próxima varredura recomeça. Não depende de login ou portal aberto. O aviso fica armazenado para leitura posterior; e-mail segue a preferência individual existente.

Feed interno: `GET /supplies/purchase-requests/pending-approvals`, operationId `list_supplies_purchase_request_pending_approvals`. Parâmetros `limit` (1–100, default 25), `after_branch` e `after_request_number` (ambos ausentes ou ambos presentes). Ordenação por filial e número da SC, cursor exclusivo, `next_cursor=null` encerra a leitura. Não há janela de data que descarte SC antiga. A paginação ocorre antes de expandir aprovadores paralelos; produtos são buscados em lote, reutilizando a consulta do indicador de alçadas.

Resposta: envelope padrão `success/message/data/error/meta`; `data.items[]` contém `branch`, `request_number`, `requester_protheus_user_id`, `requester_name`, `request_issue_date`, `pending_approvers[{code,name,protheus_user_id,level}]` e `products[{code,description}]`. Contrato tipado em `purchase_request_pending_approvals_schema.py`; OpenAPI runtime é a fonte técnica, com baseline e inventários derivados atualizados. Somente caller interno autenticado `purchase-requests-api` acessa o feed; usuários comuns são negados mesmo com permissão de leitura.

Responsabilidades materiais: arquitetura (owner SQL na api-delpi, orquestração no BFF), segurança (caller S2S e identidade), contratos (feed aditivo), dados (V006 e concorrência), frontend (catálogo e Ajuda), qualidade (regressões), runtime (lifespan e gate), confiabilidade (retry, retenção e logs).

## Persistência e falhas

`purchase_requests.daily_approval_reminders` guarda somente a chave de controle, token, timestamps e resultado. Não copia os dados dos produtos. A reivindicação é atômica com `INSERT ... ON CONFLICT ... WHERE`; leases vencem após cinco minutos e a conclusão usa token para impedir que um worker antigo finalize lease retomado. Sem identidade, não reivindica: uma associação corrigida permite envio na próxima varredura. Falha transitória deixa o lease recuperável. Rejeição permanente do Core é registrada como `skipped` para aquele dia; preferências voltam a ser avaliadas no dia seguinte. Retenção de 90 dias, limpeza uma vez por dia por processo.

Limite conhecido: o Core atual não implementa idempotência de recebimento por `metadata.dedupeKey`. Portanto existe uma janela de entrega **at least once** se o Core gravar o aviso e a resposta HTTP ou a gravação de conclusão se perder; um retry pode duplicar o aviso nessa falha específica. O ledger evita repetição normal por polling/restart e disputa entre workers; não representa garantia de exactly once distribuído. Avisos já emitidos são snapshots do momento da consulta, não são apagados automaticamente ao aprovar depois.

Logs: `purchase_requests.daily_approval_reminders`, evento `daily_approval_reminders_poll`, contadores `observed/dispatched/retry/unmapped`, sem produtos ou identidades nos logs. A leitura TOTVS é somente SELECT. Nenhuma escrita ERP ou capacidade de aprovação foi criada.

## Validação executada

- Serviço: **127 testes passaram**, incluindo os testes de banco com PostgreSQL 16 isolado, oito claims simultâneos, lease expirado, fencing de token, retomada no mesmo dia, próximo dia, papel/usuário/filial distintos e retenção.
- A V006 foi aplicada sem alteração sobre o schema anterior no PostgreSQL isolado. A fixture V001 precisou omitir somente o comando de instalação de `pgcrypto` porque o PostgreSQL embutido não distribui essa extensão; `gen_random_uuid()` nativa atende a fixture. V002–V006 foram executadas integralmente. O runner completo em banco vazio com pgcrypto **não** foi validado nesse ambiente.
- API/TOTVS: **19 testes passaram**, incluindo feed, negação de acesso direto e regressão dos indicadores e das decisões de SC.
- MFE: **28 testes passaram**, typecheck e build passaram; lint dos arquivos alterados passou. Lint geral: quatro erros preexistentes em `usePurchaseRequestRequesters.ts`, `usePurchaseRequestsList.ts` e `routing.ts` (nenhum desses arquivos alterado).
- Catálogo central e espelho do Portal conferidos; detalhes longos são completos no HTML e escapam conteúdo do ERP.
- Consulta EXATA do feed executada no SQL Server DELPI via conector de leitura: **8 SCs** (7 filial 01, 1 filial 02); identidade SAK/AK_USER resolvida. Consulta de produtos em lote: **21 produtos**. Nenhuma notificação foi enviada nessa validação.
- Estatísticas reais em `sys.dm_exec_query_stats`: duas amostras do feed de **74,925 ms** e **52,125 ms** (média amostral **63,525 ms**, máximo **74,925 ms**), CPU final 51,335 ms, 9.365–9.460 leituras lógicas, 8 linhas retornadas. Produtos: **88,895 ms**, CPU 85,385 ms, 839 leituras lógicas, 21 linhas. O elapsed do conector (2,5–3,6s) inclui overhead e não é o tempo da consulta no SQL Server.
- Plano em cache inspecionado, QueryHash `0xF886E407E2AE9CDC`, custo estimado 8,73412, com seeks de índices e quatro clustered scans. O otimizador sugere índices potenciais de SC1010; nenhuma alteração de índice foi aplicada. Para a carteira atual, as consultas ficaram abaixo de 100ms por página e a repetição default é a cada 120s por worker. Escala futura/concurrência de múltiplas réplicas continua dependente de monitoramento.
- Evidências do conector: feed `qOcuyWLuTPF5w9bM4TCp`, repetição `RLa7WmJmOQFQa5Va9ORL`, produtos `5opCSZt6GXhZZQ5Ljh6i`; estatísticas iniciais `p7fdHshJFRjHJCpbSc8h`, plano/estatísticas finais `YZHsYfpxbtBfdMDFEQZx`, estatísticas produtos `IsYpFLlOFOoDjh3cZJ73`. A ausência de SAK010 no catálogo de metadados foi resolvida pela execução autorizada da consulta vigente; a tabela está disponível no banco.
- Entrega real de notificações e smoke produtivo continuam **não verificados**, pois o host SSH não é alcançável.

## Implantação e validação operacional

Estado desta execução: implementação publicada na `main` no commit `d4ccde814eaf5fede7cefbbc0d4f1e714086d0cb`, após autorização explícita do PO para o repositório público `roberiooliveiradev/delpi-central`. Os 28 arquivos publicados foram conferidos por SHA e são idênticos ao commit local aprovado `72e22e2d`; os commits concorrentes de outras frentes foram preservados. O bloqueio automático inicial de publicação foi resolvido com a autorização do usuário e a comprovação de que o inventário enviado integra exatamente o commit aprovado. Implantação produtiva continua pendente: a tentativa do comando canônico via SSH retornou `Network is unreachable` antes de alcançar o host. Nenhuma notificação real foi enviada por esta execução.

Ordem necessária: api-delpi (feed), Core (catálogo), purchase-requests-api (V006 + poller), depois Portal e purchase-requests (preferências e Ajuda). Reutilizar o deploy sequencial canônico. O startup executa a V006 quando `PURCHASE_REQUESTS_RUN_MIGRATIONS_ON_STARTUP=true` (ver configuração efetiva); se desabilitado, executar o runner canônico antes de iniciar o poller.

```bash
cd ~/projetos/delpi-central
git pull --ff-only
./infra/scripts/up-prod-sequential.sh --build api-delpi core-api purchase-requests-api portal purchase-requests
```

O serviço `api-delpi` está confirmado no Compose canônico, com container `delpi-api-delpi`; o startup de migrations do BFF tem default `true`. Consultar health dos cinco serviços e logs do poller. A medição inicial de tempo/leituras/plano está registrada acima; repetir a observação com carteira maior e no processo real do BFF durante a homologação. Validar uma SC pendente com usuário Protheus mapeado: solicitante vê todos os aprovadores e produtos; cada aprovador ativo vê a SC; pessoa de etapa futura não recebe; outra execução no mesmo dia não duplica; aprovação/rejeição/encerramento retira dos novos lembretes. O cenário de rejeição usa também o aviso de decisão já existente.

Rollback: desabilitar o gate mestre de notificações interrompe também os pollers antigos; para rollback só desta feature, reverter o commit e reconstruir os serviços afetados pelo Git. Manter a tabela V006 (aditiva e compatível com o binário anterior). Não apagar registros de usuários ou SCs nem desfazer migrations antigas. Nenhum deploy de Pesquisa de Satisfação é necessário; seus gates permanecem fora do escopo.

## Revisão independente

| Rodada | Veredito original | OCs abertas/fechadas | Resíduo |
|---|---|---|---|
| 1 | INCONCLUSIVE | 0 / 0 | Revisão não reproduziu PostgreSQL e medição SQL estava pendente à época |
| 2 | INCONCLUSIVE | 0 / 0 | Sem alteração de código; medições obtidas pelo executor, não reproduzidas pelo segundo revisor; banco e entrega real continuam sem reprodução independente |

Veredito da rodada 1, sem edição:

```text
veredito: INCONCLUSIVE
rodada: 1
escalar: NAO
escopo: working tree @ 7ca8ba7b
contrato: PRESENTE
independencia: DEGRADADA (verificador: GPT-6/Codex, família GPT-6; executor: GPT-6.1 workhorse)
registro: OK
```

O verificador reproduziu 65 testes Python do escopo, 48 testes dos gates e 28 testes MFE, build/typecheck/lint alterado. Nenhuma ordem de correção foi emitida. Após a rodada 1, a medição SQL e o plano reais foram obtidos conforme a seção de validação acima. PostgreSQL foi executado pelo executor (127 testes verdes), mas não foi reproduzido pelo verificador, que não estava autorizado a iniciar serviços ou migrations. Não atribuir PASS independente a essa evidência.


Veredito da rodada 2, sem edição:

```text
veredito: INCONCLUSIVE
rodada: 2
escalar: NAO
escopo: working tree @ 7ca8ba7b
contrato: PRESENTE
independencia: DEGRADADA (verificador: GPT-6/Codex; executor: GPT-6.1 workhorse)
registro: OK
```

A segunda revisão reproduziu mais 20 testes unitários (12 dispatcher e 8 feed), sem ordens de correção ou decisões necessárias. Não reproduziu banco, medições SQL, suites transversais ou entrega real. A publicação de código não constitui homologação nem aprovação produtiva; o resultado independente continua INCONCLUSIVE e deve acompanhar esta entrega. As medições SQL e os 127 testes completos são evidência do executor, sem atribuir-lhes revisão independente.
