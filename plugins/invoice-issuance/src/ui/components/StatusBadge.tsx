import type { IssuanceStatus } from "../../domain/types";
import { statusLabel, statusTone } from "../../domain/status";

export function StatusBadge({ status }: { status: IssuanceStatus | string }) {
  const tone = statusTone(status);
  return (
    <span
      className={`ii-status ii-status--${tone}`}
      data-testid="status-badge"
      data-status={status}
      title={statusLabel(status)}
    >
      <span className="ii-status__dot" aria-hidden />
      <span className="ii-status__label">{statusLabel(status)}</span>
    </span>
  );
}
