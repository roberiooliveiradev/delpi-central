import { useState } from "react";
import { NativeSelectField, formFieldShellBemClasses } from "@delpi/plugin-ui/index";

import { HostContainedDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { MachineLoadOperation, MachineLoadWorkCenter } from "../types";

const fieldClasses = formFieldShellBemClasses("ppc");

type Props = {
  open: boolean;
  operation: MachineLoadOperation | null;
  workCenters: MachineLoadWorkCenter[];
  busy?: boolean;
  onClose: () => void;
  onConfirm: (targetWorkCenter: string) => void;
};

/** Escolha do centro de trabalho de destino para a operação selecionada. */
export function MachineLoadTransferModal({
  open,
  operation,
  workCenters,
  busy = false,
  onClose,
  onConfirm,
}: Props) {
  return (
    <HostContainedDialog open={open} title={copy.machineLoad.transfer.modalTitle} onClose={onClose}>
      <TransferForm
        key={`${operation?.production_order ?? ""}:${operation?.operation_code ?? ""}`}
        operation={operation}
        workCenters={workCenters}
        busy={busy}
        onClose={onClose}
        onConfirm={onConfirm}
      />
    </HostContainedDialog>
  );
}

/** Remontado por `key` a cada operação: o destino escolhido nunca vaza para a próxima. */
function TransferForm({
  operation,
  workCenters,
  busy,
  onClose,
  onConfirm,
}: Omit<Props, "open">) {
  const [target, setTarget] = useState("");
  const currentCenter = operation?.work_center ?? "";

  const options = workCenters
    .filter((center) => center.work_center !== currentCenter)
    .map((center) => ({
      value: center.work_center,
      label: center.work_center_name
        ? `${center.work_center} — ${center.work_center_name}`
        : center.work_center,
    }));

  return (
    <div className="ppc-transfer">
      <p className="ppc-transfer__lead">{copy.machineLoad.transfer.lead}</p>
      {operation ? (
        <p className="ppc-transfer__operation">
          <strong>
            {copy.machineLoad.transfer.operationSummary(
              operation.production_order,
              operation.operation_code,
            )}
          </strong>
          <span>{operation.operation_description || operation.product_description || "—"}</span>
          <span>{copy.machineLoad.transfer.currentCenter(currentCenter || "—")}</span>
        </p>
      ) : null}

      {options.length === 0 ? (
        <p className="ppc-transfer__empty">{copy.machineLoad.transfer.noTargets}</p>
      ) : (
        <NativeSelectField
          id="ppc-transfer-target"
          label={copy.machineLoad.transfer.selectLabel}
          hint={copy.machineLoad.transfer.selectHint}
          classNames={fieldClasses}
          value={target}
          onChange={setTarget}
          options={options}
          placeholderOption={copy.machineLoad.transfer.selectPlaceholder}
          disabled={busy}
          span
        />
      )}

      <div className="ppc-transfer__actions">
        <button type="button" className="ppc-transfer__cancel" onClick={onClose} disabled={busy}>
          {copy.machineLoad.transfer.cancel}
        </button>
        <button
          type="button"
          className="ppc-transfer__confirm"
          disabled={busy || !target}
          onClick={() => {
            if (!target) return;
            onConfirm(target);
          }}
        >
          {copy.machineLoad.transfer.confirmAction}
        </button>
      </div>
    </div>
  );
}
