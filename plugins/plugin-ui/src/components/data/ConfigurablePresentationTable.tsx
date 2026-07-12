import {
  formatConfigurableTableCellValue,
  mergeConfigurableTableOptions,
  type ConfigurableTableOptions,
  type ConfigurableTablePreset,
  type PresentationTableColumn,
} from "./configurableTableOptions";
import type { TableInteraction, TablePartsMap } from "./configurableTableParts";
import { useConfigurableTableClasses } from "./configurableTableClasses";
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
  tableParts?: TablePartsMap | null;
  interaction?: TableInteraction | null;
};

/** Tabela configurável para apresentação (cabeçalho, células, cores). */
export function ConfigurablePresentationTable({
  columns,
  rows,
  options,
  preset = "grid",
  emptyMessage = "Sem linhas",
  className,
  tableParts,
  interaction,
}: ConfigurablePresentationTableProps) {
  const cn = useConfigurableTableClasses();
  const config = mergeConfigurableTableOptions(options, preset);
  const valueFormat = config.valueFormat ?? "auto";
  const title = config.title?.trim();
  const showHeader = config.showHeader !== false;
  const ariaLabel = title || "Tabela de dados";
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);

  if (rows.length === 0) {
    return (
      <TableContainer options={config} className={className} empty emptyMessage={emptyMessage} />
    );
  }

  return (
    <TableContainer
      options={config}
      className={[className, interactive ? `${cn.root}--interactive` : null].filter(Boolean).join(" ")}
    >
      <TableTitle
        title={title}
        visible={config.showTitle !== false}
        interaction={interaction}
        tableParts={tableParts}
      />
      <TableFrame ariaLabel={ariaLabel}>
        <TableHeader visible={showHeader} interaction={interaction} tableParts={tableParts}>
          {columns.map((column, colIndex) => (
            <TableHeaderCell key={column.key} colIndex={colIndex} interaction={interaction}>
              {column.label}
            </TableHeaderCell>
          ))}
        </TableHeader>
        <TableBody>
          {rows.map((row, rowIndex) => (
            <TableRow key={`row-${rowIndex}`} rowIndex={rowIndex}>
              {columns.map((column, colIndex) => (
                <TableCell
                  key={`${column.key}-${rowIndex}`}
                  rowIndex={rowIndex}
                  colIndex={colIndex}
                  interaction={interaction}
                >
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
