import { useEffect, useId, useRef, useState } from "react";
import type { ReactNode } from "react";
import { MoreHorizontal, X } from "lucide-react";
import { NavigationActions } from "./NavigationActions";
import { IconButton } from "../actions/IconButton";

export type ConversationPanelControls = {
  leftToggle: ReactNode;
  rightToggle: ReactNode;
};
export type ConversationThreeRegionLayoutProps = {
  center: ReactNode | ((controls: ConversationPanelControls) => ReactNode);
  /** Collapsed rail remains mounted and retains navigation icons. */
  left?: ReactNode | ((state: { collapsed: boolean; onExpand: () => void }) => ReactNode);
  /** Optional permanently mounted category rail for hosts with a separate panel. */
  rail?: ReactNode | ((state: { onExpand: () => void }) => ReactNode);
  /** Optional read-only context content presented in a floating surface. */
  right?: ReactNode;
  leftTitle?: string;
  rightTitle?: string;
  rightAvailable?: boolean;
  className?: string;
};

/** Presentation-only: left rail stays visible; right context never takes a column. */
export function ConversationThreeRegionLayout({
  center, left, rail, right, leftTitle = "Conversas",
  rightTitle = "Contexto da conversa", rightAvailable = true, className,
}: ConversationThreeRegionLayoutProps) {
  const [leftExpanded, setLeftExpanded] = useState(true);
  const [rightOpen, setRightOpen] = useState(false);
  const [compact, setCompact] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const compactRef = useRef(false);
  const contextTriggerRef = useRef<HTMLButtonElement | null>(null);
  const contextRef = useRef<HTMLDivElement | null>(null);
  const drawerCloseRef = useRef<HTMLButtonElement | null>(null);
  const drawerReturnFocusRef = useRef(false);
  const leftId = useId();
  const rightId = useId();

  useEffect(() => {
    const host = rootRef.current?.parentElement;
    if (!host) return;
    const sync = () => {
      const width = host.getBoundingClientRect().width;
      if (width <= 0) return;
      const isCompact = width <= 920;
      if (isCompact && !compactRef.current) setLeftExpanded(false);
      compactRef.current = isCompact;
      setCompact(isCompact);
    };
    sync();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(sync);
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!rightOpen) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !event.defaultPrevented) {
        event.preventDefault();
        setRightOpen(false);
        contextTriggerRef.current?.focus();
      }
    }
    function onPointerDown(event: PointerEvent) {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (!contextRef.current?.contains(target) && !contextTriggerRef.current?.contains(target)) {
        setRightOpen(false);
      }
    }
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("pointerdown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("pointerdown", onPointerDown);
    };
  }, [rightOpen]);

  const collapsed = !leftExpanded;
  const drawerOpen = !!left && compact && leftExpanded;
  const closeDrawer = () => {
    drawerReturnFocusRef.current = true;
    setLeftExpanded(false);
  };
  const openDrawer = () => {
    if (compact) setRightOpen(false);
    setLeftExpanded(true);
  };
  const toggleContext = () => {
    if (compact && !rightOpen && drawerOpen) setLeftExpanded(false);
    setRightOpen(open => !open);
  };

  useEffect(() => {
    if (!compact || leftExpanded || !drawerReturnFocusRef.current) return;
    drawerReturnFocusRef.current = false;
    rootRef.current?.querySelector<HTMLButtonElement>(".delpi-ui-conversation-three-region__rail-heading button")?.focus();
  }, [compact, leftExpanded]);

  useEffect(() => {
    if (drawerOpen) drawerCloseRef.current?.focus();
  }, [drawerOpen]);

  useEffect(() => {
    if (compact && rightOpen && drawerOpen) setLeftExpanded(false);
  }, [compact, rightOpen, drawerOpen]);

  useEffect(() => {
    if (rightOpen && compact) contextRef.current?.querySelector<HTMLButtonElement>(".delpi-ui-conversation-three-region__context-close")?.focus();
  }, [rightOpen, compact]);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.defaultPrevented) return;
      if (event.key === "Escape") {
        event.preventDefault();
        closeDrawer();
      } else if (event.key === "Tab") {
        const candidates = Array.from(rootRef.current?.querySelectorAll<HTMLElement>(
          '.delpi-ui-conversation-three-region__category-rail button:not(:disabled), .delpi-ui-conversation-three-region__left button:not(:disabled), .delpi-ui-conversation-three-region__left a[href], .delpi-ui-conversation-three-region__left input:not(:disabled)'
        ) ?? []).filter(el => !el.closest('[inert]') && el.getClientRects().length > 0);
        if (candidates.length === 0) return;
        const first = candidates[0];
        const last = candidates[candidates.length - 1];
        if (event.shiftKey && (document.activeElement === first || !candidates.includes(document.activeElement as HTMLElement))) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && (document.activeElement === last || !candidates.includes(document.activeElement as HTMLElement))) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [drawerOpen]);
  const controls: ConversationPanelControls = {
    // Left is always present as a rail in the full-page layout.
    leftToggle: null,
    rightToggle: rightAvailable && right ? (
      <button ref={contextTriggerRef} type="button"
        className="delpi-ui-conversation-three-region__header-toggle"
        aria-label={rightOpen ? "Fechar contexto" : "Abrir contexto"}
        aria-controls={rightId} aria-expanded={rightOpen}
        onClick={toggleContext}>
        <MoreHorizontal size={19} aria-hidden="true" />
      </button>
    ) : null,
  };

  return (
    <div ref={rootRef} className={[
      "delpi-ui-conversation-three-region",
      collapsed ? "delpi-ui-conversation-three-region--left-collapsed" : "",
      compact ? "delpi-ui-conversation-three-region--compact" : "",
      rail ? "delpi-ui-conversation-three-region--with-rail" : "",
      className,
    ].filter(Boolean).join(" ")}>
      {rail ? (
        <div className="delpi-ui-conversation-three-region__category-rail">
          {collapsed ? <div className="delpi-ui-conversation-three-region__rail-heading">
            <NavigationActions action="toggle" expanded={false} onAction={openDrawer} />
          </div> : null}
          {typeof rail === "function" ? rail({ onExpand: openDrawer }) : rail}
        </div>
      ) : null}
      {drawerOpen ? (
        <button type="button" className="delpi-ui-conversation-three-region__backdrop"
          aria-label="Fechar navegação" onClick={closeDrawer} />
      ) : null}
      {left && (!rail || leftExpanded) ? (
        <nav id={leftId} aria-label={leftTitle}
          className="delpi-ui-conversation-three-region__left"
          data-drawer={drawerOpen ? "true" : "false"}>
          <div className="delpi-ui-conversation-three-region__side-heading">
            {!collapsed ? <strong>{leftTitle}</strong> : null}
            {drawerOpen ? (
              <button ref={drawerCloseRef} type="button"
                className="delpi-ui-conversation-three-region__drawer-close"
                aria-label="Recolher conversas" aria-controls={leftId} aria-expanded={true}
                onClick={closeDrawer}><X size={18} aria-hidden="true" /></button>
            ) : <NavigationActions action="toggle" expanded={!collapsed} onAction={() => setLeftExpanded((value) => !value)} />}
          </div>
          <div className="delpi-ui-conversation-three-region__side-content">
            {typeof left === "function" ? left({ collapsed, onExpand: openDrawer }) : left}
          </div>
        </nav>
      ) : null}
      <div className="delpi-ui-conversation-three-region__center" inert={drawerOpen}>
        <div className="delpi-ui-conversation-three-region__conversation">
          {typeof center === "function" ? center(controls) : center}
        </div>
      </div>
      {rightAvailable && right ? (
        <div
          ref={contextRef}
          inert={drawerOpen}
          id={rightId}
          role="dialog"
          aria-modal="false"
          aria-label={rightTitle}
          aria-hidden={!rightOpen}
          data-open={rightOpen ? "true" : "false"}
          className="delpi-ui-conversation-three-region__context-popover delpi-ui-popover-surface"
        >
          {rightOpen ? (
            <>
              <div className="delpi-ui-conversation-three-region__side-heading">
                <strong>Contexto</strong>
                <IconButton className="delpi-ui-conversation-three-region__context-close delpi-ui-conversation-three-region__chrome-icon" aria-label="Fechar painel de contexto" onClick={() => {
                  setRightOpen(false);
                  contextTriggerRef.current?.focus();
                }}>
                  <X size={18} aria-hidden="true" />
                </IconButton>
              </div>
              <div className="delpi-ui-conversation-three-region__side-content">{right}</div>
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
