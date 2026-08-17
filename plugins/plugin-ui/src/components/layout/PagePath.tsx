import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type MouseEventHandler,
} from "react";

import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { BackLink } from "../actions/BackLink";
import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type PagePathLink = {
  label: string;
  href: string;
  onNavigate?: MouseEventHandler<HTMLAnchorElement>;
};

export type PagePathItem = PagePathLink & {
  id: string;
};

export type PagePathClassNames = {
  root: string;
  list: string;
  item: string;
  link: string;
  current: string;
  separator: string;
  overflowTrigger: string;
  overflowPanel: string;
  overflowList: string;
  overflowLink: string;
};

export type PagePathProps = {
  back: PagePathLink;
  items?: PagePathItem[];
  current: string;
  maxVisibleItems?: number;
  size?: "sm" | "md";
  ariaLabel?: string;
  className?: string;
  classNames: PagePathClassNames;
  portalScopeClassName?: string;
};

/** PagePath navega apenas dentro do host atual por paths absolutos. */
export function isSafeNavigationHref(href: string): boolean {
  const value = href.trim();
  if (!value || /[\u0000-\u001f\u007f]/.test(value)) return false;
  return value.startsWith("/") && !value.startsWith("//");
}

function requireSafeHref(href: string): string {
  if (!isSafeNavigationHref(href)) {
    throw new Error("PagePath recebeu um href que não é interno ao host.");
  }
  return href.trim();
}

export function pagePathBemClasses(prefix: string): PagePathClassNames {
  const base = `${prefix}-page-path`;
  const ui = "delpi-ui-page-path";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    list: pair(`${base}__list`, `${ui}__list`),
    item: pair(`${base}__item`, `${ui}__item`),
    link: pair(`${base}__link`, `${ui}__link`),
    current: pair(`${base}__current`, `${ui}__current`),
    separator: pair(`${base}__separator`, `${ui}__separator`),
    overflowTrigger: pair(`${base}__overflow-trigger`, `${ui}__overflow-trigger`),
    overflowPanel: pair(`${base}__overflow-panel`, `${ui}__overflow-panel`),
    overflowList: pair(`${base}__overflow-list`, `${ui}__overflow-list`),
    overflowLink: pair(`${base}__overflow-link`, `${ui}__overflow-link`),
  };
}

function samePathEntry(a: PagePathLink, b: PagePathLink): boolean {
  return a.label.trim() === b.label.trim() || a.href.trim() === b.href.trim();
}

export function PagePath({
  back,
  items = [],
  current,
  maxVisibleItems,
  size = "md",
  ariaLabel = "Caminho da página",
  className,
  classNames,
  portalScopeClassName,
}: PagePathProps) {
  const rootRef = useRef<HTMLElement>(null);
  const overflowRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const [compact, setCompact] = useState(false);
  const [overflowOpen, setOverflowOpen] = useState(false);

  useEffect(() => {
    const root = rootRef.current;
    if (!root || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      setCompact((entry?.contentRect.width ?? root.clientWidth) < 640);
    });
    observer.observe(root);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!overflowOpen) return;
    panelRef.current?.querySelector<HTMLAnchorElement>("a")?.focus();
  }, [overflowOpen]);

  const safeBack = useMemo(
    () => ({ ...back, href: requireSafeHref(back.href) }),
    [back],
  );
  const ancestors = useMemo(() => {
    const seen = new Set<string>();
    return items.filter((item) => {
      requireSafeHref(item.href);
      const key = `${item.label.trim()}\u0000${item.href.trim()}`;
      const duplicatesBoundary =
        samePathEntry(item, safeBack) || item.label.trim() === current.trim();
      if (duplicatesBoundary || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [items, safeBack, current]);

  const responsiveLimit = compact ? 2 : 4;
  const totalLimit = Math.max(
    2,
    Math.min(responsiveLimit, maxVisibleItems ?? responsiveLimit),
  );
  const visibleAncestorCount = Math.max(0, totalLimit - 2);
  const overflowItems = ancestors.slice(
    0,
    Math.max(0, ancestors.length - visibleAncestorCount),
  );
  const normalizedVisibleItems =
    visibleAncestorCount === 0 ? [] : ancestors.slice(-visibleAncestorCount);

  const dismissOverflow = (restoreFocus = false) => {
    setOverflowOpen(false);
    if (restoreFocus) {
      window.requestAnimationFrame(() => overflowRef.current?.focus());
    }
  };

  const renderSeparator = (key: string) => (
    <li key={key} className={classNames.item} aria-hidden="true">
      <span className={classNames.separator}>/</span>
    </li>
  );

  const rootClass = [
    withBemModifier(classNames.root, `size-${size}`),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <nav ref={rootRef} className={rootClass} aria-label={ariaLabel}>
      <ol className={classNames.list}>
        <li className={classNames.item}>
          <BackLink
            className={withBemModifier(classNames.link, "back")}
            href={safeBack.href}
            onClick={safeBack.onNavigate}
          >
            {safeBack.label}
          </BackLink>
        </li>
        {overflowItems.length > 0 ? (
          <>
            {renderSeparator("separator-overflow")}
            <li className={classNames.item}>
              <button
                ref={overflowRef}
                type="button"
                className={classNames.overflowTrigger}
                aria-label="Mostrar páginas anteriores"
                aria-haspopup="menu"
                aria-expanded={overflowOpen}
                onClick={() => setOverflowOpen((value) => !value)}
              >
                …
              </button>
            </li>
          </>
        ) : null}
        {normalizedVisibleItems.flatMap((item) => [
          renderSeparator(`separator-${item.id}`),
          <li key={item.id} className={classNames.item}>
            <a
              className={classNames.link}
              href={requireSafeHref(item.href)}
              onClick={item.onNavigate}
            >
              {item.label}
            </a>
          </li>,
        ])}
        {renderSeparator("separator-current")}
        <li className={classNames.item}>
          <span className={classNames.current} aria-current="page">
            {current}
          </span>
        </li>
      </ol>

      <AnchoredPanelPortal
        open={overflowOpen}
        anchorRef={overflowRef}
        panelRef={panelRef}
        className={classNames.overflowPanel}
        variant="bare"
        role="menu"
        aria-label="Páginas anteriores"
        preferredPlacement="bottom"
        portalScopeClassName={portalScopeClassName}
        onDismiss={() => dismissOverflow(true)}
      >
        <ul className={classNames.overflowList}>
          {overflowItems.map((item) => (
            <li key={item.id}>
              <a
                role="menuitem"
                className={classNames.overflowLink}
                href={requireSafeHref(item.href)}
                onClick={(event) => {
                  item.onNavigate?.(event);
                  dismissOverflow();
                }}
              >
                {item.label}
              </a>
            </li>
          ))}
        </ul>
      </AnchoredPanelPortal>
    </nav>
  );
}

export type DashboardPagePathProps = Omit<
  PagePathProps,
  "classNames" | "portalScopeClassName"
>;

export function createDashboardPagePath(config: {
  prefix: string;
  portalScopeClassName?: string;
}) {
  const classNames = pagePathBemClasses(config.prefix);
  return function DashboardPagePath(props: DashboardPagePathProps) {
    return (
      <PagePath
        classNames={classNames}
        portalScopeClassName={config.portalScopeClassName}
        {...props}
      />
    );
  };
}
