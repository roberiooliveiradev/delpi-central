# production-control-api

BFF do **Portal PCP**. Dono do catálogo de subplugins, da **gestão à vista**, da **carga máquina**, da composição de **análise de problemas**, das **solicitações em excesso** (Materiais) e do **alimentador de linha**. SQL TOTVS permanece na api-delpi.

**Recado para quem implementa:** o destino do módulo é o **Portal de Produção**, com o PCP como primeira área. Este BFF **não** vira umbrella de OEE, apontamento ou retrabalho — irmãos entram por `routes[].target`, não fundindo API. Detalhe: [docs/12-roadmap-e-evolucao/production-control/README.md](../docs/12-roadmap-e-evolucao/production-control/README.md) § Recado.

## Endpoints

| Método | Path | Auth |
|--------|------|------|
| GET | `/health` | público |
| GET | `/subplugins` | JWT + `production-control.access` |
| GET | `/overview?branch=01\|02` | JWT + acesso + filial |
| GET | `/demand?branch=01\|02&search=&status=&dueFrom=&dueTo=&sort=&direction=&page=&pageSize=&refresh=` | JWT + `demand.view` + filial |
| GET | `/machine-load?branch=01\|02&workCenter=&startDate=&endDate=&includeAllCenters=` | JWT + `machine-load.view` + filial |
| GET | `/machine-load/live-status?branch=01\|02` | JWT + `machine-load.view` + filial |
| GET | `/machine-load/locate?branch=01\|02&q=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/refresh?branch=01\|02&workCenter=&startDate=&endDate=` | JWT + `machine-load.view` + filial |
| PATCH | `/machine-load/sequence?branch=01\|02&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/prioritize?branch=01\|02&orderNumber=&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/optimize-delivery?branch=01\|02&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/withdraw?branch=01\|02&orderNumber=&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/restore?branch=01\|02&orderNumber=&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/transfer?branch=01\|02&productionOrder=&operationCode=&targetWorkCenter=&workCenter=` | JWT + `machine-load.view` + filial |
| GET | `/line-feeder/requirements?branch=01\|02&cutoffDate=&cutoffTime=&workCenter=&status=&refresh=` | JWT + `line-feeder.view` + filial |
| POST | `/line-feeder/pick-plans` | JWT + `line-feeder.view` + filial (body: branch, cutoffDate, cutoffTime, workCenter) |
| GET | `/line-feeder/pick-plans?branch=01\|02&status=&limit=` | JWT + `line-feeder.view` + filial |
| GET | `/line-feeder/pick-plans/{planId}?branch=01\|02` | JWT + `line-feeder.view` + filial |
| PATCH | `/line-feeder/pick-plans/{planId}/items/{itemId}` | JWT + `line-feeder.view` + filial (body: branch, status) |
| POST | `/line-feeder/pick-plans/{planId}/close` | JWT + `line-feeder.view` + filial (body: branch) |
| GET | `/problem-analysis?branch=01\|02` | JWT + análise + filial |
| GET | `/problem-analysis/{detectorId}?branch=01\|02&page=&pageSize=` | JWT + análise + filial |
| GET | `/reports?branch=01\|02` | JWT + `reports.view` + filial |
| GET | `/reports/stock-balances?branch=&search=&sort=&page=&pageSize=&refresh=` | JWT + `reports.view` + filial |
| GET | `/reports/production-orders?branch=&opKey=&productCode=&openOnly=&motherOnly=&deliveryStart=&deliveryEnd=&actualEndStart=&actualEndEnd=&sort=&page=&pageSize=` | JWT + `reports.view` + filial |
| GET | `/reports/stock-balances/email-schedule?branch=` | JWT + `reports.view` + filial (agenda pessoal Delpi Reports) |
| PUT | `/reports/stock-balances/email-schedule?branch=` | JWT + `reports.view` + filial (body: hour, minute, enabled) |
| GET | `/public/machine-load/{token}?branch=01\|02&workCenter=` | público (token do cockpit) |
| GET | `/public/machine-load/{token}/drawings/{paCode}/pdf?branch=01\|02` | público (PDF do PA na fila) |
| GET | `/public/machine-load/{token}/models/{productCode}/glb?branch=01\|02` | público (GLB do produto da OP na fila) |
| POST | `/public/machine-load/{token}/bench-sessions` | público + honeypot (identifica operador) |
| DELETE | `/public/machine-load/{token}/bench-sessions/current` | público + header de sessão |
| POST | `/public/machine-load/{token}/runs` | play (sessão obrigatória) |
| POST | `/public/machine-load/{token}/runs/{id}/pause` | pause |
| POST | `/public/machine-load/{token}/runs/{id}/resume` | resume |
| POST | `/public/machine-load/{token}/runs/{id}/stop` | stop |
| GET | `/public/machine-load/{token}/runs/active?branch=&workCenter=` | run ativo + peças + device |

