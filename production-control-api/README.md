# production-control-api

BFF do **Portal PCP**. Dono do catálogo de subplugins, da **gestão à vista**, da **carga máquina** e da composição de **análise de problemas**. SQL TOTVS permanece na api-delpi.

## Endpoints

| Método | Path | Auth |
|--------|------|------|
| GET | `/health` | público |
| GET | `/subplugins` | JWT + `production-control.access` |
| GET | `/overview?branch=01\|02` | JWT + acesso + filial |
| GET | `/machine-load?branch=01\|02&workCenter=&startDate=&endDate=` | JWT + `machine-load.view` + filial |
| POST | `/machine-load/refresh?branch=01\|02&workCenter=&startDate=&endDate=` | JWT + `machine-load.view` + filial |
| PATCH | `/machine-load/sequence?branch=01\|02&workCenter=&startDate=&endDate=` | JWT + `machine-load.view` + filial |
| GET | `/problem-analysis?branch=01\|02&issueId=` | JWT + análise + filial |

Envelope `{ success, message, data }`.

`GET /overview` agrega OTD do mês corrente (`/production/otd` + `/otd/series`) e OPs atrasadas (`/production/pcp-orders/items?delayed_only=true`). A fila e o card de atraso consideram só produtos cujo código começa com `8` ou `9` (`delayedProductCodePrefixes` em `content/overview.json`).

`GET /machine-load` lê o snapshot congelado em `production_control.machine_load_snapshots` (seed automático na 1ª visita). `POST /machine-load/refresh` regenera a partir de `/production/machine-load/work-centers` + `/operations` (paginado) e **apaga** a ordem manual do período. `PATCH /machine-load/sequence` reordena só o segmento do `workCenter` no `payload_json` (`ordered_keys` = permutação exata das ops daquele CT), grava `sequence_updated_at` / `sequence_updated_by` e **não** altera `refreshed_at`. Em toda leitura, o status HZA é reaplicado via `/production/machine-load/appointment-status` — a fila SH8 não é remontada. Janela default: hoje até hoje + 7 dias (`content/machine_load.json`). Sem `workCenter`, usa o primeiro CT da lista; se o CT pedido não existir na janela, cai no primeiro e devolve `selected.requested_work_center` para a UI sinalizar.

Planos futuros do PCP devem usar tabelas irmãs no schema `production_control` (não reutilizar esta como umbrella genérica).

`GET /problem-analysis` devolve `summary` (critical/attention/ok), `issues[]` e `selected`. Fonte: `GET /production/pcp-orders/items?delayed_only=true` e `…/summary`.

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
