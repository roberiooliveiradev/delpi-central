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
| Atalho | `Esc` encerra sem marcar como concluído (ignorado com catálogo Apps aberto) |
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
| DELETE | `/me/portal-tour` | Usuário | Reinicia progresso (perfil → «Ver tour novamente») |
| GET | `/admin/portal-tour/explorers` | `rbac.manage` | Lista quem está explorando (`tourVersion`, `status`, paginação) |

**Status:** `exploring` · `completed` · `dismissed`

O portal sincroniza em background (debounce ~650 ms) a cada desafio concluído e ao concluir/pular o tour. Admin → Estatísticas → Usuários exibe painel **Tour do portal — quem está explorando**.

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

**Concluir** grava a versão no servidor e no `localStorage`. **Pular** registra `dismissed` no servidor e fecha sem marcar concluído.

---

## UI

- Painel **Descubra o portal** (canto inferior direito; full-width no mobile com safe-area)
- Barra de XP / progresso (`requiredDone / requiredTotal`)
- Lista agrupada por categoria com estados: disponível, indisponível, concluído
- Botão **Dica** em cada card — expande passos sob demanda (sem balão flutuante automático)
- Anéis de destaque (`portal-tour-highlight-ring`) — outline fixo, sem pulse no DOM
- Toast ao completar cada desafio
- Rótulo de contexto (Catálogo / Perfil / Notificações / Admin / …)

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
| `[data-tour="privacy-page"]`, `privacy-consent`, `privacy-export` | `PrivacyPage.tsx` |
| `[data-tour="admin-page"]`, `admin-nav-{key}`, `admin-mobile-nav` | `AdminPage.tsx` |

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

1. Atualizar desafios em `portalTourQuests.ts` (`getPortalTourQuests`)
2. Bump `PORTAL_TOUR_VERSION` em `portalTourStorage.ts`
3. Adicionar `data-tour` ou ids se houver novos alvos
4. Ajustar `portalTourTargetVisibility.ts` / `portalTourQuestGuide.ts` se mudar escopo
5. Documentar novidade neste arquivo
