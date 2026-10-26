# delpi-mes-api

BFF gerencial e stateless do **Delpi MES**: leitura operacional (monitoramento, timelines, paradas) e, desde a Etapa 2 de Cadastros, **administração do catálogo de motivos de parada** para usuários autorizados.

## Arquitetura e ownership

```text
plugins/delpi-mes (futuro)
        ↓ JWT de usuário
 delpi-mes-api
        ↓ service token + X-Delpi-Caller-App: delpi-mes-api
 production-control-api /integrations/mes/*
        ↓
 fatos MES
```

O `delpi-mes-api` não é o owner dos fatos MES. Runs, estados, paradas, contagens, motivos, timeline e auditoria permanecem no `production-control-api`. Este serviço não possui banco, migration, acesso SQL ou integração direta com Production Pulse.

## Endpoints

| Método | Endpoint | Permissão específica |
|---|---|---|
| GET | `/health` | público |
| GET | `/monitoring?branch=01` | `delpi-mes.monitoring.view` |
| GET | `/runs/{runId}/timeline` | `delpi-mes.history.view` |
| GET | `/runs/{runId}/performance` | `delpi-mes.monitoring.view` |
| GET | `/work-centers/{workCenter}/timeline?branch=&from=&to=` | `delpi-mes.history.view` |
| GET | `/downtimes?branch=&workCenter=&from=&to=&reasonCode=&source=&classification=&sort=&downtimeId=&page=&pageSize=` | `delpi-mes.downtimes.view` |
| GET | `/downtimes/filter-options?branch=` | `delpi-mes.downtimes.view` |
| GET | `/downtimes/analytics?branch=&from=&to=&workCenter=&reasonCode=&source=&classification=` | `delpi-mes.downtimes.view` |
| GET | `/registrations/downtime-reasons` | `delpi-mes.downtime-reasons.manage` |
| POST | `/registrations/downtime-reasons` | `delpi-mes.downtime-reasons.manage` |
| PUT | `/registrations/downtime-reasons/{code}` | `delpi-mes.downtime-reasons.manage` |
| PATCH | `/registrations/downtime-reasons/{code}/active` | `delpi-mes.downtime-reasons.manage` |

Toda rota gerencial também exige `delpi-mes.access` e principal humano; as rotas de leitura exigem ainda `delpi-mes.view.filial-01|02` para a filial consultada. As rotas `/registrations/downtime-reasons*` administram um **catálogo global** — não recebem nem exigem `branch`/permissão de filial. O provisionamento dessas permissões e o manifesto pertencem à Fase 2.

### Consulta gerencial de paradas (Paradas — Etapa 1)

`GET /downtimes` aceita os filtros `reasonCode`, `source`, `classification` (`pending|confirmed`), `sort` (`recent|oldest`) e `downtimeId`, além dos parâmetros originais — todos repassados ao contrato S2S do owner; `total` reflete o conjunto filtrado no backend, não a página. `downtimeId` continua escopado pela filial autorizada e serve à consulta pontual do detalhe/deep link — nunca revela ocorrência de outra filial. `classification=pending` corresponde a `confirmed IS NOT TRUE` no owner (parada sem confirmação válida, incluindo registros históricos incompletos); `classification=confirmed` exige `confirmed IS TRUE`.

### Análise gerencial de paradas (Paradas — Etapa 2)

`GET /downtimes/analytics` encaminha os mesmos filtros da listagem ao owner (`GET /integrations/mes/downtimes/analytics`) e projeta estritamente os campos do contrato gerencial (`summary`, `byReason`, `byWorkCenter`, `byDay`, `byWeekdayHour`, `quality`) — nenhum campo interno do Production Control vaza para o MFE. A agregação cobre **todos** os eventos elegíveis da janela (nunca a página atual), usa `referenceAt` único resolvido pelo owner para paradas abertas e honra a janela máxima e o teto de fatos do owner — `quality.partial`/`factsCapped` propagam a sinalização, e `quality.overlapDetected` informa quando `attributedSeconds` diverge do tempo deduplicado. `page`, `pageSize`, `sort` e `downtimeId` não são aceitos como determinantes de métrica. Mesma autorização da listagem: principal humano + `delpi-mes.access` + `delpi-mes.downtimes.view` + permissão da filial.

`GET /downtimes/filter-options?branch=` expõe projeção estritamente de leitura para a UI de filtros — motivos do catálogo (ativos **e** inativos, pois desativar um motivo não pode tornar suas ocorrências invisíveis) e origens válidas (`GET /integrations/mes/downtime-sources`, projeção do enum de domínio do owner). Exige principal humano + `delpi-mes.access` + `delpi-mes.downtimes.view` + permissão da filial — **não** exige a permissão administrativa `delpi-mes.downtime-reasons.manage`. Campos OEE e dados administrativos nunca são propagados.

### Performance do run (Fase 2.5)

`GET /runs/{runId}/performance` e o bloco `item.performance` de `GET /monitoring` transportam as métricas calculadas no owner dos fatos MES (`MesRunPerformanceService` via `/integrations/mes/runs/{runId}/performance` e `/work-centers/live`). O BFF não recalcula nada: autoriza (.access + .monitoring.view + permissão da filial do run retornado pelo upstream), aplica DTO explícito (`_PERFORMANCE_FIELDS`) e preserva `null`, `dataQuality` degradada e Performance acima de 100%.

### Administração do catálogo (Cadastros — Etapa 2)

As quatro rotas `/registrations/downtime-reasons*` encaminham para `/integrations/mes/downtime-reasons*` do `production-control-api` — a escrita, a unicidade de `code`, a proteção do motivo `setup`, o soft-delete e a validação industrial permanecem autoridade do owner. O BFF apenas autoriza o usuário (`.access` + `.downtime-reasons.manage`, principal humano — principal S2S é rejeitado mesmo como superadmin), aplica allowlist de DTO (os campos OEE `defaultPlanned`/`defaultCountsAsAvailabilityLoss` nunca atravessam o BFF) e preserva status funcionais: 404, 409 (incl. `setup` protegido e duplicidade) e 422 do upstream. Não existe DELETE.

## S2S outbound

`ProductionControlMesGateway` reutiliza um pool `httpx.Client` durante o lifespan, aplica `delpi_auth.service_token.apply_internal_service_headers`, identifica o chamador como `delpi-mes-api` e fecha o client no shutdown. Erros upstream são traduzidos sem expor URL interna, token ou stack trace.

## Variáveis

| Variável | Default | Uso |
|---|---|---|
| `DELPI_MES_API_ROOT_PATH` | `/apps/delpi-mes-api` | root path ASGI |
| `PRODUCTION_CONTROL_API_URL` | `http://production-control-api:8000` | owner dos fatos MES |
| `PRODUCTION_CONTROL_API_TIMEOUT` | `5` | timeout S2S em segundos |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | sem default | credencial S2S compartilhada |
| `DELPI_AUTH_CORE_API_URL` | Compose: `http://core-api:8000` | permissões efetivas via Core |
| `KEYCLOAK_JWKS_URL`, `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE`, `JWT_ALGORITHMS` | ambiente | validação JWT |

## Execução local

```bash
./infra/scripts/up-dev-sequential.sh --build production-control-api delpi-mes-api
curl http://localhost/apps/delpi-mes-api/health
```

## Testes

```bash
python -m pytest -q
```

## Fora de escopo

Plugin/MFE, manifesto, provisionamento RBAC, banco/read model próprio, cache, WebSocket, OEE, Performance, Qualidade, writes MES/TOTVS e alteração do ownership.
