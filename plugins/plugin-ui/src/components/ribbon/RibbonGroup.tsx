import { ChevronDown, type LucideIcon } from "lucide-react";
import {
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { SectionHintLabel } from "../help/SectionHintLabel";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  measureElementContentWidth,
  useRibbonOverflowContext,
} from "./RibbonGroupsRow";
import { ribbonGroupWidthsNearlyEqual } from "./resolveCollapsedRibbonGroupIds";
import { RibbonGroupSurfaceProvider } from "./RibbonGroupSurfaceContext";

export type RibbonGroupClassNames = {
  root: string;
  rootWide: string;
  rootCollapsed: string;
  rootNoCaption: string;
  rootCaptionAbove: string;
  body: string;
  caption: string;
  captionAbove: string;
  captionText: string;
  collapseTrigger: string;
  collapseIcon: string;
  collapseLabel: string;
  collapseChevron: string;
  popover: string;
  popoverBody: string;
  popoverCaption: string;
  measure: string;
};

export function ribbonGroupBemClasses(prefix = "delpi-ui"): RibbonGroupClassNames {
  const base = `${prefix}-ribbon-group`;
  const ui = "delpi-ui-ribbon-group";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    rootWide: pair(`${base}--wide`, `${ui}--wide`),
    rootCollapsed: pair(`${base}--collapsed`, `${ui}--collapsed`),
    rootNoCaption: pair(`${base}--no-caption`, `${ui}--no-caption`),
    rootCaptionAbove: pair(`${base}--caption-above`, `${ui}--caption-above`),
    body: pair(`${base}__body`, `${ui}__body`),
    caption: pair(`${base}__caption`, `${ui}__caption`),
    captionAbove: pair(`${base}__caption--above`, `${ui}__caption--above`),
    captionText: pair(`${base}__caption-text`, `${ui}__caption-text`),
    collapseTrigger: pair(`${base}__collapse-trigger`, `${ui}__collapse-trigger`),
    collapseIcon: pair(`${base}__collapse-icon`, `${ui}__collapse-icon`),
    collapseLabel: pair(`${base}__collapse-label`, `${ui}__collapse-label`),
    collapseChevron: pair(`${base}__collapse-chevron`, `${ui}__collapse-chevron`),
    popover: pair(`${base}__popover`, `${ui}__popover`),
    popoverBody: pair(`${base}__popover-body`, `${ui}__popover-body`),
    popoverCaption: pair(`${base}__popover-caption`, `${ui}__popover-caption`),
    measure: pair(`${base}__measure`, `${ui}__measure`),
  };
}

const DEFAULT_CN = ribbonGroupBemClasses();

export type RibbonGroupProps = {
  /** Id estável para overflow; sem id o grupo não colapsa. */
  groupId?: string;
  label: string;
  hint?: string;
  wide?: boolean;
  captionPlacement?: "below" | "above" | "none";
  /** Ordem visual na faixa (0 = esquerda). */
  order?: number;
  collapseIcon?: LucideIcon;
  className?: string;
  classNames?: RibbonGroupClassNames;
  children: ReactNode;
};

let nextOrderSeq = 0;

/**
 * Grupo de ribbon: expandido (controles + caption) ou colapsado (botão → popover).
 * CSS: `styles/ribbon-overflow.css`.
 */
