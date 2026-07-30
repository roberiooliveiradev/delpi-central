import { ChevronDown, type LucideIcon } from "lucide-react";
import { useId, useRef, useState } from "react";

import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";

export type DiagramIoMenuItem = {
  id: string;
  label: string;
  icon: LucideIcon;
  onSelect: () => void;
  disabled?: boolean;
};

type Props = {
  items: DiagramIoMenuItem[];
  /** Classe do botão gatilho (ex.: chrome-action ghost). */
  triggerClassName?: string;
  label?: string;
  menuAriaLabel?: string;
  portalScopeClassName?: string;
};

/**
 * Agrupa ações de importação/exportação do diagrama num popover ancorado.
 */
export function DiagramIoMenu({
  items,
  triggerClassName,
  label = "Importar / exportar",
  menuAriaLabel = "Importar e exportar diagrama",
  portalScopeClassName = "dashboard-transformometro",
}: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  if (!items.length) return null;

  const close = () => setOpen(false);

  return (
    <div ref={rootRef} className="delpi-ui-bpmn-io-menu">
      <button
        type="button"
        className={triggerClassName}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-controls={open ? menuId : undefined}
        onClick={() => setOpen((prev) => !prev)}
      >
        <span>{label}</span>
        <ChevronDown size={14} aria-hidden="true" />
      </button>
      {open ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          className="delpi-ui-bpmn-io-menu__panel delpi-ui-popover-surface"
          role="menu"
          aria-label={menuAriaLabel}
          density="compact"
          preferredPlacement="bottom"
          portalScopeClassName={portalScopeClassName}
          onDismiss={close}
        >
          <div id={menuId} ref={panelRef} className="delpi-ui-bpmn-io-menu__list">
            {items.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  type="button"
                  role="menuitem"
                  className="delpi-ui-bpmn-io-menu__item"
                  disabled={item.disabled}
                  onClick={() => {
                    if (item.disabled) return;
                    item.onSelect();
                    close();
                  }}
                >
                  <Icon size={15} aria-hidden="true" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
