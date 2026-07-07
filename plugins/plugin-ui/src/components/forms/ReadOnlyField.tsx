import type { ReactNode } from "react";

import { FieldLabel } from "../help/FieldLabel";
import { HelpTooltip } from "../help/HelpTooltip";

export type ReadOnlyFieldAppearance = "inline" | "ficha" | "field";

export type ReadOnlyFieldClassNames = {
  resolveRoot: (options: {
    wide: boolean;
    multiline: boolean;
    appearance: ReadOnlyFieldAppearance;
  }) => string;
  label: string;
  resolveValue: (options: {
    multiline: boolean;
    appearance: ReadOnlyFieldAppearance;
    empty: boolean;
  }) => string;
  valueMuted?: string;
  wideModifier?: string;
};

export type ReadOnlyFieldLabels = {
  emptyDisplay: string;
  fieldHelpAriaLabel: (label: string) => string;
};

export type ReadOnlyFieldProps = {
  label: string;
  hint?: string;
  value?: ReactNode;
  wide?: boolean;
  multiline?: boolean;
  id?: string;
  appearance?: ReadOnlyFieldAppearance;
  /** `helpTooltip` (kaizen) ou `fieldLabel` (PAC). */
  labelMode?: "helpTooltip" | "fieldLabel";
  classNames: ReadOnlyFieldClassNames;
  labels: ReadOnlyFieldLabels;
};

function isEmptyValue(value: ReactNode, emptyDisplay: string): boolean {
  if (value == null || value === "") {
    return true;
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed === "" || trimmed === emptyDisplay;
  }
  return false;
}

function resolveDisplayValue(value: ReactNode | undefined, emptyDisplay: string): ReactNode {
  if (value == null || value === "") {
    return emptyDisplay;
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed ? trimmed : emptyDisplay;
  }
  return value;
}

export function readOnlyFieldKaizenBemClasses(prefix: string): ReadOnlyFieldClassNames {
  const field = `${prefix}-read-field`;
  return {
    resolveRoot: ({ wide }) =>
      [field, wide ? `${prefix}-span-2` : ""].filter(Boolean).join(" "),
    label: `${field}__label`,
    resolveValue: ({ multiline, empty }) =>
      [
        `${field}__value`,
        multiline ? `${field}__value--multiline` : "",
        empty ? `${field}__value--empty` : "",
      ]
        .filter(Boolean)
        .join(" "),
    wideModifier: `${prefix}-span-2`,
  };
}

export function readOnlyFieldPacBemClasses(prefix: string): ReadOnlyFieldClassNames {
  const field = `${prefix}-field`;
  const ficha = `${prefix}-ficha-field`;
  const readonly = `${prefix}-readonly-field`;

  return {
    resolveRoot: ({ wide, multiline, appearance }) => {
      const isFicha = appearance !== "field";
      return [
        field,
        isFicha ? ficha : readonly,
        wide ? `${field}--full` : "",
        multiline
          ? isFicha
            ? `${ficha}--multiline`
            : `${readonly}--multiline`
          : "",
      ]
        .filter(Boolean)
        .join(" ");
    },
    label: `${field}__label`,
    resolveValue: ({ appearance }) =>
      appearance === "field" ? `${readonly}__value` : `${ficha}__value`,
    valueMuted: `${prefix}-muted`,
  };
}

function renderLabel(
  props: Pick<ReadOnlyFieldProps, "label" | "hint" | "id" | "labelMode" | "labels">,
  labelClassName: string,
): ReactNode {
  const { label, hint, id, labelMode = "helpTooltip", labels } = props;
  const labelId = id ? `${id}-label` : undefined;

  if (labelMode === "fieldLabel") {
    return (
      <span className={labelClassName} id={labelId}>
        <FieldLabel label={label} hint={hint} />
      </span>
    );
  }

  return (
    <span className={labelClassName}>
      {label}
      {hint ? (
        <HelpTooltip content={hint} ariaLabel={labels.fieldHelpAriaLabel(label)} />
      ) : null}
    </span>
  );
}

export function ReadOnlyField({
  label,
  hint,
  value,
  wide = false,
  multiline = false,
  id,
  appearance = "inline",
  labelMode = "helpTooltip",
  classNames,
  labels,
}: ReadOnlyFieldProps) {
  const empty = isEmptyValue(value, labels.emptyDisplay);
  const displayValue = resolveDisplayValue(value, labels.emptyDisplay);
  const rootClassName = classNames.resolveRoot({ wide, multiline, appearance });
  const valueClassName = classNames.resolveValue({ multiline, appearance, empty });
  const labelId = id ? `${id}-label` : undefined;
  const useParagraph = labelMode === "fieldLabel";

  const valueNode =
    empty && classNames.valueMuted ? (
      <span className={classNames.valueMuted}>{labels.emptyDisplay}</span>
    ) : (
      displayValue
    );

  return (
    <div className={rootClassName}>
      {renderLabel({ label, hint, id, labelMode, labels }, classNames.label)}
      {useParagraph ? (
        <p id={id} className={valueClassName} aria-labelledby={labelId}>
          {valueNode}
        </p>
      ) : (
        <span className={valueClassName}>{empty ? labels.emptyDisplay : displayValue}</span>
      )}
    </div>
  );
}

export type DashboardReadOnlyFieldProps = Omit<
  ReadOnlyFieldProps,
  "classNames" | "labels" | "labelMode" | "appearance"
> & {
  appearance?: ReadOnlyFieldAppearance;
  fullWidth?: boolean;
};

export function createDashboardReadOnlyField(config: {
  classNames: ReadOnlyFieldClassNames;
  labels: ReadOnlyFieldLabels;
  labelMode?: "helpTooltip" | "fieldLabel";
  defaultAppearance?: ReadOnlyFieldAppearance;
}) {
  return function DashboardReadOnlyField({
    wide,
    fullWidth,
    appearance,
    ...props
  }: DashboardReadOnlyFieldProps) {
    return (
      <ReadOnlyField
        classNames={config.classNames}
        labels={config.labels}
        labelMode={config.labelMode}
        appearance={appearance ?? config.defaultAppearance ?? "inline"}
        wide={wide ?? fullWidth}
        {...props}
      />
    );
  };
}
