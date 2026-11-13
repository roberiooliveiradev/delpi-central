import { AppWindow, BookOpen, ClipboardList, Database, LayoutDashboard, Network, Server, Monitor, Workflow } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { SHELL_CONTENT } from "../content/labels";
import {
  ITP_PORTAL_SCOPE,
  ItpCommandPalette,
  ItpTopBar,
  ItpTopBarSearchTrigger,
  ItpTopBarUserIdentity,
  ItpTopBarUtilityCluster,
} from "./itPortalUi";
import { navigateTo } from "./navigation";
import { usePortal } from "./PortalContext";
import { activeNavId, buildPath, type NavId, type PluginView } from "./routes";

const NAV_ICONS: Record<NavId, ReactNode> = {
  home: <LayoutDashboard size={16} strokeWidth={1.75} aria-hidden="true" />,
  workstations: <Monitor size={16} strokeWidth={1.75} aria-hidden="true" />,
  servers: <Server size={16} strokeWidth={1.75} aria-hidden="true" />,
  services: <AppWindow size={16} strokeWidth={1.75} aria-hidden="true" />,
  databases: <Database size={16} strokeWidth={1.75} aria-hidden="true" />,
  networks: <Network size={16} strokeWidth={1.75} aria-hidden="true" />,
  integrations: <Workflow size={16} strokeWidth={1.75} aria-hidden="true" />,
  action_plans: <ClipboardList size={16} strokeWidth={1.75} aria-hidden="true" />,
  help: <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />,
};

const ShellSearchContext = createContext<{ openPalette: () => void }>({
  openPalette: () => undefined,
});

/** Abre a mesma CommandPalette da TopBar (usado pela busca do hero da Home). */
export function useShellSearch(): { openPalette: () => void } {
  return useContext(ShellSearchContext);
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  return ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
}

export function PluginShell({ view, children }: { view: PluginView; children: ReactNode }) {
  const { basePath, capabilities } = usePortal();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const searchTriggerRef = useRef<HTMLButtonElement>(null);

  const navIds = useMemo<NavId[]>(() => {
    if (!capabilities) return [];
    const ids: NavId[] = ["home"];
    if (capabilities.can_view_computers) ids.push("workstations");
    if (capabilities.can_view_servers) ids.push("servers");
    if (capabilities.can_view_services) ids.push("services");
    if (capabilities.can_view_databases) ids.push("databases");
    if (capabilities.can_view_networks) ids.push("networks");
    if (capabilities.can_view_integrations) ids.push("integrations");
    if (capabilities.can_view_action_plans) ids.push("action_plans");
    ids.push("help");
    return ids;
  }, [capabilities]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const chord = (event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey);
      if (!chord || navIds.length === 0) return;
      if (isEditableTarget(event.target) && !paletteOpen) return;
      event.preventDefault();
      setPaletteOpen((open) => !open);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [paletteOpen, navIds.length]);

  const hits = useMemo(() => {
    const needle = paletteQuery.trim().toLocaleLowerCase("pt-BR");
    return navIds
      .filter((id) => {
        if (!needle) return true;
        const haystack = `${SHELL_CONTENT.nav[id]} ${SHELL_CONTENT.navHints[id]}`.toLocaleLowerCase("pt-BR");
        return haystack.includes(needle);
      })
      .map((id) => ({ id, label: SHELL_CONTENT.nav[id], groupLabel: SHELL_CONTENT.search.group }));
  }, [navIds, paletteQuery]);

  const closePalette = useCallback(() => {
    setPaletteOpen(false);
    setPaletteQuery("");
  }, []);

  const openPalette = useCallback(() => {
    if (navIds.length > 0) setPaletteOpen(true);
  }, [navIds.length]);

  return (
    <div className={`${ITP_PORTAL_SCOPE} dashboard-page`}>
      <ShellSearchContext.Provider value={{ openPalette }}>
        <div className="itp-page-stack">
        <ItpTopBar
          aria-label={SHELL_CONTENT.navAriaLabel}
          activeId={activeNavId(view) ?? ""}
          collapsible
          collapseMode="hamburger"
          collapseTrigger="overflow"
          collapseLabel={SHELL_CONTENT.collapseLabel}
          expandLabel={SHELL_CONTENT.expandLabel}
          menuLabel={SHELL_CONTENT.menuLabel}
          portalScopeClassName={ITP_PORTAL_SCOPE}
          items={navIds.map((id) => ({
            id,
            label: SHELL_CONTENT.nav[id],
            icon: NAV_ICONS[id],
            title: `${SHELL_CONTENT.nav[id]}. ${SHELL_CONTENT.navHints[id]}`,
            onSelect: () => navigateTo(buildPath(basePath, id)),
          }))}
          secondary={
            navIds.length > 0 ? (
              <ItpTopBarUtilityCluster>
                <ItpTopBarSearchTrigger
                  ref={searchTriggerRef}
                  onOpen={() => setPaletteOpen(true)}
                  expanded={paletteOpen}
                  label={SHELL_CONTENT.search.label}
                  shortcutLabel={SHELL_CONTENT.search.shortcut}
                  aria-label={SHELL_CONTENT.search.ariaLabel}
                  title={SHELL_CONTENT.search.title}
                />
              </ItpTopBarUtilityCluster>
            ) : undefined
          }
          actions={
            <ItpTopBarUserIdentity
              displayName={capabilities?.display_name ?? null}
              avatarHref="/profile"
              avatarTitle="Abrir Meu Perfil na Minha DELPI"
              fallbackLabel={SHELL_CONTENT.userFallback}
              portalScopeClassName={ITP_PORTAL_SCOPE}
            />
          }
        />
          {children}
        </div>
      </ShellSearchContext.Provider>

      <ItpCommandPalette
        open={paletteOpen && navIds.length > 0}
        onClose={closePalette}
        anchorRef={searchTriggerRef}
        title={SHELL_CONTENT.search.paletteTitle}
        value={paletteQuery}
        onChange={setPaletteQuery}
        hits={hits}
        onSelectHit={(id) => {
          navigateTo(buildPath(basePath, id as NavId));
          closePalette();
        }}
        placeholder={SHELL_CONTENT.search.placeholder}
        emptyHitsLabel={SHELL_CONTENT.search.empty}
        aria-label={SHELL_CONTENT.search.ariaLabel}
      />
    </div>
  );
}
