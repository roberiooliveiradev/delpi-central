import { HelpCircle } from "lucide-react";
import {
  cloneElement,
  isValidElement,
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactElement,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

import { DELPI_UI_OVERLAY_Z_INDEX } from "../../overlayLayers";

export type HelpTooltipPlacement = "top" | "bottom";

export type HelpTooltipProps = {
  content: string;
  ariaLabel?: string;
  className?: string;
  wrap?: boolean;
  placement?: HelpTooltipPlacement;
  /**
   * Força ocultar o balão (ex.: menu aberto controlado pelo host).
   * Com `wrap`, também omite automaticamente se houver descendente
   * com `aria-expanded="true"` (popover/menu do gatilho).
   */
  suppressed?: boolean;
  children?: ReactNode;
};

type BubblePosition = {
  top: number;
  left: number;
  placement: HelpTooltipPlacement;
};

const VIEWPORT_MARGIN = 12;
const BUBBLE_GAP = 8;
const BUBBLE_MAX_WIDTH = "min(280px, calc(100vw - 24px))";

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

function clampHorizontal(left: number, width: number, viewport: ViewportMetrics): number {
  const minLeft = viewport.offsetLeft + VIEWPORT_MARGIN;
  const maxLeft = viewport.offsetLeft + viewport.width - width - VIEWPORT_MARGIN;
  return Math.min(Math.max(minLeft, left), Math.max(minLeft, maxLeft));
}

function computeBubblePosition(
  anchorRect: DOMRect,
  bubbleWidth: number,
  bubbleHeight: number,
  preferredPlacement: HelpTooltipPlacement,
  viewport: ViewportMetrics,
): BubblePosition {
  const viewportTop = viewport.offsetTop;
  const viewportBottom = viewport.offsetTop + viewport.height;

  const spaceAbove = anchorRect.top - viewportTop - VIEWPORT_MARGIN;
  const spaceBelow = viewportBottom - anchorRect.bottom - VIEWPORT_MARGIN;

  let placement = preferredPlacement;
  if (placement === "top" && spaceAbove < bubbleHeight + BUBBLE_GAP && spaceBelow >= spaceAbove) {
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
    viewportBottom - bubbleHeight - VIEWPORT_MARGIN,
  );

  const centeredLeft = anchorRect.left + anchorRect.width / 2 - bubbleWidth / 2;

  return {
    top,
    left: clampHorizontal(centeredLeft, bubbleWidth, viewport),
    placement,
  };
}

function bubbleLayoutStyle(position: BubblePosition | null, positioned: boolean): CSSProperties {
  const base: CSSProperties = {
    position: "fixed",
    zIndex: DELPI_UI_OVERLAY_Z_INDEX.helpTooltip,
    maxWidth: BUBBLE_MAX_WIDTH,
    minWidth: 200,
    boxSizing: "border-box",
    pointerEvents: "none",
  };

  if (position == null) {
    return { ...base, top: -9999, left: -9999, visibility: "hidden", opacity: 0 };
  }

  return {
    ...base,
    top: position.top,
    left: position.left,
    visibility: positioned ? "visible" : "hidden",
    opacity: positioned ? 1 : 0,
  };
}

function mergeDescribedBy(existing: string | undefined, tooltipId: string): string {
  if (!existing) return tooltipId;
  if (existing.split(/\s+/).includes(tooltipId)) return existing;
  return `${existing} ${tooltipId}`;
}

/** Gatilho (ou antecessor) com menu/popover aberto — balão não deve competir. */
function hasExpandedControl(root: ParentNode | null): boolean {
  if (!root || !(root instanceof Element)) return false;
  return Boolean(root.querySelector('[aria-expanded="true"]'));
}

/** Só `aria-describedby` — handlers de hover/foco ficam no hit-target (span),
 * porque muitos gatilhos (`RibbonColorPicker`, menus de forma) não encaminham
 * props de evento de `cloneElement` até o botão DOM. */
function wrapChildDescribedBy(child: ReactNode, tooltipId: string): ReactNode {
  if (!isValidElement(child)) return child;

  const element = child as ReactElement<{
    "aria-describedby"?: string;
  }>;

  return cloneElement(element, {
    "aria-describedby": mergeDescribedBy(element.props["aria-describedby"], tooltipId),
  });
}

/** Balão explicativo com portal no body (seguro em layouts com transform/overflow). */
export function HelpTooltip({
  content,
  ariaLabel = "Saiba mais",
  className,
  wrap = false,
  placement = "top",
  suppressed = false,
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
    "delpi-ui-help-tooltip",
    wrap ? "delpi-ui-help-tooltip--wrap" : "",
    visible ? "delpi-ui-help-tooltip--open" : "",
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
      computeBubblePosition(anchorRect, bubbleWidth, bubbleHeight, placement, getViewportMetrics()),
    );
    setPositioned(true);
  }, [placement]);

  const hideTooltip = useCallback(() => {
    setVisible(false);
    setPositioned(false);
    setBubblePosition(null);
  }, []);

  const isSuppressed = useCallback(() => {
    if (suppressed) return true;
    return wrap && hasExpandedControl(rootRef.current);
  }, [suppressed, wrap]);

  const showTooltip = useCallback(() => {
    if (isSuppressed()) return;
    setPositioned(false);
    setBubblePosition(null);
    setVisible(true);
  }, [isSuppressed]);

  useLayoutEffect(() => {
    if (visible && isSuppressed()) {
      hideTooltip();
    }
  });

  useEffect(() => {
    if (!wrap) return;
    const root = rootRef.current;
    if (!root) return;

    const syncExpanded = () => {
      if (hasExpandedControl(root)) hideTooltip();
    };

    const observer = new MutationObserver(syncExpanded);
    observer.observe(root, {
      attributes: true,
      subtree: true,
      attributeFilter: ["aria-expanded"],
    });
    return () => observer.disconnect();
  }, [wrap, hideTooltip]);

  useLayoutEffect(() => {
    if (!visible) return;
    if (isSuppressed()) {
      hideTooltip();
      return;
    }

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
  }, [visible, updateBubblePosition, content, placement, isSuppressed, hideTooltip]);

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
      bubble && typeof ResizeObserver !== "undefined" ? new ResizeObserver(handleReposition) : null;
    if (bubble && resizeObserver) resizeObserver.observe(bubble);

    return () => {
      window.removeEventListener("scroll", handleReposition, true);
      window.removeEventListener("resize", handleReposition);
      window.visualViewport?.removeEventListener("resize", handleReposition);
      window.visualViewport?.removeEventListener("scroll", handleReposition);
      resizeObserver?.disconnect();
    };
  }, [visible, updateBubblePosition]);

  const bubbleClass = [
    "delpi-ui-help-tooltip__bubble",
    bubblePosition?.placement === "top"
      ? "delpi-ui-help-tooltip__bubble--placement-top"
      : "delpi-ui-help-tooltip__bubble--placement-bottom",
    positioned ? "delpi-ui-help-tooltip__bubble--ready" : "",
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
      {...(wrap
        ? {
            onMouseEnter: showTooltip,
            onMouseLeave: hideTooltip,
            onFocus: showTooltip,
            onBlur: hideTooltip,
          }
        : {})}
    >
      {wrap ? (
        wrapChildDescribedBy(children, tooltipId)
      ) : (
        <button
          ref={triggerRef}
          type="button"
          className="delpi-ui-help-tooltip__trigger"
          aria-label={ariaLabel}
          aria-describedby={tooltipId}
          onClick={(event) => event.stopPropagation()}
          onMouseDown={(event) => event.stopPropagation()}
          {...interactionHandlers}
        >
          <HelpCircle size={14} aria-hidden="true" />
        </button>
      )}
      {visible && !isSuppressed() ? createPortal(bubble, document.body) : null}
    </span>
  );
}
