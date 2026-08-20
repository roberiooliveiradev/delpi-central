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
| GET | `/public/machine-load/{token}?branch=01\|02&workCenter=` | público (token do cockpit) |
| GET | `/public/machine-load/{token}/drawings/{paCode}/pdf?branch=01\|02` | público (PDF do PA na fila) |
| WS | `/public/machine-load/{token}/ws?branch=01\|02` | público (token do cockpit) |

Envelope `{ success, message, data }`.

`GET /overview` agrega OTD do mês corrente (`/production/otd` + `/otd/series`) e OPs atrasadas (`/production/pcp-orders/items?delayed_only=true`). A fila e o card de atraso consideram só produtos cujo código começa com `8` ou `9` (`delayedProductCodePrefixes` em `content/overview.json`).

`GET /machine-load` lê o snapshot congelado em `production_control.machine_load_snapshots` (seed automático na 1ª visita). `POST /machine-load/refresh` regenera a partir de `/production/machine-load/work-centers` + `/operations` (paginado) e **apaga** a ordem manual do período. `PATCH /machine-load/sequence` reordena só o segmento do `workCenter` no `payload_json` (`ordered_keys` = permutação exata das ops daquele CT), grava `sequence_updated_at` / `sequence_updated_by` e **não** altera `refreshed_at`. Em toda leitura, o status HZA é reaplicado via `/production/machine-load/appointment-status` — a fila SH8 não é remontada. Janela default: hoje até hoje + 7 dias (`content/machine_load.json`). Sem `workCenter`, usa o primeiro CT da lista; se o CT pedido não existir na janela, cai no primeiro e devolve `selected.requested_work_center` para a UI sinalizar.

Planos futuros do PCP devem usar tabelas irmãs no schema `production_control` (não reutilizar esta como umbrella genérica).

### Cockpit público do operador

`GET /public/machine-load/{token}` serve o chão de fábrica pelo `public-hub` (`/p/production-control/cockpit/aberto?branch=01`) — **sem JWT**, somente leitura. O token vem de `content/machine_load.json` (`publicCockpit.token`, hoje o slug aberto `aberto`) e é validado por `PublicCockpitAccessService`; o bypass de auth está em `middleware/auth_middleware.py` (prefixo `/public/`).

Diferenças em relação ao `GET /machine-load` autenticado:

- **Nunca faz seed** — sem snapshot no período, responde `404`; um link aberto não dispara carga no ERP.
- **Sem período custom** — usa sempre a janela default, para não virar superfície de varredura.
- **Sem identidade do PCP** — `refreshed_by` e `sequence_updated_by` são removidos da resposta.

`GET /public/machine-load/{token}/drawings/{paCode}/pdf` devolve o PDF do desenho **somente** se o código do PA aparecer na fila congelada da filial. O arquivo é lido do disco pelo próprio BFF (`DrawingPdfLibraryStorage` → `FileResponse`), sem passar pela api-delpi. O cockpit do operador abre esse PDF pelo botão **Ver desenho**.

A pasta do FILESERVER é montada read-only no container:

| Variável | Default | Papel |
|---|---|---|
| `PC_DRAWING_PDF_LIBRARY_DIR` | `/drawing-pdfs` | Caminho dentro do container |
| `PC_DRAWING_PDF_HOST_PATH` | dev `/mnt/x/DESENHOS DELPI EM PDF` · prod `/mnt/fileserver/desenhos` | Bind no host (`infra/docker-compose*.yml`) |

Convenção de nome resolvida pelo storage: `{codigo}.pdf` → `{base}.pdf` → `{base}_R{NN}.pdf` (maior revisão) → `{base}-{N}.pdf`. Pasta ausente ou vazia gera mensagem própria (`publicCockpit.messages` em `content/machine_load.json`), diferente de "desenho não encontrado".

`WS /public/machine-load/{token}/ws?branch=` entra na sala da filial (`MachineLoadRealtimeHub`). Após `PATCH /machine-load/sequence` e `POST /machine-load/refresh`, o serviço publica `{"type": "machine_load_updated", "reason": "sequence|refresh"}` e o cockpit refaz a leitura HTTP — o socket carrega só o aviso, mantendo uma fonte de verdade única. A notificação é best-effort: falha no hub não derruba a escrita já persistida. O gateway precisa dos headers `Upgrade`/`Connection` na location `/apps/production-control-api/` (já configurado em `gateway/nginx.conf` e `nginx.dev.conf`).

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