### Integração Production Pulse (MES shadow)

Contagem em tempo real no cockpit: este BFF **puxa** snapshot S2S do Pulse
(`GET /integrations/devices/.../snapshot`) via `PRODUCTION_PULSE_API_URL`.

| Ambiente | `PRODUCTION_PULSE_API_URL` típico |
|----------|-----------------------------------|
| Dev (pulse `network_mode: host`) | `http://host.docker.internal:80/apps/production-pulse-api` |
| Prod (mesma `delpi-network`) | `http://delpi-production-pulse-api:8000` |

Auth outbound: `API_DELPI_INTERNAL_SERVICE_TOKEN` + `X-Delpi-Caller-App: production-control-api`.
O Pulse **não** conhece OP/run; a fórmula de peças é âncora absoluta + `counterEpoch` (tabelas `production_runs` / `production_run_segments`).

Doc canônico: [MES-PULSE-COUNTING.md](../docs/12-roadmap-e-evolucao/production-control/MES-PULSE-COUNTING.md).
| GET | `/product-3d-models` | JWT + `product-3d-models.manage` |
| PUT | `/product-3d-models/{productCode}` | JWT + `product-3d-models.manage` (multipart `.glb`) |
| DELETE | `/product-3d-models/{productCode}` | JWT + `product-3d-models.manage` |
| GET | `/public/machine-load/{token}/performance?branch=01\|02&workCenter=&days=` | público (desempenho do posto na fila) |
| GET | `/public/machine-load/{token}/operations/appointments?branch=&productionOrder=&operationCode=` | público (histórico de apontamentos da OP+operação na fila) |
| GET | `/public/machine-load/{token}/operations/materials?branch=&productionOrder=&operationCode=` | público (materiais SD4 da OP+operação na fila) |
| GET | `/public/machine-load/{token}/operations/process-inspections?branch=&productionOrder=&operationCode=` | público (inspeções de processo da OP+operação na fila) |
| WS | `/public/machine-load/{token}/ws?branch=01\|02` | público (token do cockpit) |

Envelope `{ success, message, data }`.

`GET /reports/production-orders` pagina a view PCP (`/production/pcp-orders/items` + `/summary`) com padrão **em aberto** e **sem janela de 12 meses** (`unbounded_delivery`), para listar OPs cuja data de entrega ainda está no futuro. `openOnly` / `motherOnly` aceitam `yes|no|all`. `actualEndStart` / `actualEndEnd` (`C2_DATRF`) só entram quando `openOnly=no`.

`GET /overview` agrega OTD do mês corrente (`/production/otd` + `/otd/series`), volume diário de PAs (`/production/appointments/series` — só `qty_produced`, com `weekday_average` excluindo sáb/dom), o checklist **a faturar até hoje** (`billing_due_today`: pedidos com `data_entrega` ≤ hoje + recently-closed com `C6_DATFAT` = hoje; check amarelo = estoque FIFO, verde = faturado) e a fila de OPs atrasadas (`/production/pcp-orders/items?delayed_only=true`). A fila de atraso considera só produtos cujo código começa com `8` ou `9` (`delayedProductCodePrefixes` em `content/overview.json`).

`GET /machine-load` lê o snapshot congelado em `production_control.machine_load_snapshots` (seed automático na 1ª visita). `GET /machine-load/locate?q=` rastreia **conjunto** (`C2_NUM` = 6 primeiros dígitos de `production_order` / H8_OP) — todas as OPs com esse prefixo — ou lista os conjuntos de um **produto** (PA) em **todos** os CTs do mesmo snapshot (com posição na fila e enrich HZA), sem embutir a lista completa em cada GET de aba. `POST /machine-load/refresh` regenera a partir de `/production/machine-load/work-centers` + `/operations` (paginado) e **apaga** a ordem manual do período. `PATCH /machine-load/sequence` reordena só o segmento do `workCenter` no `payload_json` (`ordered_keys` = permutação exata das ops daquele CT), grava `sequence_updated_at` / `sequence_updated_by` e **não** altera `refreshed_at`. O status HZA é reaplicado sobre a fila a cada leitura, mas quem consulta o TOTVS é a rota dedicada (ver abaixo). Sem `workCenter`, usa o primeiro CT da lista; se o CT pedido não existir na janela, cai no primeiro e devolve `selected.requested_work_center` para a UI sinalizar.

#### Fila completa e status ao vivo em rotas separadas

