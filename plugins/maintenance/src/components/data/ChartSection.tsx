import { useState, type ReactNode } from "react";
import { Maximize2 } from "lucide-react";

import { ChartExpandModal } from "./ChartExpandModal";

type ChartSectionProps = {
  title: string;
  /** Conteúdo estático (loading, vazio) — sem botão expandir. */
  children?: ReactNode;
  /** Renderiza o gráfico com altura explícita (inline e modal). */
  renderChart?: (height: number) => ReactNode;
  actions?: ReactNode;
  inlineChartHeight?: number;
  expandedChartHeight?: number;
};

const DEFAULT_INLINE_HEIGHT = 280;
const DEFAULT_EXPANDED_HEIGHT = 560;

export function ChartSection({
  title,
  children,
  renderChart,
  actions,
  inlineChartHeight = DEFAULT_INLINE_HEIGHT,
  expandedChartHeight = DEFAULT_EXPANDED_HEIGHT,
}: ChartSectionProps) {
  const [expanded, setExpanded] = useState(false);
  const expandable = Boolean(renderChart);

  return (
    <>
      <section className="dm-card dm-chart-section">
        <div className="dm-section-header">
          <div className="dm-section-header__title-group">
            <h3 className="dm-section-header__title">{title}</h3>
          </div>
          <div className="dm-section-header__meta">
            {actions}
            {expandable ? (
              <button
                type="button"
                className="dm-ghost-btn dm-chart-section__expand"
                onClick={() => setExpanded(true)}
                aria-label={`Expandir gráfico: ${title}`}
              >
                <Maximize2 size={16} aria-hidden="true" />
                Expandir
              </button>
            ) : null}
          </div>
        </div>
        <div className="dm-chart-wrap">
          {renderChart ? renderChart(inlineChartHeight) : children}
        </div>
      </section>

      {expandable ? (
        <ChartExpandModal
          open={expanded}
          title={title}
          onClose={() => setExpanded(false)}
          actions={actions}
        >
          {renderChart!(expandedChartHeight)}
        </ChartExpandModal>
      ) : null}
    </>
  );
}
