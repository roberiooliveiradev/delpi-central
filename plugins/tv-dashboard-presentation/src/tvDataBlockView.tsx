import type { ComunicadoDataBlock } from "./comunicadoTypes";
import { resolveDataBlockErrorText } from "./resolveDataBlockErrorText";
import {
  resolveChartType,
  resolveEffectiveDisplayMode,
  resolveTableColumns,
} from "./tvDataPresentation";
import {
  formatCellValue,
  TvDataBarChartWidget,
  TvDataKpiWidget,
  TvDataLineChartWidget,
} from "./tvDataChartWidgets";

type Props = {
  block: ComunicadoDataBlock;
  interactive?: boolean;
  loading?: boolean;
};

function TvDataTableWidget({
  resolved,
  columns,
}: {
  resolved: ComunicadoDataBlock["resolved"];
  columns: ReturnType<typeof resolveTableColumns>;
}) {
  const rows = resolved?.table?.rows ?? [];
  if (rows.length === 0) {
    return <div className="tdp-data-table tdp-data-table--empty">Sem linhas</div>;
  }
  const visibleColumns = columns.length > 0 ? columns : resolveTableColumns(resolved, rows);
  return (
    <table className="tdp-data-table">
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

export function TvDataBlockView({ block, interactive = false, loading = false }: Props) {
  const binding = block.dataBinding;
  const resolved = block.resolved;
  const label = binding.label ?? binding.operationId;
  const displayMode = resolveEffectiveDisplayMode(block);

  const errorText = resolveDataBlockErrorText(resolved);
  if (errorText) {
    return (
      <div className="tdp-data-block tdp-data-block--error">
        <span>{errorText}</span>
      </div>
    );
  }

  if (!resolved) {
    return (
      <div className={`tdp-data-block tdp-data-block--placeholder${loading ? " tdp-data-block--loading" : ""}`}>
        <span className="tdp-data-block__title">{label}</span>
        <span className="tdp-data-block__hint">
          {loading ? "Carregando dados…" : interactive ? "Dados (preview ao publicar)" : "…"}
        </span>
      </div>
    );
  }

  if (displayMode === "table") {
    const rows = resolved.table?.rows ?? [];
    const columns = resolveTableColumns(resolved, rows);
    return (
      <div className="tdp-data-block tdp-data-block--table">
        <div className="tdp-data-table-wrap">
          <TvDataTableWidget resolved={resolved} columns={columns} />
        </div>
      </div>
    );
  }

  if (displayMode === "line_chart" || displayMode === "bar_chart") {
    const chartType = resolveChartType(displayMode, resolved);
    return (
      <div className={`tdp-data-block tdp-data-block--chart tdp-data-block--chart-${chartType}`}>
        {chartType === "bar" ? (
          <TvDataBarChartWidget resolved={resolved} />
        ) : (
          <TvDataLineChartWidget resolved={resolved} />
        )}
      </div>
    );
  }

  return (
    <div className="tdp-data-block tdp-data-block--kpi">
      <TvDataKpiWidget resolved={resolved} />
    </div>
  );
}
