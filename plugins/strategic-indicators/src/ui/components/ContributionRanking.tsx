import type { ExecutiveDepartmentSummary } from "../../data/types/executiveSummaryView";

type ContributionRankingProps = {
  departments: ExecutiveDepartmentSummary[];
};

export function ContributionRanking({
  departments,
}: ContributionRankingProps) {
  const sorted = [...departments].sort(
    (a, b) => b.contribution - a.contribution
  );

  const maxContribution = sorted[0]?.contribution ?? 1;

  return (
    <section className="si-contribution-ranking">
      <div className="si-contribution-ranking__header">
        <h3 className="si-contribution-ranking__title">
          Contribuição ponderada no IGD
        </h3>
        <span className="si-contribution-ranking__subtitle">
          soma das parcelas do índice global
        </span>
      </div>

      <div className="si-contribution-ranking__list">
        {sorted.map((department) => {
          const width = `${(department.contribution / maxContribution) * 100}%`;

          return (
            <div
              key={department.id}
              className="si-contribution-ranking__item"
            >
              <div className="si-contribution-ranking__top">
                <div className="si-contribution-ranking__identity">
                  <strong>{department.name}</strong>
                  <span>{department.weightPct}% do IGD</span>
                </div>

                <strong className="si-contribution-ranking__value">
                  {department.contribution.toFixed(3)}
                </strong>
              </div>

              <div className="si-contribution-ranking__bar">
                <div
                  className="si-contribution-ranking__fill"
                  style={{ width }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}