O centro de trabalho é **recorte de apresentação**, não uma leitura diferente: `selected.items` é um filtro sobre a mesma fila da filial. Com `includeAllCenters=true`, o payload traz também `operations` com a fila visível inteira (todos os centros, já com a lente de período aplicada) — o MFE do PCP lê uma vez por filial + janela e troca de aba sem nenhuma requisição. São 1783 operações da filial 01 em ~64 KB com o `GZipMiddleware` já ativo. O parâmetro é **opt-in** em `GET /machine-load` e nas mutações (`refresh`, `sequence`, `prioritize`, `optimize-delivery`, `withdraw`, `restore`, `transfer`, `transfer-set`), para que a resposta continue enxuta para quem só precisa do centro ativo. O cockpit público **nunca** recebe a fila completa (`_strip_internal_identity` remove o bloco).

`GET /machine-load/live-status?branch=` é a única leitura do PCP que consulta o chão de fábrica: devolve `items` apenas com a chave da operação (`production_order` + `operation_code`) e os campos de apontamento que **divergem** da fila congelada (`production_status`, `is_in_production`, `active_operator_name`, `appointment_count`, entre outros), mais `summary` (`operation_count`, `in_production_count` da filial inteira) e `as_of`. Operação ausente significa «mantém o valor congelado do snapshot», mesma semântica de `_apply_status_map`. A resposta é **delta** porque o `appointment-status` da api-delpi responde por todas as chaves pedidas, inclusive as ~1780 sem novidade: na filial 01 isso é 5 KB em vez de 593 KB a cada 30 s. Sem snapshot na filial responde `404`.

Por isso `GET /machine-load` lê o status **só do cache** (`allow_remote_status=False`): a fila aparece na tela sem esperar o `POST appointment-status` com ~1800 chaves, que hoje custa ~9 s contra ~20 ms da leitura do snapshot em cache. Esse era o atraso sentido a cada clique de aba. O MFE chama `live-status` logo depois da fila e a cada 30 s, pausando com a aba oculta, e faz o merge por chave. `refresh` e as mutações mantêm a consulta síncrona (a decisão de «não ultrapassar operação já iniciada» depende do status vivo), e o `build_public` do cockpit também — com cache frio o operador não pode perder o status. O TTL curto de `machine_load_live_status_cache.py` (45 s) faz vários leitores no mesmo minuto compartilharem uma consulta.

Leitura do snapshot no Postgres: `xmin::text AS row_version` entra em `_COLUMNS` e o repositório pergunta **primeiro** a versão da tupla (~0,3 ms) para só rebuscar a linha quando o PCP realmente reescreveu a fila (~52 ms de `payload_json` já desserializado pelo psycopg). `xmin` muda em todo `UPDATE`, inclusive no `update_payload`, que não toca `refreshed_at` — por isso ele, e não o timestamp, é a chave de cache. As escritas atualizam o cache com a linha que acabaram de gravar, e o TTL de 5 min em `machine_load_snapshot_row_cache.py` é rede de segurança contra `VACUUM FREEZE`.

#### Janela por entrega do PA e uma fila viva por filial

O PCP planeja pela **entrega do PA**, não pela data de programação. `POST /machine-load/refresh` puxa por `delivery_start` / `delivery_end` da api-delpi: início **aberto** por padrão (para o atrasado continuar na fila) e fim em hoje + `defaultDeliveryWindowDays` (14, em `content/machine_load.json`). A data efetiva é `COALESCE(PA.DT_ENTREGA, C2_DATPRF)`, e `summary.missing_due_date_count` denuncia OP sem nenhuma das duas.

Existe **um** snapshot por filial (migration `V003`, unique em `branch`): a virada do dia não reseeda nem apaga ordem manual, retirada ou transferência — o carga máquina nem sempre roda todo dia, e produção do dia anterior pode não ter fechado. `start_date` / `end_date` viraram **dado** do registro (a janela realmente puxada), não chave.

No `GET /machine-load`, `startDate` / `endDate` são **lente de leitura** sobre essa fila congelada: filtram por entrega e escondem centros sem operação visível, sem tocar no TOTVS. O bloco `period` devolve `field: "delivery_date"`, `pulled_start` / `pulled_end` (o que foi puxado), `oldest_due_date` (sugestão do campo «De» na tela) e `filtered`. Para mudar o horizonte de verdade, o PCP usa **Atualizar**. As demais rotas (`sequence`, `prioritize`, `withdraw`, `restore`, `transfer`, `locate`) não recebem mais período: a fila é uma só.

`POST /machine-load/prioritize?orderNumber=` leva **todas** as OPs do conjunto (mesmo `C2_NUM`; aceita a OP completa e usa os 6 primeiros dígitos) ao topo da fila em **cada** centro onde elas aparecem. Operações já iniciadas — em produção agora ou com apontamento na HZA — não são ultrapassadas: mantêm a posição e o conjunto entra logo depois delas. A regra vive em `domain/services/machine_load_priority.py`; a escrita reaproveita o mesmo `payload_json` do sequenciamento manual (`sequence_updated_at` / `sequence_updated_by`) e avisa os cockpits (`reason: priority`). A resposta traz `prioritization` com `work_centers`, `operation_count`, `kept_ahead_count` e a mensagem exibida ao PCP.

