# SHARED-INTEGRATIONS-01 / X3 — Runtime Evidence (2026-10-22)

Deploy produtivo condicional executado em `srv-api` (`operador@192.168.1.237`),
checkout `/home/operador/projetos/delpi-central`, HEAD implantado `74289c8495`.

## Gates

| Gate | Estado | Evidência |
|---|---|---|
| GATE-I1 Redis DELPI | **PASS** | `delpi-redis` (redis:7-alpine, `delpi-network`, sem porta publicada, requirepass) healthy; PONG/auth/Lua INCR/TTL 30s verificados via redis-cli. `evolution-redis` intocado (outro produto). |
| GATE-I2 Keycloak S2S | **PASS** | Provisioner `keycloak_s2s_external_data_audience.py --apply` criou mapper `audience-external-data-api` no client `supplies-api`; token real: `azp=supplies-api`, `aud=['external-data-api','api-delpi','delpi-central','account']`, iss=`…/realms/delpi`. Client `controllership-finance-api` → **401**. |
| GATE-I3 LGPD/ROPA | **INCONCLUSIVE** | Endosso DPO/ROPA para consulta externa produtiva permanece residual documentado (decisão S3.1 §"LGPD institucional — deve ser comprovada"). `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable` mantido — zero consulta BrasilAPI em produção. |
| GATE-I4 Migrations | **PASS** | Backup `plugins-hub-supplies-pre-x3-*.sql` antes do deploy; `schema_migrations` = V001→**V001,V002,V003** após startup automático. |
| GATE-I5 Tests/Build | **PASS** | Suítes supplies-api (0 falhas) e external-data-api verdes; imagens `infra-external-data-api` (`c249f43488f0`) e `infra-supplies-api` (`595d38393f9d`) construídas no servidor via `up-prod-sequential.sh --build`. |
| GATE-I6 Readiness | **PASS** | Ordem executada: backup → env → Keycloak → delpi-redis → external-data-api → supplies-api. Nenhum serviço alheio reiniciado. |

## Runtime verificado

- `delpi-external-data-api` healthy (gunicorn 2 workers), `delpi-supplies-api` healthy, ambos `/health` → 200.
- S2S real: sem token → **401**; token inválido → **401**; token `supplies-api` → **503 `EXTERNAL_DATA_PROVIDER_UNAVAILABLE`** (autorização passou; provider off por GATE-I3); CNPJ inválido → **400 `EXTERNAL_DATA_INVALID_TAX_ID`**; client estranho → **401**.
- Redis distribuído: `supplies-api` resolve `RedisRegistryRateLimiter` (namespace `supplies:registry-rate-limit:*`); `external-data-api` resolve `RedisRateLimiter` (namespace `external-data:rate-limit:*`) — mesma instância `delpi-redis`, multiworker-safe.
- `api-delpi` S2S preservado: `aud` do token `supplies-api` mantém `api-delpi`.
- Config efetiva: `COMPANY_REGISTRY_PROVIDER=external-data-api`, `COMPANY_REGISTRY_RATE_LIMIT_STRATEGY=distributed`, `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable`, `EXTERNAL_DATA_RATE_LIMIT_STRATEGY=distributed`, `EXTERNAL_DATA_*_PROCESS_LOCAL_ALLOWED=false`.

## Smokes não executados

- Consulta real CNPJ → BrasilAPI: **bloqueada** por GATE-I3 (sem endosso institucional).
- Review/decisions E2E com usuário real: **TEST_NOT_RUN** — sem credencial de usuário de teste autorizada; sem mutation de fornecedor real.
- Nenhuma escrita Protheus ocorreu ou foi habilitada.

## Rollback

- Contenção imediata: `COMPANY_REGISTRY_PROVIDER=unavailable` em `infra/.env` + restart `supplies-api` (revisões preservadas).
- Imagem anterior `infra-supplies-api` anterior disponível no host; restaurar via checkout anterior + `--build supplies-api`.
- `.env` backup: `infra/.env.bak-x3-*` no servidor.
- DB: backup pré-deploy `plugins-hub-supplies-pre-x3-*.sql`; migrations V002/V003 não são revertidas destrutivamente.
- `delpi-redis` e o mapper Keycloak são aditivos — podem permanecer inertes.

## Residuais

- `GATE-I3` — DPO/ROPA pendente: ativar `EXTERNAL_DATA_CNPJ_PROVIDER=brasilapi` exige autorização institucional explícita.
- Smoke usuário real E2E pendente de credencial autorizada (X4 ou execução assistida).
- `DELPI_REDIS_PASSWORD`/`S2S_CLIENT_SECRET` presentes em `infra/.env` (server-side, não versionado).
