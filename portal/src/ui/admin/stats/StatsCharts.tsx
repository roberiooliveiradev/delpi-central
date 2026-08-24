// src/ui/admin/stats/StatsCharts.tsx

export type ChartSegment = {
  label: string;
  value: number;
  color: string;
};

export type BarChartItem = {
  id: string;
  label: string;
  value: number;
  sublabel?: string;
};

type DonutChartProps = {
  segments: ChartSegment[];
  centerValue?: string;
  centerLabel?: string;
  size?: number;
};

export function DonutChart({
  segments,
  centerValue,
  centerLabel = "Total",
  size = 132,
}: DonutChartProps) {
  const total = segments.reduce((sum, item) => sum + item.value, 0);
  const filtered = segments.filter((item) => item.value > 0);

  if (total <= 0 || filtered.length === 0) {
    return (
      <div className="admin-stats-chart admin-stats-chart--empty">
        <div
          className="admin-stats-donut admin-stats-donut--empty"
          style={{ width: size, height: size }}
        >
          <span>Sem dados</span>
        </div>
      </div>
    );
  }

  let accumulated = 0;
  const gradientStops = filtered
    .map((segment) => {
      const start = (accumulated / total) * 100;
      accumulated += segment.value;
      const end = (accumulated / total) * 100;
      return `${segment.color} ${start}% ${end}%`;
    })
    .join(", ");

  return (
    <div className="admin-stats-chart">
      <div
        className="admin-stats-donut"
        style={{
          width: size,
          height: size,
          background: `conic-gradient(${gradientStops})`,
        }}
      >
        <div className="admin-stats-donut__hole">
          <strong>{centerValue ?? total.toLocaleString("pt-BR")}</strong>
          <span>{centerLabel}</span>
        </div>
      </div>
      <ul className="admin-stats-legend">
        {filtered.map((segment) => (
          <li key={segment.label}>
            <span
              className="admin-stats-legend__dot"
              style={{ background: segment.color }}
              aria-hidden="true"
            />
            <span className="admin-stats-legend__label">{segment.label}</span>
            <span className="admin-stats-legend__value">
              {segment.value.toLocaleString("pt-BR")}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

type LineChartPoint = {
  label: string;
  value: number;
};

type LineChartProps = {
  points: LineChartPoint[];
  valueLabel?: string;
  accent?: string;
};

export function LineChart({
  points,
  valueLabel = "",
  accent = "var(--chart-1)",
}: LineChartProps) {
  if (points.length === 0) {
    return <p className="admin-stats__empty">Sem dados para exibir.</p>;
  }

  const width = 640;
  const height = 180;
  const padding = { top: 16, right: 12, bottom: 28, left: 12 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const max = Math.max(...points.map((point) => point.value), 1);

  const coords = points.map((point, index) => {
    const x =
      padding.left +
      (points.length === 1 ? innerWidth / 2 : (index / (points.length - 1)) * innerWidth);
    const y = padding.top + innerHeight - (point.value / max) * innerHeight;
    return { ...point, x, y };
  });

  const polyline = coords.map((point) => `${point.x},${point.y}`).join(" ");

  return (
    <div className="admin-stats-line-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Gráfico de linha">
        <polyline
          fill="none"
          stroke={accent}
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
          points={polyline}
        />
        {coords.map((point) => (
          <circle
            key={point.label}
            cx={point.x}
            cy={point.y}
            r="3.5"
            fill={accent}
          />
        ))}
      </svg>
      <ul className="admin-stats-line-chart__labels">
        {coords.map((point) => (
          <li key={point.label}>
            <span>{point.label.slice(5)}</span>
            <strong>
              {point.value.toLocaleString("pt-BR")}
              {valueLabel ? ` ${valueLabel}` : ""}
            </strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

type BarChartProps = {
  items: BarChartItem[];
  valueLabel?: string;
  maxItems?: number;
  accent?: string;
};

export function BarChart({
  items,
  valueLabel = "",
  maxItems = 6,
  accent = "linear-gradient(90deg, var(--chart-2), var(--chart-1))",
}: BarChartProps) {
  const visible = items.slice(0, maxItems);

  if (visible.length === 0) {
    return <p className="admin-stats__empty">Sem dados para exibir.</p>;
  }

  const max = Math.max(...visible.map((item) => item.value), 1);

  return (
    <div className="admin-stats-bars-chart">
      {visible.map((item, index) => {
        const width = Math.max(6, Math.round((item.value / max) * 100));

        return (
          <div key={item.id} className="admin-stats-bars-chart__row">
            <div className="admin-stats-bars-chart__meta">
              <span className="admin-stats-bars-chart__rank">{index + 1}</span>
              <div className="admin-stats-bars-chart__text">
                <span className="admin-stats-bars-chart__label" title={item.label}>
                  {item.label}
                </span>
                {item.sublabel ? (
                  <span className="admin-stats-bars-chart__sublabel">{item.sublabel}</span>
                ) : null}
              </div>
              <span className="admin-stats-bars-chart__value">
                {item.value.toLocaleString("pt-BR")}
                {valueLabel ? ` ${valueLabel}` : ""}
              </span>
            </div>
            <div className="admin-stats-bars-chart__track" aria-hidden="true">
              <div
                className="admin-stats-bars-chart__fill"
                style={{ width: `${width}%`, background: accent }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

type LiveAppUsageCardProps = {
  appName: string;
  appId: string;
  userCount: number;
  sessionCount: number;
  users: { id: string; name?: string | null; email?: string | null }[];
};

export function LiveAppUsageCard({
  appName,
  appId,
  userCount,
  sessionCount,
  users,
}: LiveAppUsageCardProps) {
  return (
    <article className="admin-stats-live-card">
      <header className="admin-stats-live-card__head">
        <div>
          <strong>{appName}</strong>
          <span>{appId}</span>
        </div>
        <div className="admin-stats-live-card__counts">
          <span>{userCount} usuário{userCount === 1 ? "" : "s"}</span>
          <span>
            {sessionCount} sessão{sessionCount === 1 ? "" : "ões"}
          </span>
        </div>
      </header>
      {users.length > 0 ? (
        <ul className="admin-stats-live-card__users">
          {users.map((user) => (
            <li key={user.id}>
              <span className="admin-stats-live-card__avatar" aria-hidden="true">
                {(user.name || user.email || "?").slice(0, 2).toUpperCase()}
              </span>
              <div>
                <span className="admin-stats-live-card__name">
                  {user.name || "Usuário"}
                </span>
                <span className="admin-stats-live-card__email">{user.email}</span>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="admin-stats__empty">Nenhum usuário neste app no momento.</p>
      )}
    </article>
  );
}
