import { HelpCircle } from "lucide-react";
import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

type HelpTooltipProps = {
  content: string;
  ariaLabel?: string;
  className?: string;
  wrap?: boolean;
  /** Preferência inicial; inverte se não houver espaço na viewport. */
  placement?: "top" | "bottom";
  children?: ReactNode;
};

type BubblePosition = {
  top: number;
  left: number;
  placement: "top" | "bottom";
};

const VIEWPORT_MARGIN = 12;
const BUBBLE_GAP = 8;

function clampHorizontal(left: number, width: number): number {
  const maxLeft = window.innerWidth - width - VIEWPORT_MARGIN;
  return Math.min(Math.max(VIEWPORT_MARGIN, left), Math.max(VIEWPORT_MARGIN, maxLeft));
}

function computeBubblePosition(
  anchorRect: DOMRect,
  bubbleWidth: number,
  bubbleHeight: number,
  preferredPlacement: "top" | "bottom"
): BubblePosition {
  const spaceAbove = anchorRect.top - VIEWPORT_MARGIN;
  const spaceBelow = window.innerHeight - anchorRect.bottom - VIEWPORT_MARGIN;

  let placement = preferredPlacement;
  if (
    placement === "top" &&
    spaceAbove < bubbleHeight + BUBBLE_GAP &&
    spaceBelow >= spaceAbove
  ) {
    placement = "bottom";
  } else if (
    placement === "bottom" &&
    spaceBelow < bubbleHeight + BUBBLE_GAP &&
    spaceAbove > spaceBelow
  ) {
    placement = "top";
  }

  let top =
    placement === "top"
      ? anchorRect.top - bubbleHeight - BUBBLE_GAP
      : anchorRect.bottom + BUBBLE_GAP;

  top = Math.min(
    Math.max(VIEWPORT_MARGIN, top),
    window.innerHeight - bubbleHeight - VIEWPORT_MARGIN
  );

  const centeredLeft =
    anchorRect.left + anchorRect.width / 2 - bubbleWidth / 2;

  return {
    top,
    left: clampHorizontal(centeredLeft, bubbleWidth),
    placement,
  };
}

/** Fixed + coords de viewport exigem portal no body (ancestrais com transform quebram o posicionamento). */
function resolvePortalContainer(): HTMLElement {
  return document.body;
}

export function HelpTooltip({
  content,
  ariaLabel = "Saiba mais",
  className,
  wrap = false,
  placement = "top",
  children,
}: HelpTooltipProps) {
  const tooltipId = useId();
  const rootRef = useRef<HTMLSpanElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const bubbleRef = useRef<HTMLSpanElement>(null);
  const [visible, setVisible] = useState(false);
  const [bubblePosition, setBubblePosition] = useState<BubblePosition | null>(null);
  const [positioned, setPositioned] = useState(false);

  const rootClass = [
    "dq-help-tooltip",
    wrap ? "dq-help-tooltip--wrap" : "",
    visible ? "dq-help-tooltip--open" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const updateBubblePosition = useCallback(() => {
    const anchor = triggerRef.current ?? rootRef.current;
    const bubble = bubbleRef.current;
    if (!anchor || !bubble) return;

    const anchorRect = anchor.getBoundingClientRect();
    const bubbleWidth = bubble.offsetWidth;
    const bubbleHeight = bubble.offsetHeight;

    setBubblePosition(
      computeBubblePosition(anchorRect, bubbleWidth, bubbleHeight, placement)
    );
    setPositioned(true);
  }, [placement]);

  const showTooltip = useCallback(() => {
    setPositioned(false);
    setVisible(true);
  }, []);

  const hideTooltip = useCallback(() => {
    setVisible(false);
    setPositioned(false);
    setBubblePosition(null);
  }, []);

  useLayoutEffect(() => {
    if (!visible) return;
    updateBubblePosition();
  }, [visible, updateBubblePosition, content]);

  useEffect(() => {
    if (!visible) return;

    const handleReposition = () => {
      setPositioned(false);
      updateBubblePosition();
    };

    window.addEventListener("scroll", handleReposition, true);
    window.addEventListener("resize", handleReposition);

    return () => {
      window.removeEventListener("scroll", handleReposition, true);
      window.removeEventListener("resize", handleReposition);
    };
  }, [visible, updateBubblePosition]);

  const bubbleClass = [
    "dq-help-tooltip__bubble",
    "dq-help-tooltip__bubble--fixed",
    bubblePosition?.placement === "top"
      ? "dq-help-tooltip__bubble--placement-top"
      : "dq-help-tooltip__bubble--placement-bottom",
    positioned ? "dq-help-tooltip__bubble--ready" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const bubbleStyle =
    bubblePosition != null
      ? { top: bubblePosition.top, left: bubblePosition.left }
      : { top: -9999, left: -9999 };

  const bubble = (
    <span
      ref={bubbleRef}
      id={tooltipId}
      role="tooltip"
      className={bubbleClass}
      style={bubbleStyle}
    >
      {content}
    </span>
  );

  const interactionHandlers = {
    onMouseEnter: showTooltip,
    onMouseLeave: hideTooltip,
    onFocus: showTooltip,
    onBlur: hideTooltip,
  };

  return (
    <span
      ref={rootRef}
      className={rootClass}
      tabIndex={wrap ? 0 : undefined}
      aria-label={wrap ? ariaLabel : undefined}
      aria-describedby={wrap ? tooltipId : undefined}
      {...(wrap ? interactionHandlers : {})}
    >
      {wrap ? (
        children
      ) : (
        <button
          ref={triggerRef}
          type="button"
          className="dq-help-tooltip__trigger"
          aria-label={ariaLabel}
          aria-describedby={tooltipId}
          onClick={(event) => event.stopPropagation()}
          onMouseDown={(event) => event.stopPropagation()}
          {...interactionHandlers}
        >
          <HelpCircle size={14} aria-hidden="true" />
        </button>
      )}
      {visible ? createPortal(bubble, resolvePortalContainer()) : null}
    </span>
  );
}

export function FieldLabel({ label, hint }: { label: string; hint?: string }) {
  return (
    <span className="dq-field__label">
      {label}
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}
    </span>
  );
}