`POST /machine-load/optimize-delivery` resequencia a fila de **todos** os centros da filial pela entrega do PA (`due_date`, com fallback `pa_due_date`), da mais próxima para a mais distante. Empate na mesma data preserva a ordem atual — o ajuste manual do PCP dentro do dia continua valendo; operação sem entrega vai para o fim do seu centro; conjunto retirado fica fora e mantém a posição original no payload. Operação já iniciada não é ultrapassada: a mecânica de travar posição é a mesma de `prioritize` e vive em `domain/services/machine_load_queue_slots.py`, com a ordenação em `domain/services/machine_load_delivery_sequencing.py`. Não chama o TOTVS nem mexe em `refreshed_at`; grava `sequence_updated_at` / `sequence_updated_by`, avisa os cockpits (`reason: delivery_sequence`) e responde com `optimization` (`work_centers` que mudaram, `moved_operation_count`, `kept_ahead_count`, `missing_due_date_count`, mensagem). Rodar duas vezes seguidas não muda nada na segunda.

`POST /machine-load/withdraw?orderNumber=` tira o conjunto da programação: as OPs somem da fila de **todos** os centros, do resumo, dos contadores de aba e do cockpit público (o PDF do desenho do PA vai junto). Elas **continuam** no `payload_json`, na posição original — a fonte de verdade é a lista `withdrawn_conjuntos` (regra em `domain/services/machine_load_withdrawal.py`), e a marca por operação é derivada na leitura. `POST /machine-load/restore?orderNumber=` remove a chave da lista e o conjunto reaparece exatamente onde estava. Ambas avisam os cockpits (`reason: withdrawal`) e respondem com `withdrawal` (ação, contagem, centros, mensagem) e o bloco `withdrawn` com os conjuntos ainda fora da programação.

Diferente da ordem manual, a retirada **sobrevive** ao `POST /machine-load/refresh`: `_pull_and_store` copia `withdrawn_conjuntos` do payload anterior. Sequenciamento (`PATCH /machine-load/sequence`) e priorização ignoram as operações retiradas — a permutação esperada é só das visíveis. O rastreio (`GET /machine-load/locate`) continua encontrando o conjunto, com `is_withdrawn` em cada parada para a UI marcar «Fora da programação».

`POST /machine-load/transfer?productionOrder=&operationCode=&targetWorkCenter=` move **uma** operação para o fim da fila do centro de destino (de lá o PCP reordena ou prioriza). A regra vive em `domain/services/machine_load_transfer.py`; a operação passa a carregar `transferred_from` (centro de origem no TOTVS) e o histórico fica em `transferred_operations` no `payload_json`. Rejeita destino inexistente no período, mesmo centro de origem, operação fora da fila e conjunto retirado da programação. Devolver a operação ao centro de origem apaga a marca e a entrada do histórico. Avisa os cockpits (`reason: transfer`, com o centro de destino) e responde com `transfer` (origem, destino, `returned_to_origin`, mensagem).

Como a retirada, a transferência **sobrevive** ao `POST /machine-load/refresh`: `_pull_and_store` reaplica `transferred_operations` sobre a fila nova do TOTVS (operação que sumiu do ERP é ignorada). Com retiradas ou transferências no período, os contadores por centro são recalculados a partir das operações realmente visíveis, e não do total que veio do TOTVS.

Planos futuros do PCP devem usar tabelas irmãs no schema `production_control` (não reutilizar esta como umbrella genérica).

### Cockpit público do operador

`GET /public/machine-load/{token}` serve o chão de fábrica pelo `public-hub` (`/p/production-control/cockpit/aberto?branch=01`) — **sem JWT**, somente leitura. O token vem de `content/machine_load.json` (`publicCockpit.token`, hoje o slug aberto `aberto`) e é validado por `PublicCockpitAccessService`; o bypass de auth está em `middleware/auth_middleware.py` (prefixo `/public/`).

Diferenças em relação ao `GET /machine-load` autenticado:

- **Nunca faz seed** — sem snapshot da filial, responde `404`; um link aberto não dispara carga no ERP.
- **Sem período custom** — mostra a fila congelada inteira, para não virar superfície de varredura.
- **Sem identidade do PCP** — `refreshed_by` e `sequence_updated_by` são removidos da resposta.
- **Sem a fila dos outros centros** — o bloco `operations` é removido; a tela mostra um centro por vez.
- **Status HZA síncrono** — o cockpit não faz polling, então o enrich continua no caminho da leitura.

