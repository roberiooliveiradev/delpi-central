import { useEffect, useState } from "react";
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
        setError(err instanceof Error ? err.message : "Erro ao carregar série de ROL.");
        setPoints([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filters.start_date, filters.end_date, filters.customer_segment, granularity]);

  if (loading) return <p className="cm-muted">Carregando evolução de ROL…</p>;
  if (error) return <p className="cm-muted" role="alert">{error}</p>;
  if (points.length === 0) return <p className="cm-muted">Sem pontos no período.</p>;

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
