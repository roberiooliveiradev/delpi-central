# GLPI #1353 — Evolução F1–F6 — Aceite de Deploy e Runtime

Data: 2026-10-30 · Ambiente: **produção** (srv-api / minhadelpi.com.br)
Commits: `d79af34bd4` (api-delpi) · `1ed63b790b` (supplies-api) · `1f4f7d364c` (plugins/supplies)

## Escopo entregue

- **F1** `GET /supplies/consumption-audit/orders` (producer) + `GET /consumption-audit/orders` (BFF):
  busca paginada com filtros combináveis — fragmento de OP, produto/descrição, período por tipo de
  data (`emission` → C2_EMISSAO, `finished` → C2_DATRF, `appointment` → SH6.H6_DTAPONT via EXISTS),
  situação, centro de trabalho e operação (SH8). SELECT-only parametrizado, `ESCAPE '\'` em LIKE,
  paginação tier `page_25_50`, ordenação estável.
- **F2** MFE: remoção do botão Consultar — busca automática com debounce 350 ms, mínimo 2 caracteres,
  descarte de respostas antigas, listbox acessível (setas/Enter/Esc), seleção direta por filial+OP na URL.
- **F3** painel de filtros (tipo de data, período, produto, situação, CT, operação) + lista paginada
  + estados `loading|empty|partial|error|forbidden` + URL serializada (F5/compartilhamento).
- **F4** `GET .../comparison` (producer + BFF): batch 2–10 OPs mesma filial, reuso do use case de
  detalhe (sem recálculo duplicado), totais somente dentro da mesma UM; MFE multi-seleção + visão
  comparativa por operação/componente.
- **F5** UX: consulta compacta, operações recolhíveis, resumo escaneável, CSS escopado.
- **F6** Help/tooltips/manual sincronizados; manifest `supplies` 0.5.0.

## Runtime

| Serviço | Imagem | Estado |
|---|---|---|
| `delpi-api-delpi` | `infra-api-delpi@sha256:11b87a6837de` | healthy — 3 rotas consumption-audit no OpenAPI |
| `delpi-supplies-api` | `infra-supplies-api@sha256:8c87aefe1e66` | healthy — rotas BFF orders/comparison |
| `delpi-supplies` | `infra-supplies@sha256:3a3cee6a031b` | running — bundle `App-CXh8zhnO.js` contém `consumption-audit`/`consumptionAudit`/`Comparar` |

srv-api `HEAD = 1cfad4d87` (contém os 3 commits como ancestrais). Deploy via
`infra/scripts/up-prod-sequential.sh --build` na ordem api-delpi → supplies-api → supplies.

## Smoke autenticado em produção (APIs oficiais, zero escrita direta em banco)

Identidade temporária `devin-smoke-1353` provisionada e removida **exclusivamente por APIs
oficiais**: KC Admin API (create/password/delete) → password grant `delpi-central` → JIT
provisioning da linha `users` pelo `auth_middleware` do Core (`/me`) → bearer superadmin via
**impersonation + OIDC authorization-code** → `POST /admin/rbac/roles/{role}/users/{user}` →
cleanup `DELETE /admin/rbac/users/{id}` + KC `DELETE /users/{id}`.

### Positivos — PASS

- `GET /consumption-audit/orders?unit=01&search=248842` → 200 com itens (`production_order`,
  produto `90264300`/`90350419`, descrição, `emission_date`, `status`, `unit_of_measure`).
- `GET ...?period_start&period_end&date_type=emission&page=1&page_size=3` → 200 com itens.
- `GET /consumption-audit/orders/24884201006?unit=01` → 200 (detalhe preservado).
- `GET /consumption-audit/comparison?unit=01&orders=24884201006,24884201005` → 200; por OP:
  operações, componentes classificados (`reconciled`, `requires_investigation`), CT-23 `evidenced`,
  80,75 MT reconciliado — UMs não somadas entre materiais incompatíveis.

### Negativos — PASS (fail-closed)

- `unit=03` → 403 · `unit` ausente → 403 · `period_start=2026-13-99` → 422 ·
  comparison com 1 OP → 422 · sem token → 401.

## Testes executados

- api-delpi: `test_consumption_audit_search.py` **49 passed**; gate `audit_pagination_tiers.py
  --check-complete` OK (123 entradas, tier `page_25_50`).
- supplies-api: **656 passed** (rotas novas: validação, AuthZ, upstream malformado/502).
- plugins/supplies: `consumptionAudit.structural.test.ts` **20/20**; suíte do plugin **545 passed**;
  `tsc` limpo; `vite build` PASS.
- Suíte ampla api-delpi: 21 falhas **ambientais pré-existentes** (`/app` permission, git ausente no
  container) — fora do diff desta evolução.

## Contratos / segurança

- Detail existente preservado; `consumption-audit.read` (S2S `supplies-api` → `api-delpi`) cobre
  as 3 rotas — já provisionado no Keycloak prod via `keycloak_s2s_supplies_scope.py --apply`.
- Nenhuma permissão nova de usuário criada (`supplies.access` via role existente).
- Nenhuma escrita Protheus; MFE não recalcula regra de domínio.

## Pendências residuais

1. Validação estética do Product Owner em produção (gate visual dele).
2. Falhas ambientais pré-existentes da suíte api-delpi (não relacionadas).
3. `delpi-external-data-scheduler` unhealthy (preexistente, fora de escopo).
