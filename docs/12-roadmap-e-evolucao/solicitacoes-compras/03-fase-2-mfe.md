# Fase 2 — MFE Solicitações de Compras (homologação 2.1.1)

> **Status:** FASE 2.1 PARCIALMENTE CONCLUÍDA (2026-08-26)  
> **Contrato:** [01-contrato-api.md](./01-contrato-api.md) · **Backend:** [02-fase-1-backend.md](./02-fase-1-backend.md)  
> **Escopo desta etapa:** homologar o MFE operacional (`plugins/purchase-requests`) — **sem** Fase 2.2 (filters, indicators, admin UI, KPIs).

---

## 1. Arquitetura

```text
Portal (host MF)
  └── remote purchase-requests → ./App (bootstrap mount/updateRoute/unmount)
        └── HTTP → /apps/purchase-requests-api/purchase-requests
              └── purchase-requests-api (BFF, escopo CC)
                    └── gateway → api-delpi /supplies/purchase-requests/lines
                          └── TOTVS SC1 / SC7 / SD1
```

- **MFE não chama api-delpi** — base canônica: `/apps/purchase-requests-api` (`purchaseRequestsApi.ts`).
- **Module Federation:** expõe `./App` → `src/bootstrap.tsx`; consome `@delpi/plugin-ui` como remote.
- **Autenticação:** JWT do Portal via `configureHttpClient`; header `X-Delpi-Caller-App: purchase-requests`.

---

## 2. Scaffold e stack

| Item | Valor |
|------|--------|
| Pacote | `plugins/purchase-requests` |
| React | 19 |
| Vite | 7 |
| TypeScript | strict (`tsconfig.app.json`) |
| MF plugin | `@originjs/vite-plugin-federation` + `federationReactProxyFix` |
| Referência | `controle-retrabalhos` (bootstrap), `travel-expenses` (drawer), `materiais-terceiros` (URL state) |
| Shim TS plugin-ui | `src/shims/plugin-ui.d.ts` (padrão `estoque-seguranca`) |

### Scripts (`package.json`)

| Script | Comando |
|--------|---------|
| `lint` | `eslint .` |
| `test` | `vitest run` |
| `typecheck` | `tsc -p tsconfig.app.json --noEmit` |
| `build` | `vite build` |
| `ci` | `lint && test && typecheck && build` |

---

## 3. Componentes e páginas

| Área | Arquivo / módulo |
|------|------------------|
| Bootstrap MF | `src/bootstrap.tsx` |
| Shell + RBAC | `src/App.tsx` |
| Página operacional | `src/pages/PurchaseRequestsPage.tsx` |
| Filtros | `src/components/PurchaseRequestsFilters.tsx` |
| Tabela | `src/components/PurchaseRequestsTable.tsx` |
| Drawer detalhe | `src/components/PurchaseRequestDetailDrawer.tsx` |
| Kit UI | `src/ui/purchaseRequestsUi.tsx` + `purchaseRequestsUiContracts.ts` |
| Hooks | `usePurchaseRequestsList`, `usePurchaseRequestDetail`, `usePurchaseRequestsRouterPath` |
| URL state | `src/utils/urlState.ts`, `queryParams.ts`, `pageState.ts` |
| Labels/status | `src/utils/labels.ts`, `formatters.ts` |
| RBAC filial | `src/security/purchaseRequestsAccess.ts` |

### Regras de apresentação (validadas em código + testes)

| Regra | Implementação |
|-------|----------------|
| `approval unknown` | **Não identificada** — nunca «Aguardando aprovação» |
| `residual_closed` | **Encerrada por resíduo** — nunca «Cancelada» |
| `buyer = null` | **Comprador não informado** — sem fallback para `order_user` |
| Timeline | Somente eventos do BFF (`detail.timeline`) |
| 404 detalhe | Mensagem neutra via `detailErrorMessage` |
| Paginação | Backend (`page`, `page_size`, `total`, `total_pages`) |

---

## 4. Filtros suportados (Fase 2.1)

