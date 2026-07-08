import type { ChangeEvent, ReactNode } from "react";

export type EditableTableCellClassNames = {
  root: string;
  control?: string;
};

export type EditableTableCellOption = {
  value: string;
  label: string;
};

export type EditableTableCellProps = {
  classNames: EditableTableCellClassNames;
  /** Slot após o controle (ex.: PendingChangeBadge). */
  badge?: ReactNode;
  disabled?: boolean;
  "aria-label"?: string;
  as?: "input" | "select";
  type?: "text" | "number" | "date";
  value: string | number;
  onChange: (value: string) => void;
  placeholder?: string;
  min?: number | string;
  step?: number | string;
  options?: readonly EditableTableCellOption[];
  placeholderOption?: string;
};

export function editableTableCellBemClasses(prefix: string): EditableTableCellClassNames {
  return {
    root: `${prefix}-editable-cell`,
  };
}

/**
 * Célula editável de tabela (input ou select nativo) + slot de badge.
 * Mantém o controle no DOM do plugin (CSS BEM via classNames).
 */
export function EditableTableCell({
  classNames,
  badge,
  disabled,
  "aria-label": ariaLabel,
  as = "input",
  type = "text",
  value,
  onChange,
  placeholder,
  min,
  step,
  options = [],
  placeholderOption,
}: EditableTableCellProps) {
  const controlClassName = classNames.control;

  const control =
    as === "select" ? (
      <select
        className={controlClassName}
        value={String(value)}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={(event: ChangeEvent<HTMLSelectElement>) => onChange(event.target.value)}
      >
        {placeholderOption !== undefined ? (
          <option value="">{placeholderOption}</option>
        ) : null}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    ) : (
      <input
        className={controlClassName}
        type={type}
        value={value}
        disabled={disabled}
        aria-label={ariaLabel}
        placeholder={placeholder}
        min={min}
        step={step}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.value)}
      />
    );

  return (
    <div className={classNames.root}>
      {control}
      {badge}
    </div>
  );
}

export type DashboardEditableTableCellProps = Omit<EditableTableCellProps, "classNames">;

export function createDashboardEditableTableCell(config: {
  classNames?: EditableTableCellClassNames;
  prefix?: string;
}) {
  const classNames =
    config.classNames ?? editableTableCellBemClasses(config.prefix ?? "delpi-ui");

  return function DashboardEditableTableCell(props: DashboardEditableTableCellProps) {
    return <EditableTableCell classNames={classNames} {...props} />;
  };
}
