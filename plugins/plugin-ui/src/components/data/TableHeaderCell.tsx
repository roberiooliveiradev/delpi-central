import { FieldLabel } from "../help/FieldLabel";

export type TableHeaderCellClassNames = {
  fieldLabelRow: string;
};

export type TableHeaderCellProps = {
  label: string;
  hint?: string;
  className?: string;
  scope?: "col" | "row";
  classNames: TableHeaderCellClassNames;
};

export function tableHeaderCellBemClasses(prefix: string): TableHeaderCellClassNames {
  return {
    fieldLabelRow: `${prefix}-field__label-row`,
  };
}

export const tableHeaderCellPacClasses = tableHeaderCellBemClasses;

/** Cabeçalho `<th>` com rótulo e balão de ajuda opcional. */
export function TableHeaderCell({
  label,
  hint,
  className,
  scope = "col",
  classNames,
}: TableHeaderCellProps) {
  return (
    <th className={className} scope={scope}>
      {hint ? (
        <FieldLabel label={label} hint={hint} className={classNames.fieldLabelRow} />
      ) : (
        label
      )}
    </th>
  );
}

export type DashboardTableHeaderCellProps = Omit<TableHeaderCellProps, "classNames">;

export function createDashboardTableHeaderCell(config: { classNames: TableHeaderCellClassNames }) {
  return function DashboardTableHeaderCell(props: DashboardTableHeaderCellProps) {
    return <TableHeaderCell classNames={config.classNames} {...props} />;
  };
}
