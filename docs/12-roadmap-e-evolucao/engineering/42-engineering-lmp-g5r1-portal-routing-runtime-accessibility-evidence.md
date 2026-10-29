# ENGINEERING.LMP.G5.R1 — Portal Routing & Runtime Accessibility Evidence

Data: 2026-10-29 · Ambiente: dev local WSL (gateway `http://localhost`)
Executor: Devin · Coordenação: EVA — Architecture / Coordination
Baseline: `BASE_HEAD = c253e052fbe55348f6f66deaf82aa74781fa924c` (= `origin/main`, branch `main`, G5 `76e547c` ancestral)

## 1. Problema reportado

Apesar da G5 (doc 41) ter migrado a experiência de acompanhamento de
LMPs para dentro do Portal Engenharia, o acesso visível ao usuário
continuava levando ao MFE legado `/apps/dashboard-lmps`. Missão:
identificar causa-raiz e corrigir a disponibilização efetiva de
`/apps/engineering/lmps`, sem criar segunda implementação, sem desativar
o legado e sem presumir a causa antecipadamente.

## 2. Authorities lidas

`AGENTS.md`; constituição global (`development-standards-index`,
`evidence-driven-execution`, `centralized-rules-first`,
`clean-code-architecture-guardrails`, `english-code-identifiers`);
`infra-sequential-container-startup`, `local-first-deploy`,
`platform-frontend-mfe-experience`, `platform-security-identity-authorization`,
`contract-evolution-backward-compatibility`, `feature-help-sync`,
`test-and-commit`, `root-cause-generalized-fix`,
`mf-federation-patch-safety`; docs Engenharia 15 (F3-R1 — registro do
manifest pendente), 32–41.

## 3. Inventário de roteamento (HEAD)

| Camada | Arquivo | Estado no HEAD |
|---|---|---|
| Rotas internas do MFE | `plugins/engineering/src/app/engineeringRoutes.ts` | `home`, `overview`, `help`, `lmps`; `navigateEngineeringView` usa `pushState`; `popstate` ouvido |
| Resolução | `plugins/engineering/src/app/engineeringRoutes.ts` `resolveEngineeringRoute` | reconhece `/lmps` e `/lmps/ov/{sale}` |
| Catálogo | `plugins/engineering/src/content/engineeringRouteCatalog.ts` | item `lmps` → `{ kind: "internal", view: "lmps" }`, `requiredPermission: engineering.access` |
| Abertura | `plugins/engineering/src/app/openCatalogRoute.ts` + `HomePage.tsx` `openRoute` | interno → `navigateEngineeringView`; externo → `navigateGovernedHref` |
| Feature | `plugins/engineering/src/features/lmps/LmpsFeature.tsx` | dashboard + detalhe OV no mesmo mount |
| Manifest | `plugins/engineering/engineering.manifest.json` | v0.2.0, basePath `/apps/engineering`, rota `/apps/engineering/lmps` (showInMenu false, `engineering.access`) |
| Host | `portal/src/ui/AppHost.tsx`, `appHostEntry.ts`, `App.tsx` | longest-prefix por `basePath`; propaga `pathname`/`search` no mount e em `updateRoute`; `ProtectedRoute` por permissão da rota principal; superadmin bypassa |
| Gateway | `delpi-gateway` `nginx -T` | `/apps/engineering-api/` → backend; `/apps/<x>/assets/remoteEntry.js` → `delpi-<x>` sem cache; demais `/apps/**` → Portal SPA (`location /` → `portal:5173`) |

## 4. Hipóteses verificadas

| Hipótese | Verificação | Resultado |
|---|---|---|
| Bundle antigo servido | asset servido contém `/apps/engineering/lmps`; `remoteEntry.js` referencia `__federation_expose_App-B9OfoW1u.js?v=14`, image `sha256:44ef1bdb…` | DESCARTADA — bundle servido é o build G5 |
| remoteEntry em cache | gateway envia `Cache-Control: no-store` + `proxy_no_cache 1` | DESCARTADA |
| Rota não resolvida pelo host | longest-prefix matching revisado + prova browser | DESCARTADA |
| Manifesto sem a rota | manifest HEAD declara `/apps/engineering/lmps` | manifest OK no repositório |
| Catálogo aponta p/ legado | fonte e bundle servido: `internal → lmps` | DESCARTADA |
| Favoritos/recentes com URL legada | recents/favorites guardam `routeId` canônico do catálogo, não URL | DESCARTADA |
| **Plugin não registrado na Core** | `SELECT … FROM apps` no Postgres Core | **CONFIRMADA — ver §5** |
| Redirect externo (`location.assign`) | nenhum `assign` para dashboard-lmps no fluxo; clique usa `pushState` | DESCARTADA |

