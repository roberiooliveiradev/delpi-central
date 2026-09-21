import type { ReactNode } from "react";

import {
  HubChipRow,
  hubChipRowBemClasses,
  type HubChipRowClassNames,
} from "./HubChipRow";
import {
  RouteChip,
  routeChipBemClasses,
  type RouteChipClassNames,
} from "./RouteChip";

export type RecentAccessItem = {
  id: string;
  label: string;
  icon?: ReactNode;
};

export type RecentAccessStripClassNames = {
  row: HubChipRowClassNames;
  chip: RouteChipClassNames;
};

export type RecentAccessStripProps = {
  items: RecentAccessItem[];
  onSelect: (id: string) => void;
  label?: ReactNode;
  maxVisible?: number;
  classNames: RecentAccessStripClassNames;
  className?: string;
  "aria-label"?: string;
};

/**
 * Faixa de últimos acessos do hub.
 * OWNS: chrome de chips recentes.
 * DOES NOT OWN: persistência, navegação, autorização.
 */
export function RecentAccessStrip({
  items,
  onSelect,
  label = "Últimos acessos",
  maxVisible,
  classNames,
  className,
  "aria-label": ariaLabel,
}: RecentAccessStripProps) {
  const visible = maxVisible && maxVisible > 0 ? items.slice(0, maxVisible) : items;
  if (!visible.length) return null;

  return (
    <HubChipRow
      classNames={classNames.row}
      className={className}
      label={label}
      aria-label={ariaLabel ?? (typeof label === "string" ? label : "Últimos acessos")}
    >
      {visible.map((item) => (
        <RouteChip
          key={item.id}
          classNames={classNames.chip}
          tone="recent"
          label={item.label}
          leadingIcon={item.icon}
          onNavigate={() => onSelect(item.id)}
        />
      ))}
    </HubChipRow>
  );
}

export type DashboardRecentAccessStripProps = Omit<RecentAccessStripProps, "classNames">;

export function createDashboardRecentAccessStrip(config: { prefix: string }) {
  const classNames: RecentAccessStripClassNames = {
    row: hubChipRowBemClasses(config.prefix),
    chip: routeChipBemClasses(config.prefix),
  };
  return function DashboardRecentAccessStrip(props: DashboardRecentAccessStripProps) {
    return <RecentAccessStrip classNames={classNames} {...props} />;
  };
}
