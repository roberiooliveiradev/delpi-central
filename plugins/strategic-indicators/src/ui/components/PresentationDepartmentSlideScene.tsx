import type {
  PresentationDepartmentFocus,
  PresentationSparklinePoint,
} from "../../data/types/presentation";
import { resolveIndicatorSparklineDirection } from "../../data/utils/resolveScoreTrendDirection";
import { PresentationDepartmentSparkline } from "./PresentationDepartmentSparkline";
import {
  formatIndicatorGapDisplay,
  formatIndicatorGoalValue,
  formatIndicatorRealizedDisplay,
  formatIndicatorScore,
} from "../shared/indicatorValueFormatter";
import { ScopeMetricBadges } from "./ScopeMetricBadges";
import "./PresentationDepartmentSlideScene.css";

type PresentationDepartmentSlideSceneProps = {
  department: PresentationDepartmentFocus | null;
  series?: PresentationSparklinePoint[];
  mode: "meeting" | "tv" | "slide";
  competence?: string | null;
};

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function formatSignedScore(value: number) {
  const formatted = formatScore(Math.abs(value));
  return `${value > 0 ? "+" : value < 0 ? "-" : ""}${formatted}`;
}

function formatPercent(value: number) {
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

function getDirectionVariant(direction: "up" | "down" | "stable") {
  if (direction === "up") return "success";
  if (direction === "down") return "warning";
  return "neutral";
}

function getDirectionText(direction: "up" | "down" | "stable") {
  if (direction === "up") return "Melhora";
  if (direction === "down") return "Queda";
  return "Estável";
}

function buildFallbackSeries(
  department: PresentationDepartmentFocus,
): PresentationSparklinePoint[] {
  const previous = Math.max(0, department.score - department.variation.value);

  return [
    { period: "Anterior", value: previous },
    { period: "Atual", value: department.score },
  ];
}

function getScoredIndicators(department: PresentationDepartmentFocus) {
  return department.indicators.filter(
    (indicator): indicator is PresentationDepartmentFocus["indicators"][number] & {
      score: number;
    } => indicator.score !== null,
  );
}

function getBestIndicator(department: PresentationDepartmentFocus) {
  const scored = getScoredIndicators(department);
  if (!scored.length) return null;
  return [...scored].sort((a, b) => b.score - a.score)[0] ?? null;
}

function getWorstIndicator(department: PresentationDepartmentFocus) {
  const scored = getScoredIndicators(department);
  if (!scored.length) return null;
  return [...scored].sort((a, b) => a.score - b.score)[0] ?? null;
}

function getCriticalIndicators(department: PresentationDepartmentFocus) {
  return getScoredIndicators(department).filter((indicator) => indicator.score < 7);
}

function getHighlightIndicators(department: PresentationDepartmentFocus) {
  return getScoredIndicators(department).filter((indicator) => indicator.score >= 9);
}

function buildClosingSentence(department: PresentationDepartmentFocus) {
  const bestIndicator = getBestIndicator(department);
  const worstIndicator = getWorstIndicator(department);

  if (!bestIndicator && !worstIndicator) {
    return `${department.name} sem indicadores suficientes para leitura complementar.`;
  }

  if (bestIndicator && worstIndicator && bestIndicator.id !== worstIndicator.id) {
    return `${bestIndicator.name} sustenta o resultado; ${worstIndicator.name} concentra a principal oportunidade de reação.`;
  }

  return `${department.name} com leitura concentrada em ${
    bestIndicator?.name ?? worstIndicator?.name
  }.`;
}

function buildIndicatorChartSeries(
  indicator: PresentationDepartmentFocus["indicators"][number],
) {
  if (indicator.series?.length) {
    return indicator.series
      .filter((point) => point.score !== null && point.score !== undefined)
      .map((point) => ({
        period: point.period,
        value: point.score as number,
      }));
  }

  if (indicator.score === null) {
    return [];
  }

  return [{ period: "Atual", value: indicator.score }];
}

function getIndicatorValueFormat(
  indicator: PresentationDepartmentFocus["indicators"][number],
) {
  return {
    valueUnit: indicator.valueUnit,
    valuePrefix: indicator.valuePrefix,
    valueSuffix: indicator.valueSuffix,
    valueDecimals: indicator.valueDecimals,
  };
}

export function PresentationDepartmentSlideScene({
  department,
  series,
  mode,
  competence,
}: PresentationDepartmentSlideSceneProps) {
  if (!department) {
    return (
      <section className="si-presentation-department-slide si-presentation-scene-card">
        <div className="si-presentation-state">
          <h2>Nenhum departamento selecionado</h2>
          <p>Selecione uma área para visualizar o slide executivo.</p>
        </div>
      </section>
    );
  }

  const bestIndicator = getBestIndicator(department);
  const worstIndicator = getWorstIndicator(department);
  const criticalIndicators = getCriticalIndicators(department);
  const highlightIndicators = getHighlightIndicators(department);
  const trendPoints = series?.length ? series : buildFallbackSeries(department);
  const closingSentence = buildClosingSentence(department);
  const compact = mode === "tv";

  return (
    <section
      className={`si-presentation-department-slide si-presentation-scene-card si-presentation-department-slide--${mode}`}
    >
      <header className="si-presentation-department-slide__hero">
        <div className="si-presentation-department-slide__hero-main">
          <div className="si-presentation-department-slide__badge-row">
            <span className="si-presentation-department-slide__department-badge">
              {department.shortName}
            </span>

            <span
              className={`si-status-badge si-status-badge--${getDirectionVariant(
                department.variation.direction,
              )}`}
            >
              {department.classification}
            </span>
          </div>

          <h2 className="si-presentation-department-slide__title">
            {department.name}
          </h2>

          {!compact ? (
            <p className="si-presentation-department-slide__subtitle">
              {department.strategicSummary}
            </p>
          ) : null}
        </div>

        <div className="si-presentation-department-slide__hero-metrics">
          <div className="si-presentation-metric-card">
            <span className="si-presentation-metric-card__label">Score atual</span>
            <strong className="si-presentation-metric-card__value">
              {formatScore(department.score)}
            </strong>
          </div>

          <div className="si-presentation-metric-card">
            <span className="si-presentation-metric-card__label">Variação</span>
            <strong className="si-presentation-metric-card__value">
              {formatSignedScore(department.variation.value)}
            </strong>
            <small className="si-presentation-metric-card__support">
              {getDirectionText(department.variation.direction)}
            </small>
          </div>

          <div className="si-presentation-metric-card">
            <span className="si-presentation-metric-card__label">Peso no IGD</span>
            <strong className="si-presentation-metric-card__value">
              {formatPercent(department.weightInIgd)}
            </strong>
          </div>

          <div className="si-presentation-metric-card">
            <span className="si-presentation-metric-card__label">
              Contribuição no IGD
            </span>
            <strong className="si-presentation-metric-card__value">
              {formatScore(department.contribution)}
            </strong>
          </div>
        </div>
      </header>

      <article className="si-presentation-department-slide__panel si-presentation-department-slide__panel--full">
        <div className="si-presentation-department-slide__panel-header">
          <h3>Evolução da área</h3>
          <span>{department.variation.directionLabel}</span>
        </div>

        <div className="si-presentation-department-slide__trend-panel si-presentation-department-slide__trend-panel--full">
          <PresentationDepartmentSparkline
            points={trendPoints}
            direction={department.variation.direction}
            height={164}
            showGrid
          />
        </div>
      </article>

      <div className="si-presentation-department-slide__priority-grid si-presentation-department-slide__priority-grid--indicators">
        {department.indicators.map((indicator) => {
          const valueFormat = getIndicatorValueFormat(indicator);
          const chartSeries = buildIndicatorChartSeries(indicator);
          const sparklineDirection = resolveIndicatorSparklineDirection(
            chartSeries,
            indicator.trend,
          );

          return (
            <article
              key={indicator.id}
              className="si-presentation-department-slide__priority-card si-presentation-department-slide__priority-card--indicator"
            >
              <div className="si-presentation-department-slide__priority-top">
                <h4>{indicator.name}</h4>
                <span
                  className={`si-status-badge si-status-badge--${getDirectionVariant(
                    sparklineDirection,
                  )}`}
                >
                  {getDirectionText(sparklineDirection)}
                </span>
              </div>

              <div className="si-presentation-department-slide__indicator-chart">
                <PresentationDepartmentSparkline
                  points={chartSeries}
                  direction={sparklineDirection}
                  height={88}
                  compact
                />
              </div>

              <div className="si-presentation-department-slide__priority-metrics si-presentation-department-slide__priority-metrics--grid">
                <div>
                  <span>Score</span>
                  <strong>{formatIndicatorScore(indicator.score)}</strong>
                </div>

                <div>
                  <span>Valor atual</span>
                  <strong>
                    <ScopeMetricBadges
                      values={indicator.realized}
                      format={valueFormat}
                      maxVisible={2}
                      emptyLabel={formatIndicatorRealizedDisplay(indicator, valueFormat)}
                    />
                  </strong>
                </div>

                <div>
                  <span>Meta</span>
                  <strong>
                    <ScopeMetricBadges
                      values={indicator.goals}
                      format={valueFormat}
                      maxVisible={2}
                      emptyLabel={formatIndicatorGoalValue(indicator, competence)}
                    />
                  </strong>
                </div>

                <div>
                  <span>Gap</span>
                  <strong>
                    <ScopeMetricBadges
                      values={indicator.gaps}
                      format={valueFormat}
                      maxVisible={2}
                      emptyLabel={formatIndicatorGapDisplay(indicator, valueFormat)}
                    />
                  </strong>
                </div>

                <div>
                  <span>Peso</span>
                  <strong>{formatPercent(indicator.weightPct)}</strong>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      <div className="si-presentation-department-slide__signal-grid">
        <article className="si-presentation-department-slide__signal-card">
          <span>Melhor indicador</span>
          <strong>{bestIndicator?.name ?? "—"}</strong>
        </article>

        <article className="si-presentation-department-slide__signal-card">
          <span>Pior indicador</span>
          <strong>{worstIndicator?.name ?? "—"}</strong>
        </article>

        <article className="si-presentation-department-slide__signal-card">
          <span>Em atenção</span>
          <strong>{criticalIndicators.length}</strong>
        </article>

        <article className="si-presentation-department-slide__signal-card">
          <span>Destaques</span>
          <strong>{highlightIndicators.length}</strong>
        </article>

        <article className="si-presentation-department-slide__signal-card">
          <span>Agregação</span>
          <strong>{department.aggregationMode}</strong>
        </article>

        <article className="si-presentation-department-slide__signal-card">
          <span>Unidades</span>
          <strong>
            {department.units.length
              ? department.units.map((unit) => unit.name).join(", ")
              : "—"}
          </strong>
        </article>

        <article className="si-presentation-department-slide__signal-card">
          <span>Leitura</span>
          <strong>{department.classification}</strong>
        </article>

        <article className="si-presentation-department-slide__signal-card">
          <span>Direção</span>
          <strong>{department.variation.directionLabel}</strong>
        </article>
      </div>

      {!compact ? (
        <footer className="si-presentation-department-slide__closing">
          <p>{closingSentence}</p>
        </footer>
      ) : null}
    </section>
  );
}