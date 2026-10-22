import {
  SuppliesActionButton,
  SuppliesDataTable,
  SuppliesStatusBadge,
  type DataTableColumn,
} from "../../../app/suppliesUi";
import {
  COMPARISON_LABELS,
  COMPARISON_VARIANTS,
  DECISION_LABELS,
  ELIGIBILITY_LABELS,
  ENRICHMENT_CONTENT as C,
} from "./content";
import {
  canAcceptProposal,
  canRejectProposal,
  enrichmentFieldLabel,
} from "./stateMachine";
import type { EnrichmentProposal } from "./types";

type EnrichmentComparisonTableProps = {
  proposals: readonly EnrichmentProposal[];
  busy: boolean;
  actionable: boolean;
  selected: ReadonlySet<string>;
  onToggleSelected: (fieldKey: string) => void;
  onDecide: (fieldKey: string, decision: "ACCEPT" | "REJECT") => void;
};

function valueText(value: string | null, emptyLabel: string): string {
  const trimmed = (value ?? "").trim();
  return trimmed || emptyLabel;
}

export function EnrichmentComparisonTable({
  proposals,
  busy,
  actionable,
  selected,
  onToggleSelected,
  onDecide,
}: EnrichmentComparisonTableProps) {
  const columns: DataTableColumn<EnrichmentProposal>[] = [
    {
      key: "select",
      header: C.selectLabel,
      interactive: true,
      rowClick: "stop",
      render: (p) =>
        actionable && canRejectProposal(p) ? (
          <input
            type="checkbox"
            className="sp-enrichment__check"
            checked={selected.has(p.field_key)}
            onChange={() => onToggleSelected(p.field_key)}
            aria-label={`${C.selectLabel} ${enrichmentFieldLabel(p.field_key)}`}
            disabled={busy}
          />
        ) : null,
    },
    {
      key: "field",
      header: C.columnField,
      render: (p) => (
        <span title={p.eligibility_reason ?? undefined}>
          {enrichmentFieldLabel(p.field_key)}
        </span>
      ),
    },
    {
      key: "current",
      header: C.columnCurrent,
      render: (p) =>
        p.comparison_state === "PROTECTED" ? (
          <span>{C.protectedValue}</span>
        ) : (
          valueText(p.current_value, C.currentNotProvided)
        ),
    },
    {
      key: "suggested",
      header: C.columnSuggested,
      render: (p) =>
        p.comparison_state === "PROTECTED"
          ? "—"
          : valueText(p.suggested_value, C.sourceNotProvided),
    },
    {
      key: "status",
      header: C.columnStatus,
      render: (p) => (
        <span className="sp-enrichment__status">
          <SuppliesStatusBadge
            variant={COMPARISON_VARIANTS[p.comparison_state] ?? "neutral"}
            label={COMPARISON_LABELS[p.comparison_state] ?? p.comparison_state}
          />
          <span className="sp-enrichment__eligibility">
            {ELIGIBILITY_LABELS[p.eligibility_state] ?? p.eligibility_state}
          </span>
        </span>
      ),
    },
    {
      key: "decision",
      header: C.columnDecision,
      interactive: true,
      rowClick: "stop",
      render: (p) =>
        p.decision_state === "PENDING" && actionable ? (
          <span className="sp-enrichment__row-actions">
            <SuppliesActionButton
              type="button"
              variant="ghost"
              disabled={busy || !canAcceptProposal(p)}
              title={
                canAcceptProposal(p)
                  ? undefined
                  : (p.eligibility_reason ?? C.errorNotEligible)
              }
              onClick={() => onDecide(p.field_key, "ACCEPT")}
            >
              {C.acceptAction}
            </SuppliesActionButton>
            <SuppliesActionButton
              type="button"
              variant="ghost"
              disabled={busy}
              onClick={() => onDecide(p.field_key, "REJECT")}
            >
              {C.rejectAction}
            </SuppliesActionButton>
          </span>
        ) : (
          DECISION_LABELS[p.decision_state]
        ),
    },
  ];

  return (
    <SuppliesDataTable
      columns={columns}
      rows={[...proposals]}
      rowKey={(p) => p.proposal_id}
      layout="section"
    />
  );
}