`GET /public/machine-load/{token}/drawings/{paCode}/pdf` devolve o PDF do desenho **somente** se o código do PA aparecer na fila congelada da filial. O BFF consulta a **api-delpi** (`GET /products/{code}/drawing/pdf`) via `ApiDelpiDrawingLibraryClient` (JWT do usuário quando houver, senão token S2S interno) e reenvia `application/pdf` inline. O cockpit do operador abre esse PDF pelo botão **Ver desenho**. O FILESERVER fica montado **apenas** no container `api-delpi` (`DRAWING_PDF_*`).

| Variável | Default | Papel |
|---|---|---|
| `DELPI_API_URL` | `http://delpi-api-delpi:8000` | Base URL da api-delpi |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | (secret) | Auth S2S quando não há JWT de usuário (cockpit público) |

Fonte canônica e resolução de arquivo: ver `api-delpi/docs/api/14-desenhos-pdf.md`. Pasta ausente/indisponível na api-delpi vira **503** (`DrawingSourceUnavailable`); desenho ausente vira **404** (`DrawingNotFound`).

`GET /public/machine-load/{token}/models/{productCode}/glb` devolve o `.glb` anexado ao **produto da OP** (`product_code`, PI ou PA) **somente** se aquele código aparece como produto de alguma operação visível na fila publicada (`public_snapshot_contains_product` — não reutiliza o gate do PA). Bytes no volume `${DELPI_DATA_HOST_DIR}/product-3d-models`; metadado em `production_control.product_3d_models`. A fila pública marca `has_3d_model` por item. Anexação autenticada: `GET/PUT/DELETE /product-3d-models` com `production-control.product-3d-models.manage`.

#### Desempenho do posto

`GET /public/machine-load/{token}/performance?branch=&workCenter=&days=` alimenta os chips de eficiência/produção/paradas na barra do cockpit e o painel de gráficos. O cálculo continua na api-delpi (`/production/eficiencia-fabril/*` e `/production/unproductive-hours/*`, ambas com RBAC); aqui o `PublicWorkCenterPerformanceService` só compõe via `DelpiProductionGateway` (token S2S por `internal_service_authorization`) e recorta o que um link anônimo pode ver. No bloco `efficiency`, `shift_produced_qty` soma `qtd_apontada` de **todos** os apontamentos do turno atual (não só o recorte de 40 da tabela pública).

`GET /public/machine-load/{token}/operations/appointments?branch=&productionOrder=&operationCode=` alimenta o modal de apontamentos do detalhe: linhas com data, quantidade, posto e nome do operador (sem login/código/R$), só se a OP+operação estiver na fila publicada. Fonte: ``SH6010`` via `list_production_appointments` (inclui CT-00 — a view de eficiência fabril exclui CT-00 na SQL e **não** serve para saldo). Recorte estrito por **OP + operação** (`H6_OP` + `H6_OPERAC`). Escala MI alinhada à fila. Janela: últimos 120 dias.

`GET /public/machine-load/{token}/operations/materials?branch=&productionOrder=&operationCode=` alimenta o modal **Materiais da operação**: código, descrição, UM, quantidade original (`D4_QTDEORI`), saldo (`D4_QUANT`) e consumido, só se a OP+operação estiver na fila publicada. Fonte: ``SD4010`` via `list_production_order_operation_materials` — filtro obrigatório `D4_OP` + `D4_OPERAC` + filial; múltiplos empenhos do mesmo componente são agregados; **sem** fallback SG1. Lista vazia = operação sem vínculo de material.

`GET /public/machine-load/{token}/operations/process-inspections?branch=&productionOrder=&operationCode=` alimenta o modal **Inspeções de processo**: quem inspecionou, data, hora e resultado (aprovado/reprovado/tolerância), só se a OP+operação estiver na fila publicada. Fonte: view `historico_tela` via `list_inspecoes_processo_operation_inspections` — agrega sessões da OP+operação **sem** linhas de ensaio.

Guardrails, no mesmo espírito do PDF do desenho:

- o `workCenter` precisa estar na fila publicada da filial — CT fora do snapshot responde `400`;
- `days` é clampado entre 7 e 30 (default 14), para o link aberto não escolher quanto histórico o TOTVS varre;
- a resposta traz o **nome** do operador do apontamento (como a fila já mostra `active_operator_name`), mas **sem** `operator_code`/`login` e **sem** qualquer valor em R$ (`total_cost`, `valor_mod_hora`, `resultado_mod`); também inclui `pa_product_code` (`produto_acabado`).

