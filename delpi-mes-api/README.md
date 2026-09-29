# delpi-mes-api

BFF gerencial, stateless e somente leitura do **Delpi MES**.

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
| GET | `/work-centers/{workCenter}/timeline?branch=&from=&to=` | `delpi-mes.history.view` |
| GET | `/downtimes?branch=&workCenter=&from=&to=&page=&pageSize=` | `delpi-mes.downtimes.view` |

Toda rota gerencial também exige `delpi-mes.access`, principal humano e `delpi-mes.view.filial-01|02` para a filial consultada. O provisionamento dessas permissões e o manifesto pertencem à Fase 2.

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
