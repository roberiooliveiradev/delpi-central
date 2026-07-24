import type { InvoicePostingStatus } from "../../domain/types";
import { statusLabel } from "../../domain/status";

const TONE: Record<string, string> = {
  pending: "pending",
  in_progress: "progress",
  blocked: "blocked",
  posted: "posted",
  cancelled: "cancelled",
};

export function StatusBadge({ status }: { status: InvoicePostingStatus | string }) {
  const tone = TONE[status] ?? "pending";
  return (
    <span
      className={`lnf-status lnf-status--${tone}`}
      data-testid="status-badge"
      data-status={status}
      title={statusLabel(status)}
    >
      <span className="lnf-status__dot" aria-hidden />
      <span className="lnf-status__label">{statusLabel(status)}</span>
    </span>
  );
}
