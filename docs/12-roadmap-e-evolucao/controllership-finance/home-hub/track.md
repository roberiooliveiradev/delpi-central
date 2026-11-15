# Trilha — Home hub (H0–H6)

Fonte: [plan.md](./plan.md). Autoridade: instruções oficiais do arquiteto e `.cursor` > padrão visual dos Portais (`docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md`) > `30-plugin-ui-reuse-map.md` > este track > plan.md.

## 1. Regras

1. `main`, sem branch, sem stash/reset/clean. `git add` **só com caminhos explícitos** da etapa (outros agentes usam a mesma árvore; nunca `git add -A`, `git add .`, `commit -a`). Push a cada etapa.
2. Protocolo: LER → INVENTARIAR → ALTERAR (mínimo) → TESTAR → VERIFICAR → DOCUMENTAR (quadro e registro deste track no mesmo commit) → REPORTAR.
3. Até 3 ciclos de correção por problema; no 4º, BLOCKED.
4. Sem permission nova (só `controllership-finance.access`/`.manage`; acesso ao LNF é leitura das permissões efetivas do Core). Backend autoriza; UI só esconde.
5. `@delpi/plugin-ui` first; reaproveitar o que o Comercial usa. Mudança no plugin-ui só se indispensável, aditiva e com prova dos consumidores (lição da T13R).
6. Migration nova só a V030; nunca editar migration aplicada.
7. Repositório público: nenhum dado real.
8. Evidência `PROVEN | TO_INVENTORY | INCONCLUSIVE`; teste `PASS | FAIL | TEST_NOT_RUN`. Página que não foi aberta é INCONCLUSIVE.

## 2. Paradas

| # | Quando parar |
|---|---|
| Z1 | 4º ciclo no mesmo problema |
| Z2 | Falha nova em suíte (não pré-existente no pai) |
| Z3 | O padrão do Comercial exige mudança no plugin-ui que não seja aditiva |
| Z4 | A regra de entrada do app LNF não pode ser lida das permissões efetivas sem acoplar ao domínio do LNF — listar opções |
| Z5 | Escolha de produto não coberta por D1–D8 (DECISION_REQUIRED) |
| Z6 | Falha em PROD → rollback e parar |

## 3. Quadro de status

| Etapa | Status | SHA |
|---|---|---|
| H0 Inventário do padrão Comercial × CF | DONE | `9904b4fb46` |
| H1 BFF: `lnfAccess` no viewer-context | DONE | `6a6ca32c84` |
| H2 BFF: favoritos (V030 + rotas) | DONE | `15f8e18653` |
| H3 MFE: cards (Portal sai, Notas fiscais, Administração) | DONE | `02d812285c` |
| H4 MFE: favoritos (estrela, store, barra do topo) e Ajuda | DONE | `3336e20b0a` |
| H5 HML | DONE | `936948b954` / docs `f7c4c10e64` |
| H6 PROD | DONE | (este commit) |

### H0 — inventário Comercial → CF

| Peça Comercial | Peça CF | Ação |
|---|---|---|
| `pluginRouteCatalog.ts` (`HUB_SECTIONS`, caps, busca) | `plugins/controllership-finance/src/content/pluginRouteCatalog.ts` | **adaptar** — remover `portal`; cards `notas-fiscais` + `administration`; cap `lnfAccess`; kind `external` + `href` |
| `hubRouteIcons.tsx` | ícones embutidos em `HomePage.tsx` (`SECTION_ICONS`) | **criar** `hubRouteIcons.tsx` (ou estender SECTION_ICONS) — `FileText`/`Receipt`/`Settings` |
| `HomePage.tsx` (estrela, recents, busca) | `features/home/HomePage.tsx` | **adaptar** — `onPinClick`, store favoritos; parar de empurrar Início nos recents |
| `homeFavoritesApi.ts` | — | **criar** → BFF CF `/me/home-favorites` |
| `homeFavoritesStore.ts` (+ test) | — | **criar** (mesmo comportamento otimista) |
| `ShellFavoritesStrip.tsx` | — | **criar**; ligar no `PluginShell` secondary |
| `commercialUi` `TopBarFavoritesStrip` | `controllershipFinanceUi.ts` | **adaptar** — exportar `CfTopBarFavoritesStrip` via `createDashboardTopBarFavoritesStrip` (já no kit) |
| `ShellTopBarSecondary` (busca + favoritos) | secondary inline no `PluginShell.tsx` | **adaptar** — inserir strip ao lado do search |
| `V006__home_favorites.sql` | — | **criar** `V030__home_favorites.sql` em `controllership_finance` |
| `home_favorites_routes.py` + repo + testes | — | **criar** espelho; auth `access` **ou** `accessDre` |
| `GET` capabilities no viewer Comercial (caps no shell) | `viewer_context_routes.py` + `viewerContextApi.ts` | **adaptar** — `capabilities.lnfAccess` aditivo |
| `has_lnf_clara_entry` / `LANCAMENTO_NOTAS_FISCAIS_ANY_PERMISSIONS` | `authz.py` + `invoice_posting/permissions.py` | **existe** — reutilizar no viewer (D6; sem permission nova) |
| Ajuda `CM_HELP.home.favorites` | `CF_HELP.home` | **adaptar** — Notas fiscais, Administração, favoritos |
| Testes estruturais hub / catálogo | `pluginRouteCatalog.test.ts`, `HomePage.test.tsx` | **adaptar** |

