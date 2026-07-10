import { formatNumber, formatPct } from "./nativeFormat";
import type { ComunicadoDataBlock, ComunicadoDataResolved } from "./comunicadoTypes";
import {
  resolveChartType,
  resolveEffectiveDisplayMode,
  resolveTableColumns,
  type TvDataTableColumn,
} from "./tvDataPresentation";

type Props = {
  block: ComunicadoDataBlock;
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

function formatKpiValue(value: unknown): string {
  return formatCellValue(value);
}

function TvDataKpiWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const label = resolved.kpi?.label ?? resolved.label ?? "Dados";
  const value = formatKpiValue(resolved.kpi?.value);
  return (
    <div className="tdp-data-kpi">
      <span className="tdp-data-kpi__label">{label}</span>
      <strong className="tdp-data-kpi__value">{value}</strong>
    </div>
  );
}

function TvDataLineChartWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const points = resolved.chart?.points ?? [];
  if (points.length === 0) {
    return <div className="tdp-data-chart tdp-data-chart--empty">Sem série</div>;
  }
  const values = points.map((point) => Number(point.value ?? 0));
  const max = Math.max(...values, 1);
  const width = 100;
  const height = 60;
  const step = points.length > 1 ? width / (points.length - 1) : width;
  const coords = points.map((point, index) => {
    const x = index * step;
    const y = height - (Number(point.value ?? 0) / max) * height;
    return `${x},${y}`;
  });
  return (
    <div className="tdp-data-chart">
      <svg viewBox={`0 0 ${width} ${height}`} className="tdp-data-chart__svg" preserveAspectRatio="none">
        <polyline points={coords.join(" ")} fill="none" stroke="#38bdf8" strokeWidth="2" />
      </svg>
    </div>
  );
}

function TvDataBarChartWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const points = resolved.chart?.points ?? [];
  if (points.length === 0) {
    return <div className="tdp-data-chart tdp-data-chart--empty">Sem série</div>;
  }
  const values = points.map((point) => Number(point.value ?? 0));
  const max = Math.max(...values, 1);
  const width = 100;
  const height = 60;
  const barWidth = width / Math.max(points.length, 1);
  const gap = Math.min(barWidth * 0.15, 2);
  const effectiveBarWidth = Math.max(barWidth - gap, 1);

  return (
    <div className="tdp-data-chart tdp-data-chart--bar">
      <svg viewBox={`0 0 ${width} ${height}`} className="tdp-data-chart__svg" preserveAspectRatio="none">
        {points.map((point, index) => {
          const value = Number(point.value ?? 0);
          const barHeight = (value / max) * height;
          const x = index * barWidth + gap / 2;
          const y = height - barHeight;
          return (
            <rect
              key={`bar-${index}`}
              x={x}
              y={y}
              width={effectiveBarWidth}
              height={barHeight}
              fill="#38bdf8"
              rx="0.5"
            />
          );
        })}
      </svg>
    </div>
  );
}

function TvDataTableWidget({
  resolved,
  columns,
}: {
  resolved: ComunicadoDataResolved;
  columns: TvDataTableColumn[];
}) {
  const rows = resolved.table?.rows ?? [];
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
