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
| GATE-F1 Privacy | **INCONCLUSIVE** | ROPA canônico (`docs/14-auditoria-lgpd/ropa-registro-tratamento.md`) existe e identifica o DPO (Michael Marotto), mas não registra operação de consulta cadastral externa de fornecedores; nenhum documento dispensa formalmente endosso. Proposta de registro elaborada para revisão do DPO em `X3-FINAL-ROPA-PROPOSAL-EXTERNAL-REGISTRY-20261022.md`. Provider permanece `unavailable`. |
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

---

## Adendo X3.E2E — Aceite real em produção (2026-10-22)

Usuário autorizado pelo PO: `rober` (sub `3bfdd634…`, ROPC via client
`delpi-central`, realm `delpi`). Senha transportada apenas por arquivo
temporário e removida; nenhum token impresso.

### Defeito real encontrado e corrigido — `EXECUTION_DRIFT` resolvido

- `DelpiCanonicalSupplierReader` exigia o wrapper `fornecedor` (contrato de
  **escrita**) sobre o `data` do `get_protheus_rest_supplier`; a resposta real
  é **flat**. Todo fornecedor retornava `None` → `404 supplier not found`.
- Correção: aceitar o dict flat quando `supplier_code`/`tax_id` presentes,
  preservando o wrapper legado — commit `2dbebb0ad1` (+5 testes de regressão,
  suíte supplies-api 432 verde).
- Observação: `docker exec` direto na `api-delpi` com o S2S no header errado
  retornava `Invalid token claims` — o contrato correto é
  `Authorization: Bearer <user>` + `X-Delpi-Service-Authorization: Bearer <s2s>`,
  exatamente o que a supplies-api envia (verificado: REST responde 200 para
  `00387801` e `00246901`).

### Rota "REST do Gabriel" — inventariada

`GET|POST|PUT /integrations/protheus/suppliers/{8d}` na api-delpi
(`protheus_router.py`): leitura canônica SA2 via Protheus REST; POST/PUT
são as rotas de escrita ERP existentes — **inventariadas e NÃO invocadas**
(`PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false`).

### Fluxo real executado (produção)

| Etapa | Resultado |
|---|---|
| Auth usuário `rober` | **200** — token Keycloak válido, identidade resolvida |
| Lista SA2 via supplies-api | **200** — 10 fornecedores PJ |
| Canonical read (flat) | **200** — fornecedor `002469/01`, CNPJ `5261…0139` |
| `POST enrichment-reviews` | **201** — review `d3b65302-ddb2-4747-a5ab-6ce2d54cf085`, `IN_REVIEW`, `source_id=brasilapi-cnpj-v1`, `source_reference` sanitizado, expiração 24h |
| S1 comparação (16 campos) | DIFFERENT: `supplier_name`, `postal_code`, `city_code`; MATCH: `district`, `state`, `city`; SOURCE_MISSING: `supplier_short_name`, `address`, `area_code`, `phone`, `email`; PROTECTED: `tax_id`; informativos: CURRENT_MISSING |
| Fornecedor homologação `003878/01` | `404 ENRICHMENT_REGISTRY_TAX_ID_NOT_FOUND` — CNPJ fake rejeitado corretamente pela BrasilAPI |
| Decisão individual (REJECT `tax_id`) | **200** |
| Replay idempotência (mesma key, nova revisão) | **409** — fail-closed correto (payload difere) |
| Probe revisão obsoleta | **422** (field_key inválida rejeitada antes do conflito) |
| Bulk REJECT (15 restantes) | **200**; replay → **409** fail-closed |
| `GET decisions` | **200** — 16 decisões |
| `POST prepare-update` | **200** — `write_gate_enabled=false`, `baseline_status=CURRENT`, draft vazio (todas rejeitadas — correto) |

### Persistência verificada (read-only, `plugins_hub.supplies`)