As paradas do BI são filtradas por `RECURSO` (`H8_RECURSO`), que **não** é o código do CT. A ponte é o próprio snapshot: `public_snapshot_work_center_resources` devolve os recursos das operações daquele centro e o serviço manda a lista separada por vírgula; centro sem recurso cadastrado cai no próprio código.

Resiliência: cache em memória de ~120 s por `branch+work_center+days` (padrão de `machine_load_live_status_cache.py`) e **degradação por bloco** — se as paradas falharem, `efficiency` ainda responde e vice-versa, cada um com `available: false` e mensagem. Nada disso derruba a fila: o cockpit renderiza `—` nos chips e segue mostrando as OPs.

Sem apontamento no turno, a eficiência volta `null`, não `0` — o posto parado não é um posto com 0% de eficiência.

`WS /public/machine-load/{token}/ws?branch=` entra na sala da filial (`MachineLoadRealtimeHub`). Após `PATCH /machine-load/sequence` e `POST /machine-load/refresh`, o serviço publica `{"type": "machine_load_updated", "reason": "sequence|refresh"}` e o cockpit refaz a leitura HTTP — o socket carrega só o aviso, mantendo uma fonte de verdade única. A notificação é best-effort: falha no hub não derruba a escrita já persistida. O gateway precisa dos headers `Upgrade`/`Connection` na location `/apps/production-control-api/` (já configurado em `gateway/nginx.conf` e `nginx.dev.conf`).

## Demanda — carteira a entregar

`GET /demand` responde o que a fábrica precisa cobrir: linhas de pedido de venda com saldo, já cruzadas com estoque e OPs abertas. Duas leituras TOTVS puras alimentam a área — `GET /pedidos-venda-abertos/totvs-open-orders` (linhas com saldo) e `GET /pedidos-venda-abertos/ops-abertas` (OPs por produto). Nenhuma regra de carteira comercial atravessa: **preço e valor não entram na resposta**, e a api-delpi não conhece o PCP. Linhas com `tipo_entidade = FORNECEDOR` (venda/remessa para fornecedor) são descartadas em `demand_entity_scope` — o PCP só vê demanda de **cliente**.

A cobertura é montada em `domain/services/demand_coverage_service.py`, por `(filial, produto)` e sempre na ordem de entrega — quem vence antes consome primeiro:

1. O saldo disponível em estoque é distribuído entre as linhas.
2. O que o estoque não cobriu é distribuído entre as OPs abertas, da que termina antes para a que termina depois.
3. O resto é demanda descoberta — o sinal que o PCP quer ver.

Daí sai o status da linha: `late` (entrega vencida), `at_risk` (sobrou saldo sem cobertura, ou a OP só termina depois da entrega), `covered_by_order` e `covered_by_stock`.

Como a api-delpi devolve o dump inteiro sem filtro nem paginação, o recorte (filial, busca, status, janela de entrega), a ordenação, a página, o `summary` e o `horizon` por semana de entrega ficam em `application/services/demand_service.py`, sobre um cache por filial com TTL de `cacheTtlSeconds` (`content/demand.json`, 120 s). Trocar de página ou de filtro não repete a consulta pesada; `refresh=true` ignora o cache.

## Materiais — excesso e falta de solicitações

`GET /materials?view=excess|shortage` analisa SC1 de **matéria-prima** (`B1_TIPO = MP`) contra o estoque de segurança. PA, PI e demais tipos não entram. A api-delpi entrega o dump TOTVS (`GET /supplies/purchase-requests/open-coverage`): `items` (SC1) e `products` (MP com SC1 ou ESTSEG), cada um com `product_coverage` (`available_stock` 01+98+99 + SC7 elegível − SD4 elegível + `safety_stock` do SBZ). A SC1 não entra na projeção (evita dupla conta com o pedido).

O BFF aplica, por produto:

1. `needed_from_sc1 = max(0, safety_stock − projected_balance)`
2. FIFO (data de necessidade, número, item): as SC1 mais antigas cobrem essa necessidade
3. `view=excess`: só a SC1 que sobrou **inteira**
4. `view=shortage`: produtos cuja SC1 aberta (ou a ausência dela) ainda não chega no ESTSEG

Os cards (`issues[]`) trazem título, descrição e `product_count` de `content/materials.json`. O terceiro card (`pa-shortage`) é consulta — sem `product_count` inventado. Busca, ordenação, página e cache por filial (120 s) ficam em `application/services/materials_service.py`. Sem preço. Sem escrita no TOTVS. Permissão: `production-control.materials.view` + filial. O grant no Keycloak é operação — código e manifesto já declaram a permissão.

`GET /materials/finished-product-shortages?branch=&product=&status=&refresh=` consulta a api-delpi (`GET /products/{code}/raw-material-set-shortages`) e devolve o estado de tela (`ok`, `not_found`, `not_finished_product`, `no_open_sets`), summary, conjuntos com semáforo e o extrato (`materials[].ledger`) para o modal. Cache 120 s por `branch+product`. A projeção **não** é refeita neste BFF.

