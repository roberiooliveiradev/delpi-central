# Tour do portal

> **Código:** `portal/src/tour/` · **Integração:** `App.tsx` (`PortalTour`)

Tour **gamificado** e **não linear** para explorar a Minha DELPI: favoritos, catálogo, notificações, perfil, RBAC, privacidade, tema e admin (quando aplicável). Exibido uma vez por usuário por versão; pode ser reiniciado em **Meu Perfil**.

---

## Comportamento

| Aspecto | Detalhe |
|---|---|
| Disparo automático | Após login, consentimento aceito e `coreLoaded`, se a versão do tour ainda não foi concluída |
| Persistência | `localStorage` (cache) + **core-api** (`user_portal_tour_progress`, `portal_tour_quest_events`) |
| Versão | `PORTAL_TOUR_VERSION` (`2026-06-portal-v6-explore`) em `portalTourStorage.ts` — incrementar para reexibir após novas features |
| Reinício manual | Botão em **Meu Perfil** → dispara `DELPI_PORTAL_TOUR_START_EVENT` |
| Atalho | `Esc` ou botão ✕ **fecham o painel** sem encerrar a exploração; retome pela home |
| Conclusão | Automática ao completar todos os desafios obrigatórios (modal de celebração) |
| Ordem | **Livre** — o usuário explora no próprio ritmo |
| Bloqueio | **Nenhum** — painel flutuante + destaque sutil; interface sempre clicável |
| Responsivo | Painel full-width no mobile; 1 anel de destaque no mobile, 2 no desktop; sidebar mobile sobrepõe a página |

O tour observa cliques e mudanças em filtros (`watchTourQuests`). Cada desafio inclui **passos práticos** (`steps`) acessíveis pelo botão **Dica** no card — sem balão flutuante automático.

**Contexto de highlights:** com catálogo aberto, só desafios `scope: launcher`; em páginas dedicadas (`/profile`, `/notifications`, etc.), só desafios daquela página.

---

## API (core-api)

| Método | Path | Auth | Descrição |
|---|---|---|---|
| GET | `/me/portal-tour` | Usuário | Estado atual do tour |
| PATCH | `/me/portal-tour` | Usuário | Sincroniza progresso (`tourVersion`, `status`, `completedQuestIds` / `completedQuestId`) |
| GET | `/me/portal-tour/catalog` | Usuário | Catálogo de desafios **disponíveis para o usuário** (permissões, progresso, novidades) |
| GET | `/me/portal-tour/achievements` | Usuário | Conquistas desbloqueadas (derivadas do catálogo visível + eventos) |
| DELETE | `/me/portal-tour` | Usuário | Reinicia progresso (perfil → «Ver tour novamente») |
| GET | `/admin/portal-tour/explorers` | `rbac.manage` | Lista quem está explorando (`tourVersion`, `status`, paginação) |

| GET | `/admin/portal-tour/top-explorers` | `rbac.manage` | Ranking semanal por desafios concluídos |

**Status:** `exploring` · `completed` (`dismissed` legado é normalizado para `exploring` na leitura)

O portal sincroniza em background (debounce ~650 ms) a cada desafio concluído. Fechar o painel (✕ / Esc) **não** encerra a exploração — só `completed` ao atingir 100%. Admin → Estatísticas → Usuários exibe painel **Tour do portal — quem está explorando**.

### Arquitetura da gamificação (extensível)

A **fonte de verdade** dos desafios fica no core-api:

| Módulo | Papel |
|---|---|
| `portal_tour_quest_catalog.py` | Catálogo canônico — id, título, categoria, `optional`, `required_permissions`, `introduced_in_version` |
| `portal_tour_availability_service.py` | Filtra desafios pelo RBAC efetivo do usuário |
| `portal_tour_gamification_service.py` | XP, percentual e nível sobre desafios **disponíveis** |
| `portal_tour_achievement_catalog.py` | Conquistas derivadas do catálogo visível (não duplica ids) |

O portal consome `GET /me/portal-tour/catalog` e alinha título/hint/progresso; a **interação DOM** (seletores, `data-tour`, `isAvailable`) permanece em `portalTourQuests.ts` / `portalTourCatalogSync.ts`.

**Ao lançar funcionalidade nova:**

