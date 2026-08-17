import { Minus, Plus, RotateCcw } from "lucide-react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type TableFontSizeControlsClassNames = {
  root: string;
  label: string;
  controls: string;
  value: string;
  button: string;
};

export type TableFontSizeControlsLabels = {
  groupAriaLabel?: string;
  label?: string;
  decreaseAriaLabel?: string;
  increaseAriaLabel?: string;
  resetAriaLabel?: string;
};

export type TableFontSizeControlsProps = {
  fontSize: number;
  canIncrease: boolean;
  canDecrease: boolean;
  isDefault: boolean;
  onIncrease: () => void;
  onDecrease: () => void;
  onReset: () => void;
  className?: string;
  classNames: TableFontSizeControlsClassNames;
  labels?: TableFontSizeControlsLabels;
};

const DEFAULT_LABELS: Required<TableFontSizeControlsLabels> = {
  groupAriaLabel: "Tamanho da fonte da tabela",
  label: "Fonte",
  decreaseAriaLabel: "Diminuir fonte da tabela",
  increaseAriaLabel: "Aumentar fonte da tabela",
  resetAriaLabel: "Restaurar fonte padrão da tabela",
};

export function tableFontSizeControlsBemClasses(
  prefix: string,
): TableFontSizeControlsClassNames {
  const base = `${prefix}-table-font-size`;
  const ui = "delpi-ui-table-font-size";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    label: pair(`${base}__label`, `${ui}__label`),
    controls: pair(`${base}__controls`, `${ui}__controls`),
    value: pair(`${base}__value`, `${ui}__value`),
    button: pair(`${base}__btn`, `${ui}__btn`),
  };
}

export function TableFontSizeControls({
  fontSize,
  canIncrease,
  canDecrease,
  isDefault,
  onIncrease,
  onDecrease,
  onReset,
  className,
  classNames,
  labels,
}: TableFontSizeControlsProps) {
  const resolved = { ...DEFAULT_LABELS, ...labels };
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} aria-label={resolved.groupAriaLabel}>
      <span className={classNames.label}>{resolved.label}</span>
      <div className={classNames.controls}>
        <button
          type="button"
          className={classNames.button}
          aria-label={resolved.decreaseAriaLabel}
          disabled={!canDecrease}
          onClick={onDecrease}
        >
          <Minus size={14} aria-hidden="true" />
        </button>
        <span className={classNames.value} aria-live="polite">
          {fontSize}px
        </span>
        <button
          type="button"
          className={classNames.button}
          aria-label={resolved.increaseAriaLabel}
          disabled={!canIncrease}
          onClick={onIncrease}
        >
          <Plus size={14} aria-hidden="true" />
        </button>
        {!isDefault ? (
          <button
            type="button"
            className={classNames.button}
            aria-label={resolved.resetAriaLabel}
            onClick={onReset}
          >
            <RotateCcw size={14} aria-hidden="true" />
          </button>
        ) : null}
      </div>
    </div>
  );
}

export type DashboardTableFontSizeControlsProps = Omit<
  TableFontSizeControlsProps,
  "classNames"
>;

export function createDashboardTableFontSizeControls(config: { prefix: string }) {
  const classNames = tableFontSizeControlsBemClasses(config.prefix);
  return function DashboardTableFontSizeControls(
    props: DashboardTableFontSizeControlsProps,
  ) {
    return <TableFontSizeControls classNames={classNames} {...props} />;
  };
}
