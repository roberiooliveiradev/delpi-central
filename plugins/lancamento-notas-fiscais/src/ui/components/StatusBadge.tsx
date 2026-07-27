import type { InvoicePostingStatus } from "../../domain/types";
import { statusLabel, statusTone } from "../../domain/status";

export function StatusBadge({ status }: { status: InvoicePostingStatus | string }) {
  const tone = statusTone(status);
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
