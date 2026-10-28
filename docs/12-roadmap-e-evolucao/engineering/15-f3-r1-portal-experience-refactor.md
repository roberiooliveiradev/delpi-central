# F3.R1 — Portal Engenharia: refatoração de experiência (padrão portal Minha DELPI)

**Status:** implementado
**Baseline:** `339e69d6c0` (F3-FINAL)
**Executor:** Devin
**Coordenação:** EVA — Architecture / Coordination

---

## 1. Escopo

Refatorar a experiência inicial do `plugins/engineering` para o padrão de
portal já usado no Portal Comercial: Top Bar (nav + busca + favoritos +
avatar), Hero de saudação, Eventos e interações, Caminhos e
funcionalidades, Visão geral e Ajuda — consumindo exclusivamente
`GET /apps/engineering-api/v1/home` e os componentes oficiais do
`@delpi/plugin-ui`. Sem EVA/MCP, sem migração de outros portais.

## 2. Reancoragem

`BASE_HEAD = 339e69d6c0cda5dae687c168d324d7d9c66657ce`. `origin/main`
avançou para `9c1d1acbe9` durante a execução (commits concorrentes) —
rebase + reteste antes do push, conforme `AGENTS.md`.

## 3. Inventário do plugin-ui (G0)

Composição de portal já existe no kit como **componentes individuais**
comprovados pelo Portal Comercial (todos exportados do remote
`@delpi/plugin-ui`):

| Funcionalidade | Componente | Owner | Reuso |
|---|---|---|---|
| Top Bar (nav/overflow/colapso) | `TopBar` + `UnderlineNav` | plugin-ui | direto (factory `createDashboardTopBar`) |
| Busca na Top Bar | `TopBarSearchTrigger` + `CommandPalette` | plugin-ui | direto |
| Favoritos na Top Bar | `TopBarFavoritesStrip` | plugin-ui | direto (chrome) |
| Avatar/identidade | `TopBarUserIdentity` | plugin-ui | direto |
| Hero | `PageHero` + `formatPortalGreeting` | plugin-ui | direto |
| Eventos | `EventsSection` (AlertQueueItem) | plugin-ui | direto |
| Catálogo | `SectionRouteCard` + `SectionCard` | plugin-ui | direto |
| Busca no catálogo | `CatalogSearchBar` | plugin-ui | direto |
| Últimos acessos | `RecentAccessStrip` | plugin-ui | direto (chrome) |
| Métricas | `MetricStrip` (PageHeroHighlight) | plugin-ui | direto |
| Manual/ajuda | `UserManual` (Frame/Layout/Concepts…) | plugin-ui | direto |
| Transição | `ViewTransition` | plugin-ui | disponível |

O que **não** é neutro no Comercial e foi inventariado como
específico do domínio: `homeFavoritesApi` (`commercial-api`
`/me/home-favorites` — Postgres, owner Comercial), `pluginRouteCatalog`
(rotas Comercial), `ShellUserPortfolioMenu` (carteira), badges de nav
(pedidos/tarefas/salas) e `useDirectoryUserLabels` (Core directory). Nada
disso foi importado ou copiado.

## 4. Decisão de generalização (G10)

**`PortalHomeComposition` não foi criada.** O Abstraction Gate não é
satisfeito: a composição Comercial é montada por componentes individuais
que já são compartilháveis por props/slots, e o Portal Engenharia é seu
segundo consumidor possível — mas ainda um único consumidor do padrão de
composição. Extrair um componente monolítico agora criaria uma terceira
camada sem consumidores nem contrato estável (fetch, favoritos e
catálogo são de domínio e não podem subir ao kit).

O MFE Engenharia **monta o kit atual** — exatamente o mesmo conjunto de
componentes do Comercial — sem alteração no `plugin-ui`, sem dependência
runtime do Comercial e sem mudança visual involuntária em outros
portais. A generalização fica registrada como candidata futura: quando
um terceiro portal pedir a composição, extrair um `PortalHomeLayout`
(slot-based, sem fetch/autorização) no `plugin-ui` com a Engenharia e o
Comercial como consumidores.

