import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";

import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import type { MessageThreadAction, MessageThreadClassNames } from "./MessageThread";

const FINE_HOVER_QUERY = "(hover: hover) and (pointer: fine)";
const CLOSE_DELAY_MS = 140;

export type MessageThreadActionsBarProps = {
  classNames: MessageThreadClassNames;
  actions: readonly MessageThreadAction[];
  actionExtras: ReactNode;
  anchorRef: RefObject<HTMLElement | null>;
  /** Outros: alinhar à direita da bolha; minhas: à esquerda. */
  alignEnd?: boolean;
  portalScopeClassName?: string;
  toolbarAriaLabel?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPanelEnter: () => void;
  onPanelLeave: () => void;
};

/**
 * Toolbar de opções da mensagem em portal no body — flip top/bottom + clamp
 * horizontal no viewport (evita corte por overflow do scroll da thread).
 */
export function MessageThreadActionsBar({
  classNames,
  actions,
  actionExtras,
  anchorRef,
  alignEnd = false,
  portalScopeClassName,
  toolbarAriaLabel,
  open,
  onOpenChange,
  onPanelEnter,
  onPanelLeave,
}: MessageThreadActionsBarProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  if (!open) return null;

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      preferredPlacement="top"
      allowFlip
      horizontalAlign={alignEnd ? "end" : "start"}
      gap={6}
      portalScopeClassName={portalScopeClassName}
      className={classNames.actions}
      role="toolbar"
      aria-label={toolbarAriaLabel}
      exclusive
      onDismiss={() => onOpenChange(false)}
      onPanelMouseEnter={onPanelEnter}
      onPanelMouseLeave={onPanelLeave}
    >
      {actionExtras}
      {actionExtras && actions.length > 0 ? (
        <span className={classNames.actionsDivider} aria-hidden />
      ) : null}
      {actions.map((action) => (
        <button
          key={action.id}
          type="button"
          className={action.danger ? classNames.actionDanger : classNames.action}
          aria-label={action.label}
          title={action.title ?? action.label}
          onClick={action.onClick}
        >
          {action.icon ?? action.label}
        </button>
      ))}
    </AnchoredPanelPortal>
  );
}

/** Hover fino → abre sob demanda; touch/coarse → permanece aberta. */
export function useMessageThreadActionsOpen(): {
  open: boolean;
  setOpen: (open: boolean) => void;
  onAnchorEnter: () => void;
  onAnchorLeave: () => void;
} {
  const [fineHover, setFineHover] = useState(() => {
    if (typeof window === "undefined" || !window.matchMedia) return true;
    return window.matchMedia(FINE_HOVER_QUERY).matches;
  });
  const [open, setOpen] = useState(() => !fineHover);
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const media = window.matchMedia(FINE_HOVER_QUERY);
    const sync = () => {
      const matches = media.matches;
      setFineHover(matches);
      if (!matches) setOpen(true);
    };
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  const clearCloseTimer = () => {
    if (closeTimerRef.current != null) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  };

  const onAnchorEnter = () => {
    clearCloseTimer();
    setOpen(true);
  };

  const onAnchorLeave = () => {
    if (!fineHover) return;
    clearCloseTimer();
    closeTimerRef.current = setTimeout(() => {
      setOpen(false);
      closeTimerRef.current = null;
    }, CLOSE_DELAY_MS);
  };

  useEffect(
    () => () => {
      clearCloseTimer();
    },
    [],
  );

  return {
    open: fineHover ? open : true,
    setOpen: (next) => {
      clearCloseTimer();
      setOpen(next);
    },
    onAnchorEnter,
    onAnchorLeave,
  };
}
