# Carga máquina — operações alocadas (`SH8010`)

Fila de operações já alocadas a centros de trabalho, com uma linha por operação de OP em aberto. Alimenta a aba **Carga máquina** do Portal PCP (via `production-control-api`) e o chat.

## Rotas

| Método | Path | operationId | Shape |
|--------|------|-------------|-------|
| GET | `/production/machine-load/work-centers` | `get_production_machine_load_work_centers` | `list` |
| GET | `/production/machine-load/operations` | `get_production_machine_load_operations` | `paged_list` |
| POST | `/production/machine-load/appointment-status` | `get_production_machine_load_appointment_status` | `list` |

Permissão: `KPI_PRODUCTION_ACCESS`.

## Fonte TOTVS

Sondado no ambiente Delpi (ago/2026) — ver `app/domain/production/machine_load_scope.py`.

| Tabela | Papel | Chave de junção |
|--------|-------|-----------------|
| `SH8010` | Alocação da operação (`H8_CTRAB`, `H8_FERRAM`, `H8_OPER`, `H8_DTINI`, `H8_HRINI`) | raiz |
| `SC2010` | OP (quantidades e roteiro) | `C2_FILIAL = H8_FILIAL`, `C2_OP = H8_OP` |
| `SB1010` | Descrição do produto | `B1_COD = C2_PRODUTO` |
| `SHB010` | Nome do centro de trabalho (`HB_NOME`) | `HB_FILIAL`, `HB_COD = H8_CTRAB` |
| `SG2010` | Descrição da operação (`G2_DESCRI`) | `G2_FILIAL`, `G2_PRODUTO = C2_PRODUTO`, `G2_CODIGO = C2_ROTEIRO`, `G2_OPERAC = H8_OPER` |
| `dbo.VW_PCP_ORDENS_PRODUCAO` | Entrega do PA | `OP_CHAVE = LEFT(H8_OP, 8) + '001'` |
| `HZA010` | Apontamento da operação (`HZA_DTINI`, `HZA_HRINI`, `HZA_OPERAD`, `HZA_STATUS`) | `HZA_FILIAL`, `HZA_OP = H8_OP`, `HZA_OPERAC = H8_OPER` |
| `SYS_USR` | Nome do operador (`USR_NOME`) | `USR_ID = HZA_OPERAD` |

Regras confirmadas na sonda:

- `H8_OP` já traz a chave completa de 11 posições, igual a `C2_OP` (número + item + sequência) — dispensa concatenar `C2_NUM + C2_ITEM + C2_SEQUEN`.
- **`H8_QUANT` não é a quantidade da ordem** (vem sempre `1`). A quantidade válida é `C2_QUANT`; o saldo é `C2_QUANT - C2_QUJE`.
- `H8_FERRAM` é a ferramenta real da alocação. O código `MOD` significa mão de obra — operação manual, sem ferramental (`is_manual_operation: true` no contrato).
- A entrega do PA vem da **OP mãe** (sequência `001` do mesmo par número + item), porque `DT_ENTREGA` da OP filha diverge da mãe na maioria dos casos.

Todas as junções usam `WITH (NOLOCK)` e `D_E_L_E_T_ = ''`. Cache `query_cache`, namespace `production-machine-load-v1`.

### Performance do apontamento

A resolução do nome do operador acontece **dentro** da subquery agregada da `HZA010`, não no `SELECT` externo. O predicado `LTRIM(RTRIM(USR_ID)) = LTRIM(RTRIM(HZA_OPERAD))` não é sargável; aplicado sobre a `SH8` inteira ele levava a consulta de ~2 s para mais de 60 s. Dentro do agregado, o join roda sobre as dezenas de apontamentos da janela. Nome, data, hora e código do operador voltam concatenados em `active_marker` (apontamento aberto) e `last_marker` (último do histórico, para status *Já apontada*), separados por `split_active_marker` no mapper.

## Status de produção (HZA010)

Constantes canônicas em `app/domain/totvs/protheus_operation_appointments.py`.

