import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";
import { ChevronDown, ChevronUp, Menu } from "lucide-react";

import { usePersistedBoolean } from "../../hooks/usePersistedBoolean";
import { useTopBarOverflowCollapsed } from "../../hooks/useTopBarOverflowCollapsed";
import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import { IconButton } from "../actions/IconButton";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import {
  UnderlineNav,
  underlineNavBemClasses,
  type UnderlineNavClassNames,
  type UnderlineNavItem,
} from "./UnderlineNav";

export type TopBarCollapseMode = "rail" | "hamburger";
export type TopBarCollapseTrigger = "manual" | "overflow";

export type TopBarClassNames = {
  root: string;
  row: string;
  nav: string;
  secondary: string;
  actions: string;
  collapseToggle: string;
  collapsedRail: string;
  collapsedTitle: string;
  measure: string;
  menuPanel: string;
  menuList: string;
  menuItem: string;
  menuItemActive: string;
  menuItemLabel: string;
  menuItemCount: string;
};

export type TopBarProps = {
  items: UnderlineNavItem[];
  activeId: string;
  classNames: TopBarClassNames;
  navClassNames: UnderlineNavClassNames;
  /** Slot entre nav e actions (ex.: favoritos). */
  secondary?: ReactNode;
  /** Slot à direita (escopo, ações). */
  actions?: ReactNode;
  /** Extensão lateral alinhada ao padding da página (padrão admin). */
  bleed?: boolean;
  sticky?: boolean;
  /** Fundo surface (banda). Default false = flush com a página. */
  surface?: boolean;
  /** Enables collapse chrome (rail or hamburger). */
  collapsible?: boolean;
  /** Visual mode when collapsed. Default `rail`. */
  collapseMode?: TopBarCollapseMode;
  /**
   * `manual` — toggle + optional localStorage.
   * `overflow` — hamburger when measure row exceeds host width (responsive).
   */
  collapseTrigger?: TopBarCollapseTrigger;
  /** Persist collapsed state as `"1"` / `"0"` (manual trigger only). */
  storageKey?: string;
  /** Controlled collapsed state (manual trigger only). */
  collapsed?: boolean;
  defaultCollapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  /** aria-label when expanded (recolher) — manual trigger. */
  collapseLabel?: string;
  /** aria-label when collapsed (expandir) — manual trigger. */
  expandLabel?: string;
  /** aria-label for hamburger menu trigger + panel. */
  menuLabel?: string;
  /** MFE root class for portal CSS scope (ex.: `dashboard-commercial`). */
  portalScopeClassName?: string;
  className?: string;
  "aria-label"?: string;
};

export function topBarBemClasses(prefix: string): TopBarClassNames {
  return {
    root: delpiUiClass(`${prefix}-topbar`, "delpi-ui-topbar"),
    row: delpiUiClass(`${prefix}-topbar__row`, "delpi-ui-topbar__row"),
    nav: delpiUiClass(`${prefix}-topbar__nav`, "delpi-ui-topbar__nav"),
    secondary: delpiUiClass(`${prefix}-topbar__secondary`, "delpi-ui-topbar__secondary"),
    actions: delpiUiClass(`${prefix}-topbar__actions`, "delpi-ui-topbar__actions"),
    collapseToggle: delpiUiClass(
      `${prefix}-topbar__collapse-toggle`,
      "delpi-ui-topbar__collapse-toggle",
    ),
    collapsedRail: delpiUiClass(
      `${prefix}-topbar__collapsed-rail`,
      "delpi-ui-topbar__collapsed-rail",
    ),
    collapsedTitle: delpiUiClass(
      `${prefix}-topbar__collapsed-title`,
      "delpi-ui-topbar__collapsed-title",
    ),
    measure: delpiUiClass(`${prefix}-topbar__measure`, "delpi-ui-topbar__measure"),
    menuPanel: delpiUiClass(
      `${prefix}-topbar__menu-panel`,
      "delpi-ui-topbar__menu-panel",
    ),
    menuList: delpiUiClass(
      `${prefix}-topbar__menu-list`,
      "delpi-ui-topbar__menu-list",
    ),
    menuItem: delpiUiClass(
      `${prefix}-topbar__menu-item`,
      "delpi-ui-topbar__menu-item",
    ),
    menuItemActive: delpiUiClass(
      `${prefix}-topbar__menu-item--active`,
      "delpi-ui-topbar__menu-item--active",
    ),
    menuItemLabel: delpiUiClass(
      `${prefix}-topbar__menu-item-label`,
      "delpi-ui-topbar__menu-item-label",
    ),
    menuItemCount: delpiUiClass(
      `${prefix}-topbar__menu-item-count`,
      "delpi-ui-topbar__menu-item-count",
    ),
  };
}

