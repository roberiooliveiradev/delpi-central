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
    <div className="dq-chart-toolbar">
      <ChartGranularityToggle
        idPrefix={idPrefix}
        value={granularity}
        onChange={onGranularityChange}
      />
      <div className="dq-chart-toolbar__actions">
        {extra}
        {onExportCsv ? (
          <button
            type="button"
            className="dq-ghost-btn dq-chart-toolbar__export"
            onClick={onExportCsv}
            disabled={exportDisabled}
          >
            <Download size={16} />
            Exportar série
          </button>
        ) : null}
      </div>
    </div>
  );
}
