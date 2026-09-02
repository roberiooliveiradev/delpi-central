import { TabHintCell } from "@delpi/plugin-ui/index";
import { Clock3, Gauge } from "lucide-react";

import { EF_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { EficienciaFabrilDashboardTab } from "../utils/dashboardTab";
import {
  DASHBOARD_TAB_EFFICIENCY,
  DASHBOARD_TAB_UNPRODUCTIVE_HOURS,
} from "../utils/dashboardTab";

type DashboardSectionTabsProps = {
  activeTab: EficienciaFabrilDashboardTab;
  onChange: (tab: EficienciaFabrilDashboardTab) => void;
};

export function DashboardSectionTabs({ activeTab, onChange }: DashboardSectionTabsProps) {
  return (
    <div className="ef-section-tabs" role="tablist" aria-label="Seções do dashboard">
      <TabHintCell
        label="Eficiência"
        hint={EF_HELP_TOOLTIPS.tabs.efficiency}
        active={activeTab === DASHBOARD_TAB_EFFICIENCY}
        onSelect={() => onChange(DASHBOARD_TAB_EFFICIENCY)}
        cellClassName="ef-section-tabs__cell"
        tabClassName="ef-section-tabs__tab"
        tabActiveClassName="is-active"
      >
        <Gauge size={15} aria-hidden="true" />
        Eficiência
      </TabHintCell>
      <TabHintCell
        label="Horas improdutivas"
        hint={EF_HELP_TOOLTIPS.tabs.unproductiveHours}
        active={activeTab === DASHBOARD_TAB_UNPRODUCTIVE_HOURS}
        onSelect={() => onChange(DASHBOARD_TAB_UNPRODUCTIVE_HOURS)}
        cellClassName="ef-section-tabs__cell"
        tabClassName="ef-section-tabs__tab"
        tabActiveClassName="is-active"
      >
        <Clock3 size={15} aria-hidden="true" />
        Horas improdutivas
      </TabHintCell>
    </div>
  );
}
