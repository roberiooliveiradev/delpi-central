import { useMemo } from "react";

import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type { FinancialBranch } from "../types";
import { buildFinancialHref, replaceFinancialQuery } from "../utils/routeParser";

type FreightPageProps = {
  branch: FinancialBranch;
  issueStart: string | null;
  issueEnd: string | null;
  entryStart: string | null;
  entryEnd: string | null;
  supplierCode: string | null;
  invoiceDocument: string | null;
  freightDocument: string | null;
  situation: string | null;
  page: number;
};

type FreightQuery = Omit<FreightPageProps, "branch"> & { branch: FinancialBranch };

const SITUATION_OPTIONS = ["all", "normal", "above_limit", "inconsistent"] as const;

function freightHref(query: FreightQuery): string {
  return buildFinancialHref({
    subpluginId: "freight",
    branch: query.branch,
    issueStart: query.issueStart,
    issueEnd: query.issueEnd,
    entryStart: query.entryStart,
    entryEnd: query.entryEnd,
    supplierCode: query.supplierCode,
    invoiceDocument: query.invoiceDocument,
    freightDocument: query.freightDocument,
    situation: query.situation,
    page: query.page,
  });
}

export function FreightPage(props: FreightPageProps) {
  const query = useMemo<FreightQuery>(() => ({ ...props }), [props]);

  /** Qualquer mudança de filtro volta para a primeira página da grade. */
  const patchQuery = (patch: Partial<FreightQuery>, keepPage = false) => {
    replaceFinancialQuery(freightHref({ ...query, page: keepPage ? query.page : 1, ...patch }));
  };

  const hasPeriod = Boolean(
    (props.issueStart && props.issueEnd) || (props.entryStart && props.entryEnd),
  );

  return (
    <div className="fin-page-stack fin-page-stack--padded">
      <FinWorkspaceHeader
        title={copy.freight.title}
        subtitle={copy.freight.subtitle}
        titleHint={helpTooltips.freight}
        branch={props.branch}
        subpluginId="freight"
        onBranchChange={(next) => patchQuery({ branch: next })}
      />

      <div className="fin-toolbar">
        <div className="fin-filters" aria-label={copy.freight.filtersAria}>
          <label>
            {`${copy.freight.issuePeriodLabel} — ${copy.period.from}`}
            <input
              type="date"
              value={props.issueStart ?? ""}
              onChange={(event) => patchQuery({ issueStart: event.target.value || null })}
            />
          </label>
          <label>
            {`${copy.freight.issuePeriodLabel} — ${copy.period.to}`}
            <input
              type="date"
              value={props.issueEnd ?? ""}
              onChange={(event) => patchQuery({ issueEnd: event.target.value || null })}
            />
          </label>
          <label>
            {`${copy.freight.entryPeriodLabel} — ${copy.period.from}`}
            <input
              type="date"
              value={props.entryStart ?? ""}
              onChange={(event) => patchQuery({ entryStart: event.target.value || null })}
            />
          </label>
          <label>
            {`${copy.freight.entryPeriodLabel} — ${copy.period.to}`}
            <input
              type="date"
              value={props.entryEnd ?? ""}
              onChange={(event) => patchQuery({ entryEnd: event.target.value || null })}
            />
          </label>
          <label>
            {copy.freight.supplierLabel}
            <input
              type="text"
              value={props.supplierCode ?? ""}
              onChange={(event) => patchQuery({ supplierCode: event.target.value || null })}
            />
          </label>
          <label>
            {copy.freight.invoiceLabel}
            <input
              type="text"
              value={props.invoiceDocument ?? ""}
              onChange={(event) => patchQuery({ invoiceDocument: event.target.value || null })}
            />
          </label>
          <label>
            {copy.freight.freightDocumentLabel}
            <input
              type="text"
              value={props.freightDocument ?? ""}
              onChange={(event) => patchQuery({ freightDocument: event.target.value || null })}
            />
          </label>
          <label>
            {copy.freight.situationLabel}
            <select
              value={props.situation ?? "all"}
              onChange={(event) => patchQuery({ situation: event.target.value })}
            >
              {SITUATION_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {copy.freight.situations[value]}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="fin-link-btn"
            onClick={() =>
              patchQuery({
                issueStart: null,
                issueEnd: null,
                entryStart: null,
                entryEnd: null,
                supplierCode: null,
                invoiceDocument: null,
                freightDocument: null,
                situation: null,
              })
            }
          >
            {copy.freight.clearFilters}
          </button>
        </div>
      </div>

      {hasPeriod ? null : (
        <p className="fin-state" role="note">
          {copy.freight.periodRequired}
        </p>
      )}
    </div>
  );
}
