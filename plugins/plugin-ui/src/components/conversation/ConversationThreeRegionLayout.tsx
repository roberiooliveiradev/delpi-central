import { useEffect, useId, useRef, useState } from "react";
import type { ReactNode } from "react";
import { PanelLeftOpen, PanelLeftClose, PanelRightOpen, X } from "lucide-react";
import { IconButton } from "../actions/IconButton";

export type ConversationPanelControls = {
  leftToggle: ReactNode;
  rightToggle: ReactNode;
};

export type ConversationThreeRegionLayoutProps = {
  /** Pass a render function to place toggles in ConversationHeader leading/actions. */
  center: ReactNode | ((controls: ConversationPanelControls) => ReactNode);
  left?: ReactNode;
  right?: ReactNode;
  leftTitle?: string;
  rightTitle?: string;
  rightAvailable?: boolean;
  className?: string;
};

/** Three-region visual shell: no transport, no conversation state, no fake history. */
export function ConversationThreeRegionLayout({
  center, left, right,
  leftTitle = "Conversas",
  rightTitle = "Contexto da conversa",
  rightAvailable = true, className,
}: ConversationThreeRegionLayoutProps) {
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(false);
  const compactRef = useRef(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const leftTriggerRef = useRef<HTMLButtonElement | null>(null);
  const rightTriggerRef = useRef<HTMLButtonElement | null>(null);
  const leftId = useId();
  const rightId = useId();

  useEffect(() => {
    const host = rootRef.current?.parentElement;
    if (!host) return;
    const sync = () => {
      const width = host.getBoundingClientRect().width;
      if (!width) return;
      const nextCompact = width <= 920;
      if (nextCompact && !compactRef.current) {
        setLeftOpen(false);
        setRightOpen(false);
      }
      compactRef.current = nextCompact;
    };
    sync();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(sync);
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  function openLeft() {
    if (compactRef.current) setRightOpen(false);
    setLeftOpen(true);
  }
  function openRight() {
    if (compactRef.current) setLeftOpen(false);
    setRightOpen(true);
  }
  function closeLeft() {
    setLeftOpen(false);
    requestAnimationFrame(() => leftTriggerRef.current?.focus());
  }
  function closeRight() {
    setRightOpen(false);
    requestAnimationFrame(() => rightTriggerRef.current?.focus());
  }

  const controls: ConversationPanelControls = {
    leftToggle: !leftOpen && left ? (
      <button ref={leftTriggerRef} type="button" onClick={openLeft}
        className="delpi-ui-conversation-three-region__header-toggle"
        aria-label="Abrir conversas" aria-controls={leftId} aria-expanded={false}>
        <PanelLeftOpen size={18} aria-hidden="true" />
      </button>
    ) : null,
    rightToggle: !rightOpen && rightAvailable && right ? (
      <button ref={rightTriggerRef} type="button" onClick={openRight}
        className="delpi-ui-conversation-three-region__header-toggle"
        aria-label="Abrir contexto" aria-controls={rightId} aria-expanded={false}>
        <PanelRightOpen size={18} aria-hidden="true" />
      </button>
    ) : null,
  };

  const isDrawerOpen = compactRef.current && ((leftOpen && !!left) || (rightOpen && rightAvailable && !!right));
  return (
    <div ref={rootRef} className={[
      "delpi-ui-conversation-three-region",
      leftOpen && left ? "delpi-ui-conversation-three-region--left-open" : "",
      rightOpen && rightAvailable && right ? "delpi-ui-conversation-three-region--right-open" : "",
      className,
    ].filter(Boolean).join(" ")}>
      {leftOpen && left ? (
        <nav id={leftId} className="delpi-ui-conversation-three-region__left" aria-label={leftTitle}>
          <div className="delpi-ui-conversation-three-region__side-heading">
            <strong>{leftTitle}</strong>
            <IconButton aria-label="Recolher conversas" onClick={closeLeft}>
              <PanelLeftClose size={18} aria-hidden="true" />
            </IconButton>
          </div>
          <div className="delpi-ui-conversation-three-region__side-content">{left}</div>
        </nav>
      ) : null}
      <div className="delpi-ui-conversation-three-region__center">
        <div className="delpi-ui-conversation-three-region__conversation">
          {typeof center === "function" ? center(controls) : center}
        </div>
      </div>
      {rightOpen && rightAvailable && right ? (
        <aside id={rightId} className="delpi-ui-conversation-three-region__right" aria-label={rightTitle}>
          <div className="delpi-ui-conversation-three-region__side-heading">
            <strong>Contexto</strong>
            <IconButton aria-label="Fechar painel de contexto" onClick={closeRight}>
              <X size={18} aria-hidden="true" />
            </IconButton>
          </div>
          <div className="delpi-ui-conversation-three-region__side-content">{right}</div>
        </aside>
      ) : null}
      {isDrawerOpen ? (
        <button className="delpi-ui-conversation-three-region__backdrop" type="button"
          aria-label="Fechar painel lateral"
          onClick={() => { if (rightOpen) closeRight(); else closeLeft(); }} />
      ) : null}
    </div>
  );
}
