import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  ClipboardList,
  Home,
  Package,
  ShoppingCart,
} from "lucide-react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import { SP_HELP } from "../content/helpTooltips";
import {
  collectSearchHits,
  findHubRouteById,
  HUB_CONTENT,
  resolveHubSections,
} from "../content/pluginRouteCatalog";
import { resolveShellNavItems, SHELL_NAV_CONTENT } from "../content/shellNav";
import { navigatePluginView } from "./pluginNavigation";
import { resolveActiveNavId, type PluginNavId, type PluginView } from "./pluginRoutes";
import { useSuppliesSession } from "./SuppliesSessionContext";
import { SP_PORTAL_SCOPE, SuppliesCommandPalette, SuppliesTopBar, SuppliesViewTransition } from "./suppliesUi";

type PluginShellProps = {
  view: PluginView;
  basePath: string;
  children: ReactNode;
};

const NAV_HELP: Partial<Record<PluginNavId, string>> = {
  home: SP_HELP.shell.navHome,
  overview: SP_HELP.shell.navOverview,
  my_tasks: SP_HELP.shell.navMyTasks,
  purchase_requests: SP_HELP.shell.navPurchaseRequests,
  operations: SP_HELP.shell.navOperations,
  administration: SP_HELP.shell.navAdmin,
  help: SP_HELP.shell.navHelp,
};

const NAV_ICONS: Record<PluginNavId, ReactNode> = {
  home: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
  overview: <BarChart3 size={16} strokeWidth={1.75} aria-hidden="true" />,
  my_tasks: <ClipboardList size={16} strokeWidth={1.75} aria-hidden="true" />,
  purchase_requests: <ShoppingCart size={16} strokeWidth={1.75} aria-hidden="true" />,
  operations: <Package size={16} strokeWidth={1.75} aria-hidden="true" />,
  administration: <BriefcaseBusiness size={16} strokeWidth={1.75} aria-hidden="true" />,
  help: <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />,
};

const NAV_TARGET: Record<PluginNavId, Parameters<typeof navigatePluginView>[0]> = {
  home: "home",
  overview: "overview",
  my_tasks: "my_tasks",
  purchase_requests: "purchase_requests",
  operations: "purchase_orders",
  administration: "administration",
  help: "help",
};

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

export function PluginShell({ view, basePath, children }: PluginShellProps) {
  const session = useSuppliesSession();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isPaletteChord =
        (event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey);
      if (!isPaletteChord) return;
      if (isEditableTarget(event.target) && !paletteOpen) return;
      event.preventDefault();
      setPaletteOpen((open) => !open);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [paletteOpen]);

  const caps = session.capabilities;
  const items = resolveShellNavItems({
    analytics: caps.analytics,
    purchaseRequests: caps.purchaseRequests,
    operations: caps.operations,
    administration: caps.administration,
  });

  const catalogCaps = useMemo(
    () => ({
      analytics: caps.analytics,
      purchaseRequests: caps.purchaseRequests,
      operations: caps.operations,
      administration: caps.administration,
    }),
    [caps.administration, caps.analytics, caps.operations, caps.purchaseRequests],
  );

  const paletteSections = useMemo(() => resolveHubSections(catalogCaps), [catalogCaps]);
  const paletteHits = useMemo(
    () => collectSearchHits(paletteSections, paletteQuery, 8),
    [paletteQuery, paletteSections],
  );

  const onSelectPaletteHit = useCallback(
    (routeId: string) => {
      const route = findHubRouteById(paletteSections, routeId);
      if (!route) return;
      navigatePluginView(route.viewId, { basePath });
      setPaletteOpen(false);
      setPaletteQuery("");
    },
    [basePath, paletteSections],
  );

  const activeId = resolveActiveNavId(view);
  const density = session.preferences?.tableDensity ?? "comfortable";

  return (
    <div
      className="dashboard-supplies-portal dashboard-page"
      data-table-density={density}
    >
      <div className="sp-page-stack">
        <SuppliesTopBar
          aria-label={SHELL_NAV_CONTENT.ariaLabel}
          activeId={activeId ?? ""}
          collapsible
          collapseLabel={SHELL_NAV_CONTENT.collapseLabel}
          expandLabel={SHELL_NAV_CONTENT.expandLabel}
          menuLabel={SHELL_NAV_CONTENT.menuLabel}
          portalScopeClassName={SP_PORTAL_SCOPE}
          items={items.map((item) => ({
            id: item.id,
            label: item.label,
            icon: NAV_ICONS[item.id],
            title: NAV_HELP[item.id]
              ? `${item.label}. ${NAV_HELP[item.id]}`
              : item.label,
            onSelect: () => navigatePluginView(NAV_TARGET[item.id], { basePath }),
          }))}
          actions={
            <HelpTooltip content={SP_HELP.coexistence} ariaLabel="Ajuda: Portal vs apps antigos" />
          }
        />
        <SuppliesViewTransition transitionKey={view} tone="page">
          {children}
        </SuppliesViewTransition>
      </div>

      <SuppliesCommandPalette
        open={paletteOpen}
        onClose={() => {
          setPaletteOpen(false);
          setPaletteQuery("");
        }}
        title={HUB_CONTENT.palette.title}
        value={paletteQuery}
        onChange={setPaletteQuery}
        hits={paletteHits.map((hit) => ({
          id: hit.id,
          label: hit.label,
          groupLabel: hit.groupLabel,
        }))}
        onSelectHit={onSelectPaletteHit}
        placeholder={HUB_CONTENT.palette.placeholder}
        emptyHitsLabel={HUB_CONTENT.palette.empty}
        closeAriaLabel={HUB_CONTENT.palette.closeAriaLabel}
        aria-label="Busca do Portal Suprimentos"
      />
    </div>
  );
}
