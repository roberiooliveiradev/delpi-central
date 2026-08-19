import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export const RESIZABLE_COLUMNS_MIN_LEFT_PX = 240;
export const RESIZABLE_COLUMNS_MAX_LEFT_RATIO = 0.4;
export const RESIZABLE_COLUMNS_DEFAULT_LEFT_RATIO = 0.2;
export const RESIZABLE_COLUMNS_COLLAPSED_RAIL_PX = 36;
export const RESIZABLE_COLUMNS_KEYBOARD_STEP_PX = 16;

export type ResizableColumnsClassNames = {
  root: string;
  rootCollapsed: string;
  left: string;
  leftRail: string;
  right: string;
  handle: string;
  collapse: string;
};

export type ResizableColumnsLabels = {
  separatorAriaLabel: string;
  collapseAriaLabel: string;
  expandAriaLabel: string;
};

export type ResizableColumnsProps = {
  left: ReactNode;
  right: ReactNode;
  classNames: ResizableColumnsClassNames;
  labels: ResizableColumnsLabels;
  leftWidthPx?: number;
  defaultLeftWidthPx?: number;
  collapsed?: boolean;
  defaultCollapsed?: boolean;
  minLeftPx?: number;
  maxLeftRatio?: number;
  onLeftWidthChange?: (widthPx: number) => void;
  onCollapsedChange?: (collapsed: boolean) => void;
  className?: string;
};

export function resizableColumnsBemClasses(prefix: string): ResizableColumnsClassNames {
  const base = `${prefix}-resizable-columns`;
  const ui = "delpi-ui-resizable-columns";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    rootCollapsed: pair(`${base} ${base}--collapsed`, `${ui} ${ui}--collapsed`),
    left: pair(`${base}__left`, `${ui}__left`),
    leftRail: pair(`${base}__left ${base}__left--rail`, `${ui}__left ${ui}__left--rail`),
    right: pair(`${base}__right`, `${ui}__right`),
    handle: pair(`${base}__handle`, `${ui}__handle`),
    collapse: pair(`${base}__collapse`, `${ui}__collapse`),
  };
}

function clampLeftWidth(
  width: number,
  containerWidth: number,
  minLeftPx: number,
  maxLeftRatio: number,
): number {
  if (containerWidth <= 0) {
    return Math.max(minLeftPx, Math.round(width));
  }
  const maxPx = Math.max(minLeftPx, Math.floor(containerWidth * maxLeftRatio));
  return Math.min(maxPx, Math.max(minLeftPx, Math.round(width)));
}

