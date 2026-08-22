import { FinBlockState } from "../components/FinBlockState";
import { FinLoadingCard } from "../components/finUiKit";
import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import { DataTable, FIN_TABLE_CLASSES, FIN_TABLE_LABELS } from "../components/dataTableUi";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useIndicators } from "../hooks/useIndicators";
import type { FinancialBranch } from "../types";
import { formatPercent, formatScore, formatIndicatorValue } from "../utils/formatNumbers";

const SI_DEPARTMENT_HREF = "/apps/strategic-indicators/departments/financial";

type IndicatorsPageProps = {
  branch: FinancialBranch;
};

export function IndicatorsPage({ branch }: IndicatorsPageProps) {
  const { data, loading, error, reload } = useIndicators(branch);
  const department = data?.department;
  const global = data?.global;

  return (
    <div className="fin-page-stack fin-page-stack--padded">
      <FinWorkspaceHeader
        title={copy.indicators.title}
        subtitle={copy.indicators.subtitle}
        titleHint={helpTooltips.indicators}
        branch={branch}
        subpluginId="indicators"
        onRefresh={reload}
        refreshBusy={loading}
        actions={
          <a className="fin-icon-btn" href={SI_DEPARTMENT_HREF}>
            {copy.indicators.openDepartment}
          </a>
        }
      />

      {loading && !data ? <FinLoadingCard title={copy.indicators.loading} /> : null}
      {error ? (
        <div className="fin-state fin-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {data ? (
        <>
          <div className="fin-score-grid">
            <article className="fin-score-card" aria-label={copy.indicators.igdTitle}>
              <h2 className="fin-board-list__title">{copy.indicators.igdTitle}</h2>
              {global?.available === false ? (
                <FinBlockState
                  block={{ available: false, error: global.reason ?? copy.indicators.unavailable }}
                />
              ) : (
                <>
                  <p className="fin-score-card__value">{copy.scoreOutOfTen(formatScore(global?.igd))}</p>
                  <p className="fin-score-card__meta">{global?.classification}</p>
                  <p className="fin-score-card__meta">
                    {copy.indicators.bestDepartment}: {global?.bestDepartment ?? copy.indicators.noValue}
                  </p>
                  <p className="fin-score-card__meta">
                    {copy.indicators.primaryRisk}: {global?.primaryRisk ?? copy.indicators.noValue}
                  </p>
                </>
              )}
            </article>

            <article className="fin-score-card" aria-label={copy.indicators.iddTitle}>
              <h2 className="fin-board-list__title">{copy.indicators.iddTitle}</h2>
              {department?.available === false ? (
                <FinBlockState
                  block={{
                    available: false,
                    error: department.reason ?? copy.indicators.unavailable,
                  }}
                />
              ) : (
                <>
                  <p className="fin-score-card__value">
                    {copy.scoreOutOfTen(formatScore(department?.idd))}
                  </p>
                  <p className="fin-score-card__meta">{department?.classification}</p>
                  <p className="fin-score-card__meta">
                    {copy.indicators.contribution}: {formatScore(department?.contribution)}
                  </p>
                  {department?.notice ? <p className="fin-score-card__meta">{department.notice}</p> : null}
                </>
              )}
            </article>
          </div>

          <article className="fin-board-list" aria-label={copy.indicators.tableTitle}>
            <header className="fin-board-list__head">
              <h2 className="fin-board-list__title">{copy.indicators.tableTitle}</h2>
            </header>
            <DataTable
              classNames={FIN_TABLE_CLASSES}
              labels={FIN_TABLE_LABELS}
              columns={[
                {
                  key: "name",
                  header: copy.indicators.columns.indicator,
                  render: (row) => row.name,
                },
                {
                  key: "weight",
                  header: copy.indicators.columns.weight,
                  align: "right",
                  render: (row) => formatPercent(row.weightPct),
                },
                {
                  key: "goal",
                  header: copy.indicators.columns.goal,
                  render: (row) => row.goalLabel ?? copy.indicators.noValue,
                },
                {
                  key: "value",
                  header: copy.indicators.columns.value,
                  align: "right",
                  render: (row) =>
                    row.hasValue
                      ? formatIndicatorValue(row.value, {
                          unit: row.valueUnit,
                          prefix: row.valuePrefix,
                          suffix: row.valueSuffix,
                          decimals: row.valueDecimals,
                        })
                      : copy.indicators.noValue,
                },
                {
                  key: "gap",
                  header: copy.indicators.columns.gap,
                  align: "right",
                  render: (row) => formatIndicatorValue(row.gap, { decimals: 1 }),
                },
                {
                  key: "score",
                  header: copy.indicators.columns.score,
                  align: "right",
                  render: (row) => copy.scoreOutOfTen(formatScore(row.score)),
                },
              ]}
              rows={department?.indicators ?? []}
              rowKey={(row) => row.indicatorId}
              emptyMessage={copy.indicators.tableEmpty}
            />
          </article>
        </>
      ) : null}
    </div>
  );
}