## 5. Causa-raiz

**O plugin `engineering` nunca foi registrado no registro de apps da
Core.** Em dev, `apps` continha 13 linhas — sem `engineering` e sem
`dashboard-lmps`; `app_manifests` idem. Consequência: `/me/apps` não
devolve o Portal Engenharia para nenhum usuário, o host não tem base
path para montar o MFE, e o único acesso LMPs visível é a rota de menu
do app legado (no ambiente onde ele está registrado, ex.: produção).

A pendência é conhecida e documentada desde a F3 (doc 15, §11–12):
"Registro do manifest `0.2.0` na Core + grant de `engineering.access`:
`PENDING_OPERATOR_TOKEN` / `PENDING_GRANT_APPROVAL`". O registro é um
passo operacional administrativo (`POST /core-api/admin/apps/register`,
permissão `apps.manage`) — **não é defeito de código**: catálogo,
roteador interno, host, gateway e bundle já estavam corretos.

No ambiente do usuário, `/apps/dashboard-lmps` estava registrado e
`engineering` não — exatamente o sintoma "o acesso disponibilizado
continua levando ao MFE legado".

## 6. Correção aplicada (dev)

Ação operacional reversível no ambiente dev, sem alterar código:

1. `POST /core-api/admin/apps/register` com
   `plugins/engineering/engineering.manifest.json` (HEAD) → HTTP 201.
   Cria linha `apps`, manifest, versão `0.2.0`, permissão
   `engineering.access` e 4 rotas.
2. `POST /core-api/admin/apps/register` com
   `plugins/dashboard-lmps/dash-lmps-microfrontend.manifest.json` →
   HTTP 201 (coexistência: legado também nunca registrado em dev).
3. `docker compose -f docker-compose.dev.yml up -d --build
   dashboard-lmps` (imagem inexistente; `delpi-engineering` já rodava).
4. `/me/apps` passou a incluir `engineering` com
   `entryUrl=/apps/engineering/assets/remoteEntry.js`,
   `renderMode=federated`, rotas incluindo `/apps/engineering/lmps`.

Em produção a ação equivalente fica com o operador — ver §10.

## 7. Evidência de browser real (Playwright, Chromium headless, login
Keycloak real `delpi-central`/`rober`)

| Cenário | Resultado |
|---|---|
| Login SSO | redirect Keycloak → portal autenticado |
| `/apps/engineering` | Portal Engenharia montado ("PORTAL ENGENHARIA / Bom dia, Robério", hero com "LMPS EM ACOMPANHAMENTO 245" — dado real de `/v1/home`); catálogo "Trabalho" com item **LMPs**; `remoteEntry.js?import` carregado |
| Clique em LMPs | URL → `/apps/engineering/lmps?start_date=2026-10-01&end_date=2026-10-29&competence=2026-10`; Portal continua montado (abas Início/Visão geral/Ajuda) |
| Renderização | `.dashboard-lmps` presente; header "Acompanhamento de LMPs", IDD 10.0, filtros, KPIs (2551 dias sem NC; 100% c/ metas 88,87%/95,00% do goal-context; lead 2,50; total 14), gráficos |
| Refresh na rota | permanece em `/apps/engineering/lmps`, feature renderizada |
| Detalhe OV | clique na linha → `/apps/engineering/lmps/ov/003696?…&branch=01`; página "Proposta 003696" com loading honesto "Consultando proposta, engenharia e produtos no TOTVS" |
| Voltar | `history.back` → `/apps/engineering/lmps?…` |
| Acesso direto | `goto /apps/engineering/lmps` → renderiza |
| Legado | `/apps/dashboard-lmps` → dashboard legado montado (`.dashboard-lmps`), chamando `/apps/api-delpi/…` (seus próprios contratos) — coexistência confirmada |

