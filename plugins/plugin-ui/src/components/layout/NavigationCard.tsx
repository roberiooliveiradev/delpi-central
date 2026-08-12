import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type NavigationCardDensity = "default" | "featured";

export type NavigationCardClassNames = {
  root: string;
  rootHorizontal: string;
  rootFeatured: string;
  rootFeaturedHorizontal: string;
  icon: string;
  body: string;
  eyebrow: string;
  title: string;
  description: string;
  meta: string;
};

export type NavigationCardProps = {
  title: string;
  onClick: () => void;
  icon?: ReactNode;
  eyebrow?: string;
  description?: string;
  meta?: string;
  disabled?: boolean;
  orientation?: "vertical" | "horizontal";
  /**
   * `featured` — hierarquia visual maior (launcher primary / bento hero tile).
   * CSS: `.delpi-ui-nav-card--featured`.
   */
  density?: NavigationCardDensity;
  className?: string;
  "aria-label"?: string;
  classNames: NavigationCardClassNames;
};

/** Dual `{prefix}-nav-card*` + `.delpi-ui-nav-card*`. */
export function navigationCardBemClasses(prefix: string): NavigationCardClassNames {
  const base = `${prefix}-nav-card`;
  const ui = "delpi-ui-nav-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    root: pair(base, ui),
    rootHorizontal: pair(
      `${base} ${base}--horizontal`,
      `${ui} ${ui}--horizontal`,
    ),
    rootFeatured: pair(`${base} ${base}--featured`, `${ui} ${ui}--featured`),
    rootFeaturedHorizontal: pair(
      `${base} ${base}--horizontal ${base}--featured`,
      `${ui} ${ui}--horizontal ${ui}--featured`,
    ),
    icon: pair(`${base}__icon`, `${ui}__icon`),
    body: pair(`${base}__body`, `${ui}__body`),
    eyebrow: pair(`${base}__eyebrow`, `${ui}__eyebrow`),
    title: pair(`${base}__title`, `${ui}__title`),
    description: pair(`${base}__description`, `${ui}__description`),
    meta: pair(`${base}__meta`, `${ui}__meta`),
  };
}

/**
 * Card clicável de navegação/atalho (unidades, submódulos, filiais).
 *
 * CSS: `styles/navigation-card.css`.
 */
export function NavigationCard({
  title,
  onClick,
  icon,
  eyebrow,
  description,
  meta,
  disabled = false,
  orientation = "vertical",
  density = "default",
  className,
  "aria-label": ariaLabel,
  classNames,
}: NavigationCardProps) {
  const featured = density === "featured";
  const baseRoot =
    orientation === "horizontal"
      ? featured
        ? classNames.rootFeaturedHorizontal
        : classNames.rootHorizontal
      : featured
        ? classNames.rootFeatured
        : classNames.root;
  const rootClass = [baseRoot, className].filter(Boolean).join(" ");

  return (
    <button
      type="button"
      className={rootClass}
      disabled={disabled}
      onClick={onClick}
      aria-label={ariaLabel ?? title}
      data-density={density}
    >
      {icon ? (
        <span className={classNames.icon} aria-hidden={true}>
          {icon}
        </span>
      ) : null}
      <span className={classNames.body}>
        {eyebrow ? <span className={classNames.eyebrow}>{eyebrow}</span> : null}
        <span className={classNames.title}>{title}</span>
        {description ? <span className={classNames.description}>{description}</span> : null}
        {meta ? <span className={classNames.meta}>{meta}</span> : null}
      </span>
    </button>
  );
}

export type DashboardNavigationCardProps = Omit<NavigationCardProps, "classNames">;

export function createDashboardNavigationCard(config: {
  classNames: NavigationCardClassNames;
}) {
  return function DashboardNavigationCard(props: DashboardNavigationCardProps) {
    return <NavigationCard classNames={config.classNames} {...props} />;
  };
}
