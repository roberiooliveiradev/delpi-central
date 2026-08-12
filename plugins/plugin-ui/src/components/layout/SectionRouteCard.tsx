import type { ReactNode } from "react";
import { Star } from "lucide-react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type SectionRouteItem = {
  id: string;
  label: string;
  onClick: () => void;
  badge?: string | number;
  disabled?: boolean;
  pinned?: boolean;
  onPinClick?: () => void;
  pinLabel?: string;
  unpinLabel?: string;
  /** Pin omitted only when onPinClick is undefined (not based on kind). */
  kind?: "navigate" | "create";
};
export type SectionRouteCardClassNames = {
  root: string;
  header: string;
  icon: string;
  titleBlock: string;
  title: string;
  description: string;
  badge: string;
  routes: string;
  route: string;
  routeLabel: string;
  routeBadge: string;
  routePin: string;
  routePinPressed: string;
};

export type SectionRouteCardProps = {
  title: string;
  icon?: ReactNode;
  badge?: string | number;
  description?: string;
  routes: readonly SectionRouteItem[];
  classNames: SectionRouteCardClassNames;
  className?: string;
  "aria-label"?: string;
};

export function sectionRouteCardBemClasses(prefix: string): SectionRouteCardClassNames {
  const base = `${prefix}-section-route-card`;
  const ui = "delpi-ui-section-route-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    header: pair(`${base}__header`, `${ui}__header`),
    icon: pair(`${base}__icon`, `${ui}__icon`),
    titleBlock: pair(`${base}__title-block`, `${ui}__title-block`),
    title: pair(`${base}__title`, `${ui}__title`),
    description: pair(`${base}__description`, `${ui}__description`),
    badge: pair(`${base}__badge`, `${ui}__badge`),
    routes: pair(`${base}__routes`, `${ui}__routes`),
    route: pair(`${base}__route`, `${ui}__route`),
    routeLabel: pair(`${base}__route-label`, `${ui}__route-label`),
    routeBadge: pair(`${base}__route-badge`, `${ui}__route-badge`),
    routePin: pair(`${base}__route-pin`, `${ui}__route-pin`),
    routePinPressed: pair(
      `${base}__route-pin ${base}__route-pin--pressed`,
      `${ui}__route-pin ${ui}__route-pin--pressed`,
    ),
  };
}

/**
 * Card de seção (1º nível) com links de aplicação/sub-rota (2º nível).
 * CSS: `styles/section-route-card.css`.
 */
export function SectionRouteCard({
  title,
  icon,
  badge,
  description,
  routes,
  classNames,
  className,
  "aria-label": ariaLabel,
}: SectionRouteCardProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <section className={rootClass} aria-label={ariaLabel ?? title}>
      <div className={classNames.header}>
        {icon ? (
          <span className={classNames.icon} aria-hidden={true}>
            {icon}
          </span>
        ) : null}
        <div className={classNames.titleBlock}>
          <h3 className={classNames.title}>{title}</h3>
          {description ? <p className={classNames.description}>{description}</p> : null}
        </div>
        {badge != null && badge !== "" && badge !== 0 ? (
          <span className={classNames.badge}>{badge}</span>
        ) : null}
      </div>
      <ul className={classNames.routes}>
        {routes.map((route) => {
          const showPin = typeof route.onPinClick === "function" && route.kind !== "create";
          const routeAria =
            route.badge != null && route.badge !== "" && route.badge !== 0
              ? `${route.label}, ${route.badge}`
              : route.label;
          return (
            <li key={route.id}>
              <div className={classNames.route}>
                <button
                  type="button"
                  className={classNames.routeLabel}
                  disabled={route.disabled}
                  onClick={route.onClick}
                  aria-label={routeAria}
                >
                  <span>{route.label}</span>
                  {route.badge != null && route.badge !== "" && route.badge !== 0 ? (
                    <span className={classNames.routeBadge} aria-hidden={true}>
                      {route.badge}
                    </span>
                  ) : null}
                </button>
                {showPin ? (
                  <button
                    type="button"
                    className={
                      route.pinned ? classNames.routePinPressed : classNames.routePin
                    }
                    aria-pressed={Boolean(route.pinned)}
                    aria-label={
                      route.pinned
                        ? route.unpinLabel ?? "Remover dos favoritos"
                        : route.pinLabel ?? "Adicionar aos favoritos"
                    }
                    onClick={(event) => {
                      event.stopPropagation();
                      route.onPinClick?.();
                    }}
                  >
                    <Star
                      size={16}
                      strokeWidth={1.75}
                      aria-hidden={true}
                      fill={route.pinned ? "currentColor" : "none"}
                    />
                  </button>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export type DashboardSectionRouteCardProps = Omit<SectionRouteCardProps, "classNames">;

export function createDashboardSectionRouteCard(config: {
  classNames: SectionRouteCardClassNames;
}) {
  return function DashboardSectionRouteCard(props: DashboardSectionRouteCardProps) {
    return <SectionRouteCard classNames={config.classNames} {...props} />;
  };
}
