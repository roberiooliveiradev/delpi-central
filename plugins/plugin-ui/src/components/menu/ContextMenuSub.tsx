import type { LucideIcon } from "lucide-react";
import { ChevronRight } from "lucide-react";
import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";

export type ContextMenuSubProps = {
  label: string;
  icon?: LucideIcon;
  disabled?: boolean;
  /** Conteúdo do submenu (`ContextMenuItem`, dividers…). */
  children: ReactNode;
};

type FlyoutSide = "right" | "left";

/**
 * Item com submenu lateral (estilo PowerPoint «Organizar ▸»).
 * Abre no hover/foco; setas →/← e Escape fecham só o submenu.
 */
export function ContextMenuSub({
  label,
  icon: Icon,
  disabled = false,
  children,
}: ContextMenuSubProps) {
  const [open, setOpen] = useState(false);
  const [side, setSide] = useState<FlyoutSide>("right");
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const closeTimerRef = useRef<number | null>(null);
  const menuId = useId();
  const triggerId = `${menuId}-trigger`;
  const panelId = `${menuId}-panel`;

  const clearCloseTimer = useCallback(() => {
    if (closeTimerRef.current != null) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  }, []);

  const scheduleClose = useCallback(() => {
    clearCloseTimer();
    closeTimerRef.current = window.setTimeout(() => {
      closeTimerRef.current = null;
      setOpen(false);
    }, 120);
  }, [clearCloseTimer]);

  const openSubmenu = useCallback(() => {
    if (disabled) return;
    clearCloseTimer();
    setOpen(true);
  }, [clearCloseTimer, disabled]);

  useEffect(() => () => clearCloseTimer(), [clearCloseTimer]);

  useLayoutEffect(() => {
    if (!open) return;
    const root = rootRef.current;
    const panel = panelRef.current;
    if (!root || !panel) return;
    const rootRect = root.getBoundingClientRect();
    const panelWidth = panel.offsetWidth || 200;
    const spaceRight = window.innerWidth - rootRect.right;
    const spaceLeft = rootRect.left;
    setSide(spaceRight < panelWidth + 8 && spaceLeft > spaceRight ? "left" : "right");
  }, [open]);

  function focusFirstItem() {
    const first = panelRef.current?.querySelector<HTMLElement>(
      '[role="menuitem"]:not([disabled])',
    );
    first?.focus();
  }

  function onTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (disabled) return;
    if (event.key === "ArrowRight" || event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      event.stopPropagation();
      openSubmenu();
      /* Próximo tick: painel já montado. */
      window.setTimeout(focusFirstItem, 0);
      return;
    }
    if (event.key === "Escape" && open) {
      event.preventDefault();
      event.stopPropagation();
      setOpen(false);
    }
  }

  function onPanelKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "ArrowLeft" || event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      setOpen(false);
      triggerRef.current?.focus();
    }
  }

  return (
    <div
      ref={rootRef}
      className={[
        "delpi-ui-context-menu__sub",
        open ? "delpi-ui-context-menu__sub--open" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onMouseEnter={openSubmenu}
      onMouseLeave={scheduleClose}
    >
      <button
        ref={triggerRef}
        type="button"
        id={triggerId}
        role="menuitem"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={panelId}
        className="delpi-ui-context-menu__item delpi-ui-context-menu__sub-trigger"
        disabled={disabled}
        onClick={() => {
          if (disabled) return;
          setOpen((prev) => !prev);
        }}
        onKeyDown={onTriggerKeyDown}
        onFocus={openSubmenu}
      >
        <span className="delpi-ui-context-menu__item-leading" aria-hidden="true">
          {Icon ? <Icon size={16} strokeWidth={1.75} /> : null}
        </span>
        <span className="delpi-ui-context-menu__item-label">{label}</span>
        <span className="delpi-ui-context-menu__item-chevron" aria-hidden="true">
          <ChevronRight size={14} strokeWidth={2} />
        </span>
      </button>
      {open ? (
        <div
          ref={panelRef}
          id={panelId}
          role="menu"
          aria-label={label}
          className={[
            "delpi-ui-context-menu delpi-ui-context-menu__sub-panel",
            side === "left"
              ? "delpi-ui-context-menu__sub-panel--left"
              : "delpi-ui-context-menu__sub-panel--right",
          ].join(" ")}
          onMouseEnter={openSubmenu}
          onMouseLeave={scheduleClose}
          onKeyDown={onPanelKeyDown}
        >
          {children}
        </div>
      ) : null}
    </div>
  );
}