function useManualCollapsedState(options: {
  collapsible: boolean;
  storageKey?: string;
  collapsed?: boolean;
  defaultCollapsed: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
}) {
  const {
    collapsible,
    storageKey,
    collapsed: collapsedControlled,
    defaultCollapsed,
    onCollapsedChange,
  } = options;

  const isControlled = collapsedControlled !== undefined;
  const persist = Boolean(collapsible && storageKey && !isControlled);

  const persisted = usePersistedBoolean({
    storageKey: storageKey ?? "delpi.plugin-ui.topbar.collapsed",
    defaultValue: defaultCollapsed,
    enabled: persist,
  });

  const [uncontrolled, setUncontrolled] = useState(defaultCollapsed);

  const collapsed = isControlled
    ? Boolean(collapsedControlled)
    : persist
      ? persisted.value
      : uncontrolled;

  const setCollapsed = (next: boolean) => {
    if (isControlled) {
      onCollapsedChange?.(next);
      return;
    }
    if (persist) {
      persisted.setValue(next);
    } else {
      setUncontrolled(next);
    }
    onCollapsedChange?.(next);
  };

  return { collapsed, setCollapsed };
}

function TopBarHamburgerMenu({
  open,
  anchorRef,
  items,
  activeId,
  classNames,
  menuLabel,
  portalScopeClassName,
  onDismiss,
}: {
  open: boolean;
  anchorRef: RefObject<HTMLElement | null>;
  items: UnderlineNavItem[];
  activeId: string;
  classNames: TopBarClassNames;
  menuLabel: string;
  portalScopeClassName?: string;
  onDismiss: () => void;
}) {
  const panelRef = useRef<HTMLDivElement>(null);

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      role="menu"
      aria-label={menuLabel}
      preferredPlacement="bottom"
      horizontalAlign="start"
      portalScopeClassName={portalScopeClassName}
      onDismiss={onDismiss}
    >
      <div ref={panelRef} className={classNames.menuPanel}>
        <ul className={classNames.menuList} role="none">
          {items.map((item) => {
            const active = item.id === activeId;
            const count =
              typeof item.count === "number" && item.count > 0 ? item.count : null;
            return (
              <li key={item.id} role="none">
                <button
                  type="button"
                  role="menuitem"
                  className={[
                    classNames.menuItem,
                    active ? classNames.menuItemActive : null,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  title={item.title}
                  aria-current={active ? "page" : undefined}
                  onClick={() => {
                    item.onSelect?.();
                    onDismiss();
                  }}
                >
                  {item.icon ? (
                    <span className="delpi-ui-topbar__menu-item-icon" aria-hidden>
                      {item.icon}
                    </span>
                  ) : null}
                  <span className={classNames.menuItemLabel}>{item.label}</span>
                  {count != null ? (
                    <span className={classNames.menuItemCount} aria-hidden>
                      {count > 99 ? "99+" : count}
                    </span>
                  ) : null}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </AnchoredPanelPortal>
  );
}

type TopBarExpandedRowProps = {
  classNames: TopBarClassNames;
  navClassNames: UnderlineNavClassNames;
  items: UnderlineNavItem[];
  activeId: string;
  ariaLabel: string;
  secondary?: ReactNode;
  actions?: ReactNode;
  collapseToggle?: ReactNode;
  rowClassName?: string;
};

function TopBarExpandedRow({
  classNames,
  navClassNames,
  items,
  activeId,
  ariaLabel,
  secondary,
  actions,
  collapseToggle,
  rowClassName,
}: TopBarExpandedRowProps) {
  return (
    <div className={[classNames.row, rowClassName].filter(Boolean).join(" ")}>
      <div className={classNames.nav}>
        <UnderlineNav
          classNames={navClassNames}
          items={items}
          activeId={activeId}
          aria-label={ariaLabel}
        />
      </div>
      {secondary ? <div className={classNames.secondary}>{secondary}</div> : null}
      {actions ? <div className={classNames.actions}>{actions}</div> : null}
      {collapseToggle}
    </div>
  );
}

export function TopBar({
  items,
  activeId,
  classNames,
  navClassNames,
  secondary,
  actions,
  bleed = true,
  sticky = true,
  surface = false,
  collapsible = false,
  collapseMode = "rail",
  collapseTrigger = "manual",
  storageKey,
  collapsed: collapsedProp,
  defaultCollapsed = false,
  onCollapsedChange,
  collapseLabel = "Collapse navigation",
  expandLabel = "Expand navigation",
  menuLabel = "Navigation menu",
  portalScopeClassName,
  className,
  "aria-label": ariaLabel = "Navegação",
}: TopBarProps) {
  const mode = collapseMode === "hamburger" ? "hamburger" : "rail";
  const responsiveOverflow =
    collapsible && collapseTrigger === "overflow" && mode === "hamburger";

  const manualState = useManualCollapsedState({
    collapsible: collapsible && !responsiveOverflow,
    storageKey,
    collapsed: collapsedProp,
    defaultCollapsed,
    onCollapsedChange,
  });

  const measureRef = useRef<HTMLDivElement>(null);
  const overflowCollapsed = useTopBarOverflowCollapsed(measureRef, {
    enabled: responsiveOverflow,
  }).collapsed;

  const [menuOpen, setMenuOpen] = useState(false);
  const menuAnchorRef = useRef<HTMLButtonElement>(null);

  const isCollapsed = responsiveOverflow
    ? overflowCollapsed
    : collapsible && manualState.collapsed;

  useEffect(() => {
    if (isCollapsed) setMenuOpen(false);
  }, [isCollapsed]);

  const activeItem = useMemo(
    () => items.find((item) => item.id === activeId) ?? items[0],
    [activeId, items],
  );

  const rootClass = [
    classNames.root,
    bleed ? withBemModifier(classNames.root, "bleed") : null,
    sticky ? withBemModifier(classNames.root, "sticky") : null,
    surface ? withBemModifier(classNames.root, "surface") : null,
    isCollapsed ? withBemModifier(classNames.root, "collapsed") : null,
    collapsible ? withBemModifier(classNames.root, `mode-${mode}`) : null,
    responsiveOverflow ? withBemModifier(classNames.root, "responsive") : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const manualCollapseToggle =
    collapsible && !responsiveOverflow ? (
      <IconButton
        className={classNames.collapseToggle}
        aria-label={isCollapsed ? expandLabel : collapseLabel}
        aria-expanded={!isCollapsed}
        onClick={() => {
          setMenuOpen(false);
          manualState.setCollapsed(!isCollapsed);
        }}
      >
        {isCollapsed ? (
          <ChevronDown size={18} strokeWidth={2} aria-hidden />
        ) : (
          <ChevronUp size={18} strokeWidth={2} aria-hidden />
        )}
      </IconButton>
    ) : null;

  const measureRow = responsiveOverflow ? (
    <div ref={measureRef} className={classNames.measure} aria-hidden="true">
      <TopBarExpandedRow
        classNames={classNames}
        navClassNames={navClassNames}
        items={items}
        activeId={activeId}
        ariaLabel={ariaLabel}
        secondary={secondary}
        actions={actions}
        rowClassName="delpi-ui-topbar__row--measure"
      />
    </div>
  ) : null;

  if (isCollapsed && mode === "rail") {
    return (
      <div className={rootClass}>
        <div className={[classNames.row, classNames.collapsedRail].join(" ")}>
          <span className={classNames.collapsedTitle}>{activeItem?.label}</span>
          {manualCollapseToggle}
        </div>
      </div>
    );
  }

  if (isCollapsed && mode === "hamburger") {
    return (
      <div className={rootClass}>
        {measureRow}
        <div className={[classNames.row, classNames.collapsedRail].join(" ")}>
          <button
            ref={menuAnchorRef}
            type="button"
            className={["delpi-ui-icon-btn", classNames.collapseToggle]
              .filter(Boolean)
              .join(" ")}
            aria-label={menuLabel}
            aria-expanded={menuOpen}
            aria-haspopup="menu"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <Menu size={18} strokeWidth={2} aria-hidden />
          </button>
          <span className={classNames.collapsedTitle}>{activeItem?.label}</span>
          {secondary ? <div className={classNames.secondary}>{secondary}</div> : null}
          {actions ? <div className={classNames.actions}>{actions}</div> : null}
        </div>
        <TopBarHamburgerMenu
          open={menuOpen}
          anchorRef={menuAnchorRef}
          items={items}
          activeId={activeId}
          classNames={classNames}
          menuLabel={menuLabel}
          portalScopeClassName={portalScopeClassName}
          onDismiss={() => setMenuOpen(false)}
        />
      </div>
    );
  }

  return (
    <div className={rootClass}>
      {measureRow}
      <TopBarExpandedRow
        classNames={classNames}
        navClassNames={navClassNames}
        items={items}
        activeId={activeId}
        ariaLabel={ariaLabel}
        secondary={secondary}
        actions={actions}
        collapseToggle={manualCollapseToggle}
      />
    </div>
  );
}

export type DashboardTopBarProps = Omit<TopBarProps, "classNames" | "navClassNames">;

export function createDashboardTopBar(config: { prefix: string }) {
  const classNames = topBarBemClasses(config.prefix);
  const navClassNames = underlineNavBemClasses(config.prefix);
  return function DashboardTopBar(props: DashboardTopBarProps) {
    return <TopBar classNames={classNames} navClassNames={navClassNames} {...props} />;
  };
}
