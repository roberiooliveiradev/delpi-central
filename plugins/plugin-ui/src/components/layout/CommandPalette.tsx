import {
  useEffect,
  useMemo,
  useRef,
  type RefObject,
} from "react";

import {
  CatalogSearchBar,
  catalogSearchBarBemClasses,
  type CatalogSearchBarClassNames,
  type CatalogSearchHit,
} from "./CatalogSearchBar";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type CommandPaletteClassNames = {
  panel: string;
  header: string;
  search: CatalogSearchBarClassNames;
  body: string;
};

export type CommandPaletteProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  /** Âncora do pill/trigger na TopBar (obrigatório para o popover). */
  anchorRef: RefObject<HTMLElement | null>;
  value: string;
  onChange: (value: string) => void;
  hits?: readonly CatalogSearchHit[];
  onSelectHit: (id: string) => void;
  placeholder?: string;
  emptyHitsLabel?: string;
  clearLabel?: string;
  classNames: CommandPaletteClassNames;
  portalScopeClassName?: string;
  "aria-label"?: string;
};

export function commandPaletteBemClasses(prefix: string): CommandPaletteClassNames {
  const base = `${prefix}-command-palette`;
  const ui = "delpi-ui-command-palette";
  return {
    panel: delpiUiClass(base, ui),
    header: delpiUiClass(`${base}__header`, `${ui}__header`),
    search: catalogSearchBarBemClasses(prefix),
    body: delpiUiClass(`${base}__body`, `${ui}__body`),
  };
}

/**
 * Command palette (Ctrl+K) — popover ancorado via AnchoredPanelPortal.
 * Atalho e âncora ficam no shell do MFE.
 */
export function CommandPalette({
  open,
  onClose,
  title,
  anchorRef,
  value,
  onChange,
  hits = [],
  onSelectHit,
  placeholder,
  emptyHitsLabel,
  clearLabel,
  classNames,
  portalScopeClassName,
  "aria-label": ariaLabel,
}: CommandPaletteProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const frame = window.requestAnimationFrame(() => {
      const input = panelRef.current?.querySelector<HTMLInputElement>(
        "input[type='search'], input",
      );
      input?.focus();
      input?.select();
    });
    return () => window.cancelAnimationFrame(frame);
  }, [open]);

  const handleSelect = (id: string) => {
    onSelectHit(id);
    onClose();
  };

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      className={classNames.panel}
      variant="bare"
      role="dialog"
      aria-label={ariaLabel ?? title}
      preferredPlacement="bottom"
      horizontalAlign="end"
      gap={6}
      portalScopeClassName={portalScopeClassName}
      onDismiss={onClose}
    >
      <div className={classNames.body}>
        <div className={classNames.header}>{title}</div>
        <CatalogSearchBar
          classNames={classNames.search}
          value={value}
          onChange={onChange}
          hits={hits}
          onSelectHit={handleSelect}
          placeholder={placeholder}
          emptyHitsLabel={emptyHitsLabel}
          clearLabel={clearLabel}
          aria-label={ariaLabel ?? placeholder ?? title}
        />
      </div>
    </AnchoredPanelPortal>
  );
}

export type DashboardCommandPaletteProps = Omit<CommandPaletteProps, "classNames">;

export function createDashboardCommandPalette(config: {
  prefix: string;
  portalScopeClassName: string;
}) {
  const classNames = commandPaletteBemClasses(config.prefix);

  return function DashboardCommandPalette(props: DashboardCommandPaletteProps) {
    const merged = useMemo(() => classNames, []);
    return (
      <CommandPalette
        {...props}
        classNames={merged}
        portalScopeClassName={props.portalScopeClassName ?? config.portalScopeClassName}
      />
    );
  };
}

export type { CatalogSearchHit };