### Mapa de entrega

`GET /delivery-map` lê o snapshot congelado em `production_control.delivery_map_snapshots` (seed automático na 1ª visita). A fonte TOTVS é `GET /production/pcp-orders/items` paginado (`mother_only`, `open_only`, produto PA prefixo `8`/`9`, saldo > 0). O BFF agrupa por data prevista: primeiro bloco **Hoje + atrasadas**, demais por dia. Observações vêm de `observation` (view / `C2_OBS`). **MP-OK** e **Feedback** (`work_center` no payload) são overrides manuais no `payload_json`, preservados no `POST /delivery-map/refresh`. `PATCH /delivery-map/overrides` atualiza marcações sem alterar `refreshed_at`. `GET /delivery-map/progress?branch=&orders=` devolve progresso **vivo por pacote** (`C2_NUM`+`C2_ITEM`, 8 dígitos): busca SH8 por prefixo da OP **incluindo intermediários (SEQUEN 002+) e OPs encerradas** (`include_closed`), em paralelo (`progressFetchMaxWorkers`) — sem enrich HZA extra por padrão (status já vem no GET). O MFE limita a consulta às **3 primeiras tabelas**. Permissão: `production-control.delivery-map.view` + filial. Textos em `content/delivery_map.json`.

## Alimentador de linha — necessidade por bancada e lista de coleta

`GET /line-feeder/requirements?cutoffDate=&cutoffTime=` responde o que precisa estar nas bancadas até um horário da fábrica. O serviço só **orquestra** donos que já existem: a fila congelada e «está na programação» vêm do snapshot da carga máquina (`MachineLoadSnapshotRepositoryPort` + `machine_load_withdrawal`), o empenho vem da api-delpi (`POST /production/orders/operation-materials/batch`) e o saldo por armazém vem de `GET /supplies/stock-balances/items` com `product_codes` (duas chamadas: ponto de uso e origem). Sem snapshot na filial responde **404** — a rota **nunca** faz seed nem puxa TOTVS por conta própria.

Elegibilidade e cálculo vivem em domain services puros:

| Módulo | Responsabilidade |
|---|---|
| `domain/services/line_feeder_schedule_cutoff.py` | corte por `scheduled_date` + `scheduled_start_time`; sem hora vale o dia inteiro, e operação sem horário entra pela data em vez de desaparecer (mesmo princípio de `machine_load_delivery_window.py`) |
| `domain/services/line_feeder_requirements.py` | agregação por bancada + produto, rateio do saldo e situação do item |
| `domain/services/machine_load_snapshot_payload.py` | decode único do `payload_json` do snapshot, consumido também pelo `MachineLoadService` |

Por bancada e **matéria-prima** (`product_type` MP no empenho; PI/PA ficam de fora), considerando só as operações visíveis dentro do corte:

- `required_qty` = soma de `open_qty` (`D4_QUANT`) dos empenhos das operações elegíveis — operação já apontada não é filtrada aqui porque o Protheus já baixou o empenho;
- `point_of_use_qty` = saldo no armazém de ponto de uso (`99`), negativo tratado como zero;
- `to_deliver_qty` = `max(required_qty − point_of_use_qty, 0)`;
- `source_available_qty` = saldo no armazém de origem (`01`);
- situação: `covered` (nada a entregar), `to_pick` (cabe no saldo da origem), `at_risk` (não cabe) e `unknown` quando o saldo não pôde ser lido.

O saldo é **por produto, não por bancada**: duas bancadas que disputam o mesmo material não podem contar o mesmo saldo como já disponível. O rateio é **FIFO pelo horário programado** da operação (mais cedo consome primeiro), e por isso o cálculo é sempre global no corte — `workCenter` e `status` são recorte de apresentação aplicado **depois** do rateio, com cache por `branch + cutoff` (`cacheTtlSeconds`). Armazéns, TTLs, tamanho do lote, teto de itens da lista e mensagens ficam em `content/line_feeder.json`.

O teto de `maxProductionOrdersPerBatch` (300) é **contrato por requisição da api-delpi**, não limite do corte: um corte normal da filial 01 tem ~550 OPs distintas, então o BFF **fatia** a lista em `commitmentBatchSize` (100) e mescla os empenhos — as fatias são disjuntas por OP, então o índice de (OP, operação) só recebe chaves novas. O guardrail passa a ser `maxCommitmentBatches` (30 lotes) e só aí `stock.truncated_orders` aparece, com aviso na tela. Sem o fatiamento a filial 01 mostraria 46 materiais no lugar de 166 — pouco mais de um quarto do que as bancadas precisam.