1. Registrar desafio em `portal_tour_quest_catalog.py` (`introduced_in_version` = versão atual ou nova).
2. Ligar interação no portal (`data-tour`, seletores em `portalTourQuests.ts`).
3. Bump `CURRENT_PORTAL_TOUR_VERSION` / `PORTAL_TOUR_VERSION` quando quiser reexibir o tour a quem já concluiu.
4. Usuários veem badge **novidade** nos desafios de `newQuestIds` retornados pela API.

Progresso, marcos e conquistas **nunca** contam desafios que o usuário não pode acessar (ex.: admin sem `rbac.manage`).

---

## Categorias e desafios

Lista agrupada no painel por categoria (`PORTAL_TOUR_CATEGORY_ORDER`).

### Apps e sidebar

| ID | Título | Disponibilidade |
|---|---|---|
| `sidebar-favorites` | Favoritos na barra | Favoritos visíveis na sidebar |
| `open-apps` | Catálogo de apps | Item Apps visível |
| `pin-app` | Fixar um app | Catálogo aberto |
| `launcher-search` | Buscar no catálogo | Catálogo aberto |

### Home

| ID | Título | Disponibilidade |
|---|---|---|
| `home-summary-notifications` | Resumo de notificações | Card na home |
| `home-favorites` | Favoritos na home | Seção `#home-favorites` |
| `home-recent` | Apps recentes | Seção `#home-recent` |
| `home-notifications` | Notificações na home | Bloco `#home-notifications` |
| `home-portal-tour-resume` | Retomar o tour na home | Card `home-portal-tour-resume` (opcional) |

### Notificações

| ID | Título | Disponibilidade |
|---|---|---|
| `sidebar-notifications` | Central na sidebar | Sino na sidebar |
| `page-notifications-inbox` | Caixa de entrada | Rota `/notifications` |
| `page-notifications-filter` | Filtrar notificações | Filtros visíveis na página |
| `page-notifications-preferences` | Preferências | Aba Preferências na página |

### Perfil e RBAC

| ID | Título | Disponibilidade |
|---|---|---|
| `sidebar-profile` | Perfil e conta | Menu do usuário na sidebar |
| `page-profile-info` | Dados pessoais | Rota `/profile` |
| `page-profile-rbac` | Grupos, papéis e permissões | Seção RBAC no perfil |
| `page-profile-apps` | Apps vinculados | Seção de apps no perfil |
| `page-profile-tour-restart` | Reiniciar tour | Botão no perfil |

### Privacidade

| ID | Título | Disponibilidade |
|---|---|---|
| `page-privacy-consent` | Consentimento | Rota `/privacy` |
| `page-privacy-export` | Exportar dados | Seção de exportação |

### Personalização

| ID | Título | Disponibilidade |
|---|---|---|
| `sidebar-theme` | Personalizar tema | Item Tema na sidebar |

### Admin (opcional)

Requer `rbac.manage` ou superadmin.

| ID | Título | Disponibilidade |
|---|---|---|
| `sidebar-admin` | Painel admin | Link Admin na sidebar |
| `page-admin-users` | Usuários | Rota `/admin`, aba Usuários |
| `page-admin-roles` | Papéis | Aba Papéis |
| `page-admin-permissions` | Permissões | Aba Permissões |
| `page-admin-apps` | Apps | Aba Apps |
| `page-admin-stats-tour` | Acompanhamento do tour | Estatísticas → Acompanhamento (opcional) |

**Conclusão:** ao atingir 100% dos desafios obrigatórios, o modal de celebração marca a versão como concluída no servidor e no `localStorage`. Não há «Pular» nem «Concluir» manual — a exploração é contínua e gamificada.

**Retomar:** com o painel fechado, a home exibe o card **Descubra o portal** (progresso e nível).

---

## UI

- Painel **Descubra o portal** (canto inferior direito; full-width no mobile com safe-area)
- Botão **✕** e `Esc` minimizam o painel; desafios continuam sendo detectados em segundo plano
- Card na **home** para reabrir o painel enquanto a exploração estiver em andamento
- Barra de XP / progresso (`requiredDone / requiredTotal`)
- Lista agrupada por categoria com estados: disponível, indisponível, concluído
- Botão **Dica** em cada card — expande passos sob demanda (sem balão flutuante automático)
- Anéis de destaque (`portal-tour-highlight-ring`) — outline fixo, sem pulse no DOM
- Toast ao completar cada desafio
- Rótulo de contexto (Catálogo / Perfil / Notificações / Admin / …)
- **Gamificação (Fases A–C):** toast +XP, bump na barra, ring verde, banners, modal de conclusão, confetti, **conquistas no perfil** — ver [playbook-portal-tour-gamificacao.md](./playbook-portal-tour-gamificacao.md)

