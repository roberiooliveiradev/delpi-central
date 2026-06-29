import { HelpCircle } from "lucide-react";
import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
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
const BUBBLE_MAX_WIDTH = "min(280px, calc(100vw - 24px))";
/** Acima de .pac-modal-overlay (10050) e tooltips do portal (~10060). */
const TOOLTIP_Z_INDEX = 10200;

type ViewportMetrics = {
  width: number;
  height: number;
  offsetLeft: number;
  offsetTop: number;
};

function getViewportMetrics(): ViewportMetrics {
  const visualViewport = window.visualViewport;
  return {
    width: visualViewport?.width ?? window.innerWidth,
    height: visualViewport?.height ?? window.innerHeight,
    offsetLeft: visualViewport?.offsetLeft ?? 0,
    offsetTop: visualViewport?.offsetTop ?? 0,
  };
}

function clampHorizontal(
  left: number,
  width: number,
  viewport: ViewportMetrics
): number {
  const minLeft = viewport.offsetLeft + VIEWPORT_MARGIN;
  const maxLeft =
    viewport.offsetLeft + viewport.width - width - VIEWPORT_MARGIN;
  return Math.min(Math.max(minLeft, left), Math.max(minLeft, maxLeft));
}

function computeBubblePosition(
  anchorRect: DOMRect,
  bubbleWidth: number,
  bubbleHeight: number,
  preferredPlacement: "top" | "bottom",
  viewport: ViewportMetrics
): BubblePosition {
  const viewportTop = viewport.offsetTop;
  const viewportBottom = viewport.offsetTop + viewport.height;

  const spaceAbove = anchorRect.top - viewportTop - VIEWPORT_MARGIN;
  const spaceBelow = viewportBottom - anchorRect.bottom - VIEWPORT_MARGIN;

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
    Math.max(viewportTop + VIEWPORT_MARGIN, top),
    viewportBottom - bubbleHeight - VIEWPORT_MARGIN
  );

  const centeredLeft =
    anchorRect.left + anchorRect.width / 2 - bubbleWidth / 2;

  return {
    top,
    left: clampHorizontal(centeredLeft, bubbleWidth, viewport),
    placement,
  };
}

function bubbleLayoutStyle(
  position: BubblePosition | null,
  positioned: boolean
): CSSProperties {
  const base: CSSProperties = {
    position: "fixed",
    zIndex: TOOLTIP_Z_INDEX,
    maxWidth: BUBBLE_MAX_WIDTH,
    minWidth: 200,
    boxSizing: "border-box",
    pointerEvents: "none",
  };

  if (position == null) {
    return {
      ...base,
      top: -9999,
      left: -9999,
      visibility: "hidden",
      opacity: 0,
    };
  }

  return {
    ...base,
    top: position.top,
    left: position.left,
    visibility: positioned ? "visible" : "hidden",
    opacity: positioned ? 1 : 0,
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
  const [bubblePosition, setBubblePosition] = useState<BubblePosition | null>(
    null
  );
  const [positioned, setPositioned] = useState(false);

  const rootClass = [
    "pac-help-tooltip",
    wrap ? "pac-help-tooltip--wrap" : "",
    visible ? "pac-help-tooltip--open" : "",
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
    if (bubbleWidth <= 0 || bubbleHeight <= 0) return;

    setBubblePosition(
      computeBubblePosition(
        anchorRect,
        bubbleWidth,
        bubbleHeight,
        placement,
        getViewportMetrics()
      )
    );
    setPositioned(true);
  }, [placement]);

  const showTooltip = useCallback(() => {
    setPositioned(false);
    setBubblePosition(null);
    setVisible(true);
  }, []);

  const hideTooltip = useCallback(() => {
    setVisible(false);
    setPositioned(false);
    setBubblePosition(null);
  }, []);

  useLayoutEffect(() => {
    if (!visible) return;

    setPositioned(false);
    setBubblePosition({ top: -9999, left: -9999, placement });

    let raf2 = 0;
    const raf1 = requestAnimationFrame(() => {
      updateBubblePosition();
      raf2 = requestAnimationFrame(updateBubblePosition);
    });

    return () => {
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
    };
  }, [visible, updateBubblePosition, content, placement]);

  useEffect(() => {
    if (!visible) return;

    const handleReposition = () => {
      setPositioned(false);
      updateBubblePosition();
    };

    window.addEventListener("scroll", handleReposition, true);
    window.addEventListener("resize", handleReposition);
    window.visualViewport?.addEventListener("resize", handleReposition);
    window.visualViewport?.addEventListener("scroll", handleReposition);

    const bubble = bubbleRef.current;
    const resizeObserver =
      bubble && typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(handleReposition)
        : null;
    if (bubble && resizeObserver) {
      resizeObserver.observe(bubble);
    }

    return () => {
      window.removeEventListener("scroll", handleReposition, true);
      window.removeEventListener("resize", handleReposition);
      window.visualViewport?.removeEventListener("resize", handleReposition);
      window.visualViewport?.removeEventListener("scroll", handleReposition);
      resizeObserver?.disconnect();
    };
  }, [visible, updateBubblePosition]);

  const bubbleClass = [
    "pac-help-tooltip__bubble",
    "pac-help-tooltip__bubble--fixed",
    bubblePosition?.placement === "top"
      ? "pac-help-tooltip__bubble--placement-top"
      : "pac-help-tooltip__bubble--placement-bottom",
    positioned ? "pac-help-tooltip__bubble--ready" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const bubble = (
    <span
      ref={bubbleRef}
      id={tooltipId}
      role="tooltip"
      className={bubbleClass}
      style={bubbleLayoutStyle(bubblePosition, positioned)}
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
          className="pac-help-tooltip__trigger"
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
    <span className="pac-field__label-row">
      <span>{label}</span>
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}
    </span>
  );
}
export function TitleWithHelp({
  title,
  hint,
  className,
}: {
  title: string;
  hint?: string;
  className?: string;
}) {
  return (
    <span className={`pac-title-with-help${className ? ` ${className}` : ""}`}>
      <span>{title}</span>
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${title}`} /> : null}
    </span>
  );
}

type TableHeaderCellProps = {
  label: string;
  hint?: string;
  className?: string;
  scope?: "col" | "row";
};

/** Cabeçalho de coluna com balão de ajuda (?), padrão das tabelas do plugin. */
export function TableHeaderCell({
  label,
  hint,
  className,
  scope = "col",
}: TableHeaderCellProps) {
  return (
    <th className={className} scope={scope}>
      {hint ? <FieldLabel label={label} hint={hint} /> : label}
    </th>
  );
}
