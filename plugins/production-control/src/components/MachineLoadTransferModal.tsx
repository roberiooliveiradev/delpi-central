import { useState } from "react";
import { NativeSelectField, formFieldShellBemClasses } from "@delpi/plugin-ui/index";

import { HostContainedDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { MachineLoadOperation, MachineLoadWorkCenter } from "../types";
import { conjuntoKeyFromOrder } from "../utils/machineLoadLocate";

const fieldClasses = formFieldShellBemClasses("ppc");

export type MachineLoadTransferMode = "operation" | "conjunto";

type Props = {
  open: boolean;
  mode?: MachineLoadTransferMode;
  operation: MachineLoadOperation | null;
  workCenters: MachineLoadWorkCenter[];
  busy?: boolean;
  onClose: () => void;
  onConfirm: (targetWorkCenter: string) => void;
};

/** Escolha do centro de trabalho de destino (item ou conjunto no CT atual). */
export function MachineLoadTransferModal({
  open,
  mode = "operation",
  operation,
  workCenters,
  busy = false,
  onClose,
  onConfirm,
}: Props) {
  const title =
    mode === "conjunto"
      ? copy.machineLoad.transfer.modalTitleConjunto
      : copy.machineLoad.transfer.modalTitle;
  return (
    <HostContainedDialog open={open} title={title} onClose={onClose}>
      <TransferForm
        key={`${mode}:${operation?.production_order ?? ""}:${operation?.operation_code ?? ""}`}
        mode={mode}
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
  mode,
  operation,
  workCenters,
  busy,
  onClose,
  onConfirm,
}: Omit<Props, "open">) {
  const [target, setTarget] = useState("");
  const currentCenter = operation?.work_center ?? "";
  const conjuntoKey = conjuntoKeyFromOrder(operation?.production_order);

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
      <p className="ppc-transfer__lead">
        {mode === "conjunto"
          ? copy.machineLoad.transfer.leadConjunto
          : copy.machineLoad.transfer.lead}
      </p>
      {operation ? (
        <p className="ppc-transfer__operation">
          <strong>
            {mode === "conjunto" && conjuntoKey
              ? copy.machineLoad.transfer.conjuntoSummary(conjuntoKey, currentCenter || "—")
              : copy.machineLoad.transfer.operationSummary(
                  operation.production_order,
                  operation.operation_code,
                )}
          </strong>
          {mode === "operation" ? (
            <span>{operation.operation_description || operation.product_description || "—"}</span>
          ) : null}
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
