import type { ReactNode } from "react";
import {
  AppWindow,
  Briefcase,
  ClipboardList,
  FileText,
  FolderKanban,
  LayoutDashboard,
  Package,
  Shield,
  Target,
  Timer,
  Users,
  UsersRound,
} from "lucide-react";

import type { PluginNavigationTarget } from "../app/pluginRoutes";

const ICON_PROPS = { size: 14, strokeWidth: 1.75, "aria-hidden": true as const };

const BY_VIEW: Partial<Record<PluginNavigationTarget, ReactNode>> = {
  my_tasks: <ClipboardList {...ICON_PROPS} />,
  open_orders: <Package {...ICON_PROPS} />,
  customers: <Briefcase {...ICON_PROPS} />,
  overview: <LayoutDashboard {...ICON_PROPS} />,
  analytics_otd: <Timer {...ICON_PROPS} />,
  analytics_opportunities: <Target {...ICON_PROPS} />,
  proposals: <FileText {...ICON_PROPS} />,
  administration: <Shield {...ICON_PROPS} />,
  administration_portfolios: <FolderKanban {...ICON_PROPS} />,
  administration_team: <Users {...ICON_PROPS} />,
  administration_groups: <UsersRound {...ICON_PROPS} />,
};

/** Ícone Lucide por viewId do hub (chips recentes / catálogo). */
export function resolveHubRouteIcon(viewId: PluginNavigationTarget): ReactNode {
  return BY_VIEW[viewId] ?? <AppWindow {...ICON_PROPS} />;
}