Período (`date_from` / `date_to`), filial (`branch`), número SC, centro de custo, produto, fornecedor, pedido, status de aprovação.  
Estado refletido na query string (refresh F5 / `updateRoute`).

**Fora desta fase:** `/filters`, `/indicators`, `mine=true`, facets, setor formal, exportação.

---

## 5. API consumida (BFF)

| Método | Path MFE |
|--------|----------|
| GET | `/apps/purchase-requests-api/purchase-requests` |
| GET | `/apps/purchase-requests-api/purchase-requests/{branch}/{request_number}` |

Envelope: `{ success, data, message }` — ver contrato § Playbook 10.

---

## 6. Manifesto

Arquivo: `plugins/purchase-requests/purchase-requests.manifest.json`

| Campo | Valor |
|-------|--------|
| `id` | `purchase-requests` |
| `name` | Solicitações de Compras |
| `version` | `0.1.0` |
| `type` | `microfrontend` |
| `basePath` | `/apps/purchase-requests` |
| `entry` | `/apps/purchase-requests/assets/remoteEntry.js` |

Permissões declaradas:

- `purchase-requests.access`
- `purchase-requests.admin`
- `purchase-requests.view-all`
- `purchase-requests.export`
- `purchase-requests.unit.filial-01`
- `purchase-requests.unit.filial-02`

**Validação schema:** `ManifestValidator` (Core API) → `is_valid: True` (2026-08-26).

**Registro:** pendente — ver § Homologação abaixo.

---

## 7. Infraestrutura

| Item | Local |
|------|--------|
| Dockerfile MFE | `plugins/purchase-requests/Dockerfile` |
| Compose dev | `infra/docker-compose.dev.yml` → `purchase-requests`, `purchase-requests-api` |
| Compose prod | `infra/docker-compose.yml` → serviços distintos (sem conflito de nome) |
| Gateway BFF | `gateway/nginx*.conf` → `/apps/purchase-requests-api/` |
| Gateway assets MFE | location genérica `/apps/([^/]+)/assets/` → `delpi-$1` |
| Build sequencial | `./infra/scripts/up-dev-sequential.sh --fase mfe --build purchase-requests` |
| Registro manifesto | `plugins/purchase-requests/scripts/register-manifest.sh` |

### Correção Compose prod (homologação)

`purchase-requests` usava `<<: *plugin-ui-federated` sem âncora definida em `docker-compose.yml` → substituído por `depends_on: [plugin-ui]` (padrão `travel-expenses`). `docker compose config` dev + prod: **OK**.

---

## 8. Testes

| Suíte | Arquivo | Casos |
|-------|---------|-------|
| query params | `queryParams.test.ts` | filtros → query BFF |
| URL state | `urlState.test.ts` | parse/serialize |
| labels | `labels.test.ts` | status, buyer, pedidos múltiplos |
| page state | `pageState.test.ts` | paginação/empty/error |
| http client | `httpClient.test.ts` | auth header, erros |
| RBAC filial | `purchaseRequestsAccess.test.ts` | filial permitida |

**CI (2026-08-26):** 15/15 testes; lint 0 erros (7 warnings `set-state-in-effect` — padrão similar a outros plugins).

---

## 9. Build e Module Federation

### CI local (container Node 20)

```bash
cd plugins/purchase-requests && npm run ci
```

Resultado: **pass** (lint, test, typecheck, build).

### Docker

```bash
./infra/scripts/up-dev-sequential.sh --fase mfe --build purchase-requests
```

| Item | Evidência |
|------|-----------|
| Imagem | `infra-purchase-requests:latest` (~94 MB) |
| Container | `delpi-purchase-requests` — running, sem restart loop |
| Logs nginx | worker processes OK |
| Federation verify | `verify-federation-react-patch.mjs` OK |

### Gateway — remoteEntry e chunks

| Asset | HTTP | Content-Type |
|-------|------|--------------|
| `/apps/purchase-requests/assets/remoteEntry.js` | 200 | `application/javascript` |
| `__federation_expose_App-*.js` | 200 | `application/javascript` |
| `App-*.js` | 200 | `application/javascript` |
| `style-*.css` | 200 | `text/css` |

