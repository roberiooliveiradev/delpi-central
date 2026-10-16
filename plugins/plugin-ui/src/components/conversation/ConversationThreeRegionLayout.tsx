import { useEffect, useId, useRef, useState } from "react";
import type { ReactNode } from "react";
import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, X } from "lucide-react";

import { IconButton } from "../actions/IconButton";

/** Shared visual layout only. Never owns conversation, history or application data. */
export type ConversationThreeRegionLayoutProps = {
  center: ReactNode;
  left?: ReactNode;
  right?: ReactNode;
  leftTitle?: string;
  rightTitle?: string;
  rightAvailable?: boolean;
  className?: string;
};

export function ConversationThreeRegionLayout({
  center,
  left,
  right,
  leftTitle = "Conversas",
  rightTitle = "Contexto da conversa",
  rightAvailable = true,
  className,
}: ConversationThreeRegionLayoutProps) {
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(false);
  const compactRef = useRef(false);
  const layoutRef = useRef<HTMLDivElement | null>(null);
  const leftId = useId();
  const rightId = useId();
  const leftToggleRef = useRef<HTMLDivElement | null>(null);
  const rightToggleRef = useRef<HTMLButtonElement | null>(null);

  // A full-page starts with the left navigation open; a dock/mobile starts
  // with both drawers closed. Observe the actual host container, not window.
  useEffect(() => {
    const root = layoutRef.current;
    const host = root?.parentElement;
    if (!host) return;
    const sync = () => {
      const width = host.getBoundingClientRect().width;
      compactRef.current = width > 0 && width <= 920;
      if (compactRef.current) {
        setLeftOpen(false);
        setRightOpen(false);
      }
    };
    sync();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(sync);
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  function closeLeft() {
    setLeftOpen(false);
    leftToggleRef.current?.querySelector("button")?.focus();
  }
  function closeRight() {
    setRightOpen(false);
    rightToggleRef.current?.querySelector("button")?.focus();
  }

  return (
    <div
      ref={layoutRef}
      className={[
        "delpi-ui-conversation-three-region",
        leftOpen ? "delpi-ui-conversation-three-region--left-open" : "",
        rightOpen && rightAvailable ? "delpi-ui-conversation-three-region--right-open" : "",
        className,
      ].filter(Boolean).join(" ")}
    >
      {leftOpen && left ? (
        <nav id={leftId} aria-label={leftTitle} className="delpi-ui-conversation-three-region__left">
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
        <div className="delpi-ui-conversation-three-region__controls" aria-label="Painéis da conversa">
          <div ref={leftToggleRef} className="delpi-ui-conversation-three-region__toggle">
            <IconButton
              aria-label={leftOpen ? "Ocultar conversas" : "Abrir conversas"}
              aria-expanded={leftOpen}
              onClick={() => { setLeftOpen((value) => !value); if (compactRef.current) setRightOpen(false); }}
              disabled={!left}
            >
              {leftOpen ? <PanelLeftClose size={18} aria-hidden="true" /> : <PanelLeftOpen size={18} aria-hidden="true" />}
            </IconButton>
          </div>
          <div ref={rightToggleRef} className="delpi-ui-conversation-three-region__toggle">
            {rightAvailable && right ? (
              <IconButton
                aria-label={rightOpen ? "Fechar contexto" : "Abrir contexto"}
                aria-expanded={rightOpen}
                onClick={() => { setRightOpen((value) => !value); if (compactRef.current) setLeftOpen(false); }}
              >
                {rightOpen ? <PanelRightClose size={18} aria-hidden="true" /> : <PanelRightOpen size={18} aria-hidden="true" />}
              </IconButton>
            ) : null}
          </div>
        </div>
        <div className="delpi-ui-conversation-three-region__conversation">{center}</div>
      </div>

      {rightOpen && rightAvailable && right ? (
        <aside id={rightId} aria-label={rightTitle} className="delpi-ui-conversation-three-region__right">
          <div className="delpi-ui-conversation-three-region__side-heading">
            <strong>{rightTitle}</strong>
            <IconButton aria-label="Fechar painel de contexto" onClick={closeRight}>
              <X size={18} aria-hidden="true" />
            </IconButton>
          </div>
          <div className="delpi-ui-conversation-three-region__side-content">{right}</div>
        </aside>
      ) : null}
      {(leftOpen && left) || (rightOpen && rightAvailable && right) ? (
        <button
          type="button"
          tabIndex={-1}
          aria-hidden="true"
          className="delpi-ui-conversation-three-region__backdrop"
          onClick={() => { setLeftOpen(false); setRightOpen(false); leftToggleRef.current?.querySelector("button")?.focus(); }}
        />
      ) : null}
    </div>
  );
}
