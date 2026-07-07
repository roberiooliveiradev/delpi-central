import { Download } from "lucide-react";
import type { ReactNode } from "react";

import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { ChartGranularityToggle } from "./ChartGranularityToggle";
import { HelpTooltip } from "@delpi/plugin-ui";
import type { ChartGranularity } from "../types/chart";

type ChartToolbarProps = {
  granularity: ChartGranularity;
  onGranularityChange: (value: ChartGranularity) => void;
  idPrefix?: string;
  onExportCsv?: () => void;
  exportDisabled?: boolean;
  exportActions?: ReactNode;
  extra?: ReactNode;
};

export function ChartToolbar({
  granularity,
  onGranularityChange,
  idPrefix,
  onExportCsv,
  exportDisabled = false,
  exportActions,
  extra,
}: ChartToolbarProps) {
  return (
    <div className="dc-chart-toolbar">
      <div className="dc-chart-toolbar__granularity">
        <ChartGranularityToggle
          idPrefix={idPrefix}
          value={granularity}
          onChange={onGranularityChange}
        />
        <HelpTooltip
          content={COMMERCIAL_HELP_TOOLTIPS.charts.rolGranularity}
          ariaLabel="Ajuda: agrupamento do gráfico"
          className="dc-chart-toolbar__granularity-help"
        />
      </div>
      <div className="dc-chart-toolbar__actions">
        {extra}
        {exportActions}
        {!exportActions && onExportCsv ? (
          <div className="dc-chart-toolbar__action">
            <button
              type="button"
              className="dc-ghost-btn dc-chart-toolbar__export"
              onClick={onExportCsv}
              disabled={exportDisabled}
              aria-label="Exportar série do gráfico em CSV"
            >
              <Download size={16} aria-hidden />
              <span>Exportar série</span>
            </button>
            <HelpTooltip
              content={COMMERCIAL_HELP_TOOLTIPS.charts.rolExport}
              ariaLabel="Ajuda: exportar CSV"
              className="dc-chart-toolbar__action-help"
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
