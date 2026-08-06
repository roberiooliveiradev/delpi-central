import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type ScopeChip = {
  id: string;
  label: ReactNode;
  active?: boolean;
  onSelect?: () => void;
};

export type ScopeChipBarClassNames = {
  root: string;
  label: string;
  chips: string;
  chip: string;
};

export type ScopeChipBarProps = {
  chips: ScopeChip[];
  label?: ReactNode;
  classNames: ScopeChipBarClassNames;
  className?: string;
  "aria-label"?: string;
};

export function scopeChipBarBemClasses(prefix: string): ScopeChipBarClassNames {
  return {
    root: delpiUiClass(`${prefix}-scope-chip-bar`, "delpi-ui-scope-chip-bar"),
    label: delpiUiClass(`${prefix}-scope-chip-bar__label`, "delpi-ui-scope-chip-bar__label"),
    chips: delpiUiClass(`${prefix}-scope-chip-bar__chips`, "delpi-ui-scope-chip-bar__chips"),
    chip: delpiUiClass(`${prefix}-scope-chip-bar__chip`, "delpi-ui-scope-chip-bar__chip"),
  };
}

export function ScopeChipBar({
  chips,
  label,
  classNames,
  className,
  "aria-label": ariaLabel = "Escopo",
}: ScopeChipBarProps) {
  if (!chips.length) return null;

  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} role="group" aria-label={ariaLabel}>
      {label ? <span className={classNames.label}>{label}</span> : null}
      <div className={classNames.chips}>
        {chips.map((chip) => {
          const chipClass = chip.active
            ? withBemModifier(classNames.chip, "active")
            : classNames.chip;
          return (
            <button
              key={chip.id}
              type="button"
              className={chipClass}
              aria-pressed={Boolean(chip.active)}
              onClick={chip.onSelect}
            >
              {chip.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export type DashboardScopeChipBarProps = Omit<ScopeChipBarProps, "classNames">;

export function createDashboardScopeChipBar(config: { prefix: string }) {
  const classNames = scopeChipBarBemClasses(config.prefix);
  return function DashboardScopeChipBar(props: DashboardScopeChipBarProps) {
    return <ScopeChipBar classNames={classNames} {...props} />;
  };
}
