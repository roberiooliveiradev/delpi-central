# Production Pulse API

BFF dedicado ao plugin **Pulso de Produção** (IoT industrial). O MFE consome **apenas** esta API — nunca a api-delpi diretamente.

## Escopo MVP

- CRUD de dispositivos (`devices`) com filial + IP único por filial
- Registry declarativo de drivers (`device_drivers.json`) — `esp8266_counter_v1` + `esp8266_gauge_v1`
- Amarração flexível (`device_bindings`) por `anchor_type` (posto, máquina, equipamento, área, avulso)
- Leituras genéricas (`readings.metrics` JSONB) + poll manual e scheduler automático
- Comandos auditados (`device_commands`) capability-gated por driver
- Catálogo CT via gateway → api-delpi `GET /production/appointments/work-centers`
- Rotas operador (`/operator/*`) com RBAC `production-pulse.operator`
- Status online/offline com grace 2× `poll_interval` (min 60 s, max 600 s)

Dispositivo piloto dev: `http://192.168.20.2/` (ESP8266 contador).

## Rotas

Base via gateway: `/apps/production-pulse-api`

Envelope: `{ "success", "message", "data" }`.

### Público / health

| Método | Path | Auth |
|--------|------|------|
| GET | `/health` | não |

### Resumo painel

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/summary?branch=` | `devices.view` |

### Catálogo

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/catalog/drivers` | `devices.view` |
| GET | `/catalog/work-centers?branch=&search=` | `devices.view` + filial |

### Dispositivos

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/devices?branch=&status=&role=&anchorType=&search=` | `devices.view` |
| POST | `/devices` | `devices.manage` |
| GET | `/devices/{id}` | `devices.view` |
| PUT/PATCH | `/devices/{id}` | `devices.manage` |
| DELETE | `/devices/{id}` | `devices.manage` (soft: `enabled=false`) |
| GET/PUT/DELETE | `/devices/{id}/binding` | view / manage |
| GET | `/devices/{id}/bindings/history` | `devices.view` |
| POST | `/devices/test-probe` | `devices.manage` |
| POST | `/devices/{id}/test` | `devices.manage` |
| POST | `/devices/{id}/poll` | `devices.view` |
| POST | `/devices/poll-all?branch=` | `devices.manage` |
| GET | `/devices/{id}/live` | `devices.view` |
| GET | `/devices/{id}/readings?from=&to=&limit=` | `devices.view` |
| GET | `/devices/{id}/commands` | `devices.view` |
| POST | `/devices/{id}/commands/{key}` | `devices.command` |

### Operador

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/operator/placements?branch=&anchorType=&search=` | `operator` |
| GET | `/operator/placements/{key}/devices?branch=` | `operator` |
| GET | `/operator/devices/{id}` | `operator` |
| POST | `/operator/devices/{id}/commands/{key}` | `operator` |
| GET | `/operator/work-centers/{code}/devices` | **308** → `/operator/placements/wc:{branch}:{code}/devices` |

## Stack

FastAPI · Postgres (`schema production_pulse` em postgres-plugins) · `delpi_auth` · drivers HTTP LAN

## LAN / Docker dev

Em desenvolvimento o serviço usa **`network_mode: host`** para alcançar IPs industriais (ex.: `192.168.20.2`). Ver [ADR-002](../docs/12-roadmap-e-evolucao/production-pulse/ADR-002-poll-scheduler-and-lan.md).

Variáveis relevantes (`infra/env.production-pulse.example`):

| Env | Uso |
|-----|-----|
| `PP_POLL_SCHEDULER_ENABLED` | Liga scheduler em background |
| `PP_POLL_MAX_CONCURRENT` | Semáforo de polls simultâneos |
| `PP_DEVICE_ONLINE_GRACE_MIN_SECONDS` / `MAX` | Limites do grace online |
| `PRODUCTION_PULSE_RUN_MIGRATIONS_ON_STARTUP` | `up` automático no boot |

## Desenvolvimento

```bash
cd production-pulse-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../shared[fastapi]

# Postgres plugins (host ou container na 5433)
export PLUGINS_DB_HOST=127.0.0.1 PLUGINS_DB_PORT=5433
export PLUGINS_DB_NAME=... PLUGINS_DB_USER=... PLUGINS_DB_PASSWORD=...

python -m production_pulse_app.infrastructure.persistence.migrations_runner up
pytest tests -q
```

Teste live opcional (rede com ESP): `pytest tests/test_esp8266_counter_driver_live.py -q`.

## Homologação

```bash
# Automático — TOKEN ou API_DELPI_INTERNAL_SERVICE_TOKEN (infra/.env)
bash ./scripts/homologacao/check-production-pulse.sh

# Live ESP piloto (opcional)
PP_LIVE_ESP=1 PP_LIVE_ESP_IP=192.168.20.2 bash ./scripts/homologacao/check-production-pulse.sh

# Pytest live (mesma rede que o container/host com network_mode: host)
PP_LIVE_ESP=1 pytest tests/test_esp8266_counter_driver_live.py -q
```

Checklist UI completo: [HOMOLOGACAO-E6-S2.md](../docs/12-roadmap-e-evolucao/production-pulse/HOMOLOGACAO-E6-S2.md).

## Documentação

- [Roadmap](../docs/12-roadmap-e-evolucao/production-pulse/ROADMAP.md)
- [Schema](../docs/12-roadmap-e-evolucao/production-pulse/SCHEMA.md)
- [Drivers](../docs/12-roadmap-e-evolucao/production-pulse/DEVICE-DRIVERS.md)
- [Plugin MFE](../plugins/production-pulse/README.md)
