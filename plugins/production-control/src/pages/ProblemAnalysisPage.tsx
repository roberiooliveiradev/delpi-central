import {
  createDashboardLoadingActivityCard,
  DataTable,
  dataTableBemClasses,
} from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";
import { useProblemAnalysis } from "../hooks/useProblemAnalysis";
import type { PpcBranch, ProblemIssue } from "../types";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { helpTooltips } from "../content/helpTooltips";
import { formatOpQuantity } from "../utils/formatOpQuantity";

const tableClassNames = dataTableBemClasses("ppc");
const tableLabels = {
  emptyMessage: copy.table.empty,
  loadingMessage: copy.table.loading,
  sortByAriaLabel: copy.table.sort,
  headerHelpAriaLabel: copy.table.help,
};

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.problemAnalysis.loading,
  },
});

type ProblemAnalysisPageProps = {
  branch: PpcBranch;
  issueId: string | null;
};

export function ProblemAnalysisPage({ branch, issueId }: ProblemAnalysisPageProps) {
  const { data, loading, error, reload } = useProblemAnalysis(branch, issueId);
  const selected = data?.selected ?? null;
  const issues = data?.issues ?? [];

  const openIssue = (issue: ProblemIssue) => {
    navigatePpc(
      buildPpcHref({
        subpluginId: "problem-analysis",
        branch,
        issueId: issue.id,
      }),
    );
  };

  return (
    <div className="ppc-page-stack">
      <PpcWorkspaceHeader
        title={copy.problemAnalysis.title}
        subtitle={copy.problemAnalysis.subtitle}
        titleHint={helpTooltips.problemAnalysis}
        branch={branch}
        subpluginId="problem-analysis"
        issueId={issueId}
        onRefresh={reload}
      />

      {loading && !data ? (
        <LoadingCard title={copy.problemAnalysis.loading} description={copy.problemAnalysis.loadingHint} />
      ) : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || copy.problemAnalysis.loadError}
        </div>
      ) : null}

      {data ? (
        <div className="ppc-analysis">
          <aside className="ppc-inbox" aria-label={copy.problemAnalysis.inbox}>
            <div className="ppc-inbox__counts">
              <span className="ppc-pill ppc-pill--critical">
                {copy.problemAnalysis.critical} {data.summary.critical}
              </span>
              <span className="ppc-pill ppc-pill--attention">
                {copy.problemAnalysis.attention} {data.summary.attention}
              </span>
              <span className="ppc-pill ppc-pill--ok">
                {copy.problemAnalysis.ok} {data.summary.ok}
              </span>
            </div>
            {issues.length === 0 ? (
              <div className="ppc-state">
                <strong>{copy.problemAnalysis.empty}</strong>
                <p>{copy.problemAnalysis.emptyHint}</p>
              </div>
            ) : (
              <ul className="ppc-inbox__list">
                {issues.map((issue) => {
                  const active = selected?.id === issue.id;
                  return (
                    <li key={issue.id}>
                      <button
                        type="button"
                        className={`ppc-issue${active ? " ppc-issue--active" : ""} ppc-issue--${issue.severity}`}
                        onClick={() => openIssue(issue)}
                      >
                        <span className="ppc-issue__dot" aria-hidden />
                        <span className="ppc-issue__body">
                          <span className="ppc-issue__title">{issue.title}</span>
                          <span className="ppc-issue__meta">
                            {issue.product_code ?? "—"}
                            {issue.product_description ? ` · ${issue.product_description}` : ""}
                          </span>
                        </span>
                        <span className="ppc-issue__delay">
                          {issue.delay_days} {copy.problemAnalysis.days}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </aside>

          <section className="ppc-detail" aria-label={copy.problemAnalysis.detail}>
            {selected ? (
              <>
                <div className={`ppc-severity ppc-severity--${selected.severity}`} />
                <h2 className="ppc-detail__title">{selected.title}</h2>
                <p className="ppc-detail__kind">{copy.problemAnalysis.delayedKind}</p>
                <dl className="ppc-facts">
                  <div>
                    <dt>{copy.problemAnalysis.order}</dt>
                    <dd>{selected.production_order ?? "—"}</dd>
                  </div>
                  <div>
                    <dt>{copy.problemAnalysis.product}</dt>
                    <dd>
                      {selected.product_code ?? "—"}
                      {selected.product_description ? ` — ${selected.product_description}` : ""}
                    </dd>
                  </div>
                  <div>
                    <dt>{copy.problemAnalysis.delay}</dt>
                    <dd>
                      {selected.delay_days} {copy.problemAnalysis.days}
                    </dd>
                  </div>
                </dl>
                <h3 className="ppc-detail__table-title">{copy.problemAnalysis.metricsTitle}</h3>
                <DataTable
                  columns={[
                    {
                      key: "metric",
                      header: "Indicador",
                      render: (row) => row.label,
                    },
                    {
                      key: "value",
                      header: "Valor",
                      align: "right",
                      render: (row) => row.value,
                    },
                  ]}
                  rows={[
                    { key: "planned", label: copy.problemAnalysis.planned, value: formatOpQuantity(selected.metrics.planned_qty) },
                    { key: "produced", label: copy.problemAnalysis.produced, value: formatOpQuantity(selected.metrics.produced_qty) },
                    { key: "pending", label: copy.problemAnalysis.pending, value: formatOpQuantity(selected.metrics.pending_qty) },
                    { key: "wh", label: copy.problemAnalysis.warehouse, value: selected.metrics.warehouse ?? "—" },
                    { key: "delivery", label: copy.problemAnalysis.delivery, value: selected.metrics.delivery_date ?? "—" },
                  ]}
                  rowKey={(row) => row.key}
                  classNames={tableClassNames}
                  labels={tableLabels}
                  layout="embedded"
                />
              </>
            ) : (
              <div className="ppc-state">{copy.problemAnalysis.noSelection}</div>
            )}
          </section>
        </div>
      ) : null}
    </div>
  );
}
