import { useMemo, type ReactNode } from "react";
import { ClipboardList, Cpu, Hammer, Home, LineChart, Settings } from "lucide-react";

import { resolveMaintenanceShellChrome } from "../app/maintenanceShellChrome";
import { MaintenanceTopBar, DM_PORTAL_SCOPE } from "../app/maintenanceUi";
import { FilialSwitcher } from "./FilialSwitcher";
import { MaintenanceShell } from "./MaintenanceShell";
import {
  TOP_BAR_COLLAPSE_MODE,
  TOP_BAR_COLLAPSE_STORAGE_KEY,
  TOP_BAR_COLLAPSE_TRIGGER,
} from "../content/topBarCollapseConfig";
import { useMaintenanceActiveFilial } from "../hooks/useMaintenanceScope";
import { resolveFilialDisplayName } from "../utils/maintenanceFilialSelection";
import { MAINTENANCE_ROUTES } from "../constants/routes";
import type { MaintenanceView } from "../utils/routeParser";

type MaintenancePluginShellProps = {
  children: ReactNode;
  variant?: "default" | "embed";
  routeView: MaintenanceView;
  pathname: string;
  filialScope?: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (path: string) => void;
};

const TOP_BAR_ICONS: Record<string, ReactNode> = {
  home: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
  ferramentas: <Hammer size={16} strokeWidth={1.75} aria-hidden="true" />,
  relatorio: <LineChart size={16} strokeWidth={1.75} aria-hidden="true" />,
  configuracao: <Settings size={16} strokeWidth={1.75} aria-hidden="true" />,
  filiais: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
  "programas-maquinas": <Cpu size={16} strokeWidth={1.75} aria-hidden="true" />,
  "manutencao-geral": <ClipboardList size={16} strokeWidth={1.75} aria-hidden="true" />,
};

export function MaintenancePluginShell({
  children,
  variant = "default",
  routeView,
  pathname,
  filialScope,
  getAccessToken,
  onNavigate,
}: MaintenancePluginShellProps) {
  const {
    filiais,
    activeFilial,
    setActiveFilial,
    loading: filialLoading,
    canManageMiniApplicators,
  } = useMaintenanceActiveFilial(getAccessToken, filialScope);

  const shellChrome = useMemo(
    () =>
      resolveMaintenanceShellChrome({
        view: routeView,
        pathname,
        filialScope,
        showConfiguration: canManageMiniApplicators,
      }),
    [canManageMiniApplicators, filialScope, pathname, routeView],
  );

  const showTopBar = variant !== "embed" && shellChrome.showTopBar;

  const handleFilialChange = (filialId: string) => {
    setActiveFilial(filialId);
    if (routeView === "manutencao-geral") {
      onNavigate(MAINTENANCE_ROUTES.manutencaoGeral(filialId));
      return;
    }
    onNavigate(MAINTENANCE_ROUTES.filialHome(filialId));
  };

  const topBarActions =
    showTopBar && !filialLoading && filiais.length > 1 ? (
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

  const topBarItems = useMemo(
    () =>
      shellChrome.items.map((item) => ({
        id: item.id,
        label: item.label,
        icon: TOP_BAR_ICONS[item.id] ?? TOP_BAR_ICONS.home,
        title: item.label,
        onSelect: () => onNavigate(item.path),
      })),
    [onNavigate, shellChrome.items],
  );

  return (
    <MaintenanceShell variant={variant}>
      {showTopBar ? (
        <div className="dm-shell-chrome">
          <MaintenanceTopBar
            aria-label={shellChrome.ariaLabel}
            activeId={shellChrome.activeId}
            collapsible
            collapseMode={TOP_BAR_COLLAPSE_MODE}
            collapseTrigger={TOP_BAR_COLLAPSE_TRIGGER}
            storageKey={
              TOP_BAR_COLLAPSE_TRIGGER === "manual" ? TOP_BAR_COLLAPSE_STORAGE_KEY : undefined
            }
            collapseLabel="Recolher navegação"
            expandLabel="Expandir navegação"
            menuLabel="Menu de navegação"
            portalScopeClassName={DM_PORTAL_SCOPE}
            items={topBarItems}
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
