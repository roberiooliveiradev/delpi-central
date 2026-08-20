import { createDashboardStatusBadge } from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";
import type { MachineLoadOperation } from "../types";
import {
  isMachineLoadStarted,
  machineLoadStatusBadge,
} from "../utils/machineLoadStatus";

const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });

export function MachineLoadStatusCell({ operation }: { operation: MachineLoadOperation }) {
  const badge = machineLoadStatusBadge(operation.production_status);
  const running = operation.is_in_production;
  const started = isMachineLoadStarted(operation.production_status);
  const showOperator = (running || started) && Boolean(operation.active_operator_name);
  const showStartedAt =
    (running || started) && Boolean(operation.production_started_time);

  return (
    <span className="ppc-load__status">
      <span className="ppc-load__status-line">
        {running ? <span className="ppc-load__pulse" aria-hidden="true" /> : null}
        <StatusBadge label={badge.label} variant={badge.variant} />
      </span>
      {showOperator ? (
        <span
          className={
            started && !running
              ? "ppc-load__operator ppc-load__operator--started"
              : "ppc-load__operator"
          }
          title={operation.active_operator_code ?? undefined}
        >
          {copy.machineLoad.status.operatorPrefix} · {operation.active_operator_name}
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
