# GLPI #1353 — Auditoria de Consumo — Deploy & Runtime Acceptance (2026-10-30)

> Página "Auditoria de consumo" (Portal Suprimentos) — deploy em produção em `srv-api`
> pelo fluxo oficial `up-prod-sequential.sh`, smoke autenticado real via gateway público.

## 1. Baseline e commits

| Item | Valor |
|---|---|
| Branch | `main` |
| `origin/main` | `891aa0483c` |
| api-delpi | `33eaa137d4` — producer read-only consumption-audit |
| supplies-api | `e15c0f8dfd` — BFF route (S2S + unit scope + error mapping) |
| infra | `54880eb6e9` — escopo `consumption-audit.read` + `--apply` no script canônico |
| MFE | `a6a2838257` — página Auditoria de Consumo (manifest v0.4.2) |
| doc contrato | `891aa0483c` — A2 contract freeze proposal |

## 2. S2S produção (sem segredos)

- Script canônico `infra/scripts/keycloak_s2s_supplies_scope.py --check`: drift
  `consumption-audit.read` ausente → `--apply` executado → scope criado e atribuído
  como default ao client `supplies-api`; audience mapper `api-delpi` presente.
- `S2S_AUDIENCE=api-delpi`; `S2S_ALLOWED_CLIENTS=supplies-api,controllership-finance-api,engineering-api`.
- `S2S_TOKEN_URL` prod: backchannel `keycloak:8080` — correto porque `KC_HOSTNAME`
  fixo (`start`, não `start-dev`) torna o `iss` estático `https://minhadelpi.com.br/auth/realms/delpi`.
- Secret re-persistida em `infra/.env` pelo script (valor nunca exibido).

## 3. Deploy sequencial (srv-api)

| Serviço | Fase | Imagem digest | Status |
|---|---|---|---|
| `delpi-api-delpi` | core | `infra-api-delpi@sha256:9e2e626660ac` | healthy |
| `delpi-supplies-api` | api | `infra-supplies-api@sha256:19da29fa3068` | healthy |
| `delpi-supplies` | mfe | `infra-supplies@sha256:b616d840f3c4` | up |

⚠ Efeito colateral conhecido: o checkout `891aa0483c` inclui o revert
`348a936706` (autor: PO) — o rebuild de `api-delpi` também removeu os artefatos
`financeiro_stock_kardex` (R06/R07 CF) do producer. Decisão registrada em `main`
pelo próprio Product Owner; CF MFE não foi rebuildado neste deploy.

## 4. Verificações pós-deploy (gateway público)

| Check | Resultado |
|---|---|
| `GET /apps/api-delpi/health` | 200 |
| `GET /apps/supplies-api/health` | 200 |
| Rota producer no OpenAPI prod | `/supplies/consumption-audit/orders/{production_order}` presente |
| `remoteEntry.js` supplies | 200; bundle `App-ugw3ZZiN.js` com marcadores `consumption-audit` + "Auditoria de consumo" |
| Página `/apps/supplies/consumption-audit` | 200 |
| BFF sem token | **401** (fail-closed) |

## 5. Smoke autenticado real (OP 24884201006, filial 01)

Identidade temporária `devin-smoke-1353` (Keycloak admin API) + role existente
"Portal Suprimentos - Acesso" (`supplies.access`) — criada só para o smoke e
**removida ao final** (KC delete 204 + Core `user_roles`/`users` delete 1/1).

| Chamada | HTTP |
|---|---|
| `GET /consumption-audit/orders/24884201006?unit=01` | **200** — envelope completo |
| `?unit=02` (filial irmã) | 404 (OP pertence à filial 01 — correto) |
| OP malformada `ABC` | 422 |
| `unit` ausente | 403 |
| OP inexistente `99999999999` | 404 |

Conteúdo real (snapshot 2026-10-29, dados dinâmicos do Protheus):

- Cabo `10010030` (op CT-23): teórico/empenho/derivado/elegível **80,75 MT**,
  `reconciled` via RE2 doc 220039841 — estrutura vigente na emissão da OP.
- Transferência **RE0 0,64 MT excluída** (`warehouse_transfer` /
  `not_raw_material_consumption`) — não entra no consumo.
- Mão de obra MOD216 0,233 HR → `unmatched` `labor_not_material` (fora da soma MP).
- CT-23 `execution_state=evidenced` (SH6 + HZA); CT-35 pendente/incompleto.
- `quality=partial` com 3 warnings honestos — sem afirmação de irregularidade.
- `related_orders`: 6 (siblings + parent via D4_OPORIG).

## 6. Gates

| Gate | Resultado |
|---|---|
| Producer unit/contract/security tests | 49/49 PASS |
| BFF tests | 12/12 PASS |
| MFE focused + full suite | 25/25 + 535/535 PASS; tsc + lint + vite build PASS |
| Integração e2e dev | PASS (rober + RBAC Core + S2S) |
| Integração e2e **prod** | **PASS** |
| Segurança | 401/403/404 fail-closed verificados em prod |
| Visual PO | pendente — validação estética do Product Owner em produção |

**Conclusão: `DEPLOYED / TECHNICAL_GATE_PASS / READY_FOR_PO_VISUAL_REVIEW`**

Rota do PO: `https://minhadelpi.com.br/apps/supplies/consumption-audit`
(visível a quem tem `supplies.access`; consulta persistida na URL para F5/share).