---

## Âncoras (`data-tour`)

| Seletor | Componente |
|---|---|
| `[data-tour="sidebar-favorites"]` | `.sidebar-content` em `Sidebar.tsx` |
| `[data-tour="sidebar-apps"]` | Item **Apps** no footer |
| `[data-tour="sidebar-notifications"]` | Item **Notificações** no footer |
| `[data-tour="sidebar-notifications-panel"]` | Dropdown de notificações |
| `[data-tour="sidebar-theme"]` | Item **Tema** no footer |
| `[data-tour="sidebar-theme-menu"]` | Dropdown de tema |
| `[data-tour="sidebar-profile"]` | Item do usuário no footer |
| `[data-tour="sidebar-profile-menu"]` | Dropdown de perfil |
| `[data-tour="sidebar-admin"]` | Link **Admin** (condicional) |
| `[data-tour="launcher-modal"]` | `.launcher-modal` em `AppLauncher.tsx` |
| `[data-tour="launcher-search"]` | Campo de busca do catálogo |
| `[data-tour="home-page"]` | Container da home |
| `[data-tour="home-summary-notifications"]` | Card resumo de notificações |
| `#home-favorites`, `#home-recent`, `#home-notifications` | `HomePage.tsx` |
| `[data-tour="notifications-page"]` | `NotificationsPage.tsx` |
| `[data-tour="notifications-filters"]` | Filtros |
| `[data-tour="notifications-list"]` | Lista |
| `[data-tour="notifications-preferences"]` | Painel de preferências |
| `[data-tour="profile-page"]` | `MyProfile.tsx` |
| `[data-tour="profile-info"]` | Dados pessoais |
| `[data-tour="profile-rbac-summary"]` | Resumo RBAC |
| `[data-tour="profile-groups"]`, `profile-roles`, `profile-permissions`, `profile-apps` | Seções RBAC |
| `[data-tour="profile-tour-restart"]` | Reiniciar tour |
| `[data-tour="profile-tour-achievements"]` | Grid de conquistas |
| `[data-tour="privacy-page"]`, `privacy-consent`, `privacy-export` | `PrivacyPage.tsx` |
| `[data-tour="admin-page"]`, `admin-nav-{key}`, `admin-mobile-nav` | `AdminPage.tsx` |
| `[data-tour="admin-stats-subnav-tour"]`, `[data-tour="admin-stats-tour-page"]` | `StatsTab.tsx` / `StatsTourPage.tsx` |
| `[data-tour="home-portal-tour-resume"]` | `PortalTourHomeEntry.tsx` |

---

## Eventos

| Evento | Função |
|---|---|
| `DELPI_SIDEBAR_EXPAND_EVENT` | Reexpande sidebar colapsada |
| `DELPI_OPEN_APP_LAUNCHER_EVENT` | Abre catálogo Apps |
| `DELPI_CLOSE_APP_LAUNCHER_EVENT` | Fecha catálogo (ouvinte em `Sidebar.tsx`) |
| `DELPI_PORTAL_TOUR_SIDEBAR_PANEL_EVENT` | Sincroniza painéis do footer (`none` / …) |
| `DELPI_PORTAL_TOUR_START_EVENT` | Reinicia tour (`startPortalTour()`) |

Durante o tour, dropdowns da sidebar não fecham por clique externo (`data-portal-tour-active`) e itens do footer só **abrem** painéis (não alternam).

---

## z-index

Painel `10060`, anéis `10048`, launcher `10040` quando tour ativo.

---

## Migration (core-api)

```bash
cd core-api && alembic upgrade head
```

Tabelas: `user_portal_tour_progress`, `portal_tour_quest_events` (revision `n0o1p2q3r4`).

---

## Nova versão do tour

1. Adicionar desafio em `core-api/.../portal_tour_quest_catalog.py`
2. Ligar interação em `portalTourQuests.ts` (`getPortalTourQuests`) + `data-tour`
3. Bump `CURRENT_PORTAL_TOUR_VERSION` (API) e `PORTAL_TOUR_VERSION` (`portalTourStorage.ts`)
4. Ajustar `portalTourTargetVisibility.ts` / `portalTourQuestGuide.ts` se mudar escopo
5. Documentar neste arquivo e no [playbook de gamificação](./playbook-portal-tour-gamificacao.md)
