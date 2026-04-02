import type { IndicatorAnalyticsItem } from "../../data/mocks/indicatorsMock";
import { StatusBadge } from "./StatusBadge";

type IndicatorDepartmentOverviewProps = {
  indicators: IndicatorAnalyticsItem[];
};

type DepartmentBucket = {
  departmentId: string;
  departmentName: string;
  totalIndicators: number;
  averageScore: number;
  warningCount: number;
  successCount: number;
  topFocus: string;
};

function buildDepartmentBuckets(
  indicators: IndicatorAnalyticsItem[]
): DepartmentBucket[] {
  const grouped = new Map<string, IndicatorAnalyticsItem[]>();

  for (const indicator of indicators) {
    const list = grouped.get(indicator.departmentId) ?? [];
    list.push(indicator);
    grouped.set(indicator.departmentId, list);
  }

  return [...grouped.entries()]
    .map(([departmentId, items]) => {
      const totalIndicators = items.length;
      const totalScore = items.reduce(
        (sum, item) => sum + item.simulatedScore,
        0
      );
      const averageScore = totalIndicators ? totalScore / totalIndicators : 0;
      const warningCount = items.filter(
        (item) => item.status === "warning" || item.status === "danger"
      ).length;
      const successCount = items.filter(
        (item) => item.status === "success"
      ).length;

      const topFocus =
        [...items].sort((a, b) => a.simulatedScore - b.simulatedScore)[0]
          ?.indicatorName ?? "Sem indicador";

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
              label={`média ${department.averageScore.toFixed(1)}`}
              variant={
                department.averageScore >= 8
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