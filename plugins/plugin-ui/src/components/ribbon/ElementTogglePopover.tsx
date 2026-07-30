import type { LucideIcon } from "lucide-react";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { useRibbonSectionPopoverSurface } from "./RibbonGroupSurfaceContext";

export type ElementTogglePresence = {
  enabled: boolean;
  onAdd: () => void;
  onRemove: () => void;
  onOpenOptions: () => void;
};

export type ElementTogglePopoverProps = {
  icon: LucideIcon;
  label: string;
  hint?: string;
  /** Presente no visual (borda ativa). */
  active?: boolean;
  /** Parte focada no palco (chrome distinto opcional). */
  focused?: boolean;
  disabled?: boolean;
  presence: ElementTogglePresence;
  labels?: {
    add?: string;
    remove?: string;
    options?: string;
    menuAria?: string;
  };
  children?: ReactNode;
  portalScopeClassName?: string;
  className?: string;
};

const DEFAULT_LABELS = {
  add: "Adicionar",
  remove: "Remover",
  options: "Opções do item…",
  menuAria: "Ações do elemento",
} as const;

/**
 * Chip de elemento de ribbon: clique no corpo abre popover com
 * Adicionar/Remover + Opções (Excel / Power BI — presença ≠ formato).
 */
export function ElementTogglePopover({
  icon: Icon,
  label,
  hint,
  active = false,
  focused = false,
  disabled = false,
  presence,
  labels: labelsProp,
  children,
  portalScopeClassName,
  className,
}: ElementTogglePopoverProps) {
  const L = { ...DEFAULT_LABELS, ...labelsProp };
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const inSectionPopover = useRibbonSectionPopoverSurface();

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const close = () => setOpen(false);

  const runAdd = () => {
    presence.onAdd();
    close();
  };
  const runRemove = () => {
    presence.onRemove();
    close();
  };
  const runOptions = () => {
    if (!presence.enabled) return;
    presence.onOpenOptions();
    close();
  };

  const tileClass = [
    "delpi-ui-element-toggle",
    active || focused ? "delpi-ui-element-toggle--active" : null,
    focused ? "delpi-ui-element-toggle--focused" : null,
    open ? "delpi-ui-element-toggle--open" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const menu = (
    <div
      id={menuId}
      className="delpi-ui-element-toggle__menu"
      role="menu"
      aria-label={L.menuAria}
    >
      {presence.enabled ? (
        <button
          type="button"
          role="menuitem"
          className="delpi-ui-element-toggle__action delpi-ui-element-toggle__action--danger"
          onClick={runRemove}
        >
          {L.remove}
        </button>
      ) : (
        <button
          type="button"
          role="menuitem"
          className="delpi-ui-element-toggle__action"
          onClick={runAdd}
        >
          {L.add}
        </button>
      )}
      <button
        type="button"
        role="menuitem"
        className="delpi-ui-element-toggle__action"
        disabled={!presence.enabled}
        onClick={runOptions}
      >
        {L.options}
      </button>
      {children ? <div className="delpi-ui-element-toggle__extra">{children}</div> : null}
    </div>
  );

  return (
    <div ref={rootRef} className={tileClass} title={hint}>
      <button
        type="button"
        className="delpi-ui-element-toggle__trigger"
        disabled={disabled}
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => {
          if (disabled) return;
          setOpen((prev) => !prev);
        }}
      >
        <span className="delpi-ui-element-toggle__icon" aria-hidden="true">
          <Icon size={18} />
        </span>
        <span className="delpi-ui-element-toggle__label">{label}</span>
      </button>
      {open ? (
        inSectionPopover ? (
          <div className="delpi-ui-element-toggle__inline">{menu}</div>
        ) : (
          <AnchoredPanelPortal
            open={open}
            onDismiss={close}
            anchorRef={rootRef}
            panelRef={panelRef}
            exclusive={!inSectionPopover}
            density="compact"
            className={["delpi-ui-element-toggle__portal", portalScopeClassName]
              .filter(Boolean)
              .join(" ")}
          >
            {menu}
          </AnchoredPanelPortal>
        )
      ) : null}
    </div>
  );
}
