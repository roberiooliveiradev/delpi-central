import { useEffect, useId, useRef, useState } from "react";
import type { ReactNode } from "react";
import { MoreHorizontal, PanelLeftClose, PanelLeftOpen, X } from "lucide-react";
import { IconButton } from "../actions/IconButton";

export type ConversationPanelControls = {
  leftToggle: ReactNode;
  rightToggle: ReactNode;
};
export type ConversationThreeRegionLayoutProps = {
  center: ReactNode | ((controls: ConversationPanelControls) => ReactNode);
  /** Collapsed rail remains mounted and retains navigation icons. */
  left?: ReactNode | ((state: { collapsed: boolean; onExpand: () => void }) => ReactNode);
  /** Optional read-only context content presented in a floating surface. */
  right?: ReactNode;
  leftTitle?: string;
  rightTitle?: string;
  rightAvailable?: boolean;
  className?: string;
};

/** Presentation-only: left rail stays visible; right context never takes a column. */
export function ConversationThreeRegionLayout({
  center, left, right, leftTitle = "Conversas",
  rightTitle = "Contexto da conversa", rightAvailable = true, className,
}: ConversationThreeRegionLayoutProps) {
  const [leftExpanded, setLeftExpanded] = useState(true);
  const [rightOpen, setRightOpen] = useState(false);
  const [compact, setCompact] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const compactRef = useRef(false);
  const contextTriggerRef = useRef<HTMLButtonElement | null>(null);
  const contextRef = useRef<HTMLDivElement | null>(null);
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
      if (event.key === "Escape") {
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
  const controls: ConversationPanelControls = {
    // Left is always present as a rail in the full-page layout.
    leftToggle: null,
    rightToggle: rightAvailable && right ? (
      <button ref={contextTriggerRef} type="button"
        className="delpi-ui-conversation-three-region__header-toggle"
        aria-label={rightOpen ? "Fechar contexto" : "Abrir contexto"}
        aria-controls={rightId} aria-expanded={rightOpen}
        onClick={() => setRightOpen((open) => !open)}>
        <MoreHorizontal size={19} aria-hidden="true" />
      </button>
    ) : null,
  };

  return (
    <div ref={rootRef} className={[
      "delpi-ui-conversation-three-region",
      collapsed ? "delpi-ui-conversation-three-region--left-collapsed" : "",
      compact ? "delpi-ui-conversation-three-region--compact" : "",
      className,
    ].filter(Boolean).join(" ")}>
      {left ? (
        <nav id={leftId} aria-label={leftTitle}
          className="delpi-ui-conversation-three-region__left">
          <div className="delpi-ui-conversation-three-region__side-heading">
            {!collapsed ? <strong>{leftTitle}</strong> : null}
            <IconButton
              className="delpi-ui-conversation-three-region__rail-toggle delpi-ui-conversation-three-region__chrome-icon"
              aria-label={collapsed ? "Expandir conversas" : "Recolher conversas"}
              aria-expanded={!collapsed}
              onClick={() => setLeftExpanded((value) => !value)}
            >
              {collapsed
                ? <PanelLeftOpen size={19} strokeWidth={1.8} aria-hidden="true" />
                : <PanelLeftClose size={19} strokeWidth={1.8} aria-hidden="true" />}
            </IconButton>
          </div>
          <div className="delpi-ui-conversation-three-region__side-content">
            {typeof left === "function" ? left({ collapsed, onExpand: () => setLeftExpanded(true) }) : left}
          </div>
        </nav>
      ) : null}
      <div className="delpi-ui-conversation-three-region__center">
        <div className="delpi-ui-conversation-three-region__conversation">
          {typeof center === "function" ? center(controls) : center}
        </div>
      </div>
      {rightAvailable && right ? (
        <div
          ref={contextRef}
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
