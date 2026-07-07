import { formatNumber, formatPct } from "./nativeFormat";
import type { ComunicadoDataBlock, ComunicadoDataResolved } from "./comunicadoTypes";

type Props = {
  block: ComunicadoDataBlock;
  interactive?: boolean;
  loading?: boolean;
};

function formatKpiValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    if (Math.abs(value) <= 100 && !Number.isInteger(value)) return formatPct(value);
    return formatNumber(value);
  }
  return String(value);
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

function TvDataChartWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
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

function TvDataTableWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const rows = resolved.table?.rows ?? [];
  if (rows.length === 0) {
    return <div className="tdp-data-table tdp-data-table--empty">Sem linhas</div>;
  }
  return (
    <table className="tdp-data-table">
      <thead>
        <tr>
          <th>Código</th>
          <th>Descrição</th>
          <th>Valor</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={`${String(row.productCode ?? index)}`}>
            <td>{String(row.productCode ?? "—")}</td>
            <td>{String(row.description ?? "—")}</td>
            <td>{formatKpiValue(row.stockValue)}</td>
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

  if (block.type === "data_chart" || resolved.chart) {
    return (
      <div className="tdp-data-block tdp-data-block--chart">
        <TvDataChartWidget resolved={resolved} />
      </div>
    );
  }

  if (block.type === "data_table" || resolved.table) {
    return (
      <div className="tdp-data-block tdp-data-block--table">
        <div className="tdp-data-table-wrap">
          <TvDataTableWidget resolved={resolved} />
        </div>
      </div>
    );
  }

  return (
    <div className="tdp-data-block tdp-data-block--kpi">
      <TvDataKpiWidget resolved={resolved} />
    </div>
  );
}
