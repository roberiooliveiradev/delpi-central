import { useMemo, type ReactNode } from "react";
import {
  Building2,
  ClipboardList,
  Cpu,
  Hammer,
  Home,
} from "lucide-react";

import {
  resolveMaintenanceNavPath,
  type MaintenanceNavId,
} from "../app/maintenanceNav";
import { MaintenanceTopBar, DM_PORTAL_SCOPE } from "../app/maintenanceUi";
import { FilialSwitcher } from "./FilialSwitcher";
import { MaintenanceShell } from "./MaintenanceShell";
import {
  resolveShellNavItems,
  SHELL_NAV_CONTENT,
  type ShellNavCapabilities,
} from "../content/shellNav";
import {
  TOP_BAR_COLLAPSE_MODE,
  TOP_BAR_COLLAPSE_STORAGE_KEY,
  TOP_BAR_COLLAPSE_TRIGGER,
} from "../content/topBarCollapseConfig";
import { useMaintenanceActiveFilial } from "../hooks/useMaintenanceScope";
import { resolveFilialDisplayName } from "../utils/maintenanceFilialSelection";
import { MAINTENANCE_ROUTES } from "../constants/routes";

type MaintenancePluginShellProps = {
  children: ReactNode;
  variant?: "default" | "embed";
  activeNavId: MaintenanceNavId;
  filialScope?: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (path: string) => void;
};

const NAV_ICONS: Record<MaintenanceNavId, ReactNode> = {
  home: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
  filiais: <Building2 size={16} strokeWidth={1.75} aria-hidden="true" />,
  "mini-aplicadores": <Hammer size={16} strokeWidth={1.75} aria-hidden="true" />,
  "programas-maquinas": <Cpu size={16} strokeWidth={1.75} aria-hidden="true" />,
  "manutencao-geral": <ClipboardList size={16} strokeWidth={1.75} aria-hidden="true" />,
};

function resolveShellCapabilities(
  canManageFiliais: boolean,
  submodules: Array<{ id: string }>,
): ShellNavCapabilities {
  const ids = new Set(submodules.map((item) => item.id));
  return {
    filiais: canManageFiliais,
    "mini-aplicadores": ids.has("mini-aplicadores"),
    "programas-maquinas": ids.has("programas-maquinas"),
    "manutencao-geral": ids.has("manutencao-geral"),
  };
}

export function MaintenancePluginShell({
  children,
  variant = "default",
  activeNavId,
  filialScope,
  getAccessToken,
  onNavigate,
}: MaintenancePluginShellProps) {
  const {
    filiais,
    activeFilial,
    setActiveFilial,
    loading: filialLoading,
    submodules,
    canManageFiliais,
  } = useMaintenanceActiveFilial(getAccessToken, filialScope);

  const capabilities = useMemo(
    () => resolveShellCapabilities(canManageFiliais, submodules),
    [canManageFiliais, submodules],
  );

  const navItems = useMemo(
    () => resolveShellNavItems(capabilities),
    [capabilities],
  );

  const showTopBar = variant !== "embed";

  const handleFilialChange = (filialId: string) => {
    setActiveFilial(filialId);
    if (activeNavId === "manutencao-geral") {
      onNavigate(MAINTENANCE_ROUTES.manutencaoGeral(filialId));
      return;
    }
    onNavigate(MAINTENANCE_ROUTES.filialHome(filialId));
  };

  const topBarActions =
    !filialLoading && filiais.length > 1 ? (
      <FilialSwitcher
        filiais={filiais.map((filial) => ({
          id: filial.id,
          label: resolveFilialDisplayName(filiais, filial.id),
        }))}
        value={activeFilial ?? filiais[0]?.id ?? ""}
        onChange={handleFilialChange}
        compact
      />
    ) : null;

  return (
    <MaintenanceShell variant={variant}>
      {showTopBar ? (
        <div className="dm-shell-chrome">
          <MaintenanceTopBar
            aria-label={SHELL_NAV_CONTENT.ariaLabel}
            activeId={activeNavId}
            collapsible
            collapseMode={TOP_BAR_COLLAPSE_MODE}
            collapseTrigger={TOP_BAR_COLLAPSE_TRIGGER}
            storageKey={
              TOP_BAR_COLLAPSE_TRIGGER === "manual" ? TOP_BAR_COLLAPSE_STORAGE_KEY : undefined
            }
            collapseLabel={SHELL_NAV_CONTENT.collapseLabel}
            expandLabel={SHELL_NAV_CONTENT.expandLabel}
            menuLabel={SHELL_NAV_CONTENT.menuLabel}
            portalScopeClassName={DM_PORTAL_SCOPE}
            items={navItems.map((item) => ({
              id: item.id,
              label: item.label,
              icon: NAV_ICONS[item.id],
              title: item.label,
              onSelect: () => onNavigate(resolveMaintenanceNavPath(item.id, filialScope ?? activeFilial)),
            }))}
            actions={topBarActions}
          />
          {children}
        </div>
      ) : (
        children
      )}
    </MaintenanceShell>
  );
}
