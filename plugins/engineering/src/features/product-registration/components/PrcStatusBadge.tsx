import { EngineeringStatusBadge } from "../../../ui/engineeringUi";
import { PRC_STATUS_VARIANTS, prcStatusLabel } from "../prcCopy";

/** Badge semântico de status do caso — texto completo (nunca só cor). */
export function PrcStatusBadge({ status }: { status: string }) {
  return (
    <EngineeringStatusBadge
      label={prcStatusLabel(status)}
      variant={PRC_STATUS_VARIANTS[status] || "neutral"}
    />
  );
}
