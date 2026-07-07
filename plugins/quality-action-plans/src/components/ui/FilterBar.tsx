import type { ReactNode } from "react";

import { FiltersRow, filtersRowBemClasses, type FiltersRowClassNames } from "@delpi/plugin-ui";

const PAC_FILTER_ROW_CLASSES: FiltersRowClassNames = filtersRowBemClasses("pac");

type FilterBarProps = {
  children: ReactNode;
  compact?: boolean;
  actions?: ReactNode;
};

export function FilterBar({ children, compact = false, actions }: FilterBarProps) {
  return (
    <FiltersRow as="div" compact={compact} trailing={actions} classNames={PAC_FILTER_ROW_CLASSES}>
      {children}
    </FiltersRow>
  );
}
