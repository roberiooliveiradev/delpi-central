import { useEffect, useMemo, type ComponentType } from "react";

import {
  CatalogSearchBar,
  catalogSearchBarBemClasses,
  type CatalogSearchBarClassNames,
  type CatalogSearchHit,
} from "./CatalogSearchBar";
import {
  ModalShell,
  createHostContainedModalShell,
  modalShellBemClasses,
  type DashboardModalShellProps,
  type ModalShellClassNames,
} from "../feedback/ModalShell";

export type CommandPaletteClassNames = {
  modal: ModalShellClassNames;
  search: CatalogSearchBarClassNames;
  body: string;
};

export type CommandPaletteProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  value: string;
  onChange: (value: string) => void;
  hits?: readonly CatalogSearchHit[];
  onSelectHit: (id: string) => void;
  placeholder?: string;
  emptyHitsLabel?: string;
  clearLabel?: string;
  closeAriaLabel?: string;
  classNames: CommandPaletteClassNames;
  /** Injected host-contained modal (preferred). Falls back to ModalShell + portal props. */
  Modal?: ComponentType<DashboardModalShellProps>;
  portalScopeClassName?: string;
  portalTarget?: Element | null;
  "aria-label"?: string;
};

export function commandPaletteBemClasses(prefix: string): CommandPaletteClassNames {
  return {
    modal: modalShellBemClasses(prefix),
    search: catalogSearchBarBemClasses(prefix),
    body: `${prefix}-command-palette__body delpi-ui-command-palette__body`,
  };
}

/**
 * Command palette (Ctrl+K). Atalho fica no shell do MFE.
 * Preferir `createDashboardCommandPalette` com host contained.
 */
export function CommandPalette({
  open,
  onClose,
  title,
  value,
  onChange,
  hits = [],
  onSelectHit,
  placeholder,
  emptyHitsLabel,
  clearLabel,
  closeAriaLabel,
  classNames,
  Modal,
  portalScopeClassName,
  portalTarget,
  "aria-label": ariaLabel,
}: CommandPaletteProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [open, onClose]);

  const handleSelect = (id: string) => {
    onSelectHit(id);
    onClose();
  };

  const body = (
    <div className={classNames.body}>
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
  );

  if (Modal) {
    return (
      <Modal
        open={open}
        title={title}
        onClose={onClose}
        closeAriaLabel={closeAriaLabel}
        initialFocusSelector="input[type='search'], input"
        containedLayout="dialog"
      >
        {body}
      </Modal>
    );
  }

  return (
    <ModalShell
      open={open}
      title={title}
      onClose={onClose}
      classNames={classNames.modal}
      closeAriaLabel={closeAriaLabel}
      initialFocusSelector="input[type='search'], input"
      portalScopeClassName={portalScopeClassName}
      portalTarget={portalTarget}
      containedInPortalTarget={Boolean(portalScopeClassName || portalTarget)}
      containedLayout="dialog"
    >
      {body}
    </ModalShell>
  );
}

export type DashboardCommandPaletteProps = Omit<CommandPaletteProps, "classNames" | "Modal">;

export function createDashboardCommandPalette(config: {
  prefix: string;
  portalScopeClassName: string;
  closeAriaLabel?: string;
}) {
  const classNames = commandPaletteBemClasses(config.prefix);
  const Modal = createHostContainedModalShell({
    prefix: config.prefix,
    portalScopeClassName: config.portalScopeClassName,
    containedLayout: "dialog",
    closeAriaLabel: config.closeAriaLabel,
  });

  return function DashboardCommandPalette(props: DashboardCommandPaletteProps) {
    const merged = useMemo(() => classNames, []);
    return (
      <CommandPalette
        {...props}
        classNames={merged}
        Modal={Modal}
        closeAriaLabel={props.closeAriaLabel ?? config.closeAriaLabel}
      />
    );
  };
}

export type { CatalogSearchHit };
