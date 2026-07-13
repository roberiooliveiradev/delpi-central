import { ChevronRight } from "lucide-react";
import {
  isChartElementEnabled,
  type ChartElementId,
  type ComunicadoChartOptions,
} from "@delpi/tv-dashboard-presentation";

import { CHART_ADD_ELEMENT_ITEMS } from "../content/chartAddElementItems";

type Props = {
  options: ComunicadoChartOptions;
  onToggle: (elementId: ChartElementId, enabled: boolean) => void;
  className?: string;
};

/** Menu cascata compartilhado (ribbon + float). */
export function ChartAddElementMenu({ options, onToggle, className }: Props) {
  return (
    <ul
      className={["td-deck-ribbon__cascade-menu", className].filter(Boolean).join(" ")}
      role="menu"
      aria-label="Adicionar elemento de gráfico"
    >
      {CHART_ADD_ELEMENT_ITEMS.map((item) => {
        const enabled = isChartElementEnabled(item.id, options);
        const Icon = item.icon;
        return (
          <li key={item.id}>
            <button
              type="button"
              role="menuitemcheckbox"
              aria-checked={enabled}
              className="td-deck-ribbon__cascade-item"
              onClick={() => onToggle(item.id, !enabled)}
            >
              <Icon size={16} aria-hidden="true" />
              <span>{item.label}</span>
              {enabled ? <ChevronRight size={14} aria-hidden="true" /> : null}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
