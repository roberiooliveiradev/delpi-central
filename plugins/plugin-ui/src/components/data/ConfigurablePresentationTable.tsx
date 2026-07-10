import {
  formatConfigurableTableCellValue,
  mergeConfigurableTableOptions,
  type ConfigurableTableOptions,
  type ConfigurableTablePreset,
  type PresentationTableColumn,
} from "./configurableTableOptions";
import {
  TableBody,
  TableCell,
  TableContainer,
  TableFrame,
  TableHeader,
  TableHeaderCell,
  TableRow,
  TableTitle,
} from "./configurableTable";

export type ConfigurablePresentationTableProps = {
  columns: PresentationTableColumn[];
  rows: Array<Record<string, unknown>>;
  options?: ConfigurableTableOptions | null;
  preset?: ConfigurableTablePreset;
  emptyMessage?: string;
  className?: string;
};

/** Tabela configurável para apresentação (cabeçalho, células, cores). */
export function ConfigurablePresentationTable({
  columns,
  rows,
  options,
  preset = "grid",
  emptyMessage = "Sem linhas",
  className,
}: ConfigurablePresentationTableProps) {
  const config = mergeConfigurableTableOptions(options, preset);
  const valueFormat = config.valueFormat ?? "auto";
  const title = config.title?.trim();
  const showHeader = config.showHeader !== false;
  const ariaLabel = title || "Tabela de dados";

  if (rows.length === 0) {
    return (
      <TableContainer options={config} className={className} empty emptyMessage={emptyMessage} />
    );
  }

  return (
    <TableContainer options={config} className={className}>
      <TableTitle title={title} visible={config.showTitle !== false} />
      <TableFrame ariaLabel={ariaLabel}>
        <TableHeader visible={showHeader}>
          {columns.map((column) => (
            <TableHeaderCell key={column.key}>{column.label}</TableHeaderCell>
          ))}
        </TableHeader>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow key={`row-${index}`} rowIndex={index}>
              {columns.map((column) => (
                <TableCell key={`${column.key}-${index}`}>
                  {formatConfigurableTableCellValue(row[column.key], valueFormat)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </TableFrame>
    </TableContainer>
  );
}

export type ConfigurableTableProps = ConfigurablePresentationTableProps;
export const ConfigurableTable = ConfigurablePresentationTable;