Exposição MF: `./App` → bootstrap com `preparePluginUiRemote()`.

Shared: `react`, `react-dom`, `@delpi/plugin-ui` (remote), `lucide-react`.

---

## 10. Homologação executada (2026-08-26)

### Concluído

1. CI completo (lint, typecheck, 15 testes, vite build).
2. Docker build + container `delpi-purchase-requests` healthy.
3. `remoteEntry.js` e chunks via Gateway `:9080`.
4. Manifesto válido contra schema Core API.
5. Compose dev/prod validado (`docker compose config`).
6. BFF health: `GET :9080/apps/purchase-requests-api/health` → 200.
7. BFF fail-closed: `GET /purchase-requests` sem JWT → 401.
8. Regras de status/buyer confirmadas em código e testes unitários.
9. Zero referências a `api-delpi` no MFE.

### Correções aplicadas na homologação

| Problema | Correção |
|----------|----------|
| Syntax error em `formatSuppliersSummary` | Template literal corrigido em `labels.ts` |
| ESLint `react-refresh/only-export-components` | Constantes extraídas para `purchaseRequestsUiContracts.ts` |
| Typecheck `StatusBadge` / `FilterInputField` | Props alinhadas ao shim plugin-ui |
| Typecheck `CompactPaginationLabels` | Shim atualizado com tipo canônico |
| Typecheck build plugin-ui source | `tsconfig` → shim, não source do remote |
| Compose prod âncora inválida | `depends_on: plugin-ui` em `docker-compose.yml` |
| `get-dev-token.sh` falha em WSL (:9080) | Fallback automático para `http://localhost:9080` |
| Tela em branco após carregar lista (`rows.length`) | `DataTable`: prop canônica `rows` (não `items`); shim TS corrigido |
| Query string do Portal ignorada no MFE | `App` repassa `search`; hook alinhado a `travel-expenses` |

## Homologação Portal — Fase 2.1.2 (2026-08-26)

### Manifesto (registro manual confirmado)

Consulta `delpi_core.apps` + `app_manifests` + `app_versions` — **sem novo registro**.

| Campo | Valor |
|-------|-------|
| `id` | `purchase-requests` |
| `version` | `0.1.0` |
| `basePath` / rota | `/apps/purchase-requests` |
| `type` | `microfrontend` |
| `entry` / `entryUrl` | `/apps/purchase-requests/assets/remoteEntry.js` |
| `active` | `true` |
| `renderMode` (manifest JSON) | `federated` |

### Permissões Core (provisionadas pelo registro manual)

Todas presentes em `permissions`:

- `purchase-requests.access`
- `purchase-requests.admin`
- `purchase-requests.view-all`
- `purchase-requests.export`
- `purchase-requests.unit.filial-01`
- `purchase-requests.unit.filial-02`

### RBAC e visibility scope

| Item | Resultado |
|------|-----------|
| Usuário homologação | `ti@delpi.com.br` (`is_superadmin=true`, UUID `7e406a83-b32d-4899-8f42-e81f29f80f4f`) |
| Permissões explícitas PR | Nenhuma role/usuário não-superadmin com `purchase-requests.*` atribuída ainda |
| Superadmin | `PermissionResolver` + `AppAuthorizationService` → acesso total; BFF trata como `view-all` |
| Visibility scope criado | **Sim** — `Homologação Portal — Filial 01 CC 0101` · filial `01` · CC real `0101` · usuário `ti@delpi.com.br` |
| Mecanismo | Repositório canônico (`VisibilityScopeRepository`) — equivalente ao `POST/PUT` admin do BFF; **sem** SQL ad hoc |

Escopo restrito simulado (usuário com `.access` + filial, CC `0101` only): **31 SC** vs **811** consolidado filial `01` (superadmin / sem filtro CC).

### `/me/apps`

Simulado in-container via `ListUserAppsUseCase` (`is_superadmin=true`):

- `purchase-requests` presente entre **34 apps**
- `basePath`: `/apps/purchase-requests`
- `entryUrl`: `/apps/purchase-requests/assets/remoteEntry.js`
- `type`: `microfrontend`

