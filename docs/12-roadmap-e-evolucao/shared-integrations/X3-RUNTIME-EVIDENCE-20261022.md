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

---

## Adendo X3.FINAL (2026-10-22)

Revalidação sob autorização PO condicional (`X3-FINAL-PO-AUTHORIZATION-20261022.md`, commit `2672e54d74`).

### Re-inventário produtivo

- Production HEAD: `a6574eb3b1` (após fix do healthcheck; base do inventário: `a34fbdf62e`).
- `delpi-external-data-api`: healthy; env efetivo `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable`, `EXTERNAL_DATA_RATE_LIMIT_STRATEGY=distributed`.
- `delpi-supplies-api`: healthy; `COMPANY_REGISTRY_RATE_LIMIT_STRATEGY=distributed`.
- `delpi-core-api`, `infra-keycloak-1`, `delpi-keycloak-db`: íntegros.
- Migrations `supplies.schema_migrations`: V001, V002, V003 — íntegras.

### Defeito corrigido: healthcheck `delpi-redis`

- Sintoma: container `unhealthy` com `AUTH failed: WRONGPASS` no healthcheck, embora o Redis respondesse PONG com credencial correta.
- Causa raiz: `DELPI_REDIS_PASSWORD` usada na interpolação compose do `command`, mas ausente do env do processo — o `CMD-SHELL` do healthcheck autenticava com senha vazia.
- Correção: `environment: DELPI_REDIS_PASSWORD` explícito no serviço (`infra/docker-compose.yml`), commit `a6574eb3b1`.
- Pós-condição verificada: `delpi-redis` `Up (healthy)`, `PONG` autenticado, downstream `supplies-api`/`external-data-api` healthy.

### Resultado dos gates X3.FINAL

| Gate | Estado | Evidência |
|---|---|---|
| GATE-F1 Privacy | **INCONCLUSIVE** | ROPA canônico (`docs/13-auditoria-lgpd/ropa-registro-tratamento.md`) existe e identifica o DPO (Michael Marotto), mas não registra operação de consulta cadastral externa de fornecedores; nenhum documento dispensa formalmente endosso. Proposta de registro elaborada para revisão do DPO em `X3-FINAL-ROPA-PROPOSAL-EXTERNAL-REGISTRY-20261022.md`. Provider permanece `unavailable`. |
| GATE-F2 Test identity | **INCONCLUSIVE** | Nenhum usuário/fornecedor de teste autorizado documentado no repositório. |
| GATE-F3 Infra | **PASS** | Revalidado: Redis healthy (após fix), S2S/mapper preservados, config efetiva distributed, migrations íntegras. |
| GATE-F4 Tests | **STALE_EVIDENCE** | Sem diff de código de aplicação no X3.FINAL; suítes verdes de X1/X2 mantidas (fix foi compose/healthcheck). |
| GATE-F5 Rollback | **PASS** | Feature flag `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable` permanece a contenção; nenhuma migration nova; imagens anteriores no host. |
| Provider BrasilAPI | **NÃO ATIVADO** | STOP obrigatório — F1 não comprovado. |
| E2E | **TEST_NOT_RUN** | Bloqueado por F1+F2. |
| No-write | **PASS** | Zero escrita Protheus; `prepare-update` draft-only intacto. |

### Conclusão X3.FINAL

`INCONCLUSIVE` — bloqueio institucional (F1) e de identidade de teste (F2), não técnico.
Próximas ações objetivas: (1) DPO endossa/incorpora proposta ROPA ou emite parecer de dispensa; (2) PO indica usuário e fornecedor de teste autorizados; (3) então reexecutar X3.FINAL a partir da ativação controlada.

---

## Adendo X3.FINAL (2026-10-22)

Revalidação sob autorização PO condicional (, commit ).

### Re-inventário produtivo

- Production HEAD:  (após fix do healthcheck; base do inventário: ).
- : healthy; env efetivo , .
- : healthy; .
- , , : íntegros.
- Migrations : V001, V002, V003 — íntegras.

### Defeito corrigido: healthcheck 

- Sintoma: container  com  no healthcheck, embora o Redis respondesse PONG com credencial correta.
- Causa raiz:  usada na interpolação compose do , mas **ausente do env do processo** — o  do healthcheck autenticava com senha vazia.
- Correção:  explícito no serviço (), commit .
- Pós-condição verificada:  ,  autenticado, downstream / healthy.

### Resultado dos gates X3.FINAL

| Gate | Estado | Evidência |
|---|---|---|
| GATE-F1 Privacy | **INCONCLUSIVE** | ROPA canônico () existe e identifica o DPO (Michael Marotto), mas **não registra operação de consulta cadastral externa de fornecedores**; nenhum documento dispensa formalmente endosso. Proposta de registro elaborada para revisão do DPO em . Provider permanece . |
| GATE-F2 Test identity | **INCONCLUSIVE** | Nenhum usuário/fornecedor de teste autorizado documentado no repositório. |
| GATE-F3 Infra | **PASS** | Revalidado: Redis healthy (após fix), S2S/mapper preservados, config efetiva distributed, migrations íntegras. |
| GATE-F4 Tests | **STALE_EVIDENCE aceita** | Sem diff de código de aplicação no X3.FINAL; suítes verdes de X1/X2 mantidas (fix foi compose/healthcheck). |
| GATE-F5 Rollback | **PASS** | Feature flag  permanece a contenção; nenhuma migration nova; imagens anteriores no host. |
| Provider BrasilAPI | **NÃO ATIVADO** | STOP obrigatório — F1 não comprovado. |
| E2E | **TEST_NOT_RUN** | Bloqueado por F1+F2. |
| No-write | **PASS** | Zero escrita Protheus;  draft-only intacto. |

### Conclusão X3.FINAL

 — bloqueio institucional (F1) e de identidade de teste (F2), não técnico.
Próximas ações objetivas: (1) DPO endossa/incorpora proposta ROPA ou emite parecer de dispensa; (2) PO indica usuário e fornecedor de teste autorizados; (3) então reexecutar X3.FINAL a partir do §10 (ativação controlada).
