import { ConfigurableTable } from "./ConfigurableTable";
import { resolveTableDisplayOptions } from "./comunicadoTableOptions";
import type { ComunicadoDataBlock, ComunicadoTablePreset } from "./comunicadoTypes";
import { resolveDataBlockErrorText } from "./resolveDataBlockErrorText";
import {
  resolveChartType,
  resolveEffectiveDisplayMode,
  resolveTableColumns,
} from "./tvDataPresentation";
import {
  TvDataBarChartWidget,
  TvDataKpiWidget,
  TvDataLineChartWidget,
} from "./tvDataChartWidgets";

type Props = {
  block: ComunicadoDataBlock;
  interactive?: boolean;
  loading?: boolean;
};

/** Default Delpi banded — templates claros / data_table sem receita explícita. */
const DEFAULT_DATA_TABLE_BANDED = {
  showBorders: true,
  zebraStripe: true,
  headerBg: "#089bdb",
  headerTextColor: "#ffffff",
  cellBg: "#ffffff",
  cellTextColor: "#0f172a",
  borderColor: "#e2e8f0",
} as const;

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
    const preset: ComunicadoTablePreset = block.tablePreset ?? "banded";
    const tableOptions = resolveTableDisplayOptions(
      block.tableOptions ?? { ...DEFAULT_DATA_TABLE_BANDED },
      preset,
      resolved,
    );
    return (
      <div className="tdp-data-block tdp-data-block--table">
        <div className="tdp-data-table-wrap">
          <ConfigurableTable
            columns={columns}
            rows={rows}
            options={tableOptions}
            preset={preset}
            tableParts={block.tableParts}
          />
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
