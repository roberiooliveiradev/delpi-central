import {
  SuppliesActionButton,
  SuppliesCompactPagination,
  SuppliesDataTable,
  SuppliesStatusBadge,
  type DataTableColumn,
} from "../../../app/suppliesUi";
import {
  ENRICHMENT_CONTENT as C,
  REVIEW_STATUS_LABELS,
} from "./content";
import type { EnrichmentReview } from "./types";

type EnrichmentHistoryTableProps = {
  items: readonly EnrichmentReview[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  activeReviewId?: string;
  onPageChange: (page: number) => void;
  onOpenReview: (reviewId: string) => void;
};

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

export function EnrichmentHistoryTable({
  items,
  total,
  page,
  pageSize,
  loading,
  activeReviewId,
  onPageChange,
  onOpenReview,
}: EnrichmentHistoryTableProps) {
  const columns: DataTableColumn<EnrichmentReview>[] = [
    {
      key: "reviewed_at",
      header: C.columnReviewedAt,
      render: (r) => formatDateTime(r.source_retrieved_at || r.created_at),
    },
    {
      key: "source",
      header: C.columnSource,
      render: (r) => r.source_id,
    },
    {
      key: "status",
      header: C.columnReviewStatus,
      render: (r) => (
        <SuppliesStatusBadge
          variant={r.status === "IN_REVIEW" ? "info" : r.status === "DECIDED" ? "success" : "neutral"}
          label={REVIEW_STATUS_LABELS[r.status] ?? r.status}
        />
      ),
    },
    {
      key: "revision",
      header: C.columnRevision,
      align: "center",
      render: (r) => String(r.revision),
    },
    {
      key: "expires",
      header: C.columnExpires,
      render: (r) => formatDateTime(r.expires_at),
    },
    {
      key: "open",
      header: "",
      interactive: true,
      rowClick: "stop",
      render: (r) =>
        r.review_id === activeReviewId ? null : (
          <SuppliesActionButton
            type="button"
            variant="ghost"
            disabled={loading}
            onClick={() => onOpenReview(r.review_id)}
          >
            {C.openReviewAction}
          </SuppliesActionButton>
        ),
    },
  ];

  return (
    <div className="sp-enrichment__history">
      <SuppliesDataTable
        columns={columns}
        rows={[...items]}
        rowKey={(r) => r.review_id}
        layout="section"
        emptyMessage={C.historyEmpty}
        loading={loading}
      />
      <SuppliesCompactPagination
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={onPageChange}
        disabled={loading}
      />
    </div>
  );
}
