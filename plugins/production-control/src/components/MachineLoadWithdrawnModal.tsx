import { HostContainedWideDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { MachineLoadWithdrawnEntry } from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";

type Props = {
  open: boolean;
  entries: MachineLoadWithdrawnEntry[];
  busy?: boolean;
  onClose: () => void;
  onRestore: (orderNumber: string) => void;
};

/** Conjuntos retirados da programação, com a ação de devolver cada um à fila. */
export function MachineLoadWithdrawnModal({ open, entries, busy = false, onClose, onRestore }: Props) {
  return (
    <HostContainedWideDialog
      open={open}
      title={copy.machineLoad.withdrawn.modalTitle}
      onClose={onClose}
    >
      <div className="ppc-withdrawn">
        <p className="ppc-withdrawn__lead">{copy.machineLoad.withdrawn.lead}</p>
        {entries.length === 0 ? (
          <p className="ppc-withdrawn__empty">{copy.machineLoad.withdrawn.empty}</p>
        ) : (
          <ul className="ppc-withdrawn__list">
            {entries.map((entry) => (
              <li key={entry.order_number} className="ppc-withdrawn__item">
                <div className="ppc-withdrawn__body">
                  <p className="ppc-withdrawn__title">
                    <strong>{copy.machineLoad.withdrawn.conjuntoLabel(entry.order_number)}</strong>
                    {entry.pa_product_code ? (
                      <span>{copy.machineLoad.withdrawn.productLabel(entry.pa_product_code)}</span>
                    ) : null}
                  </p>
                  <p className="ppc-withdrawn__meta">
                    <span>{copy.machineLoad.withdrawn.operations(entry.operation_count)}</span>
                    {entry.work_centers.length > 0 ? (
                      <span>{copy.machineLoad.withdrawn.centers(entry.work_centers)}</span>
                    ) : null}
                    {entry.pa_due_date ? (
                      <span>{copy.machineLoad.locate.due(formatIsoDate(entry.pa_due_date))}</span>
                    ) : null}
                  </p>
                  <p className="ppc-withdrawn__author">
                    {copy.machineLoad.withdrawn.withdrawnBy(
                      entry.withdrawn_by,
                      entry.withdrawn_at ? formatRefreshedAt(entry.withdrawn_at) : null,
                    )}
                  </p>
                </div>
                <button
                  type="button"
                  className="ppc-withdrawn__restore"
                  disabled={busy}
                  onClick={() => onRestore(entry.order_number)}
                >
                  {copy.machineLoad.withdrawn.restoreAction}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </HostContainedWideDialog>
  );
}