## 5. Arquitetura do MFE (G1)

```
plugins/engineering/src/
  app/
    EngineeringPluginShell.tsx   — TopBar + palette + favoritos + identidade
    engineeringRoutes.ts         — home/overview/help + paths + navegação
    openCatalogRoute.ts          — abertura governada de rotas do catálogo
    authDisplayName.ts           — display name/sub do JWT (apresentação)
    favoritesStore.ts            — favoritos locais, escopo por identidade
    recentViews.ts               — últimos acessos locais, escopo por identidade
  content/
    engineeringRouteCatalog.ts   — seções/rotas/permissões + copy pt-BR
  features/
    home/HomePage.tsx            — Hero + Eventos + Caminhos
    home/homeViewModel.ts        — mapeamento puro estados→apresentação
    home/useHomeData.ts          — fetch com AbortController + seq guard
    overview/OverviewPage.tsx    — métricas + estado das fontes
    help/HelpPage.tsx            — UserManual oficial
  api/ (inalterado + resetHttpClient)
  ui/engineeringUi.ts            — bindings factory do kit
```

Sub-rotas `/apps/engineering/overview` e `/apps/engineering/help`
resolvidas pelo Portal via maior-prefixo (`resolveMatchingRoute`) — o
manifest foi atualizado para `0.2.0` declarando-as com
`engineering.access` + `showInMenu: false` (mesmo padrão do manifesto
Comercial). Nenhuma permissão nova.

## 6. Home (G3–G5)

- **Hero:** `PageHero`, eyebrow `PORTAL ENGENHARIA`,
  `formatPortalGreeting` com nome do JWT, tiles de Minhas
  tarefas / Minhas solicitações / LMPs **somente** quando a seção está
  `available`/`empty` — fonte `unavailable`/`forbidden` nunca renderiza
  `0`.
- **Eventos e interações:** `EventsSection` com itens de
  `attention`/`tasks`/`requests` do contrato F2a; links só com `href`
  `/apps/*` devolvido pela API. Fonte degradada → aviso discreto +
  restante da página preservado; sem itens → estado honesto "Tudo em
  dia". Não converte as seis seções em cards de erro.
- **Caminhos e funcionalidades:** `SectionCard` + `CatalogSearchBar` +
  `RecentAccessStrip` + `SectionRouteCard` por categoria (Trabalho /
  Análises / Suporte). Itens externos só aparecem com a permissão do
  dono comprovada via `permissions` do host (`my-requests.access`,
  `dashboard-lmps.view`, `dashboard-engineering.view`) — apresentação,
  não RBAC. `Assistente EVA` existe no catálogo como `comingSoon` —
  desabilitado, sem link operacional.

## 7. Favoritos, recents e busca (G5)

- Não existe API neutra de favoritos na plataforma: o contrato do
  Comercial é `commercial-api`-owned. Sem aprovação para criar tabela na
  engineering-api, favoritos e últimos acessos usam **localStorage
  escopado por `sub` do JWT**
  (`engineering.home.favorites.v1.<sub>`,
  `engineering.home.recentViews.v1.<sub>`): isolado por usuário no
  mesmo dispositivo, **sem sincronização entre dispositivos**
  (documentado na Ajuda). Conteúdo = ids estáveis do catálogo, nunca
  dados de domínio.
- Estrelas do catálogo e faixa da Top Bar compartilham o mesmo store
  (subscription) — atualização imediata nas duas direções. Item que
  perdeu permissão fica fora dos destinos executáveis.
- Busca: `CommandPalette` (Ctrl+K / trigger) e `CatalogSearchBar`
  filtram nome/descrição/keywords com normalização de acentos — nunca
  retornam item sem permissão.

## 8. Diagnóstico das fontes com erro (G8)

