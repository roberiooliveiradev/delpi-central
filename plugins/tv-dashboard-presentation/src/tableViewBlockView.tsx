import { ConfigurableTable } from "./ConfigurableTable";
import { tablePresetLabel } from "./comunicadoChartView";
import { resolveTableDisplayOptions } from "./comunicadoTableOptions";
import type { ComunicadoTableInteraction } from "./comunicadoTableParts";
import type { ComunicadoTableViewBlock } from "./comunicadoTypes";
import {
  DataBlockRefreshBadge,
  withDataBlockLoadingClass,
} from "./dataBlockRefreshChrome";
import { resolveDataBlockErrorText } from "./resolveDataBlockErrorText";
import { applyViewProjection } from "./viewProjection";
import { resolveTableColumns } from "./tvDataPresentation";

type Props = {
  block: ComunicadoTableViewBlock;
  interactive?: boolean;
  loading?: boolean;
  interaction?: ComunicadoTableInteraction | null;
};

export function TableViewBlockView({
  block,
  interactive = false,
  loading = false,
  interaction = null,
}: Props) {
  const resolved = applyViewProjection(block.resolved, {
    tableProjection: block.tableProjection,
  });
  const label = tablePresetLabel(block.tablePreset);
  const tableInteraction = interactive ? interaction : null;

  const errorText = resolveDataBlockErrorText(resolved);
  if (errorText) {
    return (
      <div
        className={withDataBlockLoadingClass(
          "tdp-data-block tdp-data-block--error",
          loading,
        )}
      >
        <span>{errorText}</span>
        <DataBlockRefreshBadge loading={loading} />
      </div>
    );
  }

  if (!resolved) {
    return (
      <div className={`tdp-data-block tdp-data-block--placeholder${loading ? " tdp-data-block--loading" : ""}`}>
        <span className="tdp-data-block__title">{label}</span>
        <span className="tdp-data-block__hint">
          {loading
            ? "Carregando dados…"
            : interactive
              ? block.dataSourceId?.trim()
                ? "Sem linhas — escolha colunas na conexão do visual"
                : "Conecte uma fonte de dados"
              : "…"}
        </span>
      </div>
    );
  }

  const allRows = resolved.table?.rows ?? [];
  const allColumns = resolveTableColumns(resolved, allRows);
  const widthByKey = new Map(
    (block.tableProjection?.columns ?? [])
      .filter((column) => column.widthPct != null && column.widthPct > 0)
      .map((column) => [column.key, column.widthPct as number]),
  );
  const columns = allColumns.map((column) => {
    const widthPct = widthByKey.get(column.key);
    return widthPct != null ? { ...column, widthPct } : column;
  });
  const tableOptions = resolveTableDisplayOptions(block.tableOptions, block.tablePreset, resolved);

  return (
    <div
      className={withDataBlockLoadingClass("tdp-data-block tdp-data-block--table", loading)}
    >
      <DataBlockRefreshBadge loading={loading} />
      <div className="tdp-data-table-wrap">
        <ConfigurableTable
          columns={columns}
          rows={allRows}
          options={tableOptions}
          preset={block.tablePreset}
          tableParts={block.tableParts}
          interaction={tableInteraction}
        />
      </div>
    </div>
  );
}
