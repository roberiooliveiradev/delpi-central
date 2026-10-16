import { createDashboardStatusBadge } from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";
import type { MachineLoadOperation } from "../types";
import {
  machineLoadStatusBadge,
  resolveMachineLoadQueueStatus,
} from "../utils/machineLoadStatus";

const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });

/** ISO do início do run → HH:mm local; texto bruto se não parsear. */
function formatRunStart(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

/**
 * Situação da operação — exclusivamente a execução do cockpit.
 *
 * Sem run aberto a célula mostra «Não iniciada» (ou «Já apontada» quando o
 * saldo esgotou). Nome de operador e horário do Play HZA não entram aqui:
 * o contrato de execução não carrega identidade do operador.
 */
export function MachineLoadStatusCell({ operation }: { operation: MachineLoadOperation }) {
  const presentation = resolveMachineLoadQueueStatus(operation);
  const badge = machineLoadStatusBadge(presentation);
  const running = presentation === "in_progress";
  const startedAt =
    operation.execution_status != null && operation.execution_started_at
      ? copy.machineLoad.status.startedAt(formatRunStart(operation.execution_started_at))
      : null;

  return (
    <span className="ppc-load__status">
      <span className="ppc-load__status-line">
        {running ? <span className="ppc-load__pulse" aria-hidden="true" /> : null}
        <StatusBadge label={badge.label} variant={badge.variant} />
      </span>
      {startedAt ? <span className="ppc-load__started">{startedAt}</span> : null}
    </span>
  );
}