**D7 (Comercial):** Início e Meu perfil **não** estão em `HUB_SECTIONS`; busca/Ctrl+K só indexam o catálogo. Recents só aceitam viewIds do catálogo (`isKnownView`) — Início não entra. CF hoje tem card Portal + `pushRecentView(home)` no mount → alinhar: tirar Portal do catálogo; não empurrar Início; perfil continua no avatar (`/profile`).

**D8 (Comercial):** favoritos só `viewId` (+ `search`) do portal; sem link externo / `href`. LNF externo **sem estrela** nesta etapa.

## 4. Etapas

**H0 — Inventário (somente leitura).** No Comercial: `pluginRouteCatalog.ts` (seções, ordem, ícones `hubRouteIcons.tsx`), `HomePage.tsx` (estrela, «Últimos acessos», busca), `homeFavoritesApi.ts`, `homeFavoritesStore.ts`, `ShellFavoritesStrip.tsx`, testes estruturais (`homeLauncher.structural.test.mjs`, `pluginRouteCatalog.test.mjs`); `commercial-api` V006, rotas, repositório e testes. No CF: os equivalentes e o `/viewer-context`. Saída: tabela «peça do Comercial → peça do CF (existe / criar / adaptar)» e as respostas de D7/D8 (o que o Comercial faz).

**H1 — `lnfAccess`.** `GET /viewer-context` ganha `capabilities.lnfAccess` (aditivo), calculado das permissões efetivas do Core com a mesma regra de entrada do app LNF. Testes: com e sem permissão do LNF; contrato do viewer.

**H2 — Favoritos na BFF.** V030 `controllership_finance.home_favorites`; `GET/PUT /home-favorites` no padrão do Comercial; autorização `access` ou `accessDre`; usuário = `sub`; validação dos itens contra os caminhos do catálogo e limite de quantidade; testes (200/401/403/422, persistência, isolamento por usuário).

**H3 — Cards.** `HUB_SECTIONS` no alvo do plan §1: tira `portal`; card `notas-fiscais` (ícone do padrão, ex.: `FileText`/`Receipt` do lucide) com Auditoria de Entradas e o link externo `/apps/lancamento-notas-fiscais` (`requiredCap: "lnfAccess"`, novo `kind` para link externo se o catálogo não tiver); card `administration` com os três itens de manage; Central de Fechamento só com os três de access; DRE inalterado. Busca e «Últimos acessos» como o Comercial (D7). Testes do catálogo e estrutural do Início.

**H4 — Favoritos no MFE e Ajuda.** API, store, estrela por caminho (D8), «Favoritos» na barra do topo com o componente do plugin-ui, favorito sem permissão escondido; `CF_HELP` do Início atualizado. Testes de render e de store; `tsc`.

**H5 — HML.** Publicar BFF (V030) e MFE. Playwright: perfis access, manage, LNF sim/não, DRE → cards certos; favoritar → recarregar → continua; abrir pela barra; celular; claro/escuro; teclado/foco. Screenshots no report (não commitar).

**H6 — PROD.** Tags `rollback-home-hub-controllership-finance-api` e `rollback-home-hub-controllership-finance`; BFF (V030) → MFE; Início abre (página, não só remoteEntry); `/home-favorites` com usuário real pelo próprio app; logs sem token. Falha → rollback (Z6).

## 5. Rollback

MFE e BFF pelas tags. V030 só cria tabela nova: rollback da BFF não precisa desfazer a tabela.

## 6. Registro

| Data | Etapa | SHA | Status | Nota |
|---|---|---|---|---|
| 2026-11-14 | plano | — | READY | Doc 170. D1–D4 do owner; D5 regra do produto; D6–D8 propostas pelo Claude. |
| 2026-11-14 | H0 | `9904b4fb46` | DONE | Inventário Comercial×CF; D7/D8 confirmados no código. HEAD base `59855c61`. Higiene: index prévio incluiu 2 arquivos delia no mesmo commit (não revertidos). |
| 2026-11-14 | H1 | `6a6ca32c84` | DONE | `capabilities.lnfAccess` aditivo via `has_lnf_clara_entry`; testes viewer 24 PASS; MFE client + vitest 22 PASS. |
| 2026-11-14 | H2 | `15f8e18653` | DONE | V030 `home_favorites`; GET/PUT `/me/home-favorites`; auth access\|accessDre; 11 PASS. |
| 2026-11-14 | H3 | `02d812285c` | DONE | Cards alvo; Portal fora; LNF externo; Admin manage; D7; vitest 36 PASS. |
| 2026-11-14 | H4 | `3336e20b0a` | DONE | Favoritos MFE + strip + Ajuda; LNF sem estrela (D8); vitest 30 PASS; tsc ok. |
| 2026-11-14 | H5 | `936948b954` / `f7c4c10e64` | DONE | HML pull+build API/MFE healthy; Playwright 3/3 PASS (desktop cards+favoritos, mobile, Ctrl+K). Screenshots `/tmp/home-hub-h5-artifacts` (não commitados). Perfis manage/LNF/DRE dedicados: INCONCLUSIVE (só `hml-tester` superadmin). Claro/escuro: INCONCLUSIVE. |
| 2026-11-14 | H6 | (este commit) | DONE | Tags `rollback-home-hub-controllership-finance{,-api}` → `3336e20b0a`. PROD pull `f7c4c10e64`; V030 applied; home/remoteEntry 200; App chunk com Notas fiscais/home-favorites/lnfAccess; `/me/home-favorites` anônimo 401. Favoritos autenticados em PROD via UI: INCONCLUSIVE (prova de persistência em H5). Logs gateway sem token. |
