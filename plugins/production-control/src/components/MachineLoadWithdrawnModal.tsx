import { HostContainedWideDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { MachineLoadWithdrawnEntry, MachineLoadWithdrawnOperation } from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";

type Props = {
  open: boolean;
  entries: MachineLoadWithdrawnEntry[];
  /** Operações retiradas individualmente (E4) — restauração por item. */
  operations?: MachineLoadWithdrawnOperation[];
  busy?: boolean;
  onClose: () => void;
  onRestore: (orderNumber: string) => void;
  onRestoreOperation?: (operation: MachineLoadWithdrawnOperation) => void;
};

/** Itens fora da programação — conjuntos e operações — com devolução à fila. */
export function MachineLoadWithdrawnModal({
  open,
  entries,
  operations = [],
  busy = false,
  onClose,
  onRestore,
  onRestoreOperation,
}: Props) {
  const operationLabel = (item: MachineLoadWithdrawnOperation) =>
    copy.machineLoad.withdrawn.operationLabel(
      item.production_order,
      item.operation_code,
      item.work_center,
    );
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
        {operations.length > 0 || onRestoreOperation ? (
          <section className="ppc-withdrawn__operations">
            <h3 className="ppc-withdrawn__subtitle">
              {copy.machineLoad.withdrawn.operationsTitle}
            </h3>
            <p className="ppc-withdrawn__lead">
              {copy.machineLoad.withdrawn.operationsLead}
            </p>
            {operations.length === 0 ? (
              <p className="ppc-withdrawn__empty">
                {copy.machineLoad.withdrawn.emptyOperations}
              </p>
            ) : (
              <ul className="ppc-withdrawn__list">
                {operations.map((item) => (
                  <li
                    key={`${item.work_center}:${item.production_order}:${item.operation_code}`}
                    className="ppc-withdrawn__item"
                  >
                    <div className="ppc-withdrawn__body">
                      <p className="ppc-withdrawn__title">
                        <strong>{operationLabel(item)}</strong>
                        {item.pa_product_code ? (
                          <span>
                            {copy.machineLoad.withdrawn.productLabel(item.pa_product_code)}
                          </span>
                        ) : null}
                      </p>
                      <p className="ppc-withdrawn__meta">
                        {item.pa_due_date ? (
                          <span>
                            {copy.machineLoad.locate.due(formatIsoDate(item.pa_due_date))}
                          </span>
                        ) : null}
                      </p>
                      <p className="ppc-withdrawn__author">
                        {copy.machineLoad.withdrawn.withdrawnBy(
                          item.withdrawn_by,
                          item.withdrawn_at ? formatRefreshedAt(item.withdrawn_at) : null,
                        )}
                      </p>
                    </div>
                    <button
                      type="button"
                      className="ppc-withdrawn__restore"
                      disabled={busy || !onRestoreOperation}
                      onClick={() => onRestoreOperation?.(item)}
                    >
                      {copy.machineLoad.withdrawn.restoreAction}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ) : null}
      </div>
    </HostContainedWideDialog>
  );
}
