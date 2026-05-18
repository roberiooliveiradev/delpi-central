import { Download } from "lucide-react";
import type { ReactNode } from "react";

import { ChartGranularityToggle } from "./ChartGranularityToggle";
import type { ChartGranularity } from "../types/chart";

type ChartToolbarProps = {
  granularity: ChartGranularity;
  onGranularityChange: (value: ChartGranularity) => void;
  idPrefix?: string;
  onExportCsv?: () => void;
  exportDisabled?: boolean;
  extra?: ReactNode;
};

export function ChartToolbar({
  granularity,
  onGranularityChange,
  idPrefix,
  onExportCsv,
  exportDisabled = false,
  extra,
}: ChartToolbarProps) {
  return (
    <div className="dc-chart-toolbar">
      <ChartGranularityToggle
        idPrefix={idPrefix}
        value={granularity}
        onChange={onGranularityChange}
      />
      <div className="dc-chart-toolbar__actions">
        {extra}
        {onExportCsv ? (
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
        ) : null}
      </div>
    </div>
  );
}
