import { FieldLabel } from "../help/FieldLabel";
import { HelpTooltip } from "../help/HelpTooltip";

export type TableHeaderHintPresentation = "fieldLabel" | "icon";

export type TableHeaderCellClassNames = {
  content?: string;
  fieldLabelRow?: string;
};

export type TableHeaderCellLabels = {
  hintAriaLabel: (label: string) => string;
};

export type TableHeaderHintProps = {
  label: string;
  hint?: string;
  classNames: TableHeaderCellClassNames;
  labels: TableHeaderCellLabels;
  hintPresentation?: TableHeaderHintPresentation;
};

export type TableHeaderCellProps = TableHeaderHintProps & {
  className?: string;
  scope?: "col" | "row";
};

export function tableHeaderCellBemClasses(prefix: string): TableHeaderCellClassNames {
  return {
    fieldLabelRow: `${prefix}-field__label-row`,
  };
}

export function tableHeaderContentBemClasses(prefix: string): TableHeaderCellClassNames {
  return {
    content: `${prefix}-table__header-cell`,
  };
}

export const tableHeaderCellPacClasses = tableHeaderCellBemClasses;
export const tableHeaderContentTransformometroClasses = tableHeaderContentBemClasses;

function TableHeaderHint({
  label,
  hint,
  classNames,
  labels,
  hintPresentation = "fieldLabel",
}: TableHeaderHintProps) {
  if (!hint) {
    return hintPresentation === "icon" ? (
      <span className={classNames.content}>{label}</span>
    ) : (
      <>{label}</>
    );
  }

  if (hintPresentation === "icon") {
    return (
      <span className={classNames.content}>
        {label}
        <HelpTooltip content={hint} ariaLabel={labels.hintAriaLabel(label)} />
      </span>
    );
  }

  return (
    <FieldLabel label={label} hint={hint} className={classNames.fieldLabelRow ?? undefined} />
  );
}

/** Conteúdo interno de `<th>` — label + hint (ícone ou FieldLabel). */
export function TableHeaderContent(props: TableHeaderHintProps) {
  return <TableHeaderHint {...props} />;
}

/** Cabeçalho `<th>` com rótulo e balão de ajuda opcional. */
export function TableHeaderCell({
  label,
  hint,
  className,
  scope = "col",
  classNames,
  labels,
  hintPresentation = "fieldLabel",
}: TableHeaderCellProps) {
  return (
    <th className={className} scope={scope}>
      <TableHeaderHint
        label={label}
        hint={hint}
        classNames={classNames}
        labels={labels}
        hintPresentation={hintPresentation}
      />
    </th>
  );
}

export type DashboardTableHeaderCellProps = Omit<TableHeaderCellProps, "classNames" | "labels">;

export type DashboardTableHeaderContentProps = Omit<TableHeaderHintProps, "classNames" | "labels">;

export function createDashboardTableHeaderCell(config: {
  classNames: TableHeaderCellClassNames;
  labels: TableHeaderCellLabels;
  hintPresentation?: TableHeaderHintPresentation;
}) {
  return function DashboardTableHeaderCell(props: DashboardTableHeaderCellProps) {
    return (
      <TableHeaderCell
        classNames={config.classNames}
        labels={config.labels}
        hintPresentation={config.hintPresentation ?? "fieldLabel"}
        {...props}
      />
    );
  };
}

export function createDashboardTableHeaderContent(config: {
  classNames: TableHeaderCellClassNames;
  labels: TableHeaderCellLabels;
  hintPresentation?: TableHeaderHintPresentation;
}) {
  return function DashboardTableHeaderContent(props: DashboardTableHeaderContentProps) {
    return (
      <TableHeaderContent
        classNames={config.classNames}
        labels={config.labels}
        hintPresentation={config.hintPresentation ?? "icon"}
        {...props}
      />
    );
  };
}
