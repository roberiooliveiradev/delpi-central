import { useEffect, useState } from "react";
import { EmptyState } from "@delpi/plugin-ui/index";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getCommercialRolSeries } from "../../../api/analyticsApi";
import { cmEmptyStateClassNames, CommercialLoadingCard } from "../../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import type { ChartGranularity, CommercialRolSeriesPoint, AnalyticsFilterParams } from "../../../types/analytics";
import { formatCurrency } from "../../../utils/format";

type RolSeriesChartProps = {
  filters: Pick<AnalyticsFilterParams, "start_date" | "end_date" | "customer_segment">;
  granularity?: ChartGranularity;
};

export function AnalyticsRolSeriesChart({
  filters,
  granularity = "month",
}: RolSeriesChartProps) {
  const [points, setPoints] = useState<CommercialRolSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const emptyCopy = ANALYTICS_CONTENT.overview.chartEmpty;

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void getCommercialRolSeries({ ...filters, granularity }, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setPoints(data.points ?? []);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : emptyCopy.rolError);
        setPoints([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [emptyCopy.rolError, filters.start_date, filters.end_date, filters.customer_segment, granularity]);

  if (loading) {
    return <CommercialLoadingCard title={emptyCopy.rolLoading} variant="panel" />;
  }
  if (error) {
    return <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />;
  }
  if (points.length === 0) {
    return (
      <EmptyState
        classNames={{ ...cmEmptyStateClassNames, withTitle: true }}
        defaultTitle={emptyCopy.rolTitle}
        defaultMessage={emptyCopy.rolMessage}
      />
    );
  }

  return (
    <div className="cm-chart-wrap" style={{ width: "100%", height: 280 }}>
      <ResponsiveContainer>
        <LineChart data={points}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="periodo" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => formatCurrency(Number(v))} width={90} />
          <Tooltip formatter={(value) => formatCurrency(Number(value))} />
          <Legend />
          <Line type="monotone" dataKey="rol_matrix" name="ROL matriz" stroke="var(--chart-1, #089bdb)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="rol_branch" name="ROL filial" stroke="var(--chart-2, #10b981)" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
