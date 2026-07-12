import { ConfigurableTable } from "./ConfigurableTable";
import { tablePresetLabel } from "./comunicadoChartView";
import { resolveTableDisplayOptions } from "./comunicadoTableOptions";
import type { ComunicadoTableInteraction } from "./comunicadoTableParts";
import type { ComunicadoTableViewBlock } from "./comunicadoTypes";
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
  const resolved = block.resolved;
  const label = tablePresetLabel(block.tablePreset);
  const tableInteraction = interactive ? interaction : null;

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

  const rows = (resolved.table?.rows ?? []).slice(0, block.maxRows ?? undefined);
  const columns = resolveTableColumns(resolved, rows);
  const tableOptions = resolveTableDisplayOptions(block.tableOptions, block.tablePreset, resolved);

  return (
    <div className="tdp-data-block tdp-data-block--table">
      <div className="tdp-data-table-wrap">
        <ConfigurableTable
          columns={columns}
          rows={rows}
          options={tableOptions}
          preset={block.tablePreset}
          tableParts={block.tableParts}
          interaction={tableInteraction}
        />
      </div>
    </div>
  );
}
