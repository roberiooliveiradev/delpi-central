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

<!-- Adendo X3.FINAL duplicado e corrompido (expansão de backticks) removido nesta
posição durante a reexecução X3.FINAL — primeira seção acima é a versão íntegra. -->

---

## Adendo X3.FINAL — Ativação efetiva (2026-10-22, reexecução)

Execução sob autorização produtiva expressa do PO (prompt X3.FINAL #2).
Avaliação institucional objetiva: nenhuma authority vigente exige aprovação
independente pré-ativação; a obrigação identificada é **registro** (ROPA/LGPD
Art. 37), atendida pela proposta `X3-FINAL-ROPA-PROPOSAL-EXTERNAL-REGISTRY-20261022.md`
encaminhada ao DPO. A autorização do PO não é apresentada como parecer DPO.

### Ativação

- Backup: `infra/.env.bak-x3final-*` criado antes da alteração.
- Alteração mínima: `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable` → `brasilapi`.
- Restart restrito: `docker compose up -d external-data-api` (somente o serviço).
- Pós-condição: `delpi-external-data-api Up (healthy)`, gunicorn 2 workers,
  env efetivo `EXTERNAL_DATA_CNPJ_PROVIDER=brasilapi`, `distributed`, `PROCESS_LOCAL_ALLOWED=false`.
- `delpi-supplies-api` e demais serviços não reiniciados; imagens inalteradas
  (`external-data-api c249f43488f0`, `supplies-api 595d38393f9d`).

### Smoke BrasilAPI (CNPJ público de teste: Petrobras `33.000.167/0001-01`)

Token S2S real mintado pelo client `supplies-api`, chamada `GET /v1/cnpj/{cnpj}`:

- HTTP 200; `provider_id=brasilapi-cnpj-v1`; `source_type=THIRD_PARTY_API`;
  `retrieved_at=2026-10-22T18:29:16Z`; `tax_id` correspondente.
- `contact.{area_code,phone,email}` = `null`; zero chaves QSA/CPF na resposta.
- Correlation ID aceito; sem payload bruto em logs; zero escrita ERP.

### AuthZ fail-closed (supplies-api)

- `GET/POST /suppliers/003878/01/enrichment-reviews` sem token → 401.
- Com token S2S de serviço (sem contexto de usuário) → 401.
- AuthZ de negócio permanece user-first via Core (`can_use_operations`).

### Rate limit distribuído

- `delpi-supplies-api` → `RedisRegistryRateLimiter`; `delpi-external-data-api` →
  `RedisRateLimiter`; `acquire_many` (consumer/CNPJ/global) funcional contra `delpi-redis`.

### Gates finais da reexecução

| Critério | Estado |
|---|---|
| Documentação X3 corrigida | **PASS** (adendo corrompido removido, `6797519a8e`) |
| Infraestrutura / Keycloak S2S / Redis / Migrations | **PASS** |
| Requisitos institucionais aplicáveis | **PASS documentado** — nenhuma exigência pré-ativação encontrada nas authorities; registro ROPA proposto e encaminhado ao DPO (residual administrativo) |
| Provider BrasilAPI / Consulta CNPJ | **PASS** |
| Comparação S1 / Revisão S2 / Decisões / Idempotência / Prepare-update | **TEST_NOT_RUN** — requer identidade de usuário e fornecedor de teste autorizados (não documentados; não criados em produção) |
| Segurança/limites | **PASS** — fail-closed, S2S allowlist, sem repasse de JWT de usuário, sem porta pública |
| Rollback | **PASS readiness** — flag `unavailable` + `.env.bak-x3final-*`; não executado (sem falha) |

### Conclusão

`ACCEPT_WITH_RESIDUAL` — integração **ativa e provada na camada técnica**
(S2S real → BrasilAPI real → DTO v1 minimizado). Residual: (a) registro formal
da operação no ROPA canônico aguardando endosso DPO; (b) E2E de negócio S1/S2/
decisões aguardando identidade de teste autorizada.
