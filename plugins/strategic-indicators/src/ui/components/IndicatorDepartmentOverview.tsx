import type { IndicatorAnalyticsViewItem } from "../../data/types/indicatorAnalyticsView";
import { formatIndicatorScore } from "../shared/indicatorValueFormatter";
import { StatusBadge } from "./StatusBadge";
import "./IndicatorDepartmentOverview.css";

type IndicatorDepartmentOverviewProps = {
  indicators: IndicatorAnalyticsViewItem[];
};

type DepartmentBucket = {
  departmentId: string;
  departmentName: string;
  totalIndicators: number;
  averageScore: number | null;
  warningCount: number;
  successCount: number;
  topFocus: string;
};

function buildDepartmentBuckets(
  indicators: IndicatorAnalyticsViewItem[]
): DepartmentBucket[] {
  const grouped = new Map<string, IndicatorAnalyticsViewItem[]>();

  for (const indicator of indicators) {
    const list = grouped.get(indicator.departmentId) ?? [];
    list.push(indicator);
    grouped.set(indicator.departmentId, list);
  }

  return [...grouped.entries()]
    .map(([departmentId, items]) => {
      const totalIndicators = items.length;
      const scoredItems = items.filter(
        (item) => item.score !== null && item.score !== undefined,
      );
      const totalScore = scoredItems.reduce(
        (sum, item) => sum + Number(item.score),
        0,
      );
      const averageScore = scoredItems.length
        ? totalScore / scoredItems.length
        : null;
      const warningCount = items.filter(
        (item) => item.status === "warning" || item.status === "danger"
      ).length;
      const successCount = items.filter(
        (item) => item.status === "success"
      ).length;

      const topFocus =
        [...scoredItems].sort((a, b) => Number(a.score) - Number(b.score))[0]
          ?.indicatorName ?? "Sem indicador com nota";

      return {
        departmentId,
        departmentName: items[0]?.departmentName ?? departmentId,
        totalIndicators,
        averageScore,
        warningCount,
        successCount,
        topFocus,
      };
    })
    .sort((a, b) => a.departmentName.localeCompare(b.departmentName));
}

export function IndicatorDepartmentOverview({
  indicators,
}: IndicatorDepartmentOverviewProps) {
  const departments = buildDepartmentBuckets(indicators);

  if (!departments.length) {
    return (
      <div className="si-indicator-department-overview si-indicator-department-overview--empty">
        Nenhum departamento encontrado para os filtros aplicados.
      </div>
    );
  }

  return (
    <div className="si-indicator-department-overview">
      {departments.map((department) => (
        <article
          key={department.departmentId}
          className="si-indicator-department-card"
        >
          <div className="si-indicator-department-card__top">
            <div>
              <h3 className="si-indicator-department-card__title">
                {department.departmentName}
              </h3>
              <p className="si-indicator-department-card__subtitle">
                {department.totalIndicators} indicadores no recorte atual
              </p>
            </div>

            <StatusBadge
              label={`média ${
                department.averageScore === null
                  ? formatIndicatorScore(null)
                  : department.averageScore.toFixed(1)
              }`}
              variant={
                department.averageScore === null
                  ? "info"
                  : department.averageScore >= 8
                  ? "success"
                  : department.averageScore >= 7
                    ? "info"
                    : department.averageScore >= 6
                      ? "warning"
                      : "danger"
              }
            />
          </div>

          <div className="si-indicator-department-card__metrics">
            <div className="si-indicator-department-card__metric">
              <span className="si-indicator-department-card__metric-label">
                Faixa alta
              </span>
              <strong className="si-indicator-department-card__metric-value">
                {department.successCount}
              </strong>
            </div>

            <div className="si-indicator-department-card__metric">
              <span className="si-indicator-department-card__metric-label">
                Atenção
              </span>
              <strong className="si-indicator-department-card__metric-value">
                {department.warningCount}
              </strong>
            </div>
          </div>

          <div className="si-indicator-department-card__focus">
            <span className="si-indicator-department-card__focus-label">
              Principal foco analítico
            </span>
            <strong className="si-indicator-department-card__focus-value">
              {department.topFocus}
            </strong>
          </div>
        </article>
      ))}
    </div>
  );
}