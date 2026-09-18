import { useRef, useState } from "react";
import { Star, X } from "lucide-react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { ContextMenuItem } from "../menu/ContextMenuItem";

export type TopBarFavoritesItem = {
  id: string;
  label: string;
};

export type TopBarFavoritesStripClassNames = {
  root: string;
  trigger: string;
  triggerIcon: string;
  triggerLabel: string;
  panel: string;
  status: string;
  row: string;
  remove: string;
};

export type TopBarFavoritesStripProps = {
  items: readonly TopBarFavoritesItem[];
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
  title: string;
  emptyLabel: string;
  errorLabel?: string | null;
  openAriaLabel: string;
  closeAriaLabel: string;
  removeLabel: (label: string) => string;
  classNames: TopBarFavoritesStripClassNames;
  portalScopeClassName?: string;
};

export function topBarFavoritesStripBemClasses(prefix: string): TopBarFavoritesStripClassNames {
  const base = `${prefix}-topbar-favorites`;
  const ui = "delpi-ui-topbar-favorites";
  return {
    root: delpiUiClass(base, ui),
    trigger: delpiUiClass(`${base}__trigger`, `${ui}__trigger`),
    triggerIcon: delpiUiClass(`${base}__trigger-icon`, `${ui}__trigger-icon`),
    triggerLabel: delpiUiClass(`${base}__label`, `${ui}__label`),
    panel: delpiUiClass(`${base}__panel`, `${ui}__panel`),
    status: delpiUiClass(`${base}__status`, `${ui}__status`),
    row: delpiUiClass(`${base}__row`, `${ui}__row`),
    remove: delpiUiClass(`${base}__remove`, `${ui}__remove`),
  };
}

/**
 * Gatilho + painel de favoritos da TopBar.
 * Persistência e identificadores ficam no portal consumidor.
 */
export function TopBarFavoritesStrip({
  items,
  onSelect,
  onRemove,
  title,
  emptyLabel,
  errorLabel,
  openAriaLabel,
  closeAriaLabel,
  removeLabel,
  classNames,
  portalScopeClassName,
}: TopBarFavoritesStripProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const count = items.length;
  const triggerLabel = count > 0 ? `${title} (${count.toLocaleString("pt-BR")})` : title;

  return (
    <div
      ref={rootRef}
      className={open ? withBemModifier(classNames.root, "open") : classNames.root}
    >
      <button
        type="button"
        className={classNames.trigger}
        aria-label={open ? closeAriaLabel : openAriaLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        title={title}
        onClick={() => setOpen((current) => !current)}
      >
        <Star className={classNames.triggerIcon} size={16} strokeWidth={1.75} aria-hidden="true" />
        <span className={`${classNames.triggerLabel} delpi-ui-topbar-collapse-label`}>
          {triggerLabel}
        </span>
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={rootRef}
        panelRef={panelRef}
        className={`delpi-ui-context-menu ${classNames.panel}`}
        variant="bare"
        role="menu"
        aria-label={title}
        preferredPlacement="bottom"
        gap={6}
        portalScopeClassName={portalScopeClassName}
        onDismiss={() => setOpen(false)}
      >
        {errorLabel ? (
          <p className={classNames.status} role="status">
            {errorLabel}
          </p>
        ) : null}
        {count === 0 && !errorLabel ? (
          <p className={classNames.status} role="status">
            {emptyLabel}
          </p>
        ) : null}
        {items.map((item) => (
          <div key={item.id} className={classNames.row} role="none">
            <ContextMenuItem
              label={item.label}
              icon={Star}
              onSelect={() => {
                setOpen(false);
                onSelect(item.id);
              }}
            />
            <button
              type="button"
              className={classNames.remove}
              aria-label={removeLabel(item.label)}
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                onRemove(item.id);
              }}
            >
              <X size={14} strokeWidth={2} aria-hidden="true" />
            </button>
          </div>
        ))}
      </AnchoredPanelPortal>
    </div>
  );
}

export type DashboardTopBarFavoritesStripProps = Omit<TopBarFavoritesStripProps, "classNames">;

export function createDashboardTopBarFavoritesStrip(config: {
  prefix: string;
  portalScopeClassName?: string;
}) {
  const classNames = topBarFavoritesStripBemClasses(config.prefix);
  return function DashboardTopBarFavoritesStrip(props: DashboardTopBarFavoritesStripProps) {
    return (
      <TopBarFavoritesStrip
        {...props}
        classNames={classNames}
        portalScopeClassName={props.portalScopeClassName ?? config.portalScopeClassName}
      />
    );
  };
}