| `production_status` | Regra |
|---|---|
| `in_progress` | Apontamento com `HZA_STATUS = '1'` (em execução), `HZA_DTINI` preenchida e início dentro da janela de recência (`ACTIVE_APPOINTMENT_LOOKBACK_DAYS`) |
| `started` | A operação já teve apontamento no histórico, mas nenhum ativo agora |
| `not_started` | Sem apontamento na `HZA010` |

A janela de recência existe porque a base tem milhares de apontamentos abertos desde 2023 — `HZA_STATUS = '1'` sozinho marcaria como “rodando” operações esquecidas.

**Operações em produção sempre aparecem**, mesmo com `H8_DTINI` anterior à janela pedida: o filtro de data é aplicado com `OR` contra o predicado de apontamento ativo, porque quem está na máquina agora costuma ter sido programado ontem. A ordenação também sobe essas linhas para o topo da fila.

### Snapshot no Portal PCP

O congelamento da fila **não** fica na api-delpi. O `production-control-api` grava o sequenciamento em `production_control.machine_load_snapshots` — **uma fila viva por filial** — e só regenera via `POST /machine-load/refresh`, puxando por entrega do PA. Em cada leitura, o BFF chama:

`POST /production/machine-load/appointment-status`

para reaplicar o status HZA vivo sem remontar a SH8. Body: `{ "branch", "items": [{ "production_order", "operation_code" }] }`.

## Filtros (EN)

Comuns às duas rotas: `branch` (`01` \| `02`), `work_center`, `product_code`, `production_order`, `tool`, `open_only` (default `true` — mantém só `C2_QUANT > C2_QUJE`), mais **uma** das duas janelas abaixo.

| Janela | Parâmetros | Campo filtrado |
|---|---|---|
| **Entrega do PA** (preferida pelo PCP) | `delivery_start` / `delivery_end` | `due_date` = `COALESCE(PA.DT_ENTREGA, C2_DATPRF)` |
| Programação (legado) | `scheduled_start` / `scheduled_end` | `H8_DTINI` |

Quando `delivery_start` ou `delivery_end` chega, a janela de programação é **ignorada** — o PCP planeja por entrega, não por data de apontamento. `delivery_start` pode vir vazio para trazer também o atrasado; nesse caso só o teto é aplicado. Janela de programação: default 7 dias, máximo 90 (`DEFAULT_WINDOW_DAYS` / `MAX_WINDOW_DAYS`).

`operations` ainda aceita `page`, `page_size` (default 100, máximo 500) e `sort`: `schedule_asc` (default), `schedule_desc`, `due_date_asc`, `due_date_desc`, `op_asc`, `qty_desc`.

### Data de entrega efetiva

`due_date` nasce da OP mãe (`PA.DT_ENTREGA`) e cai para a previsão da própria OP (`C2_DATPRF`) quando o vínculo com a mãe não existe; `due_date_source` diz de onde veio (`mother_order` \| `order`). O agregado de centros devolve `missing_due_date_count` para o consumidor sinalizar OP sem nenhuma das duas datas — situação que **não deveria existir** no cadastro.

## Contrato

**Centro de trabalho:** `work_center`, `work_center_name`, `operation_count`, `order_count`, `in_production_count`, `first_scheduled_date`, `last_scheduled_date`, `first_due_date`, `last_due_date`, `missing_due_date_count`.

**Operação:** `branch`, `work_center`, `work_center_name`, `scheduled_date`, `scheduled_start_time`, `production_order`, `operation_code`, `operation_description`, `tool`, `is_manual_operation`, `product_code`, `product_description`, `unit`, `planned_qty`, `pending_qty`, `pa_due_date`, `pa_product_code`, `due_date`, `due_date_source`.

**Produção (derivado da `HZA010`):** `production_status`, `is_in_production`, `production_started_date`, `production_started_time`, `active_operator_code`, `active_operator_name`, `active_operator_count`, `appointment_count`, `last_appointment_date`.

Datas saem em ISO; horários em `HH:MM`.

## Relação com outras rotas

- `/production/pcp-orders/*` — catálogo de OPs por entrega prevista (não tem alocação por centro de trabalho).
- `/production/machine-programs` — programas de máquina cadastrados, não a fila alocada.
- Esta família — **sequenciamento**: o que cada centro de trabalho tem para fazer na janela.