| Entidade | Resultado |
|---|---|
| `supplier_enrichment_reviews` | 1 — status `DECIDED`, revision 3, `source_id` correto, actor + expiração presentes |
| `supplier_enrichment_proposals` | 16 — todas decididas |
| `supplier_enrichment_decisions` | 16 |
| `supplier_enrichment_decision_operations` | 2 (single + bulk; replays não criaram ops) |
| `supplier_enrichment_events` | 18 (trilha de auditoria) |

### Segurança e limites

- AuthZ negativa: sem token → 401; S2S sem usuário → 401 (revalidado).
- Actor rate limiter real: **429 `ENRICHMENT_RATE_LIMITED`** observado na 10ª
  tentativa de criação de review — controle efetivo em produção.
- Zero escrita Protheus; flags de escrita desligadas; nenhum PUT/POST ERP invocado.
- Contatos: campos existem na matriz mas `SOURCE_MISSING`/`NOT_APPLICABLE` —
  minimização preservada (nenhum dado de contato retornado da fonte).

### Conclusão X3.E2E

`PASS` na camada de negócio completa: usuário real → lista SA2 → canonical read
→ BrasilAPI real → comparação S1 (16 campos) → revisão S2 persistida → decisões
individual/bulk com idempotência fail-closed → prepare-update draft-only.
Residuais: registro ROPA formal (DPO) e revisão da semântica de replay 409 vs
`idempotent_replay` quando a revisão muda — comportamento atual é fail-closed
correto, mas o contrato de replay pode ser refinado no X4.

---

## Adendo X3.E2E/REWORK — Correções de evidência e cobertura (2026-10-22)

Investigação das duas inconsistências residuais apontadas na revisão
arquitetural. Conclusão: **nenhum defeito de implementação** — divergência
documental e lacuna de cobertura de testes, ambas corrigidas.

### A — `person_type` (era: afirmação incorreta na evidência)

- **Fato real (verificado em produção, read-only):** `GET /integrations/
  protheus/suppliers/{id}` retorna `person_type: "J"` no envelope flat para
  `00246901` e `00387801`. A afirmação anterior de "campo ausente" estava
  **incorreta** — a chave constava inclusive na listagem de keys capturada.
- **Gate PJ comprovado fail-closed:** `create_review` rejeita
  `person_type != "J"` (`EnrichmentUnsupportedDocumentError`). O reader
  normaliza ausente → `""` → também rejeitado. Cobertura ampliada:
  `person_type ∈ {"F", "", " ", None}` → todos rejeitados, nada persistido.
- Causa raiz da divergência: relatório X3.E2E interpretou errado a matriz
  S1 — nenhuma alteração de contrato ou producer necessária.

### B — Idempotência (semântica confirmada, cobertura ampliada)

- `request_hash` inclui `expected_revision`: **replay idêntico** (mesma
  chave + mesmo payload completo) → `idempotent_replay=true`, sem novos
  registros; **payload divergente** (inclusive revisão diferente com a
  mesma chave — cenário do E2E) → `409 ENRICHMENT_IDEMPOTENCY_CONFLICT`.
  Os 409 observados no X3.E2E eram, portanto, a semântica correta do
  contrato — não replay idêntico.
- Cobertura preexistente confirmada: replay individual idêntico
  (`replayed=True`, zero decisões novas) e conflito por payload divergente.
- Cobertura adicionada: replay **bulk** idêntico (ordenamento de
  `field_keys` insensível — payload canônico ordenado), conflito bulk por
  payload divergente, e conflito de revisão obsoleta (`r-2` com
  `expected_revision` stale → `ReviewRevisionConflictError`).
- Produção confirma o contrato: `decision_operations` = 2 (single + bulk);
  os replays 409 não geraram operações/decisões/eventos duplicados.

### Resultado do rework

- **Código de aplicação: zero alterações** — implementação correta.
- **Testes:** +6 casos (suíte supplies-api 438 verde, 21 skip PG).
- **Impacto sobre a revisão produtiva:** nenhum — dados íntegros e
  consistentes com o contrato.
