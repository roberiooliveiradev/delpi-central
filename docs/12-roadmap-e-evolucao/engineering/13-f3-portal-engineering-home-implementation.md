# F3 — Portal Engenharia MFE, Manifest Core, Integração Home

> **Fase:** F3-FINAL (escopo: MFE + Início; sem EVA/MCP).
> **Baseline:** `a7f4f32399` (F2a.R1). Execução no HEAD efetivo de
> `origin/main` após reancoragem.
> **Estado:** implementado + build evidenciado; registro Core e ativação
> funcional pendentes de autoridade operacional (ver §7).

## 1. Inventário G0 (factual)

| Pergunta | Resposta comprovada |
|---|---|
| Formato de manifest | `*.manifest.json` no plugin, `schemaVersion 1.0.0`: `id`, `name`, `description`, `icon`, `version`, `type: "microfrontend"`, `basePath`, `entry`, `permissions[]`, `routes[]`, `ui.renderMode: "federated"` (ex.: `plugins/my-requests/my-requests.manifest.json`) |
| Descoberta/registro | `POST /core-api/admin/apps/register` com JWT `apps.manage`; scripts `plugins/*/scripts/register-manifest.sh` por plugin. Update: `PUT /core-api/admin/apps/<id>/manifest`. Sem auto-sync em runtime |
| Permissões | Declaradas no `permissions[]` do manifest; grants são decisão separada da Core — registrar ≠ conceder |
| Rotas autorizadas | `routes[].permission` — o Portal resolve via `FederatedAppRouteGuard` + `ProtectedRoute` |
| Carregamento do MFE | Portal lê `entry` do app registrado → `federatedRemoteHost` carrega `remoteEntry.js` e chama `mount(el, props)` com `getAccessToken`, `pathname`, `permissions`, `isSuperadmin` |
| Lazy loading | `bootstrap.tsx` padrão: `preparePluginUiRemote()` + `await import("./App")` |
| Contexto do usuário | Props do host — sem consulta paralela |
| Cliente HTTP oficial | fetch same-origin + `Authorization: Bearer` via `getAccessToken()` + `X-Delpi-Caller-App` |
| 401/403/503 | Cliente tipado (`HomeApiError.kind`); estados honestos por seção vêm do backend |
| Gateway | Regras genéricas `/apps/([^/]+)/assets/*` → `delpi-$1` (prod e dev); página `/apps/<slug>` cai no `location /` → Portal SPA |
| Deploy | `infra/scripts/up-prod-sequential.sh --build <serviços>` após push em `main` |

## 2. S1 — Manifest e registro governado

`plugins/engineering/engineering.manifest.json`:

- `id: "engineering"`, `basePath: /apps/engineering`,
  `entry: /apps/engineering/assets/remoteEntry.js`,
  `type: "microfrontend"`, `ui.renderMode: "federated"`.
- **Uma** permissão: `engineering.access` (aprovada na F1 como alvo
  arquitetural; registrada via manifest, sem grants).
- **Uma** rota: `/apps/engineering` (Início), `showInMenu: true`.
- Coerente com `MANIFEST-DRAFT.md`: rotas futuras
  (`/my-tasks`, `/rooms`, `/tools/*`) **não** foram declaradas — o
  manifest declara somente o implementado.
- `scripts/register-manifest.sh`: cópia do padrão dos demais plugins —
  exige `TOKEN` com `apps.manage`.

**Status do registro:** `PENDING_OPERATOR_TOKEN` — o registro exige JWT
administrativo (`apps.manage`), que não faz parte da execução
autônoma. O script e o manifest estão prontos e validados contra o
schema observado. Nenhum grant foi criado.

## 3. S2 — MFE federado

`plugins/engineering/` segue a estrutura de `my-requests`:

- `vite.config.ts`: federation `name: "engineering"`,
  `filename: remoteEntry.js`, `exposes: { "./App": "./src/bootstrap.tsx" }`,
  remotes `pluginUiRemote()`, shared React canônico,
  `federationReactProxyFixPlugin()`, `base: /apps/engineering/`.
- `bootstrap.tsx`/`main.tsx`: padrão mount/unmount/updateRoute.
- `Dockerfile`: multi-stage node:20-alpine build → nginx:alpine;
  inclui `verify-federation-react-patch.mjs`.
- `src/shims/plugin-ui.d.ts`: shim tipado do kit (mesma convenção dos
  demais plugins) + declarações do kit `tasks` usado pela Home.
- Compose: serviço `engineering`/`delpi-engineering` em
  `infra/docker-compose.yml` (prod) e `infra/docker-compose.dev.yml`
  (âncora `*plugin-ui-federated`), `depends_on: plugin-ui`.
- Gateway: **zero alteração** — regras genéricas de assets já
  roteiam `delpi-engineering`; a página cai no Portal.

