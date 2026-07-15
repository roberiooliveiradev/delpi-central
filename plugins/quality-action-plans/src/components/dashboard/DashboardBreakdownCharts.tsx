import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { CHART_HEIGHT } from "../../constants/chartColors";
import {
  CHART_AXIS_TICK,
  CHART_AXIS_TICK_SM,
  CHART_TOOLTIP_PROPS,
} from "../../constants/chartTheme";
import type { DashboardBreakdowns } from "../../types/actionPlan";
import {
  buildActionTypeBreakdownData,
  buildBreakdownChartData,
} from "../../utils/chartData";
import { ChartCard } from "../ui/ChartCard";
import { PAC_STATE_BOX_EMPTY } from "../ui/stateChrome";

type Props = {
  breakdowns?: DashboardBreakdowns | null;
};

type ChartPoint = {
  name: string;
  fullName?: string;
  value: number;
  fill: string;
};

function BreakdownBarChart({ data }: { data: ChartPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--pac-card-border)" />
        <XAxis type="number" allowDecimals={false} tick={CHART_AXIS_TICK} />
        <YAxis type="category" dataKey="name" width={132} tick={CHART_AXIS_TICK_SM} />
        <Tooltip
          formatter={(value, _name, item) => [
            value ?? 0,
            (item?.payload as ChartPoint | undefined)?.fullName ?? "Quantidade",
          ]}
          {...CHART_TOOLTIP_PROPS}
        />
        <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={18}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function EmptyChart({ message }: { message: string }) {
  return <div className={PAC_STATE_BOX_EMPTY}>{message}</div>;
}

export function DashboardBreakdownCharts({ breakdowns }: Props) {
  if (!breakdowns) {
    return null;
  }

  const windowMonths = breakdowns.window_months;
  const rootCauseData = buildBreakdownChartData(breakdowns.by_root_cause);
  const failureModeData = buildBreakdownChartData(breakdowns.by_failure_mode);
  const actionTypeData = buildActionTypeBreakdownData(breakdowns.by_action_type);

  return (
    <div className="pac-charts-grid pac-charts-grid--breakdowns">
      <ChartCard
        title="Por causa raiz"
        hint={`${PAC_HELP_TOOLTIPS.charts.topCategories} (${windowMonths} meses).`}
      >
        {rootCauseData.length ? (
          <BreakdownBarChart data={rootCauseData} />
        ) : (
          <EmptyChart message="Sem causas raiz registradas no período." />
        )}
      </ChartCard>

      <ChartCard
        title="Por modo de falha"
        hint={`${PAC_HELP_TOOLTIPS.charts.topFailureModes} (${windowMonths} meses).`}
      >
        {failureModeData.length ? (
          <BreakdownBarChart data={failureModeData} />
        ) : (
          <EmptyChart message="Sem modos de falha no período." />
        )}
      </ChartCard>

      <ChartCard
        title="Por tipo de ação"
        hint={`${PAC_HELP_TOOLTIPS.charts.actionsMix} (${windowMonths} meses).`}
      >
        {actionTypeData.length ? (
          <BreakdownBarChart data={actionTypeData} />
        ) : (
          <EmptyChart message="Sem ações registradas no período." />
        )}
      </ChartCard>
    </div>
  );
}
