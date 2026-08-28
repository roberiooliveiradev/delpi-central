# production-control-api

BFF do **Portal PCP**. Dono do catálogo de subplugins, da **gestão à vista**, da **carga máquina**, da composição de **análise de problemas** e das **solicitações em excesso** (Materiais). SQL TOTVS permanece na api-delpi.

**Recado para quem implementa:** o destino do módulo é o **Portal de Produção**, com o PCP como primeira área. Este BFF **não** vira umbrella de OEE, apontamento ou retrabalho — irmãos entram por `routes[].target`, não fundindo API. Detalhe: [docs/12-roadmap-e-evolucao/production-control/README.md](../docs/12-roadmap-e-evolucao/production-control/README.md) § Recado.

## Endpoints

| Método | Path | Auth |
|--------|------|------|
| GET | `/health` | público |
| GET | `/subplugins` | JWT + `production-control.access` |
| GET | `/overview?branch=01\|02` | JWT + acesso + filial |
| GET | `/demand?branch=01\|02&search=&status=&dueFrom=&dueTo=&sort=&direction=&page=&pageSize=&refresh=` | JWT + `demand.view` + filial |
| GET | `/machine-load?branch=01\|02&workCenter=&startDate=&endDate=` | JWT + `machine-load.view` + filial |
| GET | `/machine-load/locate?branch=01\|02&q=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/refresh?branch=01\|02&workCenter=&startDate=&endDate=` | JWT + `machine-load.view` + filial |
| PATCH | `/machine-load/sequence?branch=01\|02&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/prioritize?branch=01\|02&orderNumber=&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/optimize-delivery?branch=01\|02&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/withdraw?branch=01\|02&orderNumber=&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/restore?branch=01\|02&orderNumber=&workCenter=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/transfer?branch=01\|02&productionOrder=&operationCode=&targetWorkCenter=&workCenter=` | JWT + `machine-load.view` + filial |
| GET | `/problem-analysis?branch=01\|02` | JWT + análise + filial |
| GET | `/problem-analysis/{detectorId}?branch=01\|02&page=&pageSize=` | JWT + análise + filial |
| GET | `/reports?branch=01\|02` | JWT + `reports.view` + filial |
| GET | `/reports/stock-balances?branch=&search=&sort=&page=&pageSize=&refresh=` | JWT + `reports.view` + filial |
| GET | `/reports/stock-balances/email-schedule?branch=` | JWT + `reports.view` + filial (agenda pessoal Delpi Reports) |
| PUT | `/reports/stock-balances/email-schedule?branch=` | JWT + `reports.view` + filial (body: hour, minute, enabled) |
| GET | `/public/machine-load/{token}?branch=01\|02&workCenter=` | público (token do cockpit) |
| GET | `/public/machine-load/{token}/drawings/{paCode}/pdf?branch=01\|02` | público (PDF do PA na fila) |
| WS | `/public/machine-load/{token}/ws?branch=01\|02` | público (token do cockpit) |

Envelope `{ success, message, data }`.

`GET /overview` agrega OTD do mês corrente (`/production/otd` + `/otd/series`), volume diário de PAs (`/production/appointments/series` — só `qty_produced`, com `weekday_average` excluindo sáb/dom), o checklist **a faturar até hoje** (`billing_due_today`: pedidos com `data_entrega` ≤ hoje + recently-closed com `C6_DATFAT` = hoje; check amarelo = estoque FIFO, verde = faturado) e a fila de OPs atrasadas (`/production/pcp-orders/items?delayed_only=true`). A fila de atraso considera só produtos cujo código começa com `8` ou `9` (`delayedProductCodePrefixes` em `content/overview.json`).

