import type { ReactNode } from "react";

type FilterBarProps = {
  children: ReactNode;
  compact?: boolean;
  actions?: ReactNode;
};

export function FilterBar({ children, compact = false, actions }: FilterBarProps) {
  return (
    <div className={`pac-filters-row${compact ? " pac-filters-row--compact" : ""}`}>
      {children}
      {actions ? (
        <div className="pac-filter-box pac-filter-box--action">{actions}</div>
      ) : null}
    </div>
  );
}
