import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  CalendarCheck,
  FolderKanban,
  Home,
  MessagesSquare,
} from "lucide-react";
import {
  CommandPalette,
  TopBar,
  TopBarSearchTrigger,
  TopBarUtilityCluster,
  commandPaletteBemClasses,
  topBarBemClasses,
  topBarSearchTriggerBemClasses,
  topBarUtilityClusterBemClasses,
  underlineNavBemClasses,
} from "@delpi/plugin-ui/index";

import {
  filterPortalCatalog,
  isPortalSearchShortcut,
  resolvePortalTopBarId,
  visiblePortalTopBarItems,
} from "../constants/portalExperience";
import { PortalFavoritesTrigger } from "./PortalFavoritesTrigger";
import { PortalTopBarUserIdentity } from "./PortalTopBarUserIdentity";
import { useCanManagePortal } from "../state/portalChrome";

type PortalTopBarProps = {
  currentPath?: string;
  onNavigate: (path: string) => void;
};

const TOPBAR = topBarBemClasses("ds");
const NAV = underlineNavBemClasses("ds");
const SEARCH = topBarSearchTriggerBemClasses("ds");
const UTILITY = topBarUtilityClusterBemClasses("ds");
const PALETTE = commandPaletteBemClasses("ds");

const ICON_PROPS = { size: 16, strokeWidth: 1.75, "aria-hidden": true as const };

/** Ícones alinhados ao padrão do portal Comercial (lucide 16 / 1.75). */
const PORTAL_TOPBAR_ICONS: Record<string, ReactNode> = {
  home: <Home {...ICON_PROPS} />,
  overview: <BarChart3 {...ICON_PROPS} />,
  interaction: <MessagesSquare {...ICON_PROPS} />,
  tasks: <CalendarCheck {...ICON_PROPS} />,
  processes: <FolderKanban {...ICON_PROPS} />,
  administration: <BriefcaseBusiness {...ICON_PROPS} />,
  help: <BookOpen {...ICON_PROPS} />,
};

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

export function PortalTopBar({ currentPath, onNavigate }: PortalTopBarProps) {
  const searchRef = useRef<HTMLButtonElement>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [query, setQuery] = useState("");
  const activeId = resolvePortalTopBarId(currentPath);
  const canManage = useCanManagePortal();
  const items = visiblePortalTopBarItems(canManage);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const chord = isPortalSearchShortcut(event);
      if (!chord) return;
      if (isEditableTarget(event.target) && !paletteOpen) return;
      event.preventDefault();
      setPaletteOpen((open) => !open);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [paletteOpen]);

  return (
    <>
      <TopBar
        classNames={TOPBAR}
        navClassNames={NAV}
        items={items.map((item) => ({
          id: item.id,
          label: item.label,
          icon: PORTAL_TOPBAR_ICONS[item.id],
          onSelect: () => onNavigate(item.path),
        }))}
        activeId={activeId}
        aria-label="Navegação do Portal Transforma+"
        collapsible
        menuLabel="Menu do Portal Transforma+"
        portalScopeClassName="dashboard-transformometro"
        secondary={
          <TopBarUtilityCluster classNames={UTILITY}>
            <TopBarSearchTrigger
              ref={searchRef}
              classNames={SEARCH}
              onOpen={() => setPaletteOpen(true)}
              expanded={paletteOpen}
              label="Buscar"
              shortcutLabel="Ctrl+K"
              aria-label="Buscar caminhos e funcionalidades"
              title="Buscar caminhos e funcionalidades (Ctrl+K)"
            />
            <PortalFavoritesTrigger onNavigate={onNavigate} />
          </TopBarUtilityCluster>
        }
        actions={<PortalTopBarUserIdentity />}
      />
      <CommandPalette
        classNames={PALETTE}
        portalScopeClassName="dashboard-transformometro"
        open={paletteOpen}
        anchorRef={searchRef}
        title="Caminhos e funcionalidades"
        value={query}
        onChange={setQuery}
        placeholder="Buscar caminhos e funcionalidades…"
        emptyHitsLabel="Nenhuma funcionalidade encontrada."
        clearLabel="Limpar busca"
        hits={filterPortalCatalog(query, { includeAdministration: canManage }).map((item) => ({
          id: item.path,
          label: item.label,
          groupLabel: item.group,
        }))}
        onSelectHit={(path) => {
          setQuery("");
          onNavigate(path);
        }}
        onClose={() => setPaletteOpen(false)}
      />
    </>
  );
}
