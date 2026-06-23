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
  placement?: "top" | "bottom";
  fixed?: boolean;
  children?: ReactNode;
};

function clampLeft(left: number, width: number): number {
  const margin = 12;
  const maxLeft = window.innerWidth - width - margin;
  return Math.min(Math.max(margin, left), Math.max(margin, maxLeft));
}

export function HelpTooltip({
  content,
  ariaLabel = "Saiba mais",
  className,
  wrap = false,
  placement = "top",
  fixed = false,
  children,
}: HelpTooltipProps) {
  const tooltipId = useId();
  const rootRef = useRef<HTMLSpanElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const bubbleRef = useRef<HTMLSpanElement>(null);
  const [visible, setVisible] = useState(false);
  const [fixedPosition, setFixedPosition] = useState<{ top: number; left: number } | null>(
    null
  );
  const useFixedBubble = fixed;

  const rootClass = [
    "dc-help-tooltip",
    wrap ? "dc-help-tooltip--wrap" : "",
    placement === "bottom" && !fixed ? "dc-help-tooltip--bottom" : "",
    visible && useFixedBubble ? "dc-help-tooltip--open" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const updateFixedPosition = useCallback(() => {
    const anchor = triggerRef.current ?? rootRef.current;
    if (!anchor) return;

    const rect = anchor.getBoundingClientRect();
    const bubbleWidth = bubbleRef.current?.offsetWidth ?? 240;
    setFixedPosition({
      top: rect.bottom + 8,
      left: clampLeft(rect.left, bubbleWidth),
    });
  }, []);

  const showTooltip = useCallback(() => {
    setVisible(true);
  }, []);

  const hideTooltip = useCallback(() => {
    setVisible(false);
  }, []);

  useLayoutEffect(() => {
    if (!visible || !useFixedBubble) return;
    updateFixedPosition();
  }, [visible, useFixedBubble, updateFixedPosition, content]);

  useEffect(() => {
    if (!visible || !useFixedBubble) return;

    const handleReposition = () => updateFixedPosition();
    window.addEventListener("scroll", handleReposition, true);
    window.addEventListener("resize", handleReposition);

    return () => {
      window.removeEventListener("scroll", handleReposition, true);
      window.removeEventListener("resize", handleReposition);
    };
  }, [visible, useFixedBubble, updateFixedPosition]);

  const bubbleClass = [
    "dc-help-tooltip__bubble",
    useFixedBubble ? "dc-help-tooltip__bubble--fixed" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const bubbleStyle =
    useFixedBubble && fixedPosition
      ? { top: fixedPosition.top, left: fixedPosition.left }
      : undefined;

  const bubble = (
    <span
      ref={useFixedBubble ? bubbleRef : undefined}
      id={tooltipId}
      role="tooltip"
      className={bubbleClass}
      style={bubbleStyle}
    >
      {content}
    </span>
  );

  return (
    <span
      ref={rootRef}
      className={rootClass}
      tabIndex={wrap ? 0 : undefined}
      aria-label={wrap ? ariaLabel : undefined}
      aria-describedby={wrap ? tooltipId : undefined}
      onMouseEnter={wrap && useFixedBubble ? showTooltip : undefined}
      onMouseLeave={wrap && useFixedBubble ? hideTooltip : undefined}
      onFocus={wrap && useFixedBubble ? showTooltip : undefined}
      onBlur={wrap && useFixedBubble ? hideTooltip : undefined}
    >
      {wrap ? (
        children
      ) : (
        <button
          ref={triggerRef}
          type="button"
          className="dc-help-tooltip__trigger"
          aria-label={ariaLabel}
          aria-describedby={tooltipId}
          title={content}
          onClick={(event) => event.stopPropagation()}
          onMouseDown={(event) => event.stopPropagation()}
          onMouseEnter={useFixedBubble ? showTooltip : undefined}
          onMouseLeave={useFixedBubble ? hideTooltip : undefined}
          onFocus={useFixedBubble ? showTooltip : undefined}
          onBlur={useFixedBubble ? hideTooltip : undefined}
        >
          <HelpCircle size={14} aria-hidden="true" />
        </button>
      )}
      {useFixedBubble
        ? visible
          ? createPortal(bubble, document.body)
          : null
        : bubble}
    </span>
  );
}

export function FieldLabel({ label, hint }: { label: string; hint?: string }) {
  return (
    <span className="dc-field__label">
      {label}
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}
    </span>
  );
}