`GET /machine-load` lê o snapshot congelado em `production_control.machine_load_snapshots` (seed automático na 1ª visita). `GET /machine-load/locate?q=` rastreia **conjunto** (`C2_NUM` = 6 primeiros dígitos de `production_order` / H8_OP) — todas as OPs com esse prefixo — ou lista os conjuntos de um **produto** (PA) em **todos** os CTs do mesmo snapshot (com posição na fila e enrich HZA), sem embutir a lista completa em cada GET de aba. `POST /machine-load/refresh` regenera a partir de `/production/machine-load/work-centers` + `/operations` (paginado) e **apaga** a ordem manual do período. `PATCH /machine-load/sequence` reordena só o segmento do `workCenter` no `payload_json` (`ordered_keys` = permutação exata das ops daquele CT), grava `sequence_updated_at` / `sequence_updated_by` e **não** altera `refreshed_at`. Em toda leitura, o status HZA é reaplicado via `/production/machine-load/appointment-status` — a fila SH8 não é remontada. Sem `workCenter`, usa o primeiro CT da lista; se o CT pedido não existir na janela, cai no primeiro e devolve `selected.requested_work_center` para a UI sinalizar.

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

`GET /public/machine-load/{token}/drawings/{paCode}/pdf` devolve o PDF do desenho **somente** se o código do PA aparecer na fila congelada da filial. O arquivo é lido do disco pelo próprio BFF (`DrawingPdfLibraryStorage` → `FileResponse`), sem passar pela api-delpi. O cockpit do operador abre esse PDF pelo botão **Ver desenho**.

A pasta do FILESERVER é montada read-only no container:

| Variável | Default | Papel |
|---|---|---|
| `PC_DRAWING_PDF_LIBRARY_DIR` | `/drawing-pdfs` | Caminho dentro do container |
| `PC_DRAWING_PDF_HOST_PATH` | dev `/mnt/x/DESENHOS DELPI EM PDF` · prod `/mnt/fileserver/desenhos` | Bind no host (`infra/docker-compose*.yml`) |

Convenção de nome resolvida pelo storage: `{codigo}.pdf` → `{base}.pdf` → `{base}_R{NN}.pdf` (maior revisão) → `{base}-{N}.pdf`. Pasta ausente ou vazia gera mensagem própria (`publicCockpit.messages` em `content/machine_load.json`), diferente de "desenho não encontrado".

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

`GET /delivery-map` lê o snapshot congelado em `production_control.delivery_map_snapshots` (seed automático na 1ª visita). A fonte TOTVS é `GET /production/pcp-orders/items` paginado (`mother_only`, `open_only`, produto PA prefixo `8`/`9`, saldo > 0). O BFF agrupa por data prevista: primeiro bloco **Hoje + atrasadas**, demais por dia. Observações vêm de `observation` (view / `C2_OBS`). **MP-OK** e **Feedback** (`work_center` no payload) são overrides manuais no `payload_json`, preservados no `POST /delivery-map/refresh`. `PATCH /delivery-map/overrides` atualiza marcações sem alterar `refreshed_at`. `GET /delivery-map/progress?branch=&orders=` devolve progresso **vivo** por conjunto (operações SH8 + enrich HZA), independente do snapshot da lista. Permissão: `production-control.delivery-map.view` + filial. Textos em `content/delivery_map.json`.

## Análise de problemas — detectores

A área é uma **grade de cards**, um por detector. `GET /problem-analysis` devolve `detectors[]` (`id`, `title`, `description`, `icon`, `severity`, `count`, `metrics`) e `GET /problem-analysis/{detectorId}` devolve os registros paginados daquele detector.

Título, descrição, ícone, ordem, severidade, tamanho de página e exclusões de negócio vivem em `content/problem_analysis.json`; o serviço só casa cada entrada do catálogo com a implementação registrada em `build_problem_detectors` — não há `if detector_id ==` em rota nem em serviço. Detector desconhecido responde **404**.

| Detector | Fonte api-delpi | Regra do BFF |
|---|---|---|
| `incomplete-order-sets` | `GET /production/production-order-sets/incomplete` | `critical` quando falta componente, `attention` quando só sobra; recorte de emissão (`issuedFromDays`, 730 por padrão) e exclusões por prefixo do raiz ou por código de componente |

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