O empenho custa ~45 ms por OP e é linear, então 548 OPs em série passavam de 28 s. As fatias e os dois armazéns vão em **paralelo** com pool limitado (`fetchMaxWorkers`, 6), no mesmo padrão do progresso do mapa de entrega: medido na filial 01, 28 s → 11 s nos empenhos e ~15 s na leitura completa. Mais workers não ajudam (o gargalo passa a ser o ERP), e o cache de `cacheTtlSeconds` (120 s, como Demanda e Materiais) deixa trocar de bancada e de situação em tempo de tela — o recorte não repete a leitura.

Degradação por bloco, no mesmo espírito do cockpit público: o **empenho não degrada** (sem ele não há necessidade, então a falha propaga como `502`), mas o **saldo degrada** — a necessidade responde com `stock.available: false`, mensagem e itens em `unknown`, nunca como `covered`. `POST /line-feeder/pick-plans`, ao contrário, **recusa** gerar lista quando o saldo está indisponível: lista de coleta sem saldo medido mandaria buscar material que já está na bancada.

A lista de coleta congela o que falta entregar (migrations `V006` + `V007`: `line_feeder_pick_plans` + `line_feeder_pick_items`, com `UNIQUE (plan_id, product_code)`). Cada item é **um produto** — quantidades somadas entre bancadas, ordenado por `product_code`, com `pickup_location` fotografado de `SBZ010.BZ_MPLOCAL` na filial. A grade de necessidade traz `inventory_blocked` a partir de `SB2010` (armazém fonte, default `01`). Situação do item vai e volta (`pending` ↔ `picked` ↔ `delivered`) por `PATCH …/items/{itemId}`; lista fechada (`POST …/close`) recusa alteração de item. Falha ao ler os locais **não** impede gerar a lista (locais vazios). Id malformado é `422` (validação de UUID no serviço), não erro de banco.

**Nada é escrito no Protheus** — sem requisição, empenho ou transferência de armazém. A lista é controle operacional da plataforma.

Autorização: `production-control.line-feeder.view` + filial em **todas** as rotas, inclusive as de escrita da lista. O papel operacional é um só (quem enxerga o que falta na bancada é quem separa e entrega) — decisão registrada aqui para não ser lida como permissão de escrita esquecida.

## Análise de problemas — detectores

A área é uma **grade de cards**, um por detector. `GET /problem-analysis` devolve `detectors[]` (`id`, `title`, `description`, `icon`, `severity`, `count`, `metrics`) e `GET /problem-analysis/{detectorId}` devolve os registros paginados daquele detector.

Título, descrição, ícone, ordem, severidade, tamanho de página e exclusões de negócio vivem em `content/problem_analysis.json`; o serviço só casa cada entrada do catálogo com a implementação registrada em `build_problem_detectors` — não há `if detector_id ==` em rota nem em serviço. Detector desconhecido responde **404**.

| Detector | Fonte api-delpi | Regra do BFF |
|---|---|---|
| `incomplete-order-sets` | `GET /production/production-order-sets/incomplete` | `critical` quando falta componente, `attention` quando só sobra; recorte de emissão (`issuedFromDays`, 730 por padrão) e exclusões por prefixo do raiz ou por código de componente |
| `order-set-quantity-mismatches` | `GET /production/production-order-sets/quantity-mismatches` | `critical` quando quantidade abaixo do esperado, `attention` quando só acima; mesma janela de emissão e exclusões |
| `uncovered-demand-lines` | cobertura da aba Demanda (`DemandCoverageService`) | `critical` com saldo sem estoque/OP; `attention` quando a OP só termina depois da entrega |
| `shared-structure-intermediates` | `GET /production/shared-structure-intermediates` | `attention` quando PI/PA aparece em ≥2 PAs com apontamento nos últimos 365 dias |

O recorte de emissão existe porque a Delpi arrasta conjuntos abertos desde os anos 2000: sem ele o conjunto furado da semana fica soterrado. A api-delpi devolve o diff bruto (estrutura × OPs criadas) e nada da regra do consumidor.

A OP atrasada deixou de ser exceção desta área — continua na gestão à vista (`GET /overview`), agora com `map_delayed_order` em `domain/services/delayed_order_mapper.py`.

Gateway: `X-Delpi-Caller-App: production-control-api` + `API_DELPI_INTERNAL_SERVICE_TOKEN` para a api-delpi (RBAC do produto fica neste BFF).

## Testes

```bash
cd production-control-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
python -m pytest tests -q
```

## Migrations

Schema `production_control` no `postgres-plugins`. `PC_RUN_MIGRATIONS_ON_STARTUP=true` no Compose. Só `up` em produção — nunca `reset`.