export function ResizableColumns({
  left,
  right,
  classNames,
  labels,
  leftWidthPx,
  defaultLeftWidthPx,
  collapsed,
  defaultCollapsed = false,
  minLeftPx = RESIZABLE_COLUMNS_MIN_LEFT_PX,
  maxLeftRatio = RESIZABLE_COLUMNS_MAX_LEFT_RATIO,
  onLeftWidthChange,
  onCollapsedChange,
  className,
}: ResizableColumnsProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const separatorId = useId();
  const [containerWidth, setContainerWidth] = useState(0);
  const [internalWidth, setInternalWidth] = useState(
    defaultLeftWidthPx ?? minLeftPx,
  );
  const [internalCollapsed, setInternalCollapsed] = useState(defaultCollapsed);
  const dragging = useRef(false);

  const isCollapsed = collapsed ?? internalCollapsed;
  const measuredDefault =
    containerWidth > 0
      ? clampLeftWidth(
          defaultLeftWidthPx ??
            containerWidth * RESIZABLE_COLUMNS_DEFAULT_LEFT_RATIO,
          containerWidth,
          minLeftPx,
          maxLeftRatio,
        )
      : defaultLeftWidthPx ?? minLeftPx;
  const rawWidth = leftWidthPx ?? (containerWidth > 0 ? internalWidth : measuredDefault);
  const width =
    containerWidth > 0
      ? clampLeftWidth(rawWidth, containerWidth, minLeftPx, maxLeftRatio)
      : Math.max(minLeftPx, Math.round(rawWidth));

  useEffect(() => {
    const el = rootRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver((entries) => {
      const next = entries[0]?.contentRect.width ?? 0;
      setContainerWidth(next);
    });
    observer.observe(el);
    setContainerWidth(el.getBoundingClientRect().width);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (leftWidthPx != null || containerWidth <= 0) return;
    setInternalWidth((current) =>
      current === minLeftPx && defaultLeftWidthPx == null
        ? clampLeftWidth(
            containerWidth * RESIZABLE_COLUMNS_DEFAULT_LEFT_RATIO,
            containerWidth,
            minLeftPx,
            maxLeftRatio,
          )
        : clampLeftWidth(current, containerWidth, minLeftPx, maxLeftRatio),
    );
  }, [containerWidth, defaultLeftWidthPx, leftWidthPx, maxLeftRatio, minLeftPx]);

  const setWidth = useCallback(
    (next: number) => {
      const clamped =
        containerWidth > 0
          ? clampLeftWidth(next, containerWidth, minLeftPx, maxLeftRatio)
          : Math.max(minLeftPx, Math.round(next));
      if (leftWidthPx == null) setInternalWidth(clamped);
      onLeftWidthChange?.(clamped);
    },
    [containerWidth, leftWidthPx, maxLeftRatio, minLeftPx, onLeftWidthChange],
  );

  const setCollapsed = useCallback(
    (next: boolean) => {
      if (collapsed == null) setInternalCollapsed(next);
      onCollapsedChange?.(next);
    },
    [collapsed, onCollapsedChange],
  );

  const onPointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (isCollapsed || event.button !== 0) return;
    dragging.current = true;
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const onPointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!dragging.current || isCollapsed) return;
    const root = rootRef.current;
    if (!root) return;
    const leftEdge = root.getBoundingClientRect().left;
    setWidth(event.clientX - leftEdge);
  };

  const onPointerUp = () => {
    dragging.current = false;
  };

  const onHandleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (isCollapsed) return;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      setWidth(width - RESIZABLE_COLUMNS_KEYBOARD_STEP_PX);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      setWidth(width + RESIZABLE_COLUMNS_KEYBOARD_STEP_PX);
    }
  };

  const rootClass = [
    isCollapsed ? classNames.rootCollapsed : classNames.root,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div ref={rootRef} className={rootClass}>
      <div
        className={isCollapsed ? classNames.leftRail : classNames.left}
        style={
          isCollapsed
            ? { width: RESIZABLE_COLUMNS_COLLAPSED_RAIL_PX }
            : { width }
        }
      >
        {isCollapsed ? null : left}
      </div>
      <div
        id={separatorId}
        className={classNames.handle}
        role="separator"
        aria-orientation="vertical"
        aria-label={labels.separatorAriaLabel}
        aria-valuenow={isCollapsed ? RESIZABLE_COLUMNS_COLLAPSED_RAIL_PX : width}
        tabIndex={isCollapsed ? -1 : 0}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onKeyDown={onHandleKeyDown}
      >
        <button
          type="button"
          className={classNames.collapse}
          aria-label={
            isCollapsed ? labels.expandAriaLabel : labels.collapseAriaLabel
          }
          onClick={() => setCollapsed(!isCollapsed)}
        >
          {isCollapsed ? (
            <PanelLeftOpen size={16} aria-hidden />
          ) : (
            <PanelLeftClose size={16} aria-hidden />
          )}
        </button>
      </div>
      <div className={classNames.right}>{right}</div>
    </div>
  );
}

export type DashboardResizableColumnsProps = Omit<ResizableColumnsProps, "classNames">;

export function createDashboardResizableColumns(prefix: string) {
  const classNames = resizableColumnsBemClasses(prefix);
  return function DashboardResizableColumns(props: DashboardResizableColumnsProps) {
    return <ResizableColumns classNames={classNames} {...props} />;
  };
}
