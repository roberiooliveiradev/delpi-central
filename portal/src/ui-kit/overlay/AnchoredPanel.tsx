// portal/src/ui-kit/overlay/AnchoredPanel.tsx

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";
import "./AnchoredPanel.css";

export type AnchoredPanelProps = {
  open: boolean;
  anchorRef: RefObject<HTMLElement | null>;
  onDismiss: () => void;
  children: ReactNode;
  id?: string;
  className?: string;
  minWidth?: number;
  maxHeight?: number;
  /** Ref do painel — use para focar conteúdo ou rolar até a opção ativa. */
  panelRef?: RefObject<HTMLDivElement | null>;
};

type PanelPosition = {
  top: number;
  left: number;
  width: number;
  maxHeight: number;
};

const VIEWPORT_GAP = 8;
const ANCHOR_GAP = 4;

/**
 * Painel flutuante preso a um elemento âncora, renderizado no `body`.
 *
 * Motivo do portal: gatilhos vivem dentro de containers com `overflow: auto`
 * (DenseTable, modais) — um painel `position: absolute` seria recortado.
 */
export function AnchoredPanel({
  open,
  anchorRef,
  onDismiss,
  children,
  id,
  className,
  minWidth = 192,
  maxHeight = 260,
  panelRef,
}: AnchoredPanelProps) {
  const innerRef = useRef<HTMLDivElement | null>(null);
  const [position, setPosition] = useState<PanelPosition | null>(null);

  const setRefs = useCallback(
    (node: HTMLDivElement | null) => {
      innerRef.current = node;
      if (panelRef) panelRef.current = node;
    },
    [panelRef],
  );

  useLayoutEffect(() => {
    if (!open) {
      setPosition(null);
      return;
    }

    const update = () => {
      const anchor = anchorRef.current;
      if (!anchor) return;

      const rect = anchor.getBoundingClientRect();
      const width = Math.max(rect.width, minWidth);
      const spaceBelow = window.innerHeight - rect.bottom - VIEWPORT_GAP;
      const spaceAbove = rect.top - VIEWPORT_GAP;
      const measured = innerRef.current?.offsetHeight ?? maxHeight;
      const openUp = spaceBelow < Math.min(measured, maxHeight) && spaceAbove > spaceBelow;
      const available = Math.max(140, (openUp ? spaceAbove : spaceBelow) - ANCHOR_GAP);
      const height = Math.min(maxHeight, available);

      setPosition({
        top: openUp
          ? Math.max(VIEWPORT_GAP, rect.top - ANCHOR_GAP - Math.min(measured, height))
          : rect.bottom + ANCHOR_GAP,
        left: Math.max(
          VIEWPORT_GAP,
          Math.min(rect.left, window.innerWidth - width - VIEWPORT_GAP),
        ),
        width,
        maxHeight: height,
      });
    };

    update();

    // O conteúdo muda de altura ao filtrar: sem isso o painel aberto para cima
    // descola do gatilho.
    const observer = new ResizeObserver(update);
    if (innerRef.current) observer.observe(innerRef.current);

    window.addEventListener("scroll", update, true);
    window.addEventListener("resize", update);
    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", update, true);
      window.removeEventListener("resize", update);
    };
  }, [open, anchorRef, minWidth, maxHeight]);

  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: MouseEvent | TouchEvent) => {
      const target = event.target as Node;
      if (innerRef.current?.contains(target)) return;
      if (anchorRef.current?.contains(target)) return;
      onDismiss();
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onDismiss();
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("touchstart", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("touchstart", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, anchorRef, onDismiss]);

  if (!open) return null;

  return createPortal(
    <div
      id={id}
      ref={setRefs}
      className={["portal-ui-panel", className ?? ""].filter(Boolean).join(" ")}
      style={
        position
          ? {
              top: position.top,
              left: position.left,
              width: position.width,
              maxHeight: position.maxHeight,
            }
          : { opacity: 0, pointerEvents: "none" }
      }
    >
      {children}
    </div>,
    document.body,
  );
}
