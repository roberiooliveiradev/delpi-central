import type { LucideIcon } from "lucide-react";
import { ChevronRight } from "lucide-react";
import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import { resolveContextMenuSubFlyout } from "./resolveContextMenuSubFlyout";

export type ContextMenuSubProps = {
  label: string;
  icon?: LucideIcon;
  disabled?: boolean;
  /** Conteúdo do submenu (`ContextMenuItem`, dividers…). */
  children: ReactNode;
};

/**
 * Item com submenu lateral (estilo PowerPoint «Organizar ▸»).
 * Abre no hover/foco; setas →/← e Escape fecham só o submenu.
 * Posicionamento: flip L/R + clamp vertical no viewport (igual AnchoredPanel).
 */
export function ContextMenuSub({
  label,
  icon: Icon,
  disabled = false,
  children,
}: ContextMenuSubProps) {
  const [open, setOpen] = useState(false);
  const [flyoutStyle, setFlyoutStyle] = useState<CSSProperties | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const closeTimerRef = useRef<number | null>(null);
  const focusItemTimerRef = useRef<number | null>(null);
  const mountedRef = useRef(true);
  const menuId = useId();
  const triggerId = `${menuId}-trigger`;
  const panelId = `${menuId}-panel`;

  const clearCloseTimer = useCallback(() => {
    if (closeTimerRef.current != null) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  }, []);

  const clearFocusItemTimer = useCallback(() => {
    if (focusItemTimerRef.current != null) {
      window.clearTimeout(focusItemTimerRef.current);
      focusItemTimerRef.current = null;
    }
  }, []);

  const scheduleClose = useCallback(() => {
    clearCloseTimer();
    closeTimerRef.current = window.setTimeout(() => {
      closeTimerRef.current = null;
      if (!mountedRef.current) return;
      setOpen(false);
    }, 120);
  }, [clearCloseTimer]);

  const openSubmenu = useCallback(() => {
    if (disabled || !mountedRef.current) return;
    clearCloseTimer();
    setOpen(true);
  }, [clearCloseTimer, disabled]);

  const closeSubmenu = useCallback(() => {
    clearCloseTimer();
    clearFocusItemTimer();
    if (!mountedRef.current) return;
    setOpen(false);
  }, [clearCloseTimer, clearFocusItemTimer]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      clearCloseTimer();
      clearFocusItemTimer();
    };
  }, [clearCloseTimer, clearFocusItemTimer]);

  const repositionFlyout = useCallback(() => {
    if (!mountedRef.current) return;
    const root = rootRef.current;
    const panel = panelRef.current;
    if (!root || !panel) return;
    const rootRect = root.getBoundingClientRect();
    /*
     * scrollHeight = conteúdo natural (não o box já cortado por max-height CSS).
     * Assim o clamp sobe o painel quando há espaço acima, em vez de só scrollar.
     */
    const naturalHeight = Math.max(panel.scrollHeight, panel.offsetHeight, 160);
    const coords = resolveContextMenuSubFlyout({
      trigger: {
        left: rootRect.left,
        top: rootRect.top,
        right: rootRect.right,
        bottom: rootRect.bottom,
        width: rootRect.width,
        height: rootRect.height,
      },
      panelWidth: panel.offsetWidth || 200,
      panelHeight: naturalHeight,
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
    });
    setFlyoutStyle({
      position: "fixed",
      top: coords.top,
      left: coords.left,
      right: "auto",
      zIndex: 80,
      /* Scroll só quando o resolver indica que o conteúdo não cabe. */
      ...(coords.overflowY === "auto" && coords.maxHeight != null
        ? { maxHeight: coords.maxHeight, overflowY: "auto" as const }
        : { maxHeight: "none", overflowY: "visible" as const }),
    });
  }, []);

  useLayoutEffect(() => {
    if (!open) {
      setFlyoutStyle(null);
      return;
    }
    let cancelled = false;
    const apply = () => {
      if (cancelled || !mountedRef.current) return;
      repositionFlyout();
    };
    apply();
    /* 2º frame: altura real após paint dos itens (Alinhar / Girar longos). */
    const raf = window.requestAnimationFrame(apply);
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(raf);
    };
  }, [open, repositionFlyout, children]);

  useEffect(() => {
    if (!open) return;
    const onViewportChange = () => repositionFlyout();
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("scroll", onViewportChange, true);
    return () => {
      window.removeEventListener("resize", onViewportChange);
      window.removeEventListener("scroll", onViewportChange, true);
    };
  }, [open, repositionFlyout]);

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
      clearFocusItemTimer();
      focusItemTimerRef.current = window.setTimeout(() => {
        focusItemTimerRef.current = null;
        focusFirstItem();
      }, 0);
      return;
    }
    if (event.key === "Escape" && open) {
      event.preventDefault();
      event.stopPropagation();
      closeSubmenu();
    }
  }

  function onPanelKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "ArrowLeft" || event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      closeSubmenu();
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
          className="delpi-ui-context-menu delpi-ui-context-menu__sub-panel"
          style={flyoutStyle ?? { visibility: "hidden" }}
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
