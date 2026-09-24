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
import { resolveTableColumns } from "./tvDataPresentation";

type Props = {
  block: ComunicadoTableViewBlock;
  interactive?: boolean;
  loading?: boolean;
  interaction?: ComunicadoTableInteraction | null;
};

function projectionColumns(block: ComunicadoTableViewBlock) {
  return (block.tableProjection?.columns ?? [])
    .filter((column) => column.visible !== false && Boolean(column.key?.trim()))
    .map((column) => ({
      key: column.key,
      label: column.label?.trim() || column.key,
      ...(column.widthPct != null && column.widthPct > 0 ? { widthPct: column.widthPct } : {}),
      ...(column.displayFormat ? { displayFormat: column.displayFormat } : {}),
      ...(column.valueFormat ? { valueFormat: column.valueFormat } : {}),
    }));
}

function hasTableChrome(
  block: ComunicadoTableViewBlock,
  columns: Array<{ key: string }>,
  optionsTitle?: string | null,
): boolean {
  if (columns.length > 0) return true;
  if (optionsTitle?.trim()) return true;
  const partTitle = block.tableParts?.title?.content?.trim();
  return Boolean(partTitle);
}

export function TableViewBlockView({
  block,
  interactive = false,
  loading = false,
  interaction = null,
}: Props) {
  // FE-BE-002: paint uses enrich bake only — no client re-projection (E4).
  const resolved = block.resolved;
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
    const columns = projectionColumns(block);
    const tableOptions = resolveTableDisplayOptions(block.tableOptions, block.tablePreset, undefined);
    if (hasTableChrome(block, columns, tableOptions.title)) {
      return (
        <div
          className={withDataBlockLoadingClass("tdp-data-block tdp-data-block--table", loading)}
        >
          <DataBlockRefreshBadge loading={loading} />
          <div className="tdp-data-table-wrap">
            <ConfigurableTable
              columns={columns}
              rows={[]}
              options={tableOptions}
              preset={block.tablePreset}
              tableParts={block.tableParts}
              interaction={tableInteraction}
              emptyMessage={loading ? "Carregando dados…" : "Sem linhas"}
            />
          </div>
        </div>
      );
    }
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
  const displayRows = resolved.table?.displayRows;
  const useServerDisplayRows =
    Array.isArray(displayRows) &&
    displayRows.length > 0 &&
    displayRows.length === allRows.length;
  const paintOnly =
    resolved.serverDisplayApplied === true || resolved.presentationStale === true;
  const paintRows = useServerDisplayRows
    ? allRows.map((row, index) => {
        const painted = displayRows![index] ?? {};
        return { ...row, ...painted };
      })
    : paintOnly
      ? allRows.map((row) => {
          const next: Record<string, unknown> = { ...row };
          for (const key of Object.keys(row)) {
            const v = row[key];
            next[key] = typeof v === "string" ? v : "—";
          }
          return next;
        })
      : allRows;
  const fromResolved = resolveTableColumns(resolved, allRows);
  const fromProjection = projectionColumns(block);
  const allColumns = fromResolved.length > 0 ? fromResolved : fromProjection;
  const projectionByKey = new Map(
    (block.tableProjection?.columns ?? []).map((column) => [column.key, column]),
  );
  const columns = allColumns.map((column) => {
    const projected = projectionByKey.get(column.key);
    const widthPct =
      projected?.widthPct != null && projected.widthPct > 0 ? projected.widthPct : undefined;
    if (useServerDisplayRows || paintOnly) {
      // displayRows already formatted — neutralize client format so paint is paint-only.
      return {
        ...column,
        ...(widthPct != null ? { widthPct } : {}),
        ...(projected?.label?.trim() ? { label: projected.label } : {}),
        valueFormat: "auto" as const,
        displayFormat: undefined,
      };
    }
    return {
      ...column,
      ...(widthPct != null ? { widthPct } : {}),
      ...(projected?.displayFormat ? { displayFormat: projected.displayFormat } : {}),
      ...(projected?.valueFormat ? { valueFormat: projected.valueFormat } : {}),
      ...(projected?.label?.trim() ? { label: projected.label } : {}),
    };
  });
  const tableOptions =
    useServerDisplayRows || paintOnly
      ? {
          ...resolveTableDisplayOptions(block.tableOptions, block.tablePreset, resolved),
          displayValueFormat: undefined,
          valueFormat: "auto" as const,
        }
      : resolveTableDisplayOptions(block.tableOptions, block.tablePreset, resolved);

  return (
    <div
      className={withDataBlockLoadingClass("tdp-data-block tdp-data-block--table", loading)}
    >
      <DataBlockRefreshBadge loading={loading} />
      <div className="tdp-data-table-wrap">
        <ConfigurableTable
          columns={columns}
          rows={paintRows}
          options={tableOptions}
          preset={block.tablePreset}
          tableParts={block.tableParts}
          interaction={tableInteraction}
        />
      </div>
    </div>
  );
}
