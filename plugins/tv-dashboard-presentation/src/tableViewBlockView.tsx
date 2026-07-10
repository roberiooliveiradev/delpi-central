import { formatNumber, formatPct } from "./nativeFormat";
import { tablePresetLabel } from "./comunicadoChartView";
import type { ComunicadoDataResolved, ComunicadoTableViewBlock } from "./comunicadoTypes";
import { resolveTableColumns, type TvDataTableColumn } from "./tvDataPresentation";

type Props = {
  block: ComunicadoTableViewBlock;
  interactive?: boolean;
  loading?: boolean;
};

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    if (Math.abs(value) <= 100 && !Number.isInteger(value)) return formatPct(value);
    return formatNumber(value);
  }
  return String(value);
}

function TableWidget({
  resolved,
  columns,
  preset,
  maxRows,
}: {
  resolved: ComunicadoDataResolved;
  columns: TvDataTableColumn[];
  preset: ComunicadoTableViewBlock["tablePreset"];
  maxRows?: number;
}) {
  const rows = (resolved.table?.rows ?? []).slice(0, maxRows ?? undefined);
  if (rows.length === 0) {
    return <div className="tdp-data-table tdp-data-table--empty">Sem linhas</div>;
  }
  const visibleColumns = columns.length > 0 ? columns : resolveTableColumns(resolved, rows);
  const presetClass =
    preset === "minimal"
      ? "tdp-data-table--minimal"
      : preset === "banded"
        ? "tdp-data-table--banded"
        : "";
  return (
    <table className={`tdp-data-table ${presetClass}`.trim()}>
      <thead>
        <tr>
          {visibleColumns.map((column) => (
            <th key={column.key}>{column.label}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={`row-${index}`}>
            {visibleColumns.map((column) => (
              <td key={`${column.key}-${index}`}>{formatCellValue(row[column.key])}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function TableViewBlockView({ block, interactive = false, loading = false }: Props) {
  const resolved = block.resolved;
  const label = tablePresetLabel(block.tablePreset);

  if (resolved?.error) {
    return (
      <div className="tdp-data-block tdp-data-block--error">
        <span>{String(resolved.error)}</span>
      </div>
    );
  }

  if (!resolved) {
    return (
      <div className={`tdp-data-block tdp-data-block--placeholder${loading ? " tdp-data-block--loading" : ""}`}>
        <span className="tdp-data-block__title">{label}</span>
        <span className="tdp-data-block__hint">
          {loading ? "Carregando dados…" : interactive ? "Conecte uma fonte de dados" : "…"}
        </span>
      </div>
    );
  }

  const rows = resolved.table?.rows ?? [];
  const columns = resolveTableColumns(resolved, rows);

  return (
    <div className="tdp-data-block tdp-data-block--table">
      <div className="tdp-data-table-wrap">
        <TableWidget
          resolved={resolved}
          columns={columns}
          preset={block.tablePreset}
          maxRows={block.maxRows}
        />
      </div>
    </div>
  );
}
