import type { ReactNode } from "react";
import { Star, X } from "lucide-react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type RouteChipTone = "pinned" | "recent";

export type RouteChipClassNames = {
  root: string;
  main: string;
  leading: string;
  label: string;
  remove: string;
};

export type RouteChipProps = {
  label: string;
  tone: RouteChipTone;
  leadingIcon?: ReactNode;
  onNavigate: () => void;
  onRemove?: () => void;
  removeLabel?: string;
  classNames: RouteChipClassNames;
  className?: string;
};

export function routeChipBemClasses(prefix: string): RouteChipClassNames {
  const base = `${prefix}-route-chip`;
  const ui = "delpi-ui-route-chip";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    main: pair(`${base}__main`, `${ui}__main`),
    leading: pair(`${base}__leading`, `${ui}__leading`),
    label: pair(`${base}__label`, `${ui}__label`),
    remove: pair(`${base}__remove`, `${ui}__remove`),
  };
}

/**
 * Chip de rota do hub (favorito pinned ou recente).
 * CSS: `styles/hub-route-chips.css`.
 */
export function RouteChip({
  label,
  tone,
  leadingIcon,
  onNavigate,
  onRemove,
  removeLabel = "Remover dos favoritos",
  classNames,
  className,
}: RouteChipProps) {
  const rootClass = [withBemModifier(classNames.root, tone), className]
    .filter(Boolean)
    .join(" ");
  const showRemove = tone === "pinned" && Boolean(onRemove);
  const leading =
    tone === "pinned" ? (
      <Star size={14} strokeWidth={1.75} fill="currentColor" aria-hidden="true" />
    ) : (
      leadingIcon
    );

  return (
    <span className={rootClass}>
      <button type="button" className={classNames.main} onClick={onNavigate}>
        {leading ? (
          <span className={classNames.leading} aria-hidden="true">
            {leading}
          </span>
        ) : null}
        <span className={classNames.label}>{label}</span>
      </button>
      {showRemove ? (
        <button
          type="button"
          className={classNames.remove}
          aria-label={removeLabel}
          onClick={(event) => {
            event.stopPropagation();
            onRemove?.();
          }}
        >
          <X size={14} strokeWidth={2} aria-hidden="true" />
        </button>
      ) : null}
    </span>
  );
}

export type DashboardRouteChipProps = Omit<RouteChipProps, "classNames">;

export function createDashboardRouteChip(config: { prefix: string }) {
  const classNames = routeChipBemClasses(config.prefix);
  return function DashboardRouteChip(props: DashboardRouteChipProps) {
    return <RouteChip classNames={classNames} {...props} />;
  };
}
