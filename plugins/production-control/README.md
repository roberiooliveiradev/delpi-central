# Portal PCP (MFE)

Microfrontend federado da plataforma **Portal PCP** (`id`: `production-control`): shell estilo command-center com **gestão à vista** na home e subplugins (Carga máquina, Análise de problemas).

## Fluxo técnico

```text
Portal → production-control (remoteEntry.js)
      → /apps/production-control-api/*
      → api-delpi /production/otd, /production/otd/series, /production/pcp-orders/*,
                  /production/machine-load/*
      → @delpi/plugin-ui (Module Federation)
```

O MFE **não** chama `/apps/api-delpi`. Header: `X-Delpi-Caller-App: production-control`.

## Rotas UI

| Rota | Tela |
|------|------|
| `/apps/production-control?branch=` | Gestão à vista (OTD do mês, OPs atrasadas, fila) |
| `…/machine-load?branch=01\|02&ct=&startDate=&endDate=` | Carga máquina (abas por centro de trabalho) |
| `…/problem-analysis?branch=01\|02&issue=` | Análise de problemas (inbox + detalhe) |

Subplugins futuros (`capacity`) aparecem na rail com estado *Em breve*.

**Carga máquina:** uma aba por centro de trabalho (`UnderlineNav` `mode="tabs"`) com a fila de operações alocadas — situação, OP completa, produto da operação, quantidade (3 casas), ferramenta, operação, código do PA e entrega do PA. O deep link (`?ct=`, `?startDate=`, `?endDate=`) reabre a mesma aba e janela; trocar de filial ou de CT preserva o período.

**Em produção agora:** a coluna *Situação* mostra `production_status` vindo da API (apontamento `HZA010`). Operação rodando ganha linha verde, ponto pulsante, nome do operador e horário de início. Operação *Já apontada* exibe o último operador, tacha a linha e suaviza o contraste. A aba do centro de trabalho recebe o ponto só quando há OP em produção; o resumo do período mostra quantas estão na máquina. A UI é render-only — quem decide o status é a api-delpi, o MFE só mapeia `production_status` → rótulo e variante (`utils/machineLoadStatus.ts`).

**Fila congelada:** o sequenciamento SH8 fica salvo no BFF (`machine_load_snapshots`). A primeira visita da filial/período faz seed automático; depois disso, só o botão **Atualizar** (com confirmação) chama `POST /machine-load/refresh` e **substitui** a fila — inclusive qualquer ordem manual. O status HZA continua vivo a cada GET. Trocar de centro de trabalho não regenera a fila.

**Reordenar (DnD):** no CT ativo, arraste pela alça da linha para mudar a sequência. No drop, o MFE aplica a ordem na UI e chama `PATCH /machine-load/sequence` (só aquele CT). **Ctrl+Z** desfaz e **Ctrl+Shift+Z** refaz (pilha local + PATCH). A tabela não usa sort por coluna, para não conflitar com a ordem manual. A barra de período mostra `Sequência ajustada em…` quando houver `sequence_updated_at`.

**Cockpit do operador (link público):** o botão **Link do operador** na barra de período copia `…/p/production-control/cockpit/aberto?branch={filial}` — página aberta no `public-hub`, sem login. O operador escolhe o posto na primeira abertura (a escolha fica no navegador dele), acompanha a fila em tempo real via WebSocket, copia a OP e abre o **desenho do PA** quando o arquivo existe na pasta do FILESERVER montada no `production-control-api`. É **somente leitura**: o sequenciamento continua exclusivo do PCP. Ver [plugins/public-hub/README.md](../public-hub/README.md) § *Fila de produção*.

## API

Base: `/apps/production-control-api`

| Método | Path | Uso |
|--------|------|-----|
| GET | `/health` | Liveness |
| GET | `/subplugins` | Catálogo filtrado por permissão |
| GET | `/overview?branch=` | Gestão à vista (OTD + atrasos) |
| GET | `/machine-load?branch=&workCenter=&startDate=&endDate=` | Centros de trabalho + fila do CT ativo (snapshot) |
| POST | `/machine-load/refresh?branch=&workCenter=&startDate=&endDate=` | Regenera o snapshot a partir do TOTVS |
| PATCH | `/machine-load/sequence?branch=&workCenter=&startDate=&endDate=` | Persiste a ordem manual do CT (`ordered_keys`) |
| GET | `/problem-analysis?branch=&issueId=` | Inbox de exceções |
| GET | `/public/machine-load/{token}?branch=&workCenter=` | Cockpit do operador (público, somente leitura) |
| GET | `/public/machine-load/{token}/drawings/{paCode}/pdf?branch=` | PDF do desenho do PA lido da pasta do FILESERVER montada no BFF (público, PA precisa estar na fila) |
| WS | `/public/machine-load/{token}/ws?branch=` | Aviso de mudança da fila para o cockpit |

Contrato TOTVS (não duplicado aqui): [production-pcp-orders.md](../../api-delpi/docs/api/production-pcp-orders.md) e [production-machine-load.md](../../api-delpi/docs/api/production-machine-load.md).

## Permissões

`production-control.access`, `production-control.machine-load.view`, `production-control.problem-analysis.view`, `production-control.view.filial-01`, `production-control.view.filial-02`.

## Desenvolvimento

```bash
cd plugins/production-control
npm install
npm run test
npm run build
```

Dev federado: `VITE_PLUGIN_UI_DEV=1 npm run dev` com `plugin-ui` em `5010`.

CSS escopado em `.dashboard-production-control` — zero `.delpi-ui-*` no MFE.

## Docker

```bash
./infra/scripts/up-dev-sequential.sh --fase api --build production-control-api
./infra/scripts/up-dev-sequential.sh --fase mfe --build production-control
# Nova location Nginx: recriar só o gateway (bind mount; sem --build em lote)
# docker compose -f infra/docker-compose.dev.yml -f infra/docker-compose.minimal.yml --env-file infra/.env \
#   up -d --no-deps --force-recreate --no-build gateway
```

## Registro

```bash
TOKEN=<jwt-admin> ./scripts/register-manifest.sh
```

## Smoke

```bash
curl -sI http://localhost/apps/production-control/assets/remoteEntry.js | head -3
curl -s http://localhost/apps/production-control-api/health
```
