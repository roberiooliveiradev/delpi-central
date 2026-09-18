import { useEffect, useRef, useState } from "react";
import {
  CommandPalette,
  TopBar,
  TopBarSearchTrigger,
  commandPaletteBemClasses,
  topBarBemClasses,
  topBarSearchTriggerBemClasses,
  underlineNavBemClasses,
} from "@delpi/plugin-ui/index";

import {
  PORTAL_TOPBAR_ITEMS,
  filterPortalCatalog,
  resolvePortalTopBarId,
} from "../constants/portalExperience";
import { useCanManagePortal } from "../state/portalChrome";

type PortalTopBarProps = {
  currentPath?: string;
  onNavigate: (path: string) => void;
};

const TOPBAR = topBarBemClasses("ds");
const NAV = underlineNavBemClasses("ds");
const SEARCH = topBarSearchTriggerBemClasses("ds");
const PALETTE = commandPaletteBemClasses("ds");

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
  const items = PORTAL_TOPBAR_ITEMS.filter(
    (item) => canManage || item.id !== "administration",
  );

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const chord = (event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey);
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
          onSelect: () => onNavigate(item.path),
        }))}
        activeId={activeId}
        aria-label="Navegação do Portal Transforma+"
        collapsible
        menuLabel="Menu do Portal Transforma+"
        portalScopeClassName="dashboard-transformometro"
        secondary={
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
        }
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
