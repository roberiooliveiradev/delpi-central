import { MAINTENANCE_ROUTES } from "../constants/routes";
import {
  MINI_APLICADORES_NAV_CONTENT,
  SUBMODULE_BACK_NAV_CONTENT,
  type MiniAplicadoresNavTabId,
} from "../content/miniAplicadoresNav";
import {
  normalizeMaintenancePath,
  RESERVED_MINI_SEGMENTS,
  resolveMaintenanceHomePath,
  type MaintenanceView,
} from "../utils/routeParser";

export type MaintenanceShellChromeMode = "none" | "mini-aplicadores" | "submodule-back";

export type ShellChromeNavItem = {
  id: string;
  label: string;
  path: string;
};

export type MaintenanceShellChrome = {
  mode: MaintenanceShellChromeMode;
  showTopBar: boolean;
  activeId: string;
  ariaLabel: string;
  items: ShellChromeNavItem[];
};

function isMiniAplicadoresView(view: MaintenanceView): boolean {
  return (
    view === "mini-aplicadores" ||
    view === "mini-aplicador" ||
    view === "relatorio" ||
    view === "configuracao"
  );
}

function isSubmoduleBackView(view: MaintenanceView): boolean {
  return view === "filiais" || view === "programas-maquinas" || view === "manutencao-geral";
}

export function resolveMiniAplicadoresActiveId(
  view: MaintenanceView,
  pathname: string,
): MiniAplicadoresNavTabId {
  if (view === "relatorio") {
    return MINI_APLICADORES_NAV_CONTENT.relatorio.id;
  }
  if (view === "configuracao") {
    return MINI_APLICADORES_NAV_CONTENT.configuracao.id;
  }

  const path = normalizeMaintenancePath(pathname);
  if (path === MINI_APLICADORES_NAV_CONTENT.relatorio.path) {
    return MINI_APLICADORES_NAV_CONTENT.relatorio.id;
  }
  if (path === MINI_APLICADORES_NAV_CONTENT.configuracao.path) {
    return MINI_APLICADORES_NAV_CONTENT.configuracao.id;
  }

  return MINI_APLICADORES_NAV_CONTENT.ferramentas.id;
}

export function isMiniAplicadoresFerramentasPath(pathname: string): boolean {
  const path = normalizeMaintenancePath(pathname);
  if (path === MAINTENANCE_ROUTES.miniAplicadores) {
    return true;
  }
  const detailMatch = path.match(/^\/apps\/maintenance\/mini-aplicadores\/([^/]+)$/);
  return Boolean(detailMatch && !RESERVED_MINI_SEGMENTS.has(detailMatch[1]));
}

export function resolveMaintenanceShellChrome(params: {
  view: MaintenanceView;
  pathname: string;
  filialScope?: string;
  showConfiguration: boolean;
}): MaintenanceShellChrome {
  const { view, pathname, filialScope, showConfiguration } = params;
  const hubPath = resolveMaintenanceHomePath(filialScope);

  if (view === "home") {
    return {
      mode: "none",
      showTopBar: false,
      activeId: MINI_APLICADORES_NAV_CONTENT.home.id,
      ariaLabel: SUBMODULE_BACK_NAV_CONTENT.ariaLabel,
      items: [],
    };
  }

  if (isMiniAplicadoresView(view)) {
    const tabs: ShellChromeNavItem[] = [
      {
        id: MINI_APLICADORES_NAV_CONTENT.home.id,
        label: MINI_APLICADORES_NAV_CONTENT.home.label,
        path: hubPath,
      },
      {
        id: MINI_APLICADORES_NAV_CONTENT.ferramentas.id,
        label: MINI_APLICADORES_NAV_CONTENT.ferramentas.label,
        path: MINI_APLICADORES_NAV_CONTENT.ferramentas.path,
      },
      {
        id: MINI_APLICADORES_NAV_CONTENT.relatorio.id,
        label: MINI_APLICADORES_NAV_CONTENT.relatorio.label,
        path: MINI_APLICADORES_NAV_CONTENT.relatorio.path,
      },
    ];

    if (showConfiguration) {
      tabs.push({
        id: MINI_APLICADORES_NAV_CONTENT.configuracao.id,
        label: MINI_APLICADORES_NAV_CONTENT.configuracao.label,
        path: MINI_APLICADORES_NAV_CONTENT.configuracao.path,
      });
    }

    return {
      mode: "mini-aplicadores",
      showTopBar: true,
      activeId: resolveMiniAplicadoresActiveId(view, pathname),
      ariaLabel: MINI_APLICADORES_NAV_CONTENT.ariaLabel,
      items: tabs,
    };
  }

  if (isSubmoduleBackView(view)) {
    return {
      mode: "submodule-back",
      showTopBar: true,
      activeId: SUBMODULE_BACK_NAV_CONTENT.home.id,
      ariaLabel: SUBMODULE_BACK_NAV_CONTENT.ariaLabel,
      items: [
        {
          id: SUBMODULE_BACK_NAV_CONTENT.home.id,
          label: SUBMODULE_BACK_NAV_CONTENT.home.label,
          path: hubPath,
        },
      ],
    };
  }

  return {
    mode: "none",
    showTopBar: false,
    activeId: MINI_APLICADORES_NAV_CONTENT.home.id,
    ariaLabel: SUBMODULE_BACK_NAV_CONTENT.ariaLabel,
    items: [],
  };
}
