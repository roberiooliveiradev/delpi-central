import { useMutation } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { ItpConfirmPanel, ItpDialog, itpConfirmClassNames } from "../../app/itPortalUi";
import { usePortal } from "../../app/PortalContext";
import { useInvalidateInventory } from "../servers/ServerFormModal";

export function DetailField({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="itp-field">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

/** Confirmação de ação sobre o inventário; erros e sucesso vão para os avisos do portal. */
export function InventoryConfirmDialog({
  title,
  message,
  confirmLabel,
  busyLabel,
  successMessage,
  danger,
  action,
  onClose,
}: {
  title: string;
  message: string;
  confirmLabel: string;
  busyLabel: string;
  successMessage: string;
  danger?: boolean;
  action: () => Promise<unknown>;
  onClose: () => void;
}) {
  const { notifySuccess, notifyError } = usePortal();
  const invalidate = useInvalidateInventory();
  const mutation = useMutation({
    mutationFn: action,
    onSuccess: () => {
      invalidate();
      notifySuccess(successMessage);
      onClose();
    },
    onError: (error) => {
      notifyError(error);
      onClose();
    },
  });

  return (
    <ItpDialog open title={title} onClose={() => (mutation.isPending ? undefined : onClose())}>
      <ItpConfirmPanel
        classNames={itpConfirmClassNames}
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel="Cancelar"
        confirmBusy={mutation.isPending}
        confirmBusyLabel={busyLabel}
        variant={danger ? "danger" : "default"}
        onConfirm={() => mutation.mutate()}
        onCancel={onClose}
      />
    </ItpDialog>
  );
}