Chamada HTTP autenticada `GET /core-api/me/apps` **não executada** nesta sessão (sem JWT de browser — Direct Access Grants desabilitado; instrução de não usar `get-dev-token.sh`).

### Infraestrutura

| Serviço | Status |
|---------|--------|
| `delpi-purchase-requests` | Up |
| `delpi-purchase-requests-api` | Up (healthy) |
| `delpi-api-delpi` | Up (healthy) |
| `delpi-postgres-plugins` | Up (healthy) |
| `delpi-core-api` | Up |
| `delpi-gateway` | Up (`:9080`) |
| `delpi-portal` | Up |
| `remoteEntry.js` + chunks | HTTP 200 |

### Integração ponta a ponta (BFF → api-delpi → TOTVS)

Executado in-container (`ListPurchaseRequestsUseCase` / `GetPurchaseRequestUseCase` + service token interno para api-delpi):

| Verificação | Resultado |
|-------------|-----------|
| Listagem filial `01` | **811** SC (paginação 163 páginas × 5 itens/página no smoke) |
| Campos listagem | SC, solicitante, CC, datas, situação, pedidos/fornecedores quando existem |
| SC multi-item (`177034`) | **1 linha** na lista · `visible_items_count=4` |
| Detalhe (`177075`) | Resumo + 1 linha + timeline `Solicitação criada` (sem evento fictício de aprovação) |
| Fail closed (`.access` + filial, sem scope) | Lista vazia · gateway **não** chamado |
| Filial não autorizada (`02` sem permissão) | `PermissionError` |
| CC não autorizado (escopo restrito) | `PermissionError` |
| Detalhe inacessível | `LookupError` → UI: «Solicitação não encontrada ou indisponível.» |
| MFE → api-delpi direto | **Zero** referências no código MFE |

### Smoke Portal (browser)

**Não executado nesta sessão** — requer login OAuth no Portal (JWT de sessão). Pendente validação visual: montagem MF, filtros, drawer, F5, back/forward, console.

Correção prévia aplicada e rebuildada: tela branca (`DataTable` prop `rows` vs `items`).

### Testes automatizados

| Pacote | Resultado |
|--------|-----------|
| `purchase-requests-api` | **29 passed** (container) |
| `plugins/purchase-requests` | CI verde na sessão anterior (15 testes + build); host WSL sem `node`/`npm` nesta execução |

### Problemas encontrados nesta homologação

| Problema | Severidade | Ação |
|----------|------------|------|
| Tela branca (`rows` undefined no `DataTable`) | Crítico | **Corrigido** — rebuild MFE |
| Visibility scope ausente | Operacional | **Corrigido** — escopo CC `0101` criado |
| Smoke browser Portal | Homologação | **Pendente** — login manual |
| Roles não-superadmin sem `purchase-requests.*` | RBAC | Documentado — associar via admin Core quando houver usuário de teste dedicado |

---

## 11. RBAC e escopo de dados

| Camada | O que valida |
|--------|----------------|
| **RBAC Core** | Pode abrir o app? (`purchase-requests.access`, filial `.unit.filial-*`) |
| **Data scope BFF** | Quais CCs enxerga? (visibility scopes — fail closed) |

Usuário com `.access` mas **sem** visibility scope → lista vazia (comportamento esperado, não bug do MFE).

Admin de escopos: rotas `/purchase-requests/admin/*` no BFF (Fase 1) — **sem UI admin** nesta fase.

---

## 12. Pendências Fase 2.2 (não iniciar)

- `GET /purchase-requests/filters` e `/indicators`
- KPIs, gráficos, facets, `mine=true`
- Tela administrativa de escopos/mappings
- Exportação, SLA, `due_soon`, notificações

---

## 13. Referências

- [registrar-plugin-dev-local.md](../../10-guias-operacionais/registrar-plugin-dev-local.md)
- [mfe-own-api-no-direct-api-delpi.mdc](../../../.cursor/rules/mfe-own-api-no-direct-api-delpi.mdc)
- [plugins-reusable-components.mdc](../../../.cursor/rules/plugins-reusable-components.mdc)
