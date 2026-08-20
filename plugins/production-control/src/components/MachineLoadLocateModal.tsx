import { HostContainedWideDialog } from "./PpcConfirmModal";
import { MachineLoadLocateResults } from "./MachineLoadLocateResults";
import { copy } from "../content/copy";
import type { MachineLoadLocatePayload, MachineLoadLocateStop } from "../types";

type Props = {
  open: boolean;
  /** C2_NUM do conjunto (6 dígitos). */
  productionOrder: string | null;
  /** Produto (PA) do conjunto, só informativo. */
  paCode: string | null;
  loading: boolean;
  error: string | null;
  result: MachineLoadLocatePayload | null;
  onClose: () => void;
  onGoToStop: (stop: MachineLoadLocateStop) => void;
};

/** Modal com a jornada do conjunto (mesmo C2_NUM) a partir do menu de contexto. */
export function MachineLoadLocateModal({
  open,
  productionOrder,
  paCode,
  loading,
  error,
  result,
  onClose,
  onGoToStop,
}: Props) {
  const title = productionOrder
    ? copy.machineLoad.rowActions.traceConjuntoTitle(productionOrder)
    : copy.machineLoad.rowActions.traceConjunto;

  return (
    <HostContainedWideDialog open={open} title={title} onClose={onClose}>
      <div className="ppc-locate-modal">
        <p className="ppc-locate-modal__lead">
          {copy.machineLoad.rowActions.traceConjuntoLead(paCode)}
        </p>
        <MachineLoadLocateResults
          loading={loading}
          error={error}
          result={result}
          onGoToStop={(stop) => {
            onGoToStop(stop);
            onClose();
          }}
        />
      </div>
    </HostContainedWideDialog>
  );
}
