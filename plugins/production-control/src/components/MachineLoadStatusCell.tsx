import { createDashboardStatusBadge } from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";
import type { MachineLoadOperation } from "../types";
import {
  isMachineLoadFinishedOperation,
  machineLoadStatusBadge,
  resolveMachineLoadQueueStatus,
} from "../utils/machineLoadStatus";

const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });

export function MachineLoadStatusCell({ operation }: { operation: MachineLoadOperation }) {
  const presentation = resolveMachineLoadQueueStatus(operation);
  const badge = machineLoadStatusBadge(presentation);
  const running = presentation === "in_progress";
  const finished = isMachineLoadFinishedOperation(operation);
  const hasHistory =
    finished ||
    operation.is_in_production ||
    operation.production_status === "started" ||
    operation.production_status === "in_progress";
  const showOperator = hasHistory && Boolean(operation.active_operator_name);
  const showStartedAt = hasHistory && Boolean(operation.production_started_time);

  return (
    <span className="ppc-load__status">
      <span className="ppc-load__status-line">
        {running ? <span className="ppc-load__pulse" aria-hidden="true" /> : null}
        <StatusBadge label={badge.label} variant={badge.variant} />
      </span>
      {showOperator ? (
        <span
          className={
            finished && !running
              ? "ppc-load__operator ppc-load__operator--started"
              : "ppc-load__operator"
          }
          title={
            operation.active_operator_code
              ? `${copy.machineLoad.status.operatorPrefix} · ${operation.active_operator_code}`
              : copy.machineLoad.status.operatorPrefix
          }
        >
          {operation.active_operator_name}
        </span>
      ) : null}
      {showStartedAt ? (
        <span className="ppc-load__started">
          {copy.machineLoad.status.startedAt(operation.production_started_time!)}
        </span>
      ) : null}
    </span>
  );
}
