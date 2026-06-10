import {
  hasVisibleTarget,
  isLauncherOpen,
} from "./portalTourTargetVisibility";
import {
  isAdminRoute,
  isHomeRoute,
  isNotificationsRoute,
  isPrivacyRoute,
  isProfileRoute,
} from "./portalTourRoutes";
import type {
  PortalTourQuest,
  PortalTourQuestCategory,
  PortalTourQuestContext,
} from "./portalTourQuestTypes";

export type {
  PortalTourQuest,
  PortalTourQuestCategory,
  PortalTourQuestContext,
  PortalTourQuestScope,
} from "./portalTourQuestTypes";
export {
  PORTAL_TOUR_CATEGORY_LABELS,
  PORTAL_TOUR_CATEGORY_ORDER,
} from "./portalTourQuestTypes";

function hasTarget(selector: string) {
  return Boolean(document.querySelector(selector));
}

function sidebarVisible() {
  return hasVisibleTarget(".sidebar:not(.collapsed)");
}

export function getPortalTourQuests({
  canAccessAdmin,
}: PortalTourQuestContext): PortalTourQuest[] {
  const quests: PortalTourQuest[] = [
    // —— Apps & favoritos ——
    {
      id: "sidebar-favorites",
      title: "Favoritos na barra",
      hint: "Acesse ou reorganize apps fixados.",
      steps: [
        "Clique em um favorito para abrir o app.",
        "Para reordenar: segure o card ~0,5 s e arraste.",
        "Solte na posição desejada.",
      ],
      unlockHint: "Fixe um app pelo pin no catálogo (Apps) para criar favoritos.",
      scope: "sidebar",
      category: "apps",
      actionSelector:
        '[data-tour="sidebar-favorites"] [data-app-id], [data-tour="sidebar-favorites"] .launcher-app-tile',
      highlightSelector:
        '[data-tour="sidebar-favorites"] .launcher-app-tile, [data-tour="sidebar-favorites"] [data-app-id]',
      isAvailable: () =>
        sidebarVisible() &&
        hasTarget(
          '[data-tour="sidebar-favorites"] [data-app-id], [data-tour="sidebar-favorites"] .launcher-app-tile',
        ),
    },
    {
      id: "open-apps",
      title: "Catálogo de apps",
      hint: "Abra a lista completa de aplicativos.",
      steps: [
        "No rodapé da sidebar, clique em Apps.",
        "Use a busca para filtrar por nome ou rota.",
        "Clique em um card para abrir o aplicativo.",
      ],
      scope: "sidebar",
      category: "apps",
      actionSelector: '[data-tour="sidebar-apps"]',
      isAvailable: () =>
        !isLauncherOpen() &&
        sidebarVisible() &&
        hasVisibleTarget('[data-tour="sidebar-apps"]'),
    },
    {
      id: "pin-app",
      title: "Fixar um app",
      hint: "Salve um app nos favoritos pelo pin.",
      steps: [
        "No catálogo, localize o app desejado.",
        "Clique no ícone de pin no canto do card.",
        "Apps fixados aparecem na sidebar e na home.",
      ],
      unlockHint: "Clique em Apps na barra lateral para abrir o catálogo.",
      scope: "launcher",
      category: "apps",
      actionSelector: '[data-tour="launcher-modal"] .launcher-pin',
      highlightSelector: '[data-tour="launcher-grid"] .launcher-pin, [data-tour="launcher-grid"] .launcher-app-tile',
      isAvailable: () =>
        isLauncherOpen() &&
        hasTarget('[data-tour="launcher-modal"] .launcher-pin'),
    },
    {
      id: "launcher-search",
      title: "Buscar no catálogo",
      hint: "Encontre apps e rotas pela busca.",
      steps: [
        "Com o catálogo aberto, clique no campo de busca.",
        "Digite parte do nome do app ou rota.",
        "Abra um resultado da lista.",
      ],
      unlockHint: "Abra Apps na sidebar para acessar a busca.",
      scope: "launcher",
      category: "apps",
      actionSelector:
        '[data-tour="launcher-search"] input, [data-tour="launcher-search"]',
      highlightSelector: '[data-tour="launcher-search"]',
      isAvailable: () =>
        isLauncherOpen() && hasVisibleTarget('[data-tour="launcher-search"]'),
    },

    // —— Home ——
    {
      id: "home-summary-notifications",
      title: "Resumo de notificações",
      hint: "Veja quantas mensagens não lidas você tem.",
      steps: [
        "Na home, observe o card de Notificações no topo.",
        "Clique nele para ir à central completa.",
      ],
      scope: "home",
      category: "home",
      actionSelector: '[data-tour="home-summary-notifications"]',
      isAvailable: () =>
        isHomeRoute() &&
        !isLauncherOpen() &&
        hasVisibleTarget('[data-tour="home-summary-notifications"]'),
    },
    {
      id: "home-favorites",
      title: "Favoritos na home",
      hint: "Gerencie favoritos direto da página inicial.",
      steps: [
        "Na seção Favoritos, passe o mouse sobre um card.",
        "Clique no pin para fixar ou desfixar.",
        "Use o card para abrir o app rapidamente.",
      ],
      unlockHint: "Acesse a página inicial e fixe apps pelo catálogo.",
      scope: "home",
      category: "home",
      actionSelector: "#home-favorites .launcher-pin, #home-favorites .launcher-app-tile",
      highlightSelector: "#home-favorites .launcher-app-tile",
      isAvailable: () =>
        isHomeRoute() &&
        !isLauncherOpen() &&
        hasTarget("#home-favorites .launcher-pin, #home-favorites .launcher-app-tile"),
    },
    {
      id: "home-recent",
      title: "Apps recentes",
      hint: "Retome de onde parou.",
      steps: [
        "Veja os apps usados recentemente na home.",
        "Clique em um card para abrir.",
        "Use o pin para fixar um recente nos favoritos.",
      ],
      unlockHint: "Abra qualquer app — ele aparecerá em Continuar trabalhando.",
      scope: "home",
      category: "home",
      actionSelector:
        "#home-recent .launcher-app-tile, #home-recent .launcher-pin",
      highlightSelector: "#home-recent .launcher-app-tile",
      isAvailable: () =>
        isHomeRoute() &&
        !isLauncherOpen() &&
        hasTarget("#home-recent .launcher-app-tile, #home-recent .launcher-pin"),
    },
    {
      id: "home-notifications",
      title: "Notificações na home",
      hint: "Acompanhe avisos sem sair da home.",
      steps: [
        'Clique em "Ver todas" ou em um aviso recente.',
        "Marque como lida ou abra o link da mensagem.",
      ],
      unlockHint: "Vá à página inicial para ver o painel de notificações.",
      scope: "home",
      category: "home",
      actionSelector:
        '#home-notifications .home-panel-action, #home-notifications [data-tour="home-notification-card"], #home-notifications button[type="button"]',
      highlightSelector: "#home-notifications .home-panel-action",
      isAvailable: () =>
        isHomeRoute() &&
        !isLauncherOpen() &&
        hasVisibleTarget("#home-notifications"),
    },
    {
      id: "home-portal-tour-resume",
      title: "Retomar o tour na home",
      hint: "Use o card Descubra o portal para continuar.",
      steps: [
        "Na home, localize o card Descubra o portal.",
        "Clique nele para reabrir o painel de desafios.",
        "Continue explorando no seu ritmo.",
      ],
      unlockHint: "Feche o painel do tour (✕) — o card aparece na home.",
      scope: "home",
      category: "home",
      optional: true,
      actionSelector: '[data-tour="home-portal-tour-resume"]',
      highlightSelector: '[data-tour="home-portal-tour-resume"]',
      isAvailable: () =>
        isHomeRoute() &&
        !isLauncherOpen() &&
        hasVisibleTarget('[data-tour="home-portal-tour-resume"]'),
    },

    // —— Notificações ——
    {
      id: "sidebar-notifications",
      title: "Sino na sidebar",
      hint: "Prévia rápida sem sair da tela atual.",
      steps: [
        "Clique no sino no rodapé da sidebar.",
        "Leia avisos recentes no painel.",
        'Use "Ver todas" para abrir a página completa.',
      ],
      unlockHint: "Expanda a sidebar e feche o catálogo de apps.",
      scope: "sidebar",
      category: "notifications",
      actionSelector:
        '[data-tour="sidebar-notifications"], [data-tour="sidebar-notifications-panel"] .notif-item--link, [data-tour="sidebar-notifications-panel"] .notif-item, [data-tour="sidebar-notifications-panel"] a',
      highlightSelector: '[data-tour="sidebar-notifications"]',
      isAvailable: () =>
        !isLauncherOpen() &&
        sidebarVisible() &&
        hasVisibleTarget('[data-tour="sidebar-notifications"]'),
    },
    {
      id: "page-notifications-inbox",
      title: "Central de notificações",
      hint: "Histórico completo com filtros.",
      steps: [
        "Abra Notificações pelo sino, home ou menu de perfil.",
        "Navegue pelo histórico de mensagens.",
        "Clique em um card para marcar como lida ou seguir o link.",
      ],
      unlockHint: 'Use "Ver todas" na home ou no painel do sino.',
      scope: "notifications",
      category: "notifications",
      actionSelector:
        '[data-tour="notifications-list"] [data-tour="notification-card"], [data-tour="notifications-list"] .notification-card, #notifications-section-inbox',
      highlightSelector: '[data-tour="notifications-list"]',
      isAvailable: () =>
        isNotificationsRoute() &&
        hasVisibleTarget('[data-tour="notifications-page"]'),
    },
    {
      id: "page-notifications-filter",
      title: "Filtrar notificações",
      hint: "Refine por status, categoria ou importantes.",
      steps: [
        "Use as abas Todas / Não lidas / Lidas.",
        "Escolha uma categoria no seletor.",
        "Ative o filtro de importantes, se quiser.",
      ],
      unlockHint: "Acesse a página Notificações para usar os filtros.",
      scope: "notifications",
      category: "notifications",
      actionSelector:
        '[data-tour="notifications-filters"] button, [data-tour="notifications-filters"] select, .notifications-page__status-tab, .notifications-page__important-toggle',
      highlightSelector: '[data-tour="notifications-filters"]',
      isAvailable: () =>
        isNotificationsRoute() &&
        hasVisibleTarget('[data-tour="notifications-filters"]'),
    },
    {
      id: "page-notifications-preferences",
      title: "Preferências de notificação",
      hint: "Escolha o que deseja receber.",
      steps: [
        'Na página Notificações, abra a aba "Preferências".',
        "Ative ou desative tipos de mensagem.",
        "As escolhas valem para este navegador/conta.",
      ],
      unlockHint: "Abra a página Notificações e troque para Preferências.",
      scope: "notifications",
      category: "notifications",
      actionSelector:
        '#notifications-section-preferences, [data-tour="notifications-preferences"] input, [data-tour="notifications-preferences"] button, [data-tour="notifications-preferences"] label',
      highlightSelector: "#notifications-section-preferences",
      isAvailable: () =>
        isNotificationsRoute() &&
        hasVisibleTarget("#notifications-section-preferences"),
    },

    // —— Perfil & RBAC ——
    {
      id: "sidebar-profile",
      title: "Menu de perfil",
      hint: "Atalho para conta e privacidade.",
      steps: [
        "Clique no seu nome no rodapé da sidebar.",
        "Escolha Meu Perfil, Privacidade ou sair.",
      ],
      unlockHint: "Expanda a sidebar para ver seu nome no rodapé.",
      scope: "sidebar",
      category: "profile",
      actionSelector:
        '[data-tour="sidebar-profile"], [data-tour="sidebar-profile-menu"] .dropdown-item:not(.danger)',
      highlightSelector: '[data-tour="sidebar-profile"]',
      isAvailable: () =>
        !isLauncherOpen() &&
        sidebarVisible() &&
        hasVisibleTarget('[data-tour="sidebar-profile"]'),
    },
    {
      id: "page-profile-info",
      title: "Dados da conta",
      hint: "Nome, e-mail e status de superadmin.",
      steps: [
        "Abra Meu Perfil pelo menu da sidebar.",
        "Revise nome, e-mail e identificador.",
        "Confira se sua conta está ativa.",
      ],
      unlockHint: "Menu de perfil → Meu Perfil.",
      scope: "profile",
      category: "profile",
      actionSelector: '[data-tour="profile-info"], [data-tour="profile-summary-card"]',
      highlightSelector: '[data-tour="profile-info"]',
      isAvailable: () =>
        isProfileRoute() && hasVisibleTarget('[data-tour="profile-info"]'),
    },
    {
      id: "page-profile-rbac",
      title: "Grupos, papéis e permissões",
      hint: "Entenda seu acesso na plataforma.",
      steps: [
        "No perfil, veja os cards de resumo (Grupos, Papéis, Permissões).",
        "Clique em um card para rolar até a tabela correspondente.",
        "Confira o que está vinculado à sua conta.",
      ],
      unlockHint: "Abra Meu Perfil — as seções aparecem conforme seu vínculo.",
      scope: "profile",
      category: "profile",
      actionSelector:
        '[data-tour="profile-rbac-summary"] .home-summary-card, [data-tour="profile-groups"], [data-tour="profile-roles"], [data-tour="profile-permissions"]',
      highlightSelector: '[data-tour="profile-rbac-summary"]',
      isAvailable: () =>
        isProfileRoute() &&
        hasVisibleTarget(
          '[data-tour="profile-rbac-summary"] .home-summary-card, [data-tour="profile-groups"], [data-tour="profile-roles"], [data-tour="profile-permissions"]',
        ),
    },
    {
      id: "page-profile-apps",
      title: "Apps no perfil",
      hint: "Todos os aplicativos liberados para você.",
      steps: [
        "Role até a seção Aplicativos no perfil.",
        "Use a busca para filtrar por nome.",
        "Abra um app direto da lista.",
      ],
      unlockHint: "Meu Perfil → seção Aplicativos (quando houver apps).",
      scope: "profile",
      category: "profile",
      actionSelector:
        '[data-tour="profile-apps"] .launcher-app-tile, [data-tour="profile-apps"] input, [data-tour="profile-apps"]',
      highlightSelector: '[data-tour="profile-apps"]',
      isAvailable: () =>
        isProfileRoute() && hasVisibleTarget('[data-tour="profile-apps"]'),
    },
    {
      id: "page-profile-tour-restart",
      title: "Repetir o tour",
      hint: "Revise as funcionalidades quando quiser.",
      steps: [
        'Em Meu Perfil, clique em "Ver tour do portal novamente".',
        "O painel de descobertas reaparece na home.",
        "Explore no seu ritmo — a ordem é livre.",
      ],
      unlockHint: "Abra Meu Perfil para encontrar o link do tour.",
      scope: "profile",
      category: "profile",
      actionSelector: '[data-tour="profile-tour-restart"]',
      isAvailable: () =>
        isProfileRoute() &&
        hasVisibleTarget('[data-tour="profile-tour-restart"]'),
    },

    // —— Privacidade ——
    {
      id: "page-privacy-consent",
      title: "Consentimentos LGPD",
      hint: "Gerencie finalidades de uso de dados.",
      steps: [
        "Abra Privacidade e Dados pelo menu de perfil.",
        "Revise cada finalidade listada.",
        "Use o toggle para conceder ou revogar consentimento.",
      ],
      unlockHint: "Menu de perfil → Privacidade e Dados.",
      scope: "privacy",
      category: "privacy",
      actionSelector:
        '[data-tour="privacy-consent"] button, [data-tour="privacy-consent"] .privacy-page__toggle',
      highlightSelector: '[data-tour="privacy-consent"]',
      isAvailable: () =>
        isPrivacyRoute() && hasVisibleTarget('[data-tour="privacy-consent"]'),
    },
    {
      id: "page-privacy-export",
      title: "Exportar meus dados",
      hint: "Solicite uma cópia dos seus dados.",
      steps: [
        "Na página de privacidade, localize Exportar dados.",
        "Clique para solicitar o arquivo.",
        "Aguarde o processamento conforme a política vigente.",
      ],
      unlockHint: "Menu de perfil → Privacidade e Dados.",
      scope: "privacy",
      category: "privacy",
      actionSelector: '[data-tour="privacy-export"]',
      highlightSelector: '[data-tour="privacy-export"]',
      isAvailable: () =>
        isPrivacyRoute() && hasVisibleTarget('[data-tour="privacy-export"]'),
    },

    // —— Personalização ——
    {
      id: "sidebar-theme",
      title: "Personalizar tema",
      hint: "Claro, escuro ou automático.",
      steps: [
        "Clique em Tema no rodapé da sidebar.",
        "Escolha Claro, Escuro ou Sistema.",
        "A preferência fica salva neste navegador.",
      ],
      unlockHint: "Expanda a sidebar e feche o catálogo de apps.",
      scope: "sidebar",
      category: "personalization",
      actionSelector:
        '[data-tour="sidebar-theme"], [data-tour="sidebar-theme-menu"] .dropdown-item',
      highlightSelector: '[data-tour="sidebar-theme"]',
      isAvailable: () =>
        !isLauncherOpen() &&
        sidebarVisible() &&
        hasVisibleTarget('[data-tour="sidebar-theme"]'),
    },
  ];

  if (canAccessAdmin) {
    quests.push(
      {
        id: "sidebar-admin",
        title: "Entrar no Admin",
        hint: "Atalho para gestão da plataforma.",
        steps: [
          "Clique em Admin na sidebar.",
          "Gerencie usuários, apps, papéis e estatísticas.",
        ],
        unlockHint: "Expanda a sidebar — Admin fica acima do rodapé.",
        scope: "sidebar",
        category: "admin",
        actionSelector: '[data-tour="sidebar-admin"]',
        optional: true,
        isAvailable: () =>
          !isLauncherOpen() &&
          sidebarVisible() &&
          hasVisibleTarget('[data-tour="sidebar-admin"]'),
      },
      {
        id: "page-admin-users",
        title: "Usuários (RBAC)",
        hint: "Vínculos de acesso por pessoa.",
        steps: [
          "No Admin, abra a aba Usuários.",
          "Busque usuários e edite papéis/grupos.",
          "Use o modal de RBAC para ajustes finos.",
        ],
        unlockHint: "Sidebar → Admin → aba Usuários.",
        scope: "admin",
        category: "admin",
        actionSelector:
          '[data-tour="admin-nav-users"], .admin-mobile-menu button',
        highlightSelector: '[data-tour="admin-nav-users"], [data-tour="admin-mobile-nav"]',
        optional: true,
        isAvailable: () =>
          isAdminRoute() &&
          hasVisibleTarget(
            '[data-tour="admin-nav-users"], [data-tour="admin-mobile-nav"]',
          ),
      },
      {
        id: "page-admin-roles",
        title: "Papéis",
        hint: "Conjuntos de permissões reutilizáveis.",
        steps: [
          "No Admin, abra a aba Papéis.",
          "Crie ou edite papéis conforme a governança.",
          "Associe permissões a cada papel.",
        ],
        unlockHint: "Admin → aba Papéis.",
        scope: "admin",
        category: "admin",
        actionSelector: '[data-tour="admin-nav-roles"]',
        highlightSelector: '[data-tour="admin-nav-roles"]',
        optional: true,
        isAvailable: () =>
          isAdminRoute() && hasVisibleTarget('[data-tour="admin-nav-roles"]'),
      },
      {
        id: "page-admin-permissions",
        title: "Permissões",
        hint: "Catálogo fino de capacidades.",
        steps: [
          "No Admin, abra a aba Permissões.",
          "Consulte códigos e descrições.",
          "Use papéis para agrupar permissões aos usuários.",
        ],
        unlockHint: "Admin → aba Permissões.",
        scope: "admin",
        category: "admin",
        actionSelector: '[data-tour="admin-nav-permissions"]',
        highlightSelector: '[data-tour="admin-nav-permissions"]',
        optional: true,
        isAvailable: () =>
          isAdminRoute() &&
          hasVisibleTarget('[data-tour="admin-nav-permissions"]'),
      },
      {
        id: "page-admin-apps",
        title: "Aplicações (Admin)",
        hint: "Cadastro e manifestos de apps.",
        steps: [
          "No Admin, abra a aba Aplicações.",
          "Registre ou edite apps e rotas.",
          "Controle o que aparece no catálogo.",
        ],
        unlockHint: "Admin → aba Aplicações.",
        scope: "admin",
        category: "admin",
        actionSelector: '[data-tour="admin-nav-apps"]',
        highlightSelector: '[data-tour="admin-nav-apps"]',
        optional: true,
        isAvailable: () =>
          isAdminRoute() && hasVisibleTarget('[data-tour="admin-nav-apps"]'),
      },
      {
        id: "page-admin-stats-tour",
        title: "Acompanhamento do tour",
        hint: "Monitore exploradores nas estatísticas.",
        steps: [
          "No Admin, abra a aba Estatísticas.",
          "Clique em Acompanhamento no menu interno.",
          "Veja ranking e progresso dos exploradores.",
        ],
        unlockHint: "Admin → Estatísticas → Acompanhamento.",
        scope: "admin",
        category: "admin",
        actionSelector:
          '[data-tour="admin-stats-subnav-tour"], [data-tour="admin-stats-tour-page"]',
        highlightSelector: '[data-tour="admin-stats-subnav-tour"]',
        optional: true,
        isAvailable: () =>
          isAdminRoute() &&
          hasVisibleTarget(
            '[data-tour="admin-stats-subnav-tour"], [data-tour="admin-stats-tour-page"]',
          ),
      },
    );
  }

  return quests;
}

export function resolveQuestHighlightSelector(quest: PortalTourQuest) {
  if (quest.highlightSelector) return quest.highlightSelector;
  return quest.actionSelector.split(",")[0]?.trim() ?? quest.actionSelector;
}

export function isQuestAvailable(quest: PortalTourQuest) {
  return quest.isAvailable ? quest.isAvailable() : true;
}

export function countRequiredQuests(quests: PortalTourQuest[]) {
  return quests.filter((quest) => !quest.optional).length;
}

export function countCompletedRequired(
  quests: PortalTourQuest[],
  completedIds: ReadonlySet<string>,
) {
  return quests.filter(
    (quest) => !quest.optional && completedIds.has(quest.id),
  ).length;
}

export function groupQuestsByCategory(quests: PortalTourQuest[]) {
  const grouped = new Map<
    PortalTourQuestCategory,
    PortalTourQuest[]
  >();

  for (const quest of quests) {
    const list = grouped.get(quest.category) ?? [];
    list.push(quest);
    grouped.set(quest.category, list);
  }

  return grouped;
}