Causa raiz confirmada em código, não em CSS:

- `GET /requests/mine` retorna **403** quando o usuário não tem nenhuma
  permissão `my-requests.*` (`actor_for`/`module_actor` em
  `requests_permissions.py`) → engineering-api mapeia para `forbidden`.
- `GET /requests/work-queue` retorna **200 vazio** sem
  `*.process/view-all/manage` → `empty`; `forbidden`/`unavailable`
  cobrem os demais casos.
- LMPs funcionavam porque o usuário possui grant no owner correspondente.

Ou seja: **comportamento correto e fail-closed, não bug contratual** —
a experiência anterior apenas renderizava cada seção degradada como
cartão de erro. A nova Home apresenta esses estados como aviso discreto
no card de eventos e como estado oficial na Visão geral. Nenhuma
mudança de owner/AuthZ foi feita ou necessária.

## 9. Sessão e desmontagem (G9)

- `resetHttpClient()` zera o getter de token no `unmount` — nenhum
  callback de sessão anterior sobrevive à remontagem.
- `useHomeData`: `AbortController` por carga, abort no unmount e
  sequence-guard que descarta respostas atrasadas.
- Favoritos/recents: identidade ligada ao `sub` do JWT; `reset*` no
  `unmount` limpa cache e listeners; troca de usuário recarrega do
  escopo da nova identidade.
- JWT nunca em storage/log/URL — o `sub` aparece apenas como chave
  local de isolamento.

## 10. Testes e validação

- **48 testes** em 6 arquivos (vitest, env node):
  rotas/sub-rotas/hrefs governados (8), catálogo+busca+permissões (13),
  favoritos com isolamento por identidade (4), recents com revogação
  (3), view model/estados/hero/eventos (14), client HTTP (6).
- `tsc --noEmit` limpo; `eslint` 0 problemas; `vite build` OK;
  verificação de patch federation React OK.
- Manifest `0.2.0` validado pelo `ManifestValidator` da Core.
- Audits: backend_boundaries 0 | fastapi_authz 0 | openapi_contracts 0
  | architecture_phase3 OK | platform_guardrails 0.
  (`audit_plugin_ui_duplication`/`audit_mfe_plugin_ui_css` reportam
  findings repo-wide preexistentes em ~51 plugins — incluindo
  my-requests e commercial — não introduzidos por esta mudança.)

## 11. Deploy e smoke

Deploy canônico: `git pull --ff-only` +
`./infra/scripts/up-prod-sequential.sh --build engineering` (somente o
MFE — `plugin-ui` e backend intocados; manifest re-registrado
pende do mesmo gate administrativo da F3).

Smoke público: `remoteEntry.js` → 200, `/apps/engineering` → 200,
`/apps/engineering-api/v1/home` sem JWT → 401.
Smoke autenticado: **PENDING_GRANT_APPROVAL** — depende do registro do
manifest `0.2.0` na Core + grant de `engineering.access` (mesma
pendência administrativa já registrada; nenhum grant ad-hoc criado).

## 12. Residuais

- Registro do manifest `0.2.0` + grant `engineering.access`:
  `PENDING_OPERATOR_TOKEN` / `PENDING_GRANT_APPROVAL`.
- Validação visual real (desktop/tablet/mobile, contraste, foco) —
  pendente da primeira sessão autenticada; não declarada validada.
- Favoritos/recents são locais por dispositivo — sincronização exigiria
  contrato neutro de favoritos (decisão de plataforma).
- `attention`/`activity`/`collaboration` seguem sem fonte oficial.
- Chunk `lucide-react` >500 kB — aviso conhecido do federation build.

## 13. Próximo bounded step

Registro do manifest 0.2.0 (script canônico com token `apps.manage`) →
grant autorizado → smoke autenticado com validação visual real.
Generalização `PortalHomeLayout` só quando um terceiro portal exigir a
composição. EVA/MCP fora de escopo.
