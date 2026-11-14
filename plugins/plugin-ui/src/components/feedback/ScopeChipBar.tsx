import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type ScopeChip = {
  id: string;
  label: ReactNode;
  active?: boolean;
  onSelect?: () => void;
  /**
   * Shows the "×" control and removes the chip. When set without `onSelect`,
   * the label renders as plain text (an "active filter" chip).
   */
  onRemove?: () => void;
  /** Accessible name of the remove control. Default `Remover filtro {label}`. */
  removeAriaLabel?: string;
};

export type ScopeChipBarClassNames = {
  root: string;
  label: string;
  chips: string;
  chip: string;
  /** Wrapper of a removable chip (select/label + remove control). */
  chipGroup?: string;
  /** Plain-text label of a removable chip without `onSelect`. */
  chipText?: string;
  /** The "×" control. */
  chipRemove?: string;
  /** "Limpar tudo" button. */
  clearAll?: string;
  /** Hint shown when `chips` is empty. */
  empty?: string;
};

export type ScopeChipBarProps = {
  chips: ScopeChip[];
  label?: ReactNode;
  classNames: ScopeChipBarClassNames;
  className?: string;
  "aria-label"?: string;
  /** Trailing "clear all" button, rendered only with 1+ chip. */
  onClearAll?: () => void;
  /** Default `Limpar tudo`. */
  clearAllLabel?: string;
  /** Text shown when `chips` is empty. Without it, an empty bar renders nothing. */
  emptyHint?: ReactNode;
};

export function scopeChipBarBemClasses(prefix: string): ScopeChipBarClassNames {
  const ui = "delpi-ui-scope-chip-bar";
  const base = `${prefix}-scope-chip-bar`;
  return {
    root: delpiUiClass(base, ui),
    label: delpiUiClass(`${base}__label`, `${ui}__label`),
    chips: delpiUiClass(`${base}__chips`, `${ui}__chips`),
    chip: delpiUiClass(`${base}__chip`, `${ui}__chip`),
    chipGroup: delpiUiClass(`${base}__chip-group`, `${ui}__chip-group`),
    chipText: delpiUiClass(`${base}__chip-text`, `${ui}__chip-text`),
    chipRemove: delpiUiClass(`${base}__chip-remove`, `${ui}__chip-remove`),
    clearAll: delpiUiClass(`${base}__clear-all`, `${ui}__clear-all`),
    empty: delpiUiClass(`${base}__empty`, `${ui}__empty`),
  };
}

/** Canonical-only slots used when a consumer passes the legacy four-slot object. */
const CANONICAL_FALLBACK = scopeChipBarBemClasses("delpi-ui");

const DEFAULT_CLEAR_ALL_LABEL = "Limpar tudo";

function plainTextOf(node: ReactNode): string {
  return typeof node === "string" || typeof node === "number" ? String(node) : "";
}

function defaultRemoveAriaLabel(chip: ScopeChip): string {
  const text = plainTextOf(chip.label);
  return text ? `Remover filtro ${text}` : "Remover filtro";
}

export function ScopeChipBar({
  chips,
  label,
  classNames,
  className,
  "aria-label": ariaLabel = "Escopo",
  onClearAll,
  clearAllLabel = DEFAULT_CLEAR_ALL_LABEL,
  emptyHint,
}: ScopeChipBarProps) {
  const hasEmptyHint = emptyHint !== undefined && emptyHint !== null && emptyHint !== false;
  if (!chips.length && !hasEmptyHint) return null;

  const cn = { ...CANONICAL_FALLBACK, ...stripUndefined(classNames) };
  const rootClass = [cn.root, className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} role="group" aria-label={ariaLabel}>
      {label ? <span className={cn.label}>{label}</span> : null}
      {chips.length === 0 ? (
        <span className={cn.empty}>{emptyHint}</span>
      ) : (
        <div className={cn.chips}>
          {chips.map((chip) => {
            const chipClass = chip.active ? withBemModifier(cn.chip, "active") : cn.chip;
            if (chip.onRemove) {
              const onRemove = chip.onRemove;
              return (
                <span key={chip.id} className={cn.chipGroup}>
                  {chip.onSelect ? (
                    <button
                      type="button"
                      className={chipClass}
                      aria-pressed={Boolean(chip.active)}
                      onClick={chip.onSelect}
                    >
                      {chip.label}
                    </button>
                  ) : (
                    <span className={`${chipClass} ${cn.chipText}`}>{chip.label}</span>
                  )}
                  <button
                    type="button"
                    className={cn.chipRemove}
                    aria-label={chip.removeAriaLabel ?? defaultRemoveAriaLabel(chip)}
                    onClick={() => onRemove()}
                  >
                    <span aria-hidden="true">×</span>
                  </button>
                </span>
              );
            }
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
          {onClearAll ? (
            <button type="button" className={cn.clearAll} onClick={() => onClearAll()}>
              {clearAllLabel}
            </button>
          ) : null}
        </div>
      )}
    </div>
  );
}

function stripUndefined(classNames: ScopeChipBarClassNames): Partial<ScopeChipBarClassNames> {
  const out: Partial<ScopeChipBarClassNames> = {};
  for (const [key, value] of Object.entries(classNames) as [keyof ScopeChipBarClassNames, string | undefined][]) {
    if (value !== undefined) out[key] = value;
  }
  return out;
}

export type DashboardScopeChipBarProps = Omit<ScopeChipBarProps, "classNames">;

export function createDashboardScopeChipBar(config: { prefix: string }) {
  const classNames = scopeChipBarBemClasses(config.prefix);
  return function DashboardScopeChipBar(props: DashboardScopeChipBarProps) {
    return <ScopeChipBar classNames={classNames} {...props} />;
  };
}
