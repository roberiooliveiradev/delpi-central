import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type DetailField = {
  label: string;
  hint?: string;
  value: ReactNode;
  wide?: boolean;
};

export type DetailFieldGridClassNames = {
  grid: string;
  item: string;
  itemWide: string;
  label: string;
  empty: string;
};

export type DetailFieldGridLabels = {
  emptyMessage?: string;
  fieldHelpAriaLabel: (label: string) => string;
};

export type DetailFieldGridProps = {
  fields: DetailField[];
  classNames: DetailFieldGridClassNames;
  labels: DetailFieldGridLabels;
  /** Quando definido, valores `null`/`undefined` exibem este texto (ex.: "—"). */
  valueFallback?: string;
  /** Envolve rótulos em `<span>` mesmo sem hint (ex.: commercial, lmps). */
  wrapLabels?: boolean;
};

export function detailFieldGridBemClasses(prefix: string): DetailFieldGridClassNames {
  const grid = `${prefix}-detail-grid`;
  return {
    grid,
    item: `${grid}__item`,
    itemWide: `${grid}__item ${grid}__item--wide`,
    label: `${grid}__label`,
    empty: `${prefix}-detail__empty`,
  };
}

function resolveFieldValue(value: ReactNode, valueFallback?: string): ReactNode {
  if (valueFallback !== undefined && (value == null)) {
    return valueFallback;
  }
  return value;
}

function renderFieldLabel(
  field: DetailField,
  classNames: DetailFieldGridClassNames,
  labels: DetailFieldGridLabels,
  wrapLabels: boolean,
): ReactNode {
  const labelContent = (
    <>
      {field.label}
      {field.hint ? (
        <HelpTooltip
          content={field.hint}
          ariaLabel={labels.fieldHelpAriaLabel(field.label)}
        />
      ) : null}
    </>
  );

  if (field.hint || wrapLabels) {
    return (
      <dt>
        <span className={classNames.label}>{labelContent}</span>
      </dt>
    );
  }

  return <dt>{field.label}</dt>;
}

export function DetailFieldGrid({
  fields,
  classNames,
  labels,
  valueFallback,
  wrapLabels = false,
}: DetailFieldGridProps) {
  if (fields.length === 0 && labels.emptyMessage) {
    return <p className={classNames.empty}>{labels.emptyMessage}</p>;
  }

  return (
    <dl className={classNames.grid}>
      {fields.map((field) => (
        <div
          key={field.label}
          className={field.wide ? classNames.itemWide : classNames.item}
        >
          {renderFieldLabel(field, classNames, labels, wrapLabels)}
          <dd>{resolveFieldValue(field.value, valueFallback)}</dd>
        </div>
      ))}
    </dl>
  );
}

export type DashboardDetailFieldGridProps = Omit<
  DetailFieldGridProps,
  "classNames" | "labels"
>;

export function createDashboardDetailFieldGrid(config: {
  prefix: string;
  labels: DetailFieldGridLabels;
  valueFallback?: string;
  wrapLabels?: boolean;
}) {
  const classNames = detailFieldGridBemClasses(config.prefix);

  return function DashboardDetailFieldGrid(props: DashboardDetailFieldGridProps) {
    return (
      <DetailFieldGrid
        classNames={classNames}
        labels={config.labels}
        valueFallback={config.valueFallback}
        wrapLabels={config.wrapLabels}
        {...props}
      />
    );
  };
}