Chamadas de rede capturadas (21 totais ao backend): todas sob
`/apps/engineering-api/v1/` — `home`, `lmps`, `lmps/goal-context`,
`lmps/department-idd`, `lmps/nonconformities/streak`, `lmps/003696`,
`lmps/003696/history/events`, `lmps/003696/history/flow`.
**Zero chamadas `/apps/api-delpi` pela feature nova**; legado usa
api-delpi apenas dentro do seu próprio MFE — isolamento preservado.

Screenshots: `/tmp/g5r1-evidence/01..08-*.png` +
`evidence.json` (artefatos de sessão, não versionados).

## 8. AuthN/AuthZ

- `GET /apps/engineering-api/v1/lmps` sem token → **401** (re-verificado).
- Rota `/apps/engineering/lmps` exige `engineering.access` (manifest +
  `ProtectedRoute`); superadmin bypassa (usuário de teste `rober`).
- `dashboard-lmps.view` **não** libera a feature nova (teste de catálogo
  dedicado, doc 41).
- S2S: inalterado — apenas no facts BFF backend; nenhum token técnico no
  navegador.
- Negativo de usuário não-superadmin sem grant: TEST_NOT_RUN (sem
  segundo usuário de teste; guard é `ProtectedRoute` + backend
  fail-closed, ambos verificados).

## 9. Testes executados

| Comando | Resultado |
|---|---|
| `npm test` (plugins/engineering) | 119/119 passed (14 files) em `c253e052` |
| Prova browser Playwright | todos os cenários PASS (§7) |
| `curl` gateway: deep link, remoteEntry, legado | 200/200/200 |
| `curl` eng-api sem token | 401 |

Sem diff de código — typecheck/lint/build permanecem os do HEAD
(verificados na G5: 0 erros). Audits arquiteturais sem regressão:
nenhuma mudança de código.

## 10. Produção — PREPARE/ACT (operador)

O sintoma do usuário indica que no ambiente produtivo `engineering`
ainda não está registrado. Plano:

- **Owner**: operador com `apps.manage` (Robério).
- **Escopo**: `POST /core-api/admin/apps/register` com
  `plugins/engineering/engineering.manifest.json` v0.2.0 no ambiente
  produtivo; em seguida grant de `engineering.access` aos usuários
  autorizados. Verificar se `engineering` já não está registrado com
  manifest antigo — nesse caso usar
  `PUT /core-api/admin/apps/engineering/manifest`.
- **Riscos**: baixo; endpoint administrativo existente, reversível
  (`DELETE /admin/apps/engineering`); não altera legado nem permissões.
- **Rollback**: `DELETE` do plugin ou `rollback` de versão.
- **Pós-condições**: `/me/apps` inclui `/apps/engineering`; menu
  mostra Portal Engenharia; clique LMPs → `/apps/engineering/lmps`.
- **Nota**: NÃO executado — requer autorização operacional em prod.

## 11. Estado do ambiente dev (mutações desta sessão)

- Keycloak `delpi-keycloak` estava parado (exit 255 após restart do
  host) → `docker start` + aguardo de health.
- Registrados na Core dev: `engineering` 0.2.0 e `dashboard-lmps` 1.3.0
  (ambos ausentes; nenhum usuário poderia abrir os apps antes).
- Subido `delpi-dashboard-lmps` (build local) e recriado
  `delpi-plugin-ui` como dependência do serviço.
- Lockout temporário do usuário `rober` no Keycloak observado a partir
  de ~08:53 após logins falhos manuais — transitório.

## 12. Residuais e próximos passos

- Registro/grant em produção: pendente de operador (§10).
- Negativo de permissão em browser com usuário comum: sem credencial
  secundária; backend 401/403 já verificado.
- G5.V (homologação visual completa): permanece pendente — a evidência
  aqui cobre acessibilidade e smoke visual, não paridade pixel-a-pixel.
- NC gate: fora de escopo, como autorizado.