export function RibbonGroup({
  groupId,
  label,
  hint,
  wide,
  captionPlacement = "below",
  order: orderProp,
  collapseIcon: CollapseIcon,
  className,
  classNames = DEFAULT_CN,
  children,
}: RibbonGroupProps) {
  const ctx = useRibbonOverflowContext();
  const orderRef = useRef<number | null>(orderProp ?? null);
  if (orderRef.current == null) {
    orderRef.current = orderProp ?? nextOrderSeq++;
  }
  if (orderProp != null) orderRef.current = orderProp;
  const order = orderRef.current;

  const canCollapse = Boolean(groupId && ctx);
  const collapsed = Boolean(canCollapse && groupId && ctx?.collapsedIds.has(groupId));
  const [popoverOpen, setPopoverOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const cachedExpanded = useRef(0);
  const cachedCollapsed = useRef(56);
  const reactId = useId();
  const resolvedId = groupId ?? `ribbon-group-${reactId}`;

  useLayoutEffect(() => {
    if (!collapsed) setPopoverOpen(false);
  }, [collapsed]);

  const registerRef = useRef(ctx?.registerGroup);
  const unregisterRef = useRef(ctx?.unregisterGroup);
  registerRef.current = ctx?.registerGroup;
  unregisterRef.current = ctx?.unregisterGroup;

  useLayoutEffect(() => {
    if (!groupId || !registerRef.current) return;
    if (!collapsed && rootRef.current) {
      const w = measureElementContentWidth(rootRef.current);
      if (w > 0) cachedExpanded.current = w;
    }
    if (triggerRef.current) {
      /* Força medida mesmo com classe measure (visually hidden). */
      const cw =
        Math.ceil(triggerRef.current.scrollWidth) ||
        measureElementContentWidth(triggerRef.current);
      if (cw > 0) cachedCollapsed.current = cw;
    }
    registerRef.current(groupId, {
      expandedWidth: cachedExpanded.current || cachedCollapsed.current,
      collapsedWidth: cachedCollapsed.current,
      order,
    });
    /* Sem `children`: re-render do pai não deve re-registrar e alimentar o loop RO. */
  }, [collapsed, groupId, order]);

  useLayoutEffect(() => {
    if (!groupId || !registerRef.current || typeof ResizeObserver === "undefined") {
      return;
    }
    const node = rootRef.current;
    if (!node || collapsed) return;
    const observer = new ResizeObserver(() => {
      const w = measureElementContentWidth(node);
      if (!(w > 0) || ribbonGroupWidthsNearlyEqual(w, cachedExpanded.current)) return;
      cachedExpanded.current = w;
      registerRef.current?.(groupId, {
        expandedWidth: w,
        collapsedWidth: cachedCollapsed.current,
        order,
      });
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, [collapsed, groupId, order]);

  useLayoutEffect(() => {
    if (!groupId) return;
    return () => unregisterRef.current?.(groupId);
  }, [groupId]);

  const caption =
    captionPlacement === "none" ? null : (
      <div
        className={[
          classNames.caption,
          captionPlacement === "above" ? classNames.captionAbove : null,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {hint ? (
          <SectionHintLabel label={label} hint={hint} className={classNames.captionText} />
        ) : (
          <span className={classNames.captionText}>{label}</span>
        )}
      </div>
    );

  const trigger = (
    <button
      ref={triggerRef}
      type="button"
      className={[
        classNames.collapseTrigger,
        collapsed ? null : classNames.measure,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label={label}
      aria-expanded={popoverOpen}
      aria-haspopup="dialog"
      tabIndex={collapsed ? 0 : -1}
      onClick={() => {
        if (!collapsed) return;
        setPopoverOpen((open) => !open);
      }}
    >
      {CollapseIcon ? (
        <span className={classNames.collapseIcon} aria-hidden="true">
          <CollapseIcon size={18} />
        </span>
      ) : null}
      <span className={classNames.collapseLabel}>{label}</span>
      <ChevronDown size={14} className={classNames.collapseChevron} aria-hidden="true" />
    </button>
  );

  if (collapsed) {
    return (
      <div
        className={[
          classNames.root,
          classNames.rootCollapsed,
          wide ? classNames.rootWide : null,
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        data-ribbon-group-id={resolvedId}
        data-ribbon-group-mode="collapsed"
      >
        {trigger}
        <AnchoredPanelPortal
          open={popoverOpen}
          anchorRef={triggerRef}
          panelRef={panelRef}
          variant="bare"
          role="dialog"
          aria-label={label}
          density="compact"
          preferredPlacement="bottom"
          portalScopeClassName={ctx?.portalScopeClassName}
          onDismiss={() => setPopoverOpen(false)}
        >
          <div ref={panelRef} className={classNames.popover} data-delpi-ui-density="compact">
            <div className={classNames.popoverBody}>
              <RibbonGroupSurfaceProvider value="section-popover">{children}</RibbonGroupSurfaceProvider>
            </div>
            <div className={classNames.popoverCaption}>{label}</div>
          </div>
        </AnchoredPanelPortal>
      </div>
    );
  }

  return (
    <div
      ref={rootRef}
      className={[
        classNames.root,
        wide ? classNames.rootWide : null,
        captionPlacement === "none" ? classNames.rootNoCaption : null,
        captionPlacement === "above" ? classNames.rootCaptionAbove : null,
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      data-ribbon-group-id={resolvedId}
      data-ribbon-group-mode="expanded"
    >
      {captionPlacement === "above" ? caption : null}
      <div className={classNames.body}>{children}</div>
      {captionPlacement === "below" ? caption : null}
      {canCollapse ? trigger : null}
    </div>
  );
}
