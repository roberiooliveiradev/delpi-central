# Plugin Pulso de Produção

Monitoramento IoT na fábrica: cadastro de dispositivos, leituras em tempo real, painel administrativo e modo operador (tablet).

## Fluxo

```text
Portal → plugins/production-pulse (MFE) → /apps/production-pulse-api → schema production_pulse (postgres-plugins)
                                                              └→ api-delpi (só CT / work-centers, via BFF)
```

O MFE **não** chama a api-delpi diretamente.

## Rotas UI

| Path | Descrição |
|------|-----------|
| `/apps/production-pulse` | Painel — KPI, filtros URL-sync, lista ou agrupado por posto/máquina/equipamento |
| `/apps/production-pulse/devices/new` | Cadastro de dispositivo + amarração |
| `/apps/production-pulse/devices/{id}/edit` | Edição |
| `/apps/production-pulse/devices/{id}` | Detalhe (overview, histórico, comandos) |
| `/apps/production-pulse/operator` | Hub operador — escolha de posto/máquina/equipamento |
| `/apps/production-pulse/operator/placements/{key}` | Picker quando há mais de um device no local |
| `/apps/production-pulse/operator/devices/{id}` | Superfície operador (`counter_pad` ou `gauge_readout`) |

Query params comuns: `branch`, `anchorType`, `status`, `role`, `search`, `view`, `groupBy`, `tab`.

## API

Base: `/apps/production-pulse-api` — ver [production-pulse-api/README.md](../../production-pulse-api/README.md).

Header recomendado nas chamadas autenticadas: `X-Delpi-Caller-App: production-pulse`.

## Permissões

| Código | Escopo |
|--------|--------|
| `production-pulse.access` | Abrir o plugin no portal |
| `production-pulse.devices.view` | Painel admin, detalhe, histórico, poll manual |
| `production-pulse.devices.manage` | CRUD, binding, test-probe, poll-all |
| `production-pulse.devices.command` | Comandos no painel administrativo |
| `production-pulse.operator` | Hub, picker e comandos na rota operador (sem exigir `view`) |
| `production-pulse.view.filial-01` | Dados filial SC |
| `production-pulse.view.filial-02` | Dados filial ES |
| `production-pulse.admin` | Todas as filiais |

Matriz MVP: [docs/12-roadmap-e-evolucao/production-pulse/ADR-003-rbac-mvp.md](../../docs/12-roadmap-e-evolucao/production-pulse/ADR-003-rbac-mvp.md).

## Dev

```bash
# Terminal 1 — remote plugin-ui
cd plugins/plugin-ui && npm run dev

# Terminal 2 — MFE
cd plugins/production-pulse
VITE_PLUGIN_UI_DEV=1 npm run dev
```

Stack via gateway (recomendado):

```bash
./infra/scripts/up-dev-sequential.sh --fase api --build production-pulse-api
./infra/scripts/up-dev-sequential.sh --fase mfe --build production-pulse
```

Migrations (se pendente):

```bash
docker exec delpi-production-pulse-api python -m production_pulse_app.infrastructure.persistence.migrations_runner up
```

## Testes / build

```bash
cd plugins/production-pulse && npm run test && npm run build
cd production-pulse-api && pytest tests -q
```

## Homologação HTTP

```bash
# Parcial ou completo — usa TOKEN ou API_DELPI_INTERNAL_SERVICE_TOKEN (infra/.env)
bash ./scripts/homologacao/check-production-pulse.sh

# JWT portal (opcional)
export TOKEN="<jwt sem Bearer>"
bash ./scripts/homologacao/check-production-pulse.sh

# E6.S2 — ESP piloto na LAN (requer 192.168.20.2 alcançável; dev: network_mode: host)
export PP_LIVE_ESP=1
export PP_LIVE_ESP_IP=192.168.20.2
bash ./scripts/homologacao/check-production-pulse.sh
```

Verify live ESP8266 piloto: [ROADMAP E6.S2](../../docs/12-roadmap-e-evolucao/production-pulse/ROADMAP.md).

## Contratos do kit (regressão)

`src/app/productionPulseKit.structural.test.ts` impede:

- `DataTable` cru sem `labels` — usar `PpDataTable`
- `FilterBarShell` / `pp-filters-wrap` — usar `PpFiltersRow` + `pp-filter-toolbar-row`
- `PpStateBox` com prop `actions` — canônico é `action`
- Hub operador com botão «Buscar» — usar `PpCatalogSearchBar` (busca automática)

Novos componentes devem consumir factories em `components/data/*Ui.tsx` ou `app/productionPulseUi.tsx`.

Registro do manifesto: `scripts/register-manifest.sh` (requer `TOKEN`).

## Documentação de produto

- [Roadmap](../../docs/12-roadmap-e-evolucao/production-pulse/ROADMAP.md)
- [Especificação](../../docs/12-roadmap-e-evolucao/production-pulse/ESPECIFICACAO-PLUGIN.md)
- [Wireframes](../../docs/12-roadmap-e-evolucao/production-pulse/WIREFRAMES.md)