## 4. S3 — Página Início (`/apps/engineering`)

- `src/pages/HomePage.tsx`: `EngineeringPageHeader` (título, subtítulo,
  refresh) + grid de `EngineeringSectionCard` — seções de trabalho
  (`attention`, `tasks`, `requests`, `lmps`) e continuidade
  (`activity`, `collaboration`).
- Itens renderizados via kit `TaskItemsTable` +
  `TaskItemPresentation` (`route` = `href` oficial do backend;
  `canOpen` apenas quando `href` começa com `/apps/`).
- Estados honestos por seção (`buildSectionView`):
  `available` → tabela; `empty` → empty state; `unavailable` → banner
  com razão humana (timeout/transporte/upstream/contrato);
  `forbidden` → aviso de acesso negado (nunca erro de conexão);
  `not_implemented` → aviso de capacidade futura.
- `status === "partial"` → banner de degradação honesta.
- Loading inicial (`EngineeringLoadingState`), erro de página
  (banner), refresh com indicador; requisições obsoletas descartadas
  por sequência (sem estado de usuário anterior).
- Sem polling, sem cache compartilhado, sem dados simulados.

## 5. S4 — Integração engineering-api

- `src/api/httpClient.ts`: fetch same-origin, timeout 15s,
  `AbortSignal`, `X-Delpi-Caller-App: engineering`, Bearer via
  `getAccessToken` do host. Token nunca em storage/log/URL.
- `src/api/engineeringHomeApi.ts`: `GET /apps/engineering-api/v1/home`;
  valida envelope `{ success: true, data }` e presença das 6 seções →
  `contract_error` honesto em vez de render quebrado.
- Taxonomia de erro: `unauthorized(401)`, `forbidden(403)`,
  `rate_limited(429)`, `unavailable(5xx)`, `timeout`, `network_error`,
  `contract_error`.
- O MFE **não** chama api-delpi, requests-api, Core `/me` ou banco —
  somente o BFF.

## 6. S5 — Testes

15 testes (vitest, ambiente node — lógica pura, padrão do monorepo):

- `engineeringHomeApi.test.ts` (6): envelope válido; sem `success` →
  contract_error; seção ausente → contract_error; seção sem `status` →
  contract_error; mapa 401/403/429/503 → kinds corretos; headers
  Bearer + Caller-App, token nunca na URL.
- `homeViewModel.test.ts` (9): available→itens com `route`/`canOpen`;
  `href` fora de `/apps/` → não acionável; sem `href` → sem ação;
  empty legítimo; forbidden ≠ erro de conexão; unavailable com razão;
  not_implemented; banner partial; `sourceLabel` oficial/fallback.

Regressões de backend (F1/F2a/F2a.R1): sem mudança — evidência 160/160
em `a7f4f32399` permanece válida.

## 7. Ativação (gates Core RBAC)

| Etapa | Estado |
|---|---|
| Manifest criado + script oficial | PRONTO (arquivos no SHA) |
| Registro `POST /admin/apps/register` | `PENDING_OPERATOR_TOKEN` |
| `engineering.access` reconhecido pela Core | PENDING (após registro) |
| Grants | `PENDING_GRANT_APPROVAL` — nenhum grant criado |
| Smoke autenticado 200/403 | PENDING (após grant autorizado) |

Ativação funcional permanece bloqueada: sem registro e grant, o Portal
não lista o app e `/v1/home` responde 403 — comportamento correto e
fail-closed.

## 8. Build e evidências

- `npm install` (lockfile gerado), `lint` 0 problemas, `vitest` 15/15,
  `tsc --noEmit` limpo, `vite build` OK (remoteEntry + chunks
  federados), `verify-federation-react-patch` OK.
- `docker build` da imagem OK; container smoke:
  `GET /` → 200, `GET /assets/remoteEntry.js` → 200 com `./App` exposto.
- `docker compose config` válido (prod + dev).
- Audits CI: backend_boundaries 0, fastapi_authz 0, openapi_contracts 0,
  architecture_phase3 OK, platform_guardrails 0.

## 9. Residuais

- Registro Core + grants: pendência **administrativa** (token
  `apps.manage`), não dívida técnica.
- Smoke autenticado e verificação de grants efetivos: pendem da mesma
  autoridade.
- Acessibilidade: markup semântico do kit (`role=list/status/alert`,
  aria-busy/aria-label); validação visual/manual pendente do primeiro
  uso real.
- EVA/MCP/Sala: não iniciados (fora de escopo F3).

## 10. Próximo bounded step

Operador com `apps.manage` executa `register-manifest.sh` (prod) →
Core reconhece app + `engineering.access` → owner aprova grants →
smoke autenticado (403 sem permissão; 200 + seções autorizadas com
permissão) → ativação efetiva validada.